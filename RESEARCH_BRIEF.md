# RESEARCH_BRIEF — React GUI 测试脚本的自动修复与自愈机制研究

> Source: user prompt to `/research-pipeline`, 2026-06-14.
> Language: 中文 (research notes may mix EN/CN per existing skills).

## Problem

End-to-end (E2E) GUI tests for React applications are **brittle**: small,
behaviour-preserving UI changes (renamed `class`, restructured DOM, moved
button, refactored component tree) routinely break locators (CSS / XPath /
`data-testid`) and cause `element not found` / timeout failures even though
no real defect exists.  The maintenance cost of these brittle tests is one
of the dominant pain points in modern web test suites and a primary reason
teams abandon E2E coverage.

We want a **self-healing** mechanism that automatically repairs broken
React GUI test scripts under behaviour-preserving UI changes, while
**avoiding "blind repairs"** that silently mask real regressions.

## Direction

Build and evaluate a **closed-loop, LLM-driven self-healing system** for
React E2E tests, spanning four layers:

1. **Robust locator pre-generation (write-time).**
   - Static analysis of the React source AST (and adjacent ecosystems for
     ablations: SwiftUI, Jetpack Compose) to extract the most stable
     anchors per UI control: `data-test-id`, `aria-*`, i18n keys, TS prop
     types, component display name.
   - LLM-assisted **semantic labeling** of controls by *intent* (e.g.
     "Submit order" button) rather than DOM tag, giving the healer a
     stable handle that survives markup churn.

2. **Runtime failure detection and causal analysis.**
   - Auto-capture failure context: stack/error log, full DOM snapshot,
     screenshot, network/console state.
   - Compute a **semantic diff** of DOM / React fiber tree between the
     last known-green baseline and the current failing version, isolating
     structural changes, rename events, and re-parent operations.

3. **LLM-based closed-loop repair.**
   - Feed failure context + diff + code-level constraints (TS types,
     intent label) to an LLM; receive an explanation + a patch
     (selector rewrite, wait-strategy change, or action-sequence fix).
   - **Multi-strategy fallback ladder**: preferred selector → fuzzy text
     → relative-position → visual-feature match → memory-guided historical
     fix.
   - Apply, re-run, **validate** that the fix passes *and* that other
     invariants (network calls, assertions, screenshot baseline) are not
     newly broken — guard against false-heal.

4. **Continuous learning and CI/CD integration.**
   - **Dynamic memory** of accepted repairs, indexed by component
     fingerprint / intent label, reused across runs.
   - GitHub / GitLab integration: failed CI job → background healer →
     posts proposed patch as PR comment / suggestion; humans approve.

## Constraints

- Empirical software-engineering research (no model training).  Compute
  budget is **LLM-API usage + a CI runner / Playwright cluster**, not
  GPU-hours.
- Must produce a publishable artefact: a reproducible benchmark + the
  self-healing tool + an evaluation.
- The system **must not** be evaluated only on *did the test go green
  again* — it must explicitly measure **false-heal rate** (repairs that
  mask real bugs).  This is a first-class metric, not a footnote.
- Target language: English paper, Chinese-friendly internal notes.

## Non-Goals

- Mobile-native test self-healing (iOS / Android) is out of scope for the
  main study (may appear as a limitations / future-work note or ablation
  on SwiftUI / Compose AST extraction).
- Record-and-replay generation from scratch is out of scope; we repair
  *existing* scripts, not author new ones.
- Visual-only healers (Applitools-style) are a **baseline**, not the
  contribution.

## Domain Knowledge

- Prior work to position against / cite (non-exhaustive, to be expanded
  in Stage 1 literature survey):
  - **WATER** (Choudhary et al., ICST 2011) — pioneering web test repair
    via DOM-element similarity.
  - **VISTA** / visual-based repair.
  - **CHRONICLER**, **ATA-QA**, recent LLM-for-test-repair papers (2023-2025
    ICSE / FSE / ASE / ISSTA).
  - Locator-robustness studies (Leotta et al.; Stocco et al.).
  - LLM agents for browser automation (WebArena, Mind2Web) — adjacent,
    but those *generate* actions, they don't *repair* broken scripts.
- Frameworks: React (primary), Playwright / Cypress / Selenium as test
  runners; TypeScript ASTs via `ts-morph` / Babel.

## Existing Results

None yet — this is a fresh project.  Wiki was just initialised, no prior
papers / ideas / experiments registered.

## Key Evaluation Metrics (must be reported)

- **Repair success rate** — fraction of broken scripts the system makes
  pass again.
- **False-heal rate** — fraction of "successful" repairs that mask a real
  injected defect (measured via mutation testing on the app-under-test).
- **Maintenance-cost savings** — proxy via human-edit count avoided,
  CI re-run minutes saved, or developer-time in a small user study.
- Secondary: latency per repair, $ cost per repair, generalisation
  across React versions / component libraries.

## Open Questions for Stage 1

1. Which existing React app(s) give us a realistic, reproducible
   benchmark of behaviour-preserving UI mutations + injected defects?
2. Is there an existing self-healing benchmark we can extend, or must we
   construct one?
3. What is the strongest current LLM-based test-repair baseline (2025)?
4. How do recent "browser-use" agents (Mind2Web-Repair, etc.) compare
   to dedicated test-repair tools on the *false-heal* axis?
