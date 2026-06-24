# Research Review 结果 — paper-zh-journal（工件清单 + 3-case runtime pilot 后）

- skill：`research-review`
- 后端：Codex MCP `project-0-Thesis-codex`，模型 `gpt-5.5`，`model_reasoning_effort=xhigh`
- 模式：单轮全新线程；评审声明已实际核验 `.tex`、`main.pdf`、`ARTIFACT_MANIFEST.md`、脚本和 JSON 工件，尤其是 `_docker_replay_minimal.json`
- 日期：2026-06-24
- 简报：`RESEARCH_REVIEW_REQUEST.md`
- trace：`.aris/traces/research-review/2026-06-24_run01/`

## 评分与结论
- **6.8/10**，verdict = **接近**。
- 新增的 `ARTIFACT_MANIFEST.md`、checksum、模型 digest、19 个 koenig commit 与 3-case Docker runtime pilot，把稿件从早期 6/10、上一轮 6.5/10 继续推近接收线。
- 但评审发现 F2 工件中存在一个真实阻断：`_abl_w1_f1.json` 的 id 750 生成了 JS 语法非法 selector，却仍被静态 oracle 计为 `exact_match=true`。因此当前“58/75、+3、零回归”的表述不能直接成立。

## 主要问题与修复建议
| 级别 | 问题 | 修复 |
|---|---|---|
| CRITICAL | F2 静态 oracle 把 id 750 的 `page.getByTestId('{'signup-card-content'}')` 计为 exact；Node 语法检查会报 `SyntaxError`。按“exact 且 JS 语法有效”重算，v1 应从 58/75 变成 57/75，且相对 v0 出现 id 750 回归。 | 修复 `heal_baseline.py` 的动态 `testId` 拼接/过滤逻辑；跳过 `{...}` / `{'...'}` 形式或先规范化；为所有输出增加 JS/Playwright 语法校验字段；重生成四个 `_abl_w*.json` 并更新 F2 表。 |
| MAJOR | 解析器边界仍偏宽：v1 的 58 个 exact 中有 15 个 selector 含 `.filter(...)`，当前静态解析器没有完整建模链式 Playwright 语义。 | 要么实现 `.filter({hasText})` 等链式语义，要么把这类 case 标为 ambiguous，并把威胁从讨论前移到 findings。 |
| MAJOR | 3-case runtime pilot 只能支持 sanity check，不能证明 57/58 个静态 exact 的运行时可迁移性。 | 普通中文工程期刊层次下不必强制全量 58-case replay；若要显著增强说服力，做 10–15 例分层抽样即可。 |
| MAJOR | F3 payload 仍是启发性诊断：HEAD SHA 未记录，307 未命中为非系统采样。 | 记录 payload HEAD SHA；对未命中做系统分类计数；否则 F3 明确降格为“跨应用失败案例分析”。 |
| MINOR | 无公开归档 URL。 | 投稿前提供仓库/Zenodo/OSF 归档 URL，并在补充材料给出完整 checksum。 |

## 对下一步的判断
- **不必须全量 58-case replay**：只要论文不声称端到端通过率，3-case pilot 对普通中文工程期刊短论文可作为 sanity check。
- **F2 selector 有效性已按评审意见修复**：`heal_baseline.py` 已规范化可静态求值的 JSX testId、跳过不可求值动态 testId，并写入 `selector_syntax_valid`；四个 F2 臂已重跑。
- 重跑后数字仍为 55/57/57/58，`+3/-0`、零回归结论保持；所有四臂 `syntax_invalid_nonempty=0`，id 750 不再产生非法 `getByTestId`。

## 一句话
按普通中文工程期刊短论文标准，**现稿接近可投，但不建议按当前工件直接投；修复 F2 selector 有效性并重生成表后，可以投稿**。

## 原始评审要点摘录
> 这篇稿件已经明显强于早期版本：F1、F2、resolver sensitivity、3-case Docker pilot 和 manifest/checksum 基本可核验，论文也较诚实地限定为“选择器解析层面/静态代理”。但我现在不能给到 7/10，因为 F2 工件里存在一个会影响“有效 Playwright 选择器 / 零回归”表述的真实瑕疵。
