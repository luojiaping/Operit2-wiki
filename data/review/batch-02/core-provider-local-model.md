---
title: Provider——本地模型
module: core
platforms: [all]
sources: [core/crates/provider/local-model/src/lib.rs, core/crates/provider/local-model/src/LocalModelRegistry.rs, core/crates/provider/local-model/src/LocalModelProvider.rs, core/crates/provider/local-model/src/LocalInference.rs, core/crates/provider/local-model/src/runtime_support.rs]
date: 2026-11-11
---

# Provider——本地模型

## 概述

本地模型是不依赖云端 Provider 的设备端推理能力，模型与引擎以清单加注册表管理，语音识别与语音合成在设备上执行。
本页覆盖已装模型与引擎的注册表、模型清单结构、本地推理入口（STT 与 TTS）以及 runtime 通过 `LocalModelRuntimeSupport` 拿到的本地模型能力。
云端 Provider 适配与对话编排见 [[core-provider-services|Provider——服务聚合]]；在线模型目录见 [[model-catalog|模型目录与模型识别]]。
本页 seed 中的 `LocalModelProvider` 提供 `transcribe` 作为 STT 推理入口（core/crates/provider/local-model/src/LocalModelProvider.rs:159）。
本页 seed 中的 `LocalModelProvider` 提供 `synthesize` 作为 TTS 推理入口（core/crates/provider/local-model/src/LocalModelProvider.rs:232）。
聊天推理的会话契约是 `LocalChatSession` 的 `generate`（core/crates/provider/local-model/src/LocalInference.rs:103）。
`LocalModelDownload` 与 `LocalModelHub` 只在 lib.rs 中声明（core/crates/provider/local-model/src/lib.rs:16），实现不在本页 seed 内。
`LocalLlmInference` 只在 lib.rs 末尾声明（core/crates/provider/local-model/src/lib.rs:47），实现不在本页 seed 内。

## AI 速览

- `LocalModelRegistrySnapshot` — 已装模型与引擎的快照，含 installedModels、installedEngines、preferredSourceKind、customModels（core/crates/provider/local-model/src/LocalModelRegistry.rs:49）
- `InstalledLocalModel` — 一条已装模型记录：manifest、storagePath、installedAtMs、verifiedAtMs（core/crates/provider/local-model/src/LocalModelRegistry.rs:10）
- `InstalledLocalEngine` — 一条已装引擎记录，多一个 artifact（core/crates/provider/local-model/src/LocalModelRegistry.rs:19）
- `LocalModelProvider` — 本地模型推理入口（core/crates/provider/local-model/src/LocalModelProvider.rs:75）
- `ResolvedLocalModelRuntime` — resolve 的结果：模型、引擎与三条目录（core/crates/provider/local-model/src/LocalModelProvider.rs:68）
- `LocalModelRuntimeSupport` — runtime 向实现方索取本地模型能力的 trait（core/crates/provider/local-model/src/runtime_support.rs:9）
- `LocalModelRuntimeContext` — 以 Arc 持有 support 实现的上下文（core/crates/provider/local-model/src/runtime_support.rs:22）
- `LocalModelSelection` — 推理请求选模型：modelId 与 version（core/crates/provider/local-model/src/LocalInference.rs:16）
- `LocalInferenceError` — 两种推理错误：ModelNotLoaded、RequestFailed（core/crates/provider/local-model/src/LocalInference.rs:7）
- `LocalModelProviderError` — provider 的错误枚举（core/crates/provider/local-model/src/LocalModelProvider.rs:33）
- 主入口：`LocalModelProvider::forRuntimeStorage`（core/crates/provider/local-model/src/LocalModelProvider.rs:82）
- 主入口：`resolve`（core/crates/provider/local-model/src/LocalModelProvider.rs:98）
- 主入口：`transcribe`（core/crates/provider/local-model/src/LocalModelProvider.rs:159）
- 主入口：`synthesize`（core/crates/provider/local-model/src/LocalModelProvider.rs:232）
- 数据流向：推理请求带 `LocalModelSelection` 选模型，`resolve` 查快照并校验模型与引擎，再按平台分流执行（core/crates/provider/local-model/src/LocalModelProvider.rs:98）。

## 核心机制

### 注册表快照

- 快照 `LocalModelRegistrySnapshot` 由 installedModels、installedEngines、preferredSourceKind、customModels 四组数据组成（core/crates/provider/local-model/src/LocalModelRegistry.rs:49）。
- `LocalModelRegistrySnapshot::empty()` 生成四组数据全空、preferredSourceKind 为 None 的快照（core/crates/provider/local-model/src/LocalModelRegistry.rs:58）。
- 快照反序列化时 installedEngines、preferredSourceKind、customModels 缺失时取默认值（core/crates/provider/local-model/src/LocalModelRegistry.rs:51）。
- 一条已装模型记录 `InstalledLocalModel` 含 manifest、storagePath、installedAtMs 与 verifiedAtMs（core/crates/provider/local-model/src/LocalModelRegistry.rs:10）。
- 一条已装引擎记录 `InstalledLocalEngine` 除上述四项外还记录 artifact（core/crates/provider/local-model/src/LocalModelRegistry.rs:19）。
- 已装模型的 registryKey 直接复用其 manifest 的 registryKey（core/crates/provider/local-model/src/LocalModelRegistry.rs:39）。
- 已装引擎的 registryKey 形如 {manifest.id}@{manifest.version}#{target.storageSegment()}（core/crates/provider/local-model/src/LocalModelRegistry.rs:29）。
- `getInstalledModel` 按 trim 后的 modelId 与 version 精确匹配已装模型（core/crates/provider/local-model/src/LocalModelRegistry.rs:106）。
- `modelsByKind` 按 manifest.kind 过滤已装模型（core/crates/provider/local-model/src/LocalModelRegistry.rs:114）。
- `getInstalledEngine` 按 engineId、version 与 LocalPlatformTarget 三者精确匹配已装引擎（core/crates/provider/local-model/src/LocalModelRegistry.rs:130）。
- `upsert` 按 modelId 与 version 替换同键已装模型，不存在时追加（core/crates/provider/local-model/src/LocalModelRegistry.rs:139）。
- `upsertEngine` 按 id、version 与 target 替换同键已装引擎（core/crates/provider/local-model/src/LocalModelRegistry.rs:149）。
- `remove` 按 modelId 与 version 删除已装模型，删到返回 true、未删到返回 false（core/crates/provider/local-model/src/LocalModelRegistry.rs:160）。
- `removeEngine` 按 id、version 与 target 删除已装引擎，返回值含义与 remove 相同（core/crates/provider/local-model/src/LocalModelRegistry.rs:176）。
- `getCustomModel` 按 id 与 version 在 customModels 中查找自定义导入的模型清单（core/crates/provider/local-model/src/LocalModelRegistry.rs:68）。
- `upsertCustomModel` 按 id 与 version 替换或追加自定义模型清单（core/crates/provider/local-model/src/LocalModelRegistry.rs:77）。
- `removeCustomModel` 按 id 与 version 删除自定义模型清单，删到返回 true（core/crates/provider/local-model/src/LocalModelRegistry.rs:87）。

### 模型清单与下载来源

- 模型清单的每条下载来源记录 id、kind、repository、revision 与 baseUrl（core/crates/provider/local-model/src/LocalModelRegistry.rs:246）。
- 模型清单的每条文件记录 relativePath、sha256、byteSize 与 sourceId（core/crates/provider/local-model/src/LocalModelRegistry.rs:253）。
- `preferredSource` 在未设置 preferredSourceKind 时返回 LocalModelSourceKind::HuggingFace（core/crates/provider/local-model/src/LocalModelRegistry.rs:95）。
- `setPreferredSource` 把 preferredSourceKind 写成给定的 LocalModelSourceKind（core/crates/provider/local-model/src/LocalModelRegistry.rs:100）。
- `LocalModelDownload` 与 `LocalModelHub` 只在 lib.rs 中声明（core/crates/provider/local-model/src/lib.rs:16），实现不在本页 seed 内。

### 解析：resolve

- `LocalModelProvider` 由 runtimeRoot、registryStore 与 storageHost 组成（core/crates/provider/local-model/src/LocalModelProvider.rs:75）。
- `forRuntimeStorage` 在 RuntimeStorageHost 未配置 runtimeRootDir 时返回 Storage 错误（core/crates/provider/local-model/src/LocalModelProvider.rs:85）。
- `resolve` 先从 LocalModelRegistryStore 读快照，读失败返回 Registry 错误（core/crates/provider/local-model/src/LocalModelProvider.rs:104）。
- `resolve` 按 selection 的 modelId 与 version 查已装模型，未装返回 ModelNotInstalled（core/crates/provider/local-model/src/LocalModelProvider.rs:108）。
- `resolve` 校验 manifest.kind 与 expectedKind 一致，不一致返回 ModelKindMismatch（core/crates/provider/local-model/src/LocalModelProvider.rs:116）。
- `resolve` 要求 manifest 有 engineRequirement，缺失返回 EngineRequirementMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:122）。
- `resolve` 用 LocalPlatformTarget::current() 取当前平台目标，模型不支持该平台时返回 UnsupportedDriver（core/crates/provider/local-model/src/LocalModelProvider.rs:128）。
- `resolve` 按 engineRequirement 的 engineId、version 与当前目标查已装引擎，未装返回 EngineNotInstalled（core/crates/provider/local-model/src/LocalModelProvider.rs:137）。
- `resolve` 的 engineRuntimeDirectory 是 engineDirectory 接引擎的 artifact.archiveRoot（core/crates/provider/local-model/src/LocalModelProvider.rs:148）。
- `ResolvedLocalModelRuntime` 含 model、engine、modelDirectory、engineDirectory 与 engineRuntimeDirectory（core/crates/provider/local-model/src/LocalModelProvider.rs:68）。
- `runtimeLayoutPath` 把 storagePath 去掉 RUNTIME_ROOT_PATH_PREFIX 前缀后拼进 runtimeRoot（core/crates/provider/local-model/src/LocalModelProvider.rs:299）。
- `LocalModelProviderError` 含 Registry、ModelNotInstalled、ModelKindMismatch、DriverMissing、EngineRequirementMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:33）。
- `LocalModelProviderError` 含 EngineNotInstalled、EngineExecutableMissing、RuntimeFileMissing、UnsupportedDriver、Process（core/crates/provider/local-model/src/LocalModelProvider.rs:43）。
- `LocalModelProviderError` 含 InvalidOutput、InvalidRequest 与 Storage（core/crates/provider/local-model/src/LocalModelProvider.rs:51）。
- `LocalModelProviderError` 到 `LocalInferenceError` 的转换统一变成 RequestFailed（core/crates/provider/local-model/src/LocalModelProvider.rs:56）。

### 语音识别：transcribe

- `LocalSttRequest` 含 model、audioPath、language 与 options（core/crates/provider/local-model/src/LocalInference.rs:23）。
- `transcribe` 要求引擎目标平台不是 Android、Ohos、Ios、Web，否则返回 UnsupportedDriver，注明平台语音识别由 LocalInferenceHost 执行（core/crates/provider/local-model/src/LocalModelProvider.rs:166）。
- `transcribe` 要求模型清单含 driver，缺失返回 DriverMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:174）。
- `transcribe` 从 SherpaOnnxStreamingTransducer 驱动取 encoder、decoder、joiner、tokens 与 modelType 五个字段（core/crates/provider/local-model/src/LocalModelProvider.rs:179）。
- 驱动不是 SherpaOnnxStreamingTransducer 时 transcribe 返回 UnsupportedDriver（core/crates/provider/local-model/src/LocalModelProvider.rs:187）。
- `transcribe` 用引擎声明的 sttExecutable 作为可执行文件（core/crates/provider/local-model/src/LocalModelProvider.rs:195）。
- `transcribe` 把清单声明的 encoder 与 decoder 文件解析为 --encoder 与 --decoder 参数（core/crates/provider/local-model/src/LocalModelProvider.rs:209）。
- `transcribe` 把清单声明的 joiner 与 tokens 文件解析为 --joiner 与 --tokens 参数，并传入 --model-type（core/crates/provider/local-model/src/LocalModelProvider.rs:217）。
- `transcribe` 固定用 CPU 推理、2 线程与 greedy_search 解码（core/crates/provider/local-model/src/LocalModelProvider.rs:222）。
- `transcribe` 解析引擎 stderr 最后一行 JSON 记录的 text 字段作为识别结果（core/crates/provider/local-model/src/LocalModelProvider.rs:448）。
- `transcribe` 的识别结果 segments 固定为空向量（core/crates/provider/local-model/src/LocalModelProvider.rs:467）。
- `transcribe` 识别结果为空文本时记一条 LocalSTT 警告日志（core/crates/provider/local-model/src/LocalModelProvider.rs:456）。
- `LocalSttSegment` 记录 text、startMs 与 endMs（core/crates/provider/local-model/src/LocalInference.rs:31）。
- `LocalSttResponse` 由 text 与 segments 组成（core/crates/provider/local-model/src/LocalInference.rs:39）。
- `LocalSpeechToTextSession` 定义 transcribe 与 release（core/crates/provider/local-model/src/LocalInference.rs:81）。

### 语音合成：synthesize

- `LocalTtsRequest` 含 model、text、voice、outputFormat 与 options（core/crates/provider/local-model/src/LocalInference.rs:47）。
- `synthesize` 要求引擎目标平台不是 Android、Ohos、Ios、Web，否则返回 UnsupportedDriver，注明平台语音合成由 LocalInferenceHost 执行（core/crates/provider/local-model/src/LocalModelProvider.rs:239）。
- `synthesize` 只接受 outputFormat 为 wav（忽略大小写与首尾空白），其他格式返回 InvalidRequest（core/crates/provider/local-model/src/LocalModelProvider.rs:246）。
- `synthesize` 要求 voice 解析为整数 speakerId，非数字返回 InvalidRequest（core/crates/provider/local-model/src/LocalModelProvider.rs:253）。
- `synthesize` 要求模型清单含 driver，缺失返回 DriverMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:258）。
- `synthesize` 用引擎声明的 ttsExecutable 作为可执行文件（core/crates/provider/local-model/src/LocalModelProvider.rs:265）。
- `synthesize` 从请求 options 读取 speed 参数（core/crates/provider/local-model/src/LocalModelProvider.rs:270）。
- `jsonNumberOption` 要求选项参数存在、为数字且有限正数，否则返回 InvalidRequest（core/crates/provider/local-model/src/LocalModelProvider.rs:481）。
- `synthesize` 向引擎传入 --sid、--speed、--provider=cpu、--num-threads=2 与 --output-filename 参数（core/crates/provider/local-model/src/LocalModelProvider.rs:274）。
- `appendSherpaTtsDriverArguments` 按 driver 的具体类型分分支追加 Sherpa TTS 参数（core/crates/provider/local-model/src/LocalModelProvider.rs:497）。
- 三种 TTS 驱动之外的 driver 返回 UnsupportedDriver（core/crates/provider/local-model/src/LocalModelProvider.rs:601）。
- `validateSpeakerId` 要求 speakerId 在 [0, speakerCount) 范围内，越界返回 InvalidRequest（core/crates/provider/local-model/src/LocalModelProvider.rs:613）。
- TTS 临时输出路径在 runtimeRoot 下 temp/clean_on_exit/local-tts-{pid}-{seq}.wav，序号由 LOCAL_TTS_FILE_SEQUENCE 递增（core/crates/provider/local-model/src/LocalModelProvider.rs:310）。
- `synthesize` 把合成的 WAV 经 storageHost 读回后删除临时文件，返回的 outputFormat 固定为 wav（core/crates/provider/local-model/src/LocalModelProvider.rs:287）。
- `LocalTtsResponse` 的 audioBytes 是字节数组，outputFormat 记录输出格式（core/crates/provider/local-model/src/LocalInference.rs:57）。
- `LocalTextToSpeechSession` 定义 synthesize 与 release（core/crates/provider/local-model/src/LocalInference.rs:92）。

### 引擎子进程与文件校验

- `runEngineCommand` 以 engineRuntimeDirectory 为工作目录启动引擎进程（core/crates/provider/local-model/src/LocalModelProvider.rs:391）。
- `runEngineCommand` 进程非零退出时返回 Process 错误，附 status、stdout 与 stderr（core/crates/provider/local-model/src/LocalModelProvider.rs:396）。
- `configureEngineLibraryPath` 在 Windows 上把引擎 bin 与 lib 目录前置到 PATH（core/crates/provider/local-model/src/LocalModelProvider.rs:417）。
- `configureEngineLibraryPath` 在 Linux 上设 LD_LIBRARY_PATH 为引擎 lib 目录（core/crates/provider/local-model/src/LocalModelProvider.rs:425）。
- `configureEngineLibraryPath` 在 macOS 上设 DYLD_LIBRARY_PATH 为引擎 lib 目录（core/crates/provider/local-model/src/LocalModelProvider.rs:428）。
- `configureEngineLibraryPath` 在 Android、Ohos、Ios、Web 平台返回 UnsupportedDriver，注明平台引擎由宿主驱动（core/crates/provider/local-model/src/LocalModelProvider.rs:430）。
- `engineExecutable` 要求引擎声明可执行文件相对路径并校验文件存在，未声明返回 EngineExecutableMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:324）。
- `declaredModelFile` 要求被引用的模型文件在清单 files 中声明且磁盘上存在，否则返回 RuntimeFileMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:339）。
- `declaredModelDirectory` 要求目录在清单 files 中有声明的子文件且磁盘上存在，否则返回 RuntimeFileMissing（core/crates/provider/local-model/src/LocalModelProvider.rs:356）。

### runtime_support：runtime 向实现方要什么

- `LocalModelRuntimeSupport` 要求实现方提供 localModelDataDir 与 installedLocalModels（core/crates/provider/local-model/src/runtime_support.rs:9）。
- `LocalModelRuntimeSupport` 要求实现方提供 saveInstalledLocalModels 与 availableLocalModelManifests（core/crates/provider/local-model/src/runtime_support.rs:15）。
- localModelDataDir 返回本地模型运行时数据的根目录（core/crates/provider/local-model/src/runtime_support.rs:9）。
- installedLocalModels 返回当前已装本地模型注册表快照（core/crates/provider/local-model/src/runtime_support.rs:12）。
- saveInstalledLocalModels 持久化给定的已装本地模型快照（core/crates/provider/local-model/src/runtime_support.rs:15）。
- availableLocalModelManifests 返回运行时已知的可用本地模型清单（core/crates/provider/local-model/src/runtime_support.rs:18）。
- `LocalModelRuntimeContext` 以 Arc 持有 LocalModelRuntimeSupport 实现（core/crates/provider/local-model/src/runtime_support.rs:22）。
- `LocalModelRuntimeContext::new` 接收调用方拥有的 support 实现（core/crates/provider/local-model/src/runtime_support.rs:28）。
- `LocalModelRuntimeContext::support` 返回实现引用，sharedSupport 返回共享的 Arc（core/crates/provider/local-model/src/runtime_support.rs:33）。
- `localDriverOptions` 把模型清单的 driver 序列化为 BTreeMap<String, Value> 键值映射（core/crates/provider/local-model/src/LocalModelProvider.rs:663）。
- `modelKindName` 把 LocalModelKind 映射为 SpeechToText、TextToSpeech、Chat、Embedding 四个显示名（core/crates/provider/local-model/src/LocalModelProvider.rs:649）。

## 关键符号

- `LocalModelRegistrySnapshot` — 已装模型与引擎的快照（core/crates/provider/local-model/src/LocalModelRegistry.rs:49）
- `InstalledLocalModel` — 已装模型记录（core/crates/provider/local-model/src/LocalModelRegistry.rs:10）
- `InstalledLocalEngine` — 已装引擎记录（core/crates/provider/local-model/src/LocalModelRegistry.rs:19）
- `LocalModelProvider` — 本地推理入口，持有 runtimeRoot、registryStore、storageHost（core/crates/provider/local-model/src/LocalModelProvider.rs:75）
- `LocalModelProvider::resolve` — 解析已装模型与当前平台引擎（core/crates/provider/local-model/src/LocalModelProvider.rs:98）
- `LocalModelProvider::transcribe` — 桌面 Sherpa 引擎语音识别（core/crates/provider/local-model/src/LocalModelProvider.rs:159）
- `LocalModelProvider::synthesize` — 桌面 Sherpa 引擎语音合成（core/crates/provider/local-model/src/LocalModelProvider.rs:232）
- `ResolvedLocalModelRuntime` — resolve 的结果（core/crates/provider/local-model/src/LocalModelProvider.rs:68）
- `LocalModelProviderError` — provider 错误枚举（core/crates/provider/local-model/src/LocalModelProvider.rs:33）
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
2. `transcribe` 调 `resolve` 解析 SpeechToText 模型（core/crates/provider/local-model/src/LocalModelProvider.rs:161）。
3. 平台门控：引擎目标平台为 Android、Ohos、Ios 或 Web 时返回 UnsupportedDriver，注明平台语音识别由 LocalInferenceHost 执行（core/crates/provider/local-model/src/LocalModelProvider.rs:166）。
4. 取 `SherpaOnnxStreamingTransducer` 驱动的五个字段，取引擎声明的 sttExecutable（core/crates/provider/local-model/src/LocalModelProvider.rs:195）。
5. `runEngineCommand` 以 engineRuntimeDirectory 为工作目录启动引擎进程（core/crates/provider/local-model/src/LocalModelProvider.rs:391）。
6. `parseSherpaSttOutput` 解析引擎 stderr 最后一行 JSON 记录的 text 字段作为识别结果（core/crates/provider/local-model/src/LocalModelProvider.rs:448）。

### TTS：synthesize

1. 调用方传 `LocalTtsRequest`，含 model、text、voice、outputFormat 与 options（core/crates/provider/local-model/src/LocalInference.rs:47）。
2. `synthesize` 调 `resolve` 解析 TextToSpeech 模型（core/crates/provider/local-model/src/LocalModelProvider.rs:234）。
3. 平台门控：引擎目标平台为 Android、Ohos、Ios 或 Web 时返回 UnsupportedDriver，注明平台语音合成由 LocalInferenceHost 执行（core/crates/provider/local-model/src/LocalModelProvider.rs:239）。
4. 校验 outputFormat 为 wav（core/crates/provider/local-model/src/LocalModelProvider.rs:246）。
5. voice 解析为整数 speakerId（core/crates/provider/local-model/src/LocalModelProvider.rs:253）。
6. 生成临时输出路径，从 options 读 speed，拼装引擎参数（core/crates/provider/local-model/src/LocalModelProvider.rs:270）。
7. `runEngineCommand` 接收引擎可执行文件与参数并启动进程（core/crates/provider/local-model/src/LocalModelProvider.rs:281）。
8. 经 storageHost 读回 WAV 后删除临时文件，返回 outputFormat 为 wav 的 `LocalTtsResponse`（core/crates/provider/local-model/src/LocalModelProvider.rs:287）。

## 来源

- core/crates/provider/local-model/src/lib.rs
- core/crates/provider/local-model/src/LocalModelRegistry.rs
- core/crates/provider/local-model/src/LocalModelProvider.rs
- core/crates/provider/local-model/src/LocalInference.rs
- core/crates/provider/local-model/src/runtime_support.rs
