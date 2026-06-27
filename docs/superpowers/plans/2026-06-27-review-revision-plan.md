# Review Revision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 根据审稿意见修订《Playwright 测试隐性误修复研究》，把论文定位从“完整系统论文”收紧为“隐性误修复的诊断性实证测量”，并补充至少一个前沿大模型的 F1 对照实验。

**Architecture:** 修订分为实验补强与论文叙事重写两条线。实验侧复用 `healreact/bench/scripts/false_heal_probe.py` 的候选移除协议，新增可审计的前沿模型产物；写作侧只修改 `paper-zh-journal-ids/`，弱化 HealReact 系统贡献，强调选择器层静态代理指标、F1 软提示失效、F3 锚点文化泛化风险，并压缩 F2。

**Tech Stack:** LaTeX (`ctexart`, XeLaTeX/BibTeX), Python 3 bench scripts, JSON artifacts, Ollama local model, optional OpenAI/Anthropic-compatible chat backend for frontier-model probing.

---

## File Map

- Modify: `healreact/bench/scripts/false_heal_probe.py`
  - Add a backend abstraction so the same F1 protocol can call the current Ollama model and one frontier model.
  - Preserve the current default behavior for `qwen2.5-coder:7b`.
- Create: `healreact/bench/cases/koenig/_false_heal_probe_gpt4o_vanilla.json`
  - Frontier-model F1 Vanilla output on the same 75 reachable koenig cases.
- Create: `healreact/bench/cases/koenig/_false_heal_probe_gpt4o_abstain.json`
  - Frontier-model F1 Abstain output on the same 75 reachable koenig cases.
- Modify: `healreact/bench/ARTIFACT_MANIFEST.md`
  - Add model name, provider/backend, decoding parameters, commands, and checksums for the new F1 artifacts.
- Modify: `paper-zh-journal-ids/main.tex`
  - Update Chinese/English abstract to state the study is a selector-level diagnostic measurement.
  - Add the frontier-model F1 headline if the experiment is completed.
- Modify: `paper-zh-journal-ids/sections/01_intro.tex`
  - Reframe contributions toward problem diagnosis.
  - Reduce system-completeness language around HealReact.
- Modify: `paper-zh-journal-ids/sections/03_l1_substrate.tex`
  - Make L1/L3 implemented vs L2/L4 design-placeholder status impossible to miss.
- Modify: `paper-zh-journal-ids/sections/04_findings.tex`
  - Add frontier-model F1 table/paired comparison.
  - Shorten F2 narrative.
  - Keep F3 as the second major empirical insight.
- Modify: `paper-zh-journal-ids/sections/05_discussion.tex`
  - Update model-scope limitation after the frontier probe.
  - Strengthen static proxy vs E2E runtime caveat.
- Modify: `paper-zh-journal-ids/sections/07_conclusion.tex`
  - State that all headline success/risk numbers are selector-resolution diagnostics unless explicitly marked as Docker replay.
- Test/Build: `paper-zh-journal-ids/main.pdf`
  - Recompile and check for unresolved refs, duplicate labels, overfull boxes, and page count.

## Task 1: Freeze Current Baseline

**Files:**
- Read: `paper-zh-journal-ids/main.tex`
- Read: `paper-zh-journal-ids/sections/*.tex`
- Read: `healreact/bench/ARTIFACT_MANIFEST.md`
- Read: `healreact/bench/cases/koenig/_false_heal_probe_vanilla.json`
- Read: `healreact/bench/cases/koenig/_false_heal_probe_abstain.json`

- [ ] **Step 1: Record git status**

Run:

```bash
git status --short
```

Expected: note any pre-existing dirty files before editing. Do not revert unrelated user changes.

- [ ] **Step 2: Compile the current paper**

Run:

```bash
cd paper-zh-journal-ids
xelatex -interaction=nonstopmode main.tex
bibtex main
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

Expected: `main.pdf` builds with no unresolved references. Existing underfull warnings are acceptable; overfull boxes should be recorded before later edits.

- [ ] **Step 3: Capture current F1 counts**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path("healreact/bench/cases/koenig")
for name in ["vanilla", "abstain"]:
    p = root / f"_false_heal_probe_{name}.json"
    j = json.loads(p.read_text())
    print(name, {
        "model": j.get("model"),
        "n": j.get("n"),
        "abstain": j.get("abstain"),
        "false_heal": j.get("false_heal"),
        "unresolved": j.get("unresolved"),
        "false_heal_rate_pct": j.get("false_heal_rate_pct"),
    })
PY
```

Expected:

```text
vanilla {'model': 'qwen2.5-coder:7b', 'n': 75, 'abstain': 13, 'false_heal': 59, 'unresolved': 3, 'false_heal_rate_pct': 78.7}
abstain {'model': 'qwen2.5-coder:7b', 'n': 75, 'abstain': 13, 'false_heal': 59, 'unresolved': 3, 'false_heal_rate_pct': 78.7}
```

- [ ] **Step 4: Commit baseline note if this work will be long-running**

Run only if the user wants commits:

```bash
git add docs/superpowers/plans/2026-06-27-review-revision-plan.md
git commit -m "docs: add review revision plan"
```

Expected: a small docs-only commit. Skip if the user did not ask for commits.

## Task 2: Add Frontier-Model F1 Probe

**Files:**
- Modify: `healreact/bench/scripts/false_heal_probe.py`
- Create: `healreact/bench/cases/koenig/_false_heal_probe_gpt4o_vanilla.json`
- Create: `healreact/bench/cases/koenig/_false_heal_probe_gpt4o_abstain.json`
- Modify: `healreact/bench/ARTIFACT_MANIFEST.md`

- [ ] **Step 1: Add CLI parameters without changing defaults**

In `healreact/bench/scripts/false_heal_probe.py`, extend `argparse` with:

```python
ap.add_argument("--backend", choices=["ollama", "openai-compatible"], default=os.environ.get("HEALREACT_BACKEND", "ollama"))
ap.add_argument("--model", default=os.environ.get("HEALREACT_HEAL_MODEL", MODEL))
ap.add_argument("--base-url", default=os.environ.get("HEALREACT_OPENAI_BASE_URL", "https://api.openai.com/v1"))
ap.add_argument("--api-key-env", default="OPENAI_API_KEY")
```

Expected: running the script with no new flags still uses Ollama and `qwen2.5-coder:7b`.

- [ ] **Step 2: Replace the direct `chat(MODEL, ...)` call with a backend wrapper**

Add this function near the existing imports:

```python
def chat_with_backend(args, system_prompt: str, user_prompt: str) -> str:
    if args.backend == "ollama":
        return chat(args.model, system_prompt, user_prompt)

    import urllib.request

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        raise RuntimeError(f"{args.api_key_env} is not set")

    payload = {
        "model": args.model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    req = urllib.request.Request(
        args.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]
```

Then replace:

```python
raw = chat(MODEL, system_prompt, user_prompt)
```

with:

```python
raw = chat_with_backend(args, system_prompt, user_prompt)
```

Expected: no dependency beyond Python standard library is introduced.

- [ ] **Step 3: Record backend metadata in JSON summary**

Change the summary model fields to:

```python
"backend": args.backend,
"model": args.model,
"base_url": args.base_url if args.backend == "openai-compatible" else None,
```

Expected: future artifacts identify whether they came from Ollama or an external frontier API.

- [ ] **Step 4: Run the old Ollama probe as a regression check**

Run:

```bash
cd healreact/bench/scripts
python3 false_heal_probe.py --prompt vanilla --out ../cases/koenig/_tmp_false_heal_probe_vanilla_regression.json
```

Expected: counts match the current Vanilla artifact: `abstain=13`, `false_heal=59`, `unresolved=3`, `false_heal_rate_pct=78.7`. Delete the temporary file after confirming.

- [ ] **Step 5: Run the frontier model on the same 75 cases**

Use `gpt-4o` through `OPENAI_API_KEY`. If this exact model is unavailable in the account, stop this task and record the access failure in the revision notes rather than substituting an unrecorded model.

Run:

```bash
cd healreact/bench/scripts
OPENAI_API_KEY="$OPENAI_API_KEY" python3 false_heal_probe.py \
  --backend openai-compatible \
  --model gpt-4o \
  --prompt vanilla \
  --out ../cases/koenig/_false_heal_probe_gpt4o_vanilla.json

OPENAI_API_KEY="$OPENAI_API_KEY" python3 false_heal_probe.py \
  --backend openai-compatible \
  --model gpt-4o \
  --prompt abstain \
  --out ../cases/koenig/_false_heal_probe_gpt4o_abstain.json
```

Expected: each output has `n=75`, includes row-level verdicts, and records `backend=openai-compatible`, `model=gpt-4o`, and `temperature=0` behavior through the request payload.

- [ ] **Step 6: Compute paired comparison**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path
root = Path("healreact/bench/cases/koenig")
pairs = [
    ("qwen2.5-coder:7b", root / "_false_heal_probe_vanilla.json", root / "_false_heal_probe_abstain.json"),
    ("gpt-4o", root / "_false_heal_probe_gpt4o_vanilla.json", root / "_false_heal_probe_gpt4o_abstain.json"),
]
for label, vanilla_p, abstain_p in pairs:
    v = json.loads(vanilla_p.read_text())
    a = json.loads(abstain_p.read_text())
    print(label)
    print("  vanilla", v["abstain"], v["false_heal"], v["unresolved"], v["false_heal_rate_pct"])
    print("  abstain", a["abstain"], a["false_heal"], a["unresolved"], a["false_heal_rate_pct"])
    av = {r["id"]: r.get("verdict") for r in a["rows"]}
    vv = {r["id"]: r.get("verdict") for r in v["rows"]}
    labels = ["abstain", "false_heal", "unresolved"]
    print("  paired")
    for x in labels:
        print("   ", x, [sum(vv[i] == x and av[i] == y for i in vv) for y in labels])
PY
```

Expected: printed counts are copied into the paper. If `gpt-4o` reduces false healing, report that honestly; if it does not, the paper can make the stronger claim the reviewer asked for.

- [ ] **Step 7: Update artifact manifest**

Append to `healreact/bench/ARTIFACT_MANIFEST.md`:

```markdown
## Frontier F1 probe added for reviewer response

- Backend: OpenAI-compatible `/chat/completions`
- Model: `gpt-4o`
- Decoding: `temperature=0`, single sample
- Commands:
  - `python3 false_heal_probe.py --backend openai-compatible --model gpt-4o --prompt vanilla --out ../cases/koenig/_false_heal_probe_gpt4o_vanilla.json`
  - `python3 false_heal_probe.py --backend openai-compatible --model gpt-4o --prompt abstain --out ../cases/koenig/_false_heal_probe_gpt4o_abstain.json`
- Files:
  - `bench/cases/koenig/_false_heal_probe_gpt4o_vanilla.json`
  - `bench/cases/koenig/_false_heal_probe_gpt4o_abstain.json`
```

Then run:

```bash
shasum -a 256 healreact/bench/cases/koenig/_false_heal_probe_gpt4o_*.json
```

Expected: add the first 16 hex chars for each new JSON artifact to the checksum table.

## Task 3: Reframe Abstract and Introduction

**Files:**
- Modify: `paper-zh-journal-ids/main.tex`
- Modify: `paper-zh-journal-ids/sections/01_intro.tex`

- [ ] **Step 1: Rewrite the Chinese abstract**

Replace the current Chinese abstract with wording that puts diagnosis first:

```latex
\noindent\textbf{摘\ 要：}为降低 Playwright 测试中脆弱定位器维护成本，文章研究大语言模型（Large Language Model，LLM）驱动的测试自愈是否产生隐性误修复。以 ReproBreak 数据集 koenig 项目 75 个真实可达失效用例为对象，本文在选择器解析层面对 LLM 修复器进行对抗性诊断，并以 HealReact 的 L1/L3 静态基底作为可复现测量平台。结果表明，目标元素被移除时，\texttt{qwen2.5-coder:7b} 在 78.7\% 的用例中生成指向错误元素的可解析选择器，显式放弃提示未改变逐用例判定；静态基底覆盖 80.6\% 的真实失效目标，但该数字不等同于真实 Playwright 运行时通过率。研究认为，无人值守持续集成自愈需要行为重放验证器。
```

Expected: abstract no longer reads as if the paper contributes a complete L1-L4 system.

- [ ] **Step 2: Rewrite the English abstract in parallel**

Use parallel wording:

```latex
\noindent\textbf{Abstract：} To reduce the maintenance cost of brittle locators in Playwright tests, this paper studies whether large language model (LLM)-driven test self-healing causes silent false healing. Using 75 real reachable break cases from the koenig project in the ReproBreak dataset, we perform an adversarial selector-resolution-level diagnosis and use the L1/L3 static substrate of HealReact as a reproducible measurement platform. The results show that, when the target element is removed, \texttt{qwen2.5-coder:7b} produces resolver-valid selectors pointing to wrong elements in 78.7\% of cases, and an explicit abstention prompt does not change per-case decisions. The static substrate covers 80.6\% of real break targets, but this number is not a real Playwright runtime pass rate. The study concludes that unattended continuous integration self-healing requires a behavioral replay verifier.
```

Expected: English abstract matches the Chinese scope.

- [ ] **Step 3: Update the intro contribution list**

In `paper-zh-journal-ids/sections/01_intro.tex`, replace the contribution paragraph with:

```latex
\subsection{贡献}
（i）在真实 Playwright 数据集上对隐性误修复进行选择器层面的诊断性测量，并展示软提示放弃指令在逐用例层面无效（\S\ref{sec:findings}）；
（ii）使用 HealReact 的 L1/L3 静态基底作为可复现测量平台，而非声称已实现完整 L1--L4 自愈系统（\S\ref{sec:l1}）；
（iii）给出两个辅助性工程观察：低成本确定性杠杆可带来零回归的局部改进但统计未显著，跨应用可达率受锚点文化差异显著制约（\S\ref{sec:findings}）。
```

Expected: contribution (ii) explicitly preempts the reviewer’s “architecture/evaluation mismatch” criticism.

- [ ] **Step 4: If Task 2 completed, add the frontier-model result to F1 intro bullet**

Add one sentence after the existing Qwen F1 result:

Use the actual counts from Task 2 and add one complete sentence after the existing Qwen F1 result. The sentence must include the model id, Vanilla false-heal count/rate, Abstain false-heal count/rate, and whether the paired decisions changed. Do not add this sentence if the frontier run was not completed.

## Task 4: Add Frontier-Model Results to F1

**Files:**
- Modify: `paper-zh-journal-ids/sections/04_findings.tex`

- [ ] **Step 1: Update reproducibility configuration**

In `\subsection{复现配置}`, add:

```latex
为检验模型范围威胁，修订版还在同一 F1 协议上加入一个前沿闭源模型对照（\texttt{gpt-4o}，OpenAI-compatible \texttt{/chat/completions}，\texttt{temperature}=0，单次采样）；其逐用例输出与汇总同样归档为 JSON 工件。
```

Expected: model/backend details appear before the result table.

- [ ] **Step 2: Replace `tab:falseheal` with a model-by-prompt table**

Replace the current two-row table with a four-row table. Keep the two Qwen rows exactly as below and fill the two GPT-4o rows from the JSON summaries generated in Task 2 before committing the paper:

```latex
\begin{table}[t]
\centering
\caption{误修复探针（\S\ref{sec:f1}）。所有模型均使用相同的 75 个可达 koenig 用例与相同的 ground-truth 移除协议。}
\label{tab:falseheal}
\small
\resizebox{\columnwidth}{!}{%
\begin{tabular}{llrrrr}
\toprule
模型 & prompt & 放弃\,(好) & 误修复\,(坏) & 未解析 & \textbf{误修复\,\%} \\
\midrule
\texttt{qwen2.5-coder:7b} & \textsc{Vanilla} & 13 & 59 & 3 & \textbf{78.7\%} \\
\texttt{qwen2.5-coder:7b} & \textsc{+ 放弃守门规则} & 13 & 59 & 3 & \textbf{78.7\%} \\
\texttt{gpt-4o} & \textsc{Vanilla} & 使用 JSON 中的 abstain 计数 & 使用 JSON 中的 false\_heal 计数 & 使用 JSON 中的 unresolved 计数 & \textbf{使用 JSON 中的 false\_heal\_rate\_pct} \\
\texttt{gpt-4o} & \textsc{+ 放弃守门规则} & 使用 JSON 中的 abstain 计数 & 使用 JSON 中的 false\_heal 计数 & 使用 JSON 中的 unresolved 计数 & \textbf{使用 JSON 中的 false\_heal\_rate\_pct} \\
\bottomrule
\end{tabular}}
\\[2pt]
{\scriptsize $n=75$。Ground truth 目标已从候选集中移除；任何被给出的可解析选择器即为一次隐性误修复。}
\end{table}
```

Expected: the committed `.tex` contains numeric GPT-4o counts, not the Chinese instructions shown in this planning snippet.

- [ ] **Step 3: Add paired comparison text**

After the current Qwen paired table, add one compact paragraph with the actual GPT-4o paired comparison. If GPT-4o’s Abstain prompt leaves the false-heal rate high, interpret it as evidence that the soft-prompt guardrail weakness is not unique to the local 7B model. If GPT-4o substantially reduces false healing, narrow the paper’s strong “soft prompt ineffective” claim to Qwen and present GPT-4o as evidence that model capability can help but still needs an external replay oracle for auditability.

- [ ] **Step 4: Update F1 interpretation**

Ensure the interpretation says:

```latex
因此，本文的强结论不是“所有模型必然忽视放弃提示”，而是：在缺乏外部确定性验证器时，仅凭提示文本无法作为可审计的安全边界；即便前沿模型能降低风险，仍需行为重放或确定性拒绝机制来证明补丁没有错指。
```

Expected: conclusion remains valid regardless of whether GPT-4o improves over Qwen.

## Task 5: Compress F2 and Rebalance Findings

**Files:**
- Modify: `paper-zh-journal-ids/sections/04_findings.tex`
- Modify: `paper-zh-journal-ids/sections/05_discussion.tex`

- [ ] **Step 1: Shorten F2 setup**

Replace the detailed two-bullet variant description with a compact paragraph that retains only the necessary definitions:

```latex
F2 仅作为辅助工程经验报告。我们比较两杠杆均关的 v0 与两杠杆均开的 v1，并用二因子析因分离 testId 加权检索与强锚点后置过滤的边际贡献；所有臂均使用同一模型、同一候选池与同一解析器 oracle。
```

Expected: table `tab:l3-levers` and `tab:l3-factorial` remain, but prose is shorter.

- [ ] **Step 2: Move detailed post-filter trigger counts to table note or delete if space is tight**

Keep the core result:

```latex
两者全开相对两者均关为 +3/-0，McNemar 双侧精确检验 $p=0.25$。
```

Expected: F2 reads as “辅助性工程经验”，not a central contribution.

- [ ] **Step 3: Shorten discussion subsection on F2**

Replace `\subsection{为什么两个廉价确定性杠杆胜过提示工程}` with:

```latex
\subsection{确定性杠杆的有限含义}
F2 不构成统计显著的性能 claim。它的价值在于给出一条低成本、零回归的工程线索：当系统知道某类锚点更稳定时，把约束放进候选检索与输出后置过滤，比只要求模型“优先考虑稳定锚点”更可审计。本文据此把 F2 作为辅助性经验，而非主要科学贡献。
```

Expected: aligns with reviewer recommendation 3.

## Task 6: Strengthen Static Proxy and Runtime Caveats

**Files:**
- Modify: `paper-zh-journal-ids/main.tex`
- Modify: `paper-zh-journal-ids/sections/01_intro.tex`
- Modify: `paper-zh-journal-ids/sections/05_discussion.tex`
- Modify: `paper-zh-journal-ids/sections/07_conclusion.tex`

- [ ] **Step 1: Add “选择器层面” to abstract headline numbers**

Ensure both abstracts say:

```latex
本文在选择器解析层面对 LLM 修复器进行对抗性诊断。
```

and:

```latex
该结果不等同于真实 Playwright 运行时通过率。
```

Expected: readers cannot confuse 77.3% static exact match with E2E pass rate.

- [ ] **Step 2: Keep the footnote in intro, but make it shorter**

Current footnote is useful but long. Replace it with:

```latex
\footnote{本文所有“静态修复代理”均指选择器解析器层面的元素一致性，不是端到端 Playwright 通过率；二者可能因 visibility、timing 与运行时 DOM 差异而不一致。}
```

Expected: less page pressure while preserving the caveat.

- [ ] **Step 3: Move Docker pilot into a clearly labeled limitation**

In `sections/05_discussion.tex`, ensure the Docker paragraph starts with:

```latex
\textit{运行时 pilot 仅用于证明鸿沟存在，而非估计通过率。}
```

Expected: the 2/3 pilot is not overinterpreted.

- [ ] **Step 4: Update conclusion first sentence**

Use:

```latex
本文的全部头条数字均应首先理解为选择器解析层面的诊断结果，而非工业部署中的端到端通过率。
```

Expected: the conclusion mirrors reviewer recommendation 4.

## Task 7: Clarify HealReact Scope

**Files:**
- Modify: `paper-zh-journal-ids/sections/03_l1_substrate.tex`
- Modify: `paper-zh-journal-ids/sections/01_intro.tex`

- [ ] **Step 1: Rename section heading if needed**

Change:

```latex
\section{HealReact L1 静态基底}
```

to:

```latex
\section{用于诊断测量的 HealReact 静态基底}
```

Expected: section title emphasizes measurement infrastructure.

- [ ] **Step 2: Strengthen first paragraph scope statement**

Append:

```latex
因此，本文不把 HealReact 作为完整自愈系统加以评估；本文评估的是 L1/L3 在选择器层面支撑诊断测量的能力，以及 F1 探针揭示的 L4 必要性。
```

Expected: directly answers reviewer recommendation 2.

- [ ] **Step 3: Adjust figure caption**

Replace “HealReact 流水线” with:

```latex
HealReact 诊断测量平台与未来流水线关系。
```

Expected: figure no longer oversells implemented system completeness.

## Task 8: Update Limitations and Reviewer-Response Positioning

**Files:**
- Modify: `paper-zh-journal-ids/sections/05_discussion.tex`

- [ ] **Step 1: Update model-scope limitation**

If Task 2 completed with GPT-4o, replace:

```latex
\textit{模型范围。}本文全部 LLM 数字基于单一开源小型代码模型（\texttt{qwen2.5-coder:7b}）。
```

with:

```latex
\textit{模型范围。}主实验使用 \texttt{qwen2.5-coder:7b}，修订版补充了 \texttt{gpt-4o} 在相同 F1 协议上的对照。该对照用于检验“软提示是否因小模型指令遵循不足而失效”，但仍只覆盖一个前沿模型、一个数据集与一次贪心解码设置；因此本文不声称已穷尽模型规模、训练方式或供应商差异。
```

Expected: limitation becomes more credible after experiment.

- [ ] **Step 2: If Task 2 cannot be run, be explicit**

If no frontier API access is available, write:

```latex
\textit{模型范围。}本文全部 LLM 数字仍基于单一开源小型代码模型。审稿意见指出这限制了结论的普适性；在缺少前沿模型 API 复现实验前，本文只能把“软提示失效”限定为该模型与该协议上的发现，而不能断言 GPT-4o/Claude 级模型同样失效。
```

Expected: no unsupported claim remains.

- [ ] **Step 3: Keep F3 limitation honest**

Ensure F3 still says payload HEAD SHA and systematic miss taxonomy are limitations unless they are actually fixed.

Expected: do not overclaim cross-app generalization.

## Task 9: Compile, Audit, and Prepare Response Notes

**Files:**
- Build: `paper-zh-journal-ids/main.pdf`
- Read: `paper-zh-journal-ids/main.log`
- Optional Create: `paper-zh-journal-ids/REVIEW_RESPONSE_NOTES.md`

- [ ] **Step 1: Compile**

Run:

```bash
cd paper-zh-journal-ids
xelatex -interaction=nonstopmode main.tex
bibtex main
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```

Expected: PDF builds successfully.

- [ ] **Step 2: Check LaTeX warnings**

Run:

```bash
rg -n "Undefined references|Citation .* undefined|Label\\(s\\) may have changed|Overfull \\\\hbox|LaTeX Warning" paper-zh-journal-ids/main.log
```

Expected: no undefined refs/citations. If `Label(s) may have changed` appears, run `xelatex` once more. Any overfull hbox should be fixed if it affects visible layout.

- [ ] **Step 3: Verify no conditional placeholders remain**

Run:

```bash
rg -n "使用 JSON 中|若 .* 则|如果 Task|TODO|TBD|\\.\\.\\." paper-zh-journal-ids/sections paper-zh-journal-ids/main.tex
```

Expected: no matches except legitimate Chinese ellipses already present in quoted prose. Remove all planning placeholders from the paper.

- [ ] **Step 4: Create reviewer-response notes**

Create `paper-zh-journal-ids/REVIEW_RESPONSE_NOTES.md` with:

```markdown
# Review Response Notes

## R1: Model scope
- Added frontier-model F1 probe on the same 75 koenig reachable cases.
- New artifacts: `_false_heal_probe_gpt4o_vanilla.json`, `_false_heal_probe_gpt4o_abstain.json`.
- Paper locations: abstract, §1, §3/F1, §5 limitations.

## R2: HealReact architecture mismatch
- Reframed HealReact as L1/L3 diagnostic substrate.
- Explicitly marked L2/L4 as design placeholders and future work.
- Paper locations: abstract, §1 contributions, §2/§L1 figure caption.

## R3: F2 statistical significance
- Compressed F2 and retained McNemar non-significance.
- Paper locations: §3/F2, §5 deterministic lever discussion.

## R4: Static proxy vs E2E rate
- Added selector-resolution caveat to abstract and conclusion.
- Kept Docker pilot only as evidence of metric gap, not pass-rate estimate.
- Paper locations: abstract, §1 footnote, §5 limitations, §6 conclusion.
```

Expected: notes are factual and cite exact paper sections.

- [ ] **Step 5: Final git diff review**

Run:

```bash
git diff -- paper-zh-journal-ids healreact/bench docs/superpowers/plans/2026-06-27-review-revision-plan.md
```

Expected: only planned files changed. No edits under `paper-zh-journal/`.

## Self-Review Checklist

- [ ] The plan addresses all four reviewer recommendations.
- [ ] The highest-risk missing evidence is the frontier-model F1 probe; it is Task 2.
- [ ] The paper revision path is exclusively `paper-zh-journal-ids/`.
- [ ] F2 is downgraded to auxiliary engineering evidence.
- [ ] Static proxy and runtime pass-rate caveats appear in abstract, intro, discussion, and conclusion.
- [ ] No unsupported claim about GPT-4o/Claude remains if the frontier probe cannot be run.
