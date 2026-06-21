# L1 Intent Labelling — Empirical Report v1

**Date:** 2026-06-14
**Scope:** Layer L1 of the HealReact pipeline — assigning a stable semantic intent label to every interactive UI element in a React component tree, at write-time, offline.
**Status:** pilot-ready on synthetic fixtures. Real-world ReproBreak validation pending.

> This document is the source of truth for L1 design + numbers as of v1. Any future regression must be measured against `tests/fixtures/AllFixtures.gold.json` and reproduce or beat the numbers in §4.

---

## 1. Why L1 exists

HealReact's L3 healer (runtime LLM patch generation) and L4 oracle (behavioural replay) both index test steps by **intent** rather than by raw CSS / XPath selectors. If two intents collide, the L4 oracle cannot tell whether a healed test still exercises the original control; if intents drift, the L2 fallback ladder loses its anchor of last resort.

The L1 design constraint is therefore:

1. **Stability across UI refactors.** An intent should survive a className change, an aria-label rephrase, or a DOM reshuffling — as long as the user-visible function is unchanged.
2. **Local distinguishability.** Two interactive elements in the same `<form>` / `<fieldset>` must get distinct intents whenever they trigger distinct backend effects.
3. **Safety over coverage.** When in doubt, an element must NOT be silently demoted to `non-interactive` (this would make L4 skip a real control).

Constraint 3 is the most expensive one and drives almost every design decision below.

## 2. Pipeline

```
React .tsx files
      │
      ▼  src/ast/extractor.ts   (zero LLM, ts-morph)
LocatorSheet.json  (28 records, anchors only, no intent)
      │
      ├──────────────────────────┬─────────────────────────────┐
      ▼                          ▼                             │
 src/intent/label.ts        src/intent/label.ts                │
 (primary, qwen2.5:3b)      (secondary, qwen2.5-coder:7b)      │
      │                          │                             │
      ▼                          ▼                             │
 intent.json               intent.7b.json                      │
      │                          │                             │
      ▼  calibrate.ts            ▼  calibrate.ts               │
 calibrated.json          calibrated.7b.json                   │
      │                          │                             │
      └──────────┬───────────────┘                             │
                 ▼                                              │
       src/intent/verify_flagged.ts                             │
       (qwen2.5-coder:7b as judge,                              │
        only the UNION of flagged records,                      │
        hard-guard against non-interactive escape)              │
                 │                                              │
                 ▼                                              │
        verified.json  ◀──────── primary intent for             │
                                  non-flagged records           │
                 │                                              │
                 ▼                                              │
              eval_vs_gold.ts  ◀── AllFixtures.gold.json
              (exact / lenient / int-class)
```

All four artifacts live in `tests/fixtures/`. Total wall-clock on M5 Pro 48 GB, all stages combined, for the 28-element evaluation: **~55 s, zero API cost** (local Ollama).

## 3. Calibration rules (final, src/intent/calibrate.ts)

Pure post-processing, deterministic, no LLM call.

| Rule | Trigger | Effect |
| ---- | ------- | ------ |
| A | structural label (`non-interactive`, `structural`, `presentational`) on an interactive element | conf → 0 |
| B | interactive label on a non-interactive element | conf ≤ 0.2 |
| C | intent has < 2 kebab tokens | conf → 0 |
| D | first token not in `ACTION_VERBS` (40-verb list) | conf ≤ 0.4 |
| E | bare `click` | conf → 0 |
| F | intent tokens overlap `{i18nKey, aria-label, testId, dataIntent, text, href}` | +0.1 / overlap (capped at 1.0) |
| G | `submit-*` intent but no `<form>` ancestor | conf − 0.4 |
| H | same intent appears in two structurally-unrelated parent chains | conf − 0.3 |
| I | same `(nearestContainer, intent, elementTag)` appears ≥ 2× → sibling collapse | conf − 0.4 |
| J | intent's noun ∈ `{button, input, form, checkbox, select, link, textbox, field, control, element, div, span, anchor}` OR noun == elementTag | conf − 0.4 |

Rules H–J were the ones added during pilot debugging. Rule I's `elementTag` key part is critical: without it, the legitimate `form(submit-x) + button(submit-x)` pattern triggers a false collapse warning.

## 4. Final numbers (v1)

Gold set: `tests/fixtures/AllFixtures.gold.json` — 28 interactive elements across 3 synthetic fixtures (`SampleCart.tsx`, `SampleNavbar.tsx`, `SampleSettings.tsx`). Frozen 2026-06-14 16:26 CST.

Three match flavours:
- **exact**: predicted intent string is identical to gold.
- **lenient**: same verb prefix AND ≥1 noun-token overlap.
- **int-class**: both predicted and gold either are `non-interactive` or both are not (this is the L1 safety metric).

| sheet | exact | lenient | int-class |
| ----- | ----- | ------- | --------- |
| `intent.json` (3B solo) | 13/28 (46 %) | 16/28 (57 %) | 28/28 (100 %) |
| `calibrated.json` (3B + calibrate) | 13/28 (46 %) | 16/28 (57 %) | 28/28 (100 %) |
| `intent.7b.json` (7B solo) | 17/28 (61 %) | 19/28 (68 %) | 25/28 (89 %) |
| `calibrated.7b.json` (7B + calibrate) | 17/28 (61 %) | 19/28 (68 %) | 25/28 (89 %) |
| **`verified.json` (3B + cal + 7B-verify, hard-guard)** | **17/28 (61 %)** | **20/28 (71 %)** | **28/28 (100 %)** |

Headline takeaways:

1. The **3B+calibrate+7B-verify** path matches 7B-only on exact, wins on lenient, and recovers 100 % interactivity safety.
2. The calibration layer alone does NOT change the intent string (by design — it only adjusts confidence and emits flags), so it is invisible in the exact/lenient columns. Its real value is **routing**: it sends only ~65 % of records (18 / 28 in the latest run) to the 7B verifier, saving ~13 verifier calls.
3. 7B-only has 3 elements wrongly demoted to `non-interactive` (the `save-settings` button, the brand `<a>` link, and a `<div onClick>`). The verifier's hard-guard is the safety net.

## 5. Residual hard errors (6 / 28)

| idx | element | gold | predicted | diagnosis |
| --- | ------- | ---- | --------- | --------- |
| 2 | inner cart `form` | `submit-coupon` | `submit-order` | The form only wraps the coupon input + apply button, but the model lacks the subtree-scope cue. Fix: extractor should record "direct interactive descendants" per form. |
| 5 | `button` apply-coupon | `apply-coupon` | `submit-order` (guard kept primary) | 3B labels it `submit-order`; verifier proposed `non-interactive` and was guard-rescued back to `submit-order`. Verifier needs better noun retrieval here. |
| 7 | `div onClick=quickAdd` | `quick-add-item` | `click-div-button` | Rule J caught the tag-as-noun pattern but verifier still produced one; need to also forbid synthetic compounds. |
| 11 | search `input` | `enter-search-query` | `search-input` | Same as above — `search` is both a verb and a noun, slipped past rule J. |
| 22 | settings `input notifyDigest` | `toggle-weekly-digest` | `toggle-email-notification` | Verifier copy-pasted the sibling's intent (notifyEmail). Need per-record `name` weighting. |
| (2 lenient-only misses count toward 8 lenient errors but not exact misses.) | | | | |

The remaining 5 misses count as `lenient` matches (e.g. `set-quantity` vs `set-cart-quantity`, `remove-item` vs `remove-cart-item`).

## 6. Threats to validity

1. **Synthetic fixtures.** All 28 elements come from three hand-written `.tsx` files we authored ourselves. Pattern bias is inevitable. Real ReproBreak data (next milestone) is the actual test bed.
2. **Single gold author.** v1 gold is agent-proposed + user-accepted in one pass. No inter-annotator agreement available. Three known soft calls documented in `AllFixtures.gold.proposal.json` (`set-cart-quantity` vs `set-quantity`, `create-account` vs `sign-up`, `submit-coupon` vs `submit-order` for the inner form).
3. **Verifier model overlap.** Both `intent.7b.json` and `verify_flagged.ts` use the same `qwen2.5-coder:7b`. Some failure modes may be model-correlated; we cannot distinguish "good calibration routing" from "lucky inter-prompt diversity" until we swap in a different 7B (e.g., `deepseek-r1:7b`).
4. **No accuracy stratification by element kind.** The 28-element set has 7 buttons, 6 inputs, 4 anchors, 3 forms, etc. Real ReproBreak distribution will differ.

## 7. Roadmap

| # | Item | Status | Blocks |
| - | ---- | ------ | ------ |
| 1 | Extend gold to ~150 real ReproBreak elements | TODO (depends on C) | E1 baseline numbers |
| 2 | Inter-annotator agreement (≥2 humans, Cohen's κ) | TODO | publishable accuracy claim |
| 3 | Cross-model verifier ablation (swap 7B-coder for 7B-instruct or 8B-instruct) | TODO | "diversity vs scale" claim |
| 4 | Per-element-class accuracy table | TODO | systematic error analysis |
| 5 | Rule J' (forbid synthetic verb-noun compounds like `click-div-button`) | TODO | should fix idx 7, 11 above |
| 6 | Extractor enrichment: "direct interactive descendants of a form" | TODO | should fix idx 2 above |

---

**File index (this report's claims are reproducible from):**

- `healreact/src/ast/extractor.ts`
- `healreact/src/intent/label.ts`
- `healreact/src/intent/calibrate.ts`
- `healreact/src/intent/verify_flagged.ts`
- `healreact/src/intent/eval_vs_gold.ts`
- `healreact/tests/fixtures/{SampleCart,SampleNavbar,SampleSettings}.tsx`
- `healreact/tests/fixtures/AllFixtures.gold.json` (v1, frozen)
- `healreact/tests/fixtures/AllFixtures.{intent,intent.7b,calibrated,calibrated.7b,verified}.json`

To reproduce §4 numbers, with Ollama serving `qwen2.5:3b` and `qwen2.5-coder:7b` at `localhost:11434`:

```bash
cd healreact
export OPENAI_API_BASE=http://localhost:11434/v1 OPENAI_API_KEY=ollama
npx tsx src/ast/extractor.ts --src tests/fixtures --out tests/fixtures/AllFixtures.LocatorSheet.json
HEALREACT_INTENT_MODEL=qwen2.5:3b        npx tsx src/intent/label.ts          tests/fixtures/AllFixtures.LocatorSheet.json tests/fixtures/AllFixtures.intent.json
HEALREACT_INTENT_MODEL=qwen2.5-coder:7b  npx tsx src/intent/label.ts          tests/fixtures/AllFixtures.LocatorSheet.json tests/fixtures/AllFixtures.intent.7b.json
npx tsx src/intent/calibrate.ts        tests/fixtures/AllFixtures.intent.json    tests/fixtures/AllFixtures.calibrated.json
npx tsx src/intent/calibrate.ts        tests/fixtures/AllFixtures.intent.7b.json tests/fixtures/AllFixtures.calibrated.7b.json
npx tsx src/intent/verify_flagged.ts   tests/fixtures/AllFixtures.calibrated.json tests/fixtures/AllFixtures.calibrated.7b.json tests/fixtures/AllFixtures.verified.json
npx tsx src/intent/eval_vs_gold.ts     tests/fixtures/AllFixtures.gold.json \
    tests/fixtures/AllFixtures.intent.json \
    tests/fixtures/AllFixtures.calibrated.json \
    tests/fixtures/AllFixtures.intent.7b.json \
    tests/fixtures/AllFixtures.calibrated.7b.json \
    tests/fixtures/AllFixtures.verified.json
```
