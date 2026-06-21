---
type: idea
node_id: idea:001
title: "HealReact — AST-anchored intent locators + fault-localising LLM healer with mutation-grounded false-heal evaluation"
stage: proposed
based_on: [paper:xu2023_guiding_chatgpt_fix, paper:stocco2018_visual_web_test, paper:al2026_enhancing_e2e_test]
target_gaps: [gap:G1, gap:G2, gap:G3, gap:G4, gap:G5, gap:G6]
outcome: unknown
added: 2026-06-14
---

# HealReact

## One-line hypothesis
Baking an LLM-extracted intent label into the React component AST at
write time, and verifying every LLM-generated repair against a
behavioural-replay oracle, jointly raises repair success **without**
raising false-heal.

## Why it's novel (vs SOTA Xu+25)
1. Write-time AST + intent contribution (Xu+25 is purely post-failure).
2. Behavioural-replay oracle for anti-false-heal (Xu+25 uses lexical
   explanation-consistency only).
3. React-native benchmark `ReactHealBench` with mutation-grounded
   false-heal as primary metric (no prior academic benchmark does this).

## Pilot
PAPER-ONLY at this stage. Pilot to be run by `/experiment-bridge`:
1 React app × 5 breakages × 3 mutations. Go/no-go on repair ≥3/5 AND
defect-flag ≥2/3.

## Linked claims
- claim:C1 (repair-success ≥ Xu+25 +10pp)
- claim:C2 (false-heal ≤ ½ Xu+25)
- claim:C3 (intent-label stability ≥ 80%)
- claim:C4 (median cost ≤ $0.05 / heal)

## Failure modes already considered (do NOT re-propose)
See `idea-stage/IDEA_REPORT.md §2.1` for eliminated ideas:
- idea-2 (pure visual + VLM healer) — too brittle to theming
- idea-3 (RL from logged repairs) — cold-start, no data
- idea-4 (IDE copilot only) — strictly weaker than IDEA-1
- idea-6 (cross-framework common-IR) — too broad as main idea
- idea-8 (heal-budget controller) — engineering, no research depth
