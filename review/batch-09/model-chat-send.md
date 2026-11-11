---
title: 模型调用与聊天发送契约
module: model
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

- SDK 对外暴露的发送与取消方法恰好是 `sendMessage`、`sendMessageStreaming` 与 `cancel` 三个。`docs/chat-send-api.md:8`
- Rust 权威实现在 `core/crates/plugin/sdk/src/js_sdk/chat.rs`，TypeScript 导出在 `plugins/types/chat.d.ts`。`docs/chat-send-api.md:18`
- TypeScript 导出位于 `plugins/types/chat.d.ts` 的 `Chat` 命名空间内。`plugins/types/chat.d.ts:9`
- `startTurn`、`waitTurn`、`cancelTurn`、`finishSequence`、回调式聊天流与执行句柄不在当前作者契约内。`docs/chat-send-api.md:14`
- 会话创建、列表、扩展访问与功能性 `Chat.call` 是独立的已有会话与模型能力。`docs/chat-send-api.md:13`
- Native handles 与 finalization records 是内部运行时支持类型，不是插件 SDK 结果。`docs/chat-send-api.md:19`
- `ChatHost` trait 定义聊天服务与执行参与者管理接口。`core/crates/plugin/sdk/src/js_sdk/chat.rs:330`

## AI 速览

- `sendMessage` — 单次发送，接收 `ChatSendRequest`，返回 `JsFuture<ChatSendMessageResultData>`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:401`
- `sendMessageStreaming` — 流式发送，接收 `ChatSendRequest`，返回 `JsAsyncIterable<ChatSendEvent>`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:403`
- `cancel` — 取消，接收 `chatId`，返回 `JsFuture<ChatCancelResultData>`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:405`
- `call` — 功能模型调用，使用 `ChatCallOptions`，不向聊天历史加一轮。`core/crates/plugin/sdk/src/js_sdk/chat.rs:427`
- `ChatSendRequest` — 以 `kind` 为标签区分请求形态。`core/crates/plugin/sdk/src/js_sdk/chat.rs:229`
- `ChatTurnInput` — 含 `text`、`attachments` 与 `replyToMessageTimestamp` 三个字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:198`
- `ChatInitialTurn` — 只有 `record_only` 与 `execute` 两种形态。`core/crates/plugin/sdk/src/js_sdk/chat.rs:206`
- `ChatSummaryPolicy` — 摘要策略枚举，含 `defer` 取值。`core/crates/plugin/sdk/src/js_sdk/chat.rs:216`
- `after_reply` — 在该回复实际完成后才检查已配置的摘要阈值。`core/crates/plugin/sdk/src/js_sdk/chat.rs:222`
- `ChatMessagePart` — 含 `partId`、`sequence`、`kind`、`content`、`toolCallId`、`toolName` 与 `attributes` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:288`
- `ChatMessagePartKind` — part 种类枚举，含 `markdown` 与 `thinking`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:300`
- `ChatSendEvent` — 有 `part` 与 `completed` 两种事件。`core/crates/plugin/sdk/src/js_sdk/chat.rs:317`
- `ChatCancelResult` — 含 `chatId` 与 `cancelRequested` 两个字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:327`
- `ChatRuntime` — 只有 `main` 与 `floating` 两种取值。`core/crates/plugin/sdk/src/js_sdk/chat.rs:431`
- 主入口函数为 `sendMessage`（单次发送）与 `sendMessageStreaming`（流式发送），取消入口为 `cancel`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:403`
- 数据流向一句话：`ChatSendRequest` 经 `sendMessageStreaming` 以 `ChatSendEvent` 输出 part 快照与终端回执。`core/crates/plugin/sdk/src/js_sdk/chat.rs:403`

## 核心机制

### 两种请求形态

- `submit` 保留原始文本、完整附件与显式可空回复目标，其 `turn` 选择执行或真实仅用户持久化。`docs/chat-send-api.md:24`
- `ChatSendRequest` 的 `Submit` 变体含 `chatId`、`runtime`、`input`、`turn` 与 `notifyReply` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:234`
- `ChatTurnInput` 含 `text`、`attachments` 与 `replyToMessageTimestamp` 三个字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:198`
- `ChatInitialTurn` 只有 `record_only` 与 `execute` 两种形态。`core/crates/plugin/sdk/src/js_sdk/chat.rs:206`
- `ChatInitialTurn` 的 `Execute` 变体可带可选的 `participantId`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:211`
- `continue` 标识已提交的用户时间戳与显式 participant，不能重提文本、附件或回复目标。`docs/chat-send-api.md:42`
- `Continue` 变体含 `userMessageTimestamp`、`participantId`、`notifyReply` 与 `summaryPolicy` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:243`
- 每次 continuation 都要求显式 `summaryPolicy`，取值为 `defer` 或 `after_reply`。`docs/chat-send-api.md:45`
- `ChatSummaryPolicy` 的 `defer` 推迟普通历史摘要，但工具循环的上下文限制仍触发压缩。`core/crates/plugin/sdk/src/js_sdk/chat.rs:219`
- `after_reply` 在该回复实际完成后才检查已配置的摘要阈值。`core/crates/plugin/sdk/src/js_sdk/chat.rs:222`
- 文档写明两种 `summaryPolicy` 都抑制回复前与回复中的自动摘要。`docs/chat-send-api.md:45`
- 文档写明 `after_reply` 只在成功持久化的助手回复与原生发送清理后才检查已完成的会话。`docs/chat-send-api.md:46`
- 文档写明已取消、被阻止、被消费与非持久化结果不触发 `after_reply` 检查。`docs/chat-send-api.md:48`
- 文档写明摘要失败会拒绝该次发送，但保留已提交的消息；摘要后没有自动 continuation。`docs/chat-send-api.md:49`
- 文档写明显式提供的 participant 由注册的配置 owner 校验。`docs/chat-send-api.md:26`
- 文档写明群组执行先记录输入再规划，然后在 continuation 上提供每个实际规划的 participant。`docs/chat-send-api.md:27`
- 文档写明 Core 核验 continue 的来源是真实用户行且未被另一用户行取代。`docs/chat-send-api.md:43`
- TypeScript 的 `SendRequest` 类型含 `submit` 与 `continue` 两种形态。`plugins/types/chat.d.ts:213`
- TypeScript 的 `SummaryPolicy` 为 `defer` 或 `after_reply`。`plugins/types/chat.d.ts:211`
- TypeScript 的 `InitialTurn` 为 `record_only` 或 `execute`，`execute` 可带 `participantId`。`plugins/types/chat.d.ts:205`

### 请求校验

- `ChatSendRequest` 的 `validate` 在 `chatId` 为空或全空白时拒绝请求。`core/crates/plugin/sdk/src/js_sdk/chat.rs:253`
- `Submit` 要求文本或附件至少其一，二者都空时 `validate` 拒绝请求。`core/crates/plugin/sdk/src/js_sdk/chat.rs:256`
- `Submit` 的 `replyToMessageTimestamp` 为非正值时请求被拒绝。`core/crates/plugin/sdk/src/js_sdk/chat.rs:259`
- 提交附件的 `fileName` 或 `mimeType` 为空、`fileSize` 为负或 `nodeId` 为空字符串时请求被拒绝。`core/crates/plugin/sdk/src/js_sdk/chat.rs:263`
- `ChatInitialTurn` 的 `Execute` 变体所带的 `participantId` 为空字符串时请求被拒绝。`core/crates/plugin/sdk/src/js_sdk/chat.rs:268`
- `Continue` 要求 `userMessageTimestamp` 为正且 `participantId` 非空，否则请求被拒绝。`core/crates/plugin/sdk/src/js_sdk/chat.rs:273`
- 契约测试断言不带 `summaryPolicy` 的基础请求无法解析为 `ChatSendRequest`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:527`
- 契约测试只接受 `summaryPolicy` 为 `defer` 或 `after_reply` 的值。`core/crates/plugin/sdk/src/js_sdk/chat.rs:528`
- 契约测试断言 `summaryPolicy` 为 `automatic` 的请求反序列化失败。`core/crates/plugin/sdk/src/js_sdk/chat.rs:536`

### 执行控制划分

- 文档写明两种模式共用一次准入与已有的 `startUserMessage` 管线。`docs/chat-send-api.md:52`
- 文档写明原生执行拥有规范租约、输入钩子分发、持久化回执、完成发布与租约释放。`docs/chat-send-api.md:53`
- 文档写明被接受的发送不依赖插件代码最终调用另一个 finish 方法。`docs/chat-send-api.md:54`
- `sendMessage` 只在真实回执与原生清理完成后才 resolve。`core/crates/plugin/sdk/src/js_sdk/chat.rs:400`

### 流式观察

- `sendMessageStreaming` 接收 `ChatSendRequest`，返回 `JsAsyncIterable<ChatSendEvent>`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:403`
- `sendMessageStreaming` 经一个异步迭代器流式输出权威解析 part 快照与真实终端回执。`core/crates/plugin/sdk/src/js_sdk/chat.rs:402`
- `ChatSendEvent` 有 `part` 与 `completed` 两种事件。`core/crates/plugin/sdk/src/js_sdk/chat.rs:317`
- `ChatSendEvent` 的 `Part` 变体含 `chatId`、`messageTimestamp`、`revision` 与 `parts` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:319`
- `ChatSendEvent` 的 `Completed` 变体携带 `MessageSendResultData` 作为 `result`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:321`
- part 事件替换整条有序 part 列表，包括被移除或修订的块。`core/crates/plugin/sdk/src/js_sdk/chat.rs:314`
- part 标识 markdown、thinking、工具调用、工具结果与 status，工具身份与属性已结构化。`docs/chat-send-api.md:116`
- 文档写明被移除的 part 在下一次替换中消失，消费者必须替换消息状态而不是追加每次快照。`docs/chat-send-api.md:118`
- 文档写明多个物理助手消息保留以各自实际消息时间戳标识的独立快照。`docs/chat-send-api.md:124`
- 文档写明每次发送的快照内容与元数据记账上限为 8 MiB，溢出会显式拒绝观察。`docs/chat-send-api.md:128`
- 慢消费会把未消费的修订合并为最新权威状态，不产生仅追加的分块队列。`docs/chat-send-api.md:129`
- 文档写明 JavaScript 迭代器上同时只能有一个待处理的 `next()`。`docs/chat-send-api.md:131`
- 文档写明流式提交在第一次拉取时开始，请求在迭代器创建时被捕获，调用方变更不能改变随后的原生准入。`docs/chat-send-api.md:133`
- 文档写明从未启动的迭代器返回不会发送请求。`docs/chat-send-api.md:135`
- 文档写明 `completed` 事件携带实际的最终回执，其结果区分已提交的完成或取消、非持久化输出、被阻止的输入与被插件消费的输入。`docs/chat-send-api.md:137`
- 文档写明被消费的请求不能证明消费插件自己后续的工作已完成。`docs/chat-send-api.md:139`
- 文档写明原生失败会拒绝迭代，而不是制造一个完成事件。`docs/chat-send-api.md:140`
- `ChatMessagePart` 含 `partId`、`sequence`、`kind`、`content`、`toolCallId`、`toolName` 与 `attributes` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:288`
- `ChatMessagePartKind` 包括 `markdown` 与 `thinking` 两种 part。`core/crates/plugin/sdk/src/js_sdk/chat.rs:300`
- 消息 part 还包括 `tool_call`、`tool_result` 与 `status` 三种。`core/crates/plugin/sdk/src/js_sdk/chat.rs:304`
- TypeScript 的 `SendEvent` 含 `part` 与 `completed` 两种事件。`plugins/types/chat.d.ts:238`
- TypeScript 的 `MessagePartKind` 有 `markdown`、`thinking`、`tool_call`、`tool_result` 与 `status` 五种。`plugins/types/chat.d.ts:235`

### 取消与释放

- `cancel` 只接收 `chatId`，返回 `JsFuture<ChatCancelResultData>`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:405`
- `cancel` 只取消调用插件在指定会话中已捕获的执行。`core/crates/plugin/sdk/src/js_sdk/chat.rs:404`
- `ChatCancelResult` 含 `chatId` 与 `cancelRequested` 两个字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:327`
- TypeScript 的 `CancelResult` 含 `chatId` 与 `cancelRequested` 字段。`plugins/types/chat.d.ts:243`
- TypeScript 导出 `cancel(chatId: string)`，返回 `Promise<ChatCancelResultData>`。`plugins/types/chat.d.ts:260`
- 文档写明中断循环、调用迭代器的 `return()` 或消费者抛错都会释放观察，显式释放会唤醒待处理的原生拉取。`docs/chat-send-api.md:145`
- 文档写明这些释放操作都不取消模型生成，原生发送终结仍会运行。`docs/chat-send-api.md:146`
- 文档写明 `cancel(chatId)` 在异步访问模型之前捕获调用引擎的已启用已认证包及其在该聊天的确切活动执行。`docs/chat-send-api.md:149`
- 文档写明已排队的请求不能取消另一个包或更新的执行。`docs/chat-send-api.md:150`
- 取消确认含 `chatId` 与 `cancelRequested`，终端回执报告原始发送的实际结果。`docs/chat-send-api.md:152`
- 文档写明没有活动的自有执行时产生 `cancelRequested: false` 的真实确认。`docs/chat-send-api.md:153`

### Flutter 引导（Flutter 专属）

- 文档写明 Flutter 引导目前仅支持文本，附件或回复目标会被拒绝且不清空草稿。`docs/chat-send-api.md:63`
- 文档写明 Flutter 的 Guide current conversation 调用内部 `steerMessage(chatId, messageText)` Core 路由。`docs/chat-send-api.md:61`
- 文档写明 Flutter 的 Interrupt and send 是唯一有意组合 `cancelMessage` 与新普通发送的 composer 动作。`docs/chat-send-api.md:62`
- 文档写明引导不是第二次普通发送，也不获取另一个执行租约。`docs/chat-send-api.md:66`
- 文档写明活动聊天轮次拥有共享 `FIFO` 收件箱，provider 在已完成的工具结果之后、开始下一个模型请求之前查看该收件箱。`docs/chat-send-api.md:67`
- 文档写明引导不取消在途的 provider 请求或工具调用，也不自己消费收件箱。`docs/chat-send-api.md:69`
- 文档写明在已完成物理响应边界，外层聊天轮次提交当前助手段，再逐条抽干并持久化每条引导条目为各自可见的用户消息。`docs/chat-send-api.md:72`
- 文档写明多条引导条目按 `FIFO` 顺序恰好消费一次，截止后到达的条目留给下一段。`docs/chat-send-api.md:77`
- 文档写明最终回执仍标识原始用户提交，同时返回最终助手修订。`docs/chat-send-api.md:79`
- 文档写明空的最终收件箱会原子关闭，之后的引导请求收到错误而不是被滞留在已完成的轮次中。`docs/chat-send-api.md:82`
- 文档写明取消关闭收件箱且只丢弃尚未提交的条目。`docs/chat-send-api.md:83`
- 文档写明该 Flutter/Core 控制路由不是新的插件 SDK 方法。`docs/chat-send-api.md:93`

### 群组适配

- 文档写明 `NativeGroupTurnTransport` 只用 `sendMessage` 与 `cancel`。`docs/chat-send-api.md:158`
- 文档写明群组 `finish`/`abandon` 方法是插件本地规划操作，不是额外的 `Tools.Chat` API。`docs/chat-send-api.md:162`
- 文档写明原始用户输入在调用响应规划器之前用 `record_only` 持久化一次。`docs/chat-send-api.md:164`
- 文档写明每个 participant 都用引用该已确认时间戳的 continuation。`docs/chat-send-api.md:165`
- 文档写明中间回复用 `summaryPolicy` `defer`，最终规划回复用 `after_reply` 且只有它有资格收到完成通知。`docs/chat-send-api.md:166`
- 文档写明空计划或 speak-false 计划只留用户记录且不检查摘要。`docs/chat-send-api.md:168`
- 文档写明 continuation 终结不会再次增加原始用户提交计数。`docs/chat-send-api.md:169`
- 文档写明包在生产聊天输入钩子中注册 `group-input-submit`。`docs/chat-send-api.md:172`
- 文档写明该钩子在返回 `Consume` 并清空 composer 之前等待实际输入持久化回执，规划与生成留在钩子之外。`docs/chat-send-api.md:174`
- 文档写明输入持久化失败时 composer 保持完整，规划器或响应失败保留已记录的原始输入并传播原始错误。`docs/chat-send-api.md:176`
- 文档写明 source 为 `Sequence` 的原生发送不递归进入群组规划。`docs/chat-send-api.md:179`

### 上下文与历史策略

- 文档写明会话级上下文刷新读取当前绑定并为每个当前绑定 participant 估算请求窗口，存储的会话窗口取其中最大值。`docs/chat-send-api.md:207`
- 文档写明带显式 participant 的刷新只估算该 participant，历史助手作者不选择会话的当前配置。`docs/chat-send-api.md:209`
- 文档写明重新生成助手修订需要该修订的持久化 participant 身份，缺失身份、目录初始化错误与扩展读取错误以原始失败停止重新生成而不是选替代 participant。`docs/chat-send-api.md:213` [[model-catalog|模型目录与模型识别]]
- 文档写明手动摘要插入调用摘要模型时不先解析会话执行 participant，包括只有用户消息的历史。`docs/chat-send-api.md:216`
- 文档写明共享 JavaScript 运行时为每个待处理 Promise 反应保留一次调用，主钩子完成可返回 `Consume` 而这些反应让会话保持分离。`docs/chat-send-api.md:220`
- 文档写明插件不需要为观察到的后台工作设置固定时长的 keepalive 定时器。`docs/chat-send-api.md:224`
- 文档写明配置执行结果要求完整的 `historyPolicy` 对象含 `isolateParticipants` 与 `labelUserMessages`，普通模型会话两者都为 false。`docs/chat-send-api.md:228`
- 文档写明角色卡隔离 participant，群组还标注用户消息；Core 对模型请求与上下文窗口估算都应用该策略。`docs/chat-send-api.md:230`
- 文档写明隔离的助手消息按其持久化 participant ID 在已认证配置 owner 下归属，其他 participant 的有序 Markdown 发言成为前缀为 [From role: name] 的用户参考上下文。`docs/chat-send-api.md:233`
- 文档写明其他 participant 的 thinking、status 与工具协议被排除，群组用户输入前缀为 [From user]。`docs/chat-send-api.md:237`
- 文档写明投影从最新摘要开始，不从改名卡片、重复显示名或当前群组成员推断历史作者，缺失必需作者或显示身份是错误。`docs/chat-send-api.md:239`
- 文档写明最终回复后 Core 刷新会话窗口并检查每个已配置模型的已启用摘要阈值，超阈值调度一个已有的规范摘要任务且 `autoContinue` 为 false。`docs/chat-send-api.md:243`
- 文档写明该 API 不含角色卡群组概念。`docs/chat-send-api.md:247`

### 原生存储宿主

- 文档写明原生存储宿主用标准库 `File::lock` 与 `File::try_lock`（Rust 1.89 最低）而不是 `fs2`。`docs/chat-send-api.md:250`
- 文档写明争用的租约仍归活动进程所有，其他锁错误经宿主 API 传播。`docs/chat-send-api.md:251`

### 验证范围

- 文档把 `node --test core/crates/plugin/javascript-bridge/tests/chat-send-contracts.test.mjs` 列为无需 Rust/Flutter 编译的可重复检查。`docs/chat-send-api.md:190`
- 文档写明源码断言与 Rust 语法解析不是 Rust 类型检查、实时 AI 请求或跨平台运行时验收。`docs/chat-send-api.md:198`

## 关键符号

- `ChatHost` — 聊天服务与执行参与者管理接口。`core/crates/plugin/sdk/src/js_sdk/chat.rs:330`
- `sendMessage` — 单次发送，接收 `ChatSendRequest`，返回 `JsFuture<ChatSendMessageResultData>`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:401`
- `sendMessageStreaming` — 流式发送，接收 `ChatSendRequest`，返回 `JsAsyncIterable<ChatSendEvent>`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:403`
- `cancel` — 取消，接收 `chatId`，返回 `JsFuture<ChatCancelResultData>`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:405`
- `call` — 功能模型调用，使用 `ChatCallOptions`，不向聊天历史加一轮。`core/crates/plugin/sdk/src/js_sdk/chat.rs:427`
- `ChatSendRequest` — 以 `kind` 为标签区分请求形态。`core/crates/plugin/sdk/src/js_sdk/chat.rs:229`
- `ChatTurnInput` — 含 `text`、`attachments` 与 `replyToMessageTimestamp` 三个字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:198`
- `ChatInitialTurn` — 只有 `record_only` 与 `execute` 两种形态。`core/crates/plugin/sdk/src/js_sdk/chat.rs:206`
- `ChatSendAttachment` — 含 `vfsPath`、`filePath` 与 `nodeId` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:465`
- 附件的 `fileName`、`mimeType`、`fileSize` 与 `content` 分别记录原始文件名、MIME 类型、字节数与原始内联载荷。`core/crates/plugin/sdk/src/js_sdk/chat.rs:472`
- `ChatSendContinuation` — 只含 `userMessageTimestamp` 一个字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:483`
- `ChatSendMessageOptions` — 含 `runtime`、`persist_turn` 与 `notify_reply` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:493`
- 发送选项还含 `hide_user_message`、`disable_warning` 与 `timeout_ms` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:505`
- 发送选项的 `continuation` 指向已提交的用户消息，附件、回复与替换文本被禁止。`core/crates/plugin/sdk/src/js_sdk/chat.rs:513`
- `ChatRuntime` — 只有 `main` 与 `floating` 两种取值。`core/crates/plugin/sdk/src/js_sdk/chat.rs:431`
- TypeScript 导出 `sendMessage(request: SendRequest)`，返回 `Promise<ChatSendMessageResultData>`。`plugins/types/chat.d.ts:315`
- TypeScript 导出 `sendMessageStreaming(request: SendRequest)`，返回 `AsyncIterable<SendEvent>`。`plugins/types/chat.d.ts:319`
- TypeScript 导出的 `call` 调用配置的功能模型且不向聊天历史加一轮。`plugins/types/chat.d.ts:255`

## 调用链

1. 插件构造 `Submit` 请求：`chatId`、`runtime`、`input`、`turn` 与 `notifyReply`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:234`
2. `Continue` 变体含 `userMessageTimestamp`、`participantId`、`notifyReply` 与 `summaryPolicy` 字段。`core/crates/plugin/sdk/src/js_sdk/chat.rs:243`
3. 校验先行：`ChatSendRequest` 的 `validate` 在 `chatId` 为空或全空白时拒绝请求。`core/crates/plugin/sdk/src/js_sdk/chat.rs:253`
4. 文档写明两种模式共用一次准入与已有的 `startUserMessage` 管线。`docs/chat-send-api.md:52`
5. `sendMessage` 只在真实回执与原生清理完成后才 resolve。`core/crates/plugin/sdk/src/js_sdk/chat.rs:400`
6. `sendMessageStreaming` 经一个异步迭代器流式输出权威解析 part 快照与真实终端回执。`core/crates/plugin/sdk/src/js_sdk/chat.rs:402`
7. `Completed` 事件携带 `MessageSendResultData` 作为 `result`。`core/crates/plugin/sdk/src/js_sdk/chat.rs:321`
8. `cancel` 只取消调用插件在指定会话中已捕获的执行。`core/crates/plugin/sdk/src/js_sdk/chat.rs:404`
9. 中断循环、调用迭代器的 `return()` 或消费者抛错只释放观察，都不取消模型生成。`docs/chat-send-api.md:146`

## 来源

- `docs/chat-send-api.md`：当前插件聊天发送契约文档，全文 256 行。
- `core/crates/plugin/sdk/src/js_sdk/chat.rs`：Rust 权威实现，全文 606 行。
- `plugins/types/chat.d.ts`：TypeScript 导出；文档点名该文件，写作时另行读过并逐行核对了 Chat 命名空间内的发送方法签名。

否定性核验方法：2026-11-12 对基线 AAswordman/Operit2 @ 364d1d594 的本地 checkout 执行 grep -c，`startTurn`、`waitTurn`、`cancelTurn`、`finishSequence` 在 chat.rs 与 chat.d.ts 中均为 0 命中；文档第 14-16 行亦写明四者不在当前作者契约内。

范围说明：文档中关于原生执行内部（规范租约、`startUserMessage` 管线、Flutter 引导、群组适配、8 MiB 上限、迭代器语义、取消语义）的陈述，在本页写作时只以文档为据，未在 seed 代码中逐行验证；正文已用“文档写明”标出这类断言。

未读文件：文档提到的 javascript-bridge 测试、character_cards 测试与脚本、check-chat-configuration.mjs、results.rs 等文件不在本页引用范围内，未读未引。
