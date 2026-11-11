本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**上游已改变启动时的日志失败语义及文件系统边界，需要重核相关事实。**

- [正文第 45 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-runtime.md#L45)至第 48 行、facts 第 **17–20** 条仍描述 runtimeRootDir/FileSystemHost 组装日志，并称日志配置失败后“只记警告，继续使用控制台与内存日志”。这些描述对应旧基线。当前 [OperitApplication.rs:142](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/core/application/OperitApplication.rs#L142) 在提供 runtimeStorageHost 时使用 `hostManager.vfs().expect(...)`，且第 **148** 行对 `configure_log_files` 的结果调用 `expect("Runtime VFS log files must be writable")`；配置返回错误会 panic，已不存在该处“警告后继续”的行为。
- 正文第 **56** 行、fact 第 **193** 条的聊天初始化也已从直接要求 FileSystemHost 改为 `hostManager.vfs().expect("Chat runtime requires VFS")`，见 [OperitApplication.rs:185](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/core/application/OperitApplication.rs#L185)。
- 正文第 **145、150** 行及 fact 第 **174** 条的直接图片读取边界也需更新：当前注册入口接收 `Option<&VisualFileSystem>`，经 `fileResource` 与 `FileSource::readBytes` 读取，见 [AIMessageManager.rs:883](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/core/chat/AIMessageManager.rs#L883)。

上述是源码演进引起的过期，会影响当前 Host 接入和启动失败排查。请重写对应正文/facts并迁移版本记录。另对旧基线和最新基线做了引用路径及行号边界检查：旧基线均可定位；最新版本本页有 6 条引用已超出 OperitApplication.rs 的文件行数，迁移时需一并重新定位。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

