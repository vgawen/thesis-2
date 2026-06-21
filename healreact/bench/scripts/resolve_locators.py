#!/usr/bin/env python3
"""
Best-effort Playwright selector → LocatorSheet matcher.

For each koenig break case at commit C with locator sheet C/LocatorSheet.json,
parse old_locator and new_locator and report:

  - reachable_old:    does at least one sheet record satisfy old_locator's constraints?
  - reachable_new:    same for new_locator
  - candidate_count_old / _new
  - top_match_old / _new (sheet record key)

This is L1's coverage proxy: if reachable_new is False on most breaks, L1 is
blind to the fix target and HealReact's L3 healer can't even propose a patch.

Handles three common forms:
  page.locator('CSS')              → CSS selector
  page.$('CSS')                    → CSS selector (alias)
  page.getByTestId('foo')          → testId == 'foo'
  page.getByRole('role', {name:X}) → role+name
  page.getByLabel('X')             → aria-label match

Compound CSS like '[data-kg-card-toolbar="html"] [data-testid="edit-html"]' is
split into a chain of constraints applied via parentChain ancestor check.

Usage:
    python resolve_locators.py [--cases-dir DIR] [--sheet-glob GLOB]
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "cases" / "koenig"


# ---------- selector parsing ----------

# Quote-aware first-arg extractor: matches '…' or "…" or `…` where the inner
# content can contain the OTHER quote type. Captures the inner string only.
def _first_arg(method_re: str, src: str) -> str | None:
    m = re.search(method_re + r"\(\s*(?:'([^']*)'|\"([^\"]*)\"|`([^`]*)`)", src)
    if not m:
        return None
    return m.group(1) or m.group(2) or m.group(3)


ATTR_RE = re.compile(r'\[([a-zA-Z_:-]+)(?:([=~|^$*]?=)"([^"]*)")?\]')


def split_compound_css(css: str) -> list[str]:
    """Split 'A B C' (descendant combinator) into ['A','B','C']. We ignore
    > + ~ for now — koenig breaks don't seem to use them."""
    # Tokenize respecting [..."..."]
    parts: list[str] = []
    buf = ""
    depth = 0
    for ch in css:
        if ch == "[":
            depth += 1; buf += ch
        elif ch == "]":
            depth -= 1; buf += ch
        elif ch == " " and depth == 0:
            if buf.strip():
                parts.append(buf.strip())
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf.strip())
    return parts


def parse_simple_css(token: str) -> dict:
    """Parse a single simple selector like 'div[data-x="y"].foo#bar' into constraints."""
    c = {"tag": None, "id": None, "classes": [], "attrs": {}}
    # tag at start (lowercase) or *
    m = re.match(r'^[*a-zA-Z][a-zA-Z0-9-]*', token)
    if m:
        c["tag"] = m.group(0)
        token = token[m.end():]
    while token:
        if token.startswith("#"):
            m = re.match(r'#([a-zA-Z][\w-]*)', token)
            if m: c["id"] = m.group(1); token = token[m.end():]; continue
        if token.startswith("."):
            m = re.match(r'\.([a-zA-Z][\w-]*)', token)
            if m: c["classes"].append(m.group(1)); token = token[m.end():]; continue
        if token.startswith("["):
            m = re.match(r'\[([a-zA-Z_:-]+)(?:([=~|^$*]?=)"?([^"\]]*)"?)?\]', token)
            if m:
                attr, op, val = m.group(1), m.group(2), m.group(3)
                c["attrs"][attr] = (op or "=", val or "")
                token = token[m.end():]; continue
        break
    return c


def parse_locator_expr(expr: str) -> dict:
    """Return a query dict with keys: chain (list of constraint dicts), strategy (str)."""
    expr = expr.strip().rstrip(";)")
    v = _first_arg(r'getByTestId', expr)
    if v is not None:
        return {"strategy": "testid", "value": v, "chain": [{"attrs": {"data-testid": ("=", v)}}]}
    v = _first_arg(r'getByRole', expr)
    if v is not None:
        c = {"attrs": {"role": ("=", v)}}
        mn = re.search(r'name\s*:\s*(?:\'([^\']*)\'|"([^"]*)")', expr)
        if mn:
            c["name"] = mn.group(1) or mn.group(2)
        return {"strategy": "role", "value": v, "chain": [c]}
    v = _first_arg(r'getByLabel', expr)
    if v is not None:
        return {"strategy": "label", "value": v, "chain": [{"name": v}]}
    v = _first_arg(r'getByPlaceholder', expr)
    if v is not None:
        return {"strategy": "placeholder", "value": v, "chain": [{"attrs": {"placeholder": ("=", v)}}]}
    v = _first_arg(r'getByText', expr)
    if v is not None:
        return {"strategy": "text", "value": v, "chain": [{"text": v}]}
    v = _first_arg(r'(?:locator|\$|querySelector(?:All)?|waitForSelector)', expr)
    if v is not None:
        tokens = split_compound_css(v)
        return {"strategy": "css", "value": v, "chain": [parse_simple_css(t) for t in tokens]}
    return {"strategy": "unknown", "value": expr, "chain": []}


# ---------- matching ----------

def record_matches_constraint(rec: dict, c: dict) -> bool:
    if c.get("tag") and c["tag"] != "*" and c["tag"].lower() != rec.get("elementTag", "").lower():
        return False
    if c.get("id") and c["id"] != (rec.get("id") or ""):
        return False
    if c.get("classes"):
        rec_classes = (rec.get("className") or "").split()
        for cls in c["classes"]:
            if cls not in rec_classes:
                return False
    if c.get("attrs"):
        for k, (op, v) in c["attrs"].items():
            present = False
            got = ""
            if k == "data-testid":
                got = rec.get("testId") or ""
                present = bool(rec.get("testId"))
            elif k == "aria-label":
                got = (rec.get("ariaLabel") or "").strip('"\'{}')
                present = bool(rec.get("ariaLabel"))
            elif k == "role":
                got = rec.get("role") or ""
                present = bool(rec.get("role"))
            elif k == "placeholder":
                got = rec.get("placeholder") or ""
                present = bool(rec.get("placeholder"))
            elif k == "id":
                got = rec.get("id") or ""
                present = bool(rec.get("id"))
            else:
                da = rec.get("dataAttrs") or {}
                if k in da:
                    got = da[k]
                    present = True
            # Bare [attr] (no value): only presence required.
            if op == "=" and v == "":
                if not present:
                    return False
                continue
            if not present:
                return False
            # Dynamic JS expression attribute values like `{isSelected}` /
            # `{props.color}` cannot be evaluated statically. We treat them as
            # "this attribute MAY take the selector's value at runtime", which
            # is the most useful approximation for L1 reachability.
            got_stripped = got.strip()
            if got_stripped.startswith("{") and got_stripped.endswith("}"):
                continue
            if op == "=" and got != v:
                return False
            if op == "^=" and not got.startswith(v):
                return False
            if op == "$=" and not got.endswith(v):
                return False
            if op == "*=" and v not in got:
                return False
    if c.get("name"):
        # for getByRole({name:X}) and getByLabel(X) — match against accessible-name evidence
        nm = c["name"]
        for fld in ("ariaLabel", "text", "placeholder"):
            v = (rec.get(fld) or "")
            if nm in v:
                return True
        # also accept matching i18n key tail
        ik = rec.get("i18nKey") or ""
        if nm.lower() in ik.lower():
            return True
        return False
    return True


def matches_chain(rec: dict, all_recs: list[dict], chain: list[dict]) -> bool:
    if not chain:
        return False
    # Last constraint applies to rec itself.
    if not record_matches_constraint(rec, chain[-1]):
        return False
    # Earlier constraints must each match SOME ancestor in record's parentChain
    # (we only have tags in parentChain, not full ancestor records — best-effort).
    ancestors = list(reversed(rec.get("parentChain") or []))
    for c in chain[:-1]:
        # ancestor must satisfy this constraint; we only have ancestor tags, so
        # if the constraint specifies just a tag we can check; otherwise we
        # over-approximate: accept if there is ANY record in the same file whose
        # anchors satisfy c (best-effort cross-record join).
        if c.get("tag") and not c.get("attrs") and not c.get("classes") and not c.get("id"):
            if not any(a == c["tag"] for a in ancestors):
                return False
            continue
        # Best-effort: scan all records in the same component file for an ancestor candidate.
        same_file = [r for r in all_recs if r.get("componentFile") == rec.get("componentFile") and r is not rec]
        if not any(record_matches_constraint(r, c) for r in same_file):
            return False
    return True


def find_matches(sheet_records: list[dict], query: dict, max_n: int = 5) -> list[dict]:
    hits = []
    for r in sheet_records:
        if matches_chain(r, sheet_records, query["chain"]):
            hits.append(r)
            if len(hits) >= max_n:
                break
    return hits


# ---------- main ----------

def main() -> int:
    import argparse as _ap
    ap = _ap.ArgumentParser()
    ap.add_argument("--commit", required=True, help="full commit sha to resolve against")
    ap.add_argument("--sheet", type=Path, default=None, help="LocatorSheet.json path (auto-derived if omitted)")
    ap.add_argument("--out", type=Path, default=None, help="output JSON (auto-derived if omitted)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    target_commit = args.commit
    short = target_commit[:8]
    sheet_path = args.sheet or (ROOT / "_src" / f"koenig-{short}" / "LocatorSheet.json")
    out_path = args.out or (ROOT / f"_resolve_{short}.json")
    if not sheet_path.exists():
        print(f"ERROR: {sheet_path} not found", file=sys.stderr)
        return 2
    sheet = json.loads(sheet_path.read_text())
    sheet_records = sheet["records"]
    if not args.quiet:
        print(f"loaded {len(sheet_records)} records from {sheet_path}")

    cases = sorted([p for p in ROOT.glob("*/metadata.json")])
    cases = [p for p in cases if json.loads(p.read_text())["commit_sha"] == target_commit]
    if not args.quiet:
        print(f"resolving {len(cases)} breaks at commit {short}")

    rows = []
    reach_old = reach_new = 0
    strat_old = Counter()
    strat_new = Counter()
    for p in cases:
        m = json.loads(p.read_text())
        qo = parse_locator_expr(m["old_locator"])
        qn = parse_locator_expr(m["new_locator"])
        ho = find_matches(sheet_records, qo)
        hn = find_matches(sheet_records, qn)
        strat_old[qo["strategy"]] += 1
        strat_new[qn["strategy"]] += 1
        if ho: reach_old += 1
        if hn: reach_new += 1
        rows.append({
            "id": m["id"],
            "file": m["test_file_path"],
            "old_strategy": qo["strategy"], "old_value": qo["value"], "old_hits": len(ho),
            "old_top": (f"{ho[0]['componentFile']}:{ho[0]['line']}" if ho else None),
            "new_strategy": qn["strategy"], "new_value": qn["value"], "new_hits": len(hn),
            "new_top": (f"{hn[0]['componentFile']}:{hn[0]['line']}" if hn else None),
        })

    n = len(cases)
    if not args.quiet:
        print(f"\nresult summary on {n} breaks:")
        print(f"  reachable old: {reach_old}/{n}")
        print(f"  reachable new: {reach_new}/{n}")
        print(f"  old strategy mix: {dict(strat_old)}")
        print(f"  new strategy mix: {dict(strat_new)}")
    out_path.write_text(json.dumps({
        "commit": target_commit, "sheet_records": len(sheet_records),
        "breaks_tested": n, "reachable_old": reach_old, "reachable_new": reach_new,
        "rows": rows,
    }, indent=2))
    if not args.quiet:
        print(f"  full results → {out_path}")
        misses = [r for r in rows if r["new_hits"] == 0][:5]
        if misses:
            print(f"\nFirst {len(misses)} unreachable-new misses:")
            for r in misses:
                print(f"  id={r['id']:4d}  strat={r['new_strategy']:10s}  value={r['new_value'][:80]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
