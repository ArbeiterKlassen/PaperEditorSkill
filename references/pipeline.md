# 论文与报告写作 8 阶段流水线

> 本文档是 write-paper-report 技能的流程蓝图与质检清单。内容源自 AAAI-27 论文《Why Chamfer Distance Stalls in LiDAR Point Cloud Completion》从初版到投稿的完整写作复盘。
> 论文按 8 阶段完整执行。报告走精简路径：保留 Stage 0（资料核查）、Stage 3（初稿）、Stage 4（修改）、Stage 5（审查）、Stage 6（图表），跳过 Stage 7 投稿与 Stage 8 审稿响应。

---

## Stage 0 — 选题与文献调研

**做什么**：确认研究空白（gap），建立领域时间脉络与指标演进链。

- 本体论文精读：方法结构、关键数字、实验设置（例：OccWorld = VQVAE scene tokenizer + GPT 式时空生成，Occ3D 3s mIoU 17.14）
- 谱系梳理：嫡系后续 vs 平行工作 vs 天花板指标链（17.14→22.71→27.10→31.76→39.73）
- 常见陷阱核查：误标引用（如 OccVAR 无 arXiv ID，被普遍误标为 2408.14197=Drive-OccWorld）
- gap 定位三问：方法论可否迁移？已知失效模式在新域是否未被发现？基准空白（如 SemanticKITTI LiDAR 4D occ forecasting）？
- 产物：调研报告 + 证据链文件 + 相关论文包（含 INDEX）

**自动化要点**：deep-research 多 agent 并行（每维 ≥20 搜索、原始来源溯源、反方观点记录）；所有论断带引用；输出落盘 `/research/`。

所有引用上线核验：arXiv ID 与 DOI 逐条查询，无 arXiv/DOI 的条目按标题加作者人工检索。AI 生成内容会编造来源，作者、标题、年份组合搜不到结果的一律视为可疑。

## Stage 1 — 问题定位与理论分析

**做什么**：把"现象观察"升级为"可证伪的 claim + 理论刻画"。

- 现象：CD 在 LiDAR 补全上停滞（stall）
- 理论化：Jensen 间隙、Gersho 量化上界（39.8·u^0.733）、敏感度口径（1.3%）
- 设计 probe（SAR）隔离变量
- 每条 claim 预先绑定证据来源（数据/推导/引用）

**自动化要点**：维护 `claim→evidence` 对照表（后续审查、README、rebuttal 三处复用）；数学推导必须可复算。

## Stage 2 — 实验管线与数据治理

**做什么**：可复现的实验流水 + 指标口径冻结。

- 端到端管线脚本化（completion_pipeline），可视化脚本指向正主管线而非备份
- 逐帧指标 CSV（多基线 × 多种子 × worst20 切片）
- **口径单一来源（single source of truth）**：论文定义 CD=(P2G+G2P)/2，所有 CSV 按定义重算对齐
  - 教训：LiDiff CSV 的 cd 列是另一种聚合（0.424），未对齐即引用导致与正文 0.431 不一致 —— 数值必须按论文定义复算，不能"估计"来源
- 数据契约冻结：CSV 列名、config key、print 格式一旦冻结，清理/重构不得改动

**自动化要点**：指标生成与论文数值同源；每次改动后自动复算并 diff。

## Stage 3 — 初稿写作

**做什么**：按目标会议格式（AAAI）完成结构化初稿。

- 标准骨架：Intro（claim 列表）→ Related → Method/Analysis → Experiments → Conclusion
- 正文数字只引用 Stage 2 冻结口径
- 版本化管理：V3→V25 迭代，每版留变更说明（内部用，不进公开物）

**自动化要点**：paper-writing skill 起草；大纲先行、分章写作、引用管理。

语言规范与 AI 文本修法见 references/writing.md。

## Stage 4 — 修改循环

**做什么**：评审意见/导师意见/自查 → 定向修改 → 新版本。

- 意见逐条编号，逐条响应对照（DR#6 等内部代号留在内部版）
- 修改原则：改逻辑不动数据契约；改表述不动 claim 边界
- 版本考据、调参轶事、内部代号**绝不进入**对外产物

**自动化要点**：意见→修改任务清单化；每轮修改后触发 Stage 5 全量审查（不是只查改动处）。

版本快照与变更记录规范见 references/versioning.md。

## Stage 5 — 审查（自动化价值最高的阶段）

七类审查，全部可机器化：

1. **数值一致性**：正文每个数字 ↔ CSV 复算值逐一比对（0.424/0.431 事故的直接防线）；表格、图注、摘要全覆盖
2. **交叉引用与编译**：图表编号、引用键、import 有效性（教训：models.py import 不存在的旧名 linextnet，直接崩 train.py）；全部源码过语法审计（145 py 零错误）；编号漂移、附录代码完整性与页数配平用 scripts/check_consistency.py 核查，见 references/consistency.md
3. **匿名合规扫描**（投稿匿名版必做）：
   - 文本层：作者中英文名、机构、绝对路径（/home/xxx、/data1/xxx）、miniconda 路径
   - 二进制层：ckpt 内嵌 pickle 路径字符串（需二进制 scrub）
   - 元数据层：MANIFEST.txt、训练日志、zip 内文件逐一扫
   - 判定原则：作者身份信息全删；第三方署名（hilbert.py/z_order.py/ChamferDistancePytorch 等）属正当 credit 必须保留
4. **表述清理**：AI 痕迹注释（FIX/TODO/版本考据/调参轶事/中文注释→简洁英文）；保留数学推导注释与 why 注释；符号 ASCII 化（√→sqrt、α→alpha）
5. **可复现性**：requirements 完整、相对路径化（匿名+可移植双重要求）、README 的 claim→evidence 可验证
6. **参考文献核查**：每条文献真实存在（arXiv/DOI 核验），数量与会议/期刊要求一致
7. **创新与对比核查**：通用框架提炼完整，常规算法复现对比有数据，SOTA 点具体可验证

**自动化要点**：每类审查输出 PASS/FAIL + 证据清单，FAIL 必须打回修复后全量重跑。

补充两点实做：同一数量在摘要、图注、正文、表格、图里必须同一个值，按行号逐一核对；匿名扫描覆盖源文件层，tex 注释、被注释掉的作者块、bib 头注释都在检查范围。

## Stage 6 — 绘图管线

**做什么**：论文图全部脚本生成、与数据同源。

- 统一入口绘图脚本（vis_paper.py）→ 指向数据管线正主，禁指备份文件
- 图内数值来自冻结 CSV，不手填
- 风格统一：字体、配色、符号 ASCII；向量格式优先（pdf 内嵌）
- 图随数据自动重绘：数据更新 → 一键全图刷新 → 触发数值一致性复查

teaser/overview 的叙事、面板与版式见 references/figures.md，模板见 assets/templates/teaser_template.py。

## Stage 7 — 投稿与材料打包（双轨制）

| | OpenReview 匿名补充材料 | GitHub 公开版 |
|---|---|---|
| 身份 | 严格匿名（过 Stage 5.3 全扫） | 实名 + LICENSE + bibtex |
| 体积 | ≤50MB → 只放 CSV，**ply/ckpt 放不下** | 代码 + 小数据；大文件走 Release |
| README | claim→evidence 对照 + "released upon acceptance" | 完整文档 + 复现指南 |
| 过渡方案 | anonymous.4open.science 审稿期镜像 | — |

- 路径全部相对化；双包分别终检（217/218 文件零泄漏）

打包前删掉备份文件与旧版本文件（如 figures 里的 *_backup.pdf），bib 头注释里的旧版本号也要清掉。

## Stage 8 — 审稿响应与再投

- rebuttal 直接复用 claim→evidence 表与 Stage 5 审查证据
- 逐点回应模板化；新实验走 Stage 2 管线（口径不变）
- 录用后：匿名占位符→实名，镜像→正式仓库

投稿前模拟审查与审稿意见响应见 references/rebuttal.md，回应模板见 assets/templates/rebuttal-template.md。

---

## 自动化 Skill 设计要点（提炼）

1. **阶段门控（stage-gate）**：每阶段输出固定契约文件，下一阶段先验契约再开工；审查不过=打回，无部分分
2. **数值单一来源**：所有正文数字由 CSV 程序化注入/校验，杜绝手抄 —— 本项目最大的实际事故源
3. **双轨产物**：匿名轨/实名轨从同一源树派生，清理规则可配置（删作者信息 / 保第三方 credit 白名单）
4. **审查即代码**：七类审查写成可执行检查器（数值复算、语法+import 审计、身份正则+二进制扫描、AI 痕迹词表、复现 dry-run）
5. **图随数动**：绘图脚本化 + 数据变更触发重绘 + 图文一致性复查
6. **环境与交付教训**：限速源用断点续传+EOF 校验；产物写持久存储；大文件分卷+md5 双端校验

## 本技能中的落地方式

上述要点已落到 write-paper-report 技能中：
- SKILL.md：工作流与门控规则。
- references/review.md：七类审查的操作细则。
- scripts/compile_latex.py：LaTeX 编译与日志检查。
- scripts/check_consistency.py：编号三层核查、附录代码完整性、页数配平与字体缺字。
- references/consistency.md：上述检查的做法、真实案例与命令行用法。
- assets/templates/：论文骨架、报告骨架、claim-evidence 表。
