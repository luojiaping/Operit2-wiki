# 修订 brief：core-runtime-services（Issue #27，batch-03）

- 只改 `review/batch-03/core-runtime-services.facts.json` 与 `review/batch-03/core-runtime-services.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：**上游后续变化**（2 项）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**最新实现已移除旧的终端目录分流与 Provider dataDir 接口。** 两项在原基线成立，但已不适用于当前 main。

1. 正文第 149 行及 fact 第 **255** 条称 `/app`、`/operitapp`、`/mnt`、`/virtual` 走 VFS，其他路径直接走原生解析。当前 RuntimeTerminalService.rs:451 已删除四根路径分支，宿主目录回调统一执行 `context.vfs()` → `resolveResourcePath(None, ...)` → `terminalDirectory`（第 456–463 行）。请同时保留上一层边界：RuntimeTerminalService.rs:310 先调用 `TerminalHost::resolveWorkingDirectory` 处理所选终端的命名空间，宿主目录回调才进入上述 VFS 链，避免改写成所有终端路径都直接送 VFS。
2. fact 第 **163** 条描述的 `RuntimeProviderSupport::dataDir` 已删除。当前 ProviderRuntimeSupportService.rs:575 的 `modelBindingForFunction`、第 589 行的 `resolvedModelConfig`、第 618 行的 `providerProfile` 不再接收旧 rootDir，改用默认配置管理器。请删除旧事实并重核相邻引用。

另核对了插件配置解析的错误隔离、聊天提交钩子在 Holder 锁外派发和实际收据等待、PTY 目录进入失败时关闭已建会话；这些抽查项与正文一致。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

## 核实结论（已重钉行号）

- 第 1 项（终端目录分流）：基线实测 `core/crates/runtime/application/src/services/RuntimeTerminalService.rs:457` 为 `if ["/app", "/operitapp", "/mnt", "/virtual"].iter().any(|root| {`——基线描述为真。上游 `053c6686`：**:451** 为 `fn resolve_terminal_working_dir(`，**:456** 为 `let filesystem = terminal_vfs(context)?;`（统一 VFS 链），四根路径分支已删；**:310–312** 为 `let resolvedWorkingDir = self.terminalHost.resolveWorkingDirectory(...)`（上一层边界仍在，宿主目录回调才进 VFS 链）。
- 第 2 项（dataDir）：基线实测 `core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:496` 为 `fn dataDir(&self) -> Result<PathBuf, String> {`，调用点 :253 与 `ChatHistoryDelegate.rs:1490` 的 `support.dataDir()?`——基线描述为真。上游 `053c6686`：同文件 `dataDir` **0 命中**（已删）；**:575** 为 `fn modelBindingForFunction(`、**:589** 为 `fn resolvedModelConfig(`、**:618** 为 `fn providerProfile(`，均不再接收旧 rootDir，改用默认配置管理器。

## 改法

- 第 1 项（fact #255 + 正文第 149 行）：**只加时效标注，不删除**——基线描述在基线下为真。措辞示例：“截至基线 `364d1d594`，`/app`、`/operitapp`、`/mnt`、`/virtual` 走 VFS，其他路径直接走原生解析（`RuntimeTerminalService.rs:457`）；上游 `053c6686` 已删除四根路径分支，宿主目录回调统一走 VFS 链（`resolve_terminal_working_dir`，同文件 :451–463）；上一层仍先由 `TerminalHost::resolveWorkingDirectory` 处理所选终端的命名空间（`:310`），不是所有终端路径都直接送 VFS。”落笔时重钉行号。
- 第 2 项（fact #163）：**按评审删除该条事实**（评审原话“请删除旧事实”）。⚠️ **特别标注：该事实在基线 `364d1d594` 下为真（`dataDir` 定义在 `ProviderRuntimeSupportService.rs:496`），本次删除是依用户评审意见执行、不是因为基线错了。**正文中与 `dataDir` 相关的句子同步删除或改写为“上游 `053c6686` 已删除该接口，三函数改用默认配置管理器”；删除后重核相邻引用的行号与 facts 序号，facts 总数 -1。**删除完成后，在给协调员的回报里单独确认这一项，并写明“基线为真、依评审删除”。**
- **不要**改 `.status.json` 的 `source_commit`，不要把整页基线改成新 main。

## 验收

- facts 总数预计 255 → 254（删 1 条，以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-03`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果，并单独确认 dataDir 删除项。
