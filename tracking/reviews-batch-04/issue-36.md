本轮静态审查结论：**需修改**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

**[P2] deleteMessage 的实际效果被外层委托形式遮住了。** [正文第 81 行](https://github.com/luojiaping/Operit2-wiki/blob/66baaf09e0d7d65172a961162d7eaf135c4f30de/review/batch-04/agent-chat-branch.md#L81)和 fact 第 **34** 条称“只向同步层记一条消息删除记录，不直接删行”。外层函数确实委托同步 store，但整个调用会立即删除本地数据。

实际链路是：[ChatHistoryManager.rs:1091](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/persistence/store/src/repository/ChatHistoryManager.rs#L1091) → [SqlChatSyncStore.rs:381](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/persistence/store/src/sync/SqlChatSyncStore.rs#L381) 构造消息与变体的删除项 → 第 **771–772** 行在事务里调用 applyDeletion → 第 **1305** 行起删除 message_parts/messages、第 **1360** 行起删除变体。[SqlChatSyncStore.rs:701](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/persistence/store/src/sync/SqlChatSyncStore.rs#L701) 的同一事务也在第 719 行写入同步操作。

请改为“委托同步 store，在同一 SQLite 事务中删除本地消息、变体及 parts，并记录同步删除操作”。“外层函数没有直接编写 DELETE SQL”可以作为实现分工说明，不能据此外推为 API 调用仅登记删除。这项在原基线与本轮源码都存在。

另有非阻断精确化：正文第 **106** 行、fact 第 **50** 条的 end-start+1 是请求读取的上限。[ChatHistoryManager.rs:1654](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/persistence/store/src/repository/ChatHistoryManager.rs#L1654) 使用 LIMIT/OFFSET，历史不足时会返回更少。建议将“返回条数为”改成“读取上限为”。

其他抽查包括变体提升/重编号、草稿及分支提交、消息排序和发送契约的语义快照。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

