---
type: paper
node_id: paper:joseph2026_beyond_llmbased_test
title: "Beyond LLM-based test automation: A Zero-Cost Self-Healing Approach Using DOM Accessibility Tree Extraction"
authors: ["Renjith Nelson Joseph"]
year: 2026
venue: "arXiv"
external_ids:
  arxiv: "2603.20358"
  doi: null
  s2: null
tags: ["self-healing", "locator-ladder", "zero-llm", "competitor"]
added: 2026-06-14T05:28:40Z
---

# Beyond LLM-based test automation: A Zero-Cost Self-Healing Approach Using DOM Accessibility Tree Extraction

## One-line thesis
Zero-cost self-healing via a ten-tier accessibility-tree locator hierarchy (getByRole, data-testid, ARIA, CSS, text); explicit argument that LLM at write-time is unnecessary.

## Problem / Gap
Existing self-healing test frameworks (Healenium, Mabl, Testim, and academic LLM-based repair) delegate element discovery / re-discovery to LLMs at runtime. This adds per-run API cost that scales linearly with test-suite size, becoming prohibitive at enterprise scale (300+ test cases). The paper's argument: a well-designed deterministic accessibility-tree extraction is already enough; LLMs are unnecessary for the locator layer.

## Method
**Ten-tier priority-ranked locator hierarchy** extracted from a live DOM in one initial pass:
1. `get_by_role` (W3C ARIA standard)
2. `data-testid`
3. ARIA labels (`aria-label`, `aria-labelledby`)
4. ARIA attributes (`aria-*` other)
5. ID attribute
6. Name attribute (form fields)
7. Placeholder
8. CSS class fragments (stable prefixes)
9. Visible text
10. CSS selector (last resort)

**Self-healing mechanism**: on test failure, re-extract *only the broken selectors* using the same ladder; no full re-discovery, no LLM call.

**Architecture**: engine / functions / workflows pattern, organised under three business tiers (L0 Domain → L1 Process → L2 Feature) for 300+ test cases.

## Key Results
- Validated on automationexercise.com across 3 device profiles × 10 business-process workflows = 31 test combinations.
- **100% pass rate (31/31)**; total suite wall-clock 22 s under parallel execution.
- Self-healing empirical demo: deliberately injected stale selector recovered in **<1 s, zero human intervention**.
- 82.4% element discovery coverage on first cold-cache execution.
- Zero ongoing API cost.

## Assumptions
- Each interactive element has a reasonably stable accessible name OR a stable `data-testid` OR an ARIA attribute. (If not, the ladder degrades to text or class fragments and the "first-visible" tiebreaker takes over.)
- Test suite covers a single deployed app where stale selectors are localised, not catastrophic page redesigns.
- No need to distinguish "two semantically different buttons that happen to share an accessible name" — the ladder will silently pick the first one.

## Limitations / Failure Modes
- **Silent disambiguation**: when multiple elements share the highest-priority rung (e.g. two "Save" buttons on the same modal), the ladder picks the first; that pick can change as the DOM re-orders → silent false-heal risk.
- **No semantic intent**: a button whose label changes from "Submit Order" to "Place Order" (behaviour-preserving rename) breaks the ladder's text/aria-label rung; without an intent layer, the healer must guess.
- Evaluated on a **single** e-commerce demo app; no real-world drift evaluation, no defect-mutant injection, **no false-heal measurement**.
- Class-fragment rung is unstable under Tailwind / CSS-in-JS hash churn.

## Reusable Ingredients
- The ten-tier ladder itself is well-engineered and aligns closely with Kent C. Dodds' Testing-Library priority guidance; HealReact's L1 should adopt this rung order verbatim.
- The "re-extract only broken selectors" pattern as a runtime optimisation.

## Open Questions
- How does the ladder behave under React Fiber re-parenting? (Joseph doesn't test on React specifically.)
- How often does the silent-disambiguation failure mode actually trigger in real apps? — this is exactly what HealReact's intent labels + behavioural-replay oracle aim to measure.
- Does the ladder's "100% pass" hold under mutation-injected defects? (Untested.)

## Claims
- Deterministic accessibility-tree extraction is sufficient for ≥80% of element-discovery cases.
- Per-run LLM API cost is unnecessary for the locator layer.

## Connections
- `idea:001` *extends* this paper: HealReact's L1 ladder is conceptually Joseph's ladder; the novelty narrows to (i) intent-label layer on top of the ladder, (ii) behavioural-replay oracle, (iii) false-heal evaluation methodology — none of which Joseph addresses.

## Relevance to This Project
**Critical baseline**. E1 main results include Joseph's ladder as baseline (b). Ablation A1 ("drop intent labels, ladder-only") is now a *prerequisite for E1 validity* per Codex Round-2 review — we must demonstrate that the intent layer provides measurable lift over Joseph's ladder, otherwise our LLM contribution at write-time collapses.

## Abstract (original)

> Modern web test automation frameworks rely heavily on CSS selectors, XPath expressions, and visible text labels to locate UI elements. These locators are inherently brittle -- when web applications update their DOM structure or class names, test suites fail at scale. Existing self-healing approaches increasingly delegate element discovery to Large Language Models (LLMs), introducing per-run API costs that become prohibitive at enterprise scale. This paper presents a zero-cost self-healing test automation framework that replaces LLM-based discovery with a structured accessibility tree extraction algorithm. The framework employs a ten-tier priority-ranked locator hierarchy -- get_by_role (W3C standard), data-testid, ARIA labels, CSS class fragments, visible text -- to discover robust selectors from a live DOM in a single one-time pass. A self-healing mechanism re-extracts only broken selectors upon failure, rather than re-running full discovery. The framework is validated against automationexercise.com across three device profiles (Desktop Chrome, Desktop Safari, iPhone 15) and ten business process test workflows under a three-tier hierarchy (L0: Domain, L1: Process, L2: Feature). Results demonstrate a 31/31 (100%) pass rate across 31 test combinations with total execution time of 22 seconds under parallel execution. Self-healing is empirically demonstrated: a stale selector is detected and re-discovered in under 1 second with zero human intervention. The framework scales to 300+ test cases with zero ongoing API cost.

