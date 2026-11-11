---
title: Agent 回路总览
module: agent
platforms: [all]
sources: 5
date: 2026-11-11
---

## 概述

本页描述一轮 Agent 请求在 Core 层的完整链路，从用户输入经模型工具循环到回填（`core/crates/runtime/application/src/services/ChatServiceCore.rs:537`）。
回路逻辑在 Rust Core 层实现，全部平台共用；`ChatInputMenuSettings` 的设置属于聊天绑定选定的执行 Core，不属于 UI 设备（`core/crates/runtime/application/src/services/ChatServiceCore.rs:121`）。
ChatServiceCore 是 Runtime 域的聊天服务核心（见 [[core-runtime|Runtime 总览与 OperitApplication]]），持有四个委托与服务字段（`core/crates/runtime/application/src/services/ChatServiceCore.rs:244`）。
模型工具循环本体在 EnhancedAIService 内，本页 seed 未通读其实现，只核实调用点（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:465`）。
轮次编排本体在 MessageCoordinationDelegate，本页只读过其中 `sendRoutedContinuation` 与总结检查相关区段（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:486`）。

## AI 速览

- `sendUserMessage` — `operit_core_route` 路由入口，绑定键为 `chatIdOverride`（`core/crates/runtime/application/src/services/ChatServiceCore.rs:537`）
- `startUserMessage` — 发送入口，跑输入钩子后交协调委托（`core/crates/runtime/application/src/services/ChatServiceCore.rs:550`）
- sendUserMessageStream — 按 `expectedByteLength` 收完流式文本再发送（`core/crates/runtime/application/src/services/ChatServiceCore.rs:573`）
- `newEnhancedAiServiceForChat` — 按会话 id 取独占 `EnhancedAIService`（`core/crates/runtime/application/src/services/ChatServiceCore.rs:351`）
- MessageCoordinationDelegate.sendUserMessage — 协调委托的发送入口（`core/crates/runtime/application/src/services/ChatServiceCore.rs:666`）
- AIMessageManager.sendMessage — 登记本次发送操作（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:324`）
- `getMemoryFromMessages` — 从最后一条总结起取历史（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:663`）
- prepare_conversation_history — 跑钩子、注入系统提示、归一化工具结果轮次（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:120`）
- summarizeMemory — 只总结上一次总结之后的消息（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:547`）
- `shouldGenerateSummary` — 只看配置的上下文 token 阈值（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:647`）
- `insertSummary` — 只在用户或 AI 消息处插入总结（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1407`）
- `compactChat` — 手动压缩为检查点，不论阈值（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1527`）
- switch_core — 内置工具，预检目标节点（`core/crates/tool/services/src/tools/ToolRegistration.rs:212`）
- `resolveSwitchCoreTarget` — 解析目标节点引用（`core/crates/tool/services/src/tools/ToolRegistration.rs:1558`）
- `beforeChangeRoute` — Binding 移动前检查执行归属（`core/crates/runtime/application/src/services/ChatServiceCore.rs:841`）
- `afterChangeRoute` — 路由变更到达目标 Core 后恢复目标会话（`core/crates/runtime/application/src/services/ChatServiceCore.rs:860`）
- `resumeFromRouteContext` — 用路由上下文恢复轮次（`core/crates/runtime/application/src/services/ChatServiceCore.rs:776`）
- `sendRoutedContinuation` — 路由续发，不先做总结检查（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:486`）
- `generateLocalLlm` — 只在 Binding 归属节点做模型推理（`core/crates/runtime/application/src/services/ChatServiceCore.rs:311`）
- `callToolPkgRoute` — 经 Binding 路由执行插件方法（`core/crates/runtime/application/src/services/ChatServiceCore.rs:328`）
- cancelOperationForId — 先取消令牌再关流、调 cancelConversation（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1116`）
- `steerMessage` — 只引导当前逻辑轮次（`core/crates/runtime/application/src/services/ChatServiceCore.rs:898`）

## 核心机制

### 一轮发送链路

`sendUserMessage` 是 `operit_core_route` 路由入口，绑定键为 `chatIdOverride`（`core/crates/runtime/application/src/services/ChatServiceCore.rs:537`）。
路由入口把一轮发送交给 `startUserMessage` 执行（`core/crates/runtime/application/src/services/ChatServiceCore.rs:550`）。
没有显式会话 id 时，发送入口先调 `initializeChatConfiguration` 再解析输入会话（`core/crates/runtime/application/src/services/ChatServiceCore.rs:598`）。
原生序列执行要求 `admittedLease` 与 `deferSequenceCompletion`、`nativeExecutionId` 同时有或同时无（`core/crates/runtime/application/src/services/ChatServiceCore.rs:594`）。
非续发（`continuation` 为空）且 `chatInputSubmitRequestedHandled` 未处理过时，发送前派发 `CHAT_INPUT_EVENT_SUBMIT_REQUESTED` 输入钩子，由 `dispatchRegisteredChatInputHooks` 执行（`core/crates/runtime/application/src/services/ChatServiceCore.rs:617`）。
非续发且未处理过时，钩子返回 `CHAT_INPUT_SUBMIT_ACTION_BLOCK` 或 `CHAT_INPUT_SUBMIT_ACTION_CONSUME` 时本轮不发送（`core/crates/runtime/application/src/services/ChatServiceCore.rs:628`）。
非续发且未处理过时，钩子返回 `CHAT_INPUT_SUBMIT_ACTION_REPLACE` 或 `CHAT_INPUT_SUBMIT_ACTION_ALLOW` 时继续发送，`REPLACE` 在钩子给出文本时用该文本替换输入（`core/crates/runtime/application/src/services/ChatServiceCore.rs:638`）。
非续发且 `chatInputSubmittedHandled` 未处理过时，提交后派发 `CHAT_INPUT_EVENT_SUBMITTED` 输入钩子，钩子错误用 `?` 直接传播（`core/crates/runtime/application/src/services/ChatServiceCore.rs:654`）。
钩子跑完后调用 `invalidateToggleDefinitions` 使输入菜单开关定义失效（`core/crates/runtime/application/src/services/ChatServiceCore.rs:656`）。
有增强 AI 服务与协调委托时，发送入口把该会话的待处理队列标记为阻塞（`markPendingQueueBlocked`）（`core/crates/runtime/application/src/services/ChatServiceCore.rs:658`）。
每轮发送通过 `newEnhancedAiServiceForChat` 取该会话独占的 AI 服务实例，未初始化时返回错误（`core/crates/runtime/application/src/services/ChatServiceCore.rs:660`）。
发送入口把本轮交给协调委托的 `sendUserMessage`（`messageCoordinationDelegate`）（`core/crates/runtime/application/src/services/ChatServiceCore.rs:666`）。
sendMessage 先在 `activeChatOperations` 登记本次发送操作，取操作 id（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:324`）。
sendMessage 用 `promptHistoryOverride` 覆盖时跳过 `getMemoryFromMessages`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:351`）。
图片链接默认只保留最近 2 轮用户回合，媒体链接默认只保留最近 1 轮（`maxImageHistoryUserTurnsFlow`、`maxMediaHistoryUserTurnsFlow`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:360`）。
sendMessage 先调 `limitImageLinksInChatHistory` 再调 `limitMediaLinksInChatHistory` 裁剪历史（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:366`）。
插件消息处理钩子命中时由插件执行接管本次发送（`MessageProcessingPluginRegistry::createExecutionIfMatched`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:370`）。
偏好关闭流式输出时，本次发送不启用流式（`disableStreamOutputFlow`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:402`）。
`resume` 为真时以 `ResumeRequest` 调 `resume`，否则调 `sendMessageWithConfiguration`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:465`）。
发送成功后把响应流登记进本次操作（`responseStream`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:479`）。
响应流清理任务排在宿主运行时异步任务上（`scheduleHostRuntimeAsyncTask`），收完流才注销操作（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:492`）。
历史准备在 ConversationService.prepare_conversation_history 内完成，先跑 `before_prepare_history` 钩子再组装历史（`dispatch_prompt_history_hooks`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:120`）。
历史里没有 `SYSTEM` 轮次时才注入系统提示（`PromptTurnKind::SYSTEM`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:135`）。
系统提示后追加用户偏好文本（`USER.md:` 段），除非配置禁用了用户偏好描述（`disable_user_preference_description`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:995`）。
系统提示里的 `{{aiName}}` 与 `{aiName}` 占位符替换为 AI 名称（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:1003`）。
prepare_conversation_history 对工具结果轮次做模型侧标记归一化（`normalize_tool_result_markup_for_model`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:161`）。
准备完再跑 `after_prepare_history` 钩子，返回钩子处理后的历史（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:171`）。
助手输出没有 XML 标签时，整段内容作一个助手轮次（`PromptTurnKind::ASSISTANT`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:287`）。
状态标签含 `complete` 或 `wait_for_user_need` 类型时作助手轮次，否则作用户轮次（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:317`）。
相邻同类片段合并，工具调用与工具结果轮次不合并（`PromptTurnKind::TOOL_CALL`、`PromptTurnKind::TOOL_RESULT`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:350`）。
`getMemoryFromMessages` 从最后一条总结消息起取历史，之前的消息不进入本轮（`lastSummaryIndex`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:663`）。
总结消息在历史投影里是 `SUMMARY` 轮次（`PromptTurnKind::SUMMARY`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:701`）。
工具调用部件转为 `TOOL_CALL` 轮次，工具名保留在轮次上（`PromptTurnKind::TOOL_CALL`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:727`）。
工具结果部件转为 `TOOL_RESULT` 轮次（`PromptTurnKind::TOOL_RESULT`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:742`）。
取消后，若当前轮次要求持久化（`persistTurn`）且有已生成部分消息，经 `commitAssistantMessageSegment` 提交为助手消息段（`core/crates/runtime/application/src/services/ChatServiceCore.rs:885`）。
`steerMessage` 只引导当前逻辑轮次，不取消当前模型或工具回合（`core/crates/runtime/application/src/services/ChatServiceCore.rs:898`）。
cancelOperationForId 先取消本次操作的取消令牌（`cancellationToken`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1116`）。
取消操作随后调 `cancelConversation` 取消会话（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1132`）。

### 切换 CoreNode 的边界

switch_core 工具以 `BuiltinToolName::SwitchCore` 注册为内置工具（`core/crates/tool/services/src/tools/ToolRegistration.rs:212`）。
switch_core 工具要求 `node_id` 参数，缺失时校验失败（`core/crates/tool/services/src/tools/ToolRegistration.rs:228`）。
switch_core 目标必须能承载 Core 执行（`canExecute`），否则工具调用直接失败（`core/crates/tool/services/src/tools/ToolRegistration.rs:1567`）。
switch_core 目标必须当前可达（`reachable`），否则工具调用直接失败（`core/crates/tool/services/src/tools/ToolRegistration.rs:1573`）。
switch_core 目标不是当前设备空间成员时工具调用直接失败（`CoreNodeReferenceMatch::Unknown`）（`core/crates/tool/services/src/tools/ToolRegistration.rs:1582`）。
switch_core 目标有歧义时工具调用直接失败，并列出候选（`CoreNodeReferenceMatch::Ambiguous`）（`core/crates/tool/services/src/tools/ToolRegistration.rs:1585`）。
switch_core 的实际 Binding 移动发生在当前模型轮次结束后，工具调用时只做预检（`core/crates/tool/services/src/tools/ToolRegistration.rs:243`）。
switch_core 调用成功时返回规范节点 id（`stringResultData`、`targetNodeId`）（`core/crates/tool/services/src/tools/ToolRegistration.rs:259`）。
`beforeChangeRoute` 在 Binding 移动前检查执行归属，保留当前上下文（`core/crates/runtime/application/src/services/ChatServiceCore.rs:841`）。
beforeChangeRoute 先申请执行租约（`beginChatExecution`）再释放它（`core/crates/runtime/application/src/services/ChatServiceCore.rs:849`）。
路由变更测试断言：执行中的会话拒绝切换，`beforeChangeRoute` 返回含 Conversation is executing 的错误（`core/crates/runtime/application/src/services/ChatServiceCore.rs:3707`）。
`afterChangeRoute` 在路由变更到达目标 Core 后恢复目标会话（`core/crates/runtime/application/src/services/ChatServiceCore.rs:860`）。

### Binding 路由与模型工具循环的配合

`generateLocalLlm` 只在 Binding 归属节点上做模型推理，会话与工具各自走自己的路由（`bindingKey`）（`core/crates/runtime/application/src/services/ChatServiceCore.rs:311`）。
`callToolPkgRoute` 经普通 Binding 路由目录执行带装饰的插件方法（`ToolPkgRouteRuntime::invoke`）（`core/crates/runtime/application/src/services/ChatServiceCore.rs:328`）。
`watchToolPkgRoute` 返回被捕获的 Core 流（`ToolPkgRouteRuntime::stream`）（`core/crates/runtime/application/src/services/ChatServiceCore.rs:335`）。
`pushToolPkgRoute` 在装饰插件的所属运行时消费有类型反向流（`core/crates/runtime/application/src/services/ChatServiceCore.rs:343`）。
`toolPkgRouteHost` 在释放借用的聊天核心前克隆插件执行宿主（`core/crates/runtime/application/src/services/ChatServiceCore.rs:321`）。
`resume` 在已拥有该会话 Binding 的 CoreNode 上恢复 AI 轮次（`core/crates/runtime/application/src/services/ChatServiceCore.rs:728`）。
恢复轮次前先调 `resolveChatConfigurationForOptions` 解析该会话的执行配置（`core/crates/runtime/application/src/services/ChatServiceCore.rs:735`）。
`resumeFromRouteContext` 用随路由变更带来的 `CoreRouteResumeContext` 恢复轮次（`core/crates/runtime/application/src/services/ChatServiceCore.rs:776`）。
路由恢复先为会话申请执行租约（`beginChatExecution`），租约保存在 `executionLease` 里（`core/crates/runtime/application/src/services/ChatServiceCore.rs:805`）。
路由恢复用 `ChatConfigurationApi::ready` 解析执行配置（`core/crates/runtime/application/src/services/ChatServiceCore.rs:810`）。
路由恢复按 `ChatConfigurationPurpose::Execution` 解析配置，参与者取自路由上下文（`core/crates/runtime/application/src/services/ChatServiceCore.rs:814`）。
路由恢复把轮次交给 `sendRoutedContinuation`，并把 `executionLease` 传过去（`core/crates/runtime/application/src/services/ChatServiceCore.rs:825`）。
当配置的 `extensionOwner` 不是 `MODEL_CONFIGURATION_OWNER` 时，路由续发校验配置与执行快照的身份一致，扩展归属或参与者不符时返回错误（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:495`）。
路由续发以恢复模式发送，不把空消息记入历史（`suppressUserMessageInHistory`、`isResume`）（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:534`）。

### 切换与总结压缩

路由变更测试断言：切换不总结、不改写会话，且切换后该会话无待处理总结任务（`summaryTaskForChat` 为空）（`core/crates/runtime/application/src/services/ChatServiceCore.rs:3751`）。
`sendRoutedContinuation` 直接调用消息处理委托发送续发，不先做总结检查（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:486`）。
`prepareSummaryForSend` 在发送前启动快照压缩且不延迟发送（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:784`）。
快照压缩只在发送前检查开启且该会话无进行中总结任务时启动（`checkBeforeSend`、`summaryTaskForChat`）（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:806`）。
发送前检查用 `shouldGenerateSummary` 判断当前窗口是否达到阈值（`currentWindowSize`）（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:822`）。
达到阈值时以后台任务启动总结（`launchSummary`）（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:829`）。
回复完成后按每位参与者的配置阈值复查是否需要总结（`checkSummaryAfterReply`）（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:849`）。
`shouldGenerateSummary` 只看配置的上下文 token 阈值：开启总结、最大 token 大于 0、当前占比达到 `tokenUsageThreshold`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:647`）。
summarizeMemory 只总结上一次总结之后的消息（`lastSummaryIndex`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:547`）。
总结沿用上一次总结的正文作为前序总结（`previousSummary`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:538`）。
总结经 `generateSummaryForConfiguration` 生成（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:579`）。
总结正文后附对话回顾（`appendConversationReview`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:588`）。
对话回顾条数上限 `MAX_CONVERSATION_REVIEW_ENTRIES`（100 条），超限时保留前 `CONVERSATION_REVIEW_HEAD_ENTRIES`（30 条）与后 70 条，中间省略（总条数 − 100）条（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:40`）。
总结消息的输入 token 按正文长度乘 3/2 估算，输出 token 按正文长度除 2 估算（`estimatedInputTokens`、`estimatedOutputTokens`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:599`）。
总结消息的发送方记为 `summary`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:603`）。
总结消息的角色名是 `system`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:610`）。
总结用 `SUMMARY` 功能的模型参数与服务（`getModelParametersForFunction`、`getServiceForFunction`、`FunctionType::SUMMARY`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:438`）。
总结生成先跑 `before_prepare_summary_prompt` 钩子（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:466`）。
总结发送前跑 `before_send_to_model` 钩子（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:500`）。
总结生成后跑 `after_generate_summary` 钩子（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:571`）。
总结请求不带工具：`available_tools` 为空（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:548`）。
总结流收完后校验响应完整（`ensure_response_completed`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:558`）。
空总结通不过 `validateSummaryContent` 校验（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:875`）。
总结的 token 用量写回 Provider 模型（`updateTokensForProviderModel`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:605`）。
总结请求按 `SUMMARY_GENERATION` 来源记用量统计（`recordProviderModelRequest`、`UsageRequestSource::SUMMARY_GENERATION`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:613`）。
总结提示由 buildSummaryPreparedHistory 按系统提示、历史、总结提问三段组装（`PromptTurnKind::SYSTEM`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:869`）。
`insertSummary` 只在用户或 AI 消息处插入总结（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1407`）。
insertSummary 用 `summarizeMemory` 生成总结（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1455`）。
insertSummary 生成有效总结后经 `addSummaryMessage` 插入到选定位置（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1474`）。
`compactChat` 手动把当前会话压缩为检查点，不论阈值（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1527`）。
`compactChat` 压缩前先为目标会话申请执行租约（`beginChatExecution`）（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1532`）。
compactChat 压缩经 `manuallySummarizeConversationForChat` 执行（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1543`）。
compactChat 压缩完成后释放执行租约（`executionLease`）（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1554`）。

## 关键符号

- ChatServiceCore — 聊天服务核心，持有四个委托与服务字段（`core/crates/runtime/application/src/services/ChatServiceCore.rs:244`）
- `chatEnhancedAiServicesByChatId` — 每会话独占 AI 服务缓存（`core/crates/runtime/application/src/services/ChatServiceCore.rs:256`）
- `AIMessageManager` — 无字段的单元结构体，负责发送、摘要与取消（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:43`）
- `ChatOperationRegistry` — 按会话键保存操作，操作 id 全局递增（`nextOperationId`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:112`）
- `ConversationService` — 绑定 Provider 运行时上下文（`runtime_context`）（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:100`）
- `ToolExposureMode` — `Full` 与 `Cli` 两档，控制提示历史里暴露多少工具元数据（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:30`）
- `CoreRouteResumeContext` — 随路由变更带来的恢复上下文（`core/crates/runtime/application/src/services/ChatServiceCore.rs:776`）
- `ChatConfigurationPurpose::Execution` — 路由恢复解析配置的目的（`core/crates/runtime/application/src/services/ChatServiceCore.rs:814`）
- `BuiltinToolName::SwitchCore` — switch_core 的内置工具注册名（`core/crates/tool/services/src/tools/ToolRegistration.rs:212`）
- `resolveSwitchCoreTarget` — 解析目标节点引用（`core/crates/tool/services/src/tools/ToolRegistration.rs:1558`）
- `CoreNodeReferenceMatch::Unknown` — 目标不是设备空间成员的匹配结果（`core/crates/tool/services/src/tools/ToolRegistration.rs:1582`）
- `CoreNodeReferenceMatch::Ambiguous` — 目标有歧义的匹配结果（`core/crates/tool/services/src/tools/ToolRegistration.rs:1585`）
- `PromptTurnKind::TOOL_CALL` — 工具调用轮次（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:727`）
- `PromptTurnKind::TOOL_RESULT` — 工具结果轮次（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:742`）
- `PromptTurnKind::SUMMARY` — 总结轮次（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:701`）
- `ChatInputMenuSettings` — 设置属于执行 Core，不属于 UI 设备（`core/crates/runtime/application/src/services/ChatServiceCore.rs:121`）
- `ChatRuntime::Main` — `FOLLOW_GLOBAL` 选主运行时；`ChatRuntime::Floating` — `LOCAL_ONLY` 选悬浮运行时（`core/crates/runtime/application/src/services/ChatServiceCore.rs:262`）

## 调用链

一轮发送链：

1. sendUserMessage（路由入口）把一轮发送交给 `startUserMessage`（`core/crates/runtime/application/src/services/ChatServiceCore.rs:550`）。
2. 非续发且未处理过时，startUserMessage 派发 `SUBMIT_REQUESTED` 钩子（`core/crates/runtime/application/src/services/ChatServiceCore.rs:619`）。
3. 非续发且未处理过时，钩子放行后派发 `SUBMITTED` 钩子（`core/crates/runtime/application/src/services/ChatServiceCore.rs:654`）。
4. 取会话独占 EnhancedAIService（`core/crates/runtime/application/src/services/ChatServiceCore.rs:660`）。
5. 协调委托 `sendUserMessage`（`core/crates/runtime/application/src/services/ChatServiceCore.rs:666`）。
6. AIMessageManager.sendMessage 登记本次发送操作（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:324`）。
7. 投影历史，`promptHistoryOverride` 有值时跳过 `getMemoryFromMessages`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:351`）。
8. 裁剪媒体链接（`limitImageLinksInChatHistory`、`limitMediaLinksInChatHistory`）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:366`）。
9. 插件消息处理钩子命中时由插件执行接管（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:370`）。
10. `resume` 为真时以 `ResumeRequest` 调 `resume`，否则调 `sendMessageWithConfiguration`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:465`）。
11. 历史准备：prepare_conversation_history 跑钩子、注入系统提示、归一化工具结果轮次（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:120`）。
12. 回填：取消后，若当前轮次要求持久化（`persistTurn`）且有已生成部分消息，经 `commitAssistantMessageSegment` 提交已生成的部分消息（`core/crates/runtime/application/src/services/ChatServiceCore.rs:885`）。

切换节点链：

1. switch_core 只做预检，实际 Binding 移动发生在当前模型轮次结束后（`core/crates/tool/services/src/tools/ToolRegistration.rs:243`）。
2. 轮次结束后走 `beforeChangeRoute` 检查执行归属（`core/crates/runtime/application/src/services/ChatServiceCore.rs:841`）。
3. 到达目标 Core 后 `afterChangeRoute` 恢复目标会话（`core/crates/runtime/application/src/services/ChatServiceCore.rs:860`）。
4. 恢复时 resumeFromRouteContext 先申请执行租约（`core/crates/runtime/application/src/services/ChatServiceCore.rs:805`）。
5. 路由恢复把轮次交给 `sendRoutedContinuation`，并把 `executionLease` 传过去（`core/crates/runtime/application/src/services/ChatServiceCore.rs:825`）。

## 来源

- `core/crates/runtime/application/src/services/ChatServiceCore.rs`（3796 行，全文通读）
- `core/crates/runtime/application/src/core/chat/AIMessageManager.rs`（1929 行，全文通读）
- `core/crates/provider/services/src/chat/enhance/ConversationService.rs`（1120 行，全文通读）
- `core/crates/tool/services/src/tools/ToolRegistration.rs`（补充：switch_core 工具注册与 `resolveSwitchCoreTarget` 相关区段）
- `core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs`（补充：`sendRoutedContinuation` 与总结检查相关区段）
