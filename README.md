# write-paper-report 论文/报告全流程写作 skill

本 skill 把论文与报告的写作组织成固定流程：确认类型、准备模板、收集需求、写作、审查、编译。适用于会议论文、期刊论文、学术报告和普通报告。用 Codex 打开后直接说要写论文或报告即可触发，也可以显式说 `Use $write-paper-report`。

## 功能总览

### 流程能力

- 六步工作流：确认论文/报告类型，找模板或生成初稿，收集需求，按 8 阶段流水线写作，六类审查，xelatex 编译。
- 门控规则：每阶段产出固定产物，下一阶段先核对上一阶段产物，审查不过就退回。
- 需求核实：页数与参考文献数量按会议/期刊/报告要求与用户确认，不按默认值。
- 四类文档形态：会议论文、期刊论文、普通报告、学术报告，各有对应骨架。

### 脚本（6 个）

| 脚本 | 功能 |
|------|------|
| compile_latex.py | 自动跑 xelatex 与 bibtex/biber 到引用稳定，从日志汇总错误、警告、未定义引用 |
| check_submission.py | 提交包扫描：备份文件、缺失的图与引用、未定义引用、cite 无对应条目；--anonymous 追加扫源文件与二进制文件的匿名泄漏 |
| check_references.py | 文献核查：结构检查、--tex 对照 thebibliography 年份、--online 核验 arXiv/DOI 真实存在 |
| check_ai_style.py | AI 痕迹扫描：空话开头、排比连接词、长句、拽词、连接词重复、破折号 |
| check_numbers.py | 正文数字清单，--csv/--ref 与数据源对照，标出数据源中找不到的数字 |
| snapshot_version.py | 版本快照到 archive/vN 并追加变更记录 |

### 参考文档（7 个）

| 文档 | 内容 |
|------|------|
| pipeline.md | 8 阶段流水线全说明，含每阶段产物与自动化要点 |
| review.md | 六类审查细则与 PASS/FAIL 判定 |
| writing.md | 语言规范、AI 文本问题修法、三遍修订法、标题/摘要/引言对照核查 |
| latex.md | 编译流程、AAAI 模板、期刊与学术报告模板、页数与文献数量要求 |
| rebuttal.md | 投稿前四视角模拟审查、高频攻击点、审稿意见响应流程 |
| versioning.md | 版本命名、快照、变更记录、提交前清理、与 git 配合 |
| figures.md | teaser/overview 叙事、面板规划、数据同源、版式与常见错误 |

### 模板与样式

- paper-skeleton.tex：会议论文骨架。
- cumcm-skeleton.tex：数学建模竞赛（高教社杯）论文骨架，摘要页与正文分离，电子版不含承诺书页。
- cumcmthesis/cumcmthesis.cls：数学建模竞赛 LaTeX 类，支持 withoutpreface 选项与题号、报名号、队员命令。
- journal-skeleton.tex：期刊论文骨架，附 IEEEtran、elsarticle、sn-jnl 替换说明。
- report-skeleton.tex：普通报告骨架。
- report-academic-skeleton.tex：学术报告骨架，含封面、摘要、目录、参考文献与附录。
- claim-evidence.csv：claim 与证据对照表。
- rebuttal-template.md：审稿意见逐条回应模板。
- teaser_template.py：三面板 teaser 绘图模板。
- title-abstract-intro-check.md：标题、摘要、引言对照表。
- submission-checklist.md：提交前人工检查清单。
- assets/aaai2027/：AAAI-27 官方样式文件，aaai2027.sty 与 aaai2027.bst。

### 元数据

- agents/openai.yaml：UI 名称、简介、默认提示词。
- README.md：本文件。

## 目录结构

```
write-paper-report/
├── SKILL.md            # 工作流与门控规则，Codex 执行时读取
├── README.md           # 本文件，面向使用者的说明
├── agents/openai.yaml  # UI 元数据
├── references/         # 流程细节，按需加载
├── scripts/            # 可直接运行的检查与工具
└── assets/
    ├── aaai2027/       # AAAI-27 样式文件
    └── templates/      # 骨架与可填模板
```

## 使用流程

1. 告诉 Codex 要写论文还是报告，以及目标会议或期刊。
2. 提供模板位置。没有模板时使用 skill 自带骨架。
3. 回答需求问题：主题、数据、表格、图、页数与参考文献数量。
4. 写作按 8 阶段流水线执行，语言按 writing.md 规范，每轮修改前打版本快照。
5. 提交前跑六类审查，逐项 PASS 或 FAIL。
6. 用 xelatex 编译，环境缺失时先安装再继续。

## 脚本用法

所有脚本用 Python 3 运行。

```bash
# 编译并汇总错误警告
python scripts/compile_latex.py main.tex

# 提交包扫描：备份文件、缺失引用、匿名泄漏
python scripts/check_submission.py <论文包目录> --anonymous

# 文献核查：结构检查 + 对照 thebibliography + 联网核验 arXiv/DOI
python scripts/check_references.py references.bib --tex main.tex --online

# 语言扫描：AI 痕迹词与长句
python scripts/check_ai_style.py main.tex

# 正文数字清单，可与数据 CSV 对照
python scripts/check_numbers.py main.tex --csv figures/result.csv

# 版本快照到 archive/vN 并写变更记录
python scripts/snapshot_version.py <论文包目录> --message "修改摘要"
```

## 环境要求

- TeX Live 2025 或更新版本（含 xelatex），或 MacTeX。
- Python 3.8 或更新。
- teaser 绘图模板需要 matplotlib 与 numpy。
- 文献联网核验需要可访问 arXiv 与 Crossref。

## 使用建议

- 数据口径单一来源：正文数字只从冻结的数据文件引用，不手填。
- 每轮修改前打版本快照，改动内容先写变更记录。
- 匿名投稿前必须跑 check_submission.py --anonymous，扫描对象包括源文件与二进制文件。
- 文献逐条联网核验，AI 生成的文献经常编造来源。
- 语言打磨按三遍修订法：结构、句子、词，顺序不要反。
- 提交前按 submission-checklist.md 逐项核对。

## 扩展方式

新会议或期刊：把官方 .sty 与 .bst 放进 assets/<会议名>/，在 SKILL.md 第 2 步和 references/latex.md 登记。

新检查项：在 scripts/ 加脚本，在 SKILL.md 的资源清单登记，并在 references/review.md 写判定标准。
