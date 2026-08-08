# 提交前检查清单

按顺序逐项核对，任何一项不过就不提交。

## 数值

- [ ] 正文、摘要、图注、表格的每个数字都能追溯到数据源
- [ ] 同一数量在所有位置用同一个值，跑 scripts/check_numbers.py 对照
- [ ] 数据口径冻结，无手填数字

## 引用与编译

- [ ] xelatex 编译无 error，无 undefined reference/citation
- [ ] 每条文献真实存在，跑 scripts/check_references.py --tex main.tex --online
- [ ] 文献数量与会议/期刊要求一致，已和用户确认

## 匿名（匿名投稿时）

- [ ] 作者、机构、绝对路径已清，跑 scripts/check_submission.py --anonymous
- [ ] 源文件注释、被注释的作者块、二进制文件无泄漏

## 语言

- [ ] 无 AI 痕迹词，跑 scripts/check_ai_style.py
- [ ] 标题、摘要、intro 对照表已填且一致
- [ ] 术语全文统一

## 打包

- [ ] 无备份文件、无旧版本文件，跑 scripts/check_submission.py
- [ ] 可复现性 checklist 已填并编译进包
- [ ] 补充材料与主文附录一一对应
- [ ] 期刊投稿材料齐备：cover letter、highlights、graphical abstract
