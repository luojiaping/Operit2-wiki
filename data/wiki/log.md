# Operit2-wiki 合并日志

> 追加记录，不删改。每次合并一批条目记一条。

## 2026-11-11 · batch-01（P0 首批 10 页，第 1、2 章）

- 来源：AAswordman/Operit2 @ 364d1d594；大纲 v1（outline-v1.yaml，11 章 115 页）已于 2026-11-11 获用户批准。
- 页：intro-overview、intro-not-what、intro-preview、intro-quickstart、arch-overview、arch-corenode、arch-space、arch-binding、arch-sync、arch-routing。
- 事实：761 条原子事实（facts.json），引用全部落在源文件行号范围内，坏引用 0。
- Lint：`lint.py --dir review/batch-01` 硬失败 0、警告 0。
- Critic：首批 5 页全审（intro-overview、intro-not-what、intro-preview、intro-quickstart、arch-overview），结论均为「需修改」小修，已按 critic.md 逐项修正并复验 lint 0/0；其余 5 页 facts 引用机械核验 0 坏引用。
- 质量走查（.quality.json）：4 页有记录——intro-quickstart（README 旧命令与代码不符、代理脚本缺失）、arch-overview（edge-architecture.md 断链、§8 旧名）、arch-corenode（两处断链）、arch-sync（edge-architecture.md 断链）。
- 阅读登记：16 个源文件 complete，见 tracking/read-status.json。
- 评审 Issue：#2–#11，状态均为 review-pending。
