# Paper Improvement Log — HealReact ICSE-NIER

**Reviewer model:** Codex MCP (gpt-5.5-class), high reasoning effort, fresh thread per round.

## Round 0 → 1
- **Score:** 5.8 / 10 (weak-reject)
- **CRITICAL (3):** behavioural-oracle necessity overclaim; mis-stated "lower bound" footnote; "Intent-Anchored Substrate" name not matching evidence
- **MAJOR (5):** 35-50 % projection inside table; ReactHealBench / C1-C4 in roadmap; insufficient method detail; strawman framing of Xu/Joseph; "generalisable lesson" overstatement
- **Fixes applied:**
  - Title: `Intent-Anchored Substrate` → `Anchor-Aware Static Substrate`
  - §3: explicit "intent labels are synthetic-only; real-data results use anchors"
  - §1 footnote: removed false "lower bound" claim, replaced with "correlated, neither lower nor upper bound"
  - §4 cross-app table: dropped projected reach row; payload reports raw 3.8 % only
  - §6: removed ReactHealBench / C1-C4 / pre-registered targets paragraph
  - §4: added shared L3 protocol paragraph (model, temperature, prompt contents, retrieval weights, tie handling)
  - §2: softened Xu/Joseph framing to "metrics target a different failure mode" (no flawedness implied)
  - §5: changed "generalisable lesson" to "local design lesson for HealReact"
  - §7: aligned conclusion with new claim strength
  - 4/5 MINOR wording fixes (bib metadata deferred to Phase 5.8 citation audit)

## Round 1 → 2
- **Score:** 6.8 / 10 (borderline weak-accept), +1.0 from R1
- **All CRITICAL resolved.** All MAJOR resolved or partial.
- **Remaining 5 issues (this round):**
  1. Residual "necessity" wording in F1 caption + §4 interpretation
  2. 15 % unattended-workload estimate not labelled as back-of-envelope
  3. Payload "sampling 307 misses" claim too strong
  4. Intent labeller still has some architectural prominence
  5. Stale "C3" reference; "open scripts" language without packaged artefact
- **Fixes applied:**
  - F1 caption: "necessity is established" → "need is motivated"
  - §4: "necessary next step" → "evaluating L4 as the next layer"
  - §4: 15 % estimate now explicitly "back-of-the-envelope risk estimate, not a measured deployment rate"
  - §4: "sampling 307 misses" → "spot-checking a non-systematic sample"
  - §3: stale "C3" reference removed
  - §6 Replication: "open scripts" → enumerated script names + promise of artefact bundle at camera-ready
  - F1 caption: clarified L1 is "AST anchor substrate" (not "AST+intent")

## Deliverables
- `paper/main.pdf` (current = round 2)
- `paper/main_round0_original.pdf`
- `paper/main_round1.pdf`
- `paper/main_round2.pdf`
- `paper/PAPER_PLAN.md`
- `paper/PAPER_IMPROVEMENT_LOG.md` (this file)

## Page budget
- All three versions: **5 pages** (ICSE-NIER 4+1 limit, on budget)

## Submission gates NOT YET run
- Phase 5.5: `/paper-claim-audit` (numerical fidelity vs raw JSONs)
- Phase 5.8: `/citation-audit` (bib entries existence/metadata/context — currently 17 entries with several `et al.`/`Anonymous` placeholders that need lookup)
- Phase 6: `verify_paper_audits.sh` submission gate (would block on the placeholder bib entries until fixed)
