# LaTeX 编译与版式

## 编译环境

- 检测 xelatex，运行 xelatex --version。
- 缺失时询问用户是否安装 TeX Live，或改用可用的替代引擎。
- 中文文档用 ctex 宏包，UTF-8 编码，xelatex 编译。

## 编译流程

- 优先用 [scripts/compile_latex.py](../scripts/compile_latex.py)。
- 手工流程：xelatex 后接 bibtex，再跑两遍 xelatex。
- 检查日志中的 Error、Warning、undefined citation、undefined reference。

## 交叉引用

- 图表用 \label 与 \ref，公式用 \eqref。
- 引用用 \cite，参考文献由 bibtex 或 biber 处理。
- 编译结束后必须确认没有未定义引用。

## 图

- 图用脚本生成，数据来自冻结的数据源，不手填数值。
- 优先矢量格式，pdf 内嵌。
- 图注与正文数字一致。

## 匿名处理

- 删除绝对路径与作者信息。
- 检查压缩包内的文件清单与元数据。
- 第三方代码署名保留。

## 会议模板（以 AAAI 为例）

### 模板文件

Author Kit 通常包含 .sty、.bst、模板 .tex 与 checklist。三份文件都要进提交包，编译时放同一目录。

本技能自带 AAAI-27 Author Kit 的样式文件，在 assets/aaai2027/，包含 aaai2027.sty 与 aaai2027.bst。编译时复制到论文目录。样式文件按官方声明不得修改。

### 前言固定写法

模板开头的这几行不要改：documentclass、`\usepackage[submission]{aaai2027}`、natbib（不加选项）、caption、url、`\frenchspacing`、`\pdfinfo{/TemplateVersion ...}`。

`\setcounter{secnumdepth}{0}` 使章节不编号，这是 AAAI 版式的一部分，不要删。

### 作者块

投稿版（双盲）：`\author{Anonymous submission}`，`\affiliations{Paper ID: [assigned after submission]}`。

相机就绪版：真实作者与机构，作者用 `\equalcontrib` 或 `\corresponding` 标记，机构用 `\textsuperscript{\rm 1,2}` 上标。

同一 tex 里用注释保留两个版本时，要确认只有投稿版处于激活状态。中文注释不要写真实姓名，匿名审查扫的是源文件，不是 PDF。

### 章节与图表

表格标题放在表格下方，图题放在图下方。宽表格用 `\resizebox{\linewidth}{!}{...}`，跨栏图用 `figure*`，正文图用 `figure` 单栏。数字与符号在表格里用数学模式，如 `\(\alpha\)`。

### 参考文献

AAAI 允许两种方式：bibtex 配合 aaai2027.bst，或在文末手写 `thebibliography`。手写时标签格式如 `[Behley et al.(2019)]`。两种方式都要保证每个 `\cite` 有对应条目，条目年份与 key 一致。

bib key 统一格式：第一作者姓加年份加关键词，如 behley2019semantickitti。key 里的年份必须与条目年份一致。

中文期刊参考文献常用 GB/T 7714 格式，可用 gbt7714 宏包配合 bibtex，投稿前按目标期刊要求核对。

### 可复现性 checklist

checklist 可以独立编译，也可以在主文件 `\end{document}` 前 `\input`。独立编译时用 `\if...\fi` 开关区分两种模式。提交前确认 checklist 每个问题都填了答案，且答案与论文内容一致。

### 补充材料

补充材料用同一模板，正文里的定理和附录一一对应。附录用 `\section*{Appendix A: ...}` 形式。主文承诺的附录（如 Appendix~J）必须在补充材料里真实存在。证明放补充材料时，主文引用 `\ref` 指向对应附录小节。

## 期刊与学术报告模板

skill 自带两份模板：

[assets/templates/journal-skeleton.tex](../assets/templates/journal-skeleton.tex) 是英文期刊论文骨架，默认用 article 类。投稿前换成目标期刊官方模板：IEEE 系期刊用 IEEEtran，Elsevier 期刊用 elsarticle，Springer 期刊用 sn-jnl，这些类多数 TeX Live 发行版自带。期刊投稿材料一般还包含 cover letter、highlights 与 graphical abstract，正文定稿后再准备。

[assets/templates/report-academic-skeleton.tex](../assets/templates/report-academic-skeleton.tex) 是中文学术报告骨架，用 ctexrep，含封面、摘要、关键词、目录、章节、参考文献与附录。数据类报告每章先结论后依据，数字注明来源。

数学建模竞赛（高教社杯 CUMCM）用 [assets/templates/cumcm-skeleton.tex](../assets/templates/cumcm-skeleton.tex)。按官方格式规范：电子版第一页为摘要专用页，含标题与关键词、不超过一页、页码从本页起编；正文不设目录；承诺书与编号专用页不在电子版中，用官方 Word 模板单独填写提交。

社区标准类 [assets/cumcmthesis/cumcmthesis.cls](../assets/cumcmthesis/cumcmthesis.cls) 提供完整版式。常用写法：`\documentclass[withoutpreface,bwprint]{cumcmthesis}`，`\tihao{A}` 写题号，`\baominghao{}` 写报名号，`\membera/b/c{}` 写队员，`\keywords{...}` 在 abstract 环境内写关键词。withoutpreface 表示电子版不含承诺书与编号页；纸质版需要时去掉该选项。

## 页数与参考文献数量

- 会议论文：正文页数与参考文献页数按 CFP 分别要求。AAAI 这类双栏会议对文献页数有规定，以当年 CFP 为准。
- 期刊论文：页数或字数限制按 Author Guide，图表数量可能计入。
- 学术报告：页数由任务要求决定，无统一规范。
- 文献数量：十几篇的报告与一页半文献的会议论文差距很大。写作前与用户核实目标数量，不按默认值。
- 文献页数不够时，先检查引用是否完整，再考虑补充相关工作。不为了凑数加无关文献。
