# 修订 brief：core-node-peer-link（Issue #30，batch-03）

- 只改 `review/batch-03/core-node-peer-link.facts.json` 与 `review/batch-03/core-node-peer-link.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：第 (a) 项是**原有事实偏差**（基线本身就错了），第 (b) 项是**上游后续变化**。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**[P2] 不能把来源桶清理阈值写成无条件生效的硬上限。** 正文第 102 行称“来源桶总数上限 512”，facts 第 **52** 条也将其解释为来源轮换下的内存限制。实际 pairing_throttle.rs:91、第 112 行先为新来源插入桶；任一额度不足时在第 **96–97、115–116** 行直接返回，只有成功消费令牌后才在第 **101、120** 行调用 `prune`。

因此全局桶耗尽后，持续使用新来源进入拒绝分支，来源表仍可增长到 512 以上。请区分“MAX_SOURCE_BUCKETS 常量为 512”和“成功路径执行裁剪”，不要宣称始终存在硬上限。这项要求修正文档保证；本轮不涉及修改运行时。

**另有源码版本变化：**正文第 **149、150** 行及 facts 第 **96、97** 条所述“最新修订 15、7 个 schemaRoots”对旧基线正确，当前 peer-protocol.json:116 已是 version **19**，第 120 行起为 **8** 个 schemaRoots。迁移到本轮源码时请同步更新这些值与版本记录。

其余抽查包括载体探测、消息方向、发现地址认证、路由元数据及反向流宏限制。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

## 核实结论（已重钉行号）

- 第 (a) 项：基线与上游实测一致（文件 `core/crates/node/runtime/src/peer/pairing_throttle.rs`）：**:91** 为 `let sourceBucket = self.sourceConfirmations.entry(source.into()).or_insert_with...`（先为新来源插入桶）；**:101** 为 `prune(&mut self.sourceConfirmations);`（只有成功消费令牌后才调用）。:96–97、:115–116 为额度不足时直接返回；:112、:120 为第二处插入/prune。结论：评审属实——`prune` 只在成功路径执行，拒绝分支不清理，来源表可超 512；“上限 512”是 `MAX_SOURCE_BUCKETS` 常量值，不是无条件硬上限。
- 第 (b) 项：基线实测 `core/peer-protocol.json:100` 为 `"version": 15`，`schemaRoots` 7 个；上游 `053c6686` 同文件 **:116** 为 `"version": 19`，**:120** 起为 8 个 schemaRoots（新增 foundation/vfs）。结论：评审属实。

## 改法

- 第 (a) 项（fact #52 + 正文第 102 行，按基线实测修正，ref 指基线行号）：区分“`MAX_SOURCE_BUCKETS` 常量为 512”与“成功路径执行裁剪”——改写为：新来源先插入桶（`:91`），额度不足直接返回（`:96–97`），只有成功消费令牌后才调 `prune`（`:101`）；全局桶耗尽后持续用新来源进拒绝分支，来源表可增长到 512 以上，不要宣称始终存在硬上限。
- 第 (b) 项（facts #96、#97 + 正文第 149、150 行）：**只加时效标注，不改基线值**，不要改 `.status.json` 的 `source_commit`。措辞示例：“截至基线 `364d1d594`，peer-protocol 最新修订 15、7 个 schemaRoots（`peer-protocol.json:100`）；上游 `053c6686` 已是 version 19（同文件 :116）、8 个 schemaRoots（:120 起，新增 foundation/vfs）。”
- 改前按断言原文逐条再钉一次行号，不要只按编号。

## 验收

- facts 总数预计不变（以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-03`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
