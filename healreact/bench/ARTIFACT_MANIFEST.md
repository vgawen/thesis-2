# HealReact 工件清单（paper-zh-journal 复现归档）

本清单汇总论文 §3/§F1/§F2/§F3/§5 所有数字所依赖的脚本、运行命令、输入数据标识与产物校验和，供审稿与复现使用。

## 模型
- 推理引擎：Ollama（本地，OpenAI 兼容 `/v1/chat/completions`）
- L3 修复器 / false-heal 探针：`qwen2.5-coder:7b`，Ollama digest `dae161e27b0e`
- L1 意图标注器（仅 32 元素 fixture 评估）：`qwen2.5:3b`
- 解码：`temperature=0`（贪心、单次采样）

## 数据集与 commit
- koenig（主基底）：`tryghost/koenig`，19 个失效 commit（短 SHA）：
  `0287844b 02d257a7 07bbb08e 0f131733 1a453f7c 3ba4b1aa 46b8d7c3 47847878 7efd028b 85d2db68 88a6de9d 93882b2c a3ab1eb6 be7221b0 c5a1dbf5 cabe34a7 ddee33cf ecee2a8e f2d79731`
  - per-commit LocatorSheet：`bench/cases/koenig/_src/_sheets/<short>.LocatorSheet.json`
  - per-commit resolve：`bench/cases/koenig/_src/_resolves/<short>.json`
- payload（跨应用）：`payloadcms/payload`，仅 `packages/ui/src`，单次 HEAD 快照。
  - **已知缺口**：当前冻结工件未记录该 HEAD 的精确 commit SHA（`bench/cases/payload/_summary.json` 仅含 repo / 配对数 / 记录数 / 可达率）。重新复现时应固定并记录 SHA。

## 脚本与运行命令（cwd=`bench/scripts`）
| 脚本 | 命令 | 对应结果 |
|---|---|---|
| `heal_baseline.py` | `python3 heal_baseline.py --out <cases/koenig>/_abl_w1_f1.json` | F2 v1（两杠杆开） |
| `heal_baseline.py` | `python3 heal_baseline.py --no-testid-weighting --no-post-filter --out .../_abl_w0_f0.json` | F2 v0（两杠杆关） |
| `heal_baseline.py` | `python3 heal_baseline.py --no-post-filter --out .../_abl_w1_f0.json` | F2 仅加权 |
| `heal_baseline.py` | `python3 heal_baseline.py --no-testid-weighting --out .../_abl_w0_f1.json` | F2 仅过滤 |
| `false_heal_probe.py` | `python3 false_heal_probe.py --prompt vanilla` | F1 Vanilla |
| `false_heal_probe.py` | `python3 false_heal_probe.py --prompt abstain` | F1 Abstain |
| `resolver_sensitivity.py` | `python3 resolver_sensitivity.py` | §5 strict/permissive 敏感性 |
| `cross_app_probe.py` | `python3 cross_app_probe.py` | F3 payload 跨应用 |
| `docker_replay_minimal.py` | `./docker_replay_TODO.sh --ids 615,702,703 --timeout-sec 180` | 3-case Docker 运行时重放 pilot |

F2 的 `heal_baseline.py` 产物包含 `selector_syntax_valid` 字段；后置过滤只会把可静态求值的 testId（例如 JSX `{'foo'}`）规范化为合法 `getByTestId('foo')`，不可求值的动态表达式不参与重写。

## 产物校验和（sha256 前 16 位）
| 文件（`bench/cases/koenig/`，payload 除外） | sha256[:16] |
|---|---|
| `_false_heal_probe_vanilla.json` | `0c9b8d10bd7f60f8` |
| `_false_heal_probe_abstain.json` | `b6dd7c965ebb4ced` |
| `_abl_w0_f0.json` | `7a6bae575b7310fe` |
| `_abl_w1_f0.json` | `7b94b3f7e1ec26e5` |
| `_abl_w0_f1.json` | `3b4f30abd1254b38` |
| `_abl_w1_f1.json` | `d80560405e501562` |
| `_resolver_sensitivity.json` | `3702b60d0808c206` |
| `_docker_replay_minimal.json` | `79658ce8a1050ff1` |
| `payload/_summary.json` | `94ddac814cbf4a53` |

> 重新生成校验和：`shasum -a 256 <file>`。
> 已知复现缺口（见正文 §5 与上文）：(1) payload HEAD SHA 未记录；(2) 仅有 3-case Docker 运行时重放 pilot，尚未完成 58 个 v1 静态精确匹配用例的全量重放，因此静态选择器精确匹配率与真实 Playwright 通过率的总体换算仍未建立。
