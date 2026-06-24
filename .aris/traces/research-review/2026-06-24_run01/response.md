# research-review response

已按简报要求实际读取并核验了 `.tex`、`main.pdf`、`ARTIFACT_MANIFEST.md`、脚本和 JSON 工件；没有采信 executor 叙述本身。结论如下。

**1. 总体评分**

评分：**6.8 / 10**  
verdict：**接近**

这篇稿件已经明显强于早期版本：F1、F2、resolver sensitivity、3-case Docker pilot 和 manifest/checksum 基本可核验，论文也较诚实地限定为“选择器解析层面/静态代理”。但我现在不能给到 7/10，因为 F2 工件里存在一个会影响“有效 Playwright 选择器 / 零回归”表述的真实瑕疵。

**2. 问题与修复**

**CRITICAL：F2 的静态 oracle 把一个 JS 语法非法 selector 计为精确匹配。**  
我核验到 `_abl_w1_f1.json` 中 id 750 的 `proposed_selector` 是 `page.getByTestId('{'signup-card-content'}')`，Node 语法检查会报 `SyntaxError`，但它仍被计为 `exact_match=true`。原因来自 [heal_baseline.py](/Users/DongbiaoGao/SourceCode/Thesis/healreact/bench/scripts/heal_baseline.py:285) 的 post-filter 直接把动态 `testId` 字符串拼进 `getByTestId(...)`。按“exact 且 JS 语法有效”重算，v1 从 58/75 变为 57/75，且相对 v0 出现 id 750 回归，因此“+3、零回归”当前不能严格成立。  
修复：规范化动态 testId 值，或在 post-filter 前跳过 `{...}` / `{'...'}` 形式；为所有输出增加 JS/Playwright 语法校验字段，重生成四个 `_abl_w*.json` 并更新表 3/4。

**MAJOR：解析器边界仍偏宽。**  
论文已经披露 permissive/strict 区间，文件也支持 75/93 vs 51/93；但 v1 的 58 个 exact 中有 15 个 selector 含 `.filter(...)`，当前解析器主要抽取 `locator(...)` 第一参数，链式 Playwright 语义没有完整建模。这使“选择器精确匹配”仍更像自定义静态 oracle 结果。  
修复：要么实现 `.filter({hasText})` 等链式语义，要么把这类 case 标为 ambiguous，并把 [sections/05_discussion.tex](/Users/DongbiaoGao/SourceCode/Thesis/paper-zh-journal/sections/05_discussion.tex:19) 的威胁前移到 findings。

**MAJOR：3-case runtime pilot 只能支持 sanity check。**  
`_docker_replay_minimal.json` 确认 fixed baseline 3/3 pass、patched 2/3 pass、id 702 runtime fail、0 infra fail；论文在 [sections/05_discussion.tex](/Users/DongbiaoGao/SourceCode/Thesis/paper-zh-journal/sections/05_discussion.tex:16) 没有外推 pass rate，这是正确的。但它不能证明 57/58 个静态 exact 的运行时可迁移性。  
修复：保持“pilot”措辞即可投稿；若想显著增强说服力，做分层抽样 10–15 例即可，不必一上来全量 58 例。

**MAJOR：F3 payload 仍是启发性诊断，不是严格泛化实验。**  
`payload/_summary.json` 支持 12/319=3.8%，但 manifest 也承认 payload HEAD SHA 未记录，307 未命中是非系统采样。  
修复：记录 HEAD SHA；对未命中做系统分类计数，否则 F3 应明确降格为“跨应用失败案例分析”。

**MINOR：公开归档 URL 缺失。**  
本地 checksum 已匹配 manifest，但投稿材料没有公开仓库/Zenodo/OSF URL。普通中文工程期刊未必强制，但这篇文章的可信度高度依赖工件。  
修复：提交前给出可访问归档，并把 manifest 的 sha256 全量值放入补充材料。

**3. 与早期评分比较**

新增 manifest + checksum + 3-case runtime pilot 确实把稿件从早期 **6/10**、上一轮 **6.5/10** 推近到接收线；我给 **6.8/10**。差的不是全量 58-case replay，而是当前 F2 工件暴露出的静态 oracle/selector 有效性问题。

是否必须全量 58-case replay：**不必须**。按《无线互联科技》这类普通中文工程期刊短论文标准，只要论文不声称端到端通过率，3-case pilot 足够作为 sanity check；但必须先修正 id 750 这类语法非法 selector，并重算“有效选择器、精确匹配、零回归”。

**4. 一句话**

以《无线互联科技》这类普通中文工程期刊短论文标准，**现稿接近可投，但不建议按当前工件直接投；修复 F2 selector 有效性并重生成表后，可以投稿**。
