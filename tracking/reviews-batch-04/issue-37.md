本轮静态审查结论：**本轮未发现阻断问题**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

已核对三条不同的压缩路径，正文与对应 facts 对这些等待关系的区分准确：

- 手动 compactChat 取得执行租约、忽略自动阈值并等待摘要结果，见 [ChatServiceCore.rs:1524](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/services/ChatServiceCore.rs#L1524)。
- 自动摘要默认启用，阈值为 0.85；发送前受 SummarySendPolicy 和阈值门控，后台摘要不阻塞当前发送，见 [ModelConfigData.rs:147](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/foundation/model/src/ModelConfigData.rs#L147)、[MessageCoordinationDelegate.rs:806](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs#L806)。
- 执行中超限会发出回调；协调委托等待摘要、复核回合归属，再携带原执行租约续跑同一用户回合，见 [EnhancedAIService.rs:2353](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/provider/services/src/chat/EnhancedAIService.rs#L2353)、[MessageCoordinationDelegate.rs:1117](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs#L1117)。

也核对了三阶段摘要 hook、SUMMARY 功能模型、不携带工具、JS 上下文不含完整历史及结果字段限制，见 [ConversationService.rs:438](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/provider/services/src/chat/enhance/ConversationService.rs#L438)、[ToolPkgSummaryHookBridge.rs:136](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs#L136)。路由续发不预先触发摘要的描述也与当前实现一致。相关上游 VFS 变化没有改变这些已核机制。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

