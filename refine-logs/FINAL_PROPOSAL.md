# FINAL_PROPOSAL — HealReact

> Component-AST Intent Locators and Fault-Localising LLM Repair for React E2E Tests, Evaluated with Mutation-Grounded False-Heal.

**Status:** refined (1 self-review round; external reviewer rerun required before Stage 2 acceptance).
**Source idea:** `idea-stage/IDEA_REPORT.md` → IDEA-1.

---

## 1. Problem Anchor (frozen — do not drift)

React end-to-end (Playwright/Cypress) tests fail under
behaviour-preserving UI changes (renamed class, restructured DOM,
re-parented component, refactored handler). Existing self-healing tools
either fail (DOM/visual repair) or pass-but-mask the regression (LLM
repair without false-heal control). Both failure modes are expensive.

**Frozen scope (Round 1 revision after cross-model review — narrowed):**
- React + Playwright/Cypress E2E tests, evaluated on **ReproBreak's React/Playwright subset + our paired defect mutants**.
- Behaviour-preserving UI changes *and* mutation-injected real defects on the same component (this pairing is what enables false-heal measurement).
- Repair = generate a patch (new selector / wait / step) that re-greens the test **without** masking the injected defect.

**Out of scope of the main paper (per W6 scope risk; demoted to artefact / appendix / future work):**
- Mobile (SwiftUI/Compose) — limitations note + lit-only ablation.
- Generating new tests (we *repair* existing ones).
- Pure visual healing — it is a baseline rung, not the contribution.
- CI heal-budget integration — appendix only.
- Fix-memory across-CI provenance — A3 ablation only.
- Cross-framework AST extraction — future work.

---

## 2. Method Thesis (one sentence)

> Bake an LLM-extracted **intent label** into the component AST at
> write time, then at heal time use a fault-localised, intent-aware LLM
> repair loop whose patches are **verified against a behavioural-replay
> oracle** before commit.

---

## 3. Architecture (4 layers, matched to the user brief)

### L1 — Robust-locator pre-generation (write time)
- **AST extractor** (built on `ts-morph`, inspired by `ast-tools`,
  `dom-locator-generator`) walks every component file, emits a
  `LocatorSheet.json`: `{component, role, displayName, propType,
  testIdProp, i18nKeyRefs, ariaLabelRefs, parentChain}`.
- **Intent labeller** (LLM, batch-mode, cached per component-hash)
  reads the component source + nearby JSX context and emits a short
  intent label, e.g. `submit-order-button`, `cart-line-quantity-input`.
  The label is *also written back* into the component as a
  `data-intent="…"` attribute (codemod, opt-in via config).
- **Locator ladder** (deterministic, generated per element):
  `getByRole(role,{name:i18nKey}) → getByLabelText → getByTestId →
  data-intent → AST-relative XPath → visual fingerprint`.
- Output consumed by the test runner via a thin Playwright/Cypress
  helper: `intent("submit-order-button")` ≡ the ladder above.

### L2 — Runtime failure detection & semantic diff
- Wrap the runner — on any locator failure / timeout, capture:
  `{stack, console, network HAR, full DOM, React Fiber tree dump (via
  React DevTools backend), screenshot}`.
- Diff `LocatorSheet.json @ green-baseline` vs `@ now` to localise
  the *component-level* change: a rename, re-parent, prop-rename,
  i18n-key change, or true element removal.

### L3 — LLM closed-loop repair (4-step)
1. **Context pack**: failing step + ladder + diff summary + intent
   label + TS prop type + surrounding test code.
2. **LLM proposes**: (a) selector rewrite within the ladder, or (b)
   wait-strategy change, or (c) marks `LIKELY_REAL_DEFECT` if nothing
   matches the intent.
3. **Fallback rungs**: if LLM patch fails, walk down the deterministic
   ladder; if all rungs fail, walk the **fix-memory** (past accepted
   patches for the same component-hash).
4. **Behavioural-replay oracle (anti-false-heal)** — re-run the healed
   test against the **previous green build's recorded network/state
   trace** (canonicalised: timestamps/UUIDs/JWTs redacted). If
   request/response sequence diverges semantically, **reject the
   heal** and surface `LIKELY_REAL_DEFECT` to CI as a PR comment.

### L4 — Continuous learning & CI integration
- **Fix memory**: keyed by `component-hash × failure-fingerprint`,
  records accepted patches with provenance. Reused first before LLM call.
- **CI hook**: GitHub Action / GitLab CI plugin. On failure → run L2+L3.
  If healed and oracle-verified → post **PR review comment with the
  patch diff** (does not auto-commit). If `LIKELY_REAL_DEFECT` → mark
  failure with full diagnostic bundle.
- **Heal budget** (per Sun+26): if >X% of suite is healing in one run,
  alert — likely systemic UI change, not isolated drift.

---

## 4. Differentiation vs SOTA (Round 1 revision after cross-model review)

The two most painful competitors are **Joseph 2026** (arXiv 2603.20358 — zero-cost 10-tier accessibility ladder) on the locator-layer axis, and **ReproBreak** (arXiv 2605.12158, 2026) on the benchmark axis. The novelty axes are correspondingly narrowed.

| Axis | Xu+25 ICST'25 | Joseph 2026 | ReproBreak 2026 | HealReact (ours, narrowed) |
|------|---------------|--------------|------------------|------|
| Write-time locator generation | none | 10-tier accessibility ladder | n/a (dataset) | **Same ladder + LLM intent-label layer** on top (disambiguates dynamic/duplicate accessible names) |
| Runtime healer | LLM + explanation validator | re-extract only broken selectors via same ladder | n/a | LLM healer w/ Fiber + TS + intent + AST-diff context; UTFix-style context pack |
| Anti-hallucination | lexical explanation-consistency | none (deterministic) | n/a | **Behavioural-replay oracle** (executable; canonicalised network trace) |
| False-heal metric | not reported | not reported (100% pass on single demo) | not measured | **Primary metric**, mutation-grounded |
| Benchmark | VISTA-733 (legacy Selenium) | one e-commerce demo | **449 modern Cypress/Playwright breaks** | **ReproBreak + paired defect-mutant probes** (extension, not replacement) |
| Memory | none | none | n/a | Fix-memory keyed by component-hash (demoted: A3 ablation only) |

**Defensible novelty after Round 1:**
1. **Intent-label layer** as the anti-false-heal write-time contribution that Joseph's deterministic ladder cannot make (since ambiguous accessible names → silent "first visible" tiebreak).
2. **Behavioural-replay oracle** — no prior work has executable commit-gating.
3. **Mutation-grounded false-heal evaluation methodology** on a React/Playwright benchmark.

**Not defensible novelty anymore (cut from paper claims):**
- "First React-native locator-break benchmark" — ReproBreak got there first; ReactHealBench is now positioned as a ReproBreak extension.
- Generic "AST contributes at write-time" — Joseph 2026 already proves the *deterministic* part.
- CI heal-budget integration — demoted to appendix.

---

## 5. Risks & mitigations (carryover from Phase 4)

| Risk | Mitigation (Round 1 revision) |
|------|-----------|
| Intent label unstable across refactors (W1) | E2 measures intent-label stability rate; **pass bar = pilot-derived 95% CI lower bound − 5pp** (not the previously stated arbitrary 80%); semantic equivalence labeled by two blind annotators with Cohen's κ. |
| Mutation noise (W2) | Keep only mutants **survived by the baseline locator-only run AND killed by the original developer-written test suite at the green baseline** — the explicit two-condition definition in `SCHEMA.md` step 4. The shorthand "stubborn / surviving" is dropped as ambiguous. |
| Two-contributions paper (W3) | Lean benchmark = ReproBreak React/Playwright subset + ≥100 paired defect mutants (pilot must first measure the subset size; if too small, expand to all-frameworks-but-React-apps); split into artefact track if reviewers push back. |
| Oracle-replay false-positive AND false-negative (W4) | E4 measures full confusion matrix on labeled green+buggy runs (precision, recall, F1, stratified by canonicalisation class) — replaces the previously arbitrary ≤2% FP target. |
| Generality (W5) | Cross-framework note in discussion only; not an ablation in the main paper (per W6 scope narrowing). |
| LLM-API cost (W6) | Cost/latency table (E5); per-component caching; deterministic ladder tried first. |
| `data-intent` codemod changes test contract (W5 of cross-model review) | Ablation A5 runs HealReact in "AST-side-sheet only, no codemod" variant; compared head-to-head with the codemod variant on E1. |
| Single-model self-review (Stage 1 initial) | **Done**: Cross-model review via Codex MCP completed two rounds; final score 6.2/10, verdict 'almost'. See `review-stage/AUTO_REVIEW.md`. |

---

## 6. Pre-registered success criteria (for `/result-to-claim`)

The paper claims hold iff:

- **C1 (Repair-success)**: HealReact ≥ Xu+25 on repair-success-rate on
  `ReactHealBench` by ≥ +10 pp (one-sided).
- **C2 (False-heal)**: HealReact false-heal-rate ≤ ½ × Xu+25 false-heal-rate
  on the same benchmark.
- **C3 (Intent stability)**: stability rate on 100 behaviour-preserving
  refactors ≥ (pilot-derived 95% CI lower bound − 5pp), pre-registered
  before the main run. Semantic equivalence labeled by two blind
  annotators with reported Cohen's κ.
- **C4 (Cost)**: Median repair cost ≤ $0.05 and ≤ 8 s wall-clock per
  failure on a commodity model (target: GPT-4o-mini class).

If C2 fails, the paper pivots from "method" to "the metric matters"
(benchmark-only contribution).
