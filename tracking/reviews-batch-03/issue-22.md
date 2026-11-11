本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**公开构造接口已随上游变化，需要更新文件系统注入说明。** [正文第 12 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-plugin-sdk.md#L12)、调用链第 220 行和 facts 第 **11** 条仍将第三组输入称为“文件系统宿主”。这在原基线上成立；当前 [PackageManager.rs:34](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/plugin/sdk/src/PackageManager.rs#L34) 的第三个参数已是 `filesystem: Arc<VisualFileSystem>`，并将同一 VFS 实例传给 `ToolPkgManager`，后者构造参数也已变化（[ToolPkgManager.rs:92](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs#L92)）。

这是嵌入者实际调用的公开 Rust 接口。请明确列出“执行引擎工厂、资源源、`Arc<VisualFileSystem>`、包状态解析器”，区分 VFS 与平台文件系统 Host，并更新版本记录。直接传入旧 `Arc<dyn FileSystemHost>` 与当前签名不匹配。

其他抽查包括 public_api 相对路径与文件校验、依赖问题码及拓扑顺序、hook 超时分支、main realm 租约和上下文撤销，未发现这些事实与实现冲突。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

