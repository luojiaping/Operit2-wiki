# 修订 brief：core-rslink（Issue #32，batch-03）

- 只改 `review/batch-03/core-rslink.facts.json` 与 `review/batch-03/core-rslink.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：**原有事实偏差**（基线本身就错了，1 项）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**[P2] 错误分类 helper 不能证明已经发生本地续执行为。** 正文第 63 行及 fact 第 **46** 条写“core_route_error_uses_local_source 返回 true 时，路由打开错误由本地源继续执行”。

实际 lib.rs:349 仅匹配五个错误码并返回 bool，没有执行或重开本地源；在本轮源码内检索也只有该函数定义，没有调用点。lib.rs:328 直接返回 runtime.call 的响应，第 **763–771** 行的 StateFlow 打开路径直接返回错误；带本地源的入口在第 **813** 行显式调用 `watchWithLocalSource`，行为取决于具体运行时实现。

请删除第 63 行和对应 fact 的执行断言，保留第 62 行、fact 第 **45** 条的错误码分类说明。若需解释某个 watch 的本地源行为，应引用实际调用链并限定入口。这项在条目原基线也存在，相关实现从原基线到本轮源码未变。

其余抽查覆盖反向流关闭、StateFlow 首事件错误分支、代理 watch 的 Snapshot 要求、流源池及 codegen 重导出。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

## 核实结论（已重钉行号）

- 基线与上游实测一致（文件 `core/crates/rslink/runtime/src/lib.rs`）：**:349** 为 `pub fn core_route_error_uses_local_source(error: &CoreLinkError) -> bool {`（仅匹配五个错误码返 bool，无执行/重开本地源）；全仓检索只有该函数定义、**无调用点**；**:328** 为 `let response = runtime.call(request).await;`（直接返回响应）；:763–771 的 StateFlow 打开路径直接返回错误；**:813** 为 `let stream = runtime.watchWithLocalSource(request, local_stream).await?;`（带本地源的显式入口，行为取决于具体运行时实现）。
- 结论：评审属实。分类 helper 不能证明已发生本地续执行。

## 改法

- **删除**正文第 63 行的执行断言与 fact 第 46 条（“返回 true 时路由打开错误由本地源继续执行”）。正文若该句与分类说明混在同一行，只删执行断言部分、保留分类说明。
- **保留**正文第 62 行与 fact 第 45 条的错误码分类说明（五个错误码匹配返 bool，ref `:349`）。
- 如需在页内提及 watch 的本地源行为，必须引用实际调用链并限定入口（`watchWithLocalSource`，`:813`），不得再写无条件的续执行断言。
- 删除后重核 facts 序号与相邻引用；facts 总数 -1。

## 验收

- facts 总数预计 88 → 87（删 1 条，以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-03`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
