---
title: ESP32 聊天实现
module: edge
platforms: [esp32]
sources: 2
date: 2026-11-11
---

## 概述

- 本页讲设备上的两套聊天实现：独立直连聊天与远端 Core 聊天。`edge/boards/esp32/src/edge_chat.rs:1`
- 独立聊天不需要 Core、SQL、ToolPkg 或 peer 连接。`edge/boards/esp32/src/standalone_chat.rs:1`
- 远端 Core 模式下设备只做显示与输入，模型执行留在 Core。`edge/boards/esp32/src/edge_chat.rs:790`
- 设备聊天 UI 的总览见 [[edge-overview|Edge 总览与产品形态]]。`edge/boards/esp32/src/edge_chat.rs:1`

## AI 速览

- 独立直连聊天（standalone_chat）：直连模型服务，不需要 Core。`edge/boards/esp32/src/standalone_chat.rs:1`
- 远端 Core 聊天 UI（edge_chat）：订阅 Core 的消息窗口与状态流。`edge/boards/esp32/src/edge_chat.rs:1`
- `Config` — 独立聊天配置：endpoint、model、apiKey、systemPrompt。`edge/boards/esp32/src/standalone_chat.rs:16`
- `Chat` — 独立聊天的会话持有者，保存 config、http 与 state。`edge/boards/esp32/src/standalone_chat.rs:52`
- `ChatSession` — 远端聊天的会话状态：显示缓存、流文本、游标与错误。`edge/boards/esp32/src/edge_chat.rs:171`
- `SpaceChatRoute` — 同一 Space 的聊天路由，只保留选中的 chatId。`edge/boards/esp32/src/edge_chat.rs:210`
- `UiValue` — 编码列表缓存，增量更新只解码被寻址的元素。`edge/boards/esp32/src/edge_chat.rs:99`
- `StreamText` — 流式回复文本。`edge/boards/esp32/src/edge_chat.rs:313`
- 主入口：独立聊天用 `configure` 提供配置。`edge/boards/esp32/src/standalone_chat.rs:90`
- 主入口：独立聊天用 `send` 发送消息。`edge/boards/esp32/src/standalone_chat.rs:260`
- 主入口：远端聊天用 `install` 安装会话。`edge/boards/esp32/src/edge_chat.rs:605`
- 数据流向：独立聊天由 `send` 发送用户文本，回复增量追加到本地消息。`edge/boards/esp32/src/standalone_chat.rs:260`
- 数据流向：远端聊天订阅 chatMessagesWindowFlow 接收消息窗口。`edge/boards/esp32/src/edge_chat.rs:281`

## 核心机制

### 独立直连模型服务

- `Config` 有 endpoint、model、apiKey、systemPrompt 四个字段。`edge/boards/esp32/src/standalone_chat.rs:17`
- endpoint 上限 1024 字节且必填，model 上限 128 字节且必填。`edge/boards/esp32/src/standalone_chat.rs:32`
- apiKey 上限 512 字节且选填，systemPrompt 上限 1024 字节且选填。`edge/boards/esp32/src/standalone_chat.rs:34`
- endpoint 必须以 http:// 或 https:// 开头。`edge/boards/esp32/src/standalone_chat.rs:38`
- apiKey 不得包含回车或换行。`edge/boards/esp32/src/standalone_chat.rs:38`
- `send` 拒绝空消息。`edge/boards/esp32/src/standalone_chat.rs:262`
- `send` 拒绝超过 MAX_TEXT（2048 字节）的消息。`edge/boards/esp32/src/standalone_chat.rs:264`
- `send` 在上一条仍在发送时拒绝新消息。`edge/boards/esp32/src/standalone_chat.rs:270`
- systemPrompt 非空时作为第一条 system 角色消息发出。`edge/boards/esp32/src/standalone_chat.rs:280`
- 本地追加一条空文本 ai 消息作为流式回复占位。`edge/boards/esp32/src/standalone_chat.rs:285`
- 每次发送使用 device-chat- 加 UUID 的流标识。`edge/boards/esp32/src/standalone_chat.rs:290`
- apiKey 非空时以 Bearer 方式放在 Authorization 请求头。`edge/boards/esp32/src/standalone_chat.rs:298`
- endpoint 允许 http:// 时，Bearer apiKey 会以明文经未加密 HTTP 发送。`edge/boards/esp32/src/standalone_chat.rs:38` `edge/boards/esp32/src/standalone_chat.rs:298`
- 请求体固定 stream 为 true 且 max_tokens 为 256。`edge/boards/esp32/src/standalone_chat.rs:306`
- 连接超时 10 秒，读取超时 45 秒。`edge/boards/esp32/src/standalone_chat.rs:311`
- 独立聊天按行解析 data: 开头的 SSE 事件。`edge/boards/esp32/src/standalone_chat.rs:218`
- data: [DONE] 标记流结束。`edge/boards/esp32/src/standalone_chat.rs:222`
- finish_reason 出现时流标记完成。`edge/boards/esp32/src/standalone_chat.rs:237`
- delta 的 content 增量文本追加到最后一条消息。`edge/boards/esp32/src/standalone_chat.rs:240`
- 追加的回复文本用 tail 截断到 MAX_TEXT。`edge/boards/esp32/src/standalone_chat.rs:245`
- 单个事件超过 MAX_EVENT（8192 字节）时流报错。`edge/boards/esp32/src/standalone_chat.rs:251`
- 无法解析为 JSON 的事件使流记录错误。`edge/boards/esp32/src/standalone_chat.rs:229`
- 服务端返回 error 字段时流记录 Chat service returned an error。`edge/boards/esp32/src/standalone_chat.rs:234`
- 非 2xx 状态码时发送结果报错 Chat HTTP 加状态码。`edge/boards/esp32/src/standalone_chat.rs:343`
- 流未收到完成标记就关闭时发送结果报错聊天连接提前中断。`edge/boards/esp32/src/standalone_chat.rs:349`
- `bound` 在消息数超过 MAX_MESSAGES（8 条），或（消息数多于 2 条且）文本总量超过 MAX_CONTEXT（6144 字节）时成对丢弃旧消息。`edge/boards/esp32/src/standalone_chat.rs:80`
- 已配置时，独立聊天快照的 mode 是 direct，只有一条标题为本机对话的会话，且 hasOlder 与 hasNewer 均为 false。`edge/boards/esp32/src/standalone_chat.rs:163`
- `status` 在未配置时返回未配置。`edge/boards/esp32/src/standalone_chat.rs:167`
- `status` 在发送中时返回生成中。`edge/boards/esp32/src/standalone_chat.rs:170`
- 有错误且未发送时返回错误。`edge/boards/esp32/src/standalone_chat.rs:172`
- 其余情况下返回就绪。`edge/boards/esp32/src/standalone_chat.rs:175`
- `newChat` 在发送进行中时拒绝新建会话。`edge/boards/esp32/src/standalone_chat.rs:185`
- 生成新的会话 id 并清空已有消息。`edge/boards/esp32/src/standalone_chat.rs:189`

### 远端 Core 模式

- `SpaceChatRoute` 在同一 Space 内只保留选中的 chatId，不保存会话记录副本。`edge/boards/esp32/src/edge_chat.rs:208`
- Space 变化时生成新的 chatId。`edge/boards/esp32/src/edge_chat.rs:238`
- 在会话结束且距上次尝试至少 3 秒时重试安装。`edge/boards/esp32/src/edge_chat.rs:243`
- `install` 在 chatId 为空时把会话标记为需要创建。`edge/boards/esp32/src/edge_chat.rs:610`
- `install` 为空 chatId 生成新的 UUID。`edge/boards/esp32/src/edge_chat.rs:611`
- 新会话通过 ensureRoutedChat 在 Core 显式创建。`edge/boards/esp32/src/edge_chat.rs:655`
- 通过 edge-ui-messages 订阅 chatMessagesWindowFlow。`edge/boards/esp32/src/edge_chat.rs:281`
- `windowArgs` 把显示页的 textBytes 与 textLines 预算发给 Core。`edge/boards/esp32/src/edge_chat.rs:307`
- 消息窗口超过 MAX_CHAT_MESSAGES（12 行）时返回行数超限错误。`edge/boards/esp32/src/edge_chat.rs:708`
- 640 字节与 15 行的预算对应约三个 320x240 聊天视口，数值出自 seed 文件注释。`edge/boards/esp32/src/edge_chat.rs:511`
- chatStateFlow 订阅提供远端聊天状态。`edge/boards/esp32/src/edge_chat.rs:747`
- `executionStatus` 从 isLoading 读出是否正在生成。`edge/boards/esp32/src/edge_chat.rs:793`
- `executionStatus` 从 inputProcessingState 的 Error message 读出执行错误。`edge/boards/esp32/src/edge_chat.rs:794`
- 远端模式下只保留执行摘要，模型执行留在 Core。`edge/boards/esp32/src/edge_chat.rs:790`
- `ChatSession` 的 histories 是 UiValue 显示缓存。`edge/boards/esp32/src/edge_chat.rs:174`
- messages 字段是 UiValue 显示缓存。`edge/boards/esp32/src/edge_chat.rs:184`
- 通过 routedChatListFlow 订阅对话列表。`edge/boards/esp32/src/edge_chat.rs:1221`
- 对话列表上限是 MAX_CONVERSATIONS（24 条）。`edge/boards/esp32/src/edge_chat.rs:510`
- `selectChat` 只改变本设备的视图，完整 Core 继续拥有聊天。`edge/boards/esp32/src/edge_chat.rs:1272`
- 历史游标只保留 32 个。`edge/boards/esp32/src/edge_chat.rs:1315`
- 远端快照的 hasOlder 由 older 游标是否存在决定。`edge/boards/esp32/src/edge_chat.rs:1173`
- 插件列表通过 chatAvailablePlugins 从 Core 读取。`edge/boards/esp32/src/edge_chat.rs:939`
- `pluginCallDeadline` 给插件调用设置 8 秒期限。`edge/boards/esp32/src/edge_chat.rs:1022`
- 插件测试调用 chatPluginStatus。`edge/boards/esp32/src/edge_chat.rs:1043`
- `sendImage` 仅在非 espidf 目标（编辑器模拟器）上提供，ESP32 固件无此函数；它只接受不超过 512 KiB 的 PNG 或 JPEG 图片。`edge/boards/esp32/src/edge_chat.rs:1538`
- 仅在非 espidf 目标（编辑器模拟器）上提供时，sendImage 先调用 registerChatImage 向 Core 注册图片。`edge/boards/esp32/src/edge_chat.rs:1574`
- 仅在非 espidf 目标（编辑器模拟器）上提供时，独立聊天激活时 `sendImage` 返回本机直连聊天暂不支持图片的错误。`edge/boards/esp32/src/edge_chat.rs:1536`
- 远端模式的 `send` 在独立聊天激活时转交给独立聊天。`edge/boards/esp32/src/edge_chat.rs:1600`
- 远端模式的 `send` 拒绝超过 16384 字节的消息。`edge/boards/esp32/src/edge_chat.rs:1604`
- 以 promptFunctionType CHAT 调用远端。`edge/boards/esp32/src/edge_chat.rs:1645`
- persistTurn 固定为 true。`edge/boards/esp32/src/edge_chat.rs:1650`
- 超过 2048 字节的消息用 sendUserMessageStream 分块上传。`edge/boards/esp32/src/edge_chat.rs:1658`
- 2048 字节以内的消息用 sendUserMessage 一次调用发送。`edge/boards/esp32/src/edge_chat.rs:1677`
- Chunk 事件把增量文本追加到显示尾部并受 MAX_CHAT_STRING_BYTES（640 字节）限制。`edge/boards/esp32/src/edge_chat.rs:328`
- Replace 事件先清空再追加。`edge/boards/esp32/src/edge_chat.rs:329`
- 只保留最后 MAX_CHAT_LINES（15 行）。`edge/boards/esp32/src/edge_chat.rs:332`
- `projectMessages` 只取最近 MAX_CHAT_MESSAGES 条消息。`edge/boards/esp32/src/edge_chat.rs:1452`
- 消息投影的 text 字段经 boundedText 截断。`edge/boards/esp32/src/edge_chat.rs:1458`
- 消息投影保留 sender 与 streamId 字段。`edge/boards/esp32/src/edge_chat.rs:1471`
- `renderMessages` 让快照与直播流共用一个总显示预算。`edge/boards/esp32/src/edge_chat.rs:1480`
- `UiValue` 以编码形式缓存列表，增量更新只解码被寻址的元素。`edge/boards/esp32/src/edge_chat.rs:97`
- `boundCoreValue` 把超过 MAX_CHAT_STRING_BYTES 的字符串截断。`edge/boards/esp32/src/edge_chat.rs:559`
- Core 二进制字段的保留上限是 MAX_CORE_BYTES（1024 字节），值嵌套深度上限是 MAX_CORE_VALUE_DEPTH（16 层）。`edge/boards/esp32/src/edge_chat.rs:514`
- 消息流扫描上限是 MAX_STREAM_DESCRIPTORS（8 个）、MAX_STREAM_SCAN_DEPTH（8 层）、MAX_STREAM_SCAN_ITEMS（每层 32 项）。`edge/boards/esp32/src/edge_chat.rs:341`
- `openUiSubscription` 用互斥锁串行化 watch 打开。`edge/boards/esp32/src/edge_chat.rs:58`
- 取消进行中的 watch 打开会污染共享通道，因此让它完成后再释放返回的流。`edge/boards/esp32/src/edge_chat.rs:34`
- `recordSubscriptionEnd` 只在未取消时把订阅标记为已关闭。`edge/boards/esp32/src/edge_chat.rs:806`
- `needsReconnect` 在会话要求重连或订阅已关闭时返回 true。`edge/boards/esp32/src/edge_chat.rs:809`
- `isConnected` 在独立聊天激活时返回 true。`edge/boards/esp32/src/edge_chat.rs:817`
- `clear` 丢弃本地聊天路由与显示状态，配对凭据由 Edge 配对方另外清除。`edge/boards/esp32/src/edge_chat.rs:830`
- `taskStatus` 为 320x240 任务栏提供紧凑状态标签。`edge/boards/esp32/src/edge_chat.rs:1385`
- 远端聊天的 `snapshot` 在独立聊天激活时直接返回独立聊天的快照。`edge/boards/esp32/src/edge_chat.rs:1152`

### 迟到结果隔离

- `installSession` 先调用 clear 退役旧会话。`edge/boards/esp32/src/edge_chat.rs:619`
- 远端对话创建结果只有当前会话仍是活动会话时才生效。`edge/boards/esp32/src/edge_chat.rs:657`
- 插件调用结果只有当前会话仍是活动会话时才写入状态。`edge/boards/esp32/src/edge_chat.rs:941`
- 插件详情回复只有当前会话仍是活动会话时才写入状态。`edge/boards/esp32/src/edge_chat.rs:988`
- 创建新对话的回复只有当前会话仍是活动会话时才安装。`edge/boards/esp32/src/edge_chat.rs:1366`
- Space 切换时旧会话在解析新配置之前被退役。`edge/boards/esp32/src/standalone_chat.rs:107`
- 迟到的旧工作线程保留自己的 Arc，不能向新会话写入。`edge/boards/esp32/src/standalone_chat.rs:106`
- 发送进行中的请求按原配置完成，不被新配置替换。`edge/boards/esp32/src/standalone_chat.rs:124`
- 配置与当前配置相同时返回 Ok 且不重建会话。`edge/boards/esp32/src/standalone_chat.rs:121`
- seed 内测试用例确认迟到回复到达旧会话后新会话的消息列表仍为空。`edge/boards/esp32/src/standalone_chat.rs:525`
- 丢失 peer 不会重置独立聊天，切换 Space 会重置独立聊天。`edge/boards/esp32/src/standalone_chat.rs:88`

## 关键符号

- `Config` — 独立聊天配置：endpoint、model、apiKey、systemPrompt。`edge/boards/esp32/src/standalone_chat.rs:16`
- `Chat` — 独立聊天的会话持有者。`edge/boards/esp32/src/standalone_chat.rs:52`
- `configure` — 应用提供 chat 配置以选择独立聊天。`edge/boards/esp32/src/standalone_chat.rs:90`
- `Response` — SSE 流解析器。`edge/boards/esp32/src/standalone_chat.rs:197`
- `bound` — 独立聊天上下文裁剪。`edge/boards/esp32/src/standalone_chat.rs:76`
- `send` — 独立聊天发送：POST 到模型端点并流式追加回复。`edge/boards/esp32/src/standalone_chat.rs:260`
- `newChat` — 独立聊天新建会话。`edge/boards/esp32/src/standalone_chat.rs:182`
- `status` — 独立聊天状态标签。`edge/boards/esp32/src/standalone_chat.rs:165`
- `ChatSession` — 远端聊天的会话状态。`edge/boards/esp32/src/edge_chat.rs:171`
- `SpaceChatRoute` — 同一 Space 的聊天路由。`edge/boards/esp32/src/edge_chat.rs:210`
- `UiValue` — 编码列表缓存。`edge/boards/esp32/src/edge_chat.rs:99`
- `StreamText` — 流式回复文本。`edge/boards/esp32/src/edge_chat.rs:313`
- `install` — 安装远端聊天会话。`edge/boards/esp32/src/edge_chat.rs:605`
- `installSession` — 创建会话并在需要时显式创建远端对话。`edge/boards/esp32/src/edge_chat.rs:615`
- `startSubscriptions` — 打开消息窗口与状态订阅。`edge/boards/esp32/src/edge_chat.rs:674`
- `watchChatMessages` — 订阅消息窗口流。`edge/boards/esp32/src/edge_chat.rs:273`
- `windowArgs` — 显示页预算参数。`edge/boards/esp32/src/edge_chat.rs:303`
- `executionStatus` — 从远端状态读生成标志与执行错误。`edge/boards/esp32/src/edge_chat.rs:791`
- `openUiSubscription` — 串行化打开 watch 订阅。`edge/boards/esp32/src/edge_chat.rs:58`
- `snapshot` — 远端聊天快照。`edge/boards/esp32/src/edge_chat.rs:1151`
- `selectChat` — 切换本设备视图的对话。`edge/boards/esp32/src/edge_chat.rs:1273`
- `newChat` — 在 Core 创建新对话。`edge/boards/esp32/src/edge_chat.rs:1322`
- `send` — 远端发送：用户消息到 Core。`edge/boards/esp32/src/edge_chat.rs:1599`
- `sendImageMessage` — 构造远端发送调用。`edge/boards/esp32/src/edge_chat.rs:1637`
- `sendImage` — 仅在非 espidf 目标（编辑器模拟器）上提供，注册并发送图片；ESP32 固件无此函数。`edge/boards/esp32/src/edge_chat.rs:1535`
- `conversationsAction` — 打开对话列表订阅。`edge/boards/esp32/src/edge_chat.rs:1205`
- `moveHistory` — 在有界显示页之间移动。`edge/boards/esp32/src/edge_chat.rs:1307`
- `clear` — 丢弃本地聊天路由与显示状态。`edge/boards/esp32/src/edge_chat.rs:831`
- `taskStatus` — 320x240 任务栏状态标签。`edge/boards/esp32/src/edge_chat.rs:1385`
- `pluginCallDeadline` — 插件调用 8 秒期限。`edge/boards/esp32/src/edge_chat.rs:1021`
- `boundCoreValue` — 远端值的有界截断。`edge/boards/esp32/src/edge_chat.rs:559`
- `projectMessages` — 消息投影。`edge/boards/esp32/src/edge_chat.rs:1448`
- `renderMessages` — 快照与直播流合并渲染。`edge/boards/esp32/src/edge_chat.rs:1480`

## 调用链

1. 独立聊天配置：应用提供 chat 配置 → `configure` 校验并创建 `Chat`。`edge/boards/esp32/src/standalone_chat.rs:90`
2. 独立聊天发送：用户文本 → `send` 追加到本地消息并裁剪上下文。`edge/boards/esp32/src/standalone_chat.rs:260`
3. 独立聊天收尾：收到 data: [DONE] 后流标记完成。`edge/boards/esp32/src/standalone_chat.rs:222`
4. 远端聊天安装：poll 按连接状态安装或重装会话。`edge/boards/esp32/src/edge_chat.rs:219`
5. 远端聊天发送：用户文本 → `send` 发往远端。`edge/boards/esp32/src/edge_chat.rs:1599`
6. 超过 2048 字节的消息用 sendUserMessageStream 分块上传。`edge/boards/esp32/src/edge_chat.rs:1658`
7. 2048 字节以内的消息用 sendUserMessage 一次调用发送。`edge/boards/esp32/src/edge_chat.rs:1677`
8. 迟到结果隔离：Space 切换 → 旧会话在解析新配置之前被退役 → 迟到回复不进入新会话。`edge/boards/esp32/src/standalone_chat.rs:107`
9. 迟到结果隔离：远端聊天安装新会话时 `installSession` 先调用 clear 退役旧会话。`edge/boards/esp32/src/edge_chat.rs:619`

## 来源

- seed 文件：`edge/boards/esp32/src/edge_chat.rs`（1972 行）、`edge/boards/esp32/src/standalone_chat.rs`（544 行），基线 AAswordman/Operit2 @ 364d1d594。
- 本页事实见同名 `.facts.json`，每条事实带文件行号引用。
- 本页没有全仓零命中类断言；“不需要 Core、SQL、ToolPkg 或 peer 连接”是 seed 文件首行注释原文，不是 grep 零命中结论。
- 本页全部数字来自两个 seed 文件内的常量与代码逻辑；测试用例中的断言已标注为测试用例确认。
