---
title: Runtime——业务服务
module: core
platforms: [all]
sources: [core/crates/runtime/application/src/services/ChatServiceCore.rs, core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs, core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs, core/crates/runtime/application/src/services/RuntimeTerminalService.rs]
date: 2026-11-11
---

# Runtime——业务服务

## 概述

本页写 `core/crates/runtime/application/src/services/` 下的四个服务：聊天核心 `ChatServiceCore`（core/crates/runtime/application/src/services/ChatServiceCore.rs:238）、Provider 支持 `ProviderRuntimeSupportService`（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:27）、工具支持 `ToolRuntimeSupportService`（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:49）、终端服务 `RuntimeTerminalService`（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:67）。
`ChatServiceCore` 是聊天回合的执行入口：收用户消息、跑提交钩子、驱动模型与工具回合、管理聊天历史与工作区（core/crates/runtime/application/src/services/ChatServiceCore.rs:238）。
`ProviderRuntimeSupportService` 与 `ToolRuntimeSupportService` 是两座桥：把 provider crate 与 tools crate 要的接口接到 runtime 自有的管理器与注册表上（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:27、core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:49）。
`RuntimeTerminalService` 是宿主终端 API 的外观：PTY 会话的创建、输入、输出流与退出码都经它走（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:67）。
浏览器服务不在本页 4 个 seed 文件中，本页不写浏览器挂接。
四个服务同属 runtime application 层，与 [[core-runtime|Runtime 总览与 OperitApplication]] 的应用组装互补：本页只写服务本身的实现，不写应用启动时的装配顺序。

## AI 速览

- `ChatServiceCore` — 聊天回合的执行入口，持有三个 delegate 与每聊天一个 `EnhancedAIService`（core/crates/runtime/application/src/services/ChatServiceCore.rs:243）
- `MessageProcessingDelegate` — 消息处理状态，由 `ChatServiceCore` 持有并分发给协调 delegate（core/crates/runtime/application/src/services/ChatServiceCore.rs:244）
- `ChatHistoryDelegate` — 聊天历史操作，由 `ChatServiceCore` 持有（core/crates/runtime/application/src/services/ChatServiceCore.rs:245）
- `MessageCoordinationDelegate` — 回合协调，由 `ChatServiceCore` 在 `initializeDelegates` 里新建（core/crates/runtime/application/src/services/ChatServiceCore.rs:389）
- `ChatConfigurationApi` — 聊天配置解析入口，插件后端可选，原生模型路径独立可用（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:48）
- `MODEL_CONFIGURATION_OWNER` — 内置模型会话归属常量，值为 `host.chat.model`（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:37）
- `RuntimeProviderSupport` — `ProviderRuntimeSupport` trait 的 runtime 实现（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:439）
- `RuntimeToolSupport` — `ToolRuntimeSupport` trait 的 runtime 实现（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:77）
- `RuntimeTerminalService` — 宿主终端 API 的外观（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:67）
- `ChatState` — 一次聊天运行时的状态快照：标题、工作区、加载态、待发队列、工具权限请求（core/crates/runtime/application/src/services/ChatServiceCore.rs:178）
- `PendingChatQueueState` — 一次聊天的待发消息队列状态（core/crates/runtime/application/src/services/ChatServiceCore.rs:197）
- `ChatInputMenuSettings` — 输入框行为设置：权限模式、流式开关、画像描述开关、插件开关（core/crates/runtime/application/src/services/ChatServiceCore.rs:121）
- `ChatPluginPage` — 插件列表一页：条目加总数（core/crates/runtime/application/src/services/ChatServiceCore.rs:151）
- `ChatPluginDetails` — 一个插件的有界详情：描述、工具名、偏移与总数（core/crates/runtime/application/src/services/ChatServiceCore.rs:158）
- `RuntimeTerminalSessionInfo` — 已发布的终端会话元数据（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:24）
- `RuntimeTerminalScreen` — 宿主返回的当前终端屏幕快照（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:37）
- 主入口：`sendUserMessage`（core/crates/runtime/application/src/services/ChatServiceCore.rs:537）
- 主入口：`ChatConfigurationApi` 的 `ready`（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:55）
- 主入口：`ToolRuntimeSupportService::create`（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:53）
- 主入口：`RuntimeTerminalService::getInstance`（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:256）
- 数据流向：用户消息 → 提交钩子 → MessageCoordinationDelegate → EnhancedAIService → 模型与工具回合（core/crates/runtime/application/src/services/ChatServiceCore.rs:580）

## 核心机制

`ChatServiceCore::new` 按 `ChatSelectionMode` 决定 `chatInputRuntime`：`FOLLOW_GLOBAL` 用 `ChatRuntime::Main`，`LOCAL_ONLY` 用 `ChatRuntime::Floating`（core/crates/runtime/application/src/services/ChatServiceCore.rs:261）。
`initializeDelegates` 新建 `ChatHistoryDelegate`、`MessageProcessingDelegate` 与 `MessageCoordinationDelegate`（core/crates/runtime/application/src/services/ChatServiceCore.rs:389）。
`initializeChatConfiguration` 首次调用恢复持久化历史并缓存结果，重复调用直接返回缓存结果（core/crates/runtime/application/src/services/ChatServiceCore.rs:407）。
`initializeChatConfiguration` 成功后置 `initialized` 为 true（core/crates/runtime/application/src/services/ChatServiceCore.rs:413）。
`newEnhancedAiServiceForChat` 按 chatId 返回独立的 `EnhancedAIService` 实例并缓存（core/crates/runtime/application/src/services/ChatServiceCore.rs:351）。
`sendUserMessage` 是带 `operit_core_route` 的公开发送入口，binding 为 `chatIdOverride`（core/crates/runtime/application/src/services/ChatServiceCore.rs:537）。
`sendUserMessage` 转交给 `startUserMessage` 执行（core/crates/runtime/application/src/services/ChatServiceCore.rs:550）。
`sendUserMessageStream` 要求显式空提交块加 EOF，中断上传不得把已收前缀变成聊天消息（core/crates/runtime/application/src/services/ChatServiceCore.rs:557）。
`sendUserMessageStream` 先经 `chat_input_stream::receive` 收齐流式文本再调用 `sendUserMessage`（core/crates/runtime/application/src/services/ChatServiceCore.rs:573）。
`startUserMessage` 要求 `admittedLease`、`deferSequenceCompletion`、`nativeExecutionId` 三者一致，否则返回错误（core/crates/runtime/application/src/services/ChatServiceCore.rs:580）。
`startUserMessage` 在提交前先派发 `CHAT_INPUT_EVENT_SUBMIT_REQUESTED` 钩子（core/crates/runtime/application/src/services/ChatServiceCore.rs:616）。
提交钩子返回 `BLOCK` 或 `CONSUME` 时本轮不进入生成，`CONSUME` 对应 outcome `Consumed`，`BLOCK` 对应 outcome `Blocked`（core/crates/runtime/application/src/services/ChatServiceCore.rs:624）。
提交钩子返回 `REPLACE` 或 `ALLOW` 时继续执行，`REPLACE` 用决策文本替换原消息文本（core/crates/runtime/application/src/services/ChatServiceCore.rs:638）。
`startUserMessage` 在 `SUBMIT_REQUESTED` 之后还派发 `CHAT_INPUT_EVENT_SUBMITTED` 钩子（core/crates/runtime/application/src/services/ChatServiceCore.rs:652）。
`generateLocalLlm` 只在 Binding 归属节点做模型推理，对话与工具走各自的路由（core/crates/runtime/application/src/services/ChatServiceCore.rs:311）。
`resume` 在已拥有聊天的 CoreNode 上恢复 AI 回合（core/crates/runtime/application/src/services/ChatServiceCore.rs:728）。
`resumeFromRouteContext` 用路由变更携带的 `CoreRouteResumeContext` 恢复目标聊天（core/crates/runtime/application/src/services/ChatServiceCore.rs:776）。
`beforeChangeRoute` 在路由变更前开启执行租约并立即释放以校验执行归属（core/crates/runtime/application/src/services/ChatServiceCore.rs:841）。
`afterChangeRoute` 把恢复交给 `resumeFromRouteContext`（core/crates/runtime/application/src/services/ChatServiceCore.rs:870）。
`cancelMessage` 取消指定聊天的消息生成，`persistTurn` 为真时提交已生成的部分消息（core/crates/runtime/application/src/services/ChatServiceCore.rs:874）。
`steerMessage` 在不取消当前模型或工具回合的前提下引导进行中的逻辑回合（core/crates/runtime/application/src/services/ChatServiceCore.rs:898）。
`enqueuePendingQueueMessage` 向指定聊天的待发消息队列追加一条消息并置 `wasBlocked` 为 true（core/crates/runtime/application/src/services/ChatServiceCore.rs:906）。
`takeNextPendingQueueMessageIfReady` 仅当聊天未在处理、队列曾被阻塞且未被抑制时取出下一条排队消息（core/crates/runtime/application/src/services/ChatServiceCore.rs:976）。
`restorePendingQueueMessage` 把被拒绝的排队消息插回所属聊天队列头部（core/crates/runtime/application/src/services/ChatServiceCore.rs:1006）。
`setPendingQueueExpanded` 更新指定聊天待发消息队列在界面上的展开状态（core/crates/runtime/application/src/services/ChatServiceCore.rs:1022）。
`chatConfiguration` 只解析通用展示身份、有序参与者与插件初始化数据（core/crates/runtime/application/src/services/ChatServiceCore.rs:1115）。
`chatConfigurationForMessage` 按消息的配置归属解析模型与语音回放用的消息作者（core/crates/runtime/application/src/services/ChatServiceCore.rs:1142）。
`chatConfigurationForParticipant` 精确解析指定执行参与者，解析出的 profile 与请求不一致且归属不是 `MODEL_CONFIGURATION_OWNER` 时返回错误（core/crates/runtime/application/src/services/ChatServiceCore.rs:1181）。
`deleteChatHistory` 删除会话前先取消破坏性变更中的消息生成并删除待发队列（core/crates/runtime/application/src/services/ChatServiceCore.rs:1229）。
`compactChat` 手动把当前聊天压缩为检查点，不论阈值是否达到（core/crates/runtime/application/src/services/ChatServiceCore.rs:1527）。
`insertSummary` 仅在用户或 AI 消息处插入总结，其他发送者返回失败（core/crates/runtime/application/src/services/ChatServiceCore.rs:1407）。
`rollbackToMessage` 仅当目标消息是用户消息时回滚聊天到该消息（core/crates/runtime/application/src/services/ChatServiceCore.rs:1806）。
`rewindAndResendMessage` 回滚用户消息后用编辑内容作为新回合重新发送（core/crates/runtime/application/src/services/ChatServiceCore.rs:1837）。
`regenerateSingleAiMessage` 原地重新生成一条 AI 消息，保留周围聊天历史（core/crates/runtime/application/src/services/ChatServiceCore.rs:1882）。
`handleAttachment` 按前缀分发粘贴文本与粘贴图片附件（core/crates/runtime/application/src/services/ChatServiceCore.rs:1960）。
`handleAttachment` 收到 `screen_capture`、`notifications_capture`、`location_capture` 时分别做屏幕 OCR、通知与位置捕获（core/crates/runtime/application/src/services/ChatServiceCore.rs:1976）。
`handleAttachment` 用 `PACKAGE_ATTACHMENT_PREFIX` 与 `WORKSPACE_MENTION_ATTACHMENT_PREFIX` 分发包附件与工作区引用附件（core/crates/runtime/application/src/services/ChatServiceCore.rs:1988）。
`chatAvailablePlugins` 只列出已启用且包名不超过 108 字符的插件容器（core/crates/runtime/application/src/services/ChatServiceCore.rs:2787）。
`chatAvailablePlugins` 的 items 用 `take(6)` 截取，每页返回 6 个插件（core/crates/runtime/application/src/services/ChatServiceCore.rs:2801）。
`chatPluginDetails` 的 tools 用 `take(3)` 截取，每页返回 3 个工具名（core/crates/runtime/application/src/services/ChatServiceCore.rs:2832）。
`chatPluginStatus` 只运行插件自有的诊断导出，不做只读模块存在检查（core/crates/runtime/application/src/services/ChatServiceCore.rs:2840）。
`chatPluginStatus` 的 `testKind` 缺省为 `connection`，对应 `test_connection`；`tool` 对应 `test_tool_call`（core/crates/runtime/application/src/services/ChatServiceCore.rs:2852）。
`chatMessagesWindowFlow` 按消息索引分页显示窗口，不传输完整历史或工具负载（core/crates/runtime/application/src/services/ChatServiceCore.rs:2645）。
`chatMessagesWindowFlow` 向前翻页时一次加载 14 条消息（core/crates/runtime/application/src/services/ChatServiceCore.rs:2649）。
`chatImagePreviewChunk` 先校验图片归属再返回图像预览分块，格式仅支持 `rgb565le`（core/crates/runtime/application/src/services/ChatServiceCore.rs:2675）。
`authorizeChatImage` 仅当图片 id 被本聊天的消息引用且长度不超过 80 字符时才授权（core/crates/runtime/application/src/services/ChatServiceCore.rs:3545）。
`localChatStateFlow` 用 `combine5` 合并执行状态、显示窗口状态、文件上下文、待发队列与工具权限请求五路流（core/crates/runtime/application/src/services/ChatServiceCore.rs:3054）。
`ChatConfigurationApi` 的 `ready` 加载可选插件后端，不把插件就绪作为聊天前提（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:55）。
`extensionOwner` 无插件时返回 `MODEL_CONFIGURATION_OWNER`，有插件时返回插件归属（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:87）。
`pluginConfiguration` 以 `CONFIGURATION_TIMEOUT_MILLIS` 为限调用插件公开 API，失败后禁用插件并回退（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:94）。
`CONFIGURATION_TIMEOUT_MILLIS` 为 10_000 毫秒（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:319）。
`resolveDisplay` 先尝试插件解析，失败则用 `modelDisplay` 做原生展示（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:130）。
`resolve` 在 `participantId` 为 `model:chat` 时跳过插件，直接走原生模型执行路径（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:147）。
`resolveContextParticipants` 在无指定参与者且有插件时逐参与者解析上下文配置，任一参与者解析出的上下文键或 profile 与展示不一致时禁用插件并整体回退原生路径；解析调用本身出错则直接返回错误（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:159）。
`updateBinding` 只在有插件时调用插件方法，无插件时直接返回 `Ok`（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:232）。
`updateBinding` 要求插件返回 `{acknowledgement:true}`，否则返回错误（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:241）。
`modelProfile` 要求默认 TTS 配置 id 非空，否则返回错误（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:248）。
`modelProfile` 生成的参与者 id 为 `model:chat`，名称为解析出的模型 id（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:258）。
`modelProfile` 生成的参与者 `toolAccess` 关闭，内置工具、包、技能、MCP 服务器清单均为空（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:268）。
`nativeModelExecution` 生成 `schemaVersion` 为 1 的原生执行数据，`historyPolicy` 两项均为 false（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:300）。
`decodeDisplayConfigurationResult` 拒绝插件提供的 `extensionOwner` 字段，归属只由运行时指定（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:336）。
`decodeConfigurationResult` 拒绝插件提供的 `extensionOwner` 字段，归属只由运行时指定（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:359）。
`selectChatConfigurationOwner` 无候选时返回 `MODEL_CONFIGURATION_OWNER`，唯一候选时返回该候选，多候选时报错（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:379）。
`selectChatConfigurationOwner` 拒绝插件注册冒用 `MODEL_CONFIGURATION_OWNER`（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:380）。
`validateModelExecutionData` 要求 `schemaVersion` 为 1、`contextKey` 与 profile id 均为 `model:chat`、名称等于模型绑定模型 id、单一参与者、resources 与三段提示词均为空（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:408）。
`validateNativeModelExecutionData` 还要求 `participantId` 与保存的 profile id 一致（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:420）。
`RuntimeProviderSupport::generateLocalLlm` 经 `LocalLlmService` 做本地推理，`bindingKey` 为空时先调用 `ensureLocalLlmBinding`（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:465）。
`RuntimeProviderSupport::resolveChatConfiguration` 在异步任务中经 `ChatConfigurationApi` 解析持久化聊天上下文（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:551）。
`RuntimeProviderSupport::loadCodexTokens` 返回保存的 ChatGPT Codex 会话，未保存时返回错误（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:614）。
`bindRuntimeServices` 绑定工具处理器与 provider 运行时上下文，重复绑定返回错误（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:90）。
`bindChatHistoryManager` 捕获与聊天 delegate 共享的规范记录管理器，重复绑定返回错误（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:104）。
`bindDeviceToolRuntime` 安装设备工具运行时，重复初始化返回错误（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:138）。
`executeDeviceTool` 在设备工具路由未初始化时返回失败结果而不 panic（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:145）。
`bindCoreNodeToolRuntime` 安装外部 Core 代理提供的实时路由能力（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:155）。
`coreNodeRouteState` 从已安装的外部 Core 代理读取当前路由状态，未安装时返回错误（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:166）。
`bindCoreRouteChangeHandler` 安装归属 Core 应用提供的路由变更控制器，重复绑定返回错误（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:178）。
`requestCoreRouteChange` 经已安装的控制器请求路由变更，未绑定时返回错误（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:192）。
`synthesizeSpeech` 经 `TtsSynthesisService` 按配置合成语音，未指定配置时用当前 TTS 配置（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:229）。
`speakSpeech` 按解析出的系统语音配置朗读，`interrupt` 缺省为 true，`pitch` 缺省为 1.0（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:245）。
`speakSpeech` 经 `TtsPlaybackService` 播放，播放前用 `TtsCleaner` 清洗文本（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:249）。
`transcribeSpeech` 经 `SttRecognitionService` 转录语音，未指定配置时用当前配置（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:266）。
`listTtsConfigs` 读取全部真实配置语音记录，不参考角色偏好（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:276）。
`applyThemeConfig` 只应用确切存在的命名主题，id 为空或含首尾空白时返回错误（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:295）。
`setCurrentTtsConfigId` 写入当前语音 id，要求 id 为确切非空文本（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:312）。
`readToolSourceCatalog` 读取四类真实工具来源注册表：内置工具、包、技能、MCP 服务器（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:333）。
`startChatServices` 启动父级聊天服务，取 MAIN 与 FLOATING 两个核心（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:632）。
`stopChatServices` 停止父级聊天服务并清空核心与计数器（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:640）。
`openPluginChatMessage` 准入恰好一次已认证发送并拥有其生成、最终收据与清理（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:774）。
`requestPluginChatCancellation` 同步捕获归属以便排队取消不指向后续执行（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:817）。
`sendChatMessage` 在 Holder 之外调用权威提交钩子，只等待发起回合的实际提交收据（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:845）。
`callChatModel` 直接调用配置的功能模型，不记入聊天历史（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:909）。
`RuntimeTerminalService::getInstance` 要求 `TerminalHost` 已配置，否则 panic（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:256）。
`startTerminalPty` 启动 PTY 终端会话并挂接输出流（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:301）。
`startTerminalPty` 在 `enterTerminalDirectory` 失败时关闭已建会话并返回错误（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:336）。
`terminalPtyOutput` 返回指定 PTY 会话的共享输出流（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:347）。
`writeTerminalPty` 向 PTY 会话写入 base64 解码后的字节并返回写入字节数（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:353）。
`closeTerminalPty` 关闭 PTY 会话并移除其输出流，随后重新发布会话快照（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:381）。
`inputTerminalSession` 向终端会话发送文本输入并返回接受的字符数（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:392）。
`getTerminalSessionScreen` 读取终端会话的当前屏幕内容（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:401）。
`ensureTerminalPtyOutputStream` 复用已有输出流，不为同一会话重复创建读取器（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:421）。
PTY 输出流用 `MutableSharedStreamImpl::new(512)` 创建，共享缓冲容量为 512（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:428）。
`start_terminal_pty_output_reader` 每轮轮询后等 `waitForHostRuntimeDelay(40)`，即 40 毫秒（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:202）。
`poll_terminal_pty_output` 在退出码出现后先排空最后到达的字节再关闭流（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:213）。
`resolve_terminal_working_dir` 对 `/app`、`/operitapp`、`/mnt`、`/virtual` 路径走 VFS 解析，其余路径走宿主原生解析（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:451）。

## 关键符号

- `ChatServiceCore` — 聊天回合的执行入口（core/crates/runtime/application/src/services/ChatServiceCore.rs:238）
- `ChatState` — 一次聊天运行时的状态快照（core/crates/runtime/application/src/services/ChatServiceCore.rs:178）
- `ChatInputMenuSettings` — 输入框行为设置（core/crates/runtime/application/src/services/ChatServiceCore.rs:121）
- `ChatInputMenuSummary` — 输入框摘要：窗口大小与 token 计数（core/crates/runtime/application/src/services/ChatServiceCore.rs:131）
- `ChatPluginPage` — 插件列表一页（core/crates/runtime/application/src/services/ChatServiceCore.rs:151）
- `ChatPluginDetails` — 一个插件的有界详情（core/crates/runtime/application/src/services/ChatServiceCore.rs:158）
- `PendingChatQueueState` — 一次聊天的待发消息队列状态（core/crates/runtime/application/src/services/ChatServiceCore.rs:197）
- `PendingChatQueueStore` — 在各聊天 surface 间共享待发消息队列（core/crates/runtime/application/src/services/ChatServiceCore.rs:215）
- `ChatServiceUiBridge` — 聊天服务 UI 桥 trait，当前实现为空桥（core/crates/runtime/application/src/services/ChatServiceCore.rs:88）
- `EmptyChatServiceUiBridge` — 空的 UI 桥实现（core/crates/runtime/application/src/services/ChatServiceCore.rs:90）
- `sendUserMessage` — 公开发送入口（core/crates/runtime/application/src/services/ChatServiceCore.rs:537）
- `startUserMessage` — 内部发送管线：钩子、队列、delegate（core/crates/runtime/application/src/services/ChatServiceCore.rs:580）
- `recordOnlySequenceInput` — 只提交原始输入的序列入口（core/crates/runtime/application/src/services/ChatServiceCore.rs:675）
- `finishNativeChatSequence` — 校验收据后发布序列级完成（core/crates/runtime/application/src/services/ChatServiceCore.rs:706）
- `chatConfiguration` — 解析通用展示配置（core/crates/runtime/application/src/services/ChatServiceCore.rs:1115）
- `chatConfigurationForMessage` — 按消息归属解析消息作者配置（core/crates/runtime/application/src/services/ChatServiceCore.rs:1142）
- `chatConfigurationForParticipant` — 精确解析指定执行参与者（core/crates/runtime/application/src/services/ChatServiceCore.rs:1181）
- `ProviderRuntimeSupportService` — 创建 provider 运行时服务的工厂（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:27）
- `MODEL_CONFIGURATION_OWNER` — 内置模型会话归属常量（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:37）
- `ChatConfigurationApi` — 聊天配置解析入口（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:48）
- `ChatConfigurationPlugin` — 可选插件配置后端（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:42）
- `RuntimeProviderSupport` — `ProviderRuntimeSupport` trait 的 runtime 实现（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:439）
- `CONFIGURATION_TIMEOUT_MILLIS` — 插件配置调用时限 10_000 毫秒（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:319）
- `nativeModelExecution` — 生成原生模型执行数据（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:300）
- `validateNativeModelExecutionData` — 校验原生模型执行数据与参与者身份（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:420）
- `ToolRuntimeSupportService` — 创建 tools 运行时服务的工厂（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:49）
- `RuntimeToolSupport` — `ToolRuntimeSupport` trait 的 runtime 实现（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:77）
- `RuntimeToolBindings` — 绑定到 runtime 支持实例的工具处理器与 provider 上下文（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:67）
- `bindRuntimeServices` — 绑定工具处理器与 provider 运行时上下文（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:90）
- `bindChatHistoryManager` — 捕获共享的规范记录管理器（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:104）
- `bindDeviceToolRuntime` — 安装设备工具运行时（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:138）
- `bindCoreNodeToolRuntime` — 安装外部 Core 代理的实时路由能力（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:155）
- `bindCoreRouteChangeHandler` — 安装路由变更控制器（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:178）
- `synthesizeSpeech` — 经 `TtsSynthesisService` 合成语音（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:223）
- `speakSpeech` — 经 `TtsPlaybackService` 朗读（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:235）
- `transcribeSpeech` — 经 `SttRecognitionService` 转录语音（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:264）
- `openPluginChatMessage` — 准入一次已认证的插件发送（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:774）
- `sendChatMessage` — 工具侧发送聊天消息的入口（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:845）
- `callChatModel` — 直接调用功能模型（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:909）
- `RuntimeTerminalService` — 宿主终端 API 的外观（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:67）
- `RuntimeTerminalSessionInfo` — 已发布的终端会话元数据（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:24）
- `RuntimeTerminalScreen` — 当前终端屏幕快照（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:37）
- `RuntimeTerminalTypeInfo` — 一个可创建的终端类型（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:50）
- `RuntimeTerminalInfo` — 活跃宿主暴露的全部终端类型（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:59）
- `RuntimeTerminalPtyOutputStream` — 暴露 PTY 输出给 Kotlin 风格收集器的流包装（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:73）
- `startTerminalPty` — 启动 PTY 终端会话（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:301）
- `terminalPtyOutput` — 返回 PTY 会话的共享输出流（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:347）
- `getMimeTypeFromPath` — 按扩展名返回 MIME 类型（core/crates/runtime/application/src/services/ChatServiceCore.rs:3421）
- `authorizeChatImage` — 校验图片归属后授权预览（core/crates/runtime/application/src/services/ChatServiceCore.rs:3545）

## 调用链

1. 用户发消息 → `sendUserMessage` → `startUserMessage`（core/crates/runtime/application/src/services/ChatServiceCore.rs:537）。
2. `startUserMessage` 派发 `CHAT_INPUT_EVENT_SUBMIT_REQUESTED` 钩子：`BLOCK`/`CONSUME` 拦截本轮，`REPLACE`/`ALLOW` 继续执行（core/crates/runtime/application/src/services/ChatServiceCore.rs:616）。
3. `startUserMessage` 再派发 `CHAT_INPUT_EVENT_SUBMITTED` 钩子，然后把回合交给 `MessageCoordinationDelegate`（core/crates/runtime/application/src/services/ChatServiceCore.rs:652）。
4. 协调 delegate 用按 chatId 缓存的 `EnhancedAIService` 跑模型与工具回合（core/crates/runtime/application/src/services/ChatServiceCore.rs:351）；收据经 `finishNativeChatSequence` 校验后发布（core/crates/runtime/application/src/services/ChatServiceCore.rs:706）。
5. 配置解析：`ChatConfigurationApi` 的 `ready`（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:55）找公开 API 为 `chat.configuration.resolve`（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:67）的插件后端；有插件时走插件解析，失败或无插件时走原生模型路径。
6. 原生模型路径：`modelProfile` 生成 id 为 `model:chat` 的参与者，`nativeModelExecution` 生成 `schemaVersion` 为 1 的执行数据（core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs:300）。
7. 路由变更：`beforeChangeRoute` 开启并释放执行租约，`afterChangeRoute` 经 `resumeFromRouteContext` 在目标 Core 恢复（core/crates/runtime/application/src/services/ChatServiceCore.rs:841）。
8. 工具侧发送：`RuntimeToolSupport::sendChatMessage` 在 Holder 之外跑权威提交钩子，再调 `ChatServiceCore::startUserMessage` 并等待提交收据（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:845）。
9. 插件发送：`openPluginChatMessage` 准入一次已认证发送，异步任务跑回合并做最终收据与租约清理（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:774）。
10. 语音合成：`synthesizeSpeech` → `TtsSynthesisService`；朗读：`speakSpeech` → `TtsPlaybackService`；转录：`transcribeSpeech` → `SttRecognitionService`（core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs:223）。
11. 终端：`getInstance` 取宿主 `TerminalHost`（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:256），`startTerminalPty` 建会话并挂输出流（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:301）。
12. 终端输入输出：`terminalPtyOutput` 读输出（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:347）、`writeTerminalPty` 写输入（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:353）。
13. 终端退出：`pollTerminalPtyExit` 查退出码（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:373）、`closeTerminalPty` 关闭（core/crates/runtime/application/src/services/RuntimeTerminalService.rs:381）。
14. 状态聚合：`localChatStateFlow` 用 `combine5` 合并执行状态、显示窗口状态、文件上下文、待发队列、工具权限请求，产出 `ChatState`（core/crates/runtime/application/src/services/ChatServiceCore.rs:3054）。

## 来源

- `core/crates/runtime/application/src/services/ChatServiceCore.rs`（3796 行）
- `core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs`（894 行）
- `core/crates/runtime/application/src/services/ToolRuntimeSupportService.rs`（1321 行）
- `core/crates/runtime/application/src/services/RuntimeTerminalService.rs`（578 行）
