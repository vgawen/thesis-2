---
type: paper
node_id: paper:moura2026_reprobreak_dataset_reproducible
title: "ReproBreak: A Dataset of Reproducible Web Locator Breaks"
authors: ["Thiago Santos de Moura", "Leon Adamietz", "Samra Mehboob", "Yannic Noller"]
year: 2026
venue: "arXiv"
external_ids:
  arxiv: "2605.12158"
  doi: null
  s2: null
tags: ["benchmark", "locator", "playwright", "cypress", "competitor"]
added: 2026-06-14T05:28:38Z
---

# ReproBreak: A Dataset of Reproducible Web Locator Breaks

## One-line thesis
449 reproducible locator breaks in Cypress/Playwright from 359 open-source repos; first modern dataset of locator fragility in current web testing frameworks.

## Problem / Gap
Before ReproBreak, the dominant datasets for evaluating locator fragility / repair (VISTA-733 in particular) targeted Selenium-style 2010s server-rendered apps with `id`/XPath locators. No dataset existed for the modern Cypress + Playwright stack at scale. As a result, evaluation of LLM-era locator repair (Xu+25 ICST) was confined to legacy Java Selenium harnesses.

## Method
1. Filter the E2EGit dataset (Meglio et al., 2025, 472 OSS web apps) for Cypress + Playwright → 374 repos (191 Playwright, 183 Cypress).
2. Static analysis of git history to find commits that *change a locator string* in an E2E test file (`analyze_locator_changes.py` → `locator_analysis.csv`, **9,604 candidate changes across 216 repos with sufficient test history**).
3. Pick the 4 projects with the largest number of locator changes and run an automated reproduction harness (`reproduce.py`) that checks out `commit_old`, runs the test, checks out `commit_new`, re-runs, and confirms the test breaks specifically due to the locator change (not due to other regressions). **449 confirmed reproductions.**
4. Release dataset as a SQLite DB (figshare) + scripts + Docker.

## Key Results
- 9,604 candidate locator changes (this work's `locator_analysis.csv`).
- 449 confirmed reproducible locator breaks across the 4 top projects.
- Roughly even Cypress vs Playwright split by syntax (4,737 vs 5,263 in the candidate CSV; our reading of the CSV).
- Categorisation is currently single-label `structural_break`; finer taxonomy is left to consumers of the dataset.

## Assumptions
- Locator-string change in a test file is a reasonable proxy for "locator broke and needed repair".
- The 4 top projects (Mattermost, Ionic, Microsoft/Playwright, Angular-SlickGrid) are representative of "modern web testing" — note that not all are React.
- Reproducibility is binary (test fails → confirmed break); does not annotate whether the new locator is *correct* in any deeper semantic sense.

## Limitations / Failure Modes
- The candidate CSV (9,604) is much larger than the confirmed-reproductions DB (449); a paper using only the CSV would over-count.
- React-specific subset is not explicitly labelled; consumers must filter by repo.
- No paired ground-truth defect mutants — only the UI-refactor side of the (refactor, defect) pair needed for false-heal evaluation.
- No standard split (train/val/test) released; each consumer must define their own.

## Reusable Ingredients
- `locator_analysis.csv` for syntax-level statistics without needing the figshare DB.
- `reproduce.py` for adding new repos to the dataset.
- The categorisation pipeline (`categorize_locators.py`) as a starting point for a finer taxonomy.

## Open Questions
- What fraction of the 449 are React-specific? (Our `healreact/bench/scripts/reprobreak_subset.py` estimates ~80–100 React+Playwright reproductions; figshare-DB download needed to confirm.)
- How often does the new locator in `commit_new` itself break in a subsequent commit (long-term locator-instability cascade)?
- Could the 9,155 unreproduced candidates be recovered with looser reproduction criteria (e.g. headed run, longer timeouts)?

## Claims
- ReproBreak is the first locator-break dataset for Cypress + Playwright at OSS scale (the paper's headline claim).
- Locator instability is widespread across modern web stacks (449 confirmed cases from only 4 projects).

## Connections
- `idea:001` *contradicts* this paper on the "first React-native benchmark" novelty axis — that axis is no longer defensible; ReactHealBench is now a ReproBreak *extension* with paired defect mutants.

## Relevance to This Project
**Primary**. ReactHealBench (B1) is now defined as **ReproBreak's React/Playwright subset + our paired defect mutants for false-heal probes**. We attribute upstream and contribute (a) the React-only filter, (b) the mutation-injected defect half, (c) the false-heal evaluation methodology — not a new locator-break corpus.

## Abstract (original)

> Automated GUI testing frameworks such as Cypress and Playwright rely on locators to find and interact with web elements. A locator break occurs when a structural change in the application under test causes a locator to no longer find its target element, resulting in test breakages even when the underlying functionality remains unchanged. Despite its impact on test maintenance, no dataset exists to evaluate locator fragility in Cypress and Playwright at scale. In this paper, we present ReproBreak, a dataset of reproducible locator breaks in web application GUI tests. We analyzed 359 open-source repositories to identify commits that contain locator changes. To confirm whether these changes are indeed locator breaks, we reproduced them in the top 4 projects with the largest number of locator changes and found 449 locator breaks, which are provided in the dataset along with scripts for automated reproduction. We believe ReproBreak serves as a valuable artifact to support research on locator fragility, repair techniques, and test robustness. The video is available at: https://youtu.be/mZByS_TnCvE. The dataset is at https://github.com/rub-sq/ReproBreak.

