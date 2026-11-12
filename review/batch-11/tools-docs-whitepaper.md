---
title: 白皮书 PDF 构建
module: tools
platforms: [windows]
sources: 2
date: 2026-11-11
---

## 概述

- `tools/docs/build_whitepaper.py` 构建中文论文版 PDF 与本地目视 QA 产物。`tools/docs/build_whitepaper.py:1`
- README 声明可编辑原稿是 `docs/whitepaper/Operit2论文版.md`。`tools/docs/README.md:9`
- 原稿路径未在基线核实到：基线内不存在 `docs/whitepaper/` 目录，也不存在 `docs/whitepaper/Operit2论文版.md` 文件，核验方法见「来源」小节。`tools/docs/build_whitepaper.py:32`
- 构建产物写到 `output/pdf/Operit2技术白皮书-论文版.pdf`。`tools/docs/README.md:10`
- 构建器刷新中文仓库 PDF。`tools/docs/README.md:10`
- 构建器把每一页渲染到 `tmp/pdfs/operit2-paper/` 供目视检查。`tools/docs/README.md:11`
- 构建命令须从仓库根目录运行。`tools/docs/README.md:3`
- 构建命令是 `.venv/Scripts/python.exe tools/docs/build_whitepaper.py`，该命令为 Windows PowerShell 形式。`tools/docs/README.md:5`
- 字体嵌入使用 Windows SimSun、SimHei、Times New Roman 与 matplotlib 的 STIX General。`tools/docs/README.md:14`
- 实现描述源自仓库文档与源码检查。`tools/docs/README.md:35`
- 文档生成未做性能测量，也未做完整运行时测试执行。`tools/docs/README.md:36`

## AI 速览

- `SOURCE` — 声明的原稿路径 `docs/whitepaper/Operit2论文版.md`。`tools/docs/build_whitepaper.py:32`
- `OUTPUT` — 构建产物路径 `output/pdf/Operit2技术白皮书-论文版.pdf`。`tools/docs/build_whitepaper.py:33`
- `QA` — 逐页预览与核验报告目录 `tmp/pdfs/operit2-paper`。`tools/docs/build_whitepaper.py:34`
- `register_fonts` — 从 `C:/Windows/Fonts` 嵌入本地字体。`tools/docs/build_whitepaper.py:47`
- `styles` — 定义论文版段落样式层级。`tools/docs/build_whitepaper.py:78`
- `manuscript` — 把原稿 Markdown 转为排版后的页面流。`tools/docs/build_whitepaper.py:349`
- `Diagram` — 在 PDF 内直接绘制五种矢量图。`tools/docs/build_whitepaper.py:162`
- `equation` — 把 LaTeX 公式渲染为高分辨率 PNG。`tools/docs/build_whitepaper.py:301`
- `make_table` — 排布三线表并记录表格审计。`tools/docs/build_whitepaper.py:325`
- NumberedCanvas — 在页脚写入作者与页码 / 总页数。`tools/docs/build_whitepaper.py:142`、`tools/docs/build_whitepaper.py:144`
- `header` — 在每页顶部绘制运行标题。`tools/docs/build_whitepaper.py:149`
- `render_qa` — 渲染逐页图、联系表并写 verification.json。`tools/docs/build_whitepaper.py:416`
- `main` — 构建 PDF、刷新仓库副本、调用 `render_qa` 的主入口。`tools/docs/build_whitepaper.py:459`
- 数据流向：原稿 Markdown → `manuscript` 分块排版 → `BaseDocTemplate` 构建 PDF → 复制为仓库 PDF → `render_qa` 逐页渲染核验。`tools/docs/build_whitepaper.py:454`

## 核心机制

- 构建依赖 ReportLab、matplotlib、Pillow、pypdf、pypdfium2。`tools/docs/README.md:13`
- 脚本导入 matplotlib。`tools/docs/build_whitepaper.py:12`
- 脚本把 matplotlib 后端设为 Agg。`tools/docs/build_whitepaper.py:14`
- 脚本导入 pypdfium2 并别名为 pdfium。`tools/docs/build_whitepaper.py:16`
- 脚本从 PIL 导入 Image 与 ImageDraw。`tools/docs/build_whitepaper.py:17`
- 脚本从 pypdf 导入 PdfReader。`tools/docs/build_whitepaper.py:18`
- 脚本从 reportlab.lib 导入 colors。`tools/docs/build_whitepaper.py:19`
- ROOT 是 build_whitepaper.py 所在文件的上两级目录。`tools/docs/build_whitepaper.py:31`
- 页面尺寸取自 reportlab 的 A4。`tools/docs/build_whitepaper.py:35`
- MARGIN 由 25 mm 换算为 25 * 72 / 25.4 磅。`tools/docs/build_whitepaper.py:36`
- `register_fonts` 从 `C:/Windows/Fonts` 嵌入本地安装的字体，该路径为 Windows 路径。`tools/docs/build_whitepaper.py:47`
- `register_fonts` 注册 Song 对应 simsun.ttc、Hei 对应 simhei.ttf。`tools/docs/build_whitepaper.py:48`
- `register_fonts` 注册 Times 对应 times.ttf、TimesBold 对应 timesbd.ttf。`tools/docs/build_whitepaper.py:49`
- Math 字体注册为 matplotlib 数据路径下的 fonts/ttf/STIXGeneral.ttf。`tools/docs/build_whitepaper.py:53`
- `inline` 把原稿中的 URL 转为 Times 字体的可点击链接。`tools/docs/build_whitepaper.py:56`
- `manuscript` 以 UTF-8 读 SOURCE，按空行分块。`tools/docs/build_whitepaper.py:351`
- `manuscript` 遇到 `<!-- page -->` 块插入 PageBreak。`tools/docs/build_whitepaper.py:349`
- `manuscript` 在参考文献与附录小节前插入 PageBreak。`tools/docs/build_whitepaper.py:349`
- manuscript 要求每个 `:::figure` 图块后随一个以图加数字开头的题注。`tools/docs/build_whitepaper.py:394`
- `manuscript` 用 KeepTogether 把表格题注与表格保持在一起。`tools/docs/build_whitepaper.py:349`
- `equation` 把数学显示设为 mathtext 字体集 stix、字体 STIXGeneral。`tools/docs/build_whitepaper.py:303`
- `equation` 把公式渲染为 320 dpi 的 PNG。`tools/docs/build_whitepaper.py:301`
- `make_table` 的表格审计记录三条横线 1.25/0.75/1.25 pt、竖线 0 条、背景 None、题注在上、字号 10.5 pt。`tools/docs/build_whitepaper.py:325`
- `render_qa` 把每页渲染保存为 page-NN.png。`tools/docs/build_whitepaper.py:416`
- `render_qa` 每 6 页拼一张 contact-N.png 联系表。`tools/docs/build_whitepaper.py:416`
- `render_qa` 的报告记录页数、字节数、表格审计与排版参数。`tools/docs/build_whitepaper.py:416`
- `render_qa` 把报告写到 QA 下的 verification.json。`tools/docs/build_whitepaper.py:416`
- 写作指导参考 K-Dense Scientific Agent Skills 与 scientific-writing。`tools/docs/README.md:27`
- README 引用 Kassis T、Agarwal V、He Y 等 2026 年的 Scientific Agent Skills。`tools/docs/README.md:28`
- 该引用的 DOI 是 https://doi.org/10.48550/arXiv.2609.00065。`tools/docs/README.md:29`
- AI 协助了公开来源检索、文本编辑与 PDF 生成。`tools/docs/README.md:31`
- 编辑工作流与排版说明属于本构建记录。`tools/docs/README.md:32`

## 关键符号

- `SOURCE` — 声明的原稿路径，见「概述」中原稿未核实到的说明。`tools/docs/build_whitepaper.py:32`
- `OUTPUT` — 构建产物路径。`tools/docs/build_whitepaper.py:33`
- `QA` — 预览与核验目录。`tools/docs/build_whitepaper.py:34`
- `MARGIN` — 25 mm 换算的页边距。`tools/docs/build_whitepaper.py:36`
- `register_fonts` — 注册 Song、Hei、Times、TimesBold 四种字体。`tools/docs/build_whitepaper.py:48`
- `register_fonts` — Math 字体注册为 matplotlib 数据路径下的 fonts/ttf/STIXGeneral.ttf。`tools/docs/build_whitepaper.py:45`
- `styles` — 正文基础样式用 Song 12 pt、行距 20。`tools/docs/build_whitepaper.py:80`
- `body` — 两端对齐、首行缩进 24 的正文样式。`tools/docs/build_whitepaper.py:83`
- `h2` — Hei 14 pt、行距 22 的一级标题样式。`tools/docs/build_whitepaper.py:84`
- `h3` — Hei 12 pt、行距 20 的二级标题样式。`tools/docs/build_whitepaper.py:86`
- `title` — Hei 22 pt、行距 31、居中的标题样式。`tools/docs/build_whitepaper.py:88`
- `abstract` — Song 10.5 pt、行距 15 的摘要样式。`tools/docs/build_whitepaper.py:98`
- NumberedCanvas — 在页脚写 Operit开发团队。`tools/docs/build_whitepaper.py:142`
- NumberedCanvas — 在页脚右端写当前页码 / 总页数。`tools/docs/build_whitepaper.py:144`
- `header` — 在每页顶部左端写 Operit2 技术白皮书。`tools/docs/build_whitepaper.py:152`
- `header` — 在每页顶部右端写架构、路由机制与工程实践。`tools/docs/build_whitepaper.py:153`
- `Diagram` — 支持 architecture、migration、routing、handoff、engineering 五种图。`tools/docs/build_whitepaper.py:162`
- 排版纸张为 A4，边距 25 mm。`tools/docs/README.md:17`
- 中文标题用 SimHei 22 pt，正文用 SimSun 12 pt、20 pt 行距。`tools/docs/README.md:18`
- 一级标题用 SimHei 14 pt，二级标题用 SimHei 12 pt。`tools/docs/README.md:19`
- 摘要、题注、表格与参考文献用 10.5 pt。`tools/docs/README.md:20`
- 拉丁文本用 Times New Roman。`tools/docs/README.md:21`
- 表格题注在上，恰好三条横线，线宽依次为 1.25/0.75/1.25 pt。`tools/docs/README.md:22`
- 表格无底纹、无竖线，图表与其题注保持在一起。`tools/docs/README.md:23`

## 调用链

1. `main` 创建 OUTPUT 的父目录与 QA 目录。`tools/docs/build_whitepaper.py:446`
2. `main` 调用 `register_fonts` 嵌入字体。`tools/docs/build_whitepaper.py:448`
3. main 构建的 PDF 标题元数据是 Operit2：面向个人设备空间的跨端智能体系统——架构、路由机制与工程实践。`tools/docs/build_whitepaper.py:451`
4. main 构建的 PDF 作者元数据是 Operit开发团队。`tools/docs/build_whitepaper.py:452`
5. `main` 用 NumberedCanvas 作为画布构建文档。`tools/docs/build_whitepaper.py:457`
6. `main` 构建后把 OUTPUT 复制为 docs/Operit2技术白皮书.pdf。`tools/docs/build_whitepaper.py:458`
7. `main` 最后调用 render_qa。`tools/docs/build_whitepaper.py:459`

## 来源

- seed 文件：`tools/docs/README.md`（全文 38 行）与 `tools/docs/build_whitepaper.py`（全文 463 行），合计 501 行，均已读完。`tools/docs/README.md:1`
- 原稿不存在的核验方法：2026-11-11，对基线 AAswordman/Operit2 @ 364d1d594 的本地 checkout 执行 `ls docs/whitepaper`，返回 No such file or directory；执行 `test -f docs/whitepaper/Operit2论文版.md`，返回不存在；全仓 grep `论文版|docs/whitepaper`（`*.py`、`*.md`、`*.yaml`、`*.toml`）仅命中 `tools/docs/README.md:9` 与 `tools/docs/build_whitepaper.py:32` 两处声明本身。`tools/docs/build_whitepaper.py:32`
- 刷新目标存在的核验结果：同一基线下 `test -f docs/Operit2技术白皮书.pdf` 返回存在，`main` 的复制目标文件在基线内有对应物。`tools/docs/build_whitepaper.py:458`
- 本页不写版本号与日期：脚本与 README 均未写死白皮书版本号或构建日期，版本行由原稿 `版本：` 块按 version 样式排版，而原稿未在基线核实到。`tools/docs/build_whitepaper.py:373`
- 相关页：构建脚本入口见 [[tools-build-scripts|构建脚本入口]]。`tools/docs/README.md:5`
