# Gap Map — React GUI Test Self-Healing

| ID | Gap | Status | Linked papers | Addressed by |
|----|-----|--------|---------------|--------------|
| G1 | No first-class evaluation of **false-heal** (regression-masking) in academic web-test-repair | unresolved | xu2023_guiding_chatgpt_fix, stocco2018_visual_web_test, choudhary2011_water_web_application | idea:001 |
| G2 | All published benchmarks are 2010s server-rendered apps; no React-native benchmark | unresolved | stocco2018_visual_web_test | idea:001 |
| G3 | Repair is purely post-failure; the test-author phase contributes nothing to robustness | unresolved | (all academic) | idea:001 |
| G4 | LLM-based repair uses DOM-only context; component AST + TS types + intent unused | unresolved | xu2023_guiding_chatgpt_fix | idea:001 |
| G5 | No fix memory with provenance ↔ replay across CI runs | unresolved | — | idea:001 |
| G6 | Hallucination control stops at explanation consistency; no executable behavioural oracle | unresolved | xu2023_guiding_chatgpt_fix | idea:001 |
