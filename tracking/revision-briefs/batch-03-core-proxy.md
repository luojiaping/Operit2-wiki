# 修订 brief：core-proxy（Issue #31，batch-03）

- 只改 `review/batch-03/core-proxy.facts.json` 与 `review/batch-03/core-proxy.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：第 1 项是**原有事实偏差**（基线本身就错了），第 2 项是**上游后续变化**，另有 1 项非阻断措辞建议（顺带修）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

1. **[P2] 任务调度器缺失的错误发生在执行命令时，文档误写成安装时。** 正文第 142 行及 fact 第 **43** 条写“core 命令执行器安装报错”。lib.rs:170 在安装时创建闭包；调度器检查位于这个闭包内部的第 **180–187** 行，只有调用已安装执行器时才发生。安装本身在第 **213–215** 行写入执行器并返回运行时，不检查调度器。请改为“未预设执行器时安装闭包；实际执行 Core 命令时要求 Host 调度器”。这项在原基线也存在，影响对精简 Host 启动条件的判断。
2. **上游接口变化：**正文第 152 行和 fact 第 **53** 条仍描述 `fileSystemHost()`。最新 lib.rs:283 已改成 `filesystem() -> Arc<VisualFileSystem>`，调用 `hostManager.vfs().expect("LocalCoreProxy requires VFS")`。请更新方法名、返回能力和依赖说明。

另有一项非阻断措辞建议：正文第 80 行/fact 第 **92** 条的“只收录对象方法可达类型”应与下一条的额外收录规则合并，避免单条机器事实产生绝对结论；lib.rs:78 紧接着调用 `include_source_tree_model_types`。

已核对显式根扫描、对象地址生成、流池收养、应用自有请求桥及 Dart 编解码的主要分支。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

## 核实结论（已重钉行号）

- 第 1 项：基线与上游实测一致（文件 `core/crates/proxy/local/src/lib.rs`）：**:170** 为 `Some(Arc::new_cyclic(`（安装时创建闭包）；**:180** 为 `let scheduler = runtime...`（调度器检查在闭包内部 :180–187）；**:213** 为 `application.hostManager.coreCommandExecutor = Some(executor.clone());`（安装本身写入执行器并返回运行时，不检查调度器）。结论：评审属实——调度器缺失的错误只在调用已安装执行器时发生，不是安装时。
- 第 2 项：基线实测同文件 **:283** 为 `pub fn fileSystemHost(&self) -> Arc<dyn FileSystemHost> {`；上游 `053c6686` 同文件 **:283** 已改为 `pub fn filesystem(&self) -> Arc<operit_vfs::VisualFileSystem::VisualFileSystem> {`，其内调 `hostManager.vfs().expect("LocalCoreProxy requires VFS")`。结论：评审属实。
- 非阻断项：`core/crates/proxy/dart-codegen/src/lib.rs`：**:78** 为 `let mut reachable = reachable_serializable_types(objects, serializable_types);`，紧接的 **:79** 为 `include_source_tree_model_types(&mut reachable, serializable_types);`（评审说的 :78 漂移 1 行，实际调用在 :79；基线与上游同行）。

## 改法

- 第 1 项（fact #43 + 正文第 142 行，按基线实测修正，ref 指基线行号）：改为“未预设执行器时安装闭包；实际执行 Core 命令时要求 Host 调度器”——安装时创建闭包（`:170`），调度器检查在闭包内（`:180–187`），安装本身只写执行器并返回运行时、不检查调度器（`:213–215`）。
- 第 2 项（fact #53 + 正文第 152 行）：**只加时效标注，不改基线值**，不要改 `.status.json` 的 `source_commit`。措辞示例：“截至基线 `364d1d594`，该方法为 `fileSystemHost() -> Arc<dyn FileSystemHost>`（`lib.rs:283`）；上游 `053c6686` 已改成 `filesystem() -> Arc<VisualFileSystem>`（同文件 :283），调用 `hostManager.vfs().expect("LocalCoreProxy requires VFS")`。”
- 非阻断项（fact #92 + 正文第 80 行，顺带修）：把“只收录对象方法可达类型”与下一条的额外收录规则合并，避免单条事实产生绝对结论；`include_source_tree_model_types` 调用在 `dart-codegen/src/lib.rs:79`（注意评审说的 :78 漂移 1 行）。
- 改前按断言原文逐条再钉一次行号，不要只按编号。

## 验收

- facts 总数预计不变或 -1（若第 92 条与下一条合并成一条，以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-03`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
