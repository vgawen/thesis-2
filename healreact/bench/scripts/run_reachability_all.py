#!/usr/bin/env python3
"""
For each unique commit referenced by koenig breaks, sparse-checkout the React
source at that commit, run the extractor, run the resolver, and aggregate.

Single shared clone (_src/koenig-master) is reused across commits via
`git checkout <sha>` — much faster than 19 separate clones.

Output:
  bench/cases/koenig/_reachability_per_commit.csv
  bench/cases/koenig/_reachability_summary.json
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "cases" / "koenig"
SHARED = ROOT / "_src" / "koenig-master"
EXTRACTOR = Path(__file__).resolve().parent.parent.parent / "src" / "ast" / "extractor.ts"


def sh(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, check=check)


def ensure_shared_clone() -> None:
    if (SHARED / ".git").exists():
        return
    SHARED.parent.mkdir(parents=True, exist_ok=True)
    print(f"  cloning koenig master partial → {SHARED}")
    sh(["git", "clone", "--filter=blob:none", "--no-checkout",
        "https://github.com/tryghost/koenig.git", str(SHARED)])
    sh(["git", "sparse-checkout", "init", "--cone"], cwd=SHARED)
    sh(["git", "sparse-checkout", "set", "packages/koenig-lexical/src"], cwd=SHARED)


def fetch_and_checkout(commit: str) -> None:
    # fetch the specific commit shallowly
    try:
        sh(["git", "fetch", "--depth", "1", "origin", commit], cwd=SHARED)
    except subprocess.CalledProcessError as e:
        print(f"  fetch failed for {commit[:8]}: {e.stderr[:200]}", file=sys.stderr)
        raise
    sh(["git", "checkout", "-f", commit], cwd=SHARED)


def main() -> int:
    manifest = json.loads((ROOT / "_manifest.json").read_text())
    commits = sorted({c["commit"] for c in manifest["cases"]})
    print(f"unique commits to process: {len(commits)}")
    ensure_shared_clone()

    env = os.environ.copy()
    env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH", "")

    rows = []
    grand_total = 0
    grand_old = 0
    grand_new = 0
    t0 = time.time()
    for i, commit in enumerate(commits, 1):
        short = commit[:8]
        sheet_path = ROOT / "_src" / f"_sheets" / f"{short}.LocatorSheet.json"
        sheet_path.parent.mkdir(parents=True, exist_ok=True)
        resolve_out = ROOT / "_src" / "_resolves" / f"{short}.json"
        resolve_out.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n[{i}/{len(commits)}] commit {short}")
        try:
            fetch_and_checkout(commit)
        except Exception:
            rows.append({"commit": short, "status": "fetch-failed", "total": 0, "reach_old": 0, "reach_new": 0, "records": 0})
            continue

        src_dir = SHARED / "packages" / "koenig-lexical" / "src"
        if not src_dir.exists():
            print(f"  ⚠ no src dir at this commit, skipping")
            rows.append({"commit": short, "status": "no-src", "total": 0, "reach_old": 0, "reach_new": 0, "records": 0})
            continue

        # 1) extractor
        try:
            r = sh(["npx", "tsx", str(EXTRACTOR), "--src", str(src_dir), "--out", str(sheet_path)],
                   cwd=EXTRACTOR.parent.parent.parent, check=False)
            if r.returncode != 0:
                print(f"  extractor failed:\n{r.stderr[-500:]}")
                rows.append({"commit": short, "status": "extractor-failed", "total": 0, "reach_old": 0, "reach_new": 0, "records": 0})
                continue
        except Exception as e:
            print(f"  extractor crashed: {e}")
            rows.append({"commit": short, "status": "extractor-crashed", "total": 0, "reach_old": 0, "reach_new": 0, "records": 0})
            continue

        records = json.loads(sheet_path.read_text())["count"]
        # 2) resolver
        sh(["python3", str(Path(__file__).resolve().parent / "resolve_locators.py"),
            "--commit", commit, "--sheet", str(sheet_path), "--out", str(resolve_out), "--quiet"],
           check=True)

        rj = json.loads(resolve_out.read_text())
        total = rj["breaks_tested"]
        ro = rj["reachable_old"]
        rn = rj["reachable_new"]
        grand_total += total
        grand_old += ro
        grand_new += rn
        pct = (100 * rn / total) if total else 0
        print(f"  records={records:4d}  breaks={total:3d}  reach_old={ro:3d}  reach_new={rn:3d}  ({pct:.0f}%)")
        rows.append({"commit": short, "status": "ok", "total": total, "reach_old": ro, "reach_new": rn, "records": records})

    # write CSV + JSON summary
    csv_path = ROOT / "_reachability_per_commit.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["commit", "status", "records", "total", "reach_old", "reach_new", "pct_new"])
        w.writeheader()
        for r in rows:
            r2 = dict(r)
            r2["pct_new"] = round(100 * r["reach_new"] / r["total"], 1) if r["total"] else 0
            w.writerow(r2)

    summary = {
        "commits_processed": len(commits),
        "commits_ok": sum(1 for r in rows if r["status"] == "ok"),
        "breaks_total": grand_total,
        "reach_old_total": grand_old,
        "reach_new_total": grand_new,
        "pct_old": round(100 * grand_old / grand_total, 1) if grand_total else 0,
        "pct_new": round(100 * grand_new / grand_total, 1) if grand_total else 0,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    (ROOT / "_reachability_summary.json").write_text(json.dumps(summary, indent=2))

    print(f"\n========= SUMMARY =========")
    print(json.dumps(summary, indent=2))
    print(f"\nCSV   → {csv_path}")
    print(f"JSON  → {ROOT / '_reachability_summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
