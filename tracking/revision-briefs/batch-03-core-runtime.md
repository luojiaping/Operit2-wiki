# 修订 brief：core-runtime（Issue #26，batch-03）

- 只改 `review/batch-03/core-runtime.facts.json` 与 `review/batch-03/core-runtime.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：**上游后续变化**（3 项，全部是日志/文件系统边界随 VFS 迁移而变）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**上游已改变启动时的日志失败语义及文件系统边界，需要重核相关事实。**

- 正文第 45 行至第 48 行、facts 第 **17–20** 条仍描述 runtimeRootDir/FileSystemHost 组装日志，并称日志配置失败后“只记警告，继续使用控制台与内存日志”。这些描述对应旧基线。当前 OperitApplication.rs:142 在提供 runtimeStorageHost 时使用 `hostManager.vfs().expect(...)`，且第 **148** 行对 `configure_log_files` 的结果调用 `expect("Runtime VFS log files must be writable")`；配置返回错误会 panic，已不存在该处“警告后继续”的行为。
- 正文第 **56** 行、fact 第 **193** 条的聊天初始化也已从直接要求 FileSystemHost 改为 `hostManager.vfs().expect("Chat runtime requires VFS")`，见 OperitApplication.rs:185。
- 正文第 **145、150** 行及 fact 第 **174** 条的直接图片读取边界也需更新：当前注册入口接收 `Option<&VisualFileSystem>`，经 `fileResource` 与 `FileSource::readBytes` 读取，见 AIMessageManager.rs:883。

上述是源码演进引起的过期，会影响当前 Host 接入和启动失败排查。请重写对应正文/facts并迁移版本记录。另对旧基线和最新基线做了引用路径及行号边界检查：旧基线均可定位；最新版本本页有 6 条引用已超出 OperitApplication.rs 的文件行数，迁移时需一并重新定位。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

## 核实结论（已重钉行号）

- 第 1 项（日志失败语义）：上游 `053c6686` 的 `core/crates/runtime/application/src/core/application/OperitApplication.rs`：**:142** 为 `if let Some(runtimeStorageHost) = hostManager.runtimeStorageHost.clone() {`，**:143** 为 `let filesystem = Arc::new(hostManager.vfs().expect("Runtime VFS must be configured for logging"));`，**:148** 为 `).expect("Runtime VFS log files must be writable");`——配置返回错误会 panic，“警告后继续”已不存在。基线 :142 同为 `if let Some(runtimeStorageHost)...` 开头（基线行为是旧语义，页内基线描述本身对应旧基线）。
- 第 2 项（聊天初始化）：上游同文件 **:185** 为 `let chatFilesystem = Arc::new(hostManager.vfs().expect("Chat runtime requires VFS")...`。评审属实。
- 第 3 项（直接图片读取）：上游 `core/crates/runtime/application/src/core/chat/AIMessageManager.rs:883` 为 `fn registerDirectImageAttachment(`，**:885** 为 `filesystem: Option<&VisualFileSystem>,`，其后经 `fileResource` 与 `FileSource::readBytes` 读取。评审属实。
- 另：评审说的 6 条引用超出新文件行数属实（评审列出的 :1457/:1467/:1483/:1489/:1505/:1511，新文件仅 1450 行）——这些是**上游新文件**的行号问题，不是本页基线引用的问题；本页基线引用仍可定位。

## 改法

- **不要**把整页基线改成新 main，**不要**改 `.status.json` 的 `source_commit`，**不要**按评审字面“迁移版本记录”。三处全部只加时效标注，基线描述保留（它是基线下的真话）：
  1. facts 第 17–20 条与正文第 45–48 行：加注“截至基线 `364d1d594`，日志配置失败后只记警告、继续使用控制台与内存日志；上游 `053c6686` 已改为 `hostManager.vfs().expect(...)`（`OperitApplication.rs:143`）与 `configure_log_files(...).expect("Runtime VFS log files must be writable")`（`:148`），配置失败会 panic。”
  2. fact 第 193 条与正文第 56 行：加注“截至基线，聊天初始化直接要求 FileSystemHost；上游 `053c6686` 已改为 `hostManager.vfs().expect("Chat runtime requires VFS")`（`OperitApplication.rs:185`）。”
  3. fact 第 174 条与正文第 145、150 行：加注“截至基线，直接图片读取走 FileSystemHost 边界；上游 `053c6686` 的注册入口已接收 `Option<&VisualFileSystem>`（`AIMessageManager.rs:885`），经 `fileResource` 与 `FileSource::readBytes` 读取。”
- 加注时重钉行号（上游行号以上面实测为准：:143、:148、:185、:885）；若某条 fact 加注后反引号符号超出其 ref 行 ±5 窗口，符号改 plain 文本，不要为迁就符号而改 ref。
- 评审末段的 6 条超出行数引用与本页基线引用无关，不用改；可在回报里说明。

## 验收

- facts 总数预计不变（以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-03`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
