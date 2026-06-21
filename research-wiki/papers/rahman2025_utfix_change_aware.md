---
type: paper
node_id: paper:rahman2025_utfix_change_aware
title: "UTFix: Change Aware Unit Test Repairing using LLM"
authors: ["Shanto Rahman", "Sachit Kuhar", "Berk Cirisci", "Pranav Garg", "Shiqi Wang", "Xiaofei Ma", "Anoop Deoras", "Baishakhi Ray"]
year: 2025
venue: "arXiv"
external_ids:
  arxiv: "2503.14924"
  doi: null
  s2: null
tags: ["llm-repair", "test-evolution", "context-pack"]
added: 2026-06-14T05:28:41Z
---

# UTFix: Change Aware Unit Test Repairing using LLM

## One-line thesis
LLM-based unit-test repair under code evolution; uses static slice + dynamic slice + failure message context; PACMPL OOPSLA1 2025.

## Problem / Gap
When focal methods evolve (signature change, body change, refactor), the existing unit tests targeting them often break in two ways: (i) assertion failure (expectation no longer holds), (ii) coverage drop (test no longer exercises the new path). A Meta study cited in the paper reports that 14–22% of software failures stem from outdated tests. Prior LLM test-generation work focuses on *creating* new tests, not *evolving* existing ones.

## Method
LLM-based unit test repair with a structured context pack:
- **Static slice**: code snippets statically reachable from the failure point (call graph, type info).
- **Dynamic slice**: execution traces from running the broken test to capture actual runtime values.
- **Failure message**: the assertion error / exception text verbatim.

The LLM is prompted with all three plus the new focal method body; output is a patched test. Two benchmarks: Tool-Bench (synthetic, Python OSS projects) and a real-world Python benchmark.

## Key Results
- Tool-Bench: **89.2% assertion-failure repair**, 100% coverage for 96/369 tests.
- Real-world: 60% assertion-failure repair, 100% coverage for 19/30 tests.
- First comprehensive study on unit-test evolution in Python.

## Assumptions
- Focal method is identifiable (test → method mapping is reliable).
- Static + dynamic slices fit in the LLM context window.
- Repair is *expected* to track the new focal method — i.e. the test should track code evolution rather than flag it as a regression.

## Limitations / Failure Modes
- Python-only; not GUI / not E2E.
- Assumes the *test* is wrong and the *code* is correct — does not consider that the test might be guarding intent that the new code violates.
- No false-heal evaluation: a "repair" that masks a real semantic regression in the focal method is not penalised.

## Reusable Ingredients
- The **static-slice + dynamic-slice + failure-message context pack** is the cleanest articulation we've seen of an LLM repair prompt; HealReact's L3 context bundle adopts the same pattern (AST slice + Fiber/DOM slice + failure message + screenshot).

## Open Questions
- What fraction of UTFix's "repairs" actually mask real regressions? (The paper doesn't measure.)
- Does the context-pack pattern generalise to GUI repair where the "focal method" is a React component re-render rather than a function call?

## Claims
- LLM unit-test repair benefits from a structured (static + dynamic + error) context pack over raw failure-message-only prompting.

## Connections
- `idea:001` *inspired_by* this paper: HealReact's L3 prompt structure is a GUI-analogue of UTFix's context pack.

## Relevance to This Project
**Design influence, not competitor**. Different failure class (unit-test assertion, not GUI locator). Cited in the L3 design section to anchor our context-pack choice.

## Abstract (original)

> Software updates, including bug repair and feature additions, are frequent in modern applications but they often leave test suites outdated, resulting in undetected bugs and increased chances of system failures. A recent study by Meta revealed that 14%-22% of software failures stem from outdated tests that fail to reflect changes in the codebase. This highlights the need to keep tests in sync with code changes to ensure software reliability. In this paper, we present UTFix, a novel approach for repairing unit tests when their corresponding focal methods undergo changes. UTFix addresses two critical issues: assertion failure and reduced code coverage caused by changes in the focal method. Our approach leverages language models to repair unit tests by providing contextual information such as static code slices, dynamic code slices, and failure messages. We evaluate UTFix on our generated synthetic benchmarks (Tool-Bench), and real-world benchmarks. Tool- Bench includes diverse changes from popular open-source Python GitHub projects, where UTFix successfully repaired 89.2% of assertion failures and achieved 100% code coverage for 96 tests out of 369 tests. On the real-world benchmarks, UTFix repairs 60% of assertion failures while achieving 100% code coverage for 19 out of 30 unit tests. To the best of our knowledge, this is the first comprehensive study focused on unit test in evolving Python projects. Our contributions include the development of UTFix, the creation of Tool-Bench and real-world benchmarks, and the demonstration of the effectiveness of LLM-based methods in addressing unit test failures due to software evolution.

