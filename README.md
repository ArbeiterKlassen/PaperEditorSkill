# write-paper-report

本仓库提供一个 Codex skill，用于论文、技术报告和专利文件的写作、修改、审查与编译。执行规则以 `SKILL.md` 为准，本文件说明 skill 的适用范围、工作流程、检查工具和使用方式。

## 适用范围

skill 覆盖五类文档。

- 会议论文
- 期刊论文
- 普通报告
- 学术报告
- 发明专利申请文件

每类文档都有对应的骨架、审查重点和编译方式。会议论文和期刊论文按完整流水线执行。普通报告和学术报告走精简流程。专利文件的权利要求支持、术语统一和权利要求规范性单独处理。

## 设计约束

- 文档类型先于写作模板确定。
- 页数、参考文献数量和交付格式按目标会议、期刊或课程要求确定，不采用默认值。
- 正文数字必须能追溯到数据文件、复算代码或文献。
- 修改前保存版本快照，修改后全量重跑审查。
- 审查按七类执行，出现阻塞项就回到修改阶段。
- 多轮精改按版本差异复核，逐条判断外部意见是否仍然适用。
- 语言遵守短句原则。一个句子表达一个事实，避免长难句、排比堆砌和无法量化的形容词。

## 主流程

### 1. 确认文档类型

先判断任务是论文、报告还是专利文件。用户没有指定时，按论文处理，并在交付说明中写明这一假设。专利文件需要额外检查权利要求的支持关系和术语边界。

### 2. 准备模板

论文优先使用目标会议或期刊的 Author Kit。
没有模板时使用 `assets/templates/paper-skeleton.tex` 或 `assets/templates/journal-skeleton.tex`。
学术报告使用 `assets/templates/report-academic-skeleton.tex`。
普通报告使用 `assets/templates/report-skeleton.tex`。
数学建模竞赛使用 `assets/cumcmthesis/cumcmthesis.cls`。
专利文件通常用 python-docx 脚本生成，写作规范见 `references/patent.md`。

### 3. 收集写作条件

写作前需要确认主题、目标读者、数据口径、必要表格、必要图件、页数范围和参考文献数量。报告的数据来源需要落盘，正文只引用已经核对的数据。

### 4. 写作与修改

论文按 `references/pipeline.md` 的八阶段流程执行。报告走精简流程，保留资料核查、结构与初稿、数据核对、审查和定稿五个阶段。每轮修改前使用 `scripts/snapshot_version.py` 保存版本，修改按结构、句子、词三个层次推进。

### 5. 审查

审查按七类执行。

1. 数值一致性
2. 交叉引用与编译
3. 匿名合规
4. 表述清理
5. 可复现性
6. 参考文献核查
7. 创新与对比核查

每类审查输出 PASS 或 FAIL，并附证据清单。出现 FAIL 时先修复，再从第一类开始全量复查。

### 6. 编译

使用 `scripts/compile_latex.py` 调用本地 xelatex。脚本会自动处理多次编译和 bibtex 或 biber，并从日志中汇总错误、警告、未定义引用和字体缺字。

## 多轮精改

`references/polish.md` 面向成稿复核场景。适用条件包括用户提交改后稿、提供导师或组会意见、要求逐句润色，或者要求评估另一版修改是否引入回归。

精改流程包含五类检查。

- 对比上一版，确认上一轮意见是否落实，并查找本轮引入的新错误
- 将外部意见逐条映射到当前文本，给出采纳、部分采纳或不采纳的判定
- 检查比率型指标的方向、均值统计基准和多步推导是否与公式一致
- 检查主文档与支撑文档的数值、术语和披露内容是否同步
- 检查加黑预算、内部编辑提示、证据链和诚实表述是否被误改

每轮精改生成一份报告。报告包含分级清单、批量替换表、请核对清单、不要动清单和验收清单。模板位于 `assets/templates/polish-report-template.md`。

## 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/compile_latex.py` | 编译 LaTeX 项目，处理多轮编译与参考文献，汇总日志问题 |
| `scripts/check_submission.py` | 扫描提交包，检查缺失图件、未定义引用、备份文件和匿名泄漏 |
| `scripts/check_references.py` | 检查 bib 结构，核对 thebibliography 年份，联网核验 arXiv 和 DOI |
| `scripts/check_ai_style.py` | 扫描空话、排比、长句、模板腔、正文斜杠和内部编辑提示 |
| `scripts/check_numbers.py` | 提取正文数字，与 CSV 或参考数字表对照 |
| `scripts/check_consistency.py` | 检查标签引用、写死编号、附录代码、页数和字体缺字 |
| `scripts/snapshot_version.py` | 把当前稿复制到 archive/vN，并写入变更记录 |
| `scripts/validate.sh` | 检查 SKILL 链接、Markdown 链接和脚本语法 |

## 参考文档

| 文档 | 内容 |
|------|------|
| `references/pipeline.md` | 八阶段写作流水线，每阶段产物和自动化要点 |
| `references/review.md` | 七类审查的判定标准和操作步骤 |
| `references/writing.md` | 语言规范、AI 文本修法、三遍修订法 |
| `references/latex.md` | 中文 LaTeX、会议模板、期刊模板和编译流程 |
| `references/rebuttal.md` | 投稿前模拟审查和审稿意见响应 |
| `references/versioning.md` | 版本快照、命名、变更记录和提交前清理 |
| `references/figures.md` | teaser 和 overview 图的叙事、面板与数据同源 |
| `references/cumcm.md` | 数学建模竞赛论文的篇幅、摘要、图表和附录代码规范 |
| `references/patent.md` | 专利文件结构、权利要求支持和规范性审查 |
| `references/consistency.md` | 编号漂移、附录代码、页数配平和字体缺字案例 |
| `references/polish.md` | 成稿多轮精改、外部意见判定和跨文档口径复核 |

## 模板与样式

| 文件 | 用途 |
|------|------|
| `assets/templates/paper-skeleton.tex` | 会议论文骨架 |
| `assets/templates/journal-skeleton.tex` | 期刊论文骨架 |
| `assets/templates/report-skeleton.tex` | 普通报告骨架 |
| `assets/templates/report-academic-skeleton.tex` | 学术报告骨架 |
| `assets/cumcmthesis/cumcmthesis.cls` | 数学建模竞赛论文类文件 |
| `assets/templates/claim-evidence.csv` | 论点与证据对照表 |
| `assets/templates/title-abstract-intro-check.md` | 标题、摘要和引言对照表 |
| `assets/templates/submission-checklist.md` | 提交前人工检查清单 |
| `assets/templates/polish-report-template.md` | 精改报告模板 |
| `assets/templates/rebuttal-template.md` | 审稿意见响应模板 |
| `assets/templates/teaser_template.py` | 多面板 teaser 绘图模板 |
| `assets/aaai2027/` | AAAI-27 样式文件和参考文献样式 |

## 目录结构

```text
write-paper-report/
├── SKILL.md
├── README.md
├── agents/
│   └── openai.yaml
├── references/
├── scripts/
└── assets/
    ├── aaai2027/
    └── templates/
```

## 使用方式

在 Codex 中说明文档类型、目标会议或期刊、模板位置、数据来源、页数要求和参考文献数量。没有模板时使用仓库自带骨架。写作过程按 `SKILL.md` 的门控规则推进。提交前运行七类审查，并通过编译脚本生成最终 PDF。

常用命令如下。

```bash
python scripts/compile_latex.py main.tex
python scripts/check_submission.py paper/ --anonymous
python scripts/check_references.py references.bib --tex main.tex --online
python scripts/check_ai_style.py main.tex
python scripts/check_numbers.py main.tex --csv figures/result.csv
python scripts/check_consistency.py paper/ --codes codes/ --pdf paper/main.pdf --log paper/main.log
python scripts/snapshot_version.py paper/ --message "修改摘要"
bash scripts/validate.sh .
```

## 环境与验证

LaTeX 编译需要 TeX Live 2025 或更新版本，也可以使用 MacTeX。检查脚本需要 Python 3.8 或更新版本。文献联网核验需要访问 arXiv 和 Crossref。`validate.sh` 需要 bash。Windows 环境可以使用 Git Bash。

修改 skill 后运行 `validate.sh`。该脚本检查 `SKILL.md` 的 frontmatter、Markdown 链接和 `scripts/` 下的 Python、JavaScript 与 shell 语法。

## 扩展方式

新增会议或期刊时，把官方 `.sty` 和 `.bst` 放入 `assets/<名称>/`，并同步更新 `SKILL.md` 和 `references/latex.md`。

新增检查项时，在 `scripts/` 添加脚本，在 `SKILL.md` 的资源清单中登记，并在 `references/review.md` 写清判定标准。修改完成后运行 `validate.sh`，确认链接和脚本语法保持有效。
