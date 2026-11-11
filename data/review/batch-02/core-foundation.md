---
title: 基础层——共享契约与数据模型
module: core
platforms: [android, ohos, windows, linux, macos, ios, web, esp32]
sources: [core/crates/foundation/README.md, core/crates/foundation/host-api/src/lib.rs, core/crates/foundation/host-api/src/HostManager.rs, core/crates/foundation/model/src/ChatMessage.rs, core/crates/foundation/model/src/ModelCatalog.rs, core/crates/foundation/link/src/lib.rs, core/crates/foundation/link/src/protocol.rs]
date: 2026-11-11
---

# 基础层——共享契约与数据模型

## 概述

Foundation crates 为其他核心领域提供共享契约与数据类型。(`core/crates/foundation/README.md:3`)

本页覆盖 host-api、model、link 三个 crate，不含 util；model 部分只覆盖聊天消息与模型目录。

相关概念见 [[arch-corenode|CoreNode]] 与 [[arch-routing|路由与转发]]，本页只写基础层，不展开。

## AI 速览

- `HostManager` — 聚合全部宿主能力的上下文 (`core/crates/foundation/host-api/src/HostManager.rs:140`)
- `HostEnvironmentDescriptor` — 平台宿主的环境描述符 (`core/crates/foundation/host-api/src/lib.rs:96`)
- `HostPlatform` — 九个平台变体 (`core/crates/foundation/host-api/src/lib.rs:480`)
- `HostPrivilege` — 六个特权变体 (`core/crates/foundation/host-api/src/lib.rs:491`)
- `HostIsolation` — 四个隔离变体 (`core/crates/foundation/host-api/src/lib.rs:499`)
- `HostCapability` — 能力 id、范围与操作 (`core/crates/foundation/host-api/src/lib.rs:525`)
- `HostOnboardingRequirement` — 入门前置要求 (`core/crates/foundation/host-api/src/lib.rs:533`)
- `HostResult` — 宿主边界错误的 Result 别名 (`core/crates/foundation/host-api/src/lib.rs:45`)
- `HostErrorKind` — 四种宿主边界错误种类 (`core/crates/foundation/host-api/src/lib.rs:947`)
- `ChatMessage` — 聊天消息 (`core/crates/foundation/model/src/ChatMessage.rs:13`)
- `ModelCatalog` — 内置 provider 定义 (`core/crates/foundation/model/src/ModelCatalog.rs:17`)
- `CoreValue` — Link 值模型，九个变体 (`core/crates/foundation/link/src/protocol.rs:13`)
- `CoreMethodProtocol` — 方法调用、订阅、推送三态 (`core/crates/foundation/link/src/protocol.rs:696`)
- `CoreCallRequest` — Link 调用请求 (`core/crates/foundation/link/src/protocol.rs:732`)
- `CoreCallResponse` — Link 调用响应 (`core/crates/foundation/link/src/protocol.rs:762`)
- `CoreLinkRequest` — 三种操作族的 Link 请求 (`core/crates/foundation/link/src/protocol.rs:906`)
- `CoreLinkResponse` — 按操作族保留关联的 Link 响应 (`core/crates/foundation/link/src/protocol.rs:933`)
- `CoreEventStream` — 事件接收端与可选关闭回调 (`core/crates/foundation/link/src/protocol.rs:488`)
- `CoreEventKind` — 四个事件变体 (`core/crates/foundation/link/src/protocol.rs:1027`)
- `CoreLinkError` — Link 错误载体 (`core/crates/foundation/link/src/protocol.rs:1040`)
- `RoutedCoreRequest` — 跨设备空间路由的请求载体 (`core/crates/foundation/link/src/protocol.rs:988`)
- `LinkDeviceInfo` — 设备信息 (`core/crates/foundation/link/src/protocol.rs:774`)
- `FileSystemHost` — 文件系统能力 (`core/crates/foundation/host-api/src/lib.rs:3302`)
- `TerminalHost` — 终端能力 (`core/crates/foundation/host-api/src/lib.rs:1834`)
- `RuntimeStorageHost` — 虚拟运行时存储 (`core/crates/foundation/host-api/src/lib.rs:1937`)
- `SystemOperationHost` — 系统操作 (`core/crates/foundation/host-api/src/lib.rs:3245`)
- `LINK_VERSION` — 取自包版本 (`core/crates/foundation/link/src/lib.rs:17`)

## 核心机制

**定位与分工。**

Foundation crates 为其他核心领域提供共享契约与数据类型。 (`core/crates/foundation/README.md:3`)
Foundation 层不得承担应用归属、运行时构建、节点路由、代理运行时与访问服务器五类职责。 (`core/crates/foundation/README.md:5`)
host-api crate 定义平台宿主能力契约。 (`core/crates/foundation/README.md:9`)
model crate 覆盖聊天、记忆、提示词、语音转录与合成、节点数据结构。 (`core/crates/foundation/README.md:10`)
util crate 是跨平台基础工具。 (`core/crates/foundation/README.md:11`)
link crate 承载节点间互联的协议层。 (`core/crates/foundation/README.md:12`)
contracts 列为目标布局中未来新增的跨领域 trait 载体，当前基线目录下没有该 crate。 (`core/crates/foundation/README.md:16`)

**错误模型。**

HostResult<T> 是 Result<T, HostError> 的类型别名。 (`core/crates/foundation/host-api/src/lib.rs:45`)
HostErrorKind 有 General、NotFound、Timeout、PermissionDenied 四个变体。 (`core/crates/foundation/host-api/src/lib.rs:947`)
HostError::new 创建 General 种类的宿主边界错误。 (`core/crates/foundation/host-api/src/lib.rs:962`)
HostError::timeout 创建 Timeout 种类的宿主边界错误。 (`core/crates/foundation/host-api/src/lib.rs:970`)
std::io::Error 转 HostError 时 NotFound 映射为 NotFound、PermissionDenied 映射为 PermissionDenied、其余映射为 General。 (`core/crates/foundation/host-api/src/lib.rs:989`)

**能力模型与入职要求。**

hostCapabilities 对未在 defaultHostCapabilities 中定义的 id 直接 panic，错误消息是 host capability is not defined。 (`core/crates/foundation/host-api/src/lib.rs:782`)
windowsOnboardingRequirements 返回包含 windows.admin 的前置要求。 (`core/crates/foundation/host-api/src/lib.rs:793`)
androidOnboardingRequirements 返回包含 android.fileManagement 的前置要求。 (`core/crates/foundation/host-api/src/lib.rs:807`)
android.shizuku 的 isRequired 为 false，启动 Shizuku 或 Sui 后才启用对应能力。 (`core/crates/foundation/host-api/src/lib.rs:897`)
android.root 的 isRequired 为 false。 (`core/crates/foundation/host-api/src/lib.rs:907`)
ohosOnboardingRequirements 返回包含 ohos.location 的前置要求。 (`core/crates/foundation/host-api/src/lib.rs:920`)
单测验证 OpenHarmony 入门前置要求的 id 集合是 ohos.location 与 ohos.bluetooth。 (`core/crates/foundation/host-api/src/lib.rs:3492`)

**HostManager：宿主聚合与全局默认。**

全局默认 HTTP 服务器宿主存在 OnceLock 静态变量 DEFAULT_HTTP_SERVER_HOST 中。 (`core/crates/foundation/host-api/src/HostManager.rs:16`)
setDefaultHttpServerHost 用 let _ = OnceLock::set(...) 丢弃注册结果，重复注册静默失败、第一次注册胜出。 (`core/crates/foundation/host-api/src/HostManager.rs:18`)
defaultHttpServerHost 未注册时返回 HostResult 错误，提示宿主未注册 HTTP 服务器提供方。 (`core/crates/foundation/host-api/src/HostManager.rs:20`)
defaultTcpHost 未注册时返回 HostResult 错误，提示宿主未注册 TCP 提供方。 (`core/crates/foundation/host-api/src/HostManager.rs:30`)
defaultSerialPortHost 未注册时返回 HostResult 错误，提示宿主未注册串口提供方。 (`core/crates/foundation/host-api/src/HostManager.rs:44`)
defaultServiceDiscoveryHost 未注册时返回 HostResult 错误，提示宿主未注册服务发现。 (`core/crates/foundation/host-api/src/HostManager.rs:62`)
defaultHttpHost 未注册时直接 panic，要求先配置 HTTP 宿主。 (`core/crates/foundation/host-api/src/HostManager.rs:85`)
defaultWebSocketHost 未注册时直接 panic，要求先配置 WebSocket 宿主。 (`core/crates/foundation/host-api/src/HostManager.rs:100`)
defaultHostJavaScriptRuntimeHost 未注册时直接 panic，要求先配置 JavaScript 运行时宿主。 (`core/crates/foundation/host-api/src/HostManager.rs:115`)
defaultHostRuntimeTaskSchedulerHost 未注册时直接 panic，要求先配置运行时任务调度宿主。 (`core/crates/foundation/host-api/src/HostManager.rs:130`)
CoreCommandExecutor 是宿主以 argv 风格调用核心操作的命令回调类型。 (`core/crates/foundation/host-api/src/HostManager.rs:68`)
HostManager 的 34 个宿主能力字段均为 Option<Arc<dyn 对应 Host trait>> 类型。 (`core/crates/foundation/host-api/src/HostManager.rs:140`)
HostManager 另有 hostEnvironment（HostEnvironmentDescriptor，非 Option）与 coreCommandExecutor（Option<CoreCommandExecutor>，非 Host trait）两个字段。 (`core/crates/foundation/host-api/src/HostManager.rs:174`)
HostManager::new() 创建不带任何宿主集成的上下文。 (`core/crates/foundation/host-api/src/HostManager.rs:183`)
hostEnvironment 默认取 HostEnvironmentDescriptor::android()。 (`core/crates/foundation/host-api/src/HostManager.rs:222`)
withFileSystemHost 从所给 FileSystemHost 取 environmentDescriptor 作为 hostEnvironment。 (`core/crates/foundation/host-api/src/HostManager.rs:229`)
withFileSystemWebVisitSystemOperationAndManagedRuntimeHosts 创建桌面与移动宿主用的标准完整运行时上下文。 (`core/crates/foundation/host-api/src/HostManager.rs:375`)
withBrowserAutomationHostFactory 要求先配置 FileSystemHost，否则 panic。 (`core/crates/foundation/host-api/src/HostManager.rs:580`)
HostManager 的第二个 impl 块只提供 withFloatingWindowHost，注册浮窗宿主。 (`core/crates/foundation/host-api/src/HostManager.rs:658`)
HostManager 的 withServiceDiscoveryHost 等链式方法逐个安装宿主能力。 (`core/crates/foundation/host-api/src/HostManager.rs:180`)

**聊天消息。**

ChatMessage 的字段包括 sender、parts、timestamp、roleName、pluginExtensions。 (`core/crates/foundation/model/src/ChatMessage.rs:13`)
provider、modelName、inputTokens、outputTokens、cachedInputTokens 是消息的提供方与 token 计数字段。 (`core/crates/foundation/model/src/ChatMessage.rs:22`)
sentAt、outputDurationMs、waitDurationMs、completedAt 是发送/耗时/完成时间字段。 (`core/crates/foundation/model/src/ChatMessage.rs:27`)
ChatMessage 另有 timestamp: i64 时间戳字段。 (`core/crates/foundation/model/src/ChatMessage.rs:16`)
completedExecutionGeneration 字段带 #[serde(skip)]，不参与序列化。 (`core/crates/foundation/model/src/ChatMessage.rs:30`)
isVariantPreview 字段带 #[serde(skip)]，不参与序列化。 (`core/crates/foundation/model/src/ChatMessage.rs:34`)
contentStream 是 Option<CoreStream<MarkdownStreamEvent>>。 (`core/crates/foundation/model/src/ChatMessage.rs:36`)
displayText 返回聊天记录中直接渲染的文本。 (`core/crates/foundation/model/src/ChatMessage.rs:67`)
assistantProtocolMarkup 在文本模型协议边界序列化助手部分。 (`core/crates/foundation/model/src/ChatMessage.rs:72`)
new 创建带一个标准 Markdown 部分的空消息。 (`core/crates/foundation/model/src/ChatMessage.rs:77`)
new_with_parts 用 ChatMessageTimestampAllocator::next() 取时间戳。 (`core/crates/foundation/model/src/ChatMessage.rs:111`)
new_with_timestamp 先用 ChatMessageTimestampAllocator::observe 记录时间戳。 (`core/crates/foundation/model/src/ChatMessage.rs:116`)
variantCount 的默认值为 1。 (`core/crates/foundation/model/src/ChatMessage.rs:125`)
displayMode 的默认值为 ChatMessageDisplayMode::NORMAL。 (`core/crates/foundation/model/src/ChatMessage.rs:136`)

**模型目录。**

ModelCatalog 是单元结构体，提供内置 provider 定义。 (`core/crates/foundation/model/src/ModelCatalog.rs:17`)
provider 按 providerTypeId 大小写不敏感查找，找不到报错 catalog provider not found。 (`core/crates/foundation/model/src/ModelCatalog.rs:64`)
fixedModels 只返回没有模型列表端点的 provider 的固定模型列表，其他 provider 返回空。 (`core/crates/foundation/model/src/ModelCatalog.rs:71`)
providers 解析内置的 MODEL_CATALOG_PROVIDER_ROWS 返回 Provider 条目。 (`core/crates/foundation/model/src/ModelCatalog.rs:79`)
MODEL_CATALOG_PROVIDER_ROWS 是内置的 provider 目录行表。 (`core/crates/foundation/model/src/ModelCatalog.rs:22`)
Provider 目录行按竖线切分为 5 段，段数不等于 5 时报错。 (`core/crates/foundation/model/src/ModelCatalog.rs:84`)
fixedModelRows 只解析一次内置固定模型行，解析失败即构建缺陷。 (`core/crates/foundation/model/src/ModelCatalog.rs:108`)
parseModelRow 把模型目录行按竖线切分为 15 段，段数不等于 15 时报错。 (`core/crates/foundation/model/src/ModelCatalog.rs:152`)
parseCatalogBuiltinTools 只为部分 provider 解析内置联网搜索能力。 (`core/crates/foundation/model/src/ModelCatalog.rs:195`)
OPENAI_RESPONSES、OPENAI_RESPONSES_GENERIC、DEEPSEEK、OPENAI_CODEX 的内置联网搜索用 OpenAiWebSearch 格式，可与外部工具混用。 (`core/crates/foundation/model/src/ModelCatalog.rs:204`)
handlerId 固定为 http_json。 (`core/crates/foundation/model/src/ModelCatalog.rs:268`)
list_models 操作的 requiresApiKey 在操作串冒号切分后的索引 17（第 18 段），balance 操作的在索引 5（第 6 段）。 (`core/crates/foundation/model/src/ModelCatalog.rs:281`)
除固定模型外，其他模型由运行时下载的 models.dev 目录描述。 (`core/crates/foundation/model/src/ModelCatalog.rs:16`)
OPENAI_CODEX 的固定模型含 gpt-5.5、gpt-5.5-fast、gpt-5.4、gpt-5.4-fast、gpt-6-astra、gpt-6-astra-fast。 (`core/crates/foundation/model/src/ModelCatalog.rs:414`)

**Link 协议：值模型、增量与事件流。**

link 从 route_runtime 导出 CoreRouteRuntime、coreRouteRuntime、installCoreRouteRuntime、nextCoreRouteRequestId、coreForceLocal、withCoreForceLocal、coreRouteWatchSnapshot、clearCoreRouteRuntime。 (`core/crates/foundation/link/src/lib.rs:36`)
CoreValue 有 Null、Bool、Signed、Unsigned、Float、String、Bytes、List、Map 九个变体。 (`core/crates/foundation/link/src/protocol.rs:13`)
emptyMap 返回空结构化参数映射。 (`core/crates/foundation/link/src/protocol.rs:43`)
incrementalEvent 在首次更新时返回 Snapshot 事件。 (`core/crates/foundation/link/src/protocol.rs:51`)
增量事件在增量更小时返回 Delta，否则返回 Changed。 (`core/crates/foundation/link/src/protocol.rs:58`)
applyIncrementalDelta 克隆后应用增量。 (`core/crates/foundation/link/src/protocol.rs:67`)
intoIncrementalDelta 出错时丢弃已消费的基础值。 (`core/crates/foundation/link/src/protocol.rs:74`)
增量标记常量 CORE_DELTA_MARKER 的值是 $coreDelta。 (`core/crates/foundation/link/src/protocol.rs:80`)
coreValueSize 给 Null 计 1、Bool 计 2、数值计 9，字符串与字节按长度加 1。 (`core/crates/foundation/link/src/protocol.rs:307`)
toCoreValue 把可序列化 Rust 值转为 Link 值模型。 (`core/crates/foundation/link/src/protocol.rs:473`)
fromCoreValue 把 Link 值转为有类型的 Rust 值。 (`core/crates/foundation/link/src/protocol.rs:480`)
CoreEventStream 包装一个事件接收端与可选关闭回调。 (`core/crates/foundation/link/src/protocol.rs:488`)
fromMappedReceiver 在消费方轮询时映射类型化源，不分配转发 worker。 (`core/crates/foundation/link/src/protocol.rs:557`)
channel 创建进程内 Link 源的发送端与流。 (`core/crates/foundation/link/src/protocol.rs:572`)
boundedChannel 创建有界传输流，停滞的消费方不得耗尽 Edge 内存。 (`core/crates/foundation/link/src/protocol.rs:586`)
withOnClose 注册流被丢弃时运行的回调。 (`core/crates/foundation/link/src/protocol.rs:599`)
CoreRequestId 是 String 的包装类型。 (`core/crates/foundation/link/src/protocol.rs:659`)

**Link 协议：方法协议、请求、路由与错误。**

CORE_STREAM_TARGET 的值是 $core.stream.open，标识进程内嵌式流池的固定协议地址。 (`core/crates/foundation/link/src/protocol.rs:669`)
CoreMethodMode 有 Call、Watch、Push 三个变体。 (`core/crates/foundation/link/src/protocol.rs:678`)
CorePayloadKind 只有一个变体 Value。 (`core/crates/foundation/link/src/protocol.rs:685`)
CoreWatchInitial 有 None、Snapshot 两个变体。 (`core/crates/foundation/link/src/protocol.rs:690`)
CoreMethodProtocol 的字段是 mode、payload、initial。 (`core/crates/foundation/link/src/protocol.rs:696`)
callValue 描述结构化值请求/响应方法调用。 (`core/crates/foundation/link/src/protocol.rs:704`)
watchValue 描述结构化值订阅，初始事件行为显式指定。 (`core/crates/foundation/link/src/protocol.rs:713`)
pushValue 描述客户端拥有的结构化值输入流。 (`core/crates/foundation/link/src/protocol.rs:722`)
CoreCallRequest 的字段是 requestId、target、methodName、args。 (`core/crates/foundation/link/src/protocol.rs:732`)
registryKey 返回 target::methodName 形式的派发注册键。 (`core/crates/foundation/link/src/protocol.rs:756`)
CoreCallResponse 的字段是 requestId 与 Result<CoreValue, CoreLinkError> 类型的 result。 (`core/crates/foundation/link/src/protocol.rs:762`)
LinkDeviceInfo 的字段是 platform、model、pairingIncarnation。 (`core/crates/foundation/link/src/protocol.rs:774`)
nativeCli 把 model 写成 {role}(cli)-{架构} 形式。 (`core/crates/foundation/link/src/protocol.rs:785`)
nativeCliOnHost 用宿主名替代架构，宿主名去控制字符、最多 64 字符。 (`core/crates/foundation/link/src/protocol.rs:800`)
单测验证 LinkDeviceInfo::nativeCliOnHost 在宿主名空白时回落到架构。 (`core/crates/foundation/link/src/protocol.rs:1170`)
isLegacyCliAutoModel 只认 role 为 client、server、session 且架构等于当前架构的旧自动标签。 (`core/crates/foundation/link/src/protocol.rs:814`)
native 取 platform 为当前操作系统、model 为当前架构，pairingIncarnation 为 None。 (`core/crates/foundation/link/src/protocol.rs:821`)
displayName 把 platform 与 model 用 - 连接，空段过滤掉。 (`core/crates/foundation/link/src/protocol.rs:829`)
CORE_INCREMENTAL_VALUES_ARGUMENT 的值是 $coreIncremental，标记接受通用增量值更新的订阅请求。 (`core/crates/foundation/link/src/protocol.rs:857`)
CORE_INTERNAL_TARGET 的值是 $core.internal，标识注解包装器而非 Dart 代理发出的请求。 (`core/crates/foundation/link/src/protocol.rs:860`)
CoreWatchRequest 的字段是 requestId、target、propertyName、args。 (`core/crates/foundation/link/src/protocol.rs:863`)
CorePushRequest 的字段是 requestId、target、methodName、args，args 默认取 CoreValue::emptyMap。 (`core/crates/foundation/link/src/protocol.rs:871`)
withArgs 给反向流打开请求附加一次性非流参数。 (`core/crates/foundation/link/src/protocol.rs:896`)
CoreLinkRequest 只有 Call、Watch、Push 三种操作族，节点配对与会话控制用普通 Call 消息。 (`core/crates/foundation/link/src/protocol.rs:906`)
CoreLinkWatchRequest 有 Snapshot、Open、Close 三种生命周期消息。 (`core/crates/foundation/link/src/protocol.rs:915`)
CoreLinkPushRequestMessage 有 Open、Item、Close 三种生命周期消息。 (`core/crates/foundation/link/src/protocol.rs:924`)
CoreLinkResponse 按操作族保留关联，操作失败时也保留。 (`core/crates/foundation/link/src/protocol.rs:933`)
CoreLinkWatchResponse 有 Snapshot、Opened、Event、Closed 四个变体。 (`core/crates/foundation/link/src/protocol.rs:947`)
CoreLinkPushResponse 有 Opened、ItemAccepted、Closed 三个变体。 (`core/crates/foundation/link/src/protocol.rs:956`)
CorePushItem 的字段是 pushId、sequence、args。 (`core/crates/foundation/link/src/protocol.rs:963`)
RoutedCoreRequestKind 有 Target、SpaceRoute、SpaceBinding 三个变体，默认 Target。 (`core/crates/foundation/link/src/protocol.rs:975`)
RoutedCoreRequest 的字段是 spaceId、originNodeId、targetNodeId、ttl、routeKind、payload。 (`core/crates/foundation/link/src/protocol.rs:988`)
CoreEvent 的字段是 requestId、target、propertyName、kind、value。 (`core/crates/foundation/link/src/protocol.rs:1018`)
CoreEventKind 有 Snapshot、Changed、Delta、Completed 四个变体。 (`core/crates/foundation/link/src/protocol.rs:1027`)
CoreLinkError 的字段是 code、message、details、location、backtrace。 (`core/crates/foundation/link/src/protocol.rs:1040`)
methodNotFound 生成 METHOD_NOT_FOUND 错误。 (`core/crates/foundation/link/src/protocol.rs:1082`)
watchNotFound 生成 WATCH_NOT_FOUND 错误。 (`core/crates/foundation/link/src/protocol.rs:1087`)
isRoutePermissionDenied 在 code 为 ROUTE_PERMISSION_DENIED 时返回 true。 (`core/crates/foundation/link/src/protocol.rs:1106`)
internal 捕获调用方位置生成 INTERNAL_ERROR 错误。 (`core/crates/foundation/link/src/protocol.rs:1112`)

## 关键符号

**模块。**

声明 AtomicCounter、FileSystemResource、HostManager、PluginStorage、HttpServer、PluginSdkIpc、Tcp、TerminalWorkingDirectory 等模块。 (`core/crates/foundation/host-api/src/lib.rs:6`)
声明 ServiceDiscovery 模块。 (`core/crates/foundation/host-api/src/lib.rs:3577`)

**环境描述符与能力类型。**

HostEnvironmentDescriptor 的字段包括 id、displayName、platform、privilege、isolation。 (`core/crates/foundation/host-api/src/lib.rs:96`)
capabilities、structuredCapabilities、onboardingRequirements、workspaceRoots 也是环境描述符的字段。 (`core/crates/foundation/host-api/src/lib.rs:109`)
Android 环境描述符声明 HostPlatform::Android、HostPrivilege::Normal 与 HostIsolation::OsAppSandbox。 (`core/crates/foundation/host-api/src/lib.rs:119`)
ohos() 构造 OpenHarmony 环境描述符。 (`core/crates/foundation/host-api/src/lib.rs:190`)
Windows 环境描述符声明 HostPlatform::Windows 与 HostIsolation::None。 (`core/crates/foundation/host-api/src/lib.rs:271`)
linux() 构造 Linux 环境描述符。 (`core/crates/foundation/host-api/src/lib.rs:340`)
Web 环境描述符声明 HostPlatform::Web 与 HostIsolation::OsAppSandbox。 (`core/crates/foundation/host-api/src/lib.rs:375`)
esp32() 构造 ESP32 环境描述符。 (`core/crates/foundation/host-api/src/lib.rs:446`)
esp32() 环境描述符的 capabilities 只有 device.gpio 一个值。 (`core/crates/foundation/host-api/src/lib.rs:461`)
HostEnvironmentDescriptor 的 Default 实现返回 android() 的值。 (`core/crates/foundation/host-api/src/lib.rs:469`)
HostPlatform 有 Android、Ohos、Windows、Linux、Macos、Ios、Web、Esp32、Other 九个变体。 (`core/crates/foundation/host-api/src/lib.rs:480`)
HostPrivilege 有 Normal、AndroidShizuku、AndroidRoot、Administrator、Root、ServiceAccount 六个变体。 (`core/crates/foundation/host-api/src/lib.rs:491`)
HostIsolation 有 None、OsAppSandbox、Container、VirtualMachine 四个变体。 (`core/crates/foundation/host-api/src/lib.rs:499`)
CapabilityScope 有 FileSystem、System、Network、Runtime、Device、Media 六个变体。 (`core/crates/foundation/host-api/src/lib.rs:509`)
CapabilityOperation 有 Read、Write、Execute、Connect 四个变体。 (`core/crates/foundation/host-api/src/lib.rs:517`)
HostCapability 的字段包括 id、displayName、scope、operations（`Vec<CapabilityOperation>`）。 (`core/crates/foundation/host-api/src/lib.rs:525`)
HostOnboardingRequirement 的字段包括 id、title、description、capabilityIds、isRequired、status、action。 (`core/crates/foundation/host-api/src/lib.rs:533`)
HostRequirementStatus 有 Satisfied、Missing、Unavailable 三个变体。 (`core/crates/foundation/host-api/src/lib.rs:544`)
HostRequirementAction 有 RuntimePermission、OpenSystemSettings、HostManaged、None 四个变体。 (`core/crates/foundation/host-api/src/lib.rs:551`)
WorkspaceRootDescriptor 的字段包括 id、displayName、vfsRoot、physicalRoot。 (`core/crates/foundation/host-api/src/lib.rs:559`)
defaultHostCapabilities 定义宿主能力 id 到 HostCapability 的映射。 (`core/crates/foundation/host-api/src/lib.rs:566`)

**宿主能力 trait。**

WebVisitHost 声明 visitWeb，入参为 WebVisitRequest、出参为 WebVisitResult。 (`core/crates/foundation/host-api/src/lib.rs:1092`)
BrowserAutomationHost 声明 executeBrowserTool，入参为 BrowserAutomationRequest、出参为 BrowserAutomationResponse。 (`core/crates/foundation/host-api/src/lib.rs:1108`)
BrowserSessionHost 声明 listBrowserSessions 与 createBrowserSession。 (`core/crates/foundation/host-api/src/lib.rs:1163`)
ComposeDslWebViewHost 声明 handleControllerCommand 与 openFilePicker。 (`core/crates/foundation/host-api/src/lib.rs:1332`)
saveFile 把导出内容保存到宿主用户选定的目标。 (`core/crates/foundation/host-api/src/lib.rs:1340`)
ComposeDslFilePickerMode 有 Document、Photo、Image、Video、Media、Directory 六个变体。 (`core/crates/foundation/host-api/src/lib.rs:1198`)
文件选择请求的校验在 executionContextKey 为空时报错。 (`core/crates/foundation/host-api/src/lib.rs:1263`)
文件选择请求的校验在 maxContentBytes 为 0 时报错。 (`core/crates/foundation/host-api/src/lib.rs:1271`)
文件选择请求的校验在 Directory 模式带内容时报错。 (`core/crates/foundation/host-api/src/lib.rs:1275`)
文件保存请求的校验检查 suggestedName 与 mimeType。 (`core/crates/foundation/host-api/src/lib.rs:1320`)
文件保存请求的校验在任一 extensions token 为空串或含非字母数字字符时报错；extensions 为空列表时不报错。 (`core/crates/foundation/host-api/src/lib.rs:1326`)
HttpRequestData 的字段包括 url、method、headers、body、formFields、fileParts。 (`core/crates/foundation/host-api/src/lib.rs:1355`)
connectTimeoutSeconds、readTimeoutSeconds、followRedirects、ignoreSsl、proxyHost、proxyPort 分别是连接超时、读取超时、跟随重定向、忽略证书与代理主机端口。 (`core/crates/foundation/host-api/src/lib.rs:1360`)
httpDownloadPartialTargetPath 在目标路径后追加 .operit-download.partial 后缀。 (`core/crates/foundation/host-api/src/lib.rs:1394`)
HttpDownloadProgressState 有 Started、Downloading、Completed 三个变体。 (`core/crates/foundation/host-api/src/lib.rs:1412`)
HttpDownloadControl 用 AtomicBool 记录取消状态。 (`core/crates/foundation/host-api/src/lib.rs:1447`)
HttpDownloadControl 提供 cancel 方法请求取消下载。 (`core/crates/foundation/host-api/src/lib.rs:1490`)
onCancel 订阅取消回调。 (`core/crates/foundation/host-api/src/lib.rs:1510`)
isCancelled 返回是否已请求取消。 (`core/crates/foundation/host-api/src/lib.rs:1530`)
openWebSocket 打开一个二进制 WebSocket。 (`core/crates/foundation/host-api/src/lib.rs:1576`)
sendWebSocketMessage、sendWebSocketText、closeWebSocket 分别发送二进制消息、文本帧与关闭连接。 (`core/crates/foundation/host-api/src/lib.rs:1591`)
HttpHost 声明 imageDelivery 选择图片交付方式。 (`core/crates/foundation/host-api/src/lib.rs:1607`)
HttpHost 的 executeHttpRequest 执行一次带缓冲的 HTTP 请求。 (`core/crates/foundation/host-api/src/lib.rs:1610`)
downloadToFile 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:1618`)
downloadFiles 以有界工作并发下载文件并上报进度。 (`core/crates/foundation/host-api/src/lib.rs:1626`)
HttpStreamHost 声明 openHttpByteStream 打开一个 HTTP 响应体有序字节流。 (`core/crates/foundation/host-api/src/lib.rs:1638`)
openHttpResponseStream 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:1655`)
closeHttpByteStream 关闭一个已打开的 HTTP 字节流。 (`core/crates/foundation/host-api/src/lib.rs:1666`)
runtimeWorkspaceDir、resolveRuntimeExecutable、startRuntimeProcess、runRuntimeCommand 分别定位运行时工作区、可执行文件、启动进程与运行命令。 (`core/crates/foundation/host-api/src/lib.rs:1721`)
ManagedRuntimeHost 的 openPath 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:1712`)
TerminalHost 的 resolveNativeWorkingDirectory 默认拒绝文档与资源挂载路径，拒绝进入 shell。 (`core/crates/foundation/host-api/src/lib.rs:1834`)
startPtySession 创建会话。 (`core/crates/foundation/host-api/src/lib.rs:1851`)
readPtySession、writePtySession、resizePtySession、pollPtyExitCode、closePtySession 覆盖会话的读写、尺寸调整、退出码轮询与关闭。 (`core/crates/foundation/host-api/src/lib.rs:1861`)
listSessions 列出会话。 (`core/crates/foundation/host-api/src/lib.rs:1865`)
createOrGetSession 在宿主默认终端创建或复用命名会话。 (`core/crates/foundation/host-api/src/lib.rs:1867`)
executeInSession 在会话中执行命令。 (`core/crates/foundation/host-api/src/lib.rs:1874`)
executeInSessionStreaming 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:1888`)
executeHiddenCommand 执行隐藏命令。 (`core/crates/foundation/host-api/src/lib.rs:1911`)
getSessionScreen 读取会话屏幕。 (`core/crates/foundation/host-api/src/lib.rs:1924`)
RuntimeStorageHost 的 openWriteSession 默认返回 None，允许小型旧宿主走普通有界写入路径。 (`core/crates/foundation/host-api/src/lib.rs:1937`)
openTransactionDatabase 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:1942`)
retainPreferencesCache 默认返回 true。 (`core/crates/foundation/host-api/src/lib.rs:1949`)
nodeLocalApplicationHistoryLimit 默认返回 None。 (`core/crates/foundation/host-api/src/lib.rs:1952`)
readBytes 从虚拟运行时存储路径读字节。 (`core/crates/foundation/host-api/src/lib.rs:1958`)
readBytesRange 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:1960`)
writeBytes 向虚拟运行时存储路径写字节。 (`core/crates/foundation/host-api/src/lib.rs:1967`)
writeBytesAtomically 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:1978`)
appendBytes、delete、exists、list 分别追加、删除、判存与列出虚拟运行时存储条目。 (`core/crates/foundation/host-api/src/lib.rs:1988`)
RuntimeStorageWriteSession 声明 writeChunk、commit、commitFast。 (`core/crates/foundation/host-api/src/lib.rs:2073`)
discard 丢弃待发布文件。 (`core/crates/foundation/host-api/src/lib.rs:2081`)
RuntimeStorageWriteHost 声明 createWriteSession 创建顺序写入器。 (`core/crates/foundation/host-api/src/lib.rs:2087`)
ArchiveStagingHost 声明 createArchive 创建空暂存归档。 (`core/crates/foundation/host-api/src/lib.rs:2093`)
sealArchive 定稿归档并返回持久化字节长度。 (`core/crates/foundation/host-api/src/lib.rs:2108`)
HostSecretStore 声明 readSecret、writeSecret、deleteSecret。 (`core/crates/foundation/host-api/src/lib.rs:2118`)
SqliteValue 有 Null、Integer、Real、Text、Blob 五个变体。 (`core/crates/foundation/host-api/src/lib.rs:2124`)
valueAt 按下标取值，越界报错。 (`core/crates/foundation/host-api/src/lib.rs:2173`)
valueNamed 按列名取值，未找到列报错。 (`core/crates/foundation/host-api/src/lib.rs:2179`)
RuntimeSqliteConnection 声明 executeBatch、execute、query。 (`core/crates/foundation/host-api/src/lib.rs:2201`)
lastInsertRowId 与 beginTransaction 分别读最后插入行 id 与开始事务。 (`core/crates/foundation/host-api/src/lib.rs:2213`)
visit_sqlite_pages 按 LIMIT 1 OFFSET 逐页访问行。 (`core/crates/foundation/host-api/src/lib.rs:2192`)
RuntimeSqliteHost 声明 openSqliteDatabase 打开数据库。 (`core/crates/foundation/host-api/src/lib.rs:2238`)
HostRuntimeEventHost 声明 startHostRuntimeEventStream 启动宿主运行时事件流。 (`core/crates/foundation/host-api/src/lib.rs:2244`)
HostRuntimeEventSchedule 的字段包括 scheduleId、containerPackageName、hookId、kind、delayMs、intervalMs。 (`core/crates/foundation/host-api/src/lib.rs:2261`)
HostRuntimeEventSchedulerHost 声明 replaceHostRuntimeEventSchedules 替换全部活动 ToolPkg 定时并安装触发回调。 (`core/crates/foundation/host-api/src/lib.rs:2277`)
HostJavaScriptRuntimeHost 声明 createHostJavaScriptRuntime 在当前归属执行器上创建一个具体 JavaScript 运行时。 (`core/crates/foundation/host-api/src/lib.rs:2463`)
HostRuntimeTaskSchedulerHost 声明 monotonicTimeMillis 读取与墙钟变化无关的单调毫秒。 (`core/crates/foundation/host-api/src/lib.rs:2507`)
scheduleHostRuntimeTask 调度命名一次性运行时任务。 (`core/crates/foundation/host-api/src/lib.rs:2513`)
AppInstallState 有 PermissionRequired、InstallerOpened、RestartRequired、Completed 四个变体。 (`core/crates/foundation/host-api/src/lib.rs:2569`)
AppInstallTiming 有 Immediate、AfterProcessExit 两个变体，默认 Immediate。 (`core/crates/foundation/host-api/src/lib.rs:3227`)
requireImmediate 对 AfterProcessExit 返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:3235`)
SystemOperationHost 的 applicationUpdateTarget 默认返回 None，禁用应用内更新。 (`core/crates/foundation/host-api/src/lib.rs:3245`)
startAppWithActivity 在指定 activity 时返回不支持错误，否则调用 startApp。 (`core/crates/foundation/host-api/src/lib.rs:3262`)
installApp、uninstallApp、listInstalledApps、startApp 覆盖应用安装、卸载、列表与启动。 (`core/crates/foundation/host-api/src/lib.rs:3258`)
stopApp 与 getNotifications 分别停止应用与读取通知。 (`core/crates/foundation/host-api/src/lib.rs:3268`)
getDeviceLocation 与 getDeviceInfo 分别读取设备位置与设备信息。 (`core/crates/foundation/host-api/src/lib.rs:3280`)
captureScreenshot 截屏；recognizeText 对指定图片路径做 OCR 识别文本。 (`core/crates/foundation/host-api/src/lib.rs:3284`)
AudioPlaybackHost 声明 playAudio、playMusic、pauseMusic、resumeMusic、stopMusic、seekMusic、setMusicVolume、musicStatus。 (`core/crates/foundation/host-api/src/lib.rs:2740`)
BluetoothHost 声明 supportsClassicListening 声明入站 RFCOMM 支持。 (`core/crates/foundation/host-api/src/lib.rs:2921`)
scanBluetoothDevices 扫描设备。 (`core/crates/foundation/host-api/src/lib.rs:2926`)
DeviceIoHost 声明 setDigitalOutput 写数字输出并返回已提交状态。 (`core/crates/foundation/host-api/src/lib.rs:3004`)
getDigitalOutput 读一个数字输出的最后已提交状态。 (`core/crates/foundation/host-api/src/lib.rs:3010`)
RobotFaceHost 声明 setExpression 写一个机器人表情并返回已提交显示状态。 (`core/crates/foundation/host-api/src/lib.rs:3028`)
RobotFaceHost 声明 getExpression 读当前机器人表情显示状态。 (`core/crates/foundation/host-api/src/lib.rs:3031`)
TtsSynthesisHost 声明 synthesizeSpeech 合成一次语音。 (`core/crates/foundation/host-api/src/lib.rs:3053`)
TtsPlaybackHost 声明 supportsSystemSpeech 判断宿主能否用平台系统语音朗读。 (`core/crates/foundation/host-api/src/lib.rs:3078`)
speakText 发起一次平台系统语音请求。 (`core/crates/foundation/host-api/src/lib.rs:3084`)
LocalInferenceHost 声明 transcribeLocalSpeech 通过平台推理引擎转录本地音频。 (`core/crates/foundation/host-api/src/lib.rs:3139`)
synthesizeLocalSpeech 通过平台推理引擎合成语音。 (`core/crates/foundation/host-api/src/lib.rs:3145`)
ToastHost 声明 toast 在前端内呈现一条短暂消息。 (`core/crates/foundation/host-api/src/lib.rs:3169`)
ClipboardHost 声明 setClipboardText 替换系统剪贴板文本并返回已存文本。 (`core/crates/foundation/host-api/src/lib.rs:3174`)
FloatingWindowHost 声明 command 处理一条浮窗命令。 (`core/crates/foundation/host-api/src/lib.rs:3199`)
FileSystemHost 声明 envLabel 与 environmentDescriptor。 (`core/crates/foundation/host-api/src/lib.rs:3302`)
FileSystemHost 声明 readFile、readFileWithLimit、readFileBytes。 (`core/crates/foundation/host-api/src/lib.rs:3306`)
writeFile 与 writeFileBytes 分别写文本与字节。 (`core/crates/foundation/host-api/src/lib.rs:3317`)
deleteFile、fileExists、moveFile、copyFile、makeDirectory 覆盖删除、判存、移动、复制与建目录。 (`core/crates/foundation/host-api/src/lib.rs:3332`)
findFiles、fileInfo、grepCode、zipFiles、unzipFiles、openFile、shareFile 覆盖查找、元信息、代码检索、压缩、解压、打开与分享。 (`core/crates/foundation/host-api/src/lib.rs:3339`)
readFileBytesRange 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:3311`)
openAppendFile 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:3320`)
appendFileBytes 默认返回不支持错误。 (`core/crates/foundation/host-api/src/lib.rs:3327`)

**link 导出。**

声明 client、isolation、session、codec 模块。 (`core/crates/foundation/link/src/lib.rs:1`)
声明 protocol 与 route_runtime 模块。 (`core/crates/foundation/link/src/lib.rs:11`)
LINK_VERSION 取自 CARGO_PKG_VERSION。 (`core/crates/foundation/link/src/lib.rs:17`)
link 导出 CoreLinkClient、CoreLinkPushSession、CoreLinkSharedClient。 (`core/crates/foundation/link/src/lib.rs:19`)
link 导出 encodeLink、decodeLink、decodeLinkOwned、encodeLinkInto、encodedLinkSize、CoreLinkCodecError。 (`core/crates/foundation/link/src/lib.rs:20`)
link 从 protocol 导出 CoreCallRequest、CoreCallResponse、CoreEvent、CoreLinkError、CoreLinkRequest、CoreLinkResponse。 (`core/crates/foundation/link/src/lib.rs:26`)
link 从 protocol 导出 CoreValue、CoreWatchRequest、LinkDeviceInfo、RoutedCoreRequest、RoutedCoreRequestKind。 (`core/crates/foundation/link/src/lib.rs:29`)

## 调用链

以下 13 步是 HostManager、ModelCatalog、Link 三组关键操作序列，步骤之间没有同一条数据流，不构成单条调用链。

1. HostManager::new() 创建不带任何宿主集成的上下文。 (`core/crates/foundation/host-api/src/HostManager.rs:183`)
2. HostManager 的 withServiceDiscoveryHost 等链式方法逐个安装宿主能力。 (`core/crates/foundation/host-api/src/HostManager.rs:180`)
3. withFileSystemHost 从所给 FileSystemHost 取 environmentDescriptor 作为 hostEnvironment。 (`core/crates/foundation/host-api/src/HostManager.rs:229`)
4. setDefaultHttpServerHost 注册全局默认 HTTP 服务器宿主，重复注册静默失败、第一次注册胜出。 (`core/crates/foundation/host-api/src/HostManager.rs:18`)
5. defaultHttpServerHost 未注册时返回 HostResult 错误，提示宿主未注册 HTTP 服务器提供方。 (`core/crates/foundation/host-api/src/HostManager.rs:20`)
6. defaultHttpHost 未注册时直接 panic，要求先配置 HTTP 宿主。 (`core/crates/foundation/host-api/src/HostManager.rs:85`)
7. ModelCatalog::providers 解析内置的 MODEL_CATALOG_PROVIDER_ROWS 返回 Provider 条目。 (`core/crates/foundation/model/src/ModelCatalog.rs:79`)
8. provider 按 providerTypeId 大小写不敏感查找，找不到报错 catalog provider not found。 (`core/crates/foundation/model/src/ModelCatalog.rs:64`)
9. CoreCallRequest::registryKey 返回 target::methodName 形式的派发注册键。 (`core/crates/foundation/link/src/protocol.rs:756`)
10. CoreLinkRequest 只有 Call、Watch、Push 三种操作族，节点配对与会话控制用普通 Call 消息。 (`core/crates/foundation/link/src/protocol.rs:906`)
11. CoreLinkResponse 按操作族保留关联，操作失败时也保留。 (`core/crates/foundation/link/src/protocol.rs:933`)
12. incrementalEvent 在首次更新时返回 Snapshot 事件。 (`core/crates/foundation/link/src/protocol.rs:51`)
13. 增量事件在增量更小时返回 Delta，否则返回 Changed。 (`core/crates/foundation/link/src/protocol.rs:58`)

## 来源

- `core/crates/foundation/README.md`
- `core/crates/foundation/host-api/src/lib.rs`
- `core/crates/foundation/host-api/src/HostManager.rs`
- `core/crates/foundation/model/src/ChatMessage.rs`
- `core/crates/foundation/model/src/ModelCatalog.rs`
- `core/crates/foundation/link/src/lib.rs`
- `core/crates/foundation/link/src/protocol.rs`
