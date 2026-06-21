# Auto-Review Round 3 — HealReact Pilot (C-static + L3 v1)

**Reviewer:** Codex MCP (gpt-5.2-codex, high reasoning)
**Date:** 2026-06-14
**Stage under review:** pilot results on real-world data (ReproBreak × tryghost/koenig, L1 reachability + L3 healer v1)
**Score:** 6.8 / 10 — verdict: **almost**
**Δ vs Round 2:** +0.6 (5.5 → 6.2 → 6.8)

---

## Score (0-10) and verdict

6.8/10, verdict: almost.

The project is now beyond "promising idea" and has a credible real-data pilot: 93 reproduced Playwright locator breaks from `tryghost/koenig`, 19 commits, local models, and a measurable L1→L3 pipeline. The 58/93 = 62.4% full-dataset repair proxy is a meaningful first number.

But this is still pilot-level for ICSE/FSE/ISSTA/ASE. The key missing step is executable validation: the current "end-to-end repair" number is resolver-based exact-element agreement, not "patched test passes and does not mask a defect." For a full conference paper, I would need at minimum: one additional real app, a direct baseline comparison, and Docker/ReproBreak replay showing pass/fail plus false-heal behavior.

## What got materially better since Round 2

1. Benchmark feasibility is no longer speculative — 93 real koenig breaks across 19 commits, extracted from ReproBreak rather than hand-authored mutations.
2. Extractor learned a real lesson: `data-kg-*` and custom anchor-bearing React components are first-class. The story is now empirically grounded in modern React code.
3. Honest L1/L3 decomposition: 75/93 reachable statically, then 58/75 repaired by L3 top-1. Much more reviewable than a single opaque repair-success claim.
4. L3 v1 retrieval + strict-anchor change is a good engineering signal: 53→58 / 75 with zero regressions and lower runtime. Exactly the kind of small, inspectable mechanism reviewers trust more than "the LLM got better."

## Strongest remaining weaknesses (rank ordered)

1. **"End-to-end repair" is not end-to-end.** It is exact-element match under `resolve_locators.py`. No Playwright execution, no app replay, no assertion outcome, no check that the repaired selector survives the real runtime DOM.
2. **Main novelty depends on L2/L4** (behavioural-replay oracle, mutation-grounded false-heal), but the pilot evaluates L1 reachability + lightweight L3 selector generator. L2/L4 remain unevaluated though they are the strongest differentiators in FINAL_PROPOSAL.
3. **Single-app evidence is fragile.** Koenig has a distinctive anchor ecology (`data-kg-*` dominates). Reviewer will ask whether HealReact learns Koenig conventions rather than a general React/Playwright repair strategy.
4. **L1 intent labelling is only supported on synthetic fixtures.** The real koenig pilot mostly validates anchor reachability, not semantic intent stability. Don't overclaim "intent-aware" benefits unless real elements get labelled and evaluated.
5. **The evaluator contains nontrivial approximations.** `resolve_locators.py` over-approximates ancestor matching, treats dynamic attribute expressions as may-match, compares the first resolved hit. Reasonable for triage but too permissive for final correctness claims.

## Specific things to do BEFORE writing the paper (≤5)

1. **Run ReproBreak/Docker replay for the 58 predicted repairs**: report patched test pass rate, timeout/failure rate, and mismatches between resolver success and runtime success.
2. Add **one second React+Playwright app** (e.g. `microsoft/playwright` self-suite subset).
3. Implement a **direct baseline**: Joseph-style runtime ladder, raw Playwright locator alternatives, and a no-AST LLM prompt using only failing-test context.
4. **False-heal evaluation on a small paired mutant set.** Even 20 carefully curated mutants would substantiate the paper's core anti-false-heal motivation.
5. **Freeze evaluation scripts** and audit `resolve_locators.py` assumptions with manually inspected samples, especially cases with multiple candidate hits.

## Suggested next experiment (one shot, highest ROI)

Take the 58 v1 "correct" repairs and **run actual Playwright replay in the ReproBreak materialized environment.** Measure: patched test passes, patched test still targets the intended element, cases where resolver-exact success fails at runtime.

Highest ROI because it converts the current strongest number from a static proxy into a publishable repair-success metric, and will reveal whether the resolver is optimistic, whether strict-anchor rewrites are runtime-safe, and whether Koenig's dynamic Lexical DOM creates hidden failures not visible in the LocatorSheet.

## Honesty audit

- **"End-to-end repair correctness"** smells oversold. Use "static repair proxy" or "exact target agreement" until Playwright replay passes.
- **"L1 static reachability ceiling 98%"** is too strong. The later log corrects the headline to 80.6% after an off-by-one bug. Keep the corrected number prominent; retire 85%/98% unless revalidated.
- **"Real-world data"** is true, but **"real-world generality"** is not yet shown. One app with a strong project-specific locator convention.
- **"Intent-aware repair"** not yet demonstrated on real data. L3 prompt uses anchors + lexical retrieval, not clearly L1 semantic intent labels.
- **"Zero API cost"** is fair as engineering result but should not distract from accuracy / validation gaps.
