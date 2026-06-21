# HealReact — Architecture (one-page)

```
┌──────────────────────────────────────────────────────────────────────┐
│ L1 — WRITE TIME (zero LLM at runtime)                               │
│                                                                      │
│   React source ──► AST extractor (ts-morph)  ──► LocatorSheet.json   │
│   (src/ast/extractor.ts)                          (one record per    │
│                                                    interactive JSX)  │
│                            │                                         │
│                            ▼                                         │
│              Intent labeller (LLM, batch+cached)                     │
│              (src/ast/intent_labeller.ts — stage 2)                  │
│                            │                                         │
│                            ▼                                         │
│              Optional codemod: bake `data-intent="..."` into JSX     │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼ at test time
┌──────────────────────────────────────────────────────────────────────┐
│ Runtime helper:  intent(page, "submit-order-button")                │
│  (src/runner/intent.ts)                                             │
│                                                                      │
│  Ladder: getByRole+name → getByLabel → getByTestId → data-intent →  │
│          AST-relative XPath → visual fingerprint                    │
│                                                                      │
│  If any rung resolves → return Locator (no LLM, no cost).           │
│  If ALL rungs fail → throw → caught by L2 capture                   │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼ on failure
┌──────────────────────────────────────────────────────────────────────┐
│ L2 — CAPTURE & DIFF                                                  │
│   Capture: error, console, network HAR, DOM, fiber-tree, screenshot │
│   Diff: LocatorSheet@green vs @now  →  localise component change    │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L3 — LLM CLOSED-LOOP REPAIR  (src/heal/healer.ts)                   │
│                                                                      │
│   1. Lookup fix-memory  ── hit?  ── try patch                       │
│            │ miss                  │                                 │
│            ▼                       ▼                                 │
│   2. LLM proposes patch       3. Behavioural-replay ORACLE          │
│      {selector, wait, step}      (src/oracle/replay.ts)              │
│      or LIKELY_REAL_DEFECT       compare canonicalised HAR vs       │
│            │                     pre-break green baseline           │
│            ▼                           │                             │
│   3. Oracle gates commit  ◄────────────┘                             │
│      ok → record in fix-memory, post PR comment with diff           │
│      reject → mark LIKELY_REAL_DEFECT, fail loud                    │
└──────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│ L4 — LEARN & INTEGRATE                                              │
│   Fix memory: keyed by (componentHash, failureFingerprint)          │
│   CI plugin: PR review comment with diff (never auto-commit)        │
│   Heal budget: alert if >X% suite healed in one run (Sun+26)         │
└──────────────────────────────────────────────────────────────────────┘
```

Each layer has its own evaluation block in `refine-logs/EXPERIMENT_PLAN.md`:
L1+intent → E2; L3 → E1; oracle → E4 (FP-rate) + E1 (false-heal); L4 fix-memory → A3.
