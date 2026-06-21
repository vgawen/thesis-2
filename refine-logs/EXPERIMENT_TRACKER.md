# EXPERIMENT_TRACKER — HealReact

| ID | Block | Status | Start | End | Output | Notes |
|----|-------|--------|-------|-----|--------|-------|
| Pilot | end-to-end on 1 app × 5 br × 3 mut | PENDING | — | — | `pilot/pilot_results.jsonl` | gate to E1 |
| B1 | benchmark construction | PENDING | — | — | `bench/ReactHealBench/` | needed by E1–E5 |
| E1 | main results | PENDING | — | — | `results/E1_main.csv` | claims C1, C2 |
| E2 | intent-label stability | PENDING | — | — | `results/E2_intent.csv` | claim C3, weakness W1 |
| E3 | mutation-filter sensitivity | PENDING | — | — | `results/E3_mut_sweep.csv` | weakness W2 |
| E4 | oracle FP rate | PENDING | — | — | `results/E4_oracle_fp.csv` | weakness W4 |
| E5 | cost / latency | PENDING | — | — | `results/E5_cost.csv` | claim C4, weakness W6 |
| A1 | ablate intent labels | PENDING | — | — | `results/A1.csv` | only after E1 passes |
| A2 | ablate oracle | PENDING | — | — | `results/A2.csv` | only after E1 passes |
| A3 | ablate fix memory | PENDING | — | — | `results/A3.csv` | only after E1 passes |
| A4 | DOM-only context | PENDING | — | — | `results/A4.csv` | only after E1 passes |
