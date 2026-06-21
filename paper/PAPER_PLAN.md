# PAPER_PLAN — HealReact (short paper / empirical-position)

**Date:** 2026-06-14
**Status:** Phase 1 draft (Workflow 3, paper-plan)
**Source:** `refine-logs/FINAL_PROPOSAL.md` + `healreact/docs/{L1_REPORT,C_STATIC_REPORT}.md` + `review-stage/AUTO_REVIEW_R3.md`

---

## 0. Scope decision (read this first)

The full FINAL_PROPOSAL targets a 4-layer system (L1 AST intent + L2 runtime DOM + L3 LLM healer + L4 behavioural-replay oracle) and a fresh React-only benchmark.

What we actually built and measured this round:
- L1 AST extractor + intent labeller + calibration rules (A–J)
- L3 healer baseline + v1 (retrieval + strict-anchor)
- L4-flavoured **false-heal probe** (adversarial: ground-truth removed)
- Cross-app generalisation probe on a second React+Playwright codebase

What we did NOT build:
- L2 runtime DOM capture / semantic diff
- L4 behavioural-replay oracle on a recorded green build (we only have the adversarial probe, which is a *proxy* for the oracle's necessity, not the oracle itself)
- A direct comparison vs Xu+25 / Joseph 2026 baselines
- Docker-replayed end-to-end pass rate (62.4 % is a static proxy, not Playwright pass)

**Honest scope of this paper:**
> An empirical / position paper showing that (a) bare LLM healers silently false-heal 78.7 % of the time on real-world Playwright breaks when the target element is absent, (b) prompt-level abstention does not mitigate this, and (c) HealReact's L1 AST + intent layer provides a falsifiable static substrate (80.6 % reachability on koenig, with diagnosed BEM blind spots on a second codebase) on top of which a behavioural oracle (L4) becomes a necessary next step.

This is a 6–8 page short paper, not the 10–12 page method paper. The roadmap to the full method paper is explicit in §6.

---

## 1. Title (proposed)

> **Silent False-Heal in LLM-Driven Playwright Repair: A Diagnostic Study and an Intent-Anchored Substrate for React Tests**

Alternatives:
- *"When Self-Healing Lies: Measuring 78 % Silent False-Heal in LLM Playwright Repair, and a Static Substrate to Stop It"*
- *"HealReact L1: An AST + Intent Substrate that Makes the Behavioural-Oracle Question Concrete"*

---

## 2. Target venue + format

| Venue | Track | Page limit | Fit | Rationale |
|-------|-------|------------|-----|-----------|
| **ICSE 2027 NIER** | New Ideas & Emerging Results | 4 + 1 ref | **best fit** | Short, motivation-heavy, empirical findings + roadmap; perfect for "we measured a 78 % failure mode, here's why and what's next" |
| **FSE 2026/27 Ideas / Tool** | Short / Tool | 4 + 1 ref | strong fit | Same shape; FSE values negative-result + empirical |
| **ISSTA 2027 Tool Demos** | Tool | 4 pages | medium fit | If we ship the HealReact artefact; otherwise too tool-track-y |
| **MSR 2027** | Mining track | 8 + 2 ref | strong fit if we lean on ReproBreak | "Empirical study of LLM repair on the ReproBreak Playwright slice" — cleaner story, longer page budget |
| ICSE / FSE / ISSTA full | full | 10–12 pages | poor fit **for this round** — needs L2/L4 implementation + baselines |

**Recommended primary target: ICSE-NIER** (4 + 1). Fallback: **FSE Ideas / MSR**.

User to confirm. Plan below assumes **ICSE-NIER (4 + 1)**.

---

## 3. Claims–Evidence matrix

| # | Claim | Evidence file(s) | Headline number | Robustness notes |
|---|-------|------------------|-----------------|------------------|
| **C-MOT** | Bare LLM healers silently false-heal in adversarial-by-construction Playwright break cases. | `healreact/bench/cases/koenig/_false_heal_probe_vanilla.json` | **78.7 % false-heal rate** (59 / 75; abstain 13 / 75; unresolved 3 / 75) | adversarial-by-construction; upper bound, not expected rate. Stated explicitly in claim. |
| **C-PROMPT-FAIL** | Soft prompt-level abstention guardrails do not reduce the false-heal rate. | `_false_heal_probe_abstain.json` (identical 59/75) | **Δ = 0 cases** between vanilla and ABSTAIN-prompted | identical input model + retrieval; only the prompt changed |
| **C-L1** | An AST + intent layer that recognises custom anchor-bearing React components reaches 80.6 % of real Playwright break targets statically. | `_resolve_*` per-commit JSONs + `C_STATIC_REPORT §4` | **75 / 93 = 80.6 %** on koenig | resolver heuristics documented; honesty audit in §9 retires earlier 98 % / 85 % inflated claims |
| **C-L3** | Given the L1 substrate, a small local LLM (qwen2.5-coder:7b) can propose the correct repair top-1 in 77.3 % of reachable breaks. | `_heal_baseline.json` (v1) | **58 / 75 = 77.3 %**; end-to-end static proxy 58 / 93 = 62.4 % | "static repair proxy" ≠ Playwright pass rate (deferred, Docker δ) |
| **C-LEVERS** | Two cheap, deterministic levers (testId-weighted retrieval + strict-anchor post-filter) Pareto-improve L3 with zero regressions. | v0 vs v1 row in `_heal_baseline.{v1,}.json` | 53 / 75 → 58 / 75; strict-anchor triggered 2 / 75, both correct | 5 newly-correct cases (ids 615, 702, 703, 715, 716), 0 regressions |
| **C-CROSS** | Cross-app generalisation is gated by anchor-culture diversity; static-only extractors miss BEM template-literal classes. | `cases/payload/_summary.json` + §9 of report | 12 / 319 = **3.8 % raw reach** on payload; diagnosed BEM blind spot; projected 35–50 % with baseClass resolver | shallow probe (HEAD-only, no per-commit pair); both raw and projected reported |

The paper claims hold iff all six are visible in the result tables and the honest-framing caveats are present in §4–§6.

---

## 4. Section plan (ICSE-NIER, 4 + 1)

| § | Section | Pages | Content |
|---|---------|------:|---------|
| 1 | Introduction | 0.75 | Set up the silent-false-heal problem with the 78.7 % number in the first paragraph. State the three contributions (probe, L1 substrate, levers). Roadmap. |
| 2 | Background & related work | 0.5 | ReproBreak (benchmark we extend); Xu+25 (LLM healer + explanation validator); Joseph 2026 (zero-cost ladder); UTFix (cheap-then-expensive verifier pattern). Frame each in one sentence; no general survey. |
| 3 | The HealReact L1 substrate | 1.0 | (a) AST extractor (`ts-morph`, recognises any JSX bearing stable anchor); (b) intent labeller (qwen2.5:3b solo + grouped, calibrator A–J); (c) Locator resolver as a falsifiable lens; (d) headline: 304 records, 80.6 % reach on koenig. One figure (architecture). |
| 4 | Three empirical findings | 1.5 | **4.1** Silent false-heal probe (78.7 %, table) and the abstain-prompt no-op (table). **4.2** L3 baseline v0 vs v1 levers (Pareto, table). **4.3** Cross-app gap on payload (3.8 % raw, BEM diagnosis, projected 35–50 %). |
| 5 | Discussion: implications + limitations | 0.5 | What 78.7 % means for unattended CI healing. Why soft prompts fail. Why a behavioural oracle (L4) is necessary, not optional. Limitations: single-model L3 (qwen 7B), single-app pilot, static proxy ≠ Playwright pass, BEM blind spot. Threats to validity. |
| 6 | Roadmap to the full method paper | 0.5 | Concrete next steps: Docker replay → executable pass rate; baseClass resolver → cross-app reach; L4 behavioural oracle on recorded green build; baseline comparison vs Joseph / Xu. Pre-registered targets carried over from FINAL_PROPOSAL C1–C4. |
| 7 | Conclusion | 0.25 | 3-sentence summary. |
| – | References | 1.0 | 12–18 entries. |

**Total: 5 pages.** First-draft buffer: §3 and §4 can each lose 0.25 page if overfull.

---

## 5. Figure / table plan

### Figures (auto-generated in Phase 2)

| ID | Type | Source | Tool | Caption |
|----|------|--------|------|---------|
| F1 | Architecture (HealReact pipeline: L1 → L3 → optional oracle) | hand-spec | `/figure-spec` (deterministic SVG) | "HealReact's L1–L3 pipeline. The dashed L4 layer (behavioural oracle) is the necessary next step motivated by the false-heal probe in §4.1." |
| F2 | Bar chart: false-heal probe vanilla vs abstain (abstain / false-heal / unresolved stacked) | `_false_heal_probe_{vanilla,abstain}.json` | matplotlib | "Adversarial false-heal rate: vanilla 78.7 %, abstain-prompt 78.7 %. Soft prompt-level abstention does not reduce false heals." |
| F3 | Per-commit reachability across 19 koenig commits (sorted bar) | `_resolves/*.json` | matplotlib | "Per-commit L1 reachability across the 19 koenig commits in ReproBreak. Average 80.6 %; min commit 50 %, max 100 %." |

### Tables (auto-generated in Phase 2 / written in Phase 3)

| ID | Content | Source |
|----|---------|--------|
| T1 | L3 v0 → v1 lever Pareto: top-1 / valid-selector / wall-clock; rows = variants, columns = metrics | `_heal_baseline.{v1,}.json` + commit log |
| T2 | Cross-app comparison: anchor culture distribution (testid / data-kg / aria / CSS class) × repo (koenig vs payload), with raw reach and projected reach | `C_STATIC_REPORT §9` |
| T3 | Honesty-audit table reproduced from `C_STATIC_REPORT §9` (was → now → reason) — fits in §5 or appendix | `C_STATIC_REPORT §9` |

**Manual figures:** none required for the short paper. Architecture diagram (F1) goes through `/figure-spec` (deterministic).

---

## 6. Citation scaffold (12–18 entries)

Required, with `.bib` key suggestion:

| key | what it cites | role |
|-----|---------------|------|
| `mouraReproBreak2026` | ReproBreak (arXiv 2605.12158) | **primary benchmark substrate** |
| `joseph2026zerocost` | Joseph 2026 zero-cost accessibility ladder (arXiv 2603.20358) | direct technical baseline (L1 deterministic) |
| `xu2025icst` | Xu+25 LLM-healer + explanation validator (ICST'25) | direct technical baseline (L3) |
| `utfix2025` | UTFix cheap-then-expensive verifier | inspiration for our L1 verifier + L3 confidence flow |
| `playwright2025` | Microsoft Playwright docs (locator API, getByRole/getByTestId) | system under study |
| `vista733` | VISTA-733 (legacy Selenium benchmark) | older benchmark context |
| `healenium` | Healenium | popular practitioner baseline |
| `traf` | TRaf (visual + DOM repair) | visual-heal baseline class |
| `cypress2024` | Cypress framework | second target framework (out-of-scope for this paper, mentioned in §6) |
| `lexicalRichText` | Lexical / koenig-lexical | needed to explain L2 motivation (runtime-generated `<p>` nodes) |
| `tsmorph` | ts-morph | extractor implementation |
| `qwenCoderTech2024` | qwen2.5-coder technical report | LLM we use |
| `ollama` | Ollama (optional) | inference runtime |
| `bemMethodology` | BEM CSS methodology | needed to explain the payload finding |
| `cssModules` | CSS Modules | same |
| `payloadCMS` | Payload CMS | second-app subject |
| `koenig` | tryghost/koenig | primary subject |
| `astTools` *(opt)* | ast-tools | inspiration cited in FINAL_PROPOSAL |

Audit gate (Phase 5.8) will hit ~16 entries; tractable.

---

## 7. Style + tone notes

- **Numbers first**, then mechanism. The first paragraph must contain "78.7 %", "80.6 %", "62.4 %", "3.8 %".
- **Honesty-first wording.** Use "static repair proxy", not "end-to-end repair" (Round 3 audit). Use "adversarial-by-construction" when introducing the 78.7 %. Never refer to L4 as "implemented".
- **No marketing adjectives.** Don't write "novel", "comprehensive", "extensive", "robust" without a metric next to them. ICSE-NIER reviewers punish this fast.
- **Replication paragraph in §6.** One paragraph stating "all numbers reproducible via `bench/scripts/{heal_baseline,false_heal_probe,cross_app_probe}.py` against `_heal_baseline.json` + `_false_heal_probe_*.json`".

---

## 8. Risks for this short paper

| Risk | Mitigation |
|------|-----------|
| Reviewer says "this is just a probe, not a method paper" | The framing is explicit ICSE-NIER / position paper. The contributions are scoped to (i) empirical finding, (ii) substrate, (iii) two deterministic levers — not a full method. |
| Reviewer says "78.7 % is adversarial, doesn't apply to real workloads" | §4.1 already states upper-bound framing. We can additionally report the *expected* false-heal rate on the 18 / 93 truly-unreachable koenig cases (a smaller, naturalistic subset) — that number is ≤ 18/93 × 78.7 % ≈ 15 % silent false-heal across the full koenig workload, which is still a strong number. |
| Reviewer says "cross-app payload 3.8 % is embarrassing" | We explicitly diagnose it as a BEM/template-literal blind spot, project 35–50 %, and pre-register the fix as immediate roadmap. This converts a weakness into a falsifiable contribution. |
| Reviewer asks for L2 / L4 implementation | Out of scope for NIER. Roadmap §6 lists them with concrete deliverables. |
| Page overflow at NIER 4+1 | Trim §3 by 0.25 page (drop calibration A–J details to appendix); §6 already lean. |

---

## 9. What goes into the paper directory (Phase 2 onward)

```
paper/
├── PAPER_PLAN.md         # this file
├── main.tex              # Phase 3
├── sections/
│   ├── 00_abstract.tex
│   ├── 01_intro.tex
│   ├── 02_background.tex
│   ├── 03_l1_substrate.tex
│   ├── 04_findings.tex
│   ├── 05_discussion.tex
│   ├── 06_roadmap.tex
│   └── 07_conclusion.tex
├── references.bib        # Phase 3
├── figures/
│   ├── f1_architecture.{svg,pdf}     # Phase 2b
│   ├── f2_false_heal.{py,pdf}        # Phase 2
│   ├── f3_reachability_per_commit.{py,pdf}
│   └── latex_includes.tex
└── main.pdf              # Phase 4
```

---

## 10. Next action

User decision needed on **venue** (default ICSE-NIER 4+1, alternative MSR 8+2 = more room for L3 lever details and per-commit reach distribution). Once confirmed:

1. **Phase 2** — generate F2/F3 from existing JSONs and F1 via `/figure-spec`.
2. **Phase 3** — write 7 sections + `.bib`.
3. **Phase 4** — `latexmk`.
4. **Phase 5** — `/auto-paper-improvement-loop` 2 rounds.
5. **Phase 5.5 / 5.8** — claim audit + citation audit (gates).
