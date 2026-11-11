# 修订 brief：core-plugin-sdk（Issue #22，batch-03）

- 只改 `review/batch-03/core-plugin-sdk.facts.json` 与 `review/batch-03/core-plugin-sdk.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：**上游后续变化**（1 项）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**公开构造接口已随上游变化，需要更新文件系统注入说明。** 正文第 12 行、调用链第 220 行和 facts 第 **11** 条仍将第三组输入称为“文件系统宿主”。这在原基线上成立；当前 PackageManager.rs:34 的第三个参数已是 `filesystem: Arc<VisualFileSystem>`，并将同一 VFS 实例传给 `ToolPkgManager`，后者构造参数也已变化（ToolPkgManager.rs:92）。

这是嵌入者实际调用的公开 Rust 接口。请明确列出“执行引擎工厂、资源源、`Arc<VisualFileSystem>`、包状态解析器”，区分 VFS 与平台文件系统 Host，并更新版本记录。直接传入旧 `Arc<dyn FileSystemHost>` 与当前签名不匹配。

其他抽查包括 public_api 相对路径与文件校验、依赖问题码及拓扑顺序、hook 超时分支、main realm 租约和上下文撤销，未发现这些事实与实现冲突。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

## 核实结论（已重钉行号）

- 基线实测（`364d1d594`）：`core/crates/plugin/sdk/src/PackageManager.rs:34` 为 `pub fn new(`，第三个参数在 **:37**：`fileSystemHost: Arc<dyn FileSystemHost>`。基线表述正确，无需改基线事实本身。
- 上游实测（`053c6686`）：同文件 **:37** 已改为 `filesystem: Arc<VisualFileSystem>`；`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs` 在 **:95**（结构字段）与 **:103**（`new()` 参数）均为 `filesystem: Arc<VisualFileSystem>`（评审说的 :92 漂移 3 行，实际字段在 :95）。`use operit_vfs::VisualFileSystem` 在 :6。
- 结论：评审属实。这是上游后续变化，不是基线错误。

## 改法

- **不要**把整页基线改成新 main，**不要**改 `.status.json` 的 `source_commit`。只加时效标注。
- fact 第 11 条与正文第 12 行、调用链第 220 行三处同步加注，措辞示例（按原文落笔时重钉行号）：“截至基线 `364d1d594`，`PluginPackageManager::new` 的第三组输入为 `fileSystemHost: Arc<dyn FileSystemHost>`（`PackageManager.rs:37`）；上游 `053c6686` 已改为 `filesystem: Arc<VisualFileSystem>`（同文件 :37），并将同一 VFS 实例传给 `ToolPkgManager`（`ToolPkgManager.rs:95`、`103`）；直接传入旧 `Arc<dyn FileSystemHost>` 与当前签名不匹配。”同时按评审要求在正文该处明确列出四组输入“执行引擎工厂、资源源、`Arc<VisualFileSystem>`、包状态解析器”，并区分 VFS 与平台文件系统 Host。
- 若三处中某处已是纯基线描述、加注后句意不断裂即可；不要删基线事实。

## 验收

- facts 总数预计不变（以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-03`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
