#!/usr/bin/env python3
"""
Cross-app generalisation probe — round-3 reviewer ask #3.

The koenig pilot has 264 ReproBreak cases (93 reproduced) with a strong
`data-kg-*` anchor culture. A reviewer will (correctly) suspect we are
learning Koenig conventions rather than a general React/Playwright repair
strategy. This probe answers: does HealReact's L1 extractor + resolver
generalise to a *second* React+Playwright codebase with a *different*
anchor culture?

Pick: payloadcms/payload (Next.js admin UI, 319 Playwright cases in the
ReproBreak CSV — second-largest Playwright cohort after koenig). Different
component conventions (no `data-kg-*`), heavy use of `getByRole` and
`getByTestId`, larger codebase.

Pipeline:
  1. Sparse-checkout HEAD of payloadcms/payload, restrict to TS/TSX UI.
  2. Run extractor on the UI directory.
  3. For each Playwright break pair in the CSV, resolve `new_locator`
     against the LocatorSheet. Count hits.

This is a SHALLOWER probe than the koenig one — we only check `new_locator`
reachability at HEAD, not the per-commit reach_old/reach_new pair. That's
fine for the "does the extractor generalise" question; per-commit pairing
would require BFG-ing the issue tracker again, which is out of scope.

Reads:  /Users/DongbiaoGao/Downloads/ReproBreak/ReproBreak-main/locator_analysis.csv
Writes: healreact/bench/cases/payload/{_sheet.json, _resolve_head.json, _summary.json}
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from resolve_locators import parse_locator_expr, find_matches  # type: ignore

REPRO_CSV = Path("/Users/DongbiaoGao/Downloads/ReproBreak/ReproBreak-main/locator_analysis.csv")
REPO = "payloadcms/payload"
SHORT = "payload"
BENCH = Path(__file__).resolve().parents[1] / "cases" / SHORT
SRC = BENCH / "_src"


def is_playwright(row: dict) -> bool:
    s = row["old_locator"] + row["new_locator"]
    return any(k in s for k in ("page.", "getByTestId", "getByRole(", "getByLabel(", "getByText("))


def load_breaks() -> list[dict]:
    rows = []
    with REPRO_CSV.open() as f:
        for r in csv.DictReader(f):
            if r["repository"] == REPO and is_playwright(r):
                rows.append(r)
    return rows


def sparse_clone() -> Path:
    # Reuse if present.
    target = SRC / "payload"
    if (target / ".git").exists():
        return target
    SRC.mkdir(parents=True, exist_ok=True)
    print(f"[clone] sparse clone of {REPO} HEAD …", file=sys.stderr)
    subprocess.run([
        "git", "clone", "--filter=blob:none", "--no-checkout", "--depth", "1",
        f"https://github.com/{REPO}.git", str(target),
    ], check=True)
    subprocess.run(["git", "sparse-checkout", "init", "--cone"], cwd=target, check=True)
    # payload is a monorepo. UI lives under packages/ui and packages/next.
    # We also include test/ for cross-checking if needed.
    subprocess.run(["git", "sparse-checkout", "set",
                    "packages/ui/src", "packages/next/src"], cwd=target, check=True)
    subprocess.run(["git", "checkout", "HEAD"], cwd=target, check=True)
    return target


def run_extractor(src_dir: Path, out_sheet: Path) -> int:
    """Invoke the TS extractor on the sparse-checked-out UI directory."""
    cmd = [
        "npx", "tsx",
        str(Path(__file__).resolve().parents[2] / "src" / "ast" / "extractor.ts"),
        "--src", str(src_dir),
        "--out", str(out_sheet),
    ]
    print(f"[extract] {' '.join(cmd[-2:])}", file=sys.stderr)
    r = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-500:])
        print(r.stderr[-1500:])
        return r.returncode
    return 0


def main() -> int:
    breaks = load_breaks()
    print(f"[csv] payload Playwright break pairs: {len(breaks)}", file=sys.stderr)

    repo = sparse_clone()
    # Try packages/ui/src first; fall back to whichever exists.
    candidates = [repo / "packages" / "ui" / "src", repo / "packages" / "next" / "src"]
    existing = [p for p in candidates if p.exists()]
    if not existing:
        print("[error] no expected source dirs after sparse checkout", file=sys.stderr)
        return 2
    BENCH.mkdir(parents=True, exist_ok=True)
    sheet_path = BENCH / "_sheet.json"
    # Extract from packages/ui/src (the primary UI package).
    rc = run_extractor(existing[0], sheet_path)
    if rc != 0:
        return rc

    sheet = json.loads(sheet_path.read_text())
    records = sheet["records"]
    print(f"[extract] records: {len(records)}", file=sys.stderr)

    # Resolve every new_locator (HEAD reachability proxy).
    hits = 0
    rows_out = []
    for r in breaks:
        q = parse_locator_expr(r["new_locator"])
        m = find_matches(records, q)
        ok = len(m) >= 1
        if ok:
            hits += 1
        rows_out.append({
            "id": r["id"],
            "old": r["old_locator"],
            "new": r["new_locator"],
            "category": r["category"],
            "new_hits": len(m),
            "first_hit": (m[0]["componentFile"], m[0]["line"]) if m else None,
        })

    summary = {
        "repo": REPO,
        "n_break_pairs": len(breaks),
        "n_records_extracted": len(records),
        "new_locator_reachable_at_head": hits,
        "reach_pct": round(hits / len(breaks) * 100.0, 1) if breaks else 0.0,
        "extracted_dir": str(existing[0].relative_to(repo)),
        "rows": rows_out,
    }
    (BENCH / "_resolve_head.json").write_text(json.dumps({"rows": rows_out}, indent=2))
    (BENCH / "_summary.json").write_text(json.dumps(
        {k: v for k, v in summary.items() if k != "rows"}, indent=2
    ))

    print()
    print("========= CROSS-APP PROBE SUMMARY =========")
    print(f"repo                      : {REPO}")
    print(f"extracted dir             : {summary['extracted_dir']}")
    print(f"records extracted         : {len(records)}")
    print(f"playwright break pairs    : {len(breaks)}")
    print(f"new_locator reachable HEAD: {hits} / {len(breaks)} = {summary['reach_pct']}%")
    print(f"output -> {BENCH}/_summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
