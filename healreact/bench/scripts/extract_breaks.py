#!/usr/bin/env python3
"""
Extract koenig × Playwright locator breaks from ReproBreak.db and materialise
each break as a self-contained directory:

    bench/cases/koenig/<id>/
        metadata.json            (commit, file, line, old/new locator, framework, instructions)
        test_file_snapshot.spec.js  (full test file content at break commit, fetched from GitHub raw)
        old_locator_line.txt     (the single broken line, line_no, with ±2 line context)

Uses GitHub raw for content (no auth needed, no git clone). Caches (commit, path)
fetches in memory across the run; same test file referenced by N breaks costs 1 fetch.

Usage:
    python extract_breaks.py [--db PATH] [--repo REPO] [--out DIR] [--limit N]

Defaults match ReactHealBench layout under healreact/bench/.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_REPO = "tryghost/koenig"
DEFAULT_DB = Path("/tmp/healreact_external/ReproBreak/data/ReproBreak.db")
DEFAULT_OUT = Path(__file__).resolve().parent.parent / "cases" / "koenig"


def fetch_github_raw(repo: str, commit: str, path: str, cache: dict, retries: int = 3) -> str | None:
    key = (commit, path)
    if key in cache:
        return cache[key]
    url = f"https://raw.githubusercontent.com/{repo}/{commit}/{path}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "healreact-bench"})
            with urllib.request.urlopen(req, timeout=20) as r:
                if r.status == 200:
                    content = r.read().decode("utf-8", errors="replace")
                    cache[key] = content
                    return content
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache[key] = None
                return None
            if e.code == 429:
                time.sleep(2 ** attempt)
                continue
        except Exception as e:
            if attempt == retries - 1:
                print(f"  ! fetch failed for {url}: {e}", file=sys.stderr)
                cache[key] = None
                return None
            time.sleep(2 ** attempt)
    cache[key] = None
    return None


def line_context(text: str, line_no: int, window: int = 2) -> str:
    lines = text.splitlines()
    lo = max(0, line_no - 1 - window)
    hi = min(len(lines), line_no + window)
    width = len(str(hi))
    out = []
    for i in range(lo, hi):
        marker = ">>" if i + 1 == line_no else "  "
        out.append(f"{marker} {str(i + 1).rjust(width)} | {lines[i]}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--repo", default=DEFAULT_REPO)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=0, help="0 = all")
    args = ap.parse_args()

    if not args.db.exists():
        print(f"ERROR: db not found at {args.db}", file=sys.stderr)
        return 2

    args.out.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(args.db))
    cur = con.cursor()
    cur.execute(
        """
        SELECT lc.id, lc.commit_sha, lc.test_file_path, lc.line_no,
               lc.old_locator, lc.new_locator, lc.framework, rf.instructions
        FROM locator_break lb
        JOIN locator_change lc ON lb.locator_change_id = lc.id
        JOIN reproduce_files rf ON lb.reproduce_files_id = rf.id
        WHERE lc.repository_name = ?
          AND LOWER(lc.framework) = 'playwright'
        ORDER BY lc.id
        """,
        (args.repo,),
    )
    rows = cur.fetchall()
    con.close()
    if args.limit > 0:
        rows = rows[: args.limit]
    print(f"found {len(rows)} koenig × Playwright breaks", file=sys.stderr)

    cache: dict = {}
    manifest: list[dict] = []
    fetched = missing = 0
    t0 = time.time()
    for i, (cid, commit, fpath, line_no, old_loc, new_loc, framework, instr) in enumerate(rows):
        case_dir = args.out / str(cid)
        case_dir.mkdir(parents=True, exist_ok=True)

        content = fetch_github_raw(args.repo, commit, fpath, cache)
        snapshot_path = case_dir / "test_file_snapshot.spec.js"
        line_ctx_path = case_dir / "old_locator_line.txt"
        meta_path = case_dir / "metadata.json"

        if content is None:
            missing += 1
            ctx = ""
            snap_status = "missing"
        else:
            fetched += 1
            snapshot_path.write_text(content, encoding="utf-8")
            ctx = line_context(content, line_no)
            line_ctx_path.write_text(ctx + "\n", encoding="utf-8")
            snap_status = "ok"

        meta = {
            "id": cid,
            "repository": args.repo,
            "framework": framework,
            "commit_sha": commit,
            "test_file_path": fpath,
            "line_no": line_no,
            "old_locator": old_loc,
            "new_locator": new_loc,
            "snapshot_status": snap_status,
            "snapshot_url": f"https://raw.githubusercontent.com/{args.repo}/{commit}/{fpath}",
            "reproduce_instructions": instr,
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        manifest.append(
            {"id": cid, "commit": commit, "file": fpath, "line": line_no, "snapshot_status": snap_status}
        )
        if (i + 1) % 10 == 0 or i + 1 == len(rows):
            print(f"  [{i + 1}/{len(rows)}] ok={fetched} missing={missing} cache={len(cache)} elapsed={time.time() - t0:.1f}s", file=sys.stderr)

    (args.out / "_manifest.json").write_text(
        json.dumps(
            {
                "repository": args.repo,
                "framework": "Playwright",
                "total": len(rows),
                "ok": fetched,
                "missing": missing,
                "unique_files": len(cache),
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "cases": manifest,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\ndone in {time.time() - t0:.1f}s → {args.out}\n  ok={fetched} missing={missing} unique_files={len(cache)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
