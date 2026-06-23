#!/usr/bin/env python3
"""
Resolver sensitivity sweep (F2/validity-threats ask).

The resolver in resolve_locators.py is the de-facto oracle for every
reachable / false-heal / exact-match number in the paper. Two of its
matching decisions are deliberate over-approximations (PERMISSIVE):

  1. dynamic JS attribute values `{expr}` are treated as MAY-match;
  2. non-tag ancestor constraints in compound CSS are confirmed via a
     best-effort same-file join (parentChain only carries tags).

This script recomputes koenig new_locator reachability under BOTH the
PERMISSIVE (current paper) and a STRICT assumption (both over-approximations
disabled), entirely offline from the already-extracted per-commit sheets and
the case metadata — no re-clone, no extractor, no LLM.

It also reports, per mode:
  - reachable_new / N
  - multi-match cases (>=2 sheet hits for new_locator) — resolver ambiguity
  - unresolved cases (0 hits)

Reads:  bench/cases/koenig/_src/_resolves/*.json   (commit list)
        bench/cases/koenig/_src/_sheets/<short>.LocatorSheet.json
        bench/cases/koenig/<id>/metadata.json
Writes: bench/cases/koenig/_resolver_sensitivity.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from resolve_locators import parse_locator_expr, find_matches  # type: ignore

BENCH = ROOT.parent / "cases" / "koenig"


def sweep() -> dict:
    resolves = sorted((BENCH / "_src" / "_resolves").glob("*.json"))
    modes = {"permissive": False, "strict": True}
    agg = {m: {"reach_new": 0, "reach_old": 0, "multi_new": 0, "unresolved_new": 0}
           for m in modes}
    n = 0
    flipped_ids: list[int] = []  # reachable under permissive, unreachable under strict

    for rp in resolves:
        short = rp.stem
        sheet_path = BENCH / "_src" / "_sheets" / f"{short}.LocatorSheet.json"
        if not sheet_path.exists():
            continue
        records = json.loads(sheet_path.read_text())["records"]
        rj = json.loads(rp.read_text())
        for row in rj["rows"]:
            idd = row["id"]
            meta_path = BENCH / str(idd) / "metadata.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text())
            qo = parse_locator_expr(meta["old_locator"])
            qn = parse_locator_expr(meta["new_locator"])
            n += 1
            reach_new_by_mode = {}
            for m, strict in modes.items():
                ho = find_matches(records, qo, strict=strict)
                hn = find_matches(records, qn, strict=strict)
                if ho:
                    agg[m]["reach_old"] += 1
                if hn:
                    agg[m]["reach_new"] += 1
                    if len(hn) >= 2:
                        agg[m]["multi_new"] += 1
                else:
                    agg[m]["unresolved_new"] += 1
                reach_new_by_mode[m] = bool(hn)
            if reach_new_by_mode["permissive"] and not reach_new_by_mode["strict"]:
                flipped_ids.append(idd)

    out = {"n_breaks": n, "modes": agg, "flipped_perm_to_strict": sorted(flipped_ids)}
    return out


def main() -> int:
    out = sweep()
    n = out["n_breaks"]
    print(f"n breaks: {n}")
    for m, d in out["modes"].items():
        rn = d["reach_new"]
        pct = 100 * rn / n if n else 0
        print(f"  [{m:10}] reach_new={rn}/{n} ({pct:.1f}%)  "
              f"multi_match={d['multi_new']}  unresolved={d['unresolved_new']}")
    print(f"  flipped permissive->strict (lost reachability): "
          f"{len(out['flipped_perm_to_strict'])} -> {out['flipped_perm_to_strict']}")
    out_path = BENCH / "_resolver_sensitivity.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"output -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
