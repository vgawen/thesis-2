# Research Wiki Query Pack

_Auto-generated. Do not edit._

## Project Direction
**Problem**

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

**Constraints**

- Empirical software-engineering research (no model training).  Compute
  budget is **LLM-API usage + a CI runner / Playwright cluster**, not
  GPU-hours.
- Must produce a publishable artefact: a reproducible benchmark + the
  self-healing tool + an evaluation.
- The system **must not** be evaluated only on *did the test go green
  again* — it must explicitly measure **false-heal rate** (repairs that
  mask real bugs).  This is a first-class metric, not a footnote.
- Target language: English paper, Chinese-friendly internal notes.

**Non-goals**

- Mobile-native test self-healing (iOS / Android) is out of scope for the
  main study (may appear as a limitations / future-work note or ablation
  on SwiftUI / Compose AST extraction).
- Record-and-replay generation from scratch is out of scope; we repair
  *existing* scripts, not author new ones.
- Visual-only healers (Applitools-style) are a **baseline**, not the
  contribution.

**Domain Knowledge**

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

**Existing Results**

None yet — this is a fresh project.  Wiki was just initialised, no prior
papers / ideas / experiments registered.
## Open Gaps
# Gap Map — React GUI Test Self-Healing

| ID | Gap | Status | Linked papers | Addressed by |
|----|-----|--------|---------------|--------------|
| G1 | No first-class evaluation of **false-heal** (regression-masking) in academic web-test-repair | unresolved | xu2023_guiding_chatgpt_fix, stocco2018_visual_web_test, choudhary2011_water_web_application | idea:001 |
| G2 | All published benchmarks are 2010s server-rendered apps; no React-native benchmark | unresolved | stocco2018_visual_web_test | idea:001 |
| G3 | Repair is purely post-failure; the test-author phase contributes nothing to robustness | unresolved | (all academic) | idea:001 |
| G4 | LLM-based repair uses DOM-only context; component AST + TS types + intent unused | unresolved | xu2023_guiding_chatgpt_fix | idea:001 |
| G5 | No fix memory with provenance ↔ replay across CI runs | unresolved | — | idea:001 |
| G6 | Hallucination control stops at explanation consistency; no executable behavioural oracle | unresolved | xu2023_guiding_chatgpt_fix | idea:001 |

## Key Papers (9 total)
- [paper:al2026_enhancing_e2e_test] Enhancing E2E Test Stability via AI-Assisted Self-Healing: Playwright Healer Agent Case Study
- [paper:authors2025_niodebugger_repairing_nonidempotentoutcome] NIODebugger: Repairing Non-Idempotent-Outcome Tests with an LLM-Based Agent
- [paper:choudhary2011_water_web_application] WATER: Web Application Test Repair
- [paper:joseph2026_beyond_llmbased_test] Beyond LLM-based test automation: A Zero-Cost Self-Healing Approach Using DOM Accessibility Tree Extraction
- [paper:moura2026_reprobreak_dataset_reproducible] ReproBreak: A Dataset of Reproducible Web Locator Breaks
- [paper:pei2023_timebased_repair_asynchronous] Time-based Repair for Asynchronous Wait Flaky Tests in Web Testing
- [paper:rahman2025_utfix_change_aware] UTFix: Change Aware Unit Test Repairing using LLM
- [paper:stocco2018_visual_web_test] Visual Web Test Repair
- [paper:xu2023_guiding_chatgpt_fix] Guiding ChatGPT to Fix Web UI Tests via Explanation-Consistency Checking
## Recent Relationships (16 total)
  idea:001 --inspired_by--> paper:xu2023_guiding_chatgpt_fix
  idea:001 --extends--> paper:stocco2018_visual_web_test
  idea:001 --extends--> paper:al2026_enhancing_e2e_test
  idea:001 --addresses_gap--> gap:G1
  idea:001 --addresses_gap--> gap:G2
  idea:001 --addresses_gap--> gap:G3
  idea:001 --addresses_gap--> gap:G4
  idea:001 --addresses_gap--> gap:G5
  idea:001 --addresses_gap--> gap:G6
  claim:C1 --supports--> idea:001
  claim:C2 --supports--> idea:001
  paper:authors2025_niodebugger_repairing_nonidempotentoutcome --extends--> paper:xu2023_guiding_chatgpt_fix
  idea:001 --contradicts--> paper:moura2026_reprobreak_dataset_reproducible
  idea:001 --extends--> paper:joseph2026_beyond_llmbased_test
  idea:001 --inspired_by--> paper:rahman2025_utfix_change_aware
  idea:001 --extends--> paper:pei2023_timebased_repair_asynchronous
