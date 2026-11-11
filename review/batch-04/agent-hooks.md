---
title: Hooks
module: agent
platforms: [all]
sources: 12
date: 2026-11-11
---

## 概述

Hooks 是 ToolPkg 向应用暴露的扩展机制：每个 hook 是一次注册，记下所属包、hook 标识、函数名与函数来源，Core 在特定时机调用注册的函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:12`）。
本页覆盖三组内容：ToolPkg hook 的注册类型、聊天运行时状态 hook 的桥接、hook 超时与 SummaryHook 的关系。
本页机制位于 Core 侧 Rust 代码（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:20`）。
本页超时行为以 ToolPkgPreHookTimeout.rs 代码为准（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:12`）。

## AI 速览

- `ToolPkgHookInvocation` — 调用一个 ToolPkg hook 的完整输入（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:192`）
- `ToolPkgHookDispatcher` — 按已启用包名集合分发 hook 的 trait（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:211`）
- `decodeToolPkgHookResult` — hook 输出解码，合法 JSON 解码、其余原样返回字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:226`）
- `ToolPkgChatRuntimeHookBridge` — 聊天运行时状态 hook 桥（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:20`）
- `ToolPkgSummaryHookBridge` — 摘要 hook 桥，把 ToolPkg 摘要 hook 接入 Core 摘要管线（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:25`）
- `SummaryHookRegistry` — Core 侧摘要 hook 注册表（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:58`）
- `ToolPkgPreHookTimeout` — before-hook 共享截止时间的超时策略（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:12`）
- 主入口：`dispatchStateChanged` 派发聊天运行时状态变更通知（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:53`）
- 主入口：`dispatchSummaryGenerateHooks` 在摘要生成三阶段派发摘要 hook（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:81`）
- 数据流向（聊天运行时）：聊天执行状态变更 → `dispatchStateChanged` → 各注册 hook 的主函数（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:53`）。
- 数据流向（摘要）：摘要生成三阶段调用 `dispatchSummaryGenerateHooks`（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:81`）。
- 数据流向（摘要）：`SummaryGenerateBridge` 把 ToolPkg 摘要 hook 接入该管线（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:25`）。
- 数据流向（摘要）：变更写回 `SummaryHookContext`（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:14`）。

## 核心机制

### 注册类型

- ToolPkgHooks.rs 共定义 16 个 Registration 结构体，其中 14 个是 hook 注册，另有菜单对话框子结构与 AI Provider 注册各 1 个（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:176`）。
- 应用生命周期 hook 由 `ToolPkgAppLifecycleHookRegistration` 登记，含事件名 `event`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:9`）。
- 消息处理插件由 `ToolPkgMessageProcessingHookRegistration` 登记，以 `pluginId` 标识插件（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:20`）。
- XML 渲染插件由 `ToolPkgXmlRenderHookRegistration` 登记，以 `pluginId` 加 `tag` 标识渲染目标（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:30`）。
- 输入菜单开关插件由 `ToolPkgInputMenuToggleHookRegistration` 登记，以 `pluginId` 标识插件（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:41`）。
- 聊天输入 hook 由 `ToolPkgChatInputHookRegistration` 登记（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:51`）。
- 聊天视图 hook 由 `ToolPkgChatViewHookRegistration` 登记（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:61`）。
- 聊天消息持久化 hook 由 `ToolPkgChatMessageHookRegistration` 登记（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:71`）。
- manifest 扩展处理器由 `ToolPkgManifestExtensionRegistration` 登记，以 `extensionKey` 标识扩展键（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:81`）。
- 聊天消息上下文菜单项由 `ToolPkgChatMessageMenuItemRegistration` 登记，含 `itemId`、`title`、`icon`、`order`、`senders` 与可选 `dialog`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:103`）。
- 菜单项对话框是子结构 `ToolPkgChatMessageMenuDialogRegistration`，只含 `screen` 与 `title` 两字段（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:91`）。
- 聊天运行时状态 hook 由 `ToolPkgChatRuntimeHookRegistration` 登记（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:114`）。
- 工具生命周期 hook 由 `ToolPkgToolLifecycleHookRegistration` 登记（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:124`）。
- prompt hook 与 summary hook 共用 `ToolPkgPromptHookRegistration` 登记，文档写明该结构覆盖两者（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:134`）。
- 创建初始化器由 `ToolPkgChatLifecycleHookRegistration` 登记，文档写明 `containerPackageName` 标识真实注册包而非插件返回的 owner（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:162`）。
- 宿主来源事件 hook 由 `ToolPkgHostEventRegistration` 登记，含 `source`、`trigger` 与 `enabled` 开关（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:178`）。
- 多数 hook 注册用 `hookId` 标识一次注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:11`）。
- 消息处理、XML 渲染与输入菜单开关三类用 `pluginId` 标识插件（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:22`）。
- `ToolPkgAiProviderRegistration` 是 ToolPkg 支撑的 AI Provider 注册结构，不是 hook 注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:144`）。
- 14 个 hook 注册结构都有 `containerPackageName`、`functionName` 与可选的 `functionSource`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:12`）；菜单对话框子结构只含 `screen` 与 `title`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:91`）；AI Provider 注册 `ToolPkgAiProviderRegistration`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:144`）是四组独立方法字段 `listModelsFunctionName`/`listModelsFunctionSource`、`sendMessageFunctionName`/`sendMessageFunctionSource`、`testConnectionFunctionName`/`testConnectionFunctionSource`、`calculateInputTokensFunctionName`/`calculateInputTokensFunctionSource`，无通用函数名与函数来源（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:151`）。

### 调用输入与结果解码

- 调用一个 ToolPkg hook 的完整输入是 `ToolPkgHookInvocation`，含包名、函数名、事件、事件名、插件 id 与事件载荷（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:192`）。
- ToolPkgHookInvocation 的 `timeoutMillis` 是可选的毫秒超时（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:200`）。
- `timeoutMillis` 的文档写明它只约束显式定时的 before hook，普通 hook 等待完成（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:201`）。
- `ToolPkgHookDispatcher` 规定 `dispatchToolPkgHook` 按已启用包名集合调用一个 ToolPkg hook（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:211`）。
- `decodeToolPkgHookResult` 把 hook 输出为空或非 JSON 时原样返回字符串，合法 JSON 则解码为 JSON 值（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:226`）。
- `decodeToolPkgHookResult` 输入为 None 时返回 None（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:223`）。

### hook 结果模型

- XML 渲染 hook 的对象结果是 `ToolPkgXmlRenderHookObjectResult`，含 `handled`、`text`、`content` 与 `composeDsl`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs:22`）。
- 渲染 hook 的 Compose DSL 结果是 `ToolPkgXmlRenderHookComposeDslResult`，含 `screen`、`state`、`memo` 与 `moduleSpec`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs:10`）。
- 工具生命周期事件载荷是 `ToolPkgToolLifecycleEventPayload`，含工具名、参数、授权结果与执行结果字段（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs:34`）。
- prompt hook 的一轮对话是 `ToolPkgPromptTurn`，含 kind、内容、可选工具名与元数据（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs:55`）。
- prompt hook 的对象结果是 `ToolPkgPromptHookObjectResult`，含原始输入、处理后输入、两份历史、系统提示、工具提示与可用工具（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs:66`）。

### 聊天运行时桥接

- `ToolPkgChatRuntimeHookBridge` 的 `register` 把应用运行时存入 `CHAT_RUNTIME`，供后续分发取用（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:24`）。
- `syncToolPkgRegistrations` 从已启用容器的 `chatRuntimeHooks` 同步聊天运行时 hook 注册（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:32`）。
- 同步时每个注册的包名取容器 `packageName`，hook 标识取 hook 的 id，函数名取 hook 的 function（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:39`）。
- 各桥只注册一次，由 `INSTALLED` 原子标志保证（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgCommonBridgePlugin.rs:45`）。
- 注册时订阅包目录变更监听，目录变化时重同步全部桥的注册（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgCommonBridgePlugin.rs:58`）。
- 聊天执行状态更新的发布路径调用 `dispatchToolPkgChatRuntimeStateChange`（`core/crates/runtime/application/src/services/core/MessageProcessingDelegate.rs:1130`）。
- `dispatchToolPkgChatRuntimeStateChange` 把聊天执行状态变更交给聊天运行时桥（`core/crates/runtime/application/src/services/core/MessageProcessingDelegate.rs:1101`）。
- `dispatchStateChanged` 接收聊天 id、新状态、活跃聊天 id 与三组计数，通知经 `scheduleToolPkgNotification` 异步发出（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:58`）。
- 异步任务先取已注册的运行时，未注册时直接返回（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:69`）。
- 异步任务克隆当前注册列表，注册为空时直接返回，不执行任何 hook（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:74`）。
- 每个 hook 经 `runToolPkgMainHook` 执行，事件为 `TOOLPKG_EVENT_CHAT_RUNTIME`，事件名是 `CHAT_RUNTIME_EVENT_STATE_CHANGED`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:102`）。
- `TOOLPKG_EVENT_CHAT_RUNTIME` 的值是 toolpkg_chat_runtime（`core/crates/plugin/sdk/src/toolpkg/ToolPkgCommonPluginConstants.rs:24`）。
- `CHAT_RUNTIME_EVENT_STATE_CHANGED` 的值是 state_changed（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:17`）。
- 单个 hook 成功记 done 日志，失败记 error 日志，循环继续执行下一个 hook（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:128`）。
- 载荷的 slot 固定为 main，活跃聊天 id 先排序再装入（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:157`）。
- 载荷含状态、展示文本、工具名、进度、是否活跃、活跃聊天 id 与三组计数，时间戳取当前毫秒时间（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:163`）。
- `stateName` 把 11 种 `InputProcessingState` 映射为线名（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:174`）。
- `stateMessage` 只对带 message 字段的状态返回展示文本，其余返回 None（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:197`）。
- `stateToolName` 只对 ExecutingTool、ToolProgress、ProcessingToolResult 三种状态返回工具名（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:209`）。
- `stateProgress` 只对 ToolProgress 返回进度值（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:218`）。
- `stateIsActive` 在 Idle、Completed、Error 时为 false，其余状态为 true（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:229`）。
- 聊天运行时 hook 用不限时的 `runToolPkgMainHook` 执行，未传入超时预算（`core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs:4870`）。

### hook 超时

- before-hook 超时秒数来自持久化偏好，由 ToolPkgPreHookTimeout 的 `fromPreferences` 读取（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:13`）。
- `fromSeconds` 把秒数钳制在 1 到 60 秒之间再换算为毫秒截止时间（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:20`）。
- `ToolPkgPreHookTimeout` 跟踪一条 ToolPkg pre-hook 分发链共用的单个总截止时间（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:6`）。
- `forStage` 只对 11 个 before 阶段创建截止时间（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:30`）。
- 11 个阶段是 before_process、before_prepare_history、before_finalize_prompt、before_send_to_model、before_prepare_summary_prompt、before_compose_system_prompt、compose_system_prompt_sections、build_tool_prompt、before_compose_tool_prompt、filter_tool_prompt_items、filter_tool_call_tools（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:38`）。
- 不在名单内的阶段返回 None，不创建截止时间（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:41`）。
- 有预算时先取 `remainingForHook` 的剩余时间，再调用带毫秒超时的 `runToolPkgMainHookWithTimeoutMillis`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:61`）。
- 无预算时调用不限时的 `runToolPkgMainHook`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:79`）。
- 有预算的 hook 跑完后若共享截止时间已过，返回 `reportToolPkgHookTimeout` 的超时错误（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:75`）。
- 剩余时间为零时 `remainingForHook` 返回超时错误，链路不再启动下一个 hook（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:118`）。
- `hasExpired` 用当前毫秒时间与截止时间比较判断共享截止时间是否已过（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:126`）。

### hook 与 SummaryHook 的关系

- `SummaryHookRegistry` 是 Core 侧原生的摘要 hook 注册表，与 ToolPkg hook 注册是两套机制（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:58`）。
- `SummaryHookContext` 是摘要 hook 的上下文，含阶段、两份历史、系统提示、摘要提示与摘要结果（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:14`）。
- 摘要 hook 返回的变更经 `apply_mutation` 写回上下文，只写有值的字段（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:100`）。
- `SummaryGenerateHook` 是摘要生成 hook 的 trait，同步版默认返回 None，异步版默认转调同步版（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:43`）。
- `registerSummaryGenerateHook` 先按 id 注销同名 hook 再注册，避免重复（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:58`）。
- `dispatchSummaryGenerateHooks` 先快照当前 hook 列表再按序执行（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:81`）。
- 任一 hook 执行失败时直接返回错误，成功返回的变更立即应用（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:89`）。
- 摘要桥的 `register` 把 `SummaryGenerateBridge` 注册进 `SummaryHookRegistry`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:25`）。
- `SummaryGenerateBridge` 的 id 是 builtin.toolpkg.summary-generate-bridge（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:58`）。
- ToolPkg 摘要 hook 以一个内置 Rust hook 的身份参与 Core 摘要管线，不是独立的第二条管线（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:25`）。
- 摘要桥的同步从已启用容器的 `summaryGenerateHooks` 取注册，复用 `ToolPkgPromptHookRegistration` 结构登记（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:37`）。
- 摘要 hook 的事件名是 `TOOLPKG_EVENT_SUMMARY_GENERATE`，值是 toolpkg_summary_generate（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:95`）。
- 摘要桥按当前阶段取超时预算，偏好读取失败时直接返回错误（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:77`）。
- 摘要桥把 hook 返回值解码后只处理对象结果（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:102`）。
- 对象结果只取系统提示、摘要提示、摘要结果与元数据写回变更（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:153`）。
- 任一摘要 hook 改了内容就返回 `Some(mutation)`，否则返回 None（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:131`）。
- 摘要生成在 before_prepare_summary_prompt 阶段派发摘要 hook（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:466`）。
- 摘要生成在 before_send_to_model 阶段派发摘要 hook（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:500`）。
- 摘要生成在 after_generate_summary 阶段派发摘要 hook（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:571`）。
- before_prepare_summary_prompt 与 before_send_to_model 在超时名单内（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:30`）。
- after_generate_summary 不在名单内、不创建截止时间（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:150`）。
- JS 侧摘要 hook 对象结果是 `ToolPkgSummaryHookObjectResult`，字段与摘要上下文对应（`core/crates/plugin/sdk/src/js_sdk/toolpkg.rs:1047`）。
- 摘要机制的完整说明见 [[agent-compaction|上下文压缩与摘要]]。

## 关键符号

- `ToolPkgHookInvocation` — 调用一个 ToolPkg hook 的完整输入（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:189`）
- `ToolPkgHookDispatcher` — 按已启用包名集合分发 hook 的 trait（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:208`）
- `decodeToolPkgHookResult` — hook 输出解码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:222`）
- `ToolPkgChatRuntimeHookRegistration` — 聊天运行时状态 hook 的注册结构（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:114`）
- `ToolPkgPromptHookRegistration` — prompt hook 或 summary hook 的注册结构（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:134`）
- `ToolPkgChatRuntimeHookBridge` — 聊天运行时状态 hook 桥（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:20`）
- `ToolPkgSummaryHookBridge` — 摘要 hook 桥（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:20`）
- `SummaryHookRegistry` — Core 侧摘要 hook 注册表（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:54`）
- `SummaryHookContext` — 摘要 hook 的上下文（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:9`）
- `SummaryHookMutation` — 摘要 hook 返回的变更（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:25`）
- `ToolPkgPreHookTimeout` — before-hook 共享截止时间的超时策略（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:6`）
- `ToolPkgXmlRenderHookObjectResult` — XML 渲染 hook 的对象结果（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs:18`）
- `ToolPkgPromptHookObjectResult` — prompt hook 的对象结果（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs:62`）
- `ToolPkgToolLifecycleEventPayload` — 工具生命周期事件载荷（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs:30`）

## 调用链

### 聊天运行时状态通知

1. 聊天执行状态更新的发布路径调用 `dispatchToolPkgChatRuntimeStateChange`（`core/crates/runtime/application/src/services/core/MessageProcessingDelegate.rs:1130`）。
2. `dispatchToolPkgChatRuntimeStateChange` 把聊天执行状态变更交给聊天运行时桥（`core/crates/runtime/application/src/services/core/MessageProcessingDelegate.rs:1101`）。
3. `dispatchStateChanged` 经 `scheduleToolPkgNotification` 把通知异步发出（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:58`）。
4. 异步任务先取已注册的运行时，未注册时直接返回（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:69`）。
5. 异步任务克隆当前注册列表，注册为空时直接返回（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:74`）。
6. 逐个 hook 经 `runToolPkgMainHook` 执行，事件为 `TOOLPKG_EVENT_CHAT_RUNTIME`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:102`）。
7. 单个 hook 成功记 done 日志（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:118`）。
8. 单个 hook 失败记 error 日志，循环继续执行下一个 hook（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs:128`）。

### 摘要生成

1. 摘要生成在 before_prepare_summary_prompt 阶段派发摘要 hook（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:466`）。
2. 摘要生成在 before_send_to_model 阶段派发摘要 hook（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:500`）。
3. 摘要生成在 after_generate_summary 阶段派发摘要 hook（`core/crates/provider/services/src/chat/enhance/ConversationService.rs:571`）。
4. `dispatchSummaryGenerateHooks` 先快照当前 hook 列表再按序执行（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:81`）。
5. 摘要桥按当前阶段取超时预算（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:77`）。
6. 每个 ToolPkg 摘要 hook 经带预算的执行入口运行，事件为 `TOOLPKG_EVENT_SUMMARY_GENERATE`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:95`）。
7. hook 返回值经 `decodeToolPkgHookResult` 解码，只处理对象结果（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:102`）。
8. 对象结果只取系统提示、摘要提示、摘要结果与元数据写回变更（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:153`）。
9. 有变更返回 `Some(mutation)`，否则返回 None（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs:131`）。
10. 变更经 `apply_mutation` 写回上下文，任一 hook 失败直接返回错误（`core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs:89`）。

### before-hook 超时

1. 派发方按阶段调 `forStage` 取预算（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:28`）。
2. 有预算时用剩余时间调 `runToolPkgMainHookWithTimeoutMillis`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:61`）。
3. 跑完后检查共享截止时间，过期返回超时错误（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:75`）。
4. 剩余时间为零时不再启动下一个 hook（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:118`）。
5. 不在名单内的阶段不创建预算，不限时执行（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs:41`）。

## 来源

- core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs（seed：hook 注册类型、调用输入、结果解码）
- core/crates/plugin/sdk/src/toolpkg/ToolPkgHookModels.rs（seed：hook 结果模型）
- core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatRuntimeHookBridge.rs（seed：聊天运行时 hook 桥）
- core/crates/runtime/application/src/plugins/toolpkg/ToolPkgSummaryHookBridge.rs（补充：摘要 hook 桥）
- core/crates/provider/services/src/chat/hooks/SummaryHookRegistry.rs（补充：Core 侧摘要 hook 注册表）
- core/crates/runtime/application/src/plugins/toolpkg/ToolPkgPreHookTimeout.rs（补充：before-hook 超时策略）
- core/crates/runtime/application/src/plugins/toolpkg/ToolPkgCommonBridgePlugin.rs（补充：各桥注册与目录变更同步）
- core/crates/runtime/application/src/services/core/MessageProcessingDelegate.rs（补充：聊天运行时状态变更触发点）
- core/crates/provider/services/src/chat/enhance/ConversationService.rs（补充：摘要生成三阶段派发点）
- core/crates/plugin/sdk/src/toolpkg/ToolPkgCommonPluginConstants.rs（补充：事件常量值）
- core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs（补充：主 hook 入口与超时入口）
- core/crates/plugin/sdk/src/js_sdk/toolpkg.rs（补充：JS 侧摘要 hook 对象结果）
