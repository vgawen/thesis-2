# research-review response

**1. 总体评分**

评分：**7.0 / 10**  
verdict：**是**，但属于**刚过线的可投稿 / 普通中文工程期刊接收线**，不是稳健强接收。

我实际核验后，核心数字与产物一致：F1 为 13 放弃、59 误修复、3 未解析，且 Vanilla/Abstain 逐例纯对角一致；F2 四臂为 55/57/57/58，+3/-0 无回归；`_resolver_sensitivity.json` 支持 75/93 vs 51/93；`_docker_replay_minimal.json` 支持 3 例 fixed 全过、patched 2 过 1 失败。manifest 中列出的 sha256 前 16 位也与实际文件匹配。`main.pdf` 可抽取文本，8 页，核心表述与 LaTeX 源一致。

`heal_baseline.py` 中的 JSX testId 规范化、selector 语法 guard 和后置过滤确实存在。`test_heal_baseline.py` 覆盖了旧的非法嵌套引号问题。`unittest` 在脚本目录下通过 3 个测试；原样 `py_compile` 因当前沙箱不允许写 `.pyc` 且提权被拒，未能复验，但只读 `compile()` 语法检查通过。

**2. 仍存在的问题**

CRITICAL：**无当前阻断项**。上一轮 F2 selector 有效性问题已经实质修复，id 750 当前在 `_heal_baseline.json` 与四个 ablation JSON 中均为合法 selector，`selector_syntax_valid=true`，且 `rg "page\\.getByTestId\\('\\{'" healreact/bench/cases/koenig` 无匹配。

MAJOR：**运行时证据仍太薄**。论文已诚实声明 77.3% / 62.4% 是静态代理，且 3-case Docker pilot 中 patched 只有 2/3 通过，id 702 失败。修复：至少补 58 个 v1 exact 用例全量 replay；若时间不够，补分层抽样 replay 并报告置信区间、infra fail、runtime fail 分类。

MAJOR：**解析器仍是宽松 oracle**。permissive 模式把动态属性值和复合 CSS 祖先条件过近似。这导致 80.6% 实际是上界，strict 下只有 54.8%，且 permissive 有 46/75 多匹配。修复：对多匹配样本做人工/DOM 快照复核，或把主文头条改成区间而非单点。

MAJOR：**F3 只能算泛化诊断假设**。`cross_app_probe.py` 明确是 payload HEAD 代理，不做逐 commit 配对，且 `_summary.json` 没有 HEAD SHA。修复：记录 payload commit，做 ReproBreak 配对对齐，并对 307 个 miss 做系统分类。

MAJOR：**公开复现材料尚未闭环**。本地 manifest 很好，但无公开仓库 / Zenodo / OSF URL。修复：投稿前给出冻结归档 URL，manifest 保留 checksum 与模型 digest。

MINOR：F2 “帕累托改进”措辞略强。+3/-0 是样本内零回归，但 McNemar p=0.25，不应让读者误解为统计确认。修复：结论里改成“样本内零回归的局部工程改进”。

MINOR：PDF 中部分英文 small caps 抽文本显示为 `V anilla`，可能不影响视觉，但投稿前应人工检查版式。

**3. 与早期评分比较及是否需要 58-case replay**

相较早期 **6/10**、上一轮 **6.5/10**、以及 selector 有效性问题暴露时的 **6.8/10**，本轮修复**足以推到 7.0/10**。关键原因不是 F2 +3 本身，而是：非法 selector bug 已修复；逐例配对表、二因子析因、resolver sensitivity、manifest checksum、runtime pilot 都把证据链补齐；更重要的是论文把强 claim 明确降格为“静态诊断指标 / 上界 / pilot / 假设”，没有继续偷换成端到端修复率。

**是否必须全量 58-case replay？**  
对《无线互联科技》这类普通中文工程期刊短论文，**不是达到 7/10 的必要条件**，当前证据已足够投稿为“静态选择器层面的工程实证诊断”。但若想把评分推到 7.5+，或把论文主张从“静态诊断”升级到“实际自愈有效”，则 58-case replay 基本是必须的。

**4. 一句话**

以《无线互联科技》这类普通中文工程期刊短论文标准：**现在可以投，但必须保持“静态诊断短论文”的定位，并在投稿材料中补公开归档 URL，不能宣称端到端自愈成功率。**
