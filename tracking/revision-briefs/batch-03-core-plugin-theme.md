# 修订 brief：core-plugin-theme（Issue #24，batch-03）

- 只改 `review/batch-03/core-plugin-theme.facts.json` 与 `review/batch-03/core-plugin-theme.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：**原有事实偏差**（基线本身就错了，1 项）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**[P2] Windows 保留名检查针对每个路径组件，不只针对整条路径首段。** 正文第 125 行和 facts 第 **47** 条写“Windows 保留名……作路径首段即拒绝”。实际 lib.rs:490 遍历 `path.split('/')` 的每个组件，再取该组件第一个点之前的主干检查保留名（第 501–508 行）。

因此 `assets/images/con.png`、`assets/fonts/nul.ttf` 也会被拒绝，虽然路径首段是 `assets`。该检查没有平台条件，在所有 Host 上执行。请改为“任意路径组件的主干命中保留名即拒绝”，同步修正 fact，并补一个资源路径例子。

这是原基线上也存在的事实偏差。另核对了严格解析与 draft 规范化、资源集合相等检查、重复/缺失资源、大小预算及颜色 token，所核部分与实现一致。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

## 核实结论（已重钉行号）

- 基线与上游实测一致：`core/crates/plugin/theme/src/lib.rs:490` 为 `for part in path.split('/') {`；**:501** 为 `let stem = part.split('.').next().unwrap();`（取组件第一个点之前的主干），检查逻辑在 :501–508。基线与 `053c6686` 同行。
- 结论：评审属实。原表述“作路径首段即拒绝”是错的；检查针对每个路径组件、无平台条件。

## 改法

- fact 第 47 条与正文第 125 行同步改为“任意路径组件的主干命中保留名即拒绝”，并补一个资源路径例子（`assets/images/con.png`、`assets/fonts/nul.ttf` 均被拒绝，虽然路径首段是 `assets`），同时写明该检查没有平台条件、在所有 Host 上执行。
- ref 保持 `lib.rs:490`（或按落笔重钉为 :490/:501，须在 ±5 窗口内含 `split` 与 `stem` 符号）；改前按断言原文逐条再钉一次行号，不要只按编号。

## 验收

- facts 总数预计不变（以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-03`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
