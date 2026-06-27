# Research Review Brief — paper-zh-journal

## 目标
判断这篇工程实证短论文当前是否达到《无线互联科技》（中文普通计算机工程期刊，面向实证类短论文）的可投稿水准，并给出 1–10 评分与 verdict（是 / 接近 / 否）。请**逐项核验引用的产物文件**后再下判断；executor 的说明不构成证据，只有文件本身算数。

## 待审文件（绝对路径，请实际读取）
- 主文件: /Users/DongbiaoGao/SourceCode/Thesis/paper-zh-journal/main.tex
- 章节: /Users/DongbiaoGao/SourceCode/Thesis/paper-zh-journal/sections/{01_intro,02_background,03_l1_substrate,04_findings,05_discussion,07_conclusion}.tex
- 参考文献: /Users/DongbiaoGao/SourceCode/Thesis/paper-zh-journal/references.bib
- 编译产物 PDF: /Users/DongbiaoGao/SourceCode/Thesis/paper-zh-journal/main.pdf
- 实验脚本: /Users/DongbiaoGao/SourceCode/Thesis/healreact/bench/scripts/{heal_baseline,test_heal_baseline,false_heal_probe,resolve_locators,resolver_sensitivity,docker_replay_minimal}.py
- Docker replay wrapper: /Users/DongbiaoGao/SourceCode/Thesis/healreact/bench/scripts/docker_replay_TODO.sh
- 实验工件(JSON): /Users/DongbiaoGao/SourceCode/Thesis/healreact/bench/cases/koenig/_{heal_baseline,false_heal_probe_vanilla,false_heal_probe_abstain,abl_w0_f0,abl_w1_f0,abl_w0_f1,abl_w1_f1,resolver_sensitivity,docker_replay_minimal}.json
- 工件清单: /Users/DongbiaoGao/SourceCode/Thesis/healreact/bench/ARTIFACT_MANIFEST.md

## 论文主题与核心 claim
在真实 Playwright 失效用例（ReproBreak 数据集 koenig 项目，93 个可复现失效）上，于**选择器解析层面**测量 LLM（qwen2.5-coder:7b）在缺乏行为验证 oracle 时的"隐性误修复"行为；并给出 HealReact 系统的 L1 静态基底与两个确定性改进杠杆。

核心数字：
- F1：对抗性构造下，78.7%（59/75）给出可解析但错误的选择器（选择器层面隐性误修复**上界**）；Vanilla 与 Abstain 软提示**逐用例完全一致**（配对交叉表非对角全 0）。
- F2：L1 静态可达 80.6%（75/93，permissive 假设）；L3 修复器 top-1 选择器精确匹配 77.3%（58/75）。
- F2 二因子析因：两个确定性杠杆各 +2、合计 +3、零回归，但 n=75 下 McNemar 精确检验**不显著**（p≥0.25）。
- F2 selector 有效性修复：上一轮 review 发现 id 750 曾把 JSX `{'signup-card-content'}` 直接拼成 JS 语法非法的 `page.getByTestId('{'signup-card-content'}')`，却被旧 oracle 计入 exact。现已在 `heal_baseline.py` 中加入可静态求值 testId 规范化、不可求值动态 testId 跳过、`selector_syntax_valid` 字段与回归测试；四个 F2 臂和默认 `_heal_baseline.json` 已重跑，`rg "page\\.getByTestId\\('\\{'" healreact/bench/cases/koenig` 无匹配，id 750 当前为合法 `page.locator('[data-testid="signup-card-content"]')` 且 `selector_syntax_valid=true`。
- Runtime pilot：对 3 个 v1 静态精确匹配用例（ids 615, 702, 703）做 ReproBreak Docker 运行时重放，fixed baseline 全部通过；替换 HealReact selector 后 2/3 通过、1/3 运行失败（id 702，等待 `getByTestId('color-picker-toggle')` 超时）。论文明确声明这只是小规模 pilot，不能估计全量 pass rate。
- F3：跨应用 payload 原始可达 3.8%，诊断为 BEM 模板字面量盲区（可证伪假设，非否证）。

## 本轮相对早期版本新增的实验证据（请据文件核验，不要轻信此处描述）
1. **F1 逐用例配对交叉表**（表 tab:falseheal-paired）：由 `_false_heal_probe_{vanilla,abstain}.json` join 得出，证明两提示变体逐用例一致而非仅聚合相同。
2. **F2 二因子析因 + McNemar**（表 tab:l3-factorial）：由 4 个臂 `_abl_w{0,1}_f{0,1}.json` 得出。**注意**：受控"两杠杆全关"基线是 55/75，早期稿曾用来历不明的 v0=53/75 报告过"+5 增益"，现已诚实下修为 +3 且声明统计不显著；并删除了不可靠的"墙钟节约"声明。
3. **解析器 strict/permissive 敏感性**（表 tab:resolver-sens）：由 `_resolver_sensitivity.json` 得出，可达率区间 [54.8%, 80.6%]，并披露多匹配 46/75、未解析 18→42。
4. **工件清单与 checksum**：`ARTIFACT_MANIFEST.md` 汇总脚本命令、模型 tag/digest、19 个 koenig commit、核心 JSON 的 sha256 前缀；同时诚实标注 payload HEAD SHA 未记录。
5. **3-case Docker runtime pilot**：`_docker_replay_minimal.json` 记录 ids 615/702/703 的 fixed/patched runtime 结果；其中 fixed baseline 均 pass，patched 2 pass / 1 fail / 0 infra fail。论文只把它作为 sanity check，不将 2/3 外推为全量通过率。
6. **上一轮 6.8/10 CRITICAL 已修复**：`test_heal_baseline.py` 覆盖 `{'signup-card-content'}` 规范化与旧非法嵌套引号拒绝；`python3 -m py_compile heal_baseline.py test_heal_baseline.py` 与 `python3 -m unittest test_heal_baseline.py` 通过。重跑后四臂仍为 55/57/57/58，`syntax_invalid_nonempty=0`，`+3/-0` 与零回归结论保持；论文 §F2 已把 v1 后置过滤触发次数从 2/75 更正为 1/75。

## 已知未落地项（请评估这些缺口是否构成对该期刊层次的阻断）
- 无公开仓库 URL（但已有本地冻结工件清单、checksum、koenig commit、模型 digest；投稿时仍需给公开归档 URL）。
- 无全量运行时 Docker 重放：仅有 3-case pilot，静态选择器精确匹配率与真实 Playwright 全量通过率之间的总体换算仍未建立。
- F3 payload 用 HEAD 快照、未逐 commit 对齐；307 未命中为非系统采样。

## 请给出
1. 总体评分（1–10，6=弱接收，7=接收）与 verdict（是/接近/否）。
2. 仍存在的 CRITICAL / MAJOR / MINOR 问题（按严重度），每条附可操作修复。
3. 与"早期 6/10"、上一轮 6.5/10、以及 F2 selector 有效性问题暴露时的 6.8/10 相比，本轮修复是否足以把稿件推到 7/10；若仍未到 7，明确指出**是否必须全量 58-case replay**，还是普通中文工程期刊层次下当前证据已足够投稿。
4. 一句话：以《无线互联科技》这类普通中文工程期刊短论文的标准，现在是否可以投。

请务必诚实、严苛。
