# 修订 brief：agent-chat-branch（Issue #36，batch-04）

- 只改 `review/batch-04/agent-chat-branch.facts.json` 与 `review/batch-04/agent-chat-branch.md`；不改 `.status.json`（`source_commit` 保持 `364d1d594`），不提交、不推送、不建 Issue、不发留言。
- 基线：Operit2 @ `364d1d594`；评审对照上游最新 main `053c6686`（本地已 fetch，`git show 053c6686:<path>` 可读，不要 checkout、不要改仓库）。
- 评审结论：**需修改**。类别：主项是**原有事实偏差**（基线本身就错了），另有 1 项非阻断精确化（顺带修）。评审实质内容全部属实（上一位协调员已逐项核实）。

## 评审原文（全文）

本轮静态审查结论：**需修改**。

审查版本：wiki `66baaf09`；对照上游最新 main `053c6686`，并检查相对条目原基线 `364d1d594` 的变化。

**[P2] deleteMessage 的实际效果被外层委托形式遮住了。** 正文第 81 行和 fact 第 **34** 条称“只向同步层记一条消息删除记录，不直接删行”。外层函数确实委托同步 store，但整个调用会立即删除本地数据。

实际链路是：ChatHistoryManager.rs:1091 → SqlChatSyncStore.rs:381 构造消息与变体的删除项 → 第 **771–772** 行在事务里调用 applyDeletion → 第 **1305** 行起删除 message_parts/messages、第 **1360** 行起删除变体。SqlChatSyncStore.rs:701 的同一事务也在第 719 行写入同步操作。

请改为“委托同步 store，在同一 SQLite 事务中删除本地消息、变体及 parts，并记录同步删除操作”。“外层函数没有直接编写 DELETE SQL”可以作为实现分工说明，不能据此外推为 API 调用仅登记删除。这项在原基线与本轮源码都存在。

另有非阻断精确化：正文第 **106** 行、fact 第 **50** 条的 end-start+1 是请求读取的上限。ChatHistoryManager.rs:1654 使用 LIMIT/OFFSET，历史不足时会返回更少。建议将“返回条数为”改成“读取上限为”。

其他抽查包括变体提升/重编号、草稿及分支提交、消息排序和发送契约的语义快照。

本轮核对正文、同名 `.facts.json` 和固定提交实现，语义结论限于所述重点抽查范围；未运行编译、构建、测试或实机实验。修订时请同步更新正文及对应原子事实，并重核源码引用。

## 核实结论（已重钉行号）

- 主项：基线与上游实测一致。`core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1091` 为 `pub fn deleteMessage(&self, chatId: String, timestamp: i64) -> Chat...`（外层委托同步 store）；`core/crates/persistence/store/src/sync/SqlChatSyncStore.rs:381` 为 `pub fn recordMessageDeletion(`（构造消息与变体的删除项）；同文件 **:701** 为 `let result = self.store.transaction(|transaction| {`（同一事务），:719 写入同步操作，:771–772 在事务里调用 applyDeletion，:1305 起删除 message_parts/messages，:1360 起删除变体。结论：评审属实——整个调用立即删除本地数据，“只记一条删除记录、不直接删行”是错的。
- 非阻断项：`ChatHistoryManager.rs:1654` 为 `let sql = format!("SELECT * FROM messages WHERE chatId = ?1 ORD...`，使用 LIMIT/OFFSET；end-start+1 是请求读取的上限，历史不足时返回更少。结论：评审属实。

## 改法

- 主项（fact #34 + 正文第 81 行，按基线实测修正，ref 指基线行号）：改为“委托同步 store，在同一 SQLite 事务中删除本地消息、变体及 parts，并记录同步删除操作”。“外层函数没有直接编写 DELETE SQL”可保留为实现分工说明，但不得据此外推为 API 调用仅登记删除。ref 按落笔重钉（链路锚点 :1091、:381、:701）。
- 非阻断项（fact #50 + 正文第 106 行，顺带修）：将“返回条数为”改成“读取上限为”（end-start+1 是 LIMIT 读取上限，非返回条数；ref `:1654`）。
- 改前按断言原文逐条再钉一次行号，不要只按编号。

## 验收

- facts 总数预计不变（以落盘为准）；facts 机械核验（文件存在＋行号范围＋反引号符号在 ref 行 ±5 行内）0 坏；正文引用同口径复核 0 坏（**注意**：lint 的引用正则不含 `.rs` 后缀，lint 0/0 不能代替这一步，须自写脚本逐处复核）。
- 跑 `python3 scripts/lint.py --src ~/workspace/Operit2 --dir review/batch-04`，确认全批硬失败 0、警告 0。
- 回报：改了几条、facts 总数、核验结果。
