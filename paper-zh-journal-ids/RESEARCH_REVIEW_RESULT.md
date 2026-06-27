# Research Review 结果 — paper-zh-journal（F2 selector 有效性修复后）

- skill：`research-review`
- 后端：Codex MCP `project-0-Thesis-codex`，模型 `gpt-5.5`，`model_reasoning_effort=xhigh`
- 模式：单轮全新线程；评审声明已实际核验 `.tex`、`main.pdf`、`ARTIFACT_MANIFEST.md`、脚本和 JSON 工件，尤其是 `heal_baseline.py`、`test_heal_baseline.py`、四个 `_abl_w*.json`、`_heal_baseline.json` 与 `_docker_replay_minimal.json`
- 日期：2026-06-24
- 简报：`RESEARCH_REVIEW_REQUEST.md`
- trace：`.aris/traces/research-review/2026-06-24_run02/`

## 评分与结论
- **7.0/10**，verdict = **是**，但属于**刚过线的可投稿 / 普通中文工程期刊接收线**，不是稳健强接收。
- 评审核验确认：F1 为 13 放弃 / 59 误修复 / 3 未解析且 Vanilla/Abstain 逐例纯对角一致；F2 四臂为 55/57/57/58，`+3/-0` 无回归；resolver sensitivity 为 75/93 vs 51/93；3-case Docker pilot 为 fixed 3/3、patched 2/3；manifest 的 sha256 前 16 位与实际文件匹配。
- 上一轮 F2 selector 有效性 CRITICAL 已实质修复：id 750 当前在 `_heal_baseline.json` 与四个 ablation JSON 中均为合法 selector，`selector_syntax_valid=true`，且非法 `page.getByTestId('{...')` 模式在 koenig 工件中无匹配。

## 主要问题与修复建议
| 级别 | 问题 | 修复 |
|---|---|---|
| CRITICAL | 无当前阻断项。上一轮 F2 selector 有效性问题已修复。 | 维持当前工件与正文的诚实边界，不要把静态代理改写为端到端修复率。 |
| MAJOR | 运行时证据仍薄：3-case pilot 只能支持 sanity check，patched 2/3 通过、id 702 失败。 | 若想把评分推到 7.5+，做 58 个 v1 exact 全量 replay；时间不足则做分层抽样 replay，并报告置信区间、infra fail、runtime fail 分类。 |
| MAJOR | 解析器仍是宽松 oracle：permissive 是上界，strict 下只有 54.8%，且 permissive 有 46/75 多匹配。 | 对多匹配样本做人工/DOM 快照复核，或把主文头条进一步改成区间而非单点。 |
| MAJOR | F3 payload 仍是泛化诊断假设：HEAD SHA 未记录，未逐 commit 配对，307 miss 未系统分类。 | 记录 payload commit，做 ReproBreak 配对对齐，并对 307 个 miss 做系统分类。 |
| MINOR | 无公开归档 URL。 | 投稿前提供仓库/Zenodo/OSF 归档 URL，并在补充材料给出完整 checksum。 |
| MINOR | F2 “帕累托改进”措辞略强。 | 改成“样本内零回归的局部工程改进”。 |

## 对下一步的判断
- **不必须全量 58-case replay**：只要论文不声称端到端通过率，3-case pilot 对普通中文工程期刊短论文可作为 sanity check。
- **F2 selector 有效性已按评审意见修复**：`heal_baseline.py` 已规范化可静态求值的 JSX testId、跳过不可求值动态 testId，并写入 `selector_syntax_valid`；四个 F2 臂已重跑。
- 重跑后数字仍为 55/57/57/58，`+3/-0`、零回归结论保持；所有四臂 `syntax_invalid_nonempty=0`，id 750 不再产生非法 `getByTestId`。
- **当前可投**：按《无线互联科技》普通中文工程期刊短论文标准，本轮修复足以推到 7.0/10。必须保持“静态诊断短论文”定位，并在投稿材料中补公开归档 URL。

## 一句话
以《无线互联科技》这类普通中文工程期刊短论文标准：**现在可以投，但必须保持“静态诊断短论文”的定位，并在投稿材料中补公开归档 URL，不能宣称端到端自愈成功率。**

## 原始评审要点摘录
> 相较早期 6/10、上一轮 6.5/10、以及 selector 有效性问题暴露时的 6.8/10，本轮修复足以推到 7.0/10。关键原因不是 F2 +3 本身，而是：非法 selector bug 已修复；逐例配对表、二因子析因、resolver sensitivity、manifest checksum、runtime pilot 都把证据链补齐；更重要的是论文把强 claim 明确降格为“静态诊断指标 / 上界 / pilot / 假设”，没有继续偷换成端到端修复率。
