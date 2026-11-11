本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**[P2] 错误分类 helper 不能证明已经发生本地续执行为。** [正文第 63 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-rslink.md#L63)及 fact 第 **46** 条写“core_route_error_uses_local_source 返回 true 时，路由打开错误由本地源继续执行”。

实际 [lib.rs:349](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/rslink/runtime/src/lib.rs#L349) 仅匹配五个错误码并返回 bool，没有执行或重开本地源；在本轮源码内检索也只有该函数定义，没有调用点。[lib.rs:328](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/rslink/runtime/src/lib.rs#L328) 直接返回 runtime.call 的响应，第 **763–771** 行的 StateFlow 打开路径直接返回错误；带本地源的入口在第 **813** 行显式调用 `watchWithLocalSource`，行为取决于具体运行时实现。

请删除第 63 行和对应 fact 的执行断言，保留第 62 行、fact 第 **45** 条的错误码分类说明。若需解释某个 watch 的本地源行为，应引用实际调用链并限定入口。这项在条目原基线也存在，相关实现从原基线到本轮源码未变。

其余抽查覆盖反向流关闭、StateFlow 首事件错误分支、代理 watch 的 Snapshot 要求、流源池及 codegen 重导出。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

