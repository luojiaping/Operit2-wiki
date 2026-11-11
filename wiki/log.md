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

## 2026-11-11 · batch-01 修订版（用户首轮评审后打回重写）

- 用户于 2026-11-11 在 Issue #2–#11 各留一条审查意见，结论均为需修改（静态源码核对，基线 364d1d594 未变）；修订意见原文已拉取存档于 tracking/reviews-batch-01/issue-2.md～issue-11.md。
- 三个跨页问题：Provider 凭证同步与 README:128 原则冲突（4 页）、“目标不可达时原子接管”不符合实现（3 页）、交接的屏障/代际去重是设计约束而非已实现调用链（2 页）；另有各页 P2 项（Web 开发脚本缺失、list_core_nodes 返回字段、update check 参数、配对三种操作、syncClockDigest 探针条件、快照校正条件、诊断日志字段、RoutedLink 字段、速览引用补齐等）。
- 修订：10 页并行修订，facts 761 → 876 条（+115），引用机械核验 0 坏引用；Lint 硬失败 0、警告 0；各页 .status.json 保持 review-pending，watcher 水位线已前移到各条审查留言的 comment id。
- 本版重新部署后请用户复审，Issue #2–#11 不变。
