#!/usr/bin/env python3
"""
L4 false-heal probe (Round-3 reviewer ask #4 — minimum-viable variant).

For every reachable-new koenig case we already have a heal_baseline v1 prediction.
This probe re-runs the L3 healer with the SAME prompt and SAME retrieval, but
with the ground-truth target ELEMENT REMOVED from both the candidate set AND
the underlying LocatorSheet (so the model literally cannot select it).

Outcomes we care about:
  - abstain      : model emits CANDIDATE_IDX=-1 or empty SELECTOR. CORRECT behaviour.
  - false-heal   : model emits a valid selector that the resolver maps to a
                   non-gt element. This is the BAD case — the healer would
                   silently paper over a real UI change with a wrong selector,
                   masking the underlying defect.
  - unresolved   : model emits a selector the resolver cannot resolve at all.
                   Counted separately — not a false heal but still a noisy
                   fail. Better than false-heal because a runtime would catch it.

Headline metric: false-heal rate = false_heal / (false_heal + abstain + unresolved).
Lower is better. Anything <20% is a meaningful anti-false-heal signal for the paper.

Reads:   bench/cases/koenig/_heal_baseline.json   (v1 reachable cases + sheet/commit map)
Writes:  bench/cases/koenig/_false_heal_probe.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv as _load_dotenv
except ImportError:
    _load_dotenv = None

# Reuse the healer's plumbing — same model, same prompt, same retrieval.
ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent.parent


def load_project_dotenv(env_path: Path | None = None) -> bool:
    """Load healreact/.env without overriding variables already exported by the shell."""
    if _load_dotenv is None:
        return False
    return _load_dotenv(env_path or (PROJECT_ROOT / ".env"), override=False)


load_project_dotenv()
sys.path.insert(0, str(ROOT))
from heal_baseline import (  # type: ignore
    SYSTEM_PROMPT, chat, parse_response, retrieve_candidates,
    short_candidate, context_lines, BENCH_ROOT,
)
from resolve_locators import parse_locator_expr, find_matches  # type: ignore

MODEL = os.environ.get("HEALREACT_HEAL_MODEL", "qwen2.5-coder:7b")

# Abstain-encouraging system prompt: explicitly tells the model that "no fit"
# is a valid, expected, often-correct answer. This is the L4-flavoured prompt
# variant — paper-claim equivalent of "even before runtime oracle, soft-prompted
# abstention cuts the silent false-heal rate by X%".
ABSTAIN_PROMPT = SYSTEM_PROMPT + """

CRITICAL — ABSTAIN GUARDRAIL:
  If NO candidate is a clear semantic match for the broken selector (i.e. you
  would have to guess at an anchor, invent an attribute, or pick a structurally
  similar but functionally different element), you MUST abstain:

      SELECTOR:
      CANDIDATE_IDX: -1
      RATIONALE: no candidate is a confident match — refusing to heal blindly.

  A blind heal that silently rewrites the test against the wrong element is
  ALWAYS worse than abstention. The downstream layer can re-prompt with more
  context or escalate to human review. Abstention is the safe default.
  Choose -1 unless the right answer is OBVIOUS.
"""


def load_heal_baseline() -> tuple[list[dict], dict[str, list[dict]]]:
    """Recover (reachable cases, sheets-by-commit) the same way heal_baseline does."""
    resolves = sorted((BENCH_ROOT / "_src" / "_resolves").glob("*.json"))
    sheets: dict[str, list[dict]] = {}
    cases: list[dict] = []
    for rp in resolves:
        rj = json.loads(rp.read_text())
        commit_short = rp.stem
        sheet_path = BENCH_ROOT / "_src" / "_sheets" / f"{commit_short}.LocatorSheet.json"
        if not sheet_path.exists():
            continue
        sheets[commit_short] = json.loads(sheet_path.read_text())["records"]
        for row in rj["rows"]:
            if row["new_hits"] >= 1:
                meta_path = BENCH_ROOT / str(row["id"]) / "metadata.json"
                snap_path = BENCH_ROOT / str(row["id"]) / "test_file_snapshot.spec.js"
                cases.append({
                    "commit": commit_short,
                    "row": row,
                    "meta": json.loads(meta_path.read_text()),
                    "snap_path": snap_path,
                })
    return cases, sheets


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", choices=["vanilla", "abstain"], default="vanilla",
                    help="vanilla = same prompt as heal_baseline; abstain = explicit ABSTAIN guardrail")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    system_prompt = ABSTAIN_PROMPT if args.prompt == "abstain" else SYSTEM_PROMPT
    out_path = args.out or (BENCH_ROOT / f"_false_heal_probe_{args.prompt}.json")

    cases, sheets = load_heal_baseline()
    print(f"reachable_new cases: {len(cases)} | prompt={args.prompt}", file=sys.stderr)

    out: list[dict] = []
    abstain = false_heal = unresolved = error = 0
    t0 = time.time()

    for i, c in enumerate(cases, 1):
        meta = c["meta"]
        sheet_records = sheets[c["commit"]]

        gt_q = parse_locator_expr(meta["new_locator"])
        gt_hits = find_matches(sheet_records, gt_q)
        if not gt_hits:
            # shouldn't happen for reach_new cases, skip defensively
            continue
        gt_target = (gt_hits[0]["componentFile"], gt_hits[0]["line"])

        # Build a poisoned sheet: drop every record matching the gt_target tuple.
        poisoned = [r for r in sheet_records
                    if (r["componentFile"], r["line"]) != gt_target]

        candidates = retrieve_candidates(poisoned, meta["old_locator"], k=10)
        ctx = context_lines(c["snap_path"], meta["line_no"])
        cand_json = [{"idx": j, **short_candidate(r)} for j, r in enumerate(candidates)]
        user_prompt = (
            f"OLD selector (broken):\n  {meta['old_locator']}\n\n"
            f"CONTEXT (test line ±3):\n{ctx}\n\n"
            f"CANDIDATES:\n{json.dumps(cand_json, indent=2)}\n\n"
            "Emit exactly three lines:\nSELECTOR: <expr>\nCANDIDATE_IDX: <int>\nRATIONALE: <one short sentence>"
        )

        try:
            raw = chat(MODEL, system_prompt, user_prompt)
            obj = parse_response(raw)
        except Exception as e:
            error += 1
            out.append({"id": meta["id"], "error": str(e)})
            continue

        proposed = obj.get("selector", "").strip()
        cand_idx = obj.get("candidate_idx", -1)

        # Decision tree
        if not proposed or cand_idx == -1:
            verdict = "abstain"
            abstain += 1
            resolved_target = None
        else:
            hits = find_matches(poisoned, parse_locator_expr(proposed))
            if not hits:
                verdict = "unresolved"
                unresolved += 1
                resolved_target = None
            else:
                resolved_target = (hits[0]["componentFile"], hits[0]["line"])
                # By construction the gt is gone, so any resolved hit is wrong.
                # If the resolved hit's file is the same file as gt, call it a
                # "near miss" inside false_heal — still a false heal.
                verdict = "false_heal"
                false_heal += 1

        out.append({
            "id": meta["id"],
            "commit": c["commit"],
            "old_locator": meta["old_locator"],
            "gt_new_locator": meta["new_locator"],
            "gt_target": gt_target,
            "proposed_selector": proposed,
            "candidate_idx": cand_idx,
            "rationale": obj.get("rationale", ""),
            "resolved_target": resolved_target,
            "verdict": verdict,
        })

        if i % 5 == 0 or i == len(cases):
            tot = abstain + false_heal + unresolved
            rate = (false_heal / tot * 100.0) if tot else 0.0
            print(f"  [{i}/{len(cases)}] abstain={abstain} false_heal={false_heal} "
                  f"unresolved={unresolved} error={error} false_heal_rate={rate:.1f}%",
                  file=sys.stderr)

    elapsed = time.time() - t0
    tot = abstain + false_heal + unresolved
    summary = {
        "model": MODEL,
        "prompt_variant": args.prompt,
        "n": len(out),
        "abstain": abstain,
        "false_heal": false_heal,
        "unresolved": unresolved,
        "error": error,
        "false_heal_rate_pct": round((false_heal / tot * 100.0) if tot else 0.0, 1),
        "abstain_rate_pct":   round((abstain   / tot * 100.0) if tot else 0.0, 1),
        "elapsed_sec": round(elapsed, 1),
        "rows": out,
    }
    out_path.write_text(json.dumps(summary, indent=2))
    print()
    print("========= FALSE-HEAL PROBE SUMMARY =========")
    print(f"model              : {MODEL}")
    print(f"n cases            : {len(out)}")
    print(f"abstain (good)     : {abstain} ({summary['abstain_rate_pct']}%)")
    print(f"false_heal (bad)   : {false_heal} ({summary['false_heal_rate_pct']}%)")
    print(f"unresolved (noisy) : {unresolved}")
    print(f"error              : {error}")
    print(f"output -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
