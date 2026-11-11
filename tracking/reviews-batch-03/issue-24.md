本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**[P2] Windows 保留名检查针对每个路径组件，不只针对整条路径首段。** [正文第 125 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-plugin-theme.md#L125)和 facts 第 **47** 条写“Windows 保留名……作路径首段即拒绝”。实际 [lib.rs:490](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/plugin/theme/src/lib.rs#L490) 遍历 `path.split('/')` 的每个组件，再取该组件第一个点之前的主干检查保留名（第 501–508 行）。

因此 `assets/images/con.png`、`assets/fonts/nul.ttf` 也会被拒绝，虽然路径首段是 `assets`。该检查没有平台条件，在所有 Host 上执行。请改为“任意路径组件的主干命中保留名即拒绝”，同步修正 fact，并补一个资源路径例子。

这是原基线上也存在的事实偏差。另核对了严格解析与 draft 规范化、资源集合相等检查、重复/缺失资源、大小预算及颜色 token，所核部分与实现一致。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

