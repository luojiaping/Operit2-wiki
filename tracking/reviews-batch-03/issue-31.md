本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

1. **[P2] 任务调度器缺失的错误发生在执行命令时，文档误写成安装时。** [正文第 142 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-proxy.md#L142)及 fact 第 **43** 条写“core 命令执行器安装报错”。[lib.rs:170](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/proxy/local/src/lib.rs#L170) 在安装时创建闭包；调度器检查位于这个闭包内部的第 **180–187** 行，只有调用已安装执行器时才发生。安装本身在第 **213–215** 行写入执行器并返回运行时，不检查调度器。请改为“未预设执行器时安装闭包；实际执行 Core 命令时要求 Host 调度器”。这项在原基线也存在，影响对精简 Host 启动条件的判断。
2. **上游接口变化：**[正文第 152 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-proxy.md#L152)和 fact 第 **53** 条仍描述 `fileSystemHost()`。最新 [lib.rs:283](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/proxy/local/src/lib.rs#L283) 已改成 `filesystem() -> Arc<VisualFileSystem>`，调用 `hostManager.vfs().expect("LocalCoreProxy requires VFS")`。请更新方法名、返回能力和依赖说明。

另有一项非阻断措辞建议：正文第 80 行/fact 第 **92** 条的“只收录对象方法可达类型”应与下一条的额外收录规则合并，避免单条机器事实产生绝对结论；[lib.rs:78](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/proxy/dart-codegen/src/lib.rs#L78) 紧接着调用 `include_source_tree_model_types`。

已核对显式根扫描、对象地址生成、流池收养、应用自有请求桥及 Dart 编解码的主要分支。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

