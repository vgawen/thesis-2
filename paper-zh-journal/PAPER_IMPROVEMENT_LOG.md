# Paper Improvement Log — paper-zh-journal

目标稿件：《无线互联科技》投稿版（中文工程实证短论文）
评审后端：Codex MCP `project-0-Thesis-codex`，模型 `gpt-5.5`，`model_reasoning_effort=xhigh`
评审独立性：`REVIEWER_BIAS_GUARD=true` —— 每轮均使用全新 codex 线程、零上下文、不透露任何"已修复/上一轮"信息。

## Score Progression

| Round | Score | Verdict | Key Changes |
|-------|-------|---------|-------------|
| Round 0（原始） | — | almost (上一 auto-review-loop 记录 6.4) | Baseline（main_round0_original.pdf） |
| Round 1 | 6/10 | 接近 | 收紧 silent-false-healing 框定为"选择器解析层面上界"；15% 降级为粗略上界估计；补复现配置段；F2 析因消融降级为后续工作；F3 降级为可证伪假设；引用/GB-T7714 修复（arXiv url + EB/OL urldate、去掉未引用的 mabl）；脚注编号"0" bug 修复；英文标题改 Title Case；中文引号统一 |
| Round 2 | 6/10 | 接近 | 补 Wilson 95% 置信区间 + 确定性逐用例一致说明；贡献(iii)改"叠加"措辞；增补解析器敏感性扫描为后续工作；加"代码与数据可用性"声明；URL 断行修复（xurl）；页眉清理（pagestyle plain）；图 1 灰度区分度增强 |

## 整体结论

两轮评分均为 6/10（弱接收边缘 / "接近"）。这是 writing-only 改进循环的典型形态：Round 1 解决了**框定过度、引用格式、版式**等可纯文本修复的问题；Round 2 在这些被修复后，**浮现出更深的实验严谨性诉求**（原始工件可审计链接/哈希、F1 配对统计、解析器 strict/permissive 敏感性、F2 二因子析因、F3 逐 commit 对齐）。后者需要**新实验/新数据**，超出"仅改写作质量"循环的范围，因此分数在 2 轮内未继续抬升属预期，而非修复无效。

## Round 1 Review & Fixes

<details>
<summary>GPT-5.5 xhigh Review (Round 1) — 6/10, 接近</summary>

总体评分 6/10（弱接收边缘）。

CRITICAL：核心 claim 过度表述——实验证明的是"LLM 在真值元素被移除后仍输出可解析但错误的选择器"，并非严格意义上"测试会静默通过"；`silent false healing` 暗含行为层 oracle。摘要/讨论/结论仍推到无人值守 CI 风险层面。建议改为"静态误修复风险 / selector-level false healing risk"，或补真实 Playwright replay。

MAJOR：(1) 15% 部署风险是启发式换算非测量结果，应降级为"粗略上界/敏感性估计"；(2) 实验复现信息不足（缺脚本、结果表、prompt 模板、top-k、模型 digest、commit SHA）；(3) F2 两个确定性杠杆未分离归因（缺 weighting-only / filter-only 消融）；(4) F3 跨应用结论偏弱（payload 用 HEAD 未逐 commit 对齐、307 未命中非系统采样）。

MINOR：推测性解释（"模型训练目标奖励自信输出"）应弱化；中文引号；英文标题大小写；中英文混排。

缺失参考文献/引用：mabl 未引用；"当代 LLM 定位器修复器…较高成功率"缺引用；arXiv/EB-OL 条目在 PDF 中只显示 [Z] 无 arXiv 号/URL，缺访问日期；开放脚本无仓库 URL。

版式：图 1 文字偏小、浅色灰度区分弱、浮到 §2 标题前；表 2 偏挤；**最大错误**：脚注编号显示为"0"（正文"静态修复代理0" + 脚注"0我们…"）。

结论：接近，建议大修后投稿。
</details>

### Round 1 Fixes Implemented
1. **CRITICAL** 摘要（中/英）、引言、讨论、结论统一收紧为"选择器解析层面隐性误修复上界"，并显式说明静态指标与运行时通过率的换算需真实重放；标题加"选择器层面"限定。
2. **MAJOR-1** 引言 §1 与讨论 §4 的 15% 全部降级为"粗略上界估计（非实测部署率）"。
3. **MAJOR-2** §3 findings 新增"复现配置"段：模型（qwen2.5-coder:7b / qwen2.5:3b via Ollama, temperature=0）、检索权重、top-k、逐用例工件字段、commit/HEAD 标识。
4. **MAJOR-3** §F2 解读明确"v0 vs v1 叠加对比、未拆分各自贡献"，二因子析因（含 McNemar）列为后续工作。
5. **MAJOR-4** §F3 解读补"307 未命中系统标注 + 逐 commit 对齐"为后续工作，强泛化论断降级为可证伪假设。
6. **MINOR** 推测性解释软化；全文 ASCII 直引号 → 中文引号；英文标题 Title Case。
7. **引用** references.bib：3 个 arXiv 条目补 url + urldate，8 个 EB/OL 条目补 urldate；去掉未引用的 mabl；"当代 LLM 修复器较高成功率"改保守表述。
8. **版式** 修复脚注编号"0" bug（`\addtocounter{footnote}{-1}` → `\setcounter{footnote}{0}`）。

## Round 2 Review & Fixes

<details>
<summary>GPT-5.5 xhigh Review (Round 2, 全新线程) — 6/10, 接近</summary>

总体评分 6/10（弱接收边缘）。主 claim 较克制、限定到位。

CRITICAL：核心实证证据不可由当前投稿包独立审计（无脚本/JSON 工件/仓库 URL/commit hash/checksum）。建议补 artifact URL、commit hash、模型 tag/digest、运行命令、结果文件名与 checksum，或"原始计数审计表"。

MAJOR：(1) F1"软提示无效"需配对证据（2×2 逐用例交叉计数 + 二项置信区间），而非仅聚合相同；(2) 解析器是所有数字的 oracle 但敏感性分析不足（应给 strict/permissive 两套结果、多匹配/未解析计数）；(3) F3 跨应用更像启发性案例（payload HEAD 非对应 commit、307 非系统采样）；(4) 两个确定性杠杆贡献未拆分，摘要/贡献处易被误读为各自独立验证。

MINOR：硬件描述补 OS/Ollama 版本/量化格式；"补充诚实性审计"未随包提供建议删/改；英文摘要偏长；术语首次出现给中文定义。

引用：所有 \cite 都能匹配且无未引用条目；三个核心 arXiv 预印本在线抽查存在；建议补 Playwright/可访问性树引用；GB/T 7714 的 URL 在 PDF 中断行为"https: //"，观感差。

版式：7 页双栏；图 1 浅色灰度区分弱；表 1 浮动打断 Abstain 枚举；页眉"1 背景与相关工作 2"可能不合模板；URL 断行需处理。

结论：接近，投稿前需补强（尤其可审计工件 + F1 配对 + 版式）。
</details>

### Round 2 Fixes Implemented
1. **CRITICAL（部分）** §3 findings 增"代码与数据可用性"声明：脚本与 JSON/CSV 工件作为补充材料、冻结于发表版本（含运行命令、模型 tag/digest、commit 标识）、可向作者索取；表 1–3 原始计数可由工件直接复算。*（公开仓库 URL/checksum 需作者在投稿时补实，无法在写作循环内凭空生成。）*
2. **MAJOR-1（已落地）** 表 1 注补 78.7%(59/75) 的 Wilson 95% CI ≈ [68.1%, 86.4%]；并新增表 `tab:falseheal-paired`——Vanilla×Abstain **逐用例 3×3 配对交叉表**（由 `_false_heal_probe_{vanilla,abstain}.json` join 得出，非对角全 0，13/59/3 全在对角线，证明逐例一致而非仅聚合相同）。
3. **MAJOR-2（部分）** §5 有效性威胁补：解析器是事实 oracle，未单独报告 strict/permissive 敏感性与多匹配/未解析细分，列为后续工作。
4. **MAJOR-4** 贡献(iii)改为"两杠杆叠加形成帕累托改进；各自边际贡献未做析因分离"。
5. **MINOR** "补充诚实性审计" → "解析器假设审计"。
6. **版式** 加 `\usepackage{xurl}` 修复 URL 断行；`\pagestyle{plain}` 清理页眉；图 1 填充加深（blue!12 / orange!20 / green!20 / gray!18）提升灰度区分度。

### Round 2 未落地项（需新实验/数据，超出写作循环范围）
- 公开仓库 URL + commit hash + checksum（CRITICAL，待作者投稿时补）
- ~~F1 逐用例配对交叉表~~ ✅ 已补（表 `tab:falseheal-paired`，见后记 2.1）
- ~~解析器 strict/permissive 双假设敏感性扫描~~ ✅ 已补（表 `tab:resolver-sens`，见后记 2.3）；真实 DOM 快照交叉校验仍为后续工作
- ~~F2 二因子析因消融（仅加权 / 仅过滤）+ McNemar 配对检验~~ ✅ 已补（表 `tab:l3-factorial`，见后记 2.2）
- F3 payload 逐 commit 对齐 + 307 未命中全量失因分类

## 后记：Step 2.1 落地（F1 配对交叉表）
两次探针的逐用例结果本就已存在于 `healreact/bench/cases/koenig/_false_heal_probe_vanilla.json` 与 `_false_heal_probe_abstain.json`（各 75 行，含 id + verdict），无需重跑 Ollama。按 id join 后得到 3×3 配对交叉表：对角线 = (放弃 13, 误修复 59, 未解析 3)，全部 6 个非对角元素 = 0，off-diagonal 总数 0 → 两变体逐例完全一致。该表已加入 §F1（`tab:falseheal-paired`），把原先依赖"determinism 论证"的逐例一致说法升级为实测证据。重编译通过：7 页、无 overfull、无未解析引用。

## 后记：Step 2.2 落地（F2 二因子析因 + McNemar）—— 含一处诚实性修正
**做法**：给 `healreact/bench/scripts/heal_baseline.py` 增加两个开关 `--no-testid-weighting` / `--no-post-filter`（默认开，向后兼容），用同一 harness（qwen2.5-coder:7b, temperature=0, 同系统提示）跑满 2×2 共 4 个臂，写入 `_abl_w{0,1}_f{0,1}.json`。

**受控析因结果（top-1 精确匹配，n=75）**：
| | 过滤关 | 过滤开 |
|---|---|---|
| 加权关 | 55 | 57 |
| 加权开 | 57 | **58** |

McNemar 精确检验：单开任一杠杆 +2/−0 (p=0.50)，两者全开 +3/−0 (p=0.25)；方向一致、零回归，但 n=75 下均未达显著。

**诚实性修正（重要）**：受控"两杠杆均关"基线 = **55/75**，而论文原用的 `v0=53/75` 出自来历不明的更早检索配置。据此修正：
1. F2 表 `tab:l3-levers` 的 v0 由 53→**55**（70.7%→73.3%；静态代理 57.0%→59.1%）；v1 仍为 58（77.3%/62.4% 不变）。
2. "5 增 0 减" → **3 增 0 减**（受控析因下的真实增益），同步改 §1 引言、贡献(iii)、§5 讨论。
3. **删除**原"约 22% 墙钟节约"声明——重跑显示 v1 反而更慢（81.6s→110.8s），墙钟在本机非受控、不可靠，不作为指标。
4. 新增析因表 `tab:l3-factorial`，把原"未分离归因 future work"改写为已分离 + McNemar n.s. 的诚实结论。

**脚本改动**：`retrieve_candidates` 增 `testid_weight` 参数（默认 3，向后兼容 false_heal_probe 的导入）；post-filter 块用 `args.post_filter` 包裹。

重编译通过：**8 页**（新增析因表 +1 页）、无重复 label、0 overfull、无未解析引用。快照 `main_step2.2_factorial.pdf`。

## 后记：Step 2.3 落地（解析器 strict/permissive 敏感性扫描）
**做法**：给 `resolve_locators.py` 的 `record_matches_constraint/matches_chain/find_matches` 加 `strict` 参数（默认 False = 现有 permissive，向后兼容 heal_baseline / false_heal_probe 的导入）。strict 关闭两处过近似：(1) 动态属性值 `{expr}` 不再视为可能匹配；(2) 非 tag 祖先约束不再用同文件近似。新增纯离线脚本 `resolver_sensitivity.py`，基于已存在的 per-commit sheet + case metadata 重算两套（无需 re-clone/extractor/LLM）。

**结果（koenig，n=93）**：
| 指标 | permissive（本文） | strict（下界） |
|---|---|---|
| new_locator 可达 | 75/93 (80.6%) | 51/93 (54.8%) |
| 多匹配 (≥2 命中) | 46 | 0 |
| 未解析 (0 命中) | 18 | 42 |

- permissive 复算 = **80.6%**，与论文头条完全一致（自洽验证）。
- 真实 L1 静态可达率区间 = **[54.8%, 80.6%]**，80.6% 为上界。
- 24 个用例在 strict 下从可达翻转为不可达；46/75 permissive 可达用例为多匹配（首个命中消歧）。

**写进论文**：§5 有效性威胁新增表 `tab:resolver-sens` + 区间表述，删除原"留作后续工作"措辞（真实 DOM 快照交叉校验仍为后续工作）。修复表格 8.7pt overfull（加 `\resizebox`）。

重编译通过：8 页、0 overfull、无重复 label、无未解析引用。快照 `main_step2.3_resolver.pdf`。

## Step 8 格式检查（最终）
- 页数：7 页（双栏，《无线互联科技》篇幅内）✓
- 重复 label：无 ✓
- Overfull hbox：无（仅剩 underfull 警告，可接受）✓
- 引用解析：16 条全部解析、参考文献完整 ✓
- 脚注编号"0" bug：已修复 ✓
- URL 断行"https: //"：已修复 ✓

## PDFs
- `main_round0_original.pdf` — 原始稿
- `main_round1.pdf` — Round 1 修复后
- `main_round2.pdf` — Round 2 修复后（= main.pdf 当前版本）
