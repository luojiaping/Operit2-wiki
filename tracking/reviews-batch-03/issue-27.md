本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**最新实现已移除旧的终端目录分流与 Provider dataDir 接口。** 两项在原基线成立，但已不适用于当前 main。

1. [正文第 149 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-runtime-services.md#L149)及 fact 第 **255** 条称 `/app`、`/operitapp`、`/mnt`、`/virtual` 走 VFS，其他路径直接走原生解析。当前 [RuntimeTerminalService.rs:451](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/services/RuntimeTerminalService.rs#L451) 已删除四根路径分支，宿主目录回调统一执行 `context.vfs()` → `resolveResourcePath(None, ...)` → `terminalDirectory`（第 456–463 行）。请同时保留上一层边界：[RuntimeTerminalService.rs:310](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/services/RuntimeTerminalService.rs#L310) 先调用 `TerminalHost::resolveWorkingDirectory` 处理所选终端的命名空间，宿主目录回调才进入上述 VFS 链，避免改写成所有终端路径都直接送 VFS。
2. fact 第 **163** 条描述的 `RuntimeProviderSupport::dataDir` 已删除。当前 [ProviderRuntimeSupportService.rs:575](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs#L575) 的 `modelBindingForFunction`、第 589 行的 `resolvedModelConfig`、第 618 行的 `providerProfile` 不再接收旧 rootDir，改用默认配置管理器。请删除旧事实并重核相邻引用。

另核对了插件配置解析的错误隔离、聊天提交钩子在 Holder 锁外派发和实际收据等待、PTY 目录进入失败时关闭已建会话；这些抽查项与正文一致。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

