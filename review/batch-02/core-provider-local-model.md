---
title: Provider——本地模型
module: core
platforms: [all]
sources: [core/crates/provider/local-model/src/lib.rs, core/crates/provider/local-model/src/LocalModelRegistry.rs, core/crates/provider/local-model/src/LocalModelProvider.rs, core/crates/provider/local-model/src/LocalInference.rs, core/crates/provider/local-model/src/runtime_support.rs, core/crates/provider/local-model/README.md, hosts/common/operit-host-local-inference/src/lib.rs, hosts/common/operit-host-local-inference/src/speech.rs, hosts/common/operit-host-local-inference/src/chat.rs, hosts/common/operit-host-local-inference/Cargo.toml, core/crates/runtime/application/src/services/LocalProviderService.rs]
date: 2026-11-11
---

# Provider——本地模型

## 概述

本地模型是不依赖云端 Provider 的设备端推理能力，模型与引擎以清单加注册表管理，语音识别与语音合成在设备上执行。
本页覆盖已装模型与引擎的注册表、模型清单结构、本地推理入口（STT 与 TTS）以及 runtime 通过 `LocalModelRuntimeSupport` 拿到的本地模型能力。
云端 Provider 适配与对话编排见 [[core-provider-services|Provider——服务聚合]]；在线模型目录见 [[model-catalog|模型目录与模型识别]]。
STT 推理入口是宿主 crate 的 `transcribeLocalSpeech`，未绑定平台语音宿主时走桌面 Sherpa 转录（hosts/common/operit-host-local-inference/src/lib.rs:78）。
TTS 推理入口是宿主 crate 的 `synthesizeLocalSpeech`，未绑定平台语音宿主时走桌面 Sherpa 合成（hosts/common/operit-host-local-inference/src/lib.rs:101）。
聊天推理的会话契约是 `LocalChatSession` 的 `generate`（core/crates/provider/local-model/src/LocalInference.rs:103）。
`LocalModelDownload` 与 `LocalModelHub` 只在 lib.rs 中声明（core/crates/provider/local-model/src/lib.rs:16），实现不在本页 seed 内。
聊天原生推理改由宿主 crate 的 `generateLocalChat` 执行，经 chat.rs 的 `nativeGenerate` 调原生引擎（hosts/common/operit-host-local-inference/src/lib.rs:119）（hosts/common/operit-host-local-inference/src/chat.rs:68）。

## AI 速览

- `LocalModelRegistrySnapshot` — 已装模型与引擎的快照，含 installedModels、installedEngines、preferredSourceKind、customModels（core/crates/provider/local-model/src/LocalModelRegistry.rs:55）
- `InstalledLocalModel` — 一条已装模型记录：manifest、storagePath、installedAtMs、verifiedAtMs（core/crates/provider/local-model/src/LocalModelRegistry.rs:16）
- `InstalledLocalEngine` — 一条已装引擎记录，多一个 artifact（core/crates/provider/local-model/src/LocalModelRegistry.rs:25）
- `LocalModelProvider` — 本地模型解析入口：查快照、校验模型与引擎（core/crates/provider/local-model/src/LocalModelProvider.rs:68）
- `ResolvedLocalModelRuntime` — resolve 的结果：模型、引擎与三条目录（core/crates/provider/local-model/src/LocalModelProvider.rs:59）
- `LocalModelRuntimeSupport` — runtime 向实现方索取本地模型能力的 trait（core/crates/provider/local-model/src/runtime_support.rs:9）
- `LocalModelRuntimeContext` — 以 Arc 持有 support 实现的上下文（core/crates/provider/local-model/src/runtime_support.rs:22）
- `LocalModelSelection` — 推理请求选模型：modelId 与 version（core/crates/provider/local-model/src/LocalInference.rs:16）
- `LocalInferenceError` — 两种推理错误：ModelNotLoaded、RequestFailed（core/crates/provider/local-model/src/LocalInference.rs:7）
- `LocalModelProviderError` — provider 的错误枚举（core/crates/provider/local-model/src/LocalModelProvider.rs:21）
- 主入口：LocalModelProvider 的 `forRuntimeStorage`（core/crates/provider/local-model/src/LocalModelProvider.rs:75）
- 主入口：`resolve`（core/crates/provider/local-model/src/LocalModelProvider.rs:85）
- 主入口：`transcribeLocalSpeech`（hosts/common/operit-host-local-inference/src/lib.rs:78）
- 主入口：`synthesizeLocalSpeech`（hosts/common/operit-host-local-inference/src/lib.rs:101）
- 数据流向：推理请求带 `LocalModelSelection` 选模型，`resolve` 查快照并校验模型与引擎，再由宿主按平台分流执行（core/crates/runtime/application/src/services/LocalProviderService.rs:80）。

## 核心机制

### 注册表快照

- 快照 `LocalModelRegistrySnapshot` 由 installedModels、installedEngines、preferredSourceKind、customModels 四组数据组成（core/crates/provider/local-model/src/LocalModelRegistry.rs:55）。
- 快照 `LocalModelRegistrySnapshot` 的 `empty()` 生成四组数据全空、preferredSourceKind 为 None 的快照（core/crates/provider/local-model/src/LocalModelRegistry.rs:62 core/crates/provider/local-model/src/LocalModelRegistry.rs:151）。
- 快照反序列化时 installedEngines、preferredSourceKind、customModels 缺失时取默认值（core/crates/provider/local-model/src/LocalModelRegistry.rs:57）。
- 一条已装模型记录 `InstalledLocalModel` 含 manifest、storagePath、installedAtMs 与 verifiedAtMs（core/crates/provider/local-model/src/LocalModelRegistry.rs:16）。
- 一条已装引擎记录 `InstalledLocalEngine` 除上述四项外还记录 artifact（core/crates/provider/local-model/src/LocalModelRegistry.rs:25）。
- 已装模型的 registryKey 直接复用其 manifest 的 registryKey（core/crates/provider/local-model/src/LocalModelRegistry.rs:45）。
- 已装引擎的 registryKey 形如 {manifest.id}@{manifest.version}#{target.storageSegment()}（core/crates/provider/local-model/src/LocalModelRegistry.rs:35）。
- `getInstalledModel` 按 trim 后的 modelId 与 version 精确匹配已装模型（core/crates/provider/local-model/src/LocalModelRegistry.rs:198）。
- `modelsByKind` 按 manifest.kind 过滤已装模型（core/crates/provider/local-model/src/LocalModelRegistry.rs:207）。
- `getInstalledEngine` 按 engineId、version 与 LocalPlatformTarget 三者精确匹配已装引擎（core/crates/provider/local-model/src/LocalModelRegistry.rs:215）。
- `upsert` 按 modelId 与 version 替换同键已装模型，不存在时追加（core/crates/provider/local-model/src/LocalModelRegistry.rs:232）。
- `upsertEngine` 按 id、version 与 target 替换同键已装引擎（core/crates/provider/local-model/src/LocalModelRegistry.rs:242）。
- `remove` 按 modelId 与 version 删除已装模型，删到返回 true、未删到返回 false（core/crates/provider/local-model/src/LocalModelRegistry.rs:253）。
- `removeEngine` 按 id、version 与 target 删除已装引擎，返回值含义与 remove 相同（core/crates/provider/local-model/src/LocalModelRegistry.rs:260）。
- `getCustomModel` 按 id 与 version 在 customModels 中查找自定义导入的模型清单（core/crates/provider/local-model/src/LocalModelRegistry.rs:161）。
- `upsertCustomModel` 按 id 与 version 替换或追加自定义模型清单（core/crates/provider/local-model/src/LocalModelRegistry.rs:170）。
- `removeCustomModel` 按 id 与 version 删除自定义模型清单，删到返回 true（core/crates/provider/local-model/src/LocalModelRegistry.rs:177）。

### 模型清单与下载来源

- 模型清单的每条下载来源记录 id、kind、repository、revision 与 baseUrl（core/crates/provider/local-model/src/LocalModelRegistry.rs:438）。
- 模型清单的每条文件记录 relativePath、sha256、byteSize 与 sourceId（core/crates/provider/local-model/src/LocalModelRegistry.rs:445）。
- `preferredSource` 在未设置 preferredSourceKind 时返回 LocalModelSourceKind::HuggingFace（core/crates/provider/local-model/src/LocalModelRegistry.rs:187）。
- `setPreferredSource` 把 preferredSourceKind 写成给定的 LocalModelSourceKind（core/crates/provider/local-model/src/LocalModelRegistry.rs:193）。
- `LocalModelDownload` 与 `LocalModelHub` 只在 lib.rs 中声明（core/crates/provider/local-model/src/lib.rs:16），实现不在本页 seed 内。

### 解析：resolve

- `LocalModelProvider` 由 registryStore 与 storageHost 组成，不再持有 runtimeRoot（core/crates/provider/local-model/src/LocalModelProvider.rs:68）。
- `forRuntimeStorage` 直接用给定的 RuntimeStorageHost 构造 provider，不再要求配置 runtimeRootDir（core/crates/provider/local-model/src/LocalModelProvider.rs:75）。
- `resolve` 先从 LocalModelRegistryStore 读快照，读失败返回 Registry 错误（core/crates/provider/local-model/src/LocalModelProvider.rs:85）（core/crates/provider/local-model/src/LocalModelProvider.rs:91）。
- `resolve` 按 selection 的 modelId 与 version 查已装模型，未装返回 ModelNotInstalled（core/crates/provider/local-model/src/LocalModelProvider.rs:85）（core/crates/provider/local-model/src/LocalModelProvider.rs:95）。
- `resolve` 校验 manifest.kind 与 expectedKind 一致，不一致返回 ModelKindMismatch（core/crates/provider/local-model/src/LocalModelProvider.rs:85）（core/crates/provider/local-model/src/LocalModelProvider.rs:104）。
- `resolve` 要求 manifest 有 engineRequirement，缺失返回 EngineRequirementMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:85）（core/crates/provider/local-model/src/LocalModelProvider.rs:110）。
- `resolve` 用 `LocalPlatformTarget::current()` 取当前平台目标，模型不支持该平台时返回 UnsupportedDriver（core/crates/provider/local-model/src/LocalModelProvider.rs:85）（core/crates/provider/local-model/src/LocalModelProvider.rs:117）。
- `resolve` 按 engineRequirement 的 engineId、version 与当前目标查已装引擎，未装返回 EngineNotInstalled（core/crates/provider/local-model/src/LocalModelProvider.rs:85）（core/crates/provider/local-model/src/LocalModelProvider.rs:127）。
- `resolve` 的 engineRuntimeDirectory 是 engineDirectory 接引擎归一化后的 artifact.archiveRoot（经 VfsPath::joinVfsPath 拼接），archiveRoot 为“.”时按空串处理、此时即 engineDirectory 本身（core/crates/provider/local-model/src/LocalModelProvider.rs:85）（core/crates/provider/local-model/src/LocalModelProvider.rs:141）。
- `ResolvedLocalModelRuntime` 含 model、engine、modelDirectory、engineDirectory 与 engineRuntimeDirectory（core/crates/provider/local-model/src/LocalModelProvider.rs:59）。
- `runtimeLayoutPath` 经 VfsPath::runtimeDataPath 把 storagePath 映射为运行时数据 VFS 路径（core/crates/provider/local-model/src/LocalModelProvider.rs:153）。
- `LocalModelProviderError` 含 Registry、ModelNotInstalled、ModelKindMismatch、DriverMissing、EngineRequirementMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:21）（core/crates/provider/local-model/src/LocalModelProvider.rs:27）。
- `LocalModelProviderError` 含 EngineNotInstalled、EngineExecutableMissing、RuntimeFileMissing、UnsupportedDriver、Process（core/crates/provider/local-model/src/LocalModelProvider.rs:21）（core/crates/provider/local-model/src/LocalModelProvider.rs:37）。
- `LocalModelProviderError` 含 InvalidOutput、InvalidRequest 与 Storage（core/crates/provider/local-model/src/LocalModelProvider.rs:21）（core/crates/provider/local-model/src/LocalModelProvider.rs:45）。
- `LocalModelProviderError` 到 `LocalInferenceError` 的转换统一变成 RequestFailed（core/crates/provider/local-model/src/LocalModelProvider.rs:52）。

### 语音识别：transcribe

- `LocalSttRequest` 含 model、audioPath、language 与 options（core/crates/provider/local-model/src/LocalInference.rs:23）。
- 绑定了平台语音宿主时 `transcribeLocalSpeech` 转给平台宿主执行（hosts/common/operit-host-local-inference/src/lib.rs:82）。
- `transcribe` 要求模型清单含 driver，缺失返回 DriverMissing（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:23）。
- `transcribe` 从 SherpaOnnxStreamingTransducer 驱动取 encoder、decoder、joiner、tokens 与 modelType 五个字段（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:28）。
- 驱动不是 SherpaOnnxStreamingTransducer 时 `transcribe` 返回 UnsupportedDriver（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:36）。
- `transcribe` 用引擎声明的 sttExecutable 作为可执行文件（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:43）。
- `transcribe` 把清单声明的 encoder 与 decoder 文件解析为 --encoder 与 --decoder 参数（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:54）。
- `transcribe` 把清单声明的 joiner 与 tokens 文件解析为 --joiner 与 --tokens 参数，并传入 --model-type（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:64）。
- `transcribe` 固定用 CPU 推理、2 线程与 greedy_search 解码（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:70）。
- `transcribe` 解析引擎 stderr 最后一行 JSON 记录的 text 字段作为识别结果（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:281）。
- `transcribe` 的识别结果 segments 固定为空向量（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:300）。
- `transcribe` 识别结果为空文本时记一条 LocalSTT 警告日志（hosts/common/operit-host-local-inference/src/speech.rs:18）（hosts/common/operit-host-local-inference/src/speech.rs:289）。
- `LocalSttSegment` 记录 text、startMs 与 endMs（core/crates/provider/local-model/src/LocalInference.rs:31）。
- `LocalSttResponse` 由 text 与 segments 组成（core/crates/provider/local-model/src/LocalInference.rs:39）。
- `LocalSpeechToTextSession` 定义 transcribe 与 release（core/crates/provider/local-model/src/LocalInference.rs:81）。

### 语音合成：synthesize

- `LocalTtsRequest` 含 model、text、voice、outputFormat 与 options（core/crates/provider/local-model/src/LocalInference.rs:47）。
- 绑定了平台语音宿主时 `synthesizeLocalSpeech` 转给平台宿主执行（hosts/common/operit-host-local-inference/src/lib.rs:105）。
- `synthesize` 要求 voice 解析为整数 speakerId，非数字返回 InvalidRequest（hosts/common/operit-host-local-inference/src/speech.rs:81）（hosts/common/operit-host-local-inference/src/speech.rs:82）。
- `synthesize` 要求模型清单含 driver，缺失返回 DriverMissing（hosts/common/operit-host-local-inference/src/speech.rs:81）（hosts/common/operit-host-local-inference/src/speech.rs:88）。
- `synthesize` 用引擎声明的 ttsExecutable 作为可执行文件（hosts/common/operit-host-local-inference/src/speech.rs:81）（hosts/common/operit-host-local-inference/src/speech.rs:94）。
- `synthesize` 从请求携带的 `speed` 字段取语速（hosts/common/operit-host-local-inference/src/speech.rs:81）（hosts/common/operit-host-local-inference/src/speech.rs:101）。
- `synthesize` 向引擎传入 --sid、--speed、--provider=cpu、--num-threads=2 与 --output-filename 参数（hosts/common/operit-host-local-inference/src/speech.rs:81）（hosts/common/operit-host-local-inference/src/speech.rs:105）。
- `appendSherpaTtsDriverArguments` 按 driver 的具体类型分分支追加 Sherpa TTS 参数（hosts/common/operit-host-local-inference/src/speech.rs:323）。
- 三种 TTS 驱动之外的 driver 返回 UnsupportedDriver（hosts/common/operit-host-local-inference/src/speech.rs:434）。
- `validateSpeakerId` 要求 speakerId 在 [0, speakerCount) 范围内，越界返回 InvalidRequest（hosts/common/operit-host-local-inference/src/speech.rs:442）。
- TTS 临时输出路径由 LocalProviderService 生成，形如 /operitapp/data/temp/clean_on_exit/local-tts-{uuid}.wav（core/crates/runtime/application/src/services/LocalProviderService.rs:134）。
- 合成后经 `filesystem` 读回 WAV 字节并删除临时文件，宿主返回的 outputFormat 固定为 wav（core/crates/runtime/application/src/services/LocalProviderService.rs:157）（hosts/common/operit-host-local-inference/src/speech.rs:115）。
- `LocalTtsResponse` 的 audioBytes 是字节数组，outputFormat 记录输出格式（core/crates/provider/local-model/src/LocalInference.rs:57）。
- `LocalTextToSpeechSession` 定义 synthesize 与 release（core/crates/provider/local-model/src/LocalInference.rs:92）。

### 引擎子进程与文件校验

- `runEngineCommand` 以 engineRuntimeDirectory 为工作目录启动引擎进程（hosts/common/operit-host-local-inference/src/speech.rs:209）（hosts/common/operit-host-local-inference/src/speech.rs:222）。
- `runEngineCommand` 进程非零退出时返回 Process 错误，附 status、stdout 与 stderr（hosts/common/operit-host-local-inference/src/speech.rs:209）（hosts/common/operit-host-local-inference/src/speech.rs:229）。
- `configureEngineLibraryPath` 在 Windows 上把引擎 bin 与 lib 目录前置到 PATH（hosts/common/operit-host-local-inference/src/speech.rs:241）（hosts/common/operit-host-local-inference/src/speech.rs:249）。
- `configureEngineLibraryPath` 在 Linux 上设 LD_LIBRARY_PATH 为引擎 lib 目录（hosts/common/operit-host-local-inference/src/speech.rs:241）（hosts/common/operit-host-local-inference/src/speech.rs:257）。
- `configureEngineLibraryPath` 在 macOS 上设 DYLD_LIBRARY_PATH 为引擎 lib 目录（hosts/common/operit-host-local-inference/src/speech.rs:241）（hosts/common/operit-host-local-inference/src/speech.rs:260）。
- `configureEngineLibraryPath` 在 Android、Ohos、Ios、Web 平台返回 UnsupportedDriver，注明平台引擎由宿主驱动（hosts/common/operit-host-local-inference/src/speech.rs:241）（hosts/common/operit-host-local-inference/src/speech.rs:263）。
- `engineExecutable` 要求引擎声明可执行文件相对路径并校验文件存在，未声明返回 EngineExecutableMissing（hosts/common/operit-host-local-inference/src/speech.rs:122）（hosts/common/operit-host-local-inference/src/speech.rs:126）。
- `declaredModelFile` 要求被引用的模型文件在清单 files 中声明且磁盘上存在，否则返回 RuntimeFileMissing（hosts/common/operit-host-local-inference/src/speech.rs:154）（hosts/common/operit-host-local-inference/src/speech.rs:159）。
- `declaredModelDirectory` 要求目录在清单 files 中有声明的子文件（hosts/common/operit-host-local-inference/src/speech.rs:169）（hosts/common/operit-host-local-inference/src/speech.rs:173）。
- `declaredModelDirectory` 校验目录存在，缺失返回 RuntimeFileMissing（hosts/common/operit-host-local-inference/src/speech.rs:169）（hosts/common/operit-host-local-inference/src/speech.rs:180）。

### runtime_support：runtime 向实现方要什么

- `LocalModelRuntimeSupport` 要求实现方提供 localModelDataDir 与 installedLocalModels（core/crates/provider/local-model/src/runtime_support.rs:9）。
- LocalModelRuntimeSupport 要求实现方提供 `saveInstalledLocalModels` 与 `availableLocalModelManifests`（core/crates/provider/local-model/src/runtime_support.rs:15）。
- localModelDataDir 返回本地模型运行时数据的根目录（core/crates/provider/local-model/src/runtime_support.rs:9）。
- installedLocalModels 返回当前已装本地模型注册表快照（core/crates/provider/local-model/src/runtime_support.rs:12）。
- saveInstalledLocalModels 持久化给定的已装本地模型快照（core/crates/provider/local-model/src/runtime_support.rs:15）。
- availableLocalModelManifests 返回运行时已知的可用本地模型清单（core/crates/provider/local-model/src/runtime_support.rs:18）。
- `LocalModelRuntimeContext` 以 Arc 持有 LocalModelRuntimeSupport 实现（core/crates/provider/local-model/src/runtime_support.rs:22）。
- LocalModelRuntimeContext 的 `new` 接收调用方拥有的 support 实现（core/crates/provider/local-model/src/runtime_support.rs:28）。
- LocalModelRuntimeContext 的 `support` 返回实现引用，`sharedSupport` 返回共享的 Arc（core/crates/provider/local-model/src/runtime_support.rs:33）。
- `localDriverOptions` 把模型清单的 driver 序列化为 BTreeMap<String, Value> 键值映射（core/crates/provider/local-model/src/LocalModelProvider.rs:169）。
- `modelKindName` 把 LocalModelKind 映射为 SpeechToText、TextToSpeech、Chat、Embedding 四个显示名（core/crates/provider/local-model/src/LocalModelProvider.rs:159）。

## 关键符号

- `LocalModelRegistrySnapshot` — 已装模型与引擎的快照（core/crates/provider/local-model/src/LocalModelRegistry.rs:55）
- `InstalledLocalModel` — 已装模型记录（core/crates/provider/local-model/src/LocalModelRegistry.rs:16）
- `InstalledLocalEngine` — 已装引擎记录（core/crates/provider/local-model/src/LocalModelRegistry.rs:25）
- `LocalModelProvider` — 本地模型解析入口，不再持有 runtimeRoot（core/crates/provider/local-model/src/LocalModelProvider.rs:68）
- LocalModelProvider 的 `resolve` — 解析已装模型与当前平台引擎（core/crates/provider/local-model/src/LocalModelProvider.rs:85）
- `transcribeLocalSpeech` — 宿主 STT 入口，未绑定平台宿主时走桌面 Sherpa 转录（hosts/common/operit-host-local-inference/src/lib.rs:78）
- `synthesizeLocalSpeech` — 宿主 TTS 入口，未绑定平台宿主时走桌面 Sherpa 合成（hosts/common/operit-host-local-inference/src/lib.rs:101）
- `ResolvedLocalModelRuntime` — resolve 的结果（core/crates/provider/local-model/src/LocalModelProvider.rs:59）
- `LocalModelProviderError` — provider 错误枚举（core/crates/provider/local-model/src/LocalModelProvider.rs:21）
- `LocalModelSelection` — 推理请求选模型（core/crates/provider/local-model/src/LocalInference.rs:16）
- `LocalInferenceError` — 推理错误：ModelNotLoaded、RequestFailed（core/crates/provider/local-model/src/LocalInference.rs:7）
- `LocalSpeechToTextSession` — STT 会话契约（core/crates/provider/local-model/src/LocalInference.rs:81）
- `LocalTextToSpeechSession` — TTS 会话契约（core/crates/provider/local-model/src/LocalInference.rs:92）
- `LocalChatSession` — 聊天会话契约（core/crates/provider/local-model/src/LocalInference.rs:103）
- `LocalModelRuntimeSupport` — runtime 索取本地模型能力的 trait（core/crates/provider/local-model/src/runtime_support.rs:9）
- `LocalModelRuntimeContext` — support 实现的上下文包装（core/crates/provider/local-model/src/runtime_support.rs:22）

## 调用链

### STT：transcribe

1. 调用方传 `LocalSttRequest`，含 model、audioPath、language 与 options（core/crates/provider/local-model/src/LocalInference.rs:23）。
2. LocalProviderService 的 `transcribeAudio` 先调 `resolve` 解析 SpeechToText 模型（core/crates/runtime/application/src/services/LocalProviderService.rs:79）。
3. 平台分流：绑定了平台语音宿主时转给平台宿主，否则走桌面 Sherpa 转录（hosts/common/operit-host-local-inference/src/lib.rs:82）。
4. 取 `SherpaOnnxStreamingTransducer` 驱动的五个字段，取引擎声明的 sttExecutable（hosts/common/operit-host-local-inference/src/speech.rs:28）（hosts/common/operit-host-local-inference/src/speech.rs:43）。
5. `runEngineCommand` 以 engineRuntimeDirectory 为工作目录启动引擎进程（hosts/common/operit-host-local-inference/src/speech.rs:209）（hosts/common/operit-host-local-inference/src/speech.rs:222）。
6. `parseSherpaSttOutput` 解析引擎 stderr 最后一行 JSON 记录的 text 字段作为识别结果（hosts/common/operit-host-local-inference/src/speech.rs:273）（hosts/common/operit-host-local-inference/src/speech.rs:281）。

### TTS：synthesize

1. 调用方传 `LocalTtsRequest`，含 model、text、voice、outputFormat 与 options（core/crates/provider/local-model/src/LocalInference.rs:47）。
2. LocalProviderService 的 `synthesizeAudio` 先调 `resolve` 解析 TextToSpeech 模型（core/crates/runtime/application/src/services/LocalProviderService.rs:121）。
3. 平台分流：绑定了平台语音宿主时转给平台宿主，否则走桌面 Sherpa 合成（hosts/common/operit-host-local-inference/src/lib.rs:105）。
4. voice 解析为整数 speakerId（hosts/common/operit-host-local-inference/src/speech.rs:82）。
5. 生成临时 WAV 路径，取请求携带的 speed，拼装引擎参数（core/crates/runtime/application/src/services/LocalProviderService.rs:134）（hosts/common/operit-host-local-inference/src/speech.rs:101）。
6. `runEngineCommand` 接收引擎可执行文件与参数并启动进程（hosts/common/operit-host-local-inference/src/speech.rs:209）。
7. 经 filesystem 读回 WAV 字节并删除临时文件，返回 outputFormat 为 wav 的 `LocalTtsResponse`（core/crates/runtime/application/src/services/LocalProviderService.rs:161）。

## 来源

本页事实取自以下文件，基线为 AAswordman/Operit2 @ ff5373fb6。

- core/crates/provider/local-model/src/lib.rs
- core/crates/provider/local-model/src/LocalModelRegistry.rs
- core/crates/provider/local-model/src/LocalModelProvider.rs
- core/crates/provider/local-model/src/LocalInference.rs
- core/crates/provider/local-model/src/runtime_support.rs
- core/crates/provider/local-model/README.md
- hosts/common/operit-host-local-inference/src/lib.rs
- hosts/common/operit-host-local-inference/src/speech.rs
- hosts/common/operit-host-local-inference/src/chat.rs
- hosts/common/operit-host-local-inference/Cargo.toml
- core/crates/runtime/application/src/services/LocalProviderService.rs
