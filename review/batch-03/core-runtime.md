---
title: Runtime 总览与 OperitApplication
module: core
platforms: [all]
sources: 5
date: 2026-11-11
---

## 概述

Runtime 域拥有核心业务服务与应用级运行时行为（`core/crates/runtime/README.md:3`）。
Runtime 域包含聊天运行时、偏好设置、工作区、面向 Host 的运行时服务、传输、插件宿主与运行时事件（`core/crates/runtime/README.md:5`）。
README 要求 Runtime 只向节点运行时暴露窄的本地能力，不自行创建节点或访问服务（`core/crates/runtime/README.md:7`）。
基线时 Runtime 域只有一个 application crate，README 把 application 称为当前聚合运行时 crate（`core/crates/runtime/README.md:11`）。
同一份 README 把 contracts、chat、preferences、workspace、host、transfer、plugin-host、events 与 application 共 9 个 crate 列为目标布局（`core/crates/runtime/README.md:13`）。
application crate 包含 OperitApplication、聊天服务、工作区服务、Provider 与工具运行时支持、插件运行时支持、运行时事件服务（`core/crates/runtime/README.md:11`）。
OperitApplication 是拥有进程级运行时初始化并暴露面向 Host 的应用操作的结构体（`core/crates/runtime/application/src/core/application/OperitApplication.rs:118`）。
AIMessageManager 是无字段的单元 struct，负责聊天消息的发送、摘要与取消（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:43`）。
CORE_VERSION 是编译进 runtime crate 的 Cargo 包版本，供 CoreNode 兼容检查使用（`core/crates/runtime/application/src/lib.rs:10`）。

## AI 速览

- OperitApplication — 进程级运行时初始化与面向 Host 的应用操作入口
- newWithContext(HostManager) — 主入口：安装 Host 默认值并组装各子 crate 服务
- onCreate() — 启动入口：初始化存储、工具、插件与运行时事件
- CORE_VERSION — 编译进 runtime crate 的 Cargo 包版本，供 CoreNode 兼容检查使用
- coreVersion() — 返回 CORE_VERSION
- AIMessageManager — 聊天消息发送、摘要与取消的无状态入口
- ChatOperationRegistry — 按聊天键登记进行中的发送操作，操作 id 递增
- sendMessage(SendMessageRequest) — 聊天发送主入口
- getMemoryFromMessages — 聊天记录转 Provider 回合
- shouldGenerateSummary — 自动摘要触发条件
- summarizeMemory — 生成摘要消息
- dispatchPluginLoading — 插件初始加载
- syncClock / syncClockDigest — 同步时钟收据与摘要
- ThemePreviewAsset / ThemePreviewReceipt — 主题预览的内存资产与回执
- 主入口函数：OperitApplication::newWithContext → OperitApplication::onCreate
- 数据流向：HostManager → newWithContext 组装服务 → onCreate 初始化 → dispatchPluginLoading 加载包与 MCP → AIMessageManager::sendMessage 发送消息

## 核心机制

### 组装：newWithContext

newWithContext 接收一个 HostManager 并安装共享 Host 默认值（`core/crates/runtime/application/src/core/application/OperitApplication.rs:141`）。
runtimeStorageHost 已提供但其 runtimeRootDir() 失败时，newWithContext 用 expect 直接 panic（`core/crates/runtime/application/src/core/application/OperitApplication.rs:145`）。
newWithContext 中 runtimeStorageHost 已提供而缺失 FileSystemHost 时用 expect 直接 panic（`core/crates/runtime/application/src/core/application/OperitApplication.rs:152`）。
runtimeStorageHost 已提供时，newWithContext 把日志文件解析为 /operitapp/data/logs/operit.log 与 /operitapp/data/logs/toolpkg.log（`core/crates/runtime/application/src/core/application/OperitApplication.rs:159`）。
日志文件配置失败时只记警告，应用继续使用控制台与内存日志（`core/crates/runtime/application/src/core/application/OperitApplication.rs:167`）。
HostManager 携带对应 Host 时，newWithContext 把 runtimeStorageHost、runtimeSqliteHost、hostSecretStore 注册为进程级默认值（`core/crates/runtime/application/src/core/application/OperitApplication.rs:183`）。
HostManager 携带 httpHost 与 webSocketHost 时，newWithContext 把两者注册为默认值（`core/crates/runtime/application/src/core/application/OperitApplication.rs:189`）。
newWithContext 无条件把 GitHub 登录 token 源注册为默认值（`core/crates/runtime/application/src/core/application/OperitApplication.rs:191`）。
HostManager 携带 serviceDiscoveryHost 与 httpServerHost 时，newWithContext 把两者注册为默认值（`core/crates/runtime/application/src/core/application/OperitApplication.rs:196`）。
HostManager 携带 tcpHost、serialPortHost 与 hostRuntimeTaskSchedulerHost 时，newWithContext 把三者注册为默认值（`core/crates/runtime/application/src/core/application/OperitApplication.rs:203`）。
开启 javascript 特性时，newWithContext 要求 HostManager 提供 HostJavaScriptRuntimeHost，缺失时 expect 直接 panic（`core/crates/runtime/application/src/core/application/OperitApplication.rs:215`）。
开启 javascript 特性时，工具运行时依赖使用 HostJsExecutionProvider 作为 JS 执行提供方（`core/crates/runtime/application/src/core/application/OperitApplication.rs:229`）。
FileSystemHost 缺失时，newWithContext 在 chatFileSystemHost 处用 expect 直接 panic（无条件）（`core/crates/runtime/application/src/core/application/OperitApplication.rs:220`）。
newWithContext 创建 ToolRuntimeSupportService 作为运行时工具支持（`core/crates/runtime/application/src/core/application/OperitApplication.rs:225`）。
newWithContext 创建 AIToolHandler、ToolPkgBridgeRuntime 与 ProviderRuntimeSupportService，分别作为工具处理器、ToolPkg 桥运行时与 Provider 运行时上下文（`core/crates/runtime/application/src/core/application/OperitApplication.rs:233`）。
newWithContext 把工具运行时服务绑定到工具处理器与 Provider 运行时上下文，且只绑定一次，重复绑定时 expect 报错（`core/crates/runtime/application/src/core/application/OperitApplication.rs:237`）。
newWithContext 用带运行时依赖的 ChatRuntimeHolder 替换初始 holder，并把其主聊天记录管理器绑定给工具运行时支持，同样只绑定一次（`core/crates/runtime/application/src/core/application/OperitApplication.rs:247`）。
OperitApplication::new() 使用默认 Android 风格 Host 上下文创建应用（`core/crates/runtime/application/src/core/application/OperitApplication.rs:135`）。
OperitApplication 的 Default 实现直接调用 new()（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1489`）。
sharedCoreCommandRuntime 共享同一批服务供命令使用，不创建第二个运行时或生命周期（`core/crates/runtime/application/src/core/application/OperitApplication.rs:271`）。
sharedCoreCommandRuntime 返回的副本不持有 extensionChanges 与 hostRuntimeEventRegistration，原始应用仍是唯一的生命周期与订阅持有者（`core/crates/runtime/application/src/core/application/OperitApplication.rs:284`）。
setHostManager 把 HostManager 存入 HOST_MANAGER 静态变量（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1457`）。
hostManager() 静态方法返回启动后全局注册的 HostManager，未初始化时 panic（`core/crates/runtime/application/src/core/application/OperitApplication.rs:953`）。

### 启动与生命周期：onCreate

onCreate 首先记录 appStartupTimeMs 并把 HostManager 存入进程级静态变量（`core/crates/runtime/application/src/core/application/OperitApplication.rs:341`）。
runtimeStorageHost 存在时，onCreate 调用 PreferenceSpaceMerge::prepareLayout 准备偏好布局，失败时只记错误日志不中断启动（`core/crates/runtime/application/src/core/application/OperitApplication.rs:345`）。
onCreate 先配置 OpenMP 环境再清理退出时删除文件，清理失败时返回错误中断启动（`core/crates/runtime/application/src/core/application/OperitApplication.rs:353`）。
cleanOnExitFiles 清理 /operitapp/data/temp/clean_on_exit 下的文件（`core/crates/runtime/application/src/core/application/OperitApplication.rs:293`）。
onCreate 依次初始化 WorkManager、AIMessageManager、JSON 序列化器、应用语言与 Android 权限偏好（`core/crates/runtime/application/src/core/application/OperitApplication.rs:363`）。
onCreate 打开 AppDatabase、迁移主题外观并预加载数据库（`core/crates/runtime/application/src/core/application/OperitApplication.rs:372`）。
onCreate 调用 toolHandler.registerDefaultTools 注册默认工具（`core/crates/runtime/application/src/core/application/OperitApplication.rs:387`）。
onCreate 初始化内置插件并注册 ToolPkg 聊天生命周期钩子桥（`core/crates/runtime/application/src/core/application/OperitApplication.rs:397`）。
onCreate 向 ToolPkg 派发 TOOLPKG_EVENT_APPLICATION_ON_CREATE 应用创建事件（`core/crates/runtime/application/src/core/application/OperitApplication.rs:407`）。
onCreate 启动 Host 运行时事件支持并保存其注册句柄（`core/crates/runtime/application/src/core/application/OperitApplication.rs:419`）。
onCreate 启动 ExtensionRuntimeService 并调度插件加载（`core/crates/runtime/application/src/core/application/OperitApplication.rs:431`）。
onCreate 启动 ModelCatalogService 的持续保鲜并把 initialized 置为 true（`core/crates/runtime/application/src/core/application/OperitApplication.rs:436`）。
configureOpenMpEnvironment 与 ensureWorkManagerInitialized 在本 seed 内是空实现（`core/crates/runtime/application/src/core/application/OperitApplication.rs:460`）。
initializeJsonSerializer、initializeAppLanguage 与 initAndroidPermissionPreferences 在本 seed 内是空实现（`core/crates/runtime/application/src/core/application/OperitApplication.rs:472`）。
preloadDatabase 在本 seed 内是空实现（`core/crates/runtime/application/src/core/application/OperitApplication.rs:480`）。
runtimeFileSystem 在缺少 RuntimeStorageHost 时返回错误（`core/crates/runtime/application/src/core/application/OperitApplication.rs:306`）。
ingestRuntimeEvent 把一个归一化 Host 事件交给 RuntimeEventIngressService 派发给已注册的 ToolPkg Host 事件钩子（`core/crates/runtime/application/src/core/application/OperitApplication.rs:450`）。

### CORE_VERSION 与节点兼容检查

CORE_VERSION 是编译进 runtime crate 的 Cargo 包版本，定义为 env!("CARGO_PKG_VERSION")（`core/crates/runtime/application/src/lib.rs:11`）。
CORE_VERSION 的文档注释写明其用途是供 CoreNode 兼容检查使用（`core/crates/runtime/application/src/lib.rs:10`）。
coreVersion 返回编译进 runtime crate 的 CORE_VERSION（`core/crates/runtime/application/src/core/application/OperitApplication.rs:884`）。
兼容检查的实现不在本页 seed 内，检查逻辑在节点运行时侧，见 [[core-node-runtime|节点——节点运行时]]。
application crate 的 lib.rs 声明 R、core、data、plugins、services、ui 六个顶层模块（`core/crates/runtime/application/src/lib.rs:4`）。
lib.rs 把 AIMessageManager 与 EnhancedAIService 重导出到 crate 根（`core/crates/runtime/application/src/lib.rs:12`）。
R.rs 只有一行，定义空 struct R（`core/crates/runtime/application/src/R.rs:1`）。

### 插件加载：dispatchPluginLoading

initMcpPlugins 直接调用 dispatchPluginLoading（`core/crates/runtime/application/src/core/application/OperitApplication.rs:485`）。
dispatchPluginLoading 先认领初始包注册表加载，已被认领时直接返回 Ok（`core/crates/runtime/application/src/core/application/OperitApplication.rs:493`）。
dispatchPluginLoading 在缺少 hostRuntimeTaskSchedulerHost 时把 readiness 标记为失败并返回错误（`core/crates/runtime/application/src/core/application/OperitApplication.rs:501`）。
插件启动任务以 operit-plugin-startup 为名提交给 Host 运行时任务调度器（`core/crates/runtime/application/src/core/application/OperitApplication.rs:537`）。
插件启动任务先调用 loadAvailablePackages 再要求 readiness 就绪，失败时标记 readiness 失败并记错误日志（`core/crates/runtime/application/src/core/application/OperitApplication.rs:518`）。
插件启动任务用 MCPStarter::startAllDeployedPluginsWithTimeout 启动已部署插件，超时秒数取自 ApiPreferences::getMcpStartupTimeoutSeconds（`core/crates/runtime/application/src/core/application/OperitApplication.rs:528`）。
pluginLoadingProgressFlow 返回包与插件加载进度流（`core/crates/runtime/application/src/core/application/OperitApplication.rs:548`）。
skipPluginLoading 隐藏加载遮罩但不停止加载会话（`core/crates/runtime/application/src/core/application/OperitApplication.rs:553`）。
packageManager 返回工具处理器拥有的共享包管理器（`core/crates/runtime/application/src/core/application/OperitApplication.rs:749`）。
active_package_names 返回本应用运行时中启用的包名（`core/crates/runtime/application/src/core/application/OperitApplication.rs:822`）。
mcpRepository 用本运行时 Host 与工具支持创建 MCPRepository（`core/crates/runtime/application/src/core/application/OperitApplication.rs:566`）。
skillRepository 用本运行时 Host 与工具支持创建 SkillRepository（`core/crates/runtime/application/src/core/application/OperitApplication.rs:619`）。
包工具与 MCP 工具的执行与管理见 [[core-tool-packages-mcp|工具包与 MCP 运行时]]。

### 聊天发送：AIMessageManager::sendMessage

AIMessageManager::initialize 初始化 ACTIVE_CHAT_OPERATIONS 与 LAST_ACTIVE_CHAT_KEY（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:212`）。
无 chatId 的发送使用默认聊天键 __DEFAULT_CHAT__（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:37`）。
sendMessage 把本次发送登记进 ChatOperationRegistry 并分配递增的操作 id；无 chatId 时聊天键取默认值（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:321`）。
ChatOperationRegistry::register 用 checked_add 递增操作 id，溢出时 expect 报错（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:130`）。
ChatOperationRegistry 的 get_mut 与 remove 只在 operationId 匹配时操作，避免旧清理删掉新发送（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:140`）。
sendMessage 在 promptHistoryOverride 给定时直接用它，否则从聊天记录经 getMemoryFromMessages 生成记忆（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:349`）。
sendMessage 把历史中的图片与媒体链接上限取值自 ApiPreferences，流无值时分别缺省 2 与 1 个用户回合（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:360`）。
sendMessage 先问 MessageProcessingPluginRegistry 是否有匹配的消息处理插件（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:370`）。
插件匹配时 sendMessage 直接返回插件执行流并结束本次操作，不调用 Provider（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:394`）。
sendMessage 的流式开关取自 ApiPreferences 的 disableStreamOutput，缺省为 false 即开启流式（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:403`）。
预发送钩子等待期间操作被取消时，sendMessage 返回 RequestCancelled（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:456`）。
resume 为 true 时 sendMessage 调用 EnhancedAIService::resume，否则调用 sendMessageWithConfiguration（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:465`）。
Provider 返回流后先登记到操作记录，未登记成功时关闭流并返回 RequestCancelled（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:483`）。
响应清理以 ai-message-manager-response-cleanup 为名提交给 Host 任务调度器，收完流后结束操作（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:495`）。
清理任务提交失败时取消本次操作并返回 RequestFailed（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:503`）。
test_model_connection 使用 providerRuntimeContext 测试一个模型连接（`core/crates/runtime/application/src/core/application/OperitApplication.rs:834`）。

### 用户消息内容：buildUserMessageContent

buildUserMessageContent 先经 InputProcessor::process_user_input 处理用户输入（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:223`）。
buildUserMessageContent 在 proxySenderName 非空且正文不含 proxy_sender 标记时追加 proxy_sender 标签（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:244`）。
buildUserMessageContent 在 workspacePath 非空且正文不含 workspace_attachment 标记时追加 workspace_attachment 标签（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:266`）。
buildUserMessageContent 经 buildReplyTag 为回复消息生成 reply 标签（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:255`）。
buildReplyTag 把回复内容截断到 100 字符并加省略号（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:769`）。
buildUserMessageContent 过滤掉空白部分后用空格连接成最终内容（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:296`）。
buildRecordedUserMessageContent 只序列化原始用户输入，不选参与者、不调模型、不改写已提交文本（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:301`）。

### 附件标记：buildAttachmentTag

buildAttachmentTag 对有 VFS 定位的同步附件先在本地解析物理路径并核对存在性与大小（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:805`）。
非本节点附件直接返回普通 attachment 标签，不读文件 Host（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:816`）。
直接图片附件失败时记错误日志并回退为普通附件，不中止整次发送（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:833`）。
直接音频附件经 buildDirectMediaAttachmentTag 生成媒体链接（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:853`）。
直接视频附件经 buildDirectMediaAttachmentTag 生成媒体链接（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:861`）。
直接图片附件注册要求 FileSystemHost，读不到字节或文件为空时报错（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:893`）。
图片池返回 imageId 为 error 时直接图片附件注册失败（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:904`）。
附件属性含 id、filename、type，nodeId 非空时加 node_id（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:975`）。
工具路径以 /app/、/operitapp/、/mnt/、/virtual/ 开头时附件属性加 path，fileSize 大于 0 时加 size（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:986`）。

### 历史投影与摘要

getMemoryFromMessages 从最后一条 summary 消息起取相关消息，无 summary 时取全部消息（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:663`）。
getMemoryFromMessages 把 sender 为 summary 的消息转为 SUMMARY 回合（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:701`）。
labelUserMessages 开启时，getMemoryFromMessages 给用户消息加 [From user] 前缀（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:696`）。
isolateParticipants 开启时，getMemoryFromMessages 按持久化参与者 id 区分己方与他人消息，他人发言转为 [From role: 名字] 的用户回合（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:685`）。
isolateParticipants 开启时，AI 消息缺持久化作者或缺展示身份时 getMemoryFromMessages 返回错误（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:678`）。
applyConfigurationIdentity 给 sender 为 ai 的消息写入 host.chat.identity（配置档案名与头像 URI），其余 sender 移除该键（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:198`）。
applyConfigurationIdentity 在 extensionOwner 键下写入 participantId（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:206`）。
assistantPromptTurnsFromParts 把 Markdown、Thinking、Status 部分累积为 ASSISTANT 回合，遇到 ToolCall 时先 flush 已累积文本（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:716`）。
ToolCall 部分转为带 tool_name 的 TOOL_CALL 回合（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:727`）。
ToolResult 部分转为带 tool_name 的 TOOL_RESULT 回合（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:740`）。
shouldGenerateSummary 要求开启摘要、maxTokens 大于 0 且当前 token 占比达到 tokenUsageThreshold（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:653`）。
summarizeMemory 只汇总上一次 summary 之后的用户与 AI 消息（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:552`）。
待汇总消息为空时 summarizeMemory 返回 Ok(None)（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:560`）。
summarizeMemory 在 autoContinue 为 true 时在摘要后追加中文继续句（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:592`）。
summarizeMemory 的输入 token 估算为摘要长度乘 3 除 2（至少 1），输出 token 估算为最终摘要长度除 2（至少 1）（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:599`）。
summarizeMemory 返回 sender 为 summary 的 ChatMessage（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:603`）。
对话回顾条目上限为 100 条，其中头部保留 30 条（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:40`）。
appendConversationReview 把对话回顾上限控制在 100 条：超限时保留前 30 条与后 70 条，中间省略并注明条数（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1215`）。
cleanSummarySourceMessage 去掉 meta 标签、AI 消息的 think 内容与媒体链接（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1243`）。
condenseAssistantMessageForReview 丢弃 Thinking 部分（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1292`）。
condenseAssistantMessageForReview 超过 25 段时只保留前 12 段与后 10 段并注明省略段数（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1359`）。
calculateStableContextWindow 经 getMemoryFromMessages 生成记忆后调用 estimateRequestWindowFromMemory 估算窗口（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:627`）。

### 取消

cancelCurrentOperation 取消最近活跃聊天的操作（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1082`）。
cancelOperation 把空 chatId 当作默认聊天键（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1091`）。
cancelOperationForId 先从注册表取走操作，无操作时直接返回 Ok（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1108`）。
取消时立即调用 cancellationToken.cancel()（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1116`）。
取消时关闭 operation.responseStream（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1130`）。
取消最后调用 enhancedAiService.cancelConversation 并返回其结果（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1132`）。
cancelAllOperations 快照当前全部操作并逐个按 id 取消（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1152`）。
cancelAllOperations 把各聊天的取消错误用分号连接后返回（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:1160`）。

### 同步入口

syncClock 返回 protocolVersion 1、consistencyVersion 7 与 stateSummary 摘要（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1003`）。
syncClock 还返回待处理操作数与 id、待传 blob 与错误列表（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1008`）。
syncClockDigest 返回 protocolVersion 1 与同步摘要（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1049`）。
syncOperationsSince 从 clock JSON 读取 includeProgress 标志并校验 receipt（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1058`）。
syncApplyOperations 先经 RuntimeFileSyncStore 把文件类操作水合为原始操作，失败的记入 errors 并列入 deferred（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1093`）。
syncApplyOperations 把操作接收进 journal 后应用待处理操作（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1104`）。
syncApplyOperations 最后发布已应用变更（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1112`）。
syncApplyImmediateBindingOperation 对单个路由传输的 Binding 操作直接应用，不移动持久同步时钟（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1121`）。
refreshSynchronizedChatFlows 对有活跃本地流的聊天记 chat_flow_skip 并跳过（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1214`）。
refreshSynchronizedChatFlows 对无活跃本地流的聊天调用 refreshChatMessagesFromPersistence 刷新（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1234`）。
dispatchSynchronizedChatDeletions 在缺少任务调度 Host 时返回错误（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1247`）。
syncBlobExists 检查本地 blob 是否存在而不读内容，保留各文件的独立失败（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1273`）。
syncReadBlobChunk 读取一个有界同步 blob 分块供传给另一 CoreNode（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1286`）。
runtimeSyncOperationStore 用 RUNTIME_SYNC_DIR_PATH 创建本应用实例拥有的持久同步操作存储（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1364`）。
runtimeBindingStore 创建本应用实例拥有的 Binding 存储（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1376`）。
runtimeNetworkControlStore 创建本应用实例拥有的同步 Space 授权与控制存储（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1385`）。
runtimeFileSyncStore 创建本应用实例拥有的内容寻址运行时文件存储（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1408`）。
pluginSqliteHost 要求已注册的运行时 SQLite Host，用于插件存储同步（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1420`）。
applyNonPreferenceSyncOperation 只处理 RUNTIME_FILE_SYNC_DOMAIN 下 file 实体的 upsert 与 delete 操作（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1436`）。
applyNonPreferenceSyncOperation 对其他域、实体或操作返回 unsupported sync operation 错误（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1447`）。
synchronizationDataset 按域解析数据集：聊天走 synchronizedChatId，插件存储走 PluginStorage::syncDatasetPath，网络控制走 spaceId，其余用 (entityType, entityId)（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1467`）。
synchronizedChatId 只在 CHAT_SYNC_DOMAIN 下返回聊天 id；message 实体按冒号切分出聊天 id（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1483`）。

### 扩展、市场与主题预览

getExtensionCatalogSnapshot 返回一份归一化本地扩展目录快照（`core/crates/runtime/application/src/core/application/OperitApplication.rs:634`）。
getExtensionScopes 按 kind 分 package 与 skill 等类别处理（`core/crates/runtime/application/src/core/application/OperitApplication.rs:664`）。
getExtensionScopes 对 package、skill、mcp、a2a 之外的 kind 返回 Unknown extension kind 错误（`core/crates/runtime/application/src/core/application/OperitApplication.rs:674`）。
extensionCatalogRevisionFlow 观测本地操作与设备空间同步带来的扩展目录变更（`core/crates/runtime/application/src/core/application/OperitApplication.rs:625`）。
checkExtensionCatalogUpdates 把已安装市场条目与最新发布版本对照检查（`core/crates/runtime/application/src/core/application/OperitApplication.rs:640`）。
deleteExtensionCatalogDiagnostic 在重新设计的卡片确认后删除一条包管理器诊断（`core/crates/runtime/application/src/core/application/OperitApplication.rs:648`）。
inputMenuToggleBridge 创建由本应用工具包运行时支撑的输入菜单桥（`core/crates/runtime/application/src/core/application/OperitApplication.rs:728`）。
chatComposerSlotBridge 创建由 Host 组合的聊天输入框槽位桥（`core/crates/runtime/application/src/core/application/OperitApplication.rs:734`）。
themeConfigManager 在缺少 RuntimeStorageHost 时返回错误（`core/crates/runtime/application/src/core/application/OperitApplication.rs:741`）。
importA2AConfig 把可移植 A2A 连接定义导入扩展与包注册表（`core/crates/runtime/application/src/core/application/OperitApplication.rs:572`）。
getA2AConfig 读取已保存的连接清单供编辑或导出（`core/crates/runtime/application/src/core/application/OperitApplication.rs:580`）。
discoverA2AAgent 在用户保存连接前获取并校验 Agent Card（`core/crates/runtime/application/src/core/application/OperitApplication.rs:587`）。
setA2AEnabled 通过规范的归属记录启用或禁用已安装的 A2A 包（`core/crates/runtime/application/src/core/application/OperitApplication.rs:595`）。
deleteA2A 删除 A2A 安装并移除其包工具（`core/crates/runtime/application/src/core/application/OperitApplication.rs:603`）。
invokeA2A 执行已安装包的工具所用的同一批 A2A 操作（`core/crates/runtime/application/src/core/application/OperitApplication.rs:611`）。
getInstalledMarketVersions 返回仍已安装插件的市场条目与版本标记（`core/crates/runtime/application/src/core/application/OperitApplication.rs:805`）。
installMarketEntry 安装市场条目并把成功安装的版本持久化进 Core（`core/crates/runtime/application/src/core/application/OperitApplication.rs:811`）。
installMarketArtifact 拒绝含 / 或 \ 或不是纯文件名的文件名（`core/crates/runtime/application/src/core/application/OperitApplication.rs:763`）。
installMarketArtifact 要求 SHA-256 为 64 位十六进制字符，输入先统一转小写再校验（`core/crates/runtime/application/src/core/application/OperitApplication.rs:774`）。
installMarketArtifact 先调用 prepareMarketArtifactDownload 准备下载目标（`core/crates/runtime/application/src/core/application/OperitApplication.rs:784`）。
installMarketArtifact 下载产物文件后以归一化 SHA-256 登记产物文件（`core/crates/runtime/application/src/core/application/OperitApplication.rs:791`）。
checkApplicationUpdate 使用 ApplicationUpdateManager 与 systemOperationHost 检查应用更新（`core/crates/runtime/application/src/core/application/OperitApplication.rs:849`）。
applicationUpdateProgressFlow 观测 Host 下载进度而不暴露 URL 或原生文件路径（`core/crates/runtime/application/src/core/application/OperitApplication.rs:854`）。
downloadApplicationUpdate 下载选定版本并返回不透明原生回执（`core/crates/runtime/application/src/core/application/OperitApplication.rs:860`）。
installApplicationUpdate 在 Core 内解析回执并经本地 Host 准备安装（`core/crates/runtime/application/src/core/application/OperitApplication.rs:872`）。
ThemePreviewAsset 是只交给预览界面的内存资产，不是库记录，预览 API 从不写入它（`core/crates/runtime/application/src/core/application/OperitApplication.rs:76`）。
ThemePreviewAsset 的 bytes 经 serde_bytes 以 MessagePack 二进制穿越 CoreLink 边界（`core/crates/runtime/application/src/core/application/OperitApplication.rs:85`）。
ThemePreviewReceipt 携带校验回执、theme_id、version、theme_json 与 assets，不带选择或持久化结果（`core/crates/runtime/application/src/core/application/OperitApplication.rs:93`）。
previewThemeArchive 只把 preview.png 与 assets/ 下的文件收进预览资产（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1307`）。
previewToolPkgTheme 要求模板由该 ToolPkg 声明，否则返回 Theme template is not declared by this ToolPkg 错误（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1340`）。
validateThemeArchive 在归档中按 theme_id 查找模板，找不到时返回 Selected theme template is not declared by this ToolPkg 错误（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1355`）。
单元测试 preview_asset_bytes_use_messagepack_binary 校验主题预览资产可转为 CoreValue 映射（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1505`）。
该测试断言 bytes 字段转为 CoreValue::Bytes（`core/crates/runtime/application/src/core/application/OperitApplication.rs:1511`）。

### 日志与目录

logEntries 与 logText 分别返回内存中的应用日志条目与日志文件文本（`core/crates/runtime/application/src/core/application/OperitApplication.rs:892`）。
packageLogText 返回包管理器日志文件文本（`core/crates/runtime/application/src/core/application/OperitApplication.rs:902`）。
logFilePath 与 packageLogFilePath 返回两个日志文件路径（`core/crates/runtime/application/src/core/application/OperitApplication.rs:910`）。
operitRootPath 返回用户可见的 Operit 根目录路径并确保目录存在（`core/crates/runtime/application/src/core/application/OperitApplication.rs:920`）。
exportsPath 返回导出用户产物的目录路径并确保目录存在（`core/crates/runtime/application/src/core/application/OperitApplication.rs:928`）。
cleanOnExitPath 返回退出时清理维护所用文件的目录路径并确保目录存在（`core/crates/runtime/application/src/core/application/OperitApplication.rs:936`）。
messageTimingNow 记录当前毫秒时间戳（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:171`）。
logMessageTiming 按“阶段 耗时=Nms”记录阶段耗时（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:181`）。

## 关键符号

- OperitApplication — 进程级运行时初始化与面向 Host 的应用操作入口（`core/crates/runtime/application/src/core/application/OperitApplication.rs:119`）。
- newWithContext(HostManager) — 安装 Host 默认值并组装服务的主入口（`core/crates/runtime/application/src/core/application/OperitApplication.rs:141`）。
- onCreate() — 启动入口：初始化存储、工具、插件与运行时事件（`core/crates/runtime/application/src/core/application/OperitApplication.rs:340`）。
- HOST_MANAGER — 进程级 HostManager 静态变量（`core/crates/runtime/application/src/core/application/OperitApplication.rs:104`）。
- CORE_VERSION — 编译进 runtime crate 的 Cargo 包版本（`core/crates/runtime/application/src/lib.rs:11`）。
- coreVersion() — 返回 CORE_VERSION（`core/crates/runtime/application/src/core/application/OperitApplication.rs:884`）。
- AIMessageManager — 聊天消息发送、摘要与取消的无状态入口（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:43`）。
- ChatOperationRegistry — 按聊天键登记进行中的发送操作（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:112`）。
- ActiveChatOperation — 同一次发送的取消句柄与响应流（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:105`）。
- SendMessageRequest — 发送请求结构（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:66`）。
- ToolRuntimeDependencies — 工具运行时依赖（含 JS 执行提供方）（`core/crates/runtime/application/src/core/application/OperitApplication.rs:123`）。
- ToolPkgBridgeRuntime — ToolPkg 桥运行时（`core/crates/runtime/application/src/core/application/OperitApplication.rs:125`）。
- ProviderRuntimeContext — Provider 运行时上下文（`core/crates/runtime/application/src/core/application/OperitApplication.rs:126`）。
- dispatchPluginLoading — 插件初始加载（`core/crates/runtime/application/src/core/application/OperitApplication.rs:489`）。
- ThemePreviewAsset — 主题预览的内存资产（`core/crates/runtime/application/src/core/application/OperitApplication.rs:80`）。
- ThemePreviewReceipt — 主题预览阶段回执（`core/crates/runtime/application/src/core/application/OperitApplication.rs:93`）。

## 调用链

应用启动链：
1. OperitApplication::new() 使用默认 Android 风格 Host 上下文创建应用（`core/crates/runtime/application/src/core/application/OperitApplication.rs:135`）。
2. newWithContext 安装 Host 默认值并创建 ToolRuntimeSupportService、AIToolHandler、ToolPkgBridgeRuntime、ProviderRuntimeSupportService（`core/crates/runtime/application/src/core/application/OperitApplication.rs:233`）。
3. newWithContext 把工具运行时服务绑定到工具处理器与 Provider 运行时上下文，且只绑定一次（`core/crates/runtime/application/src/core/application/OperitApplication.rs:237`）。
4. onCreate 记录 appStartupTimeMs 并把 HostManager 存入进程级静态变量（`core/crates/runtime/application/src/core/application/OperitApplication.rs:341`）。
5. onCreate 在 runtimeStorageHost 存在时准备偏好布局（失败只记日志），清理退出时删除文件（失败返回错误中断启动），打开数据库并注册默认工具（`core/crates/runtime/application/src/core/application/OperitApplication.rs:387`）。
6. onCreate 初始化内置插件并派发 TOOLPKG_EVENT_APPLICATION_ON_CREATE 事件（`core/crates/runtime/application/src/core/application/OperitApplication.rs:407`）。
7. onCreate 启动 Host 运行时事件支持、ExtensionRuntimeService 并调度插件加载（`core/crates/runtime/application/src/core/application/OperitApplication.rs:431`）。
8. dispatchPluginLoading 认领初始加载并以 operit-plugin-startup 为名提交异步任务（`core/crates/runtime/application/src/core/application/OperitApplication.rs:537`）。
9. 异步任务加载可用包并启动已部署的 MCP 插件（`core/crates/runtime/application/src/core/application/OperitApplication.rs:528`）。
10. onCreate 启动 ModelCatalogService 的持续保鲜并把 initialized 置为 true（`core/crates/runtime/application/src/core/application/OperitApplication.rs:436`）。

聊天发送链：
1. AIMessageManager::sendMessage 把本次发送登记进 ChatOperationRegistry 并分配递增的操作 id（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:321`）。
2. sendMessage 从聊天记录经 getMemoryFromMessages 生成记忆，或直接使用 promptHistoryOverride（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:349`）。
3. sendMessage 把历史中的图片与媒体链接上限取值自 ApiPreferences，流无值时分别缺省 2 与 1 个用户回合（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:360`）。
4. sendMessage 先问 MessageProcessingPluginRegistry 是否有匹配的消息处理插件，匹配时直接返回插件执行流（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:394`）。
5. sendMessage 按 resume 标志调用 EnhancedAIService::resume 或 sendMessageWithConfiguration（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:465`）。
6. Provider 返回流后先登记到操作记录，未登记成功时关闭流并返回 RequestCancelled（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:483`）。
7. 响应清理以 ai-message-manager-response-cleanup 为名提交给 Host 任务调度器，收完流后结束操作（`core/crates/runtime/application/src/core/chat/AIMessageManager.rs:495`）。

## 来源

- `core/crates/runtime/README.md`
- `core/crates/runtime/application/src/lib.rs`
- `core/crates/runtime/application/src/core/application/OperitApplication.rs`
- `core/crates/runtime/application/src/core/chat/AIMessageManager.rs`
- `core/crates/runtime/application/src/R.rs`
