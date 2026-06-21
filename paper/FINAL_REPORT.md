# Paper Writing Pipeline — Final Report

**Project:** HealReact (React GUI test self-healing diagnostic study)
**Venue:** ICSE-NIER 2027 (4+1 short paper)
**Assurance:** draft (audits run, fixes applied, but bib metadata stops short of full web-lookup canonical resolution)
**Submission-ready:** **no** (camera-ready needs final bib metadata verification + Docker e2e + L4 implementation per roadmap)
**Date:** 2026-06-14

## Pipeline Summary

| Phase | Status | Output |
|-------|--------|--------|
| 0. Assurance setup | ✅ | draft |
| 1. Paper plan | ✅ | `PAPER_PLAN.md` |
| 2. Figures | ✅ | 1 inline TikZ architecture, 4 booktabs tables |
| 3. LaTeX writing | ✅ | 7 sections, 11-entry `references.bib` (after audit pruning) |
| 4. Compilation (tectonic) | ✅ | `main.pdf` (5 pages, 125 KB) |
| 5. Improvement loop (Codex MCP, 2 rounds) | ✅ | R0 5.8/10 → R1 6.8/10 → R2 polish → R3 audit fixes |
| 5.5 Paper claim audit | ⚠ FAIL→FIX | 4 numeric inaccuracies corrected (304 records, wall-clock, 23%→22%, 49%→~50%) |
| 5.8 Citation audit | ⚠ FAIL→FIX | 4 fabricated/wrong-context cites removed; 1 orphan removed; 5 metadata fixes |
| 6 Submission gate | ⏸ deferred | full submission gate not run (still needs Docker e2e + final bib lookup) |

## Score Trajectory

| Round | PDF | Score | Notes |
|-------|-----|------:|-------|
| R0 | `main_round0_original.pdf` | 5.8/10 weak-reject | Oversell on L4 necessity, intent-substrate name mismatch, lower-bound footnote |
| R1 | `main_round1.pdf` | 6.8/10 borderline weak-accept | All CRITICAL fixed, MAJOR mostly fixed |
| R2 | `main_round2.pdf` | (polish, not re-scored) | Residual oracle-necessity + 15% framing softened |
| R3 | `main_round3.pdf` (= current `main.pdf`) | (audit pass) | 4 numeric + 4 fabricated-cite fixes |

## Deliverables (in `paper/`)

- `main.pdf` — current = R3 (5 pp, 125 KB)
- `main_round{0,1,2,3}.pdf` — full history for diff
- `main.tex`, `sections/0[1-7]_*.tex`, `references.bib` — source
- `PAPER_PLAN.md` — Phase 1 outline
- `PAPER_IMPROVEMENT_LOG.md` — per-round fix log
- `FINAL_REPORT.md` — this file

## Key Headline Numbers (all verified vs raw JSON by Phase 5.5)

- **78.7%** silent false-heal under target-absent adversarial probe (59/75)
- **Vanilla = Abstain** prompt-level abstention does not reduce false heal (Δ = 0 cases)
- **80.6%** L1 reachability on `tryghost/koenig` (75/93 across 19 commits)
- **77.3%** L3 top-1 exact-element match on reachable cases (58/75, qwen2.5-coder:7b, v1)
- **62.4%** static repair proxy across full koenig dataset (58/93)
- **+5 / -0** Pareto win from v0→v1 (testId-weighted retrieval + strict-anchor post-filter)
- **3.8%** raw cross-app reach on `payloadcms/payload` (12/319), diagnosed BEM blind spot

## Submission-blocking items remaining

1. **Bib metadata** — 11 entries verified to exist; several remain at corporate-author granularity (`Healenium Contributors`, `Ollama Contributors`, etc.) which is acceptable for many venues but should be tightened to canonical citations for camera-ready.
2. **Docker e2e replay (R1 in roadmap)** — converts 62.4% static proxy into real Playwright pass rate; not required for ICSE-NIER acceptance, but strengthens the paper materially.
3. **L4 behavioural-replay oracle (R3 in roadmap)** — needed for the full method paper; the present short paper makes the empirical case that L4 is the right next step, but does not implement it.
4. **`baseClass` resolver (R2)** — needed to convert 3.8% payload reach into a measurement rather than a hypothesis.

## Remaining issues (non-blocking)

- 3 Overfull \hbox warnings remain (≤ 36pt), all in main-body cells; visually negligible.
- 1 reference to `reproduce.py` in §6 roadmap points to a ReproBreak-side script not under the HealReact repo; this is correct, but a reader-friendly clarification could be added.

## Next steps

1. **Hand-verify final bib metadata** before camera-ready submission.
2. **Implement R1 (Docker replay)** when Docker network access is restored; would upgrade the strongest numeric claim in the paper.
3. **Implement R2 (`baseClass` resolver)** to make F3's cross-app claim measured rather than hypothesised.
4. **Submit to ICSE-NIER 2027** (deadline ~Nov 2026 per recent NIER tracks).
