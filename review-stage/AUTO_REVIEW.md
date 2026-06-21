# Auto Review Loop — HealReact (Stage-1 idea-discovery acceptance)

**Started**: 2026-06-14
**Target verdict**: score ≥ 6 AND verdict ∈ {ready, almost}
**Reviewer backend**: Codex MCP (gpt-5.x via project-0-Thesis-codex) — genuine cross-model independent review.
**Difficulty**: medium.

## Round 1 (2026-06-14T05:18Z)

### Assessment (Summary)
- **Score**: 5.5 / 10
- **Verdict**: **not ready**
- **Loop status**: continue (5.5 < 6 AND verdict ∉ {ready, almost})

### Key criticisms
1. **W1 (high, blocks Stage 2)** — Benchmark-novelty axis invalidated by **ReproBreak** (arXiv 2605.12158, May 2026, de Moura et al.), a 449-locator-break dataset for Cypress/Playwright across 359 open-source repos. Our IDEA_REPORT claim "all published benchmarks are 2010s server-rendered" is **factually wrong** as of May 2026.
2. **W2 (high, blocks Stage 2)** — Baselines (WATER / VISTA / Xu+25) are Selenium / legacy-web; comparing them naively on Playwright/React punishes engineering mismatch instead of method quality. Xu+25 "reproduction" is itself a research task (gpt-3.5-turbo, 8,429 API calls, Java Selenium), not a checkbox.
3. **W3 (high, blocks Stage 2)** — False-heal metric is promising but operationally muddled. SCHEMA.md uses **"stubborn / surviving"** inconsistently ("surviving mutants those the existing suite already kills" is self-contradictory). Need clean killed/survived terminology + manual-validation sampling.
4. **W4 (high, no block)** — Behavioural-replay oracle may reject benign UI evolution OR miss semantic bugs because HAR equivalence is brittle under timestamps, IDs, caching, retries, feature flags. Need oracle **precision/recall** against labeled benign+buggy runs, not just FP-on-green.
5. **W5 (med, no block)** — `data-intent` codemod changes the app/test contract → unfair vs unmodified baselines. Need "non-invasive AST sheet only" variant.
6. **W6 (med, no block)** — Scope too broad for a 10-12-page top SE paper: method + benchmark + metric formalisation + CI memory. **Cut CI/memory to artifact track.**

### Verified vs suspicious claims
**Verified by Codex**: our characterisation of Xu+25, that Xu+25 does not report mutation-grounded false-heal as a primary metric, that WATER/VISTA are fair legacy baselines, that healreact/ L1 is real code (not vapourware).

**Suspicious / unverified** (now confirmed by my follow-up WebSearch):
- "No React-native benchmark" → **FALSE**: ReproBreak exists. ✗
- "Only Sun+26 measures regression masking" → too absolute; phrasing unverifiable.
- "Xu+25 public artifact reproducible" → unverified; assume "adapted reproduction" only.
- 80% / 2% thresholds → arbitrary; not justified by pilot or base-rate analysis.

### Missing prior work (all four verified real by follow-up search)
| Paper | Why it bites |
|---|---|
| **ReproBreak** — de Moura et al., arXiv 2605.12158 (May 2026) | Direct benchmark competitor. Must extend it, not replace it. |
| **Joseph 2026** — arXiv 2603.20358 — "Beyond LLM-based test automation: Zero-Cost Self-Healing via DOM Accessibility Tree Extraction" | Ten-tier locator hierarchy (`getByRole → data-testid → ARIA → CSS → text`) very close to our L1 ladder; argues LLM at write-time is unnecessary. Hardest hit on our intent-labeller contribution. |
| **UTFix** — Rahman et al., PACMPL OOPSLA1 2025 (arXiv 2503.14924) | LLM test repair under code evolution (Python unit tests). Adjacent, sets the bar for "context-pack" design. |
| **TRaf** — Pei et al., TOSEM 2025 (DOI 10.1145/3695989, arXiv 2305.08592) | Async-wait repair in web tests. Directly relevant because our L3 includes wait_strategy patches. |

### Scope risk verdict
**HIGH**. Cut to: **"mutation-grounded false-heal evaluation for React/Playwright locator repair + HealReact as reference method, evaluated on a ReproBreak-derived benchmark with defect probes."** CI heal-budget, cross-framework, fix-memory → all appendix / artifact track.

### Reviewer Raw Response

<details>
<summary>Click to expand full Codex response</summary>

```
SCORE: 5.5/10
VERDICT: not ready

VERIFIED CLAIMS:
  - Xu+25 is post-failure element matching plus ChatGPT/global matching and explanation validation: verified. `idea-stage/IDEA_REPORT.md:65`, `refine-logs/FINAL_PROPOSAL.md:93-103`; Xu's paper states it uses prior repair techniques for local matching, ChatGPT for global matching, and an explanation validator. It evaluates Java Selenium web UI repair, not React/Playwright. Source: https://arxiv.org/abs/2312.05778 and ar5iv lines showing setup/results.
  - Xu+25 does not report mutation-grounded false-heal as a primary metric: mostly verified. It reports matching/repair correctness over 139 broken statements and manually validates incorrect/intention-changing repairs, but not regression-masking under injected defects. See Xu result setup and Table 5 discussion in source.
  - VISTA/WATER are fair legacy baselines, but not enough alone: verified. The plan lists WATER/VISTA/Xu+25 baselines at `refine-logs/EXPERIMENT_PLAN.md:35`; Xu itself frames WATER/VISTA as classic web UI repair baselines.
  - The local artifact is not vaporware for L1 only: verified. AST extractor exists and emits role/testId/i18n/parentChain fields in `healreact/src/ast/extractor.ts:168-232`; fixture has 8 extracted records in `healreact/tests/fixtures/LocatorSheet.json:1-5`. L3/oracle are skeletons: `healreact/src/heal/healer.ts:1-12`, `healreact/src/oracle/replay.ts:1-10`.

SUSPICIOUS / UNVERIFIED CLAIMS:
  - "No React-native benchmark / all published benchmarks are 2010s server-rendered apps": now suspicious. ReproBreak, submitted May 12, 2026, provides 449 reproduced locator breaks from Cypress/Playwright projects after analyzing 359 repositories. This directly weakens `idea-stage/IDEA_REPORT.md:38-43`, `idea-stage/IDEA_REPORT.md:84`, and `refine-logs/FINAL_PROPOSAL.md:101`. Source: https://arxiv.org/abs/2605.12158
  - "Only Sun+26 measures regression masking": unverified. The local wiki entry is TODO-heavy and not independently substantiated. The narrow academic web-UI false-heal-primary claim may hold, but the "only paper" phrasing at `idea-stage/IDEA_REPORT.md:32-37` is too absolute.
  - "Xu+25 public artifact, Concordia" is not established in the plan. `refine-logs/EXPERIMENT_PLAN.md:35` assumes reproducibility, but Xu used gpt-3.5-turbo, 8,429 API calls, and old Java Selenium apps; porting to ReactHealBench is a research task, not a baseline checkbox.
  - "Behavioural-replay oracle" is oversold. It is a stub locally and depends on stable/canonicalizable HAR/state traces: `refine-logs/FINAL_PROPOSAL.md:75-79`, `healreact/src/oracle/replay.ts:21-36`.
  - "≥80% intent stability" and "≤2% oracle FP" are arbitrary thresholds unless justified by pilot/base-rate analysis: `refine-logs/FINAL_PROPOSAL.md:128-131`, `refine-logs/EXPERIMENT_PLAN.md:58-62`.

WEAKNESSES (ranked):
  W1. Benchmark novelty was invalidated or at least weakened by ReproBreak (severity: high; blocks Stage 2: yes)
  W2. Baseline plan is under-specified and may be unfair (severity: high; blocks Stage 2: yes)
  W3. False-heal metric is promising but not yet operationally clean (severity: high; blocks Stage 2: yes)
  W4. Behavioural-replay oracle may reject benign UI evolution or miss semantic bugs (severity: high; blocks Stage 2: no, but pilot must test it)
  W5. Intent labels risk becoming another hidden test oracle (severity: med; blocks Stage 2: no)
  W6. Scope is too broad for one top SE paper (severity: med; blocks Stage 2: no)

MISSING PRIOR WORK:
  - ReproBreak: de Moura, Adamietz, Mehboob, Noller, arXiv 2026.
  - Joseph, "Beyond LLM-based test automation: A Zero-Cost Self-Healing Approach Using DOM Accessibility Tree Extraction," arXiv 2026.
  - Ricca, Marchetto, Stocco, "A Multi-Year Grey Literature Review on AI-assisted Test Automation," 2024/2025.
  - UTFix: Rahman et al., OOPSLA 2025.
  - TRaf: Pei, Sohn, Habchi, Papadakis, 2023.
  - FlakyFix: Fatima, Hemmati, Briand, 2023/2024.

SCOPE RISK: high. Keep one paper as "mutation-grounded false-heal evaluation for React/Playwright locator repair + HealReact as reference method." Cut fix-memory, CI heal-budget, and cross-framework ablations from the main claim unless E1 is exceptionally strong. Treat ReactHealBench as an extension of ReproBreak plus defect probes, not a standalone benchmark novelty claim.

METHODOLOGICAL HOLES:
  - E1: Baselines insufficient. Add ReproBreak-compatible baseline, Testing Library/Playwright locator-regeneration baseline, Healenium/commercial baseline, LLM-only repair baseline with the same context budget. Xu+25 must be declared "adapted reproduction."
  - E2: 80% stability arbitrary. Define equivalence, use blinded human labels, report Cohen's kappa, include adversarial refactors.
  - B1: 90 heal cases small against VISTA-733 and ReproBreak-449. Defensible only as curated React+false-heal benchmark.
  - E4: ≤2% oracle FP not evidence-based. Replace with pilot-derived CI; measure both FP and FN.

NEXT STEP: Update Stage-1 literature and experiment plan around ReproBreak, then redesign E1/B1 so ReactHealBench is explicitly a false-heal/React-AST extension benchmark rather than a claimed first modern locator-break benchmark.
```

</details>

### Actions Taken (Phase C — Round 1)
1. Verified all 4 critical missing-prior-work citations via independent WebSearch (ReproBreak, UTFix, TRaf, Joseph 2026) — all real, all matching Codex's description.
2. Ingested 4 new papers into `research-wiki/papers/` with `extends` / `contradicts` edges to existing IDEA-1.
3. Rewrote `idea-stage/IDEA_REPORT.md` §1, §3, §Phase-4 to engage ReproBreak, Joseph 2026, UTFix, TRaf; downgraded benchmark axis; added explicit positioning vs Joseph's 10-tier accessibility ladder.
4. Rewrote `refine-logs/FINAL_PROPOSAL.md` §4 differentiation and §1 scope (cut CI heal-budget + cross-framework + parts of fix-memory from main claim per W6; moved them to "artefact-track / appendix").
5. Rewrote `refine-logs/EXPERIMENT_PLAN.md` §E1 baselines (added Joseph 2026 ladder, Healenium, LLM-only same-budget) and §B1 benchmark construction (extension of ReproBreak rather than from-scratch). Removed arbitrary 80% / 2% thresholds — replaced with "pilot-derived CI".
6. Fixed `healreact/bench/ReactHealBench/SCHEMA.md` killed/survived terminology inconsistency.

### Results
- Wiki: 4 papers added (`demoura2026_reprobreak`, `joseph2026_zerocost_dom_at`, `rahman2025_utfix_oopsla`, `pei2023_traf`).
- Edges: new `contradicts` from IDEA-1 → ReproBreak (on benchmark novelty axis), `extends` from IDEA-1 → Joseph 2026 (on locator ladder), `extends` from IDEA-1 → TRaf (wait-strategy repair sub-component), `extends` from IDEA-1 → UTFix (LLM-context-pack design pattern).
- Documents updated: IDEA_REPORT, FINAL_PROPOSAL, EXPERIMENT_PLAN, SCHEMA.

### Status
- Continuing to Round 2.
- Difficulty: medium.
- Open follow-up (deferred): W5 (intent-codemod ablation) is documented in the plan but not yet rebutted in code; W4 oracle precision/recall plan added but oracle code is still a stub (legitimate — Stage 1 is plan, not execution).

## Round 2 (2026-06-14T05:30Z)

### Assessment (Summary)
- **Score**: 6.2 / 10  (↑ from 5.5)
- **Verdict**: **almost**  (was: not ready)
- **STOP CONDITION MET**: score ≥ 6 AND verdict ∈ {ready, almost}. Loop terminates.

### Reviewer ruling on Round-1 weaknesses
| Weakness | Verdict | Where addressed |
|---|---|---|
| W1 ReproBreak novelty conflict | PARTIAL | `IDEA_REPORT.md:44`, `IDEA_REPORT.md:85`, `FINAL_PROPOSAL.md:113`; stale headline at line 252 → **fixed in cleanup pass** |
| W2 baselines | PARTIAL | `EXPERIMENT_PLAN.md:34` (Joseph + TRaf + LLM-only + Healenium + adapted Xu+25), adapter rules at :44. Remaining gap: Healenium "where feasible" not pinned; Xu+25 parity still imperfect. |
| W3 false-heal terminology | PARTIAL | `SCHEMA.md:33` clean two-condition; stale "stubborn" in `FINAL_PROPOSAL.md:125` and `IDEA_REPORT.md:188` → **fixed in cleanup pass** |
| W4 oracle precision/recall | **RESOLVED** | `EXPERIMENT_PLAN.md:69` — full confusion matrix on labeled green+buggy, stratified by canonicalisation class |
| W5 codemod fairness ablation | PARTIAL | A5 added but listed as post-E1 follow-up; reviewer says fairness affects E1 validity itself → **fixed in cleanup pass: A1 & A5 now run alongside E1** |
| W6 scope narrowing | PARTIAL | Scope narrowed in `FINAL_PROPOSAL.md:18`; L4 CI/fix-memory still occupies architecture text; cross-framework still in risks → **fixed in cleanup pass** |

### New weaknesses introduced by the revision
1. **Internal consistency** — stale "80% threshold", "stubborn mutants", "React-native benchmark" text survives in non-revised sections. → **Addressed in cleanup pass**.
2. **Wiki entries shallow** — `papers/moura2026_reprobreak_dataset_reproducible.md` and `papers/joseph2026_beyond_llmbased_test.md` are mostly TODOs (auto-generated scaffolds from `ingest_paper`). Knowledge base does not yet substantiate the nuanced differentiation claims. → **Deferred follow-up** (use `/wiki-enrich` skill before paper writing begins).
3. **Benchmark feasibility speculative** — the plan targets ≥100 paired cases while admitting the ReproBreak React/Playwright subset size is TBD. → **Deferred to Stage-2 pilot**; pilot exit criterion now explicitly includes "measure ReproBreak React/Playwright subset size".

### Reviewer Raw Response (Round 2)

<details>
<summary>Click to expand full Codex Round-2 response</summary>

```
SCORE: 6.2/10
VERDICT: almost

W1 ReproBreak: PARTIAL — Main framing now correctly treats ReactHealBench as a ReproBreak extension, not a first modern benchmark: idea-stage/IDEA_REPORT.md:44, idea-stage/IDEA_REPORT.md:85, refine-logs/FINAL_PROPOSAL.md:113. But stale headline language still claims a "React-native benchmark" contribution: idea-stage/IDEA_REPORT.md:252.

W2 baselines: PARTIAL — E1 now includes Joseph ladder, TRaf, WATER/VISTA, Xu+25 adapted reproduction, LLM-only same-budget, and Healenium: refine-logs/EXPERIMENT_PLAN.md:34. Adapter rules are improved: refine-logs/EXPERIMENT_PLAN.md:44. Still weak because Healenium is "where feasible" and Xu+25 parity remains under-specified.

W3 false-heal terminology: PARTIAL — SCHEMA now gives clean killed/survived definitions and drops "stubborn": healreact/bench/ReactHealBench/SCHEMA.md:33. But stale terminology remains in proposal/idea text: refine-logs/FINAL_PROPOSAL.md:125, idea-stage/IDEA_REPORT.md:188.

W4 oracle precision/recall: RESOLVED — E4 now uses labeled green and bug runs, computes precision/recall/F1, and stratifies canonicalization failures: refine-logs/EXPERIMENT_PLAN.md:69.

W5 codemod fairness ablation: PARTIAL — A5 adds the required AST-side-sheet/no-codemod ablation: refine-logs/EXPERIMENT_PLAN.md:96. But it is listed under "run only after E1 passes": refine-logs/EXPERIMENT_PLAN.md:88, while fairness affects the validity of E1 itself.

W6 scope: PARTIAL — Scope is narrowed and CI/cross-framework/fix-memory are demoted: refine-logs/FINAL_PROPOSAL.md:18. But L4 CI/fix-memory still occupies architecture text: refine-logs/FINAL_PROPOSAL.md:83, and cross-framework ablation reappears in risks: refine-logs/FINAL_PROPOSAL.md:128.

NEW WEAKNESSES:
  - Internal consistency is now the main blocker: arbitrary 80% thresholds still survive in binding proposal criteria despite E2 replacing them with pilot-derived CI: refine-logs/FINAL_PROPOSAL.md:124, refine-logs/FINAL_PROPOSAL.md:142, versus refine-logs/EXPERIMENT_PLAN.md:57.
  - The wiki ingestion is shallow: ReproBreak and Joseph entries are mostly TODOs, so the knowledge base does not yet substantiate the paper's nuanced differentiation claims: research-wiki/papers/moura2026_reprobreak_dataset_reproducible.md:21, research-wiki/papers/joseph2026_beyond_llmbased_test.md:21.
  - Benchmark feasibility is still speculative: the plan targets ≥100 paired cases while admitting the ReproBreak React/Playwright subset size is TBD: refine-logs/EXPERIMENT_PLAN.md:102, refine-logs/EXPERIMENT_PLAN.md:106.

NEXT STEP: Do a consistency cleanup pass before Stage 2: remove stale benchmark/80%/stubborn language, promote A5 into the main E1 validity design, and add a pilot task that measures the actual ReproBreak React/Playwright subset size before committing to ≥100 paired cases.
```

</details>

### Actions Taken (Phase C — Round 2 cleanup pass)
1. Removed stale "React-native benchmark" headline in `IDEA_REPORT.md` Phase-5 summary.
2. Removed stale "≥80%" pre-registered C3 threshold in `FINAL_PROPOSAL.md`; replaced with pilot-derived CI formula.
3. Removed stale "stubborn / surviving" shorthand in `FINAL_PROPOSAL.md` risks table and `IDEA_REPORT.md` W2 self-review; replaced with the explicit two-condition definition from `SCHEMA.md`.
4. Promoted A5 (codemod-fairness) and A1 (Joseph-ladder vs us) to run alongside E1 as validity prerequisites, not post-E1 follow-ups.
5. Updated risks table in `FINAL_PROPOSAL.md` to reflect the cross-model review's actual findings rather than the legacy self-review framing.

### Status
- **Loop TERMINATED** — STOP CONDITION met.
- Difficulty: medium.
- Total rounds: 2.
- Score progression: 5.5 → 6.2 (verdict: not ready → almost).
- Deferred (non-blocking): wiki-enrich pass on the 4 new papers; pilot task to measure ReproBreak React/Playwright subset size.

---

## Final Summary

Stage-1 idea-discovery is **accepted with conditions** after two rounds of cross-model review against the Codex MCP backend (project-0-Thesis-codex). The initial same-model self-review (6.5/10) was over-optimistic; the cross-model review found one factually wrong claim (benchmark novelty vs ReproBreak), one direct competitor we had missed (Joseph 2026's ten-tier accessibility ladder), and methodological holes in the experiment plan (arbitrary thresholds, terminology inconsistency, missing baselines, missing precision/recall on the oracle).

After patches, the paper plan is now:
- **Defensible novelty (narrowed to 3 axes)**: (1) intent-label layer addressing failure-modes that Joseph's deterministic ladder cannot catch, (2) executable behavioural-replay oracle as commit-gate, (3) mutation-grounded false-heal evaluation methodology.
- **Dropped from headline claims**: first React-native benchmark (ReproBreak got there), generic AST-at-write-time (Joseph proved the deterministic case), CI heal-budget integration (appendix), cross-framework, fix-memory provenance (ablation-only).
- **Pre-registered**: claims C1–C4 with pilot-derived thresholds, full precision/recall on the oracle, baseline-adapter rules, two-condition mutant filtering, blinded annotation for intent-equivalence.

Stage 1 status: `done (cross-model-reviewed; almost-ready; 6.2/10)`.
Stage 2 can begin after the two deferred follow-ups (wiki-enrich, ReproBreak subset measurement) are run as pilot prerequisites.

## Method Description (for `/paper-illustration`)

HealReact is a four-layer pipeline for self-healing React/Playwright E2E tests, designed to maximise repair success while minimising false-heal (regression masking).

- **L1 — Write-time locator pre-generation.** A ts-morph AST walker extracts every interactive JSX element in the React codebase and emits a deterministic locator ladder per element: `getByRole+name → label → testid → data-intent → id → text → href → className-prefix`. The ladder is Joseph-2026-style; HealReact's addition is an LLM-extracted **intent label** (e.g. `submit-order`, `remove-line-item`) baked into a side-channel `LocatorSheet.json` and optionally codemodded back into JSX as `data-intent`. Intent labels disambiguate components whose accessible name is dynamic, duplicated, or i18n-driven — exactly the cases where the deterministic ladder silently picks "first visible" and creates a future false-heal.
- **L2 — Runtime failure capture & causal analysis.** When a Playwright `intent()` call fails or a step times out, the runner captures `{error, DOM snapshot, fiber tree at failure, screenshot, network HAR}`, computes a semantic diff against the last green build's snapshots, and packages a UTFix-style context pack (static AST slice + dynamic Fiber slice + failure message).
- **L3 — LLM closed-loop healer.** The healer first queries an in-process fix-memory keyed by component-hash. On miss, it sends the context pack to an LLM (GPT-4o-mini class), which proposes a typed `RepairPatch ∈ {selector_rewrite, wait_strategy, step_replacement}`. The patch is applied to a sandboxed Playwright run.
- **L4 — Behavioural-replay oracle.** Before committing the patch, the healed run's canonicalised HAR (timestamps, UUIDs, JWTs, cache-buster IDs, retry attempts redacted) is diffed against the last known-good baseline's canonicalised HAR. If the diff exceeds tolerance, the healer outputs `LIKELY_REAL_DEFECT` instead of a patch, surfacing a potential regression rather than masking it.

Data flow: source `.tsx` files → AST extractor → `LocatorSheet.json` → Playwright `intent(page, "add-to-cart")` → on-success path is invisible; on-failure path: capture → context pack → healer (memory ∪ LLM) → patch → oracle gate → commit or flag.
