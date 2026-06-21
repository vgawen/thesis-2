#!/usr/bin/env python3
"""
Quick stats over bench/cases/koenig/<id>/metadata.json files.

Classifies each break by:
  - selector kind in old_locator and new_locator (testid / aria / role / text / css)
  - change type (testid-rename / kind-shift / value-change / ...)

Outputs a markdown table + a JSON for downstream consumers.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

CASES_DIR = Path(__file__).resolve().parent.parent / "cases" / "koenig"


def classify_kind(loc: str) -> str:
    """Heuristic: which selector strategy does this Playwright expression use?"""
    s = loc.lower()
    if "getbytestid" in s or "data-testid" in s:
        return "testid"
    if "getbyrole" in s:
        return "role"
    if "getbylabel" in s or "aria-label" in s:
        return "aria-label"
    if "getbytext" in s or ".text(" in s or ":text(" in s or ".gettext" in s:
        return "text"
    if "getbyplaceholder" in s or "placeholder" in s:
        return "placeholder"
    if "getbyalt" in s or "alt=" in s:
        return "alt"
    if "data-kg" in s:
        return "data-kg-*"
    if "xpath" in s or s.strip().startswith("//") or "/xpath/" in s:
        return "xpath"
    if any(ch in s for ch in [".", "#", "[", " > "]):
        return "css"
    return "other"


def change_type(old_kind: str, new_kind: str, old: str, new: str) -> str:
    if old_kind == new_kind:
        # same kind but different value: rename
        if old_kind == "testid":
            return "testid-rename"
        if old_kind == "data-kg-*":
            return "data-kg-attribute-rename"
        if old_kind == "css":
            return "css-tweak"
        return f"{old_kind}-value-change"
    return f"{old_kind}→{new_kind}"


def main() -> int:
    metas = sorted(CASES_DIR.glob("*/metadata.json"))
    if not metas:
        print("no cases found; run extract_breaks.py first", file=sys.stderr)
        return 1

    old_kinds: Counter = Counter()
    new_kinds: Counter = Counter()
    transitions: Counter = Counter()
    per_file: Counter = Counter()
    per_commit: Counter = Counter()
    rows = []
    for p in metas:
        m = json.loads(p.read_text())
        ok = classify_kind(m["old_locator"])
        nk = classify_kind(m["new_locator"])
        ct = change_type(ok, nk, m["old_locator"], m["new_locator"])
        old_kinds[ok] += 1
        new_kinds[nk] += 1
        transitions[ct] += 1
        per_file[m["test_file_path"]] += 1
        per_commit[m["commit_sha"][:8]] += 1
        rows.append({"id": m["id"], "old_kind": ok, "new_kind": nk, "change_type": ct,
                     "old": m["old_locator"], "new": m["new_locator"], "file": m["test_file_path"]})

    total = len(metas)
    print(f"\nTotal koenig × Playwright breaks: {total}")
    print(f"Unique test files: {len(per_file)}")
    print(f"Unique commits: {len(per_commit)}\n")

    print("## old_locator selector kind")
    for k, v in old_kinds.most_common():
        print(f"  {k:18s} {v:3d}  ({100*v/total:.0f}%)")
    print("\n## new_locator selector kind")
    for k, v in new_kinds.most_common():
        print(f"  {k:18s} {v:3d}  ({100*v/total:.0f}%)")
    print("\n## change type (old_kind → new_kind)")
    for k, v in transitions.most_common():
        print(f"  {k:30s} {v:3d}  ({100*v/total:.0f}%)")
    print("\n## top 5 test files by # of breaks")
    for k, v in per_file.most_common(5):
        print(f"  {v:3d}  {k}")
    print("\n## breaks per commit (top 5)")
    for k, v in per_commit.most_common(5):
        print(f"  {v:3d}  {k}")

    out = CASES_DIR / "_analysis.json"
    out.write_text(json.dumps({
        "total": total,
        "old_kinds": dict(old_kinds),
        "new_kinds": dict(new_kinds),
        "transitions": dict(transitions),
        "per_file": dict(per_file),
        "per_commit": dict(per_commit),
        "rows": rows,
    }, indent=2))
    print(f"\nfull analysis → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
