# HealReact

AST-anchored **intent locators** + fault-localising LLM **healer** + behavioural-**replay oracle** for React E2E test self-healing, evaluated with mutation-grounded **false-heal** as a primary metric.

> Research artefact for: `idea-stage/IDEA_REPORT.md` → IDEA-1.
> Spec: `refine-logs/FINAL_PROPOSAL.md`, plan: `refine-logs/EXPERIMENT_PLAN.md`.

## Layout

```
healreact/
├── src/
│   ├── ast/         L1 — write-time AST extraction (ts-morph)
│   ├── heal/        L3 — LLM closed-loop repair
│   ├── oracle/      L3 — behavioural-replay verifier
│   ├── memory/      L4 — fix memory keyed by component-hash
│   └── runner/      Playwright integration helpers (intent(...))
├── tests/
│   ├── pilot/       Pilot 5×3 matrix (`/research-pipeline` Stage 2 gate)
│   └── e2e/         Full ReactHealBench E2E suite
├── bench/
│   └── ReactHealBench/
│       ├── apps/        cloned apps (gitignored)
│       ├── breakages/   broken-statement JSONL per app
│       └── results/     per-run metrics
├── scripts/         setup / fetch / run scripts
└── docs/            SETUP.md, ARCHITECTURE.md
```

## Quickstart

```bash
cd healreact
npm install
npx playwright install chromium

npm run extract -- --src ../bench/ReactHealBench/apps/react-shopping-cart/src   # L1 sanity check

npm run bench:fetch   # clones the 3 benchmark apps

# Once OPENAI_API_KEY is set (or local model configured):
npm run test:pilot
```

See `docs/SETUP.md` for keys, MCP setup, and infra notes.
