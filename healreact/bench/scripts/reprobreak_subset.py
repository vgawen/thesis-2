#!/usr/bin/env python3
"""
Measure the React/Playwright subset of ReproBreak.

Usage:
  # 1. Clone ReproBreak alongside this repo
  git clone https://github.com/rub-sq/ReproBreak.git /tmp/ReproBreak

  # 2. Optionally download the reproduced-breaks DB from
  #    https://figshare.com/s/9d1b3910b52d1aa1c2dc → /tmp/ReproBreak/data/ReproBreak.db

  # 3. Run this script
  python3 healreact/bench/scripts/reprobreak_subset.py /tmp/ReproBreak

Outputs:
  - candidate React/Playwright subset count from locator_analysis.csv
  - if ReproBreak.db is present, the *reproduced* React/Playwright subset count
  - JSON report at healreact/bench/ReactHealBench/reprobreak_subset.json
"""
from __future__ import annotations
import csv
import json
import sqlite3
import sys
from pathlib import Path
from collections import Counter

# Repos in the top-216 that we know to be React-based.
# Extend this list after manual inspection — these are sufficient for the pilot.
KNOWN_REACT_REPOS = {
    "payloadcms/payload",        # Next.js / React admin
    "citizenlabdotco/citizenlab", # React frontend
    "mattermost/mattermost",     # React webapp
    "kong/insomnia",             # React + Electron
    "tryghost/koenig",           # React editor
    "ethyca/fides",              # Next.js / React
    "porsche-design-system/porsche-design-system",  # Stencil (React-adjacent web components)
    "microsoft/playwright",      # Playwright's own test suite (React playgrounds)
}


def classify_playwright(loc: str) -> bool:
    """Heuristic: any of Playwright's locator APIs."""
    if not loc:
        return False
    return (
        "page." in loc
        or "getByRole" in loc
        or "getByTestId" in loc
        or "getByLabel" in loc
        or "getByText" in loc
        or "locator(" in loc
    )


def classify_cypress(loc: str) -> bool:
    return loc.startswith("cy.") if loc else False


def main(reprobreak_root: str) -> None:
    root = Path(reprobreak_root)
    csv_path = root / "locator_analysis.csv"
    db_path = root / "data" / "ReproBreak.db"

    if not csv_path.exists():
        sys.exit(f"missing {csv_path}; did you `git clone https://github.com/rub-sq/ReproBreak.git {root}`?")

    rows = list(csv.DictReader(csv_path.open()))
    repo_counter = Counter(r["repository"] for r in rows)
    pw_rows = [r for r in rows if classify_playwright(r["old_locator"]) or classify_playwright(r["new_locator"])]
    cy_rows = [r for r in rows if classify_cypress(r["old_locator"]) or classify_cypress(r["new_locator"])]

    react_pw_rows = [r for r in pw_rows if r["repository"] in KNOWN_REACT_REPOS]
    react_cy_rows = [r for r in cy_rows if r["repository"] in KNOWN_REACT_REPOS]

    report = {
        "source": "locator_analysis.csv (candidate locator changes; NOT reproduced breaks)",
        "total_candidate_changes": len(rows),
        "distinct_repos": len(repo_counter),
        "by_framework_syntax": {
            "playwright_style": len(pw_rows),
            "cypress_style": len(cy_rows),
        },
        "react_subset_candidates": {
            "playwright": len(react_pw_rows),
            "cypress": len(react_cy_rows),
            "repos_used": sorted(KNOWN_REACT_REPOS),
        },
        "reproduced_breaks_total": None,
        "reproduced_breaks_react_playwright": None,
        "note": "9604 rows in locator_analysis.csv are CANDIDATE locator changes; the paper reports 449 REPRODUCED breaks. To get the reproduced subset, download data/ReproBreak.db from Figshare and re-run this script.",
    }

    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        report["db_tables"] = [r[0] for r in cur.fetchall()]

        # Schema (database/schema.sql):
        #   locator_change(id, framework, repository_name, ...)
        #   locator_break(locator_change_id, reproduce_files_id)  -- the REPRODUCED set
        # A locator_change is "reproduced" iff its id appears in locator_break.

        cur.execute("SELECT COUNT(DISTINCT locator_change_id) FROM locator_break")
        report["reproduced_breaks_total"] = cur.fetchone()[0]

        cur.execute(
            "SELECT lc.framework, COUNT(DISTINCT lc.id) "
            "FROM locator_change lc JOIN locator_break lb ON lb.locator_change_id = lc.id "
            "GROUP BY lc.framework"
        )
        report["reproduced_by_framework"] = {fw or "unknown": n for fw, n in cur.fetchall()}

        # React+Playwright reproduced, per repo
        placeholders = ",".join(["?"] * len(KNOWN_REACT_REPOS))
        cur.execute(
            f"SELECT lc.repository_name, COUNT(DISTINCT lc.id) "
            f"FROM locator_change lc JOIN locator_break lb ON lb.locator_change_id = lc.id "
            f"WHERE LOWER(lc.framework) = 'playwright' AND lc.repository_name IN ({placeholders}) "
            f"GROUP BY lc.repository_name ORDER BY 2 DESC",
            list(KNOWN_REACT_REPOS),
        )
        per_repo = {repo: n for repo, n in cur.fetchall()}
        report["reproduced_breaks_react_playwright"] = {
            "total": sum(per_repo.values()),
            "per_repo": per_repo,
        }

        # Pilot focus: tryghost/koenig (the chosen pilot app per EXPERIMENT_PLAN §Pilot)
        cur.execute(
            "SELECT COUNT(DISTINCT lc.id) "
            "FROM locator_change lc JOIN locator_break lb ON lb.locator_change_id = lc.id "
            "WHERE LOWER(lc.framework) = 'playwright' AND lc.repository_name = 'tryghost/koenig'"
        )
        report["pilot_tryghost_koenig_reproduced_playwright"] = cur.fetchone()[0]

        conn.close()

    out_path = Path(__file__).resolve().parents[1] / "ReactHealBench" / "reprobreak_subset.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"\nreport written to {out_path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/ReproBreak")
