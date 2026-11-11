---
title: TTS 供应商目录
module: model
platforms: [all]
sources: 4
date: 2026-11-11
---

## 概述

- TTS 供应商目录是 Rust Core 内的一张静态表，集中保存每个 TTS 供应商的默认 endpoint、默认模型、默认音频格式、请求模板、鉴权头、响应管道与在线音色查询定义。`TtsCatalog`（core/crates/foundation/model/src/TtsCatalog.rs:10）
- 文档称 TTS 设置界面从 Rust 的 `TtsCatalog` 读取供应商、请求模板、鉴权头、音频格式、响应管道和音色列表操作。(docs/tts-providers.md:3)
- 文档称新增目录项会出现在 Flutter 的“新建 TTS 供应商”选项中。(docs/tts-providers.md:3)
- 文档的供应商表列出通义千问、Cartesia、Speechify、Inworld、Hume Octave、Rime 六家。(docs/tts-providers.md:9)
- 文档正文另补 ElevenLabs 使用 `eleven_multilingual_v2`，提供预置音色和在线音色查询。(docs/tts-providers.md:16)
- 代码目录共 22 行供应商行，文档介绍的七家之外另有其他供应商行。(core/crates/foundation/model/src/TtsCatalog.rs:12)
- SYSTEM_TTS、HTTP_TTS、LOCAL_MODEL 三行没有默认 endpoint 与默认模型。(core/crates/foundation/model/src/TtsCatalog.rs:13)
- 模型侧的通用目录见 [[model-catalog|模型目录与模型识别]]。

## AI 速览

- `TtsCatalog::providers` — 解析全部目录行并返回供应商条目列表。(core/crates/foundation/model/src/TtsCatalog.rs:53)
- `TtsCatalog::provider` — 按类型 ID 忽略大小写取单个供应商条目，找不到返回错误。(core/crates/foundation/model/src/TtsCatalog.rs:46)
- `TtsCatalog::voicesForProvider` — 返回指定供应商的预置音色列表。(core/crates/foundation/model/src/TtsCatalog.rs:60)
- `TTS_CATALOG_PROVIDER_ROWS` — 供应商目录常量，共 22 行。(core/crates/foundation/model/src/TtsCatalog.rs:12)
- `TTS_CATALOG_VOICE_ROWS` — 预置音色表常量，位于 collects/TtsCatalog.rs。(core/crates/foundation/model/collects/TtsCatalog.rs:1)
- `VoiceServiceFactory::createVoiceService` — 按供应商类型创建语音服务。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:13)
- `HttpVoiceProvider` — 非系统、非本地模型供应商的语音服务实现，由工厂创建。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:32)
- 数据流向：`TtsCatalog` 提供供应商条目，工厂按类型创建服务。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:32)
- 文档称合成请求和音色查询通过现有 Host HTTP 接口执行。(docs/tts-providers.md:3)

## 核心机制

### 目录格式

- 供应商目录行以 `|` 分隔为 11 个字段，字段不足返回错误。(core/crates/foundation/model/src/TtsCatalog.rs:84)
- 供应商操作行以 `^` 分隔为 12 个字段，只接受 `list_voices` 操作类型。(core/crates/foundation/model/src/TtsCatalog.rs:133)
- `list_voices` 操作的 handlerId 固定为 `http_json`。(core/crates/foundation/model/src/TtsCatalog.rs:138)
- 预置音色行以 `|` 分隔为 5 个字段。(core/crates/foundation/model/src/TtsCatalog.rs:187)
- 音色行模型非空时用行内模型，否则用传入的 `providerModel` 参数。(core/crates/foundation/model/src/TtsCatalog.rs:200)

### 七家供应商

- QWEN_TTS 通义千问：默认模型 `qwen3-tts-flash`，默认音频格式 wav，鉴权头 `Authorization: Bearer {apiKey}`。(core/crates/foundation/model/src/TtsCatalog.rs:28)
- QWEN_TTS 默认响应管道为 `parse_json → pick $.output.audio.url → http_get`，请求模板不含 `{speed}`。(core/crates/foundation/model/src/TtsCatalog.rs:28)
- QWEN_TTS 没有 `list_voices` 操作，其供应商行第 11 字段为空。(core/crates/foundation/model/src/TtsCatalog.rs:28)
- QWEN_TTS 预置音色为 Cherry、Serena、Ethan、Chelsie，共 4 行。(core/crates/foundation/model/collects/TtsCatalog.rs:118)
- CARTESIA_TTS：默认模型 `sonic-3.6`，默认音频格式 mp3，鉴权头 `Authorization: Bearer {apiKey}`，另有固定头 `Cartesia-Version: 2026-08-14`。(core/crates/foundation/model/src/TtsCatalog.rs:29)
- CARTESIA_TTS 请求模板在 `generation_config.speed` 写入 `{speed}`，默认响应管道为空数组。(core/crates/foundation/model/src/TtsCatalog.rs:29)
- CARTESIA_TTS 在线音色查询为 GET `/voices?limit=100`，每页取 100 条。(core/crates/foundation/model/src/TtsCatalog.rs:29)
- CARTESIA_TTS 预置音色仅 Skylar 一行。(core/crates/foundation/model/collects/TtsCatalog.rs:122)
- SPEECHIFY_TTS：默认模型 `simba-3.0`，默认音频格式 mp3，鉴权头 `Authorization: Bearer {apiKey}`。(core/crates/foundation/model/src/TtsCatalog.rs:30)
- SPEECHIFY_TTS 默认响应管道为 `parse_json → pick $.audio_data → base64_decode`，请求模板不含 `{speed}`。(core/crates/foundation/model/src/TtsCatalog.rs:30)
- SPEECHIFY_TTS 在线音色查询为 GET `/v1/voices?limit=200`，每页取 200 条。(core/crates/foundation/model/src/TtsCatalog.rs:30)
- SPEECHIFY_TTS 在预置音色表中零行。(core/crates/foundation/model/collects/TtsCatalog.rs:1)
- 文档称 Speechify 的音色来源为在线音色列表。(docs/tts-providers.md:11)
- INWORLD_TTS：默认模型 `inworld-tts-2`，默认音频格式 mp3，鉴权头 `Authorization: Basic {apiKey}`。(core/crates/foundation/model/src/TtsCatalog.rs:31)
- INWORLD_TTS 默认响应管道为 `parse_json → pick $.audioContent → base64_decode`，请求模板在 `audioConfig.speakingRate` 写入 `{speed}`。(core/crates/foundation/model/src/TtsCatalog.rs:31)
- INWORLD_TTS 在线音色查询为 GET `/voices/v1/voices?pageSize=2000`，每页取 2000 条。(core/crates/foundation/model/src/TtsCatalog.rs:31)
- INWORLD_TTS 预置音色为 Ashley、Dennis、Alex，共 3 行。(core/crates/foundation/model/collects/TtsCatalog.rs:123)
- HUME_TTS：默认模型 `2`，默认音频格式 mp3，鉴权头 `X-Hume-Api-Key: {apiKey}`。(core/crates/foundation/model/src/TtsCatalog.rs:32)
- HUME_TTS 请求模板在 utterances 的 `voice.provider` 写入 `HUME_AI`，并在 `speed` 写入 `{speed}`；默认响应管道为空数组。(core/crates/foundation/model/src/TtsCatalog.rs:32)
- HUME_TTS 在线音色查询为 GET `/v0/tts/voices?provider=HUME_AI&page_size=100`，每页取 100 条。(core/crates/foundation/model/src/TtsCatalog.rs:32)
- HUME_TTS 在预置音色表中零行。(core/crates/foundation/model/collects/TtsCatalog.rs:1)
- 文档称 Hume 的音色来源为在线共享音色列表。(docs/tts-providers.md:13)
- RIME_TTS：默认模型 `coda`，默认音频格式 mp3，鉴权头 `Authorization: Bearer {apiKey}`，另有固定头 `Accept: audio/mpeg`。(core/crates/foundation/model/src/TtsCatalog.rs:33)
- RIME_TTS 请求模板不含 `{speed}`，默认响应管道为空数组，没有 `list_voices` 操作。(core/crates/foundation/model/src/TtsCatalog.rs:33)
- RIME_TTS 预置音色为 astra（模型 coda）与 cove（模型 mistv3），共 2 行。(core/crates/foundation/model/collects/TtsCatalog.rs:126)
- ELEVENLABS_TTS：默认模型 `eleven_multilingual_v2`，默认音频格式 `mp3_44100_128`，鉴权头 `xi-api-key: {apiKey}`。(core/crates/foundation/model/src/TtsCatalog.rs:20)
- ELEVENLABS_TTS 请求模板在 `voice_settings.speed` 写入 `{speed}`，默认响应管道为空数组。(core/crates/foundation/model/src/TtsCatalog.rs:20)
- ELEVENLABS_TTS 在线音色查询为 GET `/v2/voices?page_size=100`，每页取 100 条。(core/crates/foundation/model/src/TtsCatalog.rs:20)
- ELEVENLABS_TTS 预置音色为 Rachel、Bella、Antoni、Elli、Josh、Arnold、Adam、Sam，共 8 行。(core/crates/foundation/model/collects/TtsCatalog.rs:40)

### 速度参数与音频管道

- 文档称 Cartesia、Inworld、Hume 和 ElevenLabs 的模板包含服务端速度参数，通义千问、Speechify 和 Rime 的预设不声明此参数。(docs/tts-providers.md:24)
- 文档称 Cartesia、Hume、Rime、ElevenLabs 直接返回音频字节。(docs/tts-providers.md:21)

### 文档说法、未在代码验证

- 文档称通义千问默认连接北京地域，选择其他地域时 API Key 与 endpoint 必须对应。(docs/tts-providers.md:9)
- QWEN_TTS 供应商行只有一个 endpoint，没有地域字段。(core/crates/foundation/model/src/TtsCatalog.rs:28)
- 文档称 Speechify 的 `simba-3.0` 支持英语、德语、西班牙语、法语、意大利语和葡萄牙语。(docs/tts-providers.md:11)
- 文档称在线音色查询当前只读取一页，需要列表之外的音色时直接填写控制台中的 ID。(docs/tts-providers.md:18)
- 文档称通义千问下载音频的步骤不携带百炼鉴权头。(docs/tts-providers.md:23)

### 目录之外的行

- KOKORO_TTS 默认模型为 kokoro，默认音频格式为 mp3，默认 endpoint 为 http://localhost:8880/v1/audio/speech。(core/crates/foundation/model/src/TtsCatalog.rs:34)
- 目录另有 OpenAI 兼容、MiniMax 等行，本页不展开。(core/crates/foundation/model/src/TtsCatalog.rs:12)

## 关键符号

- `TtsCatalog` — 无字段结构体，供应商目录的唯一入口。(core/crates/foundation/model/src/TtsCatalog.rs:10)
- `TtsCatalog::providers` — 解析全部目录行并返回供应商条目列表。(core/crates/foundation/model/src/TtsCatalog.rs:53)
- `TtsCatalog::provider` — 按类型 ID 忽略大小写取单个供应商条目。(core/crates/foundation/model/src/TtsCatalog.rs:46)
- `TtsCatalog::voicesForProvider` — 返回指定供应商的预置音色列表。(core/crates/foundation/model/src/TtsCatalog.rs:60)
- `TtsProviderCatalogEntry` — 单个供应商条目的解析结果。(core/crates/foundation/model/src/TtsCatalog.rs:87)
- `parseProviderRow` — 把一行目录文本解析为供应商条目，字段不足 11 个时返回错误。(core/crates/foundation/model/src/TtsCatalog.rs:84)
- `parseOperation` — 把操作文本解析为供应商操作定义，只接受 `list_voices`。(core/crates/foundation/model/src/TtsCatalog.rs:129)
- `parseVoiceRow` — 把一行预置音色文本解析为音色行，字段不足 5 个时返回错误。(core/crates/foundation/model/src/TtsCatalog.rs:187)
- `catalogModel` — 音色行模型非空时用行内模型，否则用传入的 `providerModel` 参数。(core/crates/foundation/model/src/TtsCatalog.rs:200)
- `VoiceServiceFactory::createVoiceService` — 按供应商类型创建语音服务。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:13)
- `HttpVoiceProvider` — 非系统、非本地模型供应商的语音服务实现。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:32)
- `SystemVoiceProvider` — SYSTEM_TTS 的语音服务实现。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:26)

## 调用链

1. 文档称 TTS 设置界面从 Rust 的 `TtsCatalog` 读取供应商、请求模板、鉴权头、音频格式、响应管道和音色列表操作。(docs/tts-providers.md:3)
2. `TtsCatalog::providers` 解析全部目录行并返回供应商条目列表。(core/crates/foundation/model/src/TtsCatalog.rs:53)
3. `TtsCatalog::provider` 按类型 ID 忽略大小写取单个供应商条目。(core/crates/foundation/model/src/TtsCatalog.rs:46)
4. `VoiceServiceFactory::createVoiceService` 按供应商类型分发。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:13)
5. SYSTEM_TTS 从上下文取 `TtsSynthesisHost` 与 `FileSystemHost`，缺失时返回错误。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:22)
6. 两个 Host 用于创建 `SystemVoiceProvider`。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:26)
7. LOCAL_MODEL 返回错误，要求由 runtime local model service 创建。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:28)
8. 其余供应商类型先经 `TtsCatalog::provider` 校验，再创建 `HttpVoiceProvider`。(core/crates/provider/services/src/tts/VoiceServiceFactory.rs:32)
9. 文档称合成请求和音色查询通过现有 Host HTTP 接口执行。(docs/tts-providers.md:3)
10. 在线音色查询走 `list_voices` 操作，handlerId 固定为 `http_json`。(core/crates/foundation/model/src/TtsCatalog.rs:138)

## 来源

- `docs/tts-providers.md`（41 行）：供应商目录的说明文档，七家供应商的默认模型、音频格式、音色来源与在线查询页数均先见于此，代码逐行核验后写入正文；文档说法与代码未验证处已在正文“文档说法、未在代码验证”小节标明。
- `core/crates/foundation/model/src/TtsCatalog.rs`（207 行）：供应商目录常量 `TTS_CATALOG_PROVIDER_ROWS` 与解析函数，七家供应商的默认模型、音频格式、请求模板、鉴权头、响应管道与 `list_voices` 定义均出自此文件。
- `core/crates/foundation/model/collects/TtsCatalog.rs`（155 行）：预置音色表常量 `TTS_CATALOG_VOICE_ROWS`，由 `TtsCatalog.rs` 第 1–2 行以 `#[path]` 引入；七家供应商的预置音色行数与音色名均出自此文件。
- `core/crates/provider/services/src/tts/VoiceServiceFactory.rs`（37 行）：按供应商类型创建语音服务的工厂，SYSTEM_TTS、LOCAL_MODEL 与其余类型的分发逻辑均出自此文件。
- 否定性结论核验方法：2026-11-12 于基线 AAswordman/Operit2 @ 364d1d594，对 `core/crates/foundation/model/collects/TtsCatalog.rs` 执行 `grep SPEECHIFY_TTS` 与 `grep HUME_TTS`，两者均为零命中，SPEECHIFY_TTS 与 HUME_TTS 在预置音色表中无行；“22 行供应商行”为数 `TtsCatalog.rs` 第 13–34 行的目录行所得。
- 文档提及的 `HttpVoiceProviderTests.rs` 与 `TtsVoiceListFetcherTests.rs` 不在 seed 文件清单内，本页未读这两个文件，正文只记录文档称其覆盖测试，不作代码验证结论。
- Flutter 设置界面本身不在 seed 文件清单内，正文关于设置界面的断言均为文档说法。
