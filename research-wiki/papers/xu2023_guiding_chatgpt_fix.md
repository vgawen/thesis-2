---
type: paper
node_id: paper:xu2023_guiding_chatgpt_fix
title: "Guiding ChatGPT to Fix Web UI Tests via Explanation-Consistency Checking"
authors: ["Zhuolin Xu", "Qiushi Li", "Shin Hwei Tan"]
year: 2023
venue: "arXiv"
external_ids:
  arxiv: "2312.05778"
  doi: null
  s2: null
tags: ["test-repair", "llm", "web", "sota-baseline"]
added: 2026-06-14T04:27:40Z
---

# Guiding ChatGPT to Fix Web UI Tests via Explanation-Consistency Checking

## One-line thesis
ChatGPT + explanation-validator improves attribute-prioritised web UI test repair after WATER/VISTA local matching.

## Problem / Gap
_TODO._

## Method
_TODO._

## Key Results
_TODO._

## Assumptions
_TODO._

## Limitations / Failure Modes
_TODO._

## Reusable Ingredients
_TODO._

## Open Questions
_TODO._

## Claims
_TODO._

## Connections
_Edges are recorded in `graph/edges.jsonl`; summarize here for human readers._

## Relevance to This Project
_TODO._

## Abstract (original)

> The rapid evolution of Web UI incurs time and effort in UI test maintenance. Prior techniques in Web UI test repair focus on locating the target elements on the new Webpage that match the old ones so that the corresponding broken statements can be repaired. These techniques usually rely on prioritizing certain attributes (e.g., XPath) during matching where the similarity of certain attributes is ranked before other attributes, indicating that there may be bias towards certain attributes during matching. To mitigate the bias, we present the first study that investigates the feasibility of using prior Web UI repair techniques for initial matching and then using ChatGPT to perform subsequent matching. Our key insight is that given a list of elements matched by prior techniques, ChatGPT can leverage language understanding to perform subsequent matching and use its code generation model for fixing the broken statements. To mitigate hallucination in ChatGPT, we design an explanation validator that checks if the provided explanation for the matching results is consistent, and provides hints to ChatGPT via a self-correction prompt to further improve its results. Our evaluation on a widely used dataset shows that the ChatGPT-enhanced techniques improve the effectiveness of existing Web test repair techniques. Our study also shares several important insights in improving future Web UI test repair techniques.

