# ReactHealBench — Schema

Each broken-statement record is one JSONL line under
`breakages/<app>/<commit_pair>/cases.jsonl`.

```jsonc
{
  "case_id": "shopping-cart-001",
  "app": "react-shopping-cart",
  "commit_old": "<sha7>",         // last green
  "commit_new": "<sha7>",         // first red after UI refactor
  "test_file": "tests/e2e/add_to_cart.spec.ts",
  "broken_step": "intent('add-to-cart-button')",
  "breakage_category": "fiber_reparent" | "class_hash_churn" | "i18n_key_change" |
                        "role_change" | "wrapper_div_added" | "tag_swap" |
                        "test_id_renamed" | "propagated",
  "expected_outcome": "heal" | "flag_defect",
  "mutation_id": "shopping-cart-mut-007" | null,   // null = pure UI refactor; non-null = mutation that SHOULD survive heal
  "ground_truth_patch": {
    "kind": "selector_rewrite" | "wait_strategy" | "step_replacement",
    "new_code": "...",
    "rationale": "..."
  } | null,                       // null when expected_outcome=flag_defect
  "stryker_mutation_meta": { ... } | null
}
```

## Construction recipe (Round 1 revision — primary substrate is ReproBreak)

1. **UI-refactor cases**: pull the Cypress/Playwright locator breaks from **ReproBreak** (de Moura et al., arXiv 2605.12158, 449 breaks across 359 repos; github.com/rub-sq/ReproBreak). Filter for `framework=playwright` AND `app uses React`. Carry the `case_id` forward as `reprobreak_case_id` for attribution.
2. **Classification**: tag each break via VISTA taxonomy + 3 React-specific categories (`fiber_reparent`, `class_hash_churn`, `hook_driven`).
3. **Defect-mutant injection**: run `npx stryker run` on each app at `commit_new`.
4. **Mutant filtering (W3 of cross-model review — terminology was self-contradictory in v1; this is the corrected definition):**
   - A mutant is **killed** by a test if that test fails on the mutated app.
   - A mutant is **survived** if it passes the entire test suite.
   - We keep mutants that are:
     - **survived** by the *baseline locator-only* run (so the healer must rely on the behavioural oracle to catch the regression — otherwise it false-heals),
     - AND **killed** by the *original developer-written test suite* at the green baseline (so we know they are non-equivalent real-defect proxies, not dead-code / equivalent mutants).
   - The intersection is what we previously called "stubborn"; that term is **dropped** as ambiguous.
5. For each broken test on `commit_new`, pair with ≥1 such mutant where the test SHOULD stay red (`expected_outcome: flag_defect`).
6. **Manual validation**: blind 20% sample reviewed by two annotators; report Cohen's κ on (i) "UI change is behaviour-preserving" and (ii) "mutant is a real semantic regression".

## Categories of mutation we keep

- Removed event handler (onClick / onSubmit)
- Flipped boolean condition in render
- Swapped sibling order in critical list
- Removed dispatch / state-update call
- Off-by-one in price/quantity computation
