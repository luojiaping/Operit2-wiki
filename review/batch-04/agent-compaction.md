---
title: 上下文压缩与摘要
module: agent
platforms: [all]
sources: [core/crates/runtime/application/src/services/ChatServiceCore.rs, core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs, core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs, core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs, core/crates/foundation/model/src/ModelConfigData.rs, core/crates/provider/services/src/chat/EnhancedAIService.rs, core/crates/runtime/application/src/core/chat/AIMessageManager.rs, core/crates/provider/services/src/chat/config/FunctionalPrompts.rs, core/crates/provider/services/src/chat/enhance/ConversationService.rs, core/crates/runtime/application/src/services/core/ChatHistoryDelegate.rs, core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs, core/crates/runtime/application/src/services/core/TokenStatisticsDelegate.rs]
date: 2026-11-11
---

## 概述

上下文压缩把过长的对话历史压缩成检查点摘要，压缩后对话以摘要为历史继续（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1524`）。
手动压缩入口是 ChatServiceCore 的 `compactChat`，未传 chatId 时取当前聊天（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1527`）。
手动压缩无视阈值，把当前聊天压缩成检查点（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1524`）。
自动压缩存在：ModelSummarySettings 默认启用摘要，默认阈值 0.85（`core/crates/foundation/model/src/ModelConfigData.rs:147`）。
2026-10-13 差距调查把自动 compaction 缺失列为 P0，HEAD 上的实现与该结论相反，自动压缩已存在且默认启用（`core/crates/foundation/model/src/ModelConfigData.rs:147`）。
自动摘要只取决于配置的上下文 token 阈值（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:646`）。
摘要 hook 在摘要生成全过程分发三阶段事件，hook 可改写提示词与结果（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:86`）。
压缩与 CoreNode 切换互不干扰：路由变更测试断言切换后不产生摘要任务（`core/crates/runtime/application/src/services/ChatServiceCore.rs:3753`）。
上下文用量显示存在：chatInputMenuSummary 返回当前窗口大小与累计 token 数（`core/crates/runtime/application/src/services/ChatServiceCore.rs:2981`）。
摘要消息的 sender 为 summary、roleName 为 system（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:608`）。

## AI 速览

- `compactChat` — 手动压缩入口（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1527`）
- `insertSummary` — 在用户或 AI 消息处插入总结（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1407`）
- `ModelSummarySettings` — 摘要开关与阈值配置（`core/crates/foundation/model/src/ModelConfigData.rs:320`）
- SummarySendPolicy — 发送前摘要策略（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:74`）
- `prepareSummaryForSend` — 发送前摘要检查（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:784`）
- checkSummaryAfterReply — 回复后摘要检查（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:859`）
- handleTokenLimitExceeded — 执行中超限处理（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1125`）
- manuallySummarizeConversationForChat — 手动摘要执行（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1055`）
- launchSummary — 摘要任务调度（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:925`）
- generateAndStoreSummary — 摘要生成与持久化（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1030`）
- AIMessageManager 的 `summarizeMemory` — 摘要内容生成（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:526`）
- AIMessageManager 的 `shouldGenerateSummary` — 阈值判断（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:650`）
- AIMessageManager 的 `getMemoryFromMessages` — 提示记忆取用（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:660`）
- SummaryHookRegistry — 摘要 hook 注册与分发（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:86`）
- `SummaryHookContext` — hook 上下文（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:10`）
- ToolPkgSummaryHookBridge — ToolPkg 摘要 hook 桥（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:60`）
- FunctionalPrompts 的 `buildSummarySystemPrompt` — 摘要系统提示词（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:159`）
- FunctionalPrompts 的 `SUMMARY_PROMPT` — 摘要指令（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:3`）
- `chatInputMenuSummary` — 上下文用量显示（`core/crates/runtime/application/src/services/ChatServiceCore.rs:2962`）
- beforeChangeRoute — 路由变更前钩子（`core/crates/runtime/application/src/services/ChatServiceCore.rs:849`）
- afterChangeRoute — 路由变更后钩子（`core/crates/runtime/application/src/services/ChatServiceCore.rs:869`）
- 主入口：`compactChat`（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1527`）
- 数据流向：消息发送 / 回复 / 执行 → 阈值检查 → 摘要生成 → 摘要消息落库 → 窗口重算。

## 核心机制

### 手动压缩

- `compactChat` 未传 chatId 时取当前聊天（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1527`）。
- `compactChat` 的文档注明手动压缩无视阈值，把当前聊天压缩成检查点（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1524`）。
- compactChat 压缩前通过 `beginChatExecution` 取执行租约（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1535`）。
- compactChat 压缩完成后调用 `release` 释放执行租约（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1555`）。
- compactChat 在 `newEnhancedAiServiceForChat` 返回空时返回 false，不执行压缩（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1538`）。
- compactChat 把压缩交给 `manuallySummarizeConversationForChat`，返回值表示是否压缩成功（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1543`）。
- manuallySummarizeConversationForChat 在 `summaryTaskForChat` 返回进行中任务时直接返回 false（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1055`）。
- manuallySummarizeConversationForChat 以 `autoContinue` 为假、`requireCurrentChat` 为假启动摘要（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1086`）。
- manuallySummarizeConversationForChat 摘要失败时把错误写入 `nonFatalErrorEventFlow`（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1097`）。
- MessageCoordinationDelegate 的 `manuallySummarizeConversation` 对当前聊天调用 `manuallySummarizeConversationForChat`（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1110`）。
- ChatServiceCore 的 `insertSummary` 只在用户或 AI 消息处插入总结，其他发送者直接失败（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1407`）。
- insertSummary 通过 `loadMessagesForSummaryInsertion` 取选中消息前后的待总结消息（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1436`）。
- insertSummary 调用 AIMessageManager 的 `summarizeMemory` 生成摘要，第三个参数传 false（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1455`）。
- insertSummary 通过 `addSummaryMessage` 持久化摘要，相邻位置已有总结时插入失败（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1474`）。
- insertSummary 插入摘要后调用 `refreshStableContextWindow` 重新计算稳定上下文窗口（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1486`）。

### 自动压缩：配置与三处触发

- `ModelSummarySettings` 含 `enableSummary` 与 `summaryTokenThreshold` 两个字段（`core/crates/foundation/model/src/ModelConfigData.rs:320`）。
- ModelSummarySettings 默认启用摘要，默认阈值 `DEFAULT_SUMMARY_TOKEN_THRESHOLD` 为 0.85（`core/crates/foundation/model/src/ModelConfigData.rs:147`）。
- ModelSummarySettings 的 `tokenThresholdRatio` 把大于 1 的旧百分比阈值除以 100，并钳制到 0 到 1（`core/crates/foundation/model/src/ModelConfigData.rs:337`）。
- 发送前摘要策略的启用条件是 `settings.enableSummary` 与 `turnOptions.persistTurn` 同时成立，禁用时阈值为 `f64::MAX`（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:74`）。
- SummarySendPolicy 的 `checkBeforeSend` 要求启用、允许发送前检查、非后台发送且未 `deferSummary`（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:80`）。
- MessageCoordinationDelegate 的 `prepareSummaryForSend` 在发送前做摘要检查（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:784`）。
- 发送前检查按 `SummarySendPolicy` 决策：`checkBeforeSend` 为真且无进行中摘要任务时才评估窗口占比（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:806`）。
- 窗口占比达到阈值时 prepareSummaryForSend 调用 `shouldGenerateSummary` 判断并启动摘要（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:822`）。
- prepareSummaryForSend 启动的摘要不阻塞发送，其完成句柄以 `let _summaryCompletion` 丢弃（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:829`）。
- 发送前摘要检查的开关在续跑、自动续跑与 resume 时为假，三个标志是 `isContinuation`、`isAutoContinuation` 与 `isResume`（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:710`）。
- MessageCoordinationDelegate 的 `checkSummaryAfterReply` 在回复后调用 recalculateStableWindowSize 重算稳定窗口（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:849`）。
- checkSummaryAfterReply 逐个参与者调用 `shouldGenerateSummary` 核对各自模型的摘要阈值（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:867`）。
- 在已准入回合完成、且回合工作要求回复后摘要（`summaryPolicy` 为 `AfterReply`，`core/crates/runtime/application/src/services/core/ChatTurnTransport.rs:69`）且结果已提交完成时，ToolRuntimeSupportService 调用 `checkSummaryAfterReply`（`core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:1047`）。
- 执行中 `usageRatio` 达到 `tokenUsageThreshold` 时记 `chat.token_limit` 日志（`core/crates/provider/services/src/chat/EnhancedAIService.rs:2364`）。
- 超限后调用 `onTokenLimitExceeded` 回调（`core/crates/provider/services/src/chat/EnhancedAIService.rs:2379`）。
- MessageCoordinationDelegate 的 `handleTokenLimitExceeded` 先等 summaryTaskForChat 返回的进行中摘要任务完成，再调用 isCurrentChatTurn 校验回合归属（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1117`）。
- handleTokenLimitExceeded 以 `autoContinue` 为真启动摘要（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1155`）。
- handleTokenLimitExceeded 压缩后调用 `sendMessageInternal` 续跑同一已提交用户回合（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1166`）。
- 续跑时原执行租约以 `Some(request.executionLease)` 传入（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1183`）。
- AIMessageManager 的 `shouldGenerateSummary` 的文档注明自动摘要只取决于配置的上下文 token 阈值（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:646`）。
- AIMessageManager 的 `shouldGenerateSummary` 在启用、`maxTokens` 大于 0 且当前 token 数占比达到 `tokenUsageThreshold` 时返回真（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:650`）。
- MessageCoordinationDelegate 的 `launchSummary` 把摘要排成名为 chat-summary 的可取消 host 任务（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:883`）。
- launchSummary 把输入处理状态置为 `Summarizing`，消息为 `chat_compressing_history`（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:918`）。
- 摘要插入位置取最新 AI 消息之后，由 `findProperSummaryPosition` 计算（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1007`）。
- generateAndStoreSummary 生成摘要后调用 `addSummaryMessage` 持久化，再调用 `refreshStableContextWindow` 重算窗口（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1030`）。
- ChatHistoryDelegate 的 `addSummaryMessage` 把摘要消息持久化到相邻消息时间戳之间（`core/crates/runtime/application/src/services/core/ChatHistoryDelegate.rs:2538`）。
- ChatHistoryDelegate 的 `findProperSummaryPosition` 返回最新 AI 消息之后的位置（`core/crates/runtime/application/src/services/core/ChatHistoryDelegate.rs:2569`）。
- ChatServiceCore 在注册委托时挂钩 `setBeforeDestructiveHistoryMutation`，破坏性历史变更前取消该聊天的摘要任务（`core/crates/runtime/application/src/services/ChatServiceCore.rs:394`）。

### 摘要生成：只总结上一次摘要之后

- summarizeMemory 只总结 `lastSummaryIndex` 之后的用户与 AI 消息，无上一次摘要时总结全部用户与 AI 消息（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:547`）。
- summarizeMemory 取上一次 `sender` 为 `summary` 的消息正文作 `previousSummary`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:535`）。
- summarizeMemory 在 `autoContinue` 为真时在摘要末尾追加如果任务尚未完成请基于以上摘要继续（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:592`）。
- summarizeMemory 生成的摘要消息 `sender` 为 `summary`，`roleName` 为 `system`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:608`）。
- 摘要消息的 token 数按字符长度估算，输入 token 数为 `estimatedInputTokens`（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:599`）。
- AIMessageManager 的 `getMemoryFromMessages` 只取上一次摘要消息起的后续消息作提示记忆（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:660`）。
- FunctionalPrompts 的 `buildSummarySystemPrompt` 把上一次摘要拼进系统提示，要求新摘要融合旧摘要信息（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:159`）。
- `FunctionalPrompts` 的 `SUMMARY_PROMPT` 要求新摘要完全取代旧摘要，成为后续对话的唯一历史参考（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:3`）。
- FunctionalPrompts 的 `boundaryWrapper` 按语言取检查点包装语（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:182`）。
- FunctionalPrompts 的 `boundaryPreservedNote` 标注检查点之后保留的最近原文（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:192`）。
- FunctionalPrompts 的 `boundaryContinue` 提供自动或交接触发压缩的续跑指令（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:202`）。

### 摘要 hook：三阶段

- `SummaryHookContext` 含 `stage`、`chat_id`、`use_english` 与 `previous_summary`（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:10`）。
- SummaryHookContext 含 `chat_history`、`prepared_history`、`system_prompt`、`summary_prompt`、`summary_result`、`model_parameters` 与 `metadata`（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:16`）。
- `SummaryGenerateHook` 要求实现 `id`，`on_event` 默认返回空（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:41`）。
- SummaryGenerateHook 的 `on_event_async` 把同步 `on_event` 适配为异步分发（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:47`）。
- SummaryHookRegistry 的 `registerSummaryGenerateHook` 按 id 先注销再注册，避免同一 hook 重复挂载（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:58`）。
- 摘要 hook 分发先对 hook 列表做 `snapshot` 再按序调用 `apply_mutation`，首个执行失败即返回（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:86`）。
- 变更应用只替换给出的字段，`metadata` 做合并（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:113`）。
- ConversationService 在 `before_prepare_summary_prompt` 阶段分发摘要 hook，此时 `prepared_history` 为空、`summary_result` 为空（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:470`）。
- before_prepare_summary_prompt 的元数据含 `providerModel` 与 `sourceMessageCount`（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:453`）。
- ConversationService 在 `before_send_to_model` 阶段分发摘要 hook，此时 `prepared_history` 已生成（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:500`）。
- before_send_to_model 的元数据追加 `preparedMessageCount`（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:513`）。
- ConversationService 在 `after_generate_summary` 阶段分发摘要 hook，此时 `summary_result` 为已生成内容（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:575`）。
- after_generate_summary 的元数据追加 `preparedMessageCount`、`inputTokens`、`cachedInputTokens` 与 `outputTokens`（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:587`）。

### ToolPkg 摘要 hook 桥

- ToolPkgSummaryHookBridge 的 hook id 为 `builtin.toolpkg.summary-generate-bridge`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:60`）。
- ToolPkgSummaryHookBridge 的 `register` 把摘要桥注册进 `SummaryHookRegistry`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:24`）。
- ToolPkgSummaryHookBridge 的 `syncToolPkgRegistrations` 从已提交的活跃包目录收集 `summaryGenerateHooks`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:32`）。
- ToolPkgSummaryHookBridge 发给 JS hook 的上下文只含标量字段与 `modelParameters`、`metadata`，不含 chat_history 与 prepared_history（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:141`）。
- ToolPkgSummaryHookBridge 只从 JS hook 结果取回 `systemPrompt`、`summaryPrompt` 与 `summaryResult`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:159`）。
- ToolPkgSummaryHookBridge 从 JS hook 结果取回 `metadata` 并合并进变更（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:167`）。
- ToolPkgSummaryHookBridge 按 `context.stage` 取每阶段超时预算，阶段前失败直接向上传播（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:77`）。
- ToolPkgSummaryHookBridge 以 `TOOLPKG_EVENT_SUMMARY_GENERATE` 事件名调用 JS hook 函数（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:95`）。

### 上下文用量显示

- `ChatInputMenuSummary` 含 `currentWindowSize`、`inputTokenCount`、`outputTokenCount` 与 `maxContextLength` 四个值（`core/crates/runtime/application/src/services/ChatServiceCore.rs:2981`）。
- chatInputMenuSummary 的 `maxContextLength` 取自已解析模型配置的 `config.context.maxContextLength`（`core/crates/runtime/application/src/services/ChatServiceCore.rs:2984`）。
- ChatServiceCore 的 `currentWindowSizeFlow` 暴露当前上下文窗口大小的状态流（`core/crates/runtime/application/src/services/ChatServiceCore.rs:3125`）。
- ChatServiceCore 的 `inputTokenCountFlow` 暴露累计输入 token 数的状态流（`core/crates/runtime/application/src/services/ChatServiceCore.rs:3133`）。
- ChatServiceCore 的 `outputTokenCountFlow` 暴露累计输出 token 数的状态流（`core/crates/runtime/application/src/services/ChatServiceCore.rs:3141`）。
- syncTokenStatisticsForCurrentChat 把 ChatHistory 的 `inputTokens`、`outputTokens`、`currentWindowSize` 同步进 `tokenStatisticsDelegate`（`core/crates/runtime/application/src/services/ChatServiceCore.rs:434`）。
- ChatServiceCore 的 `resetTokenStatistics` 清空 `UsageStatisticsStore` 的全部 token 用量记录（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1931`）。
- ChatServiceCore 的 `updateCumulativeStatistics` 为当前聊天重算累计 token 统计（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1948`）。
- 从缓存刷新活跃聊天统计时，`currentWindowSize` 被写入缓存的窗口大小并推送 `currentWindowSizeFlow`（`core/crates/runtime/application/src/services/core/TokenStatisticsDelegate.rs:74`）。

### 压缩与 CoreNode 切换的时序

- beforeChangeRoute 在路由变更前调用 `beginChatExecution` 取执行租约并立即释放，用于校验执行归属（`core/crates/runtime/application/src/services/ChatServiceCore.rs:849`）。
- afterChangeRoute 在路由到达目标 Core 后调用 `resumeFromRouteContext` 续跑（`core/crates/runtime/application/src/services/ChatServiceCore.rs:869`）。
- resumeFromRouteContext 经 sendRoutedContinuation 把路由携带的 `runtimeChatHistory` 交给续跑发送（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:521`）。
- 路由变更测试断言切换后不产生摘要任务，`summaryTaskForChat` 返回空（`core/crates/runtime/application/src/services/ChatServiceCore.rs:3753`）。
- 路由决策与跨节点调用写在 [[core-node-runtime|节点——节点运行时]]。

## 关键符号

- `compactChat` — 手动压缩入口（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1527`）
- `insertSummary` — 在用户或 AI 消息处插入总结（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1407`）
- `ModelSummarySettings` — 摘要开关与阈值配置（`core/crates/foundation/model/src/ModelConfigData.rs:320`）
- SummarySendPolicy — 发送前摘要策略（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:74`）
- `prepareSummaryForSend` — 发送前摘要检查（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:784`）
- checkSummaryAfterReply — 回复后摘要检查（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:859`）
- handleTokenLimitExceeded — 执行中超限处理（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1125`）
- manuallySummarizeConversationForChat — 手动摘要执行（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1055`）
- launchSummary — 摘要任务调度（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:925`）
- generateAndStoreSummary — 摘要生成与持久化（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1030`）
- AIMessageManager 的 `summarizeMemory` — 摘要内容生成（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:526`）
- AIMessageManager 的 `shouldGenerateSummary` — 阈值判断（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:650`）
- AIMessageManager 的 `getMemoryFromMessages` — 提示记忆取用（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:660`）
- `SummaryHookContext` — hook 上下文（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:10`）
- SummaryHookRegistry — 摘要 hook 注册与分发（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:86`）
- ToolPkgSummaryHookBridge — ToolPkg 摘要 hook 桥（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:60`）
- FunctionalPrompts 的 `buildSummarySystemPrompt` — 摘要系统提示词（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:159`）
- FunctionalPrompts 的 `SUMMARY_PROMPT` — 摘要指令（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:3`）
- `chatInputMenuSummary` — 上下文用量显示（`core/crates/runtime/application/src/services/ChatServiceCore.rs:2962`）
- beforeChangeRoute — 路由变更前钩子（`core/crates/runtime/application/src/services/ChatServiceCore.rs:849`）
- afterChangeRoute — 路由变更后钩子（`core/crates/runtime/application/src/services/ChatServiceCore.rs:869`）

## 调用链

1. 手动压缩：`compactChat` 取当前聊天（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1527`）。
2. 手动压缩：`beginChatExecution` 取执行租约（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1535`）。
3. 手动压缩：`manuallySummarizeConversationForChat` 启动摘要（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1543`）。
4. 手动压缩：launchSummary 把摘要排成 `chat-summary` 任务（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:925`）。
5. 手动压缩：generateAndStoreSummary 生成摘要并持久化（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1030`）。
6. 手动压缩：压缩完成后 `release` 释放执行租约（`core/crates/runtime/application/src/services/ChatServiceCore.rs:1555`）。
7. 发送前自动压缩：`prepareSummaryForSend` 做摘要检查（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:784`）。
8. 发送前自动压缩：`SummarySendPolicy` 决策是否评估窗口占比（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:806`）。
9. 发送前自动压缩：窗口占比达到阈值时 `shouldGenerateSummary` 判断并启动摘要（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:822`）。
10. 回复后自动压缩：在已准入回合完成、且回合工作要求回复后摘要（`summaryPolicy` 为 `AfterReply`，`core/crates/runtime/application/src/services/core/ChatTurnTransport.rs:69`）且结果已提交完成时，ToolRuntimeSupportService 调用 `checkSummaryAfterReply`（`core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:1047`）。
11. 回复后自动压缩：checkSummaryAfterReply 逐个参与者核对摘要阈值（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:867`）。
12. 执行中超限：`usageRatio` 达到 `tokenUsageThreshold` 时记 `chat.token_limit` 日志（`core/crates/provider/services/src/chat/EnhancedAIService.rs:2364`）。
13. 执行中超限：超限后调用 `onTokenLimitExceeded` 回调（`core/crates/provider/services/src/chat/EnhancedAIService.rs:2379`）。
14. 执行中超限：handleTokenLimitExceeded 以 `autoContinue` 为真启动摘要（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1155`）。
15. 执行中超限：压缩后 `sendMessageInternal` 续跑同一已提交用户回合（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1166`）。
16. 摘要生成：summarizeMemory 只总结上一次摘要之后的用户与 AI 消息（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:547`）。
17. 摘要生成：`buildSummarySystemPrompt` 把上一次摘要拼进系统提示（`core/crates/provider/services/src/chat/config/FunctionalPrompts.rs:159`）。
18. 摘要生成：三阶段 hook 分发从 `before_prepare_summary_prompt` 开始（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:470`）。
19. 摘要生成：`before_send_to_model` 阶段 `prepared_history` 已生成（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:500`）。
20. 摘要生成：`after_generate_summary` 阶段 `summary_result` 为已生成内容（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:575`）。
21. 摘要生成：`addSummaryMessage` 把摘要持久化到最新 AI 消息之后（`core/crates/runtime/application/src/services/core/ChatHistoryDelegate.rs:2538`）。
22. 摘要生成：`refreshStableContextWindow` 重算稳定上下文窗口（`core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs:1030`）。
23. 路由切换：beforeChangeRoute 取租约并立即释放，校验执行归属（`core/crates/runtime/application/src/services/ChatServiceCore.rs:849`）。
24. 路由切换：afterChangeRoute 调用 `resumeFromRouteContext` 续跑（`core/crates/runtime/application/src/services/ChatServiceCore.rs:869`）。

## 来源

- `core/crates/runtime/application/src/services/ChatServiceCore.rs`
- `core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs`
- `core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs`
- `core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs`
- `core/crates/foundation/model/src/ModelConfigData.rs`
- `core/crates/provider/services/src/chat/EnhancedAIService.rs`
- `core/crates/runtime/application/src/core/chat/AIMessageManager.rs`
- `core/crates/provider/services/src/chat/config/FunctionalPrompts.rs`
- `core/crates/provider/services/src/chat/enhance/ConversationService.rs`
- `core/crates/runtime/application/src/services/core/ChatHistoryDelegate.rs`
- `core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs`
- `core/crates/runtime/application/src/services/core/TokenStatisticsDelegate.rs`
