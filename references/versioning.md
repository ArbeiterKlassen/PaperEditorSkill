# 论文版本管理

原则：任何时刻只有一个源树。版本通过快照与变更记录管理，不在同一文件里堆多个版本的注释。

## 命名

主文件按语义命名加版本号，如 paper_full_v21.tex。备份文件不得留在工作目录，统一进 archive 目录。

## 快照

每轮修改前打快照：把源文件与 PDF 复制到 archive/v<下一版本号>/，同时写一条变更记录。用 [scripts/snapshot_version.py](../scripts/snapshot_version.py) 完成。

快照内容：
- 源 tex、bib、sty、bst、图源文件与数据。
- 编译好的 PDF。
- 变更记录一行：版本、日期、本轮改了什么。

不放快照：aux、log、out、toc、临时文件、压缩包。

## 变更记录

每轮修改先写变更说明，再动手。变更记录写清楚：
- 本轮改了什么：表述、数值、结构还是图。
- 动了哪个契约：数值口径、claim 边界、图表编号。
- 修改原则：改逻辑不动数据契约，改表述不动 claim 边界。

数值口径或 claim 变化时升主版本，仅表述修改升次版本，如 v21 到 v21.1。

## 提交前清理

版本考据、变更记录、内部代号一律不进提交包。提交前执行 [scripts/check_submission.py](../scripts/check_submission.py)，确认 archive 目录不在包内。

## 与 git 的配合

有 git 时：每个快照对应一次 commit，commit message 写变更记录；大改前打 tag。用 latexdiff 生成改动标记 PDF 给合作者看。没有 git 时用 snapshot_version.py 的 archive 机制。
