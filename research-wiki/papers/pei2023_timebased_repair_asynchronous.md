---
type: paper
node_id: paper:pei2023_timebased_repair_asynchronous
title: "Time-based Repair for Asynchronous Wait Flaky Tests in Web Testing"
authors: ["Yu Pei", "Jeongju Sohn", "Sarra Habchi", "Mike Papadakis"]
year: 2023
venue: "arXiv"
external_ids:
  arxiv: "2305.08592"
  doi: null
  s2: null
tags: ["test-repair", "async-wait", "web", "adjacent"]
added: 2026-06-14T05:28:42Z
---

# Time-based Repair for Asynchronous Wait Flaky Tests in Web Testing

## One-line thesis
Time-based repair for async-wait flaky tests in web front-end; suggests adjusted wait times via code-similarity + history; extended to TOSEM 2025.

## Problem / Gap
Asynchronous waits (`waitFor`, `sleep`, polling) are the single most common root cause of flaky web-test failures. Developers typically just bump the timeout when a wait fails, with no principled basis. The paper builds a 49-case dataset of reproducible async-wait flakes in Web apps and finds 63% (31/49) of developer fixes simply adjusted timeout values, often suboptimally (over-long → wasted CI time; too-short → still flaky).

## Method
TRaf = Time-based Repair for Async-Wait Flaky tests:
1. **Static suggestion**: for a flaky async-wait point, find the most similar `wait`/`waitFor` call elsewhere in the codebase (or in the project's git history) using code-similarity heuristics; reuse its successful wait time.
2. **Dynamic refinement** (optional): run the test under instrumentation, observe the actual condition-met time, and shrink the wait to just above that.

Output is a patched wait time; the rest of the test is untouched.

## Key Results
- Static-only TRaf: **11.1% test-execution-time reduction** vs developer-written fixes.
- Static + dynamic: **20.2% reduction** end-to-end; **16.8%** at first successful refinement.
- 3/16 PRs accepted upstream.
- Extended journal version in TOSEM 2025 (DOI 10.1145/3695989).

## Assumptions
- The flake is genuinely an async-wait problem (the dataset is curated for this class).
- A similar wait exists elsewhere in the codebase or git history.
- Wait time, not condition-correctness, is the fix.

## Limitations / Failure Modes
- Solves *only* async-wait flakes; does nothing for locator brittleness, state pollution, or assertion races.
- Refined wait times are still timeouts — fundamentally a timing heuristic, not a synchronisation primitive.
- Selenium-era web stack (jQuery / AngularJS / classic DOM) — modern Playwright `auto-waiting` (`await locator.click()` waits for visible+enabled+stable) reduces the size of TRaf's addressable population.

## Reusable Ingredients
- TRaf's similarity-based wait-time inference can be plugged into HealReact L3's `wait_strategy` patch branch as a per-class baseline / specialist sub-healer.

## Open Questions
- How does TRaf interact with Playwright's auto-waiting (which often eliminates the explicit wait in the first place)?
- Could TRaf-style historical mining work for other patch classes (selector_rewrite, step_replacement)?

## Claims
- For the async-wait flake sub-class, static historical-similarity inference of wait times beats developer-written fixes on execution-time metrics.

## Connections
- `idea:001` *extends* this paper: HealReact's L3 `wait_strategy` patch type is the same class TRaf addresses; we either reuse TRaf's heuristic or run TRaf as a per-class baseline in E1.

## Relevance to This Project
**Per-class baseline**. In E1 main results, TRaf serves as the specialist baseline for the `wait_strategy` patch class — establishing that HealReact's general LLM healer is at least competitive with the best class-specific tool on each class.

## Abstract (original)

> Asynchronous waits are one of the most prevalent root causes of flaky tests and a major time-influential factor of web application testing. To investigate the characteristics of asynchronous wait flaky tests and their fixes in web testing, we build a dataset of 49 reproducible flaky tests, from 26 open-source projects, caused by asynchronous waits, along with their corresponding developer-written fixes. Our study of these flaky tests reveals that in approximately 63% of them (31 out of 49), developers addressed Asynchronous Wait flaky tests by adapting the wait time, even for cases where the root causes lie elsewhere. Based on this finding, we propose TRaf, an automated time-based repair method for asynchronous wait flaky tests in web applications. TRaf tackles the flakiness issues by suggesting a proper waiting time for each asynchronous call in a web application, using code similarity and past change history. The core insight is that as developers often make similar mistakes more than once, hints for the efficient wait time exist in the current or past codebase. Our analysis shows that TRaf can suggest a shorter wait time to resolve the test flakiness compared to developer-written fixes, reducing the test execution time by 11.1%. With additional dynamic tuning of the new wait time, TRaf further reduces the execution time by 20.2%.

