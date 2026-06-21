# EXPERIMENT_PLAN — HealReact

> Claim-driven roadmap. Every block maps to a claim in `FINAL_PROPOSAL.md §6`.

**Compute model**: this is empirical SE research — no GPU training.
"Compute" = LLM-API tokens + a Playwright runner box (1× 8-core CPU
laptop or CI runner is sufficient). Total budget estimate: **≤ $200 in
LLM-API calls** + **≤ 40 wall-hours** of Playwright execution.

---

## Pilot — Round 2 revision (Option B per `EXPERIMENT_PROGRESS.md`)

**Why revised**: The original pilot named `react-shopping-cart` as the app. Inspection during the experiment-bridge phase showed it has only RTL unit tests, **no Playwright/Cypress E2E tests**, so the original pilot could not run. The pivot uses real-world reproduced locator breaks from ReproBreak instead — which also closes Codex Round-2's "benchmark feasibility speculative" concern by working against actual reproduced cases.

**Goal**: validate the pipeline end-to-end on **1 ReproBreak React+Playwright app × N reproduced cases × 3 hand-crafted mutations per case** before scaling.

| Setting | Choice | Rationale |
|---|---|---|
| App | **`tryghost/koenig`** (https://github.com/TryGhost/Koenig) | React-based Ghost editor. **Confirmed via DB query (figshare ReproBreak.db, 2026-06-14): 93 reproduced Playwright locator breaks** — verifiable via `python3 healreact/bench/scripts/reprobreak_subset.py /tmp/healreact_external/ReproBreak`. Small, well-known, real-world test corpus. |
| N (pilot) | First **12** reproduced cases (chronological by `git_commit.commit_date`) | Matches the original pilot's "small but informative" intent; if pilot signal is positive, the remaining 81 cases roll into E1 main. |
| N (main / B1) | All 93 from `tryghost/koenig` + 50 from `microsoft/playwright` test-self-suite = **143 paired cases** | Clears the B1 ≥100-pair target without needing a third app; resolves Codex Round-2's "benchmark feasibility speculative" weakness. |
| Mutations per case | 3 hand-crafted | At least one of each: (a) remove event handler; (b) flip boolean / off-by-one in render path; (c) drop state-update side effect. |
| Substrate setup | Run ReproBreak's `reproduce.py` to materialise the per-case (commit_old, commit_new, test_file, Docker app) tuples; HealReact runs against the materialised Playwright test on `commit_new`. | Reuses ReproBreak's infrastructure; we contribute only the mutation half. |

**Expected pilot signal (unchanged from original):**
- HealReact must successfully repair ≥ 60% of the UI-refactor cases (re-green the test with a verified patch).
- HealReact must flag ≥ 67% of mutation-injected cases as `LIKELY_REAL_DEFECT` (i.e. behavioural-replay oracle catches the regression).
- If both signals absent → return to design (likely L3 prompt engineering or L4 canonicalisation rules).

**Prerequisites for pilot run:**
1. ~~Download `data/ReproBreak.db`~~ **DONE** — `/tmp/healreact_external/ReproBreak/data/ReproBreak.db` (1 GB) present 2026-06-14.
2. ~~Re-run `reprobreak_subset.py`~~ **DONE** — confirmed 93 Playwright reproductions for `tryghost/koenig`; output at `healreact/bench/ReactHealBench/reprobreak_subset.json`.
3. LLM API key configured for HealReact's L3 (e.g. `OPENAI_API_KEY`) — see `healreact/docs/SETUP.md`. User has deferred this decision to pilot-execution time.
4. Implementation of L2 (failure capture), L3 (LLM healer), L4 (oracle) per the 8-week plan (currently skeletons only).
5. Materialise the pilot cases by running ReproBreak's `reproduce.py` against `tryghost/koenig` (Docker-based) — gives us per-case `(commit_old, commit_new, test_file)` tuples to run HealReact against.

**Pilot exit criteria → green-light Stage 2 main runs (E1–E5 + ablations).**

---

## E1 — Main results (C1, C2) — Round 1 revision

| Setting | Details |
|---------|---------|
| Benchmark | `ReactHealBench` = ReproBreak's React/Playwright subset + our paired defect mutants (B1 below) |
| Baselines (added per W2 + missing-prior-work) | (a) raw test no-heal; (b) **Joseph 2026 ten-tier accessibility ladder** (re-implementation, ladder-only no LLM); (c) **TRaf 2025** on the `wait_strategy` sub-class (per-class baseline); (d) WATER (legacy back-compat, via UITestFix); (e) VISTA (legacy back-compat); (f) **Xu+25 adapted reproduction** — declared as "adapted" because Xu used gpt-3.5-turbo on Java Selenium, we run their candidate-list-then-LLM matching on Playwright with parity rules; (g) **LLM-only same-budget baseline** — GPT-4o-mini with raw DOM context, same token budget as HealReact, no ladder/oracle/intent — isolates the contribution of each HealReact layer; (h) Healenium (commercial-class OSS healer) where feasible to integrate; (i) HealReact-ours. |
| Metrics | repair-success-rate, **false-heal-rate** (primary), latency, $/heal |
| Stat test | one-sided proportion test, α=0.05, McNemar paired |
| Runs | 3 seeds for LLM-stochastic baselines, take median |

**Pre-registered:** primary axis is the joint (success ↑, false-heal ↓).
A method that only improves success without reducing false-heal does
NOT support C1+C2.

**Baseline adapter rules (per W2 — must be defined before running):**
- Same input: each baseline receives the same `(broken_test, failing_step, page_at_failure)` triple.
- Same retry budget: max 1 healed attempt per case (no multi-round inner loops, those are an ablation).
- Same per-case wall-clock cap.
- "Adapted reproduction" of Xu+25 explicitly disclosed and ablated against the original Java Selenium setup.

## E2 — Intent-label stability (C3, W1 from self-review) — Round 1 revision

100 hand-crafted *behaviour-preserving* refactors across the 3
benchmark apps. Measure fraction where the intent label of an
affected component remains identical (or equivalent up to a
canonical-form check).

**Threshold (per W2 of Codex review — replaces arbitrary 80%):**
- Pre-register the threshold as the **pilot-derived lower bound** of a 95% CI on stability rate over a 20-refactor pilot subset; the bar is "main-run stability rate ≥ pilot lower bound − 5pp" so we cannot retro-fit the success criterion.
- Define semantic equivalence formally: two labels are equivalent if a blinded human annotator marks them as "same intended user action" with Cohen's κ ≥ 0.7 between two independent annotators on a 30-pair sample.
- Include **adversarial refactors** (role-change but semantically equivalent action, e.g. `<button>` → `<a role="button">`) as a distinct cell.

## E3 — Mutation-filter sensitivity (W2)

Sweep "stubborn-mutant threshold" ∈ {0, 0.25, 0.5, 0.75, 1.0} where
0 = all mutants, 1 = only mutants killed by the entire baseline suite.
Plot false-heal-rate as a function of this threshold. Establishes that
the metric is not an artefact of mutation noise.

## E4 — Behavioural-replay oracle precision & recall (W4 of self-review, W4 of Codex review) — Round 1 revision

Replace "FP on green only" with the proper confusion matrix on **labeled** runs:

- **200 known-green** runs (no UI change, no mutation) — measures false-positive
- **200 known-bug** runs (mutation-injected defects from B1) — measures false-negative (oracle missing the bug)
- Compute precision, recall, F1, and the operating point we ship at.
- **Replace arbitrary ≤2% FP target** with the pilot-derived FP rate's 95% CI as the pre-registered bar; report whether the production setting we ship beats that bar.
- Stratify by canonicalisation class (timestamps redacted / IDs redacted / JWTs redacted / retries collapsed / cache-busting normalised) to expose which class drives each error type.

## E5 — Cost & latency (C4, W6)

Tabulate median + p95 of: (i) LLM-API cost per heal, (ii) wall-clock
per heal, (iii) tokens in / out. Compare across GPT-4o-mini, GPT-4o,
and an open-weight 70B model (DeepSeek-Coder-V2-Instruct, served via
local vLLM, *not* in scope of this session — flag as needs-infra).

---

## Ablations — Round 1 revision

**Important (per W5 of Codex Round-2 review):** A5 (codemod-fairness) and A1 (Joseph-ladder-vs-us) are **prerequisites for E1 validity**, not optional follow-ups; they run alongside E1 in the main results table. A2–A4 still run only after E1 passes.

| ID | Drop | What it tests |
|----|------|--------------|
| A1 | Intent labels (use Joseph-2026-style ladder alone) | **The critical Joseph-2026-vs-us ablation**: does the LLM intent layer actually buy anything when the deterministic ladder is already in place? |
| A2 | Behavioural-replay oracle | how much false-heal control comes from it (vs from intent layer alone) |
| A3 | Fix memory | learning-over-time contribution (demoted from main claim) |
| A4 | Fiber-tree context (DOM-only context) | value of React-aware vs framework-agnostic |
| **A5 (new, per W5 of Codex review)** | `data-intent` codemod (use AST-side-sheet only, no codemod) | Whether writing `data-intent` back into JSX changes the test contract enough to make our vs-baselines comparison unfair |

## B1 — `ReactHealBench` construction — Round 1 revision (extends ReproBreak)

| Step | Detail |
|------|--------|
| Primary substrate | **ReproBreak's React/Playwright subset** (filter the 449-case dataset for `framework=playwright` AND `app uses React`). This gives us the locator-break half for free. |
| Defect-mutant half | For each broken test on `commit_new`, run `Stryker.js` mutation testing on the React app at the same commit. Keep only **survived mutants killed by the original developer-written test suite at `commit_old`** — these are non-equivalent real-defect proxies (Codex W3 terminology fix). |
| Pairs | each broken test paired with: (a) the UI refactor from ReproBreak (heal *should* succeed and produce a verified patch); (b) ≥1 surviving mutant on the same component where the test SHOULD stay red (heal must report `LIKELY_REAL_DEFECT`). |
| Manual validation | sample 20% of cases, blind human label confirms (i) the UI change is behaviour-preserving, (ii) the mutant is a real semantic regression. Report Cohen's κ between two annotators. |
| Defensible size | ReproBreak's React/Playwright subset will be smaller than 449 (filter ratio TBD in pilot); target ≥100 paired (refactor, mutant) cases. Position as "first false-heal-paired benchmark", **not** "first modern locator benchmark" — that title belongs to ReproBreak. |
| Format | JSONL: `{case_id, app, commit_old, commit_new, test_file, broken_step, breakage_category, expected_outcome ∈ {heal, flag_defect}, mutation_id?, ground_truth_patch?, reprobreak_case_id?}` |
| Release | public GitHub repo + Zenodo DOI; artefact-track ready; clearly attributes ReproBreak as upstream. |

---

## Run order (8-week solo timeline)

| Week | Block | Output |
|------|-------|--------|
| 1 | Pilot | go/no-go decision |
| 2 | B1 — bench construction (start) | 30 breakages × 1 app |
| 3 | L1 + L2 implementation | locator ladder + diff |
| 4 | L3 implementation (LLM repair + oracle) | end-to-end repair loop |
| 5 | B1 finish (3 apps) + E2 + E4 | intent stability + oracle FP |
| 6 | E1 main run + E5 cost | tables 1-3 |
| 7 | A1-A4 ablations + E3 mutation sweep | tables 4-5 |
| 8 | `/auto-review-loop` + paper draft | submission-ready |

## What is NOT in scope of this session

- Actual code is not executed in this Stage-1 session. `/experiment-bridge`
  in Stage 2 implements L1–L4, ports the baselines, and runs the
  pilot. Expect that step to take a multi-hour real-infra run.
