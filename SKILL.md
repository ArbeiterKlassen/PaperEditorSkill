---
name: write-paper-report
description: 论文与报告的全流程写作技能。先确认用户要写论文还是报告，查找或生成模板，收集内容、数据、表格与图的需求并列出待办清单，按 8 阶段流水线完成写作、审查与修改，最后用本地 xelatex 编译为 PDF。当用户要求撰写、修改、润色、审查或编译论文/报告，或要求用 LaTeX 产出结构化文档并做质量检查时使用。
---

# 论文/报告全流程写作

## 概述

本技能把论文与报告的写作组织为固定流程：确认类型、准备模板、收集内容、写作、审查、编译。每个环节有明确产物。审查不通过就退回修改，不跳过。

## 工作流

### 1. 确认类型

先问用户要写论文还是报告。用户没有明确时，按论文处理，并在开头说明这个假设。

### 2. 准备模板

论文：在工作区查找模板与 Author Kit（.cls、.sty、模板目录、模板压缩包）。找到后询问用户是否使用。找不到就使用 [assets/templates/paper-skeleton.tex](assets/templates/paper-skeleton.tex) 生成初稿。

目标会议是 AAAI 时，样式文件用 [assets/aaai2027/](assets/aaai2027/) 里的 aaai2027.sty 与 aaai2027.bst，详见 [references/latex.md](references/latex.md)。

目标是期刊时，用 [assets/templates/journal-skeleton.tex](assets/templates/journal-skeleton.tex) 生成初稿，投稿前换成目标期刊的官方模板。学术报告用 [assets/templates/report-academic-skeleton.tex](assets/templates/report-academic-skeleton.tex)，含封面、摘要、目录与附录。

数学建模竞赛（高教社杯/华数杯）优先用 [assets/cumcmthesis/cumcmthesis.cls](assets/cumcmthesis/cumcmthesis.cls) 社区标准类，用法示例见 [assets/templates/cumcm-skeleton.tex](assets/templates/cumcm-skeleton.tex)。电子版用 withoutpreface 选项，承诺书与编号专用页用官方模板单独提交。

报告：查找报告模板。找到后询问用户是否使用。找不到就使用 [assets/templates/report-skeleton.tex](assets/templates/report-skeleton.tex) 生成初稿。

### 3. 收集内容

问清以下内容：主题与目标读者，必要细节，数据及其口径，需要的表格，需要的图，页数与参考文献数量。会议、期刊、报告对页数和文献数量的要求不同，必须与用户核实，不按默认值。整理成待办清单，与用户确认后再动笔。记录每个数字的来源，正文只引用核对过的数据。

### 4. 写作与完善

按 [references/pipeline.md](references/pipeline.md) 的 8 阶段执行。论文走完整流程。报告走精简流程：资料核查、结构与初稿、数据核对、审查、定稿，跳过投稿与审稿响应阶段。

写作语言按 [references/writing.md](references/writing.md) 执行：短句直述，术语一致，不用排比堆砌，不用长难句，不用空泛的大词。

进入修改循环前用 [scripts/snapshot_version.py](scripts/snapshot_version.py) 打版本快照，规范见 [references/versioning.md](references/versioning.md)。每轮修改按三遍进行：结构、句子、词。

需要 teaser 或 overview 图时，按 [references/figures.md](references/figures.md) 先定叙事再画面板，模板见 [assets/templates/teaser_template.py](assets/templates/teaser_template.py)。

### 5. 审查

按 [references/review.md](references/review.md) 执行六类审查：数值一致性、交叉引用与编译、匿名合规、表述清理、可复现性、参考文献核查。每类给出 PASS 或 FAIL 与证据清单。出现 FAIL 就修复，修复后全量重跑审查，不只查改动处。

用 [scripts/check_submission.py](scripts/check_submission.py) 扫描提交包：备份文件、缺失的图与引用、未定义引用、匿名泄漏。匿名投稿时加 --anonymous，会额外扫源文件里的作者块、中文字符与绝对路径。

用 [scripts/check_references.py](scripts/check_references.py) 检查 .bib 结构，加 --tex 核对 thebibliography 与 bib 的年份一致性，加 --online 联网核验 arXiv 与 DOI，防止 AI 编造文献。没有 arXiv 或 DOI 的条目按标题加作者人工检索。

数值一致性用 [scripts/check_numbers.py](scripts/check_numbers.py) 生成正文数字清单，加 --csv 与数据源对照，找出不在数据源中的数字。

投稿前按 [references/rebuttal.md](references/rebuttal.md) 模拟四类审稿人，逐条准备回答。语言问题用 [scripts/check_ai_style.py](scripts/check_ai_style.py) 扫描 AI 痕迹词与长句，按 [references/writing.md](references/writing.md) 的三遍修订法处理。

### 6. 编译

用 [scripts/compile_latex.py](scripts/compile_latex.py) 编译。脚本会先检测本地 xelatex。环境缺失时，告诉用户需要安装 TeX 环境，说明安装方式，得到用户同意后再继续。

## 门控规则

每个阶段先产出固定产物（待办清单、数据口径表、claim 与证据对照表、版本说明），下一阶段开工前先核对上一阶段的产物。审查不过就退回，不给部分通过。

## 资源

- [scripts/compile_latex.py](scripts/compile_latex.py)：编译主 .tex，自动跑 xelatex 与 bibtex 到引用稳定，从日志汇总错误与警告。
- [scripts/check_submission.py](scripts/check_submission.py)：扫描提交包的备份文件、引用完整性与匿名泄漏。
- [scripts/check_ai_style.py](scripts/check_ai_style.py)：扫描 AI 痕迹词、排比连接词与长句。
- [scripts/check_references.py](scripts/check_references.py)：检查 .bib 结构，联网核验 arXiv 与 DOI。
- [scripts/check_numbers.py](scripts/check_numbers.py)：列出正文数字，与数据源 CSV 对照。
- [scripts/snapshot_version.py](scripts/snapshot_version.py)：版本快照到 archive/ 并追加变更记录。
- [references/pipeline.md](references/pipeline.md)：8 阶段流水线的完整说明，含每阶段产物与自动化要点。
- [references/review.md](references/review.md)：五类审查的操作细则与 PASS/FAIL 判定。
- [references/writing.md](references/writing.md)：语言规范与版式调整要求。
- [references/latex.md](references/latex.md)：LaTeX 编译、中文支持、交叉引用与匿名处理。
- [references/rebuttal.md](references/rebuttal.md)：投稿前模拟审查与审稿意见响应流程。
- [references/versioning.md](references/versioning.md)：版本快照、命名与变更记录规范。
- [references/figures.md](references/figures.md)：teaser/overview 绘图的叙事、面板与版式。
- [assets/templates/paper-skeleton.tex](assets/templates/paper-skeleton.tex)：论文初稿骨架。
- [assets/templates/cumcm-skeleton.tex](assets/templates/cumcm-skeleton.tex)：数学建模竞赛论文骨架，摘要页与正文分离，不含承诺书页。
- [assets/cumcmthesis/cumcmthesis.cls](assets/cumcmthesis/cumcmthesis.cls)：数学建模竞赛 LaTeX 类文件，含题号、报名号、队员等命令。
- [assets/templates/journal-skeleton.tex](assets/templates/journal-skeleton.tex)：期刊论文骨架，附 IEEEtran、elsarticle、sn-jnl 替换说明。
- [assets/templates/report-skeleton.tex](assets/templates/report-skeleton.tex)：报告初稿骨架。
- [assets/templates/report-academic-skeleton.tex](assets/templates/report-academic-skeleton.tex)：学术报告骨架，含封面、摘要、目录与附录。
- [assets/templates/claim-evidence.csv](assets/templates/claim-evidence.csv)：claim 与证据对照表模板。
- [assets/templates/rebuttal-template.md](assets/templates/rebuttal-template.md)：审稿意见逐条回应模板。
- [assets/templates/teaser_template.py](assets/templates/teaser_template.py)：三面板 teaser 绘图模板。
- [assets/templates/title-abstract-intro-check.md](assets/templates/title-abstract-intro-check.md)：标题、摘要、引言对照表。
- [assets/templates/submission-checklist.md](assets/templates/submission-checklist.md)：提交前人工检查清单。
- [assets/aaai2027/](assets/aaai2027/)：AAAI-27 Author Kit 样式文件，aaai2027.sty 与 aaai2027.bst。
