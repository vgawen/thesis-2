#!/usr/bin/env python3
"""
L3 healer baseline — γ pilot.

For every koenig × Playwright break where the LocatorSheet at the break commit
contains the fix-target element (reach_new = True), present the LLM with:

  1. the broken Playwright selector (old_locator)
  2. ±3 lines of test source around the break
  3. a short list of candidate LocatorSheet records retrieved by lexical overlap
     between the old_locator and the record's anchors (testId / dataAttrs / etc.)

The LLM (default qwen2.5-coder:7b via Ollama) is asked to emit a single new
Playwright selector expression. We then resolve that expression against the
sheet and compare the resolved element to the ground-truth `new_locator`'s
resolved element. Two metrics:

  - exact_element_match: same (componentFile, line) tuple
  - same_file_match:     same componentFile

Usage:
  python heal_baseline.py [--limit N] [--model MODEL]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import urllib.request
import urllib.error

# Import the existing parser/matcher in-process so we don't fork a subprocess per case.
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from resolve_locators import parse_locator_expr, find_matches  # type: ignore

BENCH_ROOT = ROOT.parent / "cases" / "koenig"
API_BASE = os.environ.get("OPENAI_API_BASE", "http://localhost:11434/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "ollama")

SYSTEM_PROMPT = """You are a UI test maintainer. A Playwright selector just stopped finding its target element after a React refactor. You will be shown:
  - the broken selector (OLD)
  - the test source line where it appears (CONTEXT)
  - up to 10 candidate elements from the rendered React tree (CANDIDATES), each with stable anchors

Your job: emit ONE new Playwright selector expression that refers to the SAME functional UI element. Pick the most stable anchor available on the best candidate.

OUTPUT FORMAT (plain text, no JSON, exactly these three lines):
SELECTOR: <playwright expression on one line>
CANDIDATE_IDX: <integer or -1>
RATIONALE: <one short sentence, <= 20 words>

Rules:
  - Prefer data-testid > data-kg-* > role+name > aria-label > id > CSS class. The first available wins.
  - If you use a data-* attribute whose value in the source is a JS expression (shown like {expr}), do NOT include a value: emit `[data-kg-foo]` not `[data-kg-foo="x"]`.
  - Wrap CSS selectors with page.locator('...') unless using getByTestId / getByRole / getByLabel.
  - candidate_idx must point to the candidate you actually used; use -1 only if no candidate fits.
  - Never invent a data-* attribute that does not appear in any candidate.
"""


def chat(model: str, system: str, user: str) -> str:
    body = json.dumps({
        "model": model,
        "temperature": 0,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        j = json.loads(r.read().decode("utf-8"))
    return j["choices"][0]["message"]["content"]


def parse_response(s: str) -> dict:
    """Parse SELECTOR: / CANDIDATE_IDX: / RATIONALE: lines from LLM output."""
    out = {"selector": "", "candidate_idx": -1, "rationale": ""}
    # Strip common code-fence wrapping the LLM sometimes adds.
    s = re.sub(r'^```[a-zA-Z]*\n', '', s, flags=re.MULTILINE)
    s = s.replace('```', '')
    for line in s.splitlines():
        m = re.search(r'SELECTOR\s*:\s*(.+)', line)
        if m and not out["selector"]:
            sel = m.group(1).strip().strip("`").strip()
            # Drop trailing punctuation the model sometimes adds.
            sel = sel.rstrip(".,")
            # If the model returned a bare CSS selector (no Playwright method call),
            # wrap it so the resolver understands it.
            if sel and not re.search(r'(?:locator|\$|getByTestId|getByRole|getByLabel|getByText|getByPlaceholder|querySelector|waitForSelector)\s*\(', sel):
                if sel.startswith('[') or sel.startswith('.') or sel.startswith('#') or sel[:1].isalpha():
                    # Use double-quote outer to allow single quotes inside, or vice versa.
                    if '"' in sel and "'" not in sel:
                        sel = f"page.locator('{sel}')"
                    else:
                        sel = f'page.locator("{sel}")'
            out["selector"] = sel
            continue
        m = re.search(r'CANDIDATE_IDX\s*:\s*(-?\d+)', line)
        if m: out["candidate_idx"] = int(m.group(1)); continue
        m = re.search(r'RATIONALE\s*:\s*(.+)', line)
        if m and not out["rationale"]:
            out["rationale"] = m.group(1).strip()
    return out


def normalize_static_js_string(value: str | None) -> str | None:
    """Return a static string value for literal-like JSX attribute values.

    LocatorSheet may store JSX expression containers such as
    `{'signup-card-content'}`. That is statically recoverable, but arbitrary
    expressions like `{props.testId}` are not safe to rewrite into getByTestId.
    """
    if not value:
        return None
    v = str(value).strip()
    if v.startswith("{") and v.endswith("}"):
        inner = v[1:-1].strip()
        if len(inner) >= 2 and inner[0] == inner[-1] and inner[0] in {"'", '"'}:
            v = inner[1:-1]
        else:
            return None
    if not v or any(ch in v for ch in "\r\n"):
        return None
    return v


def js_string_literal(value: str) -> str:
    """Render a JavaScript string literal for a Playwright selector argument."""
    if "'" not in value and "\\" not in value:
        return f"'{value}'"
    return json.dumps(value)


def build_testid_selector(testid: str | None) -> str | None:
    """Build a syntactically valid getByTestId selector for static testId values."""
    normalized = normalize_static_js_string(testid)
    if normalized is None:
        return None
    return f"page.getByTestId({js_string_literal(normalized)})"


def _first_string_arg_is_syntactically_closed(expr: str) -> bool:
    m = re.search(
        r'(?:locator|\$|getByTestId|getByRole|getByLabel|getByText|getByPlaceholder|'
        r'querySelector|waitForSelector)\s*\(\s*([\'"])',
        expr,
    )
    if not m:
        return False
    quote = m.group(1)
    i = m.end(1)
    escaped = False
    while i < len(expr):
        ch = expr[i]
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == quote:
            rest = expr[i + 1:].lstrip()
            return not rest or rest[0] in {")", ",", "."}
        i += 1
    return False


def is_supported_selector_expr(expr: str) -> bool:
    """Lightweight syntax guard for the Playwright forms this resolver supports."""
    if not expr:
        return False
    if parse_locator_expr(expr).get("strategy") == "unknown":
        return False
    return _first_string_arg_is_syntactically_closed(expr)


def keyword_tokens(loc: str) -> set[str]:
    """Extract data-attribute names + literal string values from a Playwright expr.
    Also split kebab/camel composite values into sub-tokens (e.g. 'media-upload-placeholder'
    yields {media, upload, placeholder}) so retrieval can score by sub-string overlap."""
    toks: set[str] = set()
    for m in re.finditer(r'data-[a-zA-Z0-9-]+', loc):
        toks.add(m.group(0))
    raw_strings: list[str] = []
    for m in re.finditer(r"'([^']{3,80})'", loc):
        raw_strings.append(m.group(1))
    for m in re.finditer(r'"([^"]{3,80})"', loc):
        raw_strings.append(m.group(1))
    for s in raw_strings:
        toks.add(s.lower())
        for sub in re.split(r'[-_/\s]', s):
            if len(sub) >= 3:
                toks.add(sub.lower())
    return toks


def retrieve_candidates(sheet_records: list[dict], old_locator: str, k: int = 15,
                        testid_weight: int = 3) -> list[dict]:
    """Score each record by token overlap with the old_locator, return top-k.

    Scoring (additive):
      +testid_weight for each token that matches the record's testId (exact or substring)
      +2 for each token that matches a dataAttr key
      +2 for each token that matches a dataAttr value
      +1 for each token that matches aria-label / id / className / text / file path
    A token that matches via the testId path is the highest signal for a
    Playwright break: most repairs land back on the same testid family.

    `testid_weight` is the ablation knob for F2: 3 = testId-weighted retrieval
    (v1), 1 = uniform anchor weighting (no special testId boost, the v0 arm).
    """
    needles = keyword_tokens(old_locator)
    scored = []
    for r in sheet_records:
        score = 0
        testid = (r.get("testId") or "").lower()
        da = r.get("dataAttrs") or {}
        da_keys = " ".join(da.keys()).lower()
        da_vals = " ".join(da.values()).lower()
        aria = (r.get("ariaLabel") or "").lower()
        rid = (r.get("id") or "").lower()
        cls = (r.get("className") or "").lower()
        txt = (r.get("text") or "").lower()
        path = (r.get("componentFile") or "").lower()
        for n in needles:
            n = n.lower()
            if testid and (n == testid or n in testid or testid in n):
                score += testid_weight
            if n in da_keys:
                score += 2
            if n in da_vals:
                score += 2
            if n in aria or n in rid or n in cls or n in txt or n in path:
                score += 1
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda x: (-x[0], x[1].get("componentFile") or "", x[1].get("line") or 0))
    return [r for _, r in scored[:k]]


def short_candidate(rec: dict) -> dict:
    da = rec.get("dataAttrs") or {}
    return {
        "tag": rec["elementTag"],
        "componentFile": rec["componentFile"].split("/koenig-lexical/src/")[-1],
        "line": rec["line"],
        "testId": rec.get("testId"),
        "ariaLabel": rec.get("ariaLabel"),
        "role": rec.get("role"),
        "id": rec.get("id"),
        "dataAttrs": da,
        "text": rec.get("text"),
    }


def context_lines(test_file: Path, line_no: int) -> str:
    if not test_file.exists():
        return "(unavailable)"
    lines = test_file.read_text(errors="replace").splitlines()
    lo = max(0, line_no - 1 - 3)
    hi = min(len(lines), line_no + 3)
    out = []
    for i in range(lo, hi):
        marker = ">>" if i + 1 == line_no else "  "
        out.append(f"{marker} {i + 1:4d}| {lines[i]}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="0 = all reachable")
    ap.add_argument("--model", default=os.environ.get("HEALREACT_HEAL_MODEL", "qwen2.5-coder:7b"))
    ap.add_argument("--out", type=Path, default=BENCH_ROOT / "_heal_baseline.json")
    # F2 factorial-ablation knobs (default ON = v1 behaviour, preserves backward compat):
    ap.add_argument("--no-testid-weighting", dest="testid_weighting", action="store_false",
                    help="disable testId x3 retrieval weighting (use uniform anchor weights)")
    ap.add_argument("--no-post-filter", dest="post_filter", action="store_false",
                    help="disable deterministic strong-anchor post-filter (getByTestId rewrite)")
    ap.set_defaults(testid_weighting=True, post_filter=True)
    args = ap.parse_args()
    testid_weight = 3 if args.testid_weighting else 1
    print(f"arm: testid_weighting={args.testid_weighting} post_filter={args.post_filter}",
          file=sys.stderr)

    # Collect (commit, reachable cases) from per-commit resolve JSONs.
    resolves = sorted((BENCH_ROOT / "_src" / "_resolves").glob("*.json"))
    sheets: dict[str, list[dict]] = {}
    all_cases: list[dict] = []
    for rp in resolves:
        rj = json.loads(rp.read_text())
        commit_short = rp.stem
        sheet_path = BENCH_ROOT / "_src" / "_sheets" / f"{commit_short}.LocatorSheet.json"
        if not sheet_path.exists():
            continue
        sheet = json.loads(sheet_path.read_text())
        sheets[commit_short] = sheet["records"]
        for row in rj["rows"]:
            if row["new_hits"] >= 1:
                meta_path = BENCH_ROOT / str(row["id"]) / "metadata.json"
                snap_path = BENCH_ROOT / str(row["id"]) / "test_file_snapshot.spec.js"
                meta = json.loads(meta_path.read_text())
                all_cases.append({
                    "commit": commit_short,
                    "row": row,
                    "meta": meta,
                    "snap_path": snap_path,
                })
    print(f"reachable_new cases: {len(all_cases)}", file=sys.stderr)
    if args.limit:
        all_cases = all_cases[: args.limit]

    results = []
    exact = 0
    same_file = 0
    valid_selector = 0
    t0 = time.time()
    for i, c in enumerate(all_cases, 1):
        meta = c["meta"]
        sheet_records = sheets[c["commit"]]
        candidates = retrieve_candidates(sheet_records, meta["old_locator"], k=10,
                                         testid_weight=testid_weight)
        ctx = context_lines(c["snap_path"], meta["line_no"])
        cand_json = [{"idx": i, **short_candidate(r)} for i, r in enumerate(candidates)]
        user_prompt = (
            f"OLD selector (broken):\n  {meta['old_locator']}\n\n"
            f"CONTEXT (test line ±3):\n{ctx}\n\n"
            f"CANDIDATES:\n{json.dumps(cand_json, indent=2)}\n\n"
            "Emit exactly three lines:\nSELECTOR: <expr>\nCANDIDATE_IDX: <int>\nRATIONALE: <one short sentence>"
        )
        t = time.time()
        try:
            raw = chat(args.model, SYSTEM_PROMPT, user_prompt)
            obj = parse_response(raw)
        except Exception as e:
            results.append({"id": meta["id"], "error": str(e)})
            continue

        proposed = obj.get("selector", "")
        cand_idx = obj.get("candidate_idx", -1)
        guard_note = ""
        # Strict-anchor post-filter: if the model chose a candidate that DOES
        # carry a testId, and the proposed selector is NOT a getByTestId /
        # data-testid lookup, rewrite to use the testId. This enforces the
        # "testId beats aria-label / data-kg-* / class" anchor priority
        # deterministically — the system prompt asks for it but small models
        # routinely drift.
        if args.post_filter and 0 <= cand_idx < len(candidates):
            chosen = candidates[cand_idx]
            chosen_tid = chosen.get("testId")
            normalized_tid = normalize_static_js_string(chosen_tid)
            if chosen_tid and proposed and normalized_tid:
                uses_tid = (f"data-testid=\"{normalized_tid}\"" in proposed
                            or f"data-testid='{normalized_tid}'" in proposed
                            or f"getByTestId('{normalized_tid}')" in proposed
                            or f'getByTestId("{normalized_tid}")' in proposed)
                rewritten = build_testid_selector(chosen_tid)
                if not uses_tid and rewritten:
                    proposed = rewritten
                    guard_note = "strict-anchor: rewrote to getByTestId"
            elif chosen_tid and proposed:
                guard_note = "strict-anchor: skipped dynamic testId"

        # Resolve proposed selector against the sheet.
        prop_target = None
        prop_hits = []
        selector_syntax_valid = is_supported_selector_expr(proposed)
        if proposed and selector_syntax_valid:
            q = parse_locator_expr(proposed)
            prop_hits = find_matches(sheet_records, q)
            if prop_hits:
                prop_target = (prop_hits[0]["componentFile"], prop_hits[0]["line"])
                valid_selector += 1

        # Ground-truth target from new_locator
        gt_q = parse_locator_expr(meta["new_locator"])
        gt_hits = find_matches(sheet_records, gt_q)
        gt_target = (gt_hits[0]["componentFile"], gt_hits[0]["line"]) if gt_hits else None

        is_exact = prop_target is not None and prop_target == gt_target
        is_same_file = prop_target is not None and gt_target is not None and prop_target[0] == gt_target[0]
        if is_exact: exact += 1
        if is_same_file: same_file += 1

        results.append({
            "id": meta["id"],
            "commit": c["commit"],
            "old_locator": meta["old_locator"],
            "new_locator": meta["new_locator"],
            "proposed_selector": proposed,
            "selector_syntax_valid": selector_syntax_valid,
            "candidate_idx": cand_idx,
            "guard_note": guard_note,
            "rationale": obj.get("rationale", ""),
            "proposed_target": prop_target,
            "ground_truth_target": gt_target,
            "exact_match": is_exact,
            "same_file_match": is_same_file,
            "ms": round((time.time() - t) * 1000),
        })
        if i % 5 == 0 or i == len(all_cases):
            elapsed = time.time() - t0
            print(f"  [{i}/{len(all_cases)}] exact={exact}({100*exact/i:.0f}%) sameFile={same_file}({100*same_file/i:.0f}%) validSel={valid_selector} elapsed={elapsed:.0f}s", file=sys.stderr)

    args.out.write_text(json.dumps({
        "model": args.model,
        "n": len(all_cases),
        "exact_match": exact,
        "same_file_match": same_file,
        "valid_selector": valid_selector,
        "elapsed_sec": round(time.time() - t0, 1),
        "rows": results,
    }, indent=2))

    print(f"\n========= SUMMARY =========")
    n = len(all_cases)
    print(f"model: {args.model}")
    print(f"n reachable cases: {n}")
    print(f"exact element match: {exact}/{n} ({100*exact/n:.0f}%)")
    print(f"same-file match: {same_file}/{n} ({100*same_file/n:.0f}%)")
    print(f"valid Playwright selector: {valid_selector}/{n} ({100*valid_selector/n:.0f}%)")
    print(f"\noutput → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
