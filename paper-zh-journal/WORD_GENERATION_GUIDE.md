# Word 文件生成经验指南

本文档记录本论文从 LaTeX/PDF 生成可提交 Word 文件时踩过的坑和较稳妥的工作流，供后续需要再次生成或修订 Word 文件时复用。

## 结论先行

最稳妥的方式不是直接从 LaTeX 重新生成完整 Word，而是：

1. 以 LaTeX 源文件作为权威内容来源。
2. 以已有的高质量可编辑 Word 文件作为版式底稿。
3. 用 OOXML 脚本对 Word 做小范围、可控的文本和样式修补。
4. 用 LibreOffice 渲染为 PDF/PNG 后做视觉检查。

一句话概括：

> LaTeX 负责权威内容，已有 Word 负责稳定版式，OOXML 脚本负责定点同步修改，LibreOffice 渲染负责最终验收。

## 为什么不建议直接 Pandoc 一步生成

可以使用 Pandoc 作为辅助工具，但不建议把 `pandoc main.tex -o xxx.docx` 作为最终交付方式。对于本文这种 LaTeX 结构，直接转换容易出现以下问题：

- `\twocolumn[...]` 中的标题、摘要、关键词等前置内容可能被忽略或丢失。
- 图、表、题注和交叉引用可能退化，甚至只剩标签文本。
- `\rev{...}` 这类红色修订宏可能不会稳定转换成 Word 里的红色文字。
- 数学表达、`top-k` 之类的片段、节引用和表引用可能转换不完整。
- 参考文献标题可能丢失，参考文献条目样式也可能变形。

因此，Pandoc 生成的 Word 适合作为临时参考，不适合作为最终提交版。

## 推荐文件角色

- `main.tex` 和 `sections/*.tex`：论文正文的权威源文件。
- `main.pdf`：LaTeX 编译出的权威 PDF 版，用于核对内容和排版。
- `main_red_revision_editable.docx`：可编辑 Word 底稿，适合作为后续 Word 生成的起点。
- `main_red_revision_latest.docx`：最新交付 Word 文件。
- `WORD_GENERATION_GUIDE.md`：本文档。

如果后续需要重新生成 Word，优先从最新质量可靠的可编辑 Word 底稿复制一份，再做定点修补。

## 推荐流程

### 1. 先在 LaTeX 中完成内容修改

正文、摘要、结论、参考文献等内容应优先在 LaTeX 源文件中修改，并正常编译 PDF。

示例：

```bash
xelatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
xelatex -interaction=nonstopmode -halt-on-error main.tex
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

这样可以保证 PDF 版和论文源文件仍然是可信的主版本。

### 2. 选择 Word 底稿

优先使用已有的可编辑 Word 文件作为底稿，例如：

```text
main_red_revision_editable.docx
```

不要轻易用新 Pandoc 输出覆盖这个底稿。它通常已经保留了：

- 摘要和关键词；
- 参考文献；
- 原有红色修订；
- 基本段落样式；
- 表格和标题的大致结构。

### 3. 复制出最新交付文件

建议先复制一份，所有后续修改都作用在交付文件上：

```bash
cp main_red_revision_editable.docx main_red_revision_latest.docx
```

如需保留回滚点，可以额外复制备份：

```bash
cp main_red_revision_latest.docx main_red_revision_latest.before_patch.docx
```

### 4. 用 OOXML 做定点修补

Word 文件本质上是一个 zip 包，核心正文在：

```text
word/document.xml
```

样式定义在：

```text
word/styles.xml
```

建议用 Python 脚本完成以下操作：

- 删除不应保留的句子；
- 替换本轮润色后的词句；
- 给新增或调整内容套用红色字符样式；
- 补充缺失标题，例如“参考文献”；
- 确保红色样式在 `styles.xml` 中真实存在。

不要手动大段重写 Word XML。优先做小范围替换，尽量保留原有段落结构。

## 红色修订处理

如果编辑要求保留红色修订标记，Word 中应使用真正的字符样式，而不是只依赖 LaTeX 宏或 Pandoc 的临时属性。

推荐样式名：

```text
RedText
```

需要确认 `word/styles.xml` 中该样式包含红色定义：

```xml
<w:color w:val="FF0000" />
```

在 `word/document.xml` 中，新增或调整的红色文字可以使用：

```xml
<w:rPr>
  <w:rStyle w:val="RedText" />
</w:rPr>
```

生成后可以检查红色样式是否存在：

```bash
python3 - <<'PY'
from pathlib import Path
import zipfile

p = Path("main_red_revision_latest.docx")
with zipfile.ZipFile(p) as z:
    doc = z.read("word/document.xml").decode("utf-8", errors="ignore")
    styles = z.read("word/styles.xml").decode("utf-8", errors="ignore")

print("RedText refs:", doc.count("RedText"))
print("RedText style exists:", "RedText" in styles)
print("RedText style has FF0000:", "FF0000" in styles)
PY
```

## 内容检查

生成 Word 后，先做文本级检查，确认关键内容没有丢失。

示例：

```bash
textutil -convert txt -stdout main_red_revision_latest.docx | rg -n "摘要|关键词|参考文献|^\\[1\\]"
```

建议重点检查：

- 摘要是否存在；
- 关键词是否存在；
- 删除句是否确实删除；
- 本轮替换词是否生效；
- “参考文献”标题是否存在；
- 第一条参考文献是否跟在标题后；
- 红色修订文字是否仍在。

例如本轮曾发现的问题是：

- Pandoc 生成的 Word 丢失了摘要块；
- 参考文献标题丢失；
- 红色修订样式需要额外确认。

## 渲染检查

文本存在不等于 Word 排版正常。最终交付前必须做渲染检查。

推荐流程：

```bash
rm -rf /tmp/main_red_revision_latest_render
mkdir -p /tmp/main_red_revision_latest_render/pdf /tmp/main_red_revision_latest_render/png

soffice --headless \
  --convert-to pdf \
  --outdir /tmp/main_red_revision_latest_render/pdf \
  main_red_revision_latest.docx

pdfinfo /tmp/main_red_revision_latest_render/pdf/main_red_revision_latest.pdf

pdftoppm -png -r 150 \
  /tmp/main_red_revision_latest_render/pdf/main_red_revision_latest.pdf \
  /tmp/main_red_revision_latest_render/png/page
```

然后抽查 PNG 页面：

- 首页：标题、作者、摘要、关键词、红色修订是否正常；
- 正文中段：章节标题、表格、红色修订是否正常；
- 结尾页：结论、参考文献标题、参考文献条目是否完整。

如果有文档技能里的 `render_docx.py` 可用，也可以优先使用它；如果因为环境依赖失败，可以用上面的 LibreOffice + `pdftoppm` 方案兜底。

## 常见问题和处理

### 摘要丢失

常见原因是 LaTeX 的前置结构无法被 Pandoc 正确理解，例如 `\twocolumn[...]`。

处理方式：

- 不使用 Pandoc 输出作为最终版；
- 回到已有 Word 底稿；
- 只把最新修改定点同步进去。

### 红色修订没有显示

常见原因是 Pandoc 只生成了类似 `style="color: red"` 的中间属性，但 Word Writer 没有真正应用颜色样式。

处理方式：

- 在 `styles.xml` 中定义 `RedText`；
- 在正文 run 上引用 `RedText`；
- 渲染成 PNG 后确认红色可见。

### 参考文献标题丢失

处理方式：

- 在第一条参考文献 `[1]` 前插入一个独立段落；
- 段落文本为“参考文献”；
- 样式可复用 `Heading1` 或当前文档中对应标题样式；
- 插入后重新渲染检查最后两页。

### 交叉引用显示为空或变成标签

常见于 LaTeX 到 Word 的自动转换。处理方式：

- 最终 Word 尽量基于已有底稿修补；
- 避免全量重转；
- 必要时手动核对 PDF，将关键引用替换成稳定文本。

### 图表丢失或表格变形

处理方式：

- 优先保留 Word 底稿中的图表和表格结构；
- 不用 Pandoc 全量覆盖；
- 若必须重建表格，修改后必须渲染检查。

## 最终交付前清单

交付 `main_red_revision_latest.docx` 前，至少确认：

- [ ] 摘要存在。
- [ ] 关键词存在。
- [ ] 不需要保留的编辑说明句已删除。
- [ ] 本轮新增或调整内容已用红色标记。
- [ ] 原有红色修订没有被清除。
- [ ] “参考文献”标题存在。
- [ ] 参考文献条目完整。
- [ ] Word 可被 LibreOffice 正常转成 PDF。
- [ ] 首页渲染正常。
- [ ] 正文中段渲染正常。
- [ ] 结尾和参考文献页渲染正常。

## 推荐心法

生成 Word 不是单纯的格式转换，而是一次小型交付。最容易出错的地方不是脚本报错，而是静默丢内容、静默丢样式、静默丢标题。

所以后续应坚持：

- 不迷信一键转换；
- 不覆盖可靠底稿；
- 修改尽量局部；
- 红色修订要落到 Word 样式；
- 最终一定渲染看图。
