本轮静态审查结论：**需修改**。

审查对象：wiki `cd042091`；按本轮要求对照上游最新 main `053c6686`。条目声明的原源码基线是 `364d1d594`，以下将原有事实偏差与上游后续变化分开说明。

**[P2] 不能把来源桶清理阈值写成无条件生效的硬上限。** [正文第 102 行](https://github.com/luojiaping/Operit2-wiki/blob/cd042091244eb5bc5ab9c035342b0f88bc2f9e3d/review/batch-03/core-node-peer-link.md#L102)称“来源桶总数上限 512”，facts 第 **52** 条也将其解释为来源轮换下的内存限制。实际 [pairing_throttle.rs:91](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/node/runtime/src/peer/pairing_throttle.rs#L91)、第 112 行先为新来源插入桶；任一额度不足时在第 **96–97、115–116** 行直接返回，只有成功消费令牌后才在第 **101、120** 行调用 `prune`。

因此全局桶耗尽后，持续使用新来源进入拒绝分支，来源表仍可增长到 512 以上。请区分“MAX_SOURCE_BUCKETS 常量为 512”和“成功路径执行裁剪”，不要宣称始终存在硬上限。这项要求修正文档保证；本轮不涉及修改运行时。

**另有源码版本变化：**正文第 **149、150** 行及 facts 第 **96、97** 条所述“最新修订 15、7 个 schemaRoots”对旧基线正确，当前 [peer-protocol.json:116](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/peer-protocol.json#L116) 已是 version **19**，第 120 行起为 **8** 个 schemaRoots。迁移到本轮源码时请同步更新这些值与版本记录。

其余抽查包括载体探测、消息方向、发现地址认证、路由元数据及反向流宏限制。

本轮核对了正文、同名 `.facts.json` 与固定版本实现；未运行编译、构建或测试。需要修订的断言请同时更新正文与原子事实；源码版本迁移后请同步重核引用和 `source_commit`。

