---
title: 会话与分支
module: agent
platforms: [all]
sources: [core/crates/persistence/store/src/repository/ChatHistoryManager.rs, docs/chat-send-api.md]
date: 2026-11-11
---

## 概述

- `ChatHistoryManager` 是会话、消息、变体、分支与同步记录的仓库（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:208）。
- 消息主行存 `messages` 表，按 `timestamp` 排序；全量读出入口已删，历史改为按需加载：`loadChatMessagesAscAfter` 自时间戳后升序取，`loadOlderChatMessages` 向前分页取（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1790）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1802）。
- 变体修订存 `message_variants` 表（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:144）。
- 各修订的 part 行存 `message_parts` 表（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:166）。
- 插件发送消息的契约入口只有 `sendMessage`、`sendMessageStreaming`、`cancel` 三个方法（docs/chat-send-api.md:8）。
- 摘要消息由 `addSummaryMessageBetweenSliceNeighbors` 插入两条相邻消息之间（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:971）。
- 同步记录的落盘细节见 [[core-persistence-sync|持久化——同步存储]]，store 聚合结构见 [[core-persistence-store|持久化——store 聚合 crate]]。

## AI 速览

- `ChatHistoryManager` — 会话、消息、变体、分支与同步记录的仓库（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:208）。
- `getInstance` — 返回共享单例（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:242）。
- `hydrateMessages` — 按选中变体序号拼装消息（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:316）。
- `persistMessageLocked` — 原子写消息、修订 part、会话排序与同步状态（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:827）。
- `deleteMessageVariantRevision` — 按 Kotlin 提升与相邻选择规则原子删变体修订（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:95）。
- `addMessageVariant` — 为 AI 消息新增变体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1180）。
- `selectMessageVariant` — 切换选中变体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1214）。
- `commitAssistantMessageSegment` — 原子提交一段助手消息（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1117）。
- `newChatDraft` — 建未持久化会话草稿（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1354）。
- `commitChatDraft` — 提交草稿，或按 source 提交为源会话分支（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1377）。
- `getBranches` — 按 parentChatId 取分支会话（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1666）。
- `deleteChatHistory` — 删除整段会话（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1338）。
- `Tools.Chat.sendMessage` — 插件发送消息的入口（docs/chat-send-api.md:8）。
- `Tools.Chat.sendMessageStreaming` — 流式发送消息的入口（docs/chat-send-api.md:9）。
- `Tools.Chat.cancel` — 取消发送的入口（docs/chat-send-api.md:10）。
- `steerMessage` — Flutter 端引导当前会话的内部 Core 路由（docs/chat-send-api.md:90）。
- 主入口（持久化）：`getInstance`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:242）。
- 主入口（发送）：`sendMessage`（docs/chat-send-api.md:8）。
- 数据流向（发送）：提交经一次准入进入 `startUserMessage` 管线，原生执行持有租约并负责持久化收据（docs/chat-send-api.md:67）。
- 数据流向（持久化）：`persistMessageLocked` 写消息与 part 行，同步层记快照（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:827）。

## 核心机制

**存储模型**

- 每条消息的 `variantCount` 等于变体行数加 1，基础修订计为第 1 个变体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:362）。
- `selectedVariantIndex` 为 0 时消息用基础 parts 拼装（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:364）。
- 选中变体序号非 0 时经选中变体的 `applyTo` 把变体字段与变体 parts 合成消息（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:387）。
- 消息缺少基础 parts 时加载报 IllegalState，错误文本含 `Missing base parts for message`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:354）。
- 当前会话 id 存在偏好键 `current_chat_id`，由 `CURRENT_CHAT_ID` 返回（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:228）。

**变体删除**

- 删除变体修订只接受 AI 消息，非 AI 消息返回 `Only AI messages can delete variants`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:103）。
- 删除变体时 variantIndex 为 0 表示删除第一个变体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:112）。
- 删除变体后 `selectedVariantIndex` 重算：删 0 号变体后选 0，删中间变体后选被删序号（由后位递补），删末位变体后选前一位（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:125）。
- 删除 0 号变体时把被提升变体的 `roleName`、`provider`、`modelName` 与 token 计数写回 `messages` 主行（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:148）。
- 删除 0 号变体时先删旧基础 parts，再把被提升变体的 parts 重编号为 0（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:166）。
- 删除变体后，后位变体按升序逐个减 1 重编号，`message_variants` 与 `message_parts` 同步改（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:189）。

**消息写入**

- 变体序号为负时写入拒绝，错误为 `Variant index must be nonnegative`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:834）。
- 写变体修订（variantIndex 大于 0）时先查 `message_variants`，不存在则报错（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:848）。
- 写变体修订时把 `messages` 行的 `selectedVariantIndex` 同步改成该变体序号（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:856）。
- 新用户消息把会话顶到列表最前：`displayOrder` 取 -updatedAt 与全库最小值减 1 的较小者（通常为 -updatedAt）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:873）。
- 新建的非用户消息只更新会话的 `updatedAt`，不改 `displayOrder`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:877）。
- 已完成的 AI 消息写入时只更新会话的 `updatedAt`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:877）。
- 持久化消息时给 Markdown 与 Thinking part 补 `file_base_path` 与 `file_node_id` 属性（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:820）。

**变体新增与选择**

- 只有 AI 消息能新增变体，否则返回 `Only AI messages can have regenerated variants`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1193）。
- 新变体序号取 `message_variants` 表内计数加 1（`COUNT(*) + 1`）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1196）。
- 新增变体后 `messages` 行的 `selectedVariantIndex` 立即指向新变体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1205）。
- 选中非 0 变体时先查 `message_variants`，不存在则报错（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1228）。
- 选中变体序号为负时报错 `Variant index must be nonnegative`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1222）。

**消息删除**

- `deleteMessage` 本身未直接编写 DELETE SQL，而是委托同步 store（`recordMessageDeletion`），在同一 SQLite 事务中删除本地消息、变体及 parts，并记录同步删除操作（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1077）（core/crates/persistence/store/src/sync/SqlChatSyncStore.rs:405）。
- `deleteMessagesFrom` 删除从指定时间戳起的全部消息（`recordMessagesFromDeletion`）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1245）。
- `clearChatMessages` 删除会话内全部消息与变体（`recordAllMessagesForChatDeletion`）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1255）。

**助手段提交**

- `commitAssistantMessageSegment` 原子提交一段助手消息、用量增量、可选上下文窗口与同步状态（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1117）。
- 助手段要求 sender 为 ai，否则返回 `assistant segment requires an ai message`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1125）。
- 助手段要求基于 base revision，即 `selectedVariantIndex` 为 0（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1128）。
- 助手段要求占位消息已存在，否则报 IllegalState（`Assistant placeholder` 不存在）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1138）。

**摘要消息插入**

- 任一相邻消息的 sender 为 `summary` 时不插入摘要，返回 None（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1008）。
- 摘要消息时间戳取 `actualBeforeTimestamp` 与 `actualAfterTimestamp` 的中点（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:950）。
- 两条相邻消息时间戳相差不超过 1 时无法插入摘要，返回 None（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:945）。
- 只有前邻居时摘要时间戳为前邻居时间戳加 1（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:957）。
- 只有后邻居时摘要时间戳为后邻居时间戳减 1（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:963）。
- 摘要消息的生成与压缩见 [[agent-compaction|上下文压缩与摘要]]（前向引用，本批待写）。

**消息读取**

- `loadChatMessagesRange` 要求 0 <= start <= end，否则报 `range requires 0 <= start <= end`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1612）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1621）。
- loadChatMessagesRange 读取上限为 end - start + 1（`checked_sub` 后 `checked_add(1)`，由 `LIMIT` 执行，历史不足时返回更少）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1626）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1641）。
- loadRuntimeChatMessages 从最新一条 `summary` 消息起（含该摘要）加载消息，供模型上下文（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1736）。
- `hasUserMessageAfter` 不加载会话消息即查指定时间戳后是否有更新的用户回合（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1724）。
- `loadRuntimeChatMessagesUpTo` 从一条历史消息起加载模型上下文，含该时间点前的最新摘要（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1746）。
- `loadChatMessageDepths` 只计数指定时间戳后已持久化的消息数，不水合预览、part 或变体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1767）。
- `loadChatMessageIndexPosition` 不读消息体即解析一条已持久化消息的精确位置（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1785）。
- loadMessagesAfterLatestSummaryInRange 只取最新摘要之后的消息，不含摘要本身（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1692）。
- `getLatestSummaryTimestamp` 返回一个会话里最新摘要消息的时间戳（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1684）。
- `searchChatIdsByContent` 的空查询返回空集（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1646）。
- 消息定位预览截断长度 `LOCATOR_PREVIEW_CHAR_COUNT` 为 48 字符（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:37）。
- `loadChatMessageLocatorPreviews` 读全局消息索引返回有界预览，不水合消息体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1774）。

**分支**

- `getBranches` 按 `parentChatId` 取一个父会话的分支会话列表（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1666）。
- `getBranchesFlow` 与 `getBranches` 返回相同结果（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1676）。
- `promoteChatToRoot` 把会话从父会话脱离为根会话（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:795）。
- `ensureOutputDirectory` 沿父会话链上溯找输出目录（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:497）。
- 父会话链成环时 ensureOutputDirectory 报 IllegalState，错误含 `Cyclic parent conversations`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:503）。
- 会话绑定了 workspace 时 `fileDirectoryForChat` 返回 workspace 主目录，否则走输出目录（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:517）。
- `newChatDraft` 接受 title、插件扩展、workspaceId 与 `parentChatId`，建一个未持久化的会话草稿（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1348）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1354）。
- 建草稿前插件扩展须通过 `validatePluginExtensions` 校验（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1361）。
- 建草稿时指定的 workspace 不存在则报错 `Workspace does not exist`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1365）。
- `commitChatDraft` 把草稿与初始消息提交入库，或按 `source` 提交为源会话的分支（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1377）。
- 提交草稿时输出目录从 `parentChatId` 或 source 指定的父会话继承（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1383）。
- `saveChatHistory` 保存会话后记一次同步快照（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:612）。
- 新会话保存后创建本地 `Binding`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:618）。
- `ensureRoutedChat` 先校验 Binding 已存在（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1396）。
- 路由会话缺失时以 `Edge Chat` 为标题创建（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1401）。

**整段删除**

- `deleteChatHistory` 删除整段会话，返回是否成功（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1338）。
- 删除会话前先冻结全部子会话的输出目录绑定（子会话从父行继承目录）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1339）。
- 同步层 `deleteChat` 返回 false 时整个删除返回 false，不再删 Binding（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1343）。
- 删除成功后删 Binding；若被删会话是当前会话，清除当前会话 id（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1348）。
- `canDeleteChatHistory`：已锁定会话返回 false；不存在的会话返回同步层记录的删除状态（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1330）。
- `chatIsDeleted` 通过同步层索引的生命周期键查一个会话的已提交删除事实（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1325）。

**导入导出与当前会话**

- `exportChatHistoriesToJson` 把全部会话与消息导出为 Operit 归档 JSON（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:625）。
- 导入归档时 `archiveType` 不符拒绝，错误含 `invalid archiveType`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:686）。
- 导入归档时 `formatVersion` 不符拒绝，错误含 `unsupported formatVersion`（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:692）。
- 导入时已存在 id 的会话计为 updated，新 id 计为 new（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:717）。
- `setCurrentChatId` 把当前会话 id 写入偏好存储（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1304）。
- `clearCurrentChatId` 从偏好存储移除当前会话 id（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1312）。
- `getTotalChatCount` 与 `getTotalMessageCount` 分别计数会话总数与消息总数（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:542）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:547）。
- `getMessageCountsByChatId` 按会话分组计数消息（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:552）。
- `updateChatLocked` 改锁定态后记同步元数据（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:779）。
- `updateChatPinned` 改置顶态后记同步元数据（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:787）。
- `renameRoleNameInMessages` 批量改名消息行里的 roleName（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1867）。
- `updateMessage` 经 `persistMessageLocked` 更新消息内容与选中变体元数据（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1113）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1107）。
- `setMessageFavorite` 只在收藏态变化时才写库并记快照（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1162）。

**发送契约（chat-send-api）**

- 插件 SDK 的发送与取消入口只有 `sendMessage`、`sendMessageStreaming`、`cancel` 三个方法（docs/chat-send-api.md:8）。
- `startTurn`、`waitTurn`、`cancelTurn`、`finishSequence` 与回调式流不在当前作者契约内（docs/chat-send-api.md:14）。
- 发送契约的 Rust 权威实现在 `core/crates/plugin/sdk/src/js_sdk/chat.rs`，TypeScript 导出在 `plugins/types/chat.d.ts`（docs/chat-send-api.md:18）。
- `kind: "submit"` 保留原文、全部附件与显式可空的回复目标（docs/chat-send-api.md:39）。
- submit 的 `turn` 在执行与仅做真实用户持久化之间二选一（docs/chat-send-api.md:40）。
- `kind: "continue"` 指向已提交的用户时间戳与显式参与者，不能重发文本、附件或回复目标（docs/chat-send-api.md:57）。
- 每次 continue 必须带 `summaryPolicy`，取值为 `"defer"` 或 `"after_reply"`（docs/chat-send-api.md:60）。
- 两种 summaryPolicy 都抑制回复前与回复中的自动摘要（docs/chat-send-api.md:61）。
- submit 与 continue 共用一次准入与既有 `startUserMessage` 管线（docs/chat-send-api.md:67）。
- 被接受的发送不依赖插件代码事后调用单独的 finish 方法（docs/chat-send-api.md:69）。
- send_message 工具接受 `hide_user_message: true`，Core 以 `HIDDEN_PLACEHOLDER` 记录用户消息，原 parts 仍保留在持久化历史与模型上下文中，仅改变转录呈现（docs/chat-send-api.md:74）。
- Flutter 端「引导当前会话」走内部 `steerMessage(chatId, messageText)` Core 路由（docs/chat-send-api.md:90）。
- Flutter 端「打断并发送」是唯一把 `cancelMessage` 与一次新普通发送组合起来的 composer 动作（docs/chat-send-api.md:91）。
- 引导不是第二次普通发送，不再拿执行租约；活动回合共享一个 FIFO 收件箱（docs/chat-send-api.md:95）。
- 最终收件箱为空时原子关闭，之后的引导请求会报错而不是挂住（docs/chat-send-api.md:111）。
- `part` 事件是该消息完整有序 part 列表的原子替换，不是文本增量（docs/chat-send-api.md:150）。
- 每次发送的快照内容与元数据计费上限为 8 MiB，超限显式拒绝观察（docs/chat-send-api.md:163）。
- JavaScript 迭代器上同时只能有一个待处理的 `next()`（docs/chat-send-api.md:166）。
- `cancel(chatId)` 先捕获调用引擎的已启用已认证包及其在该会话的精确活动执行（docs/chat-send-api.md:184）。
- 排队的请求不能取消其他包或更新的执行（docs/chat-send-api.md:186）。
- `NativeGroupTurnTransport` 只用 `sendMessage` 与 `cancel`（docs/chat-send-api.md:193）。
- 群组原始用户输入先以 `record_only` 持久化一次，再调用响应规划器（docs/chat-send-api.md:199）。
- 群组中间回复用 `summaryPolicy: "defer"`，最后一条规划回复用 `"after_reply"`，只有它可触发完成通知（docs/chat-send-api.md:201）。
- 续发完成不重复递增原始用户提交计数（docs/chat-send-api.md:205）。
- 对话级上下文刷新取各绑定参与者估计值中的最大值作为存储窗口（docs/chat-send-api.md:244）。
- 配置执行结果要求完整的 `historyPolicy` 对象，含 `isolateParticipants` 与 `labelUserMessages`；普通模型对话两者都为 false（docs/chat-send-api.md:263）。
- 其他参与者的有序 Markdown 发言以前缀 `[From role: name]` 作为用户参考上下文（docs/chat-send-api.md:271）。
- 群组用户输入加前缀 `[From user]`（docs/chat-send-api.md:273）。
- 发送契约的可重复校验入口包括 `chat-send-contracts.test.mjs` 的 node 测试（docs/chat-send-api.md:225）。

## 关键符号

- `ChatHistoryManager` — 会话、消息、变体、分支与同步记录的仓库（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:208）。
- `ChatHistoryManagerError` — 持久化与导入导出操作的错误面（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:76）。
- `ChatHistoryManagerResult` — 仓库操作的 Result 别名（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:92）。
- `getInstance` — 返回共享单例（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:242）。
- `CURRENT_CHAT_ID` — 当前会话 id 的偏好键（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:228）。
- `hydrateMessages` — 按选中变体序号拼装消息（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:316）。
- `loadMessagesSnapshot` — 在一次一致的 SQLite 快照上执行查询（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:394）。
- `persistMessageLocked` — 原子写消息、修订 part、会话排序与同步状态（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:827）。
- `deleteMessageVariantRevision` — 原子删变体修订（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:95）。
- `addMessageVariant` — 为 AI 消息新增变体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1180）。
- `selectMessageVariant` — 切换选中变体（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1214）。
- `commitAssistantMessageSegment` — 原子提交一段助手消息（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1117）。
- `addSummaryMessageBetweenSliceNeighbors` — 在相邻消息间插入摘要（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:971）。
- `resolveAnchoredMessageLocked` — 解析锚定消息时间戳（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:885）。
- `newChatDraft` — 建未持久化会话草稿（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1354）。
- `commitChatDraft` — 提交草稿或源会话分支（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1377）。
- `getBranches` — 按 parentChatId 取分支会话（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1666）。
- `deleteChatHistory` — 删除整段会话（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1338）。
- `canDeleteChatHistory` — 查会话是否允许删除（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1330）。
- `setCurrentChatId` — 把当前会话 id 写入偏好存储（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1304）。
- `clearCurrentChatId` — 从偏好存储移除当前会话 id（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1312）。
- `loadRuntimeChatMessages` — 从最新摘要起加载模型上下文消息（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1729）。
- `hasUserMessageAfter` — 不加载会话消息即查指定时间戳后是否有更新的用户回合（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1724）。
- `loadRuntimeChatMessagesUpTo` — 从一条历史消息起加载模型上下文，含该时间点前的最新摘要（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1746）。
- `loadChatMessageDepths` — 只计数指定时间戳后已持久化的消息数（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1767）。
- `loadChatMessageIndexPosition` — 不读消息体即解析一条消息的精确位置（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1785）。
- `Tools.Chat.sendMessage` — 插件发送消息的入口（docs/chat-send-api.md:8）。
- `Tools.Chat.sendMessageStreaming` — 流式发送消息的入口（docs/chat-send-api.md:9）。
- `Tools.Chat.cancel` — 取消发送的入口（docs/chat-send-api.md:10）。
- `steerMessage` — Flutter 端引导当前会话的内部 Core 路由（docs/chat-send-api.md:90）。
- `NativeGroupTurnTransport` — 群组回合传输，只用 sendMessage 与 cancel（docs/chat-send-api.md:193）。

## 调用链

1. 插件调用 `Tools.Chat.sendMessage` 提交发送请求（docs/chat-send-api.md:8）。
2. submit 与 continue 共用一次准入，进入既有 `startUserMessage` 管线（docs/chat-send-api.md:67）。
3. 原生执行持有规范租约（`canonical lease`），负责输入钩子分发、持久化收据、完成发布与租约释放（docs/chat-send-api.md:68）。
4. 用户消息经 `persistMessageLocked` 写入消息行与 part 行（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:827）。
5. 新用户消息把会话的 `displayOrder` 取 -updatedAt 与全库最小值减 1 的较小者（通常为 -updatedAt），顶到列表最前（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:873）。
6. 助手回复分段经 `commitAssistantMessageSegment` 原子提交（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1117）。
7. 流式观察者收 `part` 事件：每次都是完整有序 part 列表的原子替换（docs/chat-send-api.md:150）。
8. 完成时收 `completed` 事件，携带实际定稿收据（docs/chat-send-api.md:172）。
9. 分支创建：`newChatDraft` 带 `parentChatId` 建草稿（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1348）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1354）。
10. `commitChatDraft` 按 `source` 提交为源会话分支，并从父会话继承输出目录（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1383）。
11. 读分支：`getBranches` 按 `parentChatId` 取分支会话列表（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1666）。
12. 整段删除：`deleteChatHistory` 先冻结子会话输出目录绑定（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1339）。
13. 若被删会话是当前会话，清除当前会话 id（`clearCurrentChatId`）（core/crates/persistence/store/src/repository/ChatHistoryManager.rs:1348）。

## 来源

- core/crates/persistence/store/src/repository/ChatHistoryManager.rs（1945 行，全读）
- docs/chat-send-api.md（290 行，全读）
