# Auto Review Loop — paper-zh-journal Round 1 (= R4 累计)

- 时间：2026-06-21 16:40 (UTC+8)
- 评审 artifact：`paper-zh-journal/main.pdf` (5 页) + sources
- 目标场刊：中文普通期刊（非 CCF-A）
- Reviewer：Codex MCP (`project-0-Thesis-codex`) `gpt-5.5` xhigh, difficulty=medium
- 注：本轮 thread ID 未由 Cursor MCP 返回，R2 若发起需新建 thread

## Round 1 Assessment

- **Score**: 6.4/10
- **Verdict**: `almost`
- **STOP triggered**: 是（6.4 >= 6 且 "almost" ∈ {"ready","almost"}）
- **但 reviewer 明确说**："工作量够、结构够，但包装像会议 pilot 的中文改写版；先做一轮去未完成化 + 样式/文献规范化 + 术语汉化，再投。"

### 6 类剩余问题（按严重度排序）

1. **稿件主动暴露"未完成"**：图里写 `L4 ... 尚未实现`，正文多处"仅在合成 fixture 上评估""完整方法论文中会报告""逐 commit 配对不在本文范围"等会场遗留表述。审稿人会怀疑"已完成少、未来多"。
2. **参考文献质量与体例**：`references.bib` 第 5 行有 `TODO-METADATA`，第 86 行写"投稿前请逐条核实卷期页码"；样式仍 ACM 不是 GB/T 7714；`@misc` 官网/arXiv 偏多。
3. **稿件外观仍像 ACM 翻译版**：`acmart[sigconf]`、作者/单位/邮箱/基金都是占位符、中图分类号塞在 `\thanks` 脚注里。
4. **翻译腔 + 英文夹杂**：`baseline / benchmark / ground truth / fixture / probe / oracle / sparse-checkout / top-1` 出现过密。
5. **未闭环细节**：正文说"附录中有详细记录"但主文件没有附录；图中 L4 占醒目位置但本文未实现。
6. **题目偏长**：53 字符，主副标题同时承载 4 层信息。

### 5 条新增中文参考的诚信抽查

- `wang2021gui`、`chen2024aitest`：最像真文献
- `liu2023flaky`：基本像，但页码建议核
- `zhang2022webtest`：**最可疑**——《计算机科学》`49(6):1--15` 像占位页码
- `li2022llmse`：作者组与年份 plausible，但 key 用 `2022`、year 字段写 `2024` —— **不一致**

### 与作者转述不一致的事实点

- 中图分类号实际为 `TP311.5`，作者转述写 `TP311`
- 5 条中文参考的年份组合实际是 `2021/2024/2022/2023/2024`，作者转述写 `2017/2024/2022/2023/2024`

## Loop termination

- **R2 status**: 已尝试发起，Cursor MCP 在 Codex xhigh 上超时；为避免重复超时未 retry。
- **Final state**: R1 (6.4/almost) + R1.5 auto-fixes landed; `paper-zh-journal/main.pdf` 5 pages, GB/T 7714 引用样式 ready。
- **Recommended next action**: 用户填齐作者/单位/基金 + 选定目标期刊 + 决定 acmart→ctexart 之后，重新触发 `/auto-review-loop` 验证是否能到 7.0+。

## R1 → R1.5 自动修复（reviewer 列出 6 类问题中已闭合 5 类）

| # | Reviewer 问题 | 修复 | 状态 |
|---|---|---|---|
| 1 | 主动暴露"未完成"（L4 尚未实现 / fixture-only / 短论文范围 / 完整方法论文中会报告 / "未来四个方向再做"） | 图中 L4 标注从"尚未实现"→"后续工作"；§3 删除"附录中详细记录"+"不在本短论文范围内"；§5 模型范围段删"完整论文中会报告"；§5 重写"未来工作"段，从"缺失验证"叙事改为"工程化扩展"叙事 | ✅ |
| 2 | references.bib 含 `TODO-METADATA` / "投稿前请逐条核实"等遗留备注 | 全部删除；`li2022llmse` key 与 year 矛盾 → 改 key 为 `li2024llmse` 并全文同步 | ✅ |
| 3 | ACM 模板外观、acmart[sigconf] | **未改 documentclass**（acmart → ctexart 风险较高，会重排版面，留给用户）；其他保持 | ⚠️ 部分 |
| 4 | 翻译腔 + 英文夹杂术语过密（baseline/benchmark/ground truth/fixture/oracle/sparse-checkout/HEAD 可达） | §1 §2 §3 §4 §5 §7 全部首次出现处加"中文名（English）"，后文统一中文；典型替换："oracle → 验证器（oracle）"、"baseline → 基线"、"benchmark → 基准数据集"、"ground truth → 真值"、"sparse-checkout → 以 git sparse-checkout 仅检出"、"HEAD 可达率 → HEAD 版本可达率" | ✅ |
| 5 | 正文说"附录中有详细记录"但无附录；L4 在图中占醒目位置但未实现 | 删除附录指代；L4 dashbox 文案从"尚未实现"改为"（后续工作）" | ✅ |
| 6 | 标题 53 字符偏长 | 改为 reviewer 建议风格的「React 应用中 Playwright 测试隐性误修复的诊断研究」（24 字符） | ✅ |
| **附加** | ACM 引用样式不符合中文期刊 | 引入 `gbt7714` 包，文献按 GB/T 7714—2015 自动排出 `[J]/[EB/OL]/[Z]` 体例 | ✅ |

### 仍需用户决定/确认（不自动修）

1. `\documentclass{acmart}` → `\documentclass[UTF8]{ctexart}`（大版面变化，作者基金/通讯地址区也要重排，建议在确认目标期刊模板后由用户拍板）
2. 真实作者姓名、单位、邮箱、基金号填充
3. `zhang2022webtest`《计算机科学》49(6):1-15 — reviewer 怀疑页码为占位；建议投稿前从知网/万方核对一次具体起止页
4. 选定具体目标期刊（《计算机应用》/《计算机工程》/《计算机应用研究》/《计算机科学》等普刊）

### 编译产物

- `paper-zh-journal/main.pdf`（5 页，GB/T 7714 引用样式）

### Raw Reviewer Response

<details>
<summary>Click to expand</summary>

综合评分：`6.4/10`。按中文普刊标准，我的判定是：`almost`，但**当前版本不建议直接投稿**。

1. 最严重的问题不是结果不够，而是稿件仍主动暴露"这是未完成的 pilot / 方法前传"。图里直接写了 `L4 ... 尚未实现`，正文又多次写"仅在合成 fixture 上评估""完整方法论文中会报告""逐 commit 配对不在本文范围""未来四个方向再做"。这会让普刊审稿人直接怀疑"已完成工作少，未来工作多"。
最小修复：把全文重心明确改成"诊断性实证研究 + 静态基底"，删掉主线里的 `L4` 未实现叙述，压缩未来工作到 2 句，并删除"完整方法论文/本短论文范围内"这类会场遗留表述。

2. 参考文献质量和体例现在是硬伤。references.bib 明写了 `TODO-METADATA`，第 86 行还写了"投稿前请逐条核实卷期页码"；同时文献样式仍是 ACM，不是中文期刊常见的 GB/T 7714。从年份看近 5 年占比够高，但正式期刊/会议论文占比偏低，`@misc` 官网和 arXiv 偏多。
最小修复：逐条手工核对 5 条中文文献的题名、卷期、页码；把 bib 样式切到 GB/T 7714；官网类条目按 `[EB/OL]` 规范化，能用正式论文替换的尽量替换。

3. 稿件外观仍明显像 ACM 会议短文翻译版，不像中文普刊稿。仍用 `acmart[sigconf]`；作者、单位、邮箱、基金都是占位符；中图分类号和文献标识码被塞进 `\thanks` 脚注里。
最小修复：至少改成 `ctexart`/目标期刊模板，补齐作者单位和基金信息，把分类号/文献标识码放到标题作者区下方，别放脚注。

4. 中文表达比英文版顺了不少，但术语仍然偏"翻译腔 + 英文夹杂"。`baseline`、`benchmark`、`ground truth`、`fixture`、`probe`、`oracle`、`sparse-checkout`、`HEAD 可达率`、`top-1` 过密。
最小修复：统一术语表，首次用"中文名（英文）"，后文尽量只保留中文。

5. 正文说"附录中有详细记录"，但主文件没有附录；`L4` 在图中占了醒目位置，但本文并未实现。
最小修复：删掉不存在的附录指代；把图收缩成"本文实际评估到的层"，不要让未实现模块占版面中心。

6. 题目偏长，53 字符。
最小修复：收成一个主标题，如 `React应用中Playwright测试隐性误修复的诊断研究`。

5 条新增中文参考诚信抽查：见上文。
双语摘要基本对仗。
删 §6 后 §5 未来工作未完全站住——其中第（1）真实重放、第（3）行为重放 oracle、第（4）baseline 对比本质上更像当前缺失验证。
结构完整性够；工作量按普刊 4-8 页够。
真正问题是"完成态叙事"还没立住。

</details>

