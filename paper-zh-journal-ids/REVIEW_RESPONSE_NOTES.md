# Review Response Notes

## R1: Model scope
- Added a frontier-model F1 probe on the same 75 reachable koenig cases and the same ground-truth removal protocol.
- New artifacts: `_false_heal_probe_gpt4o_vanilla.json`, `_false_heal_probe_gpt4o_abstain.json`.
- Result: GPT-4o Vanilla produced 63/75 false heals (84.0%); GPT-4o Abstain produced 51/75 false heals (68.0%), with error=0 after request-delay and retry handling.
- Paper locations: abstract, §1, §3/F1, §5 limitations, §6 conclusion.

## R2: HealReact architecture mismatch
- Reframed HealReact as an L1/L3 diagnostic measurement substrate, not a complete evaluated L1-L4 self-healing system.
- Explicitly marked L2/L4 as design placeholders and future work.
- Paper locations: abstract, §1 contributions, §2/§L1 section title and figure caption.

## R3: F2 statistical significance
- Compressed F2 and retained McNemar non-significance.
- Reframed the deterministic levers as auxiliary engineering evidence rather than a central scientific claim.
- Paper locations: §3/F2 and §5 deterministic-lever discussion.

## R4: Static proxy vs E2E rate
- Added selector-resolution caveats to the abstract and conclusion.
- Kept the Docker pilot only as evidence that a gap exists between static selector matching and runtime pass rate, not as a pass-rate estimate.
- Paper locations: abstract, §1 footnote, §5 limitations, §6 conclusion.
