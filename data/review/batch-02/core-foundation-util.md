---
title: 基础层——通用工具库
module: core
platforms: [all]
sources: [core/crates/foundation/util/Cargo.toml, core/crates/foundation/util/src/lib.rs, core/crates/foundation/util/src/FileUtils.rs, core/crates/foundation/util/src/AppLogger.rs, core/crates/foundation/util/src/ArchiveUtil.rs, core/crates/foundation/util/src/stream/Stream.rs, core/crates/foundation/util/src/stream/mod.rs, core/crates/foundation/util/src/streamnative/mod.rs, core/crates/foundation/util/src/exceptions/mod.rs, core/crates/foundation/util/src/stream/plugins/mod.rs]
date: 2026-11-11
---

# 基础层——通用工具库

## 概述

`operit-util` 是 Operit2 的共享工具 crate，版本是 2.0.0-preview.17（core/crates/foundation/util/Cargo.toml:3）。

本页覆盖的 seed 是 `lib.rs` 等 5 个文件与 4 个子模块索引文件，另加 `Cargo.toml`；其余模块本页只按 `lib.rs` 的声明做子能力清点，不描述未读实现。

`operit-util` 的描述是 Shared utility services and stream primitives for Operit（core/crates/foundation/util/Cargo.toml:7）。

## AI 速览

- `operit-util` — 共享工具 crate，提供日志与流式原语（core/crates/foundation/util/Cargo.toml:7）
- `AppLogger` — 进程级应用日志器（core/crates/foundation/util/src/AppLogger.rs:172）
- `LogEntry` — 一条内存与文件日志记录（core/crates/foundation/util/src/AppLogger.rs:51）
- `LogFileWriteBatch` — 同步文件写入批，析构时刷入（core/crates/foundation/util/src/AppLogger.rs:114）
- `FileUtils` — 文件分类工具（core/crates/foundation/util/src/FileUtils.rs:3）
- `ArchiveUtil` — 空占位 struct，无方法（core/crates/foundation/util/src/ArchiveUtil.rs:1）
- `Stream` — 拉取式异步流 trait（core/crates/foundation/util/src/stream/Stream.rs:73）
- `VecStream` — 内存队列有限流（core/crates/foundation/util/src/stream/Stream.rs:148）
- `FnStream` — 冷流，生产者在收集时运行（core/crates/foundation/util/src/stream/Stream.rs:221）
- `StreamCollector` — 向下游发送元素的接口（core/crates/foundation/util/src/stream/Stream.rs:133）
- `StreamLogger` — 流诊断开关与写入口（core/crates/foundation/util/src/stream/Stream.rs:8）
- 主入口：`AppLogger::configure_log_files` 绑定两个日志文件（core/crates/foundation/util/src/AppLogger.rs:273）
- 主入口：`Stream::collect` 收集流元素（core/crates/foundation/util/src/stream/Stream.rs:98）
- 日志流向：调用方 → `write_entry` → 内存历史、日志文件与控制台（core/crates/foundation/util/src/AppLogger.rs:487）
- 流流向：生产者 → `Stream::collect` → 收集器（core/crates/foundation/util/src/stream/Stream.rs:98）

## 核心机制

### crate 构成与 feature 门

- crate 名是 `operit-util`（core/crates/foundation/util/Cargo.toml:2）。
- 版本是 2.0.0-preview.17（core/crates/foundation/util/Cargo.toml:3）。
- `operit-util` 依赖 `operit-host-api`，路径指向 `../host-api`（core/crates/foundation/util/Cargo.toml:17）。
- 宿主能力边界见 [[core-foundation|基础层——共享契约与数据模型]]。
- `ChatUtils` 的声明带 `#[cfg(feature = "full")]` 门（core/crates/foundation/util/src/lib.rs:8）。
- `DocumentConversionUtil` 的声明带 `#[cfg(feature = "full")]` 门（core/crates/foundation/util/src/lib.rs:12）。
- `TokenCacheManager` 的声明带 `#[cfg(feature = "full")]` 门（core/crates/foundation/util/src/lib.rs:46）。
- `Cargo.toml` 的 `default` 特性包含 `full`（core/crates/foundation/util/Cargo.toml:13）。
- `full` 特性拉入 `flate2`、`regex`、`zip` 三个可选依赖（core/crates/foundation/util/Cargo.toml:14）。
- `flate2` 是可选依赖（core/crates/foundation/util/Cargo.toml:20）。
- `regex` 是可选依赖（core/crates/foundation/util/Cargo.toml:23）。
- `zip` 是可选依赖（core/crates/foundation/util/Cargo.toml:28）。
- 三个门控模块随默认构建编译，因为 `default` 包含 `full`（core/crates/foundation/util/Cargo.toml:13）。
- `UpdateHttp` 是内部的私有模块，不对外公开（core/crates/foundation/util/src/lib.rs:17）。

### 子能力清点

- 日志：`AppLogger`、`ChainLogger`（core/crates/foundation/util/src/lib.rs:3）。
- 资产复制：`AssetCopyUtils`（core/crates/foundation/util/src/lib.rs:5）。
- 文本分段：`TextSegmenter`（core/crates/foundation/util/src/lib.rs:45）。
- 平台路径：`AndroidUserPathUtils`、`AnrMonitor`（core/crates/foundation/util/src/lib.rs:1）。
- 聊天标记：`ChatMarkupRegex`（core/crates/foundation/util/src/lib.rs:7）。
- 颜色与崩溃：`ColorQrCodeUtil`、`CrashRecoveryState`（core/crates/foundation/util/src/lib.rs:10）。
- 音视频与文件：`FFmpegUtil`、`FileUtils`、`GithubReleaseUtil`（core/crates/foundation/util/src/lib.rs:14）。
- 异常与解析：`GlobalExceptionHandler`、`HtmlParserUtil`、`HttpMultiPartDownloader`（core/crates/foundation/util/src/lib.rs:18）。
- 图像与序列化：`ImageBitmapLimiter`、`ImagePoolManager`、`IntRangeSerializer`、`LocalDateTimeSerializer`（core/crates/foundation/util/src/lib.rs:21）。
- 区域与渲染：`LocaleUtils`、`LocationUtils`、`MarkdownRenderStream`（core/crates/foundation/util/src/lib.rs:25）。
- 媒体池：`MediaBase64Limiter`、`MediaLinkBuilder`、`MediaPoolManager`、`MediaRegistration`（core/crates/foundation/util/src/lib.rs:28）。
- 网络与路径：`NetworkUtils`、`OCRUtils`、`OperitPaths`（core/crates/foundation/util/src/lib.rs:32）。
- 存储布局：`PortProcessKiller`、`PluginStoragePaths`、`RuntimeStorageLayout`、`RuntimeStoreRoot`（core/crates/foundation/util/src/lib.rs:35）。
- 转换与解析：`SerializationSetup`、`SkillRepoZipPoolManager`、`StreamingJsonXmlConverter`、`StructuredAssistantContentParser`（core/crates/foundation/util/src/lib.rs:41）。
- 语音与消息：`TtsCleaner`、`TtsSegmenter`、`UriSerializer`、`WaifuMessageProcessor`（core/crates/foundation/util/src/lib.rs:48）。
- 子树：`exceptions`、`stream`、`streamnative`（core/crates/foundation/util/src/lib.rs:52）。
- `stream` 子树包含 `HotStream`、`ReverseStream`、`RevisableTextStream` 与 `Stream`（core/crates/foundation/util/src/stream/mod.rs:1）。
- `stream` 子树包含 `StreamBuilders`、`StreamGroup`、`StreamKmpGraph`、`StreamKmpMatchResult` 与 `StreamOperators`（core/crates/foundation/util/src/stream/mod.rs:5）。
- `stream` 子树包含 `StringExtensions`、`TextStreamRevisionTracker` 与 `plugins`（core/crates/foundation/util/src/stream/mod.rs:10）。
- `stream/plugins` 包含 `BaseJsonPlugin`、`StreamJsonPlugin`、`StreamMarkdownPlugin`、`StreamPlugin`、`StreamPureJsonPlugin` 与 `StreamXmlPlugin`（core/crates/foundation/util/src/stream/plugins/mod.rs:1）。
- `streamnative` 子树包含 `MarkdownInlineStream`、`NativeMarkdownSplitter`、`NativeMarkdownStreamOperators` 与 `NativeXmlSplitter`（core/crates/foundation/util/src/streamnative/mod.rs:1）。
- `exceptions` 子树只含 `UserCancellationException`（core/crates/foundation/util/src/exceptions/mod.rs:1）。

### 日志：级别与 Verbose 分级

- 优先级是 Android 兼容的：`VERBOSE`=2、`DEBUG`=3、`INFO`=4（core/crates/foundation/util/src/AppLogger.rs:13）。
- `WARN`=5、`ERROR`=6、`ASSERT`=7（core/crates/foundation/util/src/AppLogger.rs:19）。
- `VERBOSE_LEVEL_1` 至 `VERBOSE_LEVEL_3` 的值是 1 至 3（core/crates/foundation/util/src/AppLogger.rs:26）。
- `VERBOSE_LEVEL_4` 至 `VERBOSE_LEVEL_6` 的值是 4 至 6（core/crates/foundation/util/src/AppLogger.rs:32）。
- `VERBOSE_LEVEL_1` 是进程与配置生命周期诊断，`VERBOSE_LEVEL_2` 是用户操作阶段诊断，`VERBOSE_LEVEL_3` 是服务与工具调用边界诊断（core/crates/foundation/util/src/AppLogger.rs:25）。
- `VERBOSE_LEVEL_4` 是组件与会话生命周期诊断，`VERBOSE_LEVEL_5` 是路由与持久化内部诊断，`VERBOSE_LEVEL_6` 是逐项逐块细节诊断（core/crates/foundation/util/src/AppLogger.rs:31）。
- 默认启用文件日志与控制台日志，控制台最低级别是 `INFO`（core/crates/foundation/util/src/AppLogger.rs:150）。
- 控制台 Verbose 上限默认是 `VERBOSE_LEVEL_6`，内存历史默认保留（core/crates/foundation/util/src/AppLogger.rs:153）。

### 日志：条目与双文件 sink

- `LogEntry` 含 `priority`、`verbose_level`、`tag`、`message`、`throwable` 与 `timestamp_ms` 六个字段（core/crates/foundation/util/src/AppLogger.rs:52）。
- `LogEntry` 可序列化与反序列化（core/crates/foundation/util/src/AppLogger.rs:49）。
- `configure_log_files` 同时绑定运行日志与 ToolPkg 日志两个文件路径（core/crates/foundation/util/src/AppLogger.rs:273）。
- 任一日志文件准备失败时清空两个 sink、关闭文件日志并返回错误（core/crates/foundation/util/src/AppLogger.rs:293）。
- `get_log_file` 返回已绑定的运行日志路径（core/crates/foundation/util/src/AppLogger.rs:305）。
- `get_package_log_file` 返回已绑定的 ToolPkg 日志路径（core/crates/foundation/util/src/AppLogger.rs:315）。
- 未绑定时 `get_log_file_path` 返回 `AppLogger log file is not bound` 错误（core/crates/foundation/util/src/AppLogger.rs:325）。
- `TOOLPKG_LOG_TAG` 的值是 `ToolPkg`（core/crates/foundation/util/src/AppLogger.rs:38）。
- `write_entry` 在 tag 等于 `TOOLPKG_LOG_TAG`（忽略大小写）时额外生成一行包日志（core/crates/foundation/util/src/AppLogger.rs:506）。
- 包日志从消息里提取 `toolPkgId` 等 token 写成 `[PKG:...]`（core/crates/foundation/util/src/AppLogger.rs:806）。
- 包日志从消息里提取 `script` 等 token 写成 `[SCRIPT:...]`（core/crates/foundation/util/src/AppLogger.rs:811）。
- 包日志从消息里提取 `plugin` 等 token 写成 `[PLUGIN:...]`（core/crates/foundation/util/src/AppLogger.rs:815）。
- `format_log_line` 输出 `时间戳 优先级/标签: 消息`（core/crates/foundation/util/src/AppLogger.rs:769）。
- `format_log_line` 把 `throwable` 的每一行都带上相同前缀（core/crates/foundation/util/src/AppLogger.rs:786）。
- `priority_label` 对 `VERBOSE` 带级别时输出 `V{级别}`，否则输出单个字符（core/crates/foundation/util/src/AppLogger.rs:880）。
- `entries` 返回内存日志条目的快照（core/crates/foundation/util/src/AppLogger.rs:352）。
- `entries_json` 把内存日志条目序列化为 JSON（core/crates/foundation/util/src/AppLogger.rs:361）。
- `text` 通过文件系统宿主读回运行日志文件的文本（core/crates/foundation/util/src/AppLogger.rs:366）。
- `package_text` 通过文件系统宿主读回 ToolPkg 日志文件的文本（core/crates/foundation/util/src/AppLogger.rs:377）。

### 日志：写入路径、批处理与轮转

- `v` 写 `VERBOSE_LEVEL_1` 级别的诊断（core/crates/foundation/util/src/AppLogger.rs:388）。
- `v_with_level` 对超出 `VERBOSE_LEVEL_1` 至 `VERBOSE_LEVEL_6` 的级别断言失败（core/crates/foundation/util/src/AppLogger.rs:393）。
- `v_with_level` 在立即写入时写入成功返回 0、失败返回 -1（core/crates/foundation/util/src/AppLogger.rs:393）。
- 批处理作用域内 `v_with_level` 只把日志行排入线程本地队列即返回 0，文件尚未实际写入，调用方不能据返回 0 判断已落盘（core/crates/foundation/util/src/AppLogger.rs:590）。
- `trace` 写 `VERBOSE_LEVEL_5` 级别的诊断，`trace_detail` 写 `VERBOSE_LEVEL_6` 级别的诊断（core/crates/foundation/util/src/AppLogger.rs:402）。
- `d` 写 `DEBUG` 级别，`i` 写 `INFO` 级别（core/crates/foundation/util/src/AppLogger.rs:412）。
- `w` 写 `WARN` 级别，`e` 写 `ERROR` 级别（core/crates/foundation/util/src/AppLogger.rs:422）。
- `wtf` 写 `ASSERT` 级别（core/crates/foundation/util/src/AppLogger.rs:432）。
- `println` 显式指定优先级，`VERBOSE` 时带 `VERBOSE_LEVEL_1` 级别（core/crates/foundation/util/src/AppLogger.rs:437）。
- `println_with_error` 把错误链附加到日志消息（core/crates/foundation/util/src/AppLogger.rs:451）。
- `error_chain` 把错误与各级 `cause` 拼成 `caused by` 链（core/crates/foundation/util/src/AppLogger.rs:924）。
- `extract_named_token` 在消息里找 `name=` 标记并取到空白或逗号为止的值（core/crates/foundation/util/src/AppLogger.rs:903）。
- `write_entry` 的时间戳取 `TimeUtils::currentTimeMillisU128`（core/crates/foundation/util/src/AppLogger.rs:494）。
- `write_entry` 在保留历史开启时把条目追加到内存历史（core/crates/foundation/util/src/AppLogger.rs:512）。
- `write_entry` 把运行日志行追加到运行日志文件并把结果记入 `write_result`（core/crates/foundation/util/src/AppLogger.rs:521）。
- `write_entry` 在立即写入时任一文件 sink 失败返回 `Err`（core/crates/foundation/util/src/AppLogger.rs:485）。
- 控制台输出先走 `tryLogHostConsole`，失败时 `ERROR` 与 `ASSERT` 走 stderr、其余走 stdout（core/crates/foundation/util/src/AppLogger.rs:554）。
- `is_loggable` 只比较级别与控制台最低级别，忽略 `tag` 参数（core/crates/foundation/util/src/AppLogger.rs:472）。
- `is_verbose_loggable` 要求 `VERBOSE` 通过控制台阈值且级别在 `VERBOSE_LEVEL_1` 至当前上限内（core/crates/foundation/util/src/AppLogger.rs:477）。
- `is_console_loggable` 要求优先级不低于控制台最低级别，`VERBOSE` 还要求级别不超过上限（core/crates/foundation/util/src/AppLogger.rs:893）。
- `set_retain_entries(false)` 会清空内存历史（core/crates/foundation/util/src/AppLogger.rs:195）。
- `set_console_min_level` 只接受 `VERBOSE` 至 `ASSERT` 之间的级别（core/crates/foundation/util/src/AppLogger.rs:232）。
- `set_console_max_verbose_level` 只接受 `VERBOSE_LEVEL_1` 至 `VERBOSE_LEVEL_6`（core/crates/foundation/util/src/AppLogger.rs:252）。
- `batch_file_writes` 合并一个同步作用域内的文件写入（core/crates/foundation/util/src/AppLogger.rs:176）。
- `batch_future_file_writes` 只按每次同步轮询分批，future 让出或换线程前刷掉（core/crates/foundation/util/src/AppLogger.rs:184）。
- `LogFileWriteBatch` 在 drop 时深度减 1，为 0 时取出全部攒写（core/crates/foundation/util/src/AppLogger.rs:123）。
- 取出的攒写经 `append_line_with_rotation_cap` 按文件刷入（core/crates/foundation/util/src/AppLogger.rs:135）。
- 刷入结果以 `let _ =` 丢弃，刷入失败无法回传给此前已结束的日志调用，调用方不能依赖返回值获知所有后续写入错误（core/crates/foundation/util/src/AppLogger.rs:135）。
- `LogFileWriteBatch` 的刷入在解开过程也会执行（core/crates/foundation/util/src/AppLogger.rs:119）。
- `append_line` 在批处理深度大于 0 时把同文件同宿主的写入合并到线程本地批（core/crates/foundation/util/src/AppLogger.rs:575）。
- 追加时文件超过 4 MB 则轮转（core/crates/foundation/util/src/AppLogger.rs:612）：旧文件移到 `.1` 归档并重建空文件（core/crates/foundation/util/src/AppLogger.rs:654）。
- 轮转前删掉已存在的旧 `.1` 归档（core/crates/foundation/util/src/AppLogger.rs:642）。
- 追加时部分写入失败会丢弃已缓存的句柄，不重试该记录（core/crates/foundation/util/src/AppLogger.rs:622）。
- 内存历史超过 4096 条时淘汰最旧记录，只保留最新 2048 条（core/crates/foundation/util/src/AppLogger.rs:670）。
- `evict_log_file_oldest` 只在日志文件超过 4 MB 时裁剪（core/crates/foundation/util/src/AppLogger.rs:687）。
- 日志裁剪后写入一条 `oldest records evicted` 提示行（core/crates/foundation/util/src/AppLogger.rs:699）。
- `ensure_log_file` 在绑定时裁剪上次运行留下的超大日志（core/crates/foundation/util/src/AppLogger.rs:751）。
- `ensure_log_file` 在路径是目录时返回错误（core/crates/foundation/util/src/AppLogger.rs:733）。
- `ensure_log_file` 在路径缺失时建父目录并创建空文件（core/crates/foundation/util/src/AppLogger.rs:743）。
- `reset_log_file` 关闭两个日志文件、把文件内容写空并清除内存条目（core/crates/foundation/util/src/AppLogger.rs:345）。
- `get_stack_trace_string` 在非 ESP-IDF 上用 `Backtrace::capture` 捕获栈（core/crates/foundation/util/src/AppLogger.rs:461）。
- `get_stack_trace_string` 在 ESP-IDF 上返回 `Backtrace unavailable on ESP-IDF`（core/crates/foundation/util/src/AppLogger.rs:465）。

### 日志：平台分支

- ESP-IDF 上时间戳只用 UTC 日时钟字段输出（core/crates/foundation/util/src/AppLogger.rs:838）。
- 非 ESP-IDF 上时间戳输出本地时间（core/crates/foundation/util/src/AppLogger.rs:851）。

### 文件分类

- `FileUtils` 是供文件工具与工作区读取器共用的文件分类工具（core/crates/foundation/util/src/FileUtils.rs:1）。
- `isTextLike` 对整段字节判断是否为文本（core/crates/foundation/util/src/FileUtils.rs:7）。
- `isTextLikeSample` 只采样前 `sampleSize` 个字节（core/crates/foundation/util/src/FileUtils.rs:12）。
- `isTextLikeSample` 对空输入返回 `true`（core/crates/foundation/util/src/FileUtils.rs:14）。
- 非文本字节占比低于 10% 时判定为文本（core/crates/foundation/util/src/FileUtils.rs:43）。
- `isTextBasedExtension` 按去空白转小写后的扩展名匹配已知文本扩展名集合（core/crates/foundation/util/src/FileUtils.rs:47）。
- `isTextBasedFileName` 在无扩展名时按 `readme`、`makefile` 等裸文件名判定（core/crates/foundation/util/src/FileUtils.rs:164）。
- `isAsciiTextByte` 把可打印 ASCII（32..=126）与制表符、换行、回车当作文本字节（core/crates/foundation/util/src/FileUtils.rs:199）。
- `utf8SequenceLength` 只接受首字节 `0xC2` 至 `0xF4` 开头的 2/3/4 字节序列（core/crates/foundation/util/src/FileUtils.rs:207）。
- `utf8SequenceLength` 要求后续字节高两位为 10（`(byte & 0xC0) == 0x80`），否则返回 0（core/crates/foundation/util/src/FileUtils.rs:217）。

### 流框架

- `StreamLogger` 的诊断开关默认启用（core/crates/foundation/util/src/stream/Stream.rs:60）。
- `StreamLogger::set_enabled` 控制流诊断开关（core/crates/foundation/util/src/stream/Stream.rs:12）。
- `StreamLogger::d` 把流调度与状态诊断写到 V5（core/crates/foundation/util/src/stream/Stream.rs:17）。
- `StreamLogger::i` 把逐项流细节写到 V6（core/crates/foundation/util/src/stream/Stream.rs:24）。
- `StreamLogger::v` 把逐项流细节写到 V6（core/crates/foundation/util/src/stream/Stream.rs:35）。
- `StreamLogger::w` 写警告级流诊断（core/crates/foundation/util/src/stream/Stream.rs:46）。
- `StreamLogger::e` 写错误级流诊断（core/crates/foundation/util/src/stream/Stream.rs:53）。
- `StreamLogger` 的诊断统一打 `StreamFramework` 标签（core/crates/foundation/util/src/stream/Stream.rs:19）。
- `CollectFuture` 与 `ProducerFuture` 是装箱的异步 future 类型（core/crates/foundation/util/src/stream/Stream.rs:63）。
- `Stream` 是拉取式异步流，`Item` 须 `Send`（core/crates/foundation/util/src/stream/Stream.rs:73）。
- `Stream` 的取消通常由生产者拥有，丢弃收集 future 只停止该收集器（core/crates/foundation/util/src/stream/Stream.rs:70）。
- `Stream` 的 `is_locked` 与 `buffered_count` 默认返回 `false` 与 0（core/crates/foundation/util/src/stream/Stream.rs:77）。
- `Stream` 的 `lock`、`unlock` 与 `clear_buffer` 默认是空实现（core/crates/foundation/util/src/stream/Stream.rs:90）。
- `Stream::collect` 是唯一的必需方法，收集到生产者结束或关闭为止（core/crates/foundation/util/src/stream/Stream.rs:98）。
- `Box<S>` 对 `Stream` 做转发实现（core/crates/foundation/util/src/stream/Stream.rs:101）。
- `StreamCollector::emit` 向下游发送一个元素（core/crates/foundation/util/src/stream/Stream.rs:133）。
- `FnMut(T)` 自动实现 `StreamCollector`（core/crates/foundation/util/src/stream/Stream.rs:138）。
- `VecStream` 是内存队列支持的有限流（core/crates/foundation/util/src/stream/Stream.rs:148）。
- `VecStream::new` 按迭代顺序收下元素（core/crates/foundation/util/src/stream/Stream.rs:157）。
- `VecStream` 锁定时把新元素缓存在本地缓冲（core/crates/foundation/util/src/stream/Stream.rs:166）。
- `VecStream::collect` 先发出缓冲里的元素，再逐个发出队列元素（core/crates/foundation/util/src/stream/Stream.rs:206）。
- `VecStream` 收集结束时把流标记为已关闭（core/crates/foundation/util/src/stream/Stream.rs:215）。
- `FnStream` 是冷流，生产者在异步收集时才运行（core/crates/foundation/util/src/stream/Stream.rs:221）。
- `FnStream::collect` 先排空缓冲（core/crates/foundation/util/src/stream/Stream.rs:270）。
- `FnStream` 发出元素时若锁定则进缓冲，否则直接交给收集器（core/crates/foundation/util/src/stream/Stream.rs:281）。
- `FnStream` 再次收集时以 `FnStream producer must only be collected once` 触发 panic（core/crates/foundation/util/src/stream/Stream.rs:280）。
- `FnStream` 收集结束时把流标记为已关闭（core/crates/foundation/util/src/stream/Stream.rs:289）。
- `Stream.rs` 的测试 `fn_stream_starts_producer_during_collection` 验证生产者在收集开始前不启动（core/crates/foundation/util/src/stream/Stream.rs:396）。

### 归档占位

- `ArchiveUtil` 是空 struct，只有 `Debug`、`Clone`、`Default` 派生，无字段也无方法（core/crates/foundation/util/src/ArchiveUtil.rs:1）。

## 关键符号

- `AppLogger` — 进程级应用日志器（core/crates/foundation/util/src/AppLogger.rs:172）
- `LogEntry` — 一条内存与文件日志记录（core/crates/foundation/util/src/AppLogger.rs:51）
- `LogFileWriteBatch` — 同步文件写入批，析构时刷入（core/crates/foundation/util/src/AppLogger.rs:114）
- `FileUtils` — 文件分类工具（core/crates/foundation/util/src/FileUtils.rs:3）
- `ArchiveUtil` — 空占位 struct（core/crates/foundation/util/src/ArchiveUtil.rs:1）
- `Stream` — 拉取式异步流 trait（core/crates/foundation/util/src/stream/Stream.rs:73）
- `StreamCollector` — 向下游发送元素的接口（core/crates/foundation/util/src/stream/Stream.rs:133）
- `VecStream` — 内存队列有限流（core/crates/foundation/util/src/stream/Stream.rs:148）
- `FnStream` — 冷流（core/crates/foundation/util/src/stream/Stream.rs:221）
- `StreamLogger` — 流诊断开关与写入口（core/crates/foundation/util/src/stream/Stream.rs:8）
- `CollectFuture` — 异步流收集返回的 future 类型（core/crates/foundation/util/src/stream/Stream.rs:63）
- `ProducerFuture` — 冷流生产者返回的 future 类型（core/crates/foundation/util/src/stream/Stream.rs:66）
- `VERBOSE`、`DEBUG`、`INFO` — 优先级 2、3、4（core/crates/foundation/util/src/AppLogger.rs:13）
- `WARN`、`ERROR`、`ASSERT` — 优先级 5、6、7（core/crates/foundation/util/src/AppLogger.rs:19）
- `VERBOSE_LEVEL_1` 至 `VERBOSE_LEVEL_3` — 细节分级 1 至 3（core/crates/foundation/util/src/AppLogger.rs:26）
- `VERBOSE_LEVEL_4` 至 `VERBOSE_LEVEL_6` — 细节分级 4 至 6（core/crates/foundation/util/src/AppLogger.rs:32）
- `TOOLPKG_LOG_TAG` — ToolPkg 日志标签，值是 `ToolPkg`（core/crates/foundation/util/src/AppLogger.rs:38）
- `LOG_FILE_MAX_BYTES` — 单个日志文件 4 MB 上限（core/crates/foundation/util/src/AppLogger.rs:41）
- `MAX_MEMORY_ENTRIES` — 内存历史 4096 条上限（core/crates/foundation/util/src/AppLogger.rs:45）

## 调用链

### 一次日志写入

1. 调用方调 `AppLogger::i`（core/crates/foundation/util/src/AppLogger.rs:417）。
2. `i` 调 `println`（core/crates/foundation/util/src/AppLogger.rs:418）。
3. `println` 调 `write_entry`（core/crates/foundation/util/src/AppLogger.rs:437）。
4. `write_entry` 取时间戳（core/crates/foundation/util/src/AppLogger.rs:494）。
5. `write_entry` 把条目追加到内存历史（core/crates/foundation/util/src/AppLogger.rs:512）。
6. `write_entry` 把日志行追加到日志文件（core/crates/foundation/util/src/AppLogger.rs:521）。
7. 控制台输出先走 `tryLogHostConsole`（core/crates/foundation/util/src/AppLogger.rs:550）。
8. 宿主控制台失败时 `ERROR` 与 `ASSERT` 走 stderr、其余走 stdout（core/crates/foundation/util/src/AppLogger.rs:554）。

### 一次 VecStream 收集

1. `VecStream::new` 按迭代顺序收下元素（core/crates/foundation/util/src/stream/Stream.rs:157）。
2. `collect` 先发出缓冲里的元素（core/crates/foundation/util/src/stream/Stream.rs:206）。
3. 再逐个发出队列元素（core/crates/foundation/util/src/stream/Stream.rs:209）。
4. 收集结束时把流标记为已关闭（core/crates/foundation/util/src/stream/Stream.rs:215）。

### 一次 FnStream 收集

1. `FnStream::new` 收下生产者回调（core/crates/foundation/util/src/stream/Stream.rs:230）。
2. `collect` 先排空缓冲（core/crates/foundation/util/src/stream/Stream.rs:272）。
3. 取出生产者回调，二次收集触发 panic（core/crates/foundation/util/src/stream/Stream.rs:280）。
4. 生产者回调运行，发出元素（core/crates/foundation/util/src/stream/Stream.rs:288）。
5. 收集结束时把流标记为已关闭（core/crates/foundation/util/src/stream/Stream.rs:289）。

### 一次文件分类判定

1. `isTextLike` 调 `isTextLikeSample`（core/crates/foundation/util/src/FileUtils.rs:7）。
2. `isTextLikeSample` 只采样前 `sampleSize` 个字节（core/crates/foundation/util/src/FileUtils.rs:12）。
3. 空输入返回 `true`（core/crates/foundation/util/src/FileUtils.rs:14）。
4. 非文本字节占比低于 10% 时判定为文本（core/crates/foundation/util/src/FileUtils.rs:43）。

## 来源

- core/crates/foundation/util/Cargo.toml
- core/crates/foundation/util/src/lib.rs
- core/crates/foundation/util/src/FileUtils.rs
- core/crates/foundation/util/src/AppLogger.rs
- core/crates/foundation/util/src/ArchiveUtil.rs
- core/crates/foundation/util/src/stream/Stream.rs
- core/crates/foundation/util/src/stream/mod.rs
- core/crates/foundation/util/src/streamnative/mod.rs
- core/crates/foundation/util/src/exceptions/mod.rs
- core/crates/foundation/util/src/stream/plugins/mod.rs
