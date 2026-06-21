# Idea Discovery Report — React GUI Test Self-Healing

**Direction**: 适用于 React GUI 测试脚本的自动修复与自愈（Self-healing）机制研究
**Date**: 2026-06-14
**Pipeline**: research-lit → idea-creator → novelty-check → research-review → research-refine
**Run ID**: `react-selfheal-20260614`
**Source brief**: `RESEARCH_BRIEF.md`

> ⚠️ **Reviewer-independence caveat.** This session has a single LLM (no
> Codex MCP / cross-model jury in scope). The "external review" in Phase 4
> below is an *adversarial self-review* by the same model and is marked
> as such. Before submission, this must be re-run with a genuinely
> independent reviewer (Codex GPT-5.5 xhigh or human). The same caveat
> applies to the novelty check in Phase 3 (web-search based, no
> independent LLM cross-check).

---

## Executive Summary (Round 1 revision after cross-model review)

**🏆 Recommended idea (IDEA-1):** *Mutation-grounded false-heal evaluation
for React/Playwright locator repair, with HealReact — an intent-label
layer + behavioural-replay oracle on top of a Joseph-2026-style
accessibility ladder — as the reference method, evaluated on a
**ReproBreak-extended** benchmark with paired UI-refactor / defect-mutant
cases.*

The contribution narrowed in Round 1 (was three axes, now two):

1. **Mutation-grounded false-heal as a first-class evaluation axis** (kept).
   Current academic LLM-repair papers (Xu+25 ICST'25) report only
   repair-success; even the industry Playwright Healer case study
   (Sun+26) surfaces regression-masking only anecdotally (3 incidents
   in 6 months). We make false-heal measurable via paired
   UI-refactor + injected-defect cases on the same component.
2. **HealReact method**, isolated to the two pieces that are NOT in
   Joseph 2026's zero-cost ten-tier accessibility ladder: (a) an
   **LLM-extracted intent-label layer** that survives behaviour-preserving
   refactors when the accessibility ladder would silently disambiguate to
   the wrong element; (b) a **behavioural-replay oracle** that gates
   every commit-time selector change against the previous green build's
   canonicalised network trace.

**Dropped from the main paper claim** (per W6 scope-risk):
- "First React-native benchmark" — invalidated by ReproBreak (de Moura
  et al., arXiv 2605.12158, May 2026). ReactHealBench is now positioned
  as a **ReproBreak extension** that adds paired defect mutants, not as
  a standalone benchmark contribution.
- CI heal-budget integration → artefact-track / appendix.
- Cross-framework (SwiftUI/Compose) AST extraction → future work, lit-only.
- Fix-memory contribution → ablation A3 only; not a headline claim.

**Pilot evidence:** Paper-only validation (no Playwright cluster
in-session). Pilot definition unchanged from Phase 4.5.

---

## Phase 1 — Literature Landscape

### 1.1 Canonical line of work (DOM / visual repair)

| Year | Paper | Key idea | Limitation we exploit |
|------|-------|----------|----------------------|
| 2011 | **WATER** — Choudhary, Prasad, Orso, ICST | DOM-element similarity; the original web-test repair | Operates on raw DOM, no semantic intent, low recall on heavy refactors |
| 2018 | **VISTA** — Stocco, Yandrapally, Mesbah, ESEC/FSE | Visual / image-processing pipeline; 81% repair on 733-breakage benchmark | Pixel-similarity is fragile to theming / dark-mode; benchmark is 2010s PHP, not React |
| 2023 | **WebEvo / SFTM-2023** | Multi-signal similarity over DOM evolution | Same benchmark family; no LLM |
| 2018 dataset | VISTA-733 benchmark (Claroline 165, Collabtive 218, PPMA 300, AddressBook 50) | The default eval | Architecturally distant from modern React |

### 1.2 LLM-era test repair (SOTA we must beat)

| Year | Paper | Setup | Why we can beat it / how we position |
|------|-------|-------|-------------------|
| **2025** | **Xu, Li, Tan — ICST** "Understanding and Enhancing Attribute Prioritization in Fixing Web UI Tests with LLMs" (arXiv 2312.05778v3) | ChatGPT performs *global* element matching after WATER/VISTA/EditDis local matching; **explanation-validator** mitigates hallucination by checking the LLM's stated reason for consistency. Evaluated on 139 broken Java Selenium statements (8,429 API calls on gpt-3.5-turbo). | (a) Purely post-failure / element-matching — no write-time AST/intent contribution. (b) Evaluated only on legacy Java Selenium (VISTA-733 family). (c) Repair accuracy only, no false-heal / mutation-masking. (d) **Reproducibility is itself a research task** (per W2): port to Playwright counts as "adapted reproduction" only. |
| **2026** | **Joseph — arXiv 2603.20358** "Beyond LLM-based Test Automation: Zero-Cost Self-Healing via DOM Accessibility Tree Extraction" | **Ten-tier priority-ranked locator hierarchy** (`getByRole → data-testid → ARIA → CSS-class-fragments → text`) extracted from live DOM in one pass; on failure re-extracts only broken selectors. Validated on automationexercise.com with 100% pass on 31 combinations and stale-selector recovery in <1s. **Explicit argument that LLM at write-time is unnecessary.** | This is the most painful competitor and changes our framing: HealReact's L1 deterministic ladder *is* roughly Joseph's ten-tier ladder, so we cannot claim novelty there. **What we add on top:** (a) LLM-extracted intent labels for components whose accessible name is dynamic or duplicated across the page (which Joseph's ladder silently disambiguates to "first visible" — a false-heal risk); (b) behavioural-replay oracle gating commits; (c) mutation-grounded false-heal eval. Joseph's paper does NOT measure false-heal. |
| 2025 | **NIODebugger** — ICSE | LLM-agent for non-idempotent-outcome flaky tests (state pollution across runs) | Different failure class (NIO), not GUI brittleness — orthogonal, complementary baseline category not a direct competitor |
| 2025 | **UTFix** — Rahman et al., PACMPL OOPSLA1 (arXiv 2503.14924) | LLM unit-test repair under code evolution for Python; context pack = static slice + dynamic slice + failure message; trained on synthetic Tool-Bench + real Python repos. | Not GUI but sets the **context-pack design pattern** we adopt in L3: HealReact's healer prompt also bundles static (AST) + dynamic (DOM/Fiber) + failure-message context. We cite as design influence, not competitor. |
| 2023 | **TRaf** — Pei et al., extended TOSEM 2025 (arXiv 2305.08592) | Time-based repair of async-wait flaky tests; analyses code-similarity + history to pick a wait time. | Solves one sub-class (`wait_strategy` patches in our taxonomy). HealReact's L3 should either reuse TRaf's wait-time inference for that branch or run TRaf as a per-class baseline. |
| 2024 | **FlakyFix** — Fatima, Hemmati, Briand (arXiv 2307.00012) | LLM (GPT-3.5-Turbo) repairs flaky test code conditioned on a predicted fix-category label. | Different failure class (general flakiness, not GUI locator). Adjacent context for L3 prompting strategy. |
| 2025 | Huang et al. **TOSEM SLR** on LLM4APR | 189 papers, no dedicated GUI/E2E repair chapter | Confirms our niche is under-covered |

### 1.3 Industry / artifacts (positions our novelty)

| | Source | Stance |
|---|--------|--------|
| **ReproBreak** dataset | de Moura, Adamietz, Mehboob, Noller — arXiv 2605.12158 (May 2026); github.com/rub-sq/ReproBreak | **449 reproducible locator breaks** in Cypress/Playwright from 359 repos. Derived from E2EGit. **This is now our primary benchmark substrate.** ReactHealBench = ReproBreak (or its React-only subset) + paired mutation-injected defect probes. |
| Playwright Healer Agent case study | Sun et al., 2026 (IJESR, non-peer-reviewed) | First write-up of **regression-masking incidents** (3/6 months) and **heal-budget** governance — frames (but does not measure) the false-heal problem we formalise. |
| `ast-tools` (earthHa11Queen, GH) | ts-morph React extractor with rich attribute groups | Validates feasibility of AST extraction; we extend with **intent labelling** + behavioural oracle. |
| `dom-locator-generator` (craigwh10) | `getLocators(ReactElement, ["data-testid"], scope)` | Existing primitive for compile-time locator extraction — design influence. |
| `UITestFix` (Lin) | Refactored research benchmark with WATER/VISTA/SFTM/SFTM2023/WebEvo plug-ins | Reused for **legacy-app** comparison runs (back-compat sanity). |
| RTL guidance (Kent C. Dodds; Davis) | "Prefer getByRole/getByLabelText over getByTestId" | Frames our deterministic ladder (rungs match RTL priority by design). |
| Ricca, Marchetto, Stocco — "Multi-Year Grey Literature Review on AI-assisted Test Automation" (2024-25) | Industry tool landscape (Mabl, Healenium, Testim, Applitools, Functionize, BotGauge, AccelQ) | Positions our paper against commercial healers in the discussion / threats-to-validity section. |

### 1.4 Recurring gaps (used as ideation seeds; Round 1 revision)

| ID | Gap | Status | Linked to |
|----|-----|--------|-----------|
| **G1** | No first-class evaluation of **false-heal** (regression masking) in academic web-test-repair | **CONFIRMED, primary contribution** | Xu+25, VISTA, WATER, Joseph 2026; only Sun+26 industry surfaces it anecdotally |
| ~~G2~~ | ~~All published benchmarks are 2010s server-rendered apps~~ | **INVALIDATED by ReproBreak** (Round 1). Replaced with G2': "no benchmark pairs UI refactors with mutation-injected defects on the same component" | ReproBreak fills the 'modern benchmark' half; G2' is the remaining half |
| **G2'** | No benchmark provides **paired (UI-refactor, defect-mutant)** cases on the same component for false-heal measurement | unresolved | ReproBreak (UI breaks only), Stryker.js (mutants only) |
| **G3** | Repair operates either purely post-failure (Xu+25, VISTA) OR purely write-time-deterministic (Joseph 2026); no work combines a write-time intent layer with a runtime healer | unresolved | Joseph 2026, Xu+25 |
| **G4** | LLM-based repair operates on **DOM-only context**; component AST + TS types + intent are not used | unresolved | Xu+25 |
| **G5** | No **fix memory** with provenance ↔ replay across CI runs | unresolved (demoted to A3 ablation per W6 scope) | All — industry tools cache silently |
| **G6** | "Hallucination control" stops at *explanation consistency* (Xu+25) or static accessibility-name match (Joseph 2026); nobody **verifies the healed test against an executable behavioural oracle** | unresolved | Xu+25 explanation-validator, Joseph 2026 |

---

## Phase 2 — Idea Generation & Filtering

### 2.1 Brainstormed (8 candidates)

| # | Title | Sketch | Verdict |
|---|-------|--------|---------|
| 1 | **AST-anchored intent locator + fault-localising LLM healer + false-heal eval** | Write-time AST extraction → intent label baked into runtime → multi-strategy healer ladder → mutation-test eval | **🏆 KEEP** — see §IDEA-1 |
| 2 | Pure visual + LLM-vision healer | Replace VISTA's CV with a vision-language model on screenshots | KILL — heavy dependence on stable rendering, sidesteps G3/G4, expensive |
| 3 | RL-trained healer on logged repair traces | Learn a policy from accepted repairs | KILL — cold start; no public dataset; reviewers will ask "why not LLM?" |
| 4 | "Test-author copilot" that suggests robust locators in IDE | Static-only, no runtime healer | KILL — ablation of IDEA-1, weaker contribution |
| 5 | **Behavioural-oracle replay verifier** — given a healed test, replay against the previous green build's network log and assert no behaviour diff | Anti-false-heal mechanism only | **MERGE into IDEA-1** as its core anti-false-heal component |
| 6 | Cross-framework AST extractor (React + SwiftUI + Compose) common-IR | Generalisation play | KILL as main idea — keep as §Ablation in IDEA-1 |
| 7 | **`ReactHealBench`** — new mutation-based React benchmark with paired UI-change + bug-inject | Pure benchmark contribution | **MERGE into IDEA-1** — benchmark *plus* method is a stronger paper |
| 8 | "Heal-budget controller" for CI | Governance only | KILL — engineering contribution, no research depth; cite Sun+26, fold into discussion |

### 2.2 Surviving idea

**IDEA-1** = (1) ⊕ (5) ⊕ (7). System name: **`HealReact`** (working name).

### 2.3 Eliminated ideas log

See table above — kept here for the wiki's "failed ideas" anti-repeat memory (per `research-wiki` skill, failed ideas are highest-value memory).

---

## Phase 3 — Deep Novelty Check (IDEA-1)

**Method:** WebSearch on "self-healing LLM React Playwright 2024/2025",
"false healing regression masking test repair", "AST extraction React
robust locator". Plus knowledge-cutoff cross-check.

**Closest prior work and differentiation (Round 1 revision after cross-model review):**

| Closest | What they do | What we do differently |
|---------|--------------|------------------------|
| **Joseph 2026 (arXiv 2603.20358)** | Zero-cost 10-tier accessibility-tree ladder; rejects LLM at write-time | (a) **Intent-label layer on top of the ladder** for components whose accessible name is dynamic/duplicated — exactly the cases where Joseph's "first visible" tiebreaker silently picks the wrong element (a false-heal in waiting). (b) **Behavioural-replay oracle** gating commits — Joseph has no commit-time verification. (c) **Mutation-grounded false-heal eval** — Joseph reports 100% pass rate on a single e-commerce demo, but does not inject defects. |
| **Xu+25 (ICST)** | LLM + explanation validator over WATER/VISTA candidates on Java Selenium | (a) Modern React/Playwright stack, not legacy Selenium. (b) Executable behavioural-replay oracle, not lexical explanation-consistency. (c) Mutation-based false-heal eval as primary metric. (d) Context pack uses Fiber tree + TS types + intent, not DOM-only. |
| **ReproBreak (arXiv 2605.12158, 2026)** | Cypress/Playwright locator-break **dataset** (449 cases, 359 repos) | They contribute a dataset; we contribute a method **and** an extension of that dataset with paired defect mutants for false-heal probes. Cite, reuse, do not compete on benchmark novelty. |
| **VISTA (FSE'18)** | Visual element matching | We use semantic AST + intent, not pixels; visual is a fallback rung. Run VISTA-733 as back-compat sanity, not as the headline eval. |
| **Sun+26 (Playwright Healer case study)** | Engineering deployment, **anecdotal** regression-masking (3 incidents) | We formalise false-heal as a measurable axis with mutation-test injection. |
| **UTFix (OOPSLA'25)** | LLM unit-test repair w/ static+dynamic slice + failure msg context | Adopt their context-pack pattern in L3. Not a GUI competitor. |
| **TRaf (TOSEM'25)** | Async-wait timeout repair on web tests | Solves one HealReact sub-class (`wait_strategy`). Either reuse or per-class baseline. |
| **NIODebugger (ICSE'25)** | LLM agent for NIO flaky tests | Different failure class (state pollution); adjacent, not a baseline. |
| **`ast-tools` / `dom-locator-generator`** | Compile-time AST → locator export | We layer LLM intent labelling on top + wire into a runtime healer. |

**Concurrent-work risk (last 6 mo):** Joseph 2026 (March 2026) is the
most painful overlap on the deterministic-ladder axis; ReproBreak (May
2026) takes the dataset axis. Our defensible novelty has narrowed to:
**(i) intent-label layer + behavioural-replay oracle as anti-false-heal
machinery, and (ii) the mutation-grounded false-heal evaluation
methodology itself.** The intent layer must be empirically shown
necessary — i.e. Joseph's ladder alone produces measurable false-heals on
ambiguous-name cases that intent labels prevent.

**Verdict:** Novel on the narrower (ii + intent/oracle) axes, but the
"first React-native benchmark" axis is dropped.

---

## Phase 4 — Adversarial Self-Review (same-model, MUST re-run with codex)

**Reviewer score (provisional, same-model self-review): 6.5 / 10.**

### 4.1 Strengths
- Clean three-axis novelty against the closest paper (Xu+25).
- False-heal as primary axis is unusual and timely.
- Practical artefact path (benchmark + tool + CI integration).

### 4.2 Weaknesses (must address)

**W1 — "Intent label" is the hardest part and the paper lives or dies on
it.** What if the LLM-assigned intent label is wrong or unstable across
refactors? You need an inter-annotator-agreement-style study or an
ablation showing how often the intent label survives behaviour-preserving
refactors. *Fix*: Add a dedicated experiment block measuring **intent-label
stability rate** across a curated set of React refactors. If <80%, the
intent locator collapses to "another flaky heuristic".

**W2 — Mutation-based false-heal eval is hard to do honestly.** Mutation
testing on real React apps generates many semantically dead mutants
(unreachable code, equivalent renders). Without filtering, false-heal
rates become noisy. *Fix (Round 1 revised terminology)*: keep only mutants
that are **survived by the baseline locator-only test AND killed by the
original developer-written test suite at the green baseline** (the
two-condition definition that replaces the ambiguous "stubborn / surviving"
shorthand; see `healreact/bench/ReactHealBench/SCHEMA.md` step 4). This
intersection captures real non-equivalent defects that would be invisible
to a locator-only check.

**W3 — Benchmark construction is its own paper.** Two contributions
(benchmark + method) competing in 9 pages is risky. *Fix*: Either (a)
split — bench at MSR / artifact track, method at ICSE/FSE; or (b) keep
the bench minimal-but-defensible (3 apps × 30 breakages each × 5
mutations) and let the method results carry the paper.

**W4 — "Behavioural-oracle replay" assumes a stable network log.** Most
React apps have dynamic API responses (timestamps, IDs). The
oracle-replay must canonicalise responses, otherwise it adds *its own*
false-positive layer. *Fix*: Adopt a snapshot-diff canonicaliser
(redact known volatile fields), measured separately for
false-positive-rate.

**W5 — Why React only?** Cross-framework generality is the obvious
reviewer 2 ask. *Fix*: Single-section limitations + SwiftUI/Compose
**ablation** on intent-label stability (lit-only or 1 toy app),
explicitly scoping "method principle generalises, evaluation focused on
React for tractable benchmark construction".

**W6 — LLM-API cost.** A 200-test suite with 4 healer rounds × 5
strategies × $0.01 per call ≈ $40 / suite-run; not free. *Fix*: Cost &
latency table.

### 4.3 Required minimum experiments (per reviewer feedback)

The plan in §Phase 4.5 already includes:
- E1 main results (repair success & false-heal vs 4 baselines)
- E2 intent-label stability (W1)
- E3 mutation-filter sensitivity (W2)
- E4 oracle-replay false-positive rate (W4)
- E5 cost / latency (W6)
- A1-A4 ablations

Phase 4.5 is the binding plan.

---

## Phase 4.5 — Refined Proposal & Experiment Plan

**Refined proposal:** `refine-logs/FINAL_PROPOSAL.md`
**Experiment plan:** `refine-logs/EXPERIMENT_PLAN.md`
**Tracker (skeleton):** `refine-logs/EXPERIMENT_TRACKER.md`

Headline:

> *HealReact: Component-AST Intent Locators and Fault-Localising LLM
> Repair for React E2E Tests, Evaluated with Mutation-Grounded
> False-Heal.*

---

## 🏆 IDEA-1 (RECOMMENDED) — HealReact

- **Problem anchor**: React E2E tests are brittle under
  behaviour-preserving UI refactors; existing repair masks regressions.
- **Hypothesis**: Combining write-time AST + LLM-extracted intent labels
  (front-loaded robustness) with a fault-localising LLM healer that is
  *verified* against a behavioural-replay oracle (back-loaded
  anti-false-heal) jointly raises repair success **without** raising
  false-heal beyond a tight bound.
- **Dominant contribution** (Round 1 revision): First academic work to measure
  and bound **false-heal** (regression-masking) as a primary metric on a
  modern React/Playwright stack, via a **ReproBreak-extended benchmark with
  paired defect-mutant probes**, alongside HealReact — a method that adds an
  intent-label layer + behavioural-replay oracle on top of a Joseph-2026-style
  accessibility ladder. *(The earlier "first React-native benchmark" framing
  is dropped: ReproBreak is the modern locator-break dataset; we extend it.)*
- **Pilot status**: PAPER-ONLY (this session); see EXPERIMENT_PLAN §Pilot.
- **Novelty**: CONFIRMED via Phase 3.
- **Self-reviewer score**: 6.5/10 (same-model caveat).
- **Next step**: `/experiment-bridge` to implement and run E1–E5 + A1–A4.

## Idea 5 (MERGED into IDEA-1) — Behavioural-Oracle Replay Verifier
Folded as IDEA-1's anti-false-heal mechanism.

## Idea 7 (MERGED into IDEA-1) — `ReactHealBench`
Folded as IDEA-1's benchmark contribution.

## Eliminated Ideas
2, 3, 4, 6, 8 — see §2.1 with reasons. Kept here as "failed-ideas"
memory for `research-wiki/`.

---

## Cross-Model Review Trace
- Phase 4 self-review: **same-model**, marked unreliable.
  Trace placeholder: `.aris/traces/PHASE4_SELFREVIEW_PLACEHOLDER.md`.
  **Action required**: re-run via Codex MCP `mcp__codex__codex` with
  `gpt-5.5 xhigh` before claiming Stage 1 accepted.

## Next Steps
- [ ] Re-run Phase 3 & Phase 4 with a genuinely external reviewer.
- [ ] `/experiment-bridge "HealReact"` to implement and execute the
      EXPERIMENT_PLAN.
- [ ] After E1 main results pass, `/ablation-planner` for A1–A4.
- [ ] `/auto-review-loop` (medium difficulty) on returned results.
- [ ] `/paper-writing — venue: ICSE` (or FSE/ASE/ISSTA — pick at
      Stage 5 gate).
