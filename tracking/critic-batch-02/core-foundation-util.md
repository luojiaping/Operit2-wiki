# Critic 报告：core-foundation-util（基础层——通用工具库）

- 评审 Issue：#14
- 评审日期：2026-11-11
- 结论：**需修改**（见问题清单，共 3 项必修小修 + 2 项建议；无事实性错误，无需打回重写）
- 被审文件：`review/batch-02/core-foundation-util.md`（276 行）、`review/batch-02/core-foundation-util.facts.json`（149 条）
- Critic 与写手无关联，全新 session，只读被审文件与引用指向的源码行。

## 审读范围与方法

- 通读被审页正文全文与全部 149 条 facts。
- 逐行读完 10 个 seed 文件全文（`~/workspace/Operit2 @ 364d1d594`，只读）：
  `core/crates/foundation/util/Cargo.toml`、`src/lib.rs`、`src/FileUtils.rs`、`src/AppLogger.rs`（937 行）、
  `src/ArchiveUtil.rs`、`src/stream/Stream.rs`（413 行）、`src/stream/mod.rs`、`src/streamnative/mod.rs`、
  `src/exceptions/mod.rs`、`src/stream/plugins/mod.rs`。
- 机械核验：149 条 facts 的 ref 全部解析成功、文件存在、行号在范围内，坏引用 0；逐条打印 ref 行内容与断言逐一对照。
- 全批 lint 已跑：硬失败 0、警告 0（本页无禁用词，正文 grep 复核：`可能/大概/似乎/应该/也许` 0 命中）。
- 覆盖范围核对：写手声明整 crate 79 个 `.rs` 文件中约 70 个未深读、正文只按 `lib.rs` 声明做子能力清点。
  Critic 直数复核：`find . -name '*.rs' | wc -l` = 79，`cat | wc -l` = 17,476，与概述数字一致；
  正文无任何关于未读文件的实现断言，范围声明诚实。

## 逐条判定（149 条）

- 支撑 148 条，不支撑 0 条，存疑 1 条（[101]，见问题 1）。
- [79]、[80]、[129] 判支撑：断言内容为真、符号在 ref 行 ±5 行内，但锚行本身不是符号行（见问题 2，小修）。

### Cargo.toml（[1]–[13]）：全部支撑

| fact | 判定 |
| --- | --- |
| [1] crate 名 operit-util（:2） | 支撑 |
| [2] 版本 2.0.0-preview.17（:3） | 支撑 |
| [3] 描述 Shared utility services and stream primitives for Operit（:7） | 支撑 |
| [4] 依赖 operit-host-api，路径 ../host-api（:17） | 支撑 |
| [5] 直接依赖包括 base64 与 chrono（:18；chrono 在 :19，±5 内） | 支撑 |
| [6] 直接依赖包括 heic-rs 与 image（:21；image 在 :22） | 支撑 |
| [7] 直接依赖包括 serde、serde_json 与 tokio（:24；其余在 :25、:26） | 支撑 |
| [8] 直接依赖包括 uuid（:27） | 支撑 |
| [9] default 特性包含 full（:13） | 支撑 |
| [10] full 拉入 flate2、regex、zip（:14） | 支撑 |
| [11] flate2 optional = true（:20） | 支撑 |
| [12] regex optional = true（:23） | 支撑 |
| [13] zip optional = true（:28） | 支撑 |

### lib.rs（[14]–[34]）：全部支撑

| fact | 判定 |
| --- | --- |
| [14] ChatUtils 声明带 #[cfg(feature = "full")]（:8） | 支撑 |
| [15] DocumentConversionUtil 声明带 #[cfg(feature = "full")]（:12） | 支撑 |
| [16] TokenCacheManager 声明带 #[cfg(feature = "full")]（:46） | 支撑 |
| [17] AndroidUserPathUtils、AnrMonitor 公开模块（:1） | 支撑 |
| [18] AppLogger、ArchiveUtil、AssetCopyUtils、ChainLogger、ChatMarkupRegex 公开模块（:3） | 支撑 |
| [19] ChatUtils 公开模块（:9） | 支撑 |
| [20] ColorQrCodeUtil、CrashRecoveryState 公开模块（:10） | 支撑 |
| [21] DocumentConversionUtil 公开模块（:13） | 支撑 |
| [22] FFmpegUtil、FileUtils、GithubReleaseUtil 公开模块（:14） | 支撑 |
| [23] GlobalExceptionHandler、HtmlParserUtil、HttpMultiPartDownloader 公开模块（:18） | 支撑 |
| [24] ImageBitmapLimiter、ImagePoolManager、IntRangeSerializer、LocalDateTimeSerializer 公开模块（:21） | 支撑 |
| [25] LocaleUtils、LocationUtils、MarkdownRenderStream 公开模块（:25） | 支撑 |
| [26] MediaBase64Limiter、MediaLinkBuilder、MediaPoolManager、MediaRegistration 公开模块（:28） | 支撑 |
| [27] NetworkUtils、OCRUtils、OperitPaths 公开模块（:32） | 支撑 |
| [28] PortProcessKiller、PluginStoragePaths、RuntimeStorageLayout、RuntimeStoreRoot 公开模块（:35） | 支撑 |
| [29] SerializationSetup、SkillRepoZipPoolManager、StreamingJsonXmlConverter、StructuredAssistantContentParser 公开模块（:41） | 支撑 |
| [30] TextSegmenter 公开模块（:45） | 支撑 |
| [31] TokenCacheManager 公开模块（:47） | 支撑 |
| [32] TtsCleaner、TtsSegmenter、UriSerializer、WaifuMessageProcessor 公开模块（:48） | 支撑 |
| [33] exceptions、stream、streamnative 公开子模块树（:52） | 支撑 |
| [34] UpdateHttp 内部私有模块，不对外公开（:17，`mod UpdateHttp;` 无 pub） | 支撑 |

### 子树 mod.rs（[35]–[40]）：全部支撑

| fact | 判定 |
| --- | --- |
| [35] stream 子树含 HotStream、ReverseStream、RevisableTextStream、Stream（stream/mod.rs:1） | 支撑 |
| [36] stream 子树含 StreamBuilders、StreamGroup、StreamKmpGraph、StreamKmpMatchResult、StreamOperators（:5） | 支撑 |
| [37] stream 子树含 StringExtensions、TextStreamRevisionTracker、plugins（:10） | 支撑 |
| [38] stream/plugins 含 6 个插件模块（plugins/mod.rs:1） | 支撑 |
| [39] streamnative 子树含 4 个模块（streamnative/mod.rs:1） | 支撑 |
| [40] exceptions 子树只含 UserCancellationException（exceptions/mod.rs:1） | 支撑 |

### ArchiveUtil / FileUtils（[41]–[51]）：全部支撑

| fact | 判定 |
| --- | --- |
| [41] ArchiveUtil 空 struct，只有 Debug、Clone、Default 派生，无字段无方法（:1） | 支撑（全仓 grep 复核：无 `impl ArchiveUtil`、无 `ArchiveUtil::` 调用，与 quality.json 的零调用结论一致） |
| [42] FileUtils 是文件工具与工作区读取器共用的文件分类工具（:1，doc 原文） | 支撑 |
| [43] isTextLike 对整段字节判断是否为文本（:7） | 支撑 |
| [44] isTextLikeSample 只采样前 sampleSize 个字节（:12，`bytes.len().min(sampleSize)`） | 支撑 |
| [45] isTextLikeSample 对空输入返回 true（:14） | 支撑 |
| [46] 非文本字节占比低于 10% 时判定为文本（:43，`nonText*100 < total*10`） | 支撑 |
| [47] isTextBasedExtension 按去空白转小写后的扩展名匹配已知集合（:47） | 支撑 |
| [48] isTextBasedFileName 在无扩展名时按 readme、makefile 等裸文件名判定（:164） | 支撑 |
| [49] isAsciiTextByte 把可打印 ASCII（32..=126）与制表符、换行、回车当作文本字节（:199） | 支撑 |
| [50] utf8SequenceLength 只接受首字节 0xC2 至 0xF4 开头的 2/3/4 字节序列（:207，`0xC2..=0xDF => 2, 0xE0..=0xEF => 3, 0xF0..=0xF4 => 4`） | 支撑 |
| [51] utf8SequenceLength 要求后续字节符合 0x80 掩码，否则返回 0（:217，`(byte & 0xC0) == 0x80`） | 支撑（措辞见问题 5，建议改精确） |

### AppLogger（[52]–[121]）：148 条中 147 条支撑，1 条存疑

| fact | 判定 |
| --- | --- |
| [52] VERBOSE=2、DEBUG=3、INFO=4，Android 兼容（:13） | 支撑 |
| [53] WARN=5、ERROR=6、ASSERT=7（:19） | 支撑 |
| [54] VERBOSE_LEVEL_1 至 _3 的值是 1 至 3（:26） | 支撑 |
| [55] VERBOSE_LEVEL_4 至 _6 的值是 4 至 6（:32） | 支撑 |
| [56] V1 进程与配置生命周期、V2 用户操作阶段、V3 服务与工具调用边界（:25，doc 原文） | 支撑 |
| [57] V4 组件与会话生命周期、V5 路由与持久化内部、V6 逐项逐块细节（:31，doc 原文） | 支撑 |
| [58] LogEntry 含 6 个字段（:52） | 支撑 |
| [59] LogEntry 可序列化与反序列化（:49，derive Serialize, Deserialize） | 支撑 |
| [60] 默认启用文件日志与控制台日志，控制台最低级别 INFO（:150，state 初始化） | 支撑 |
| [61] 控制台 Verbose 上限默认 VERBOSE_LEVEL_6，内存历史默认保留（:153） | 支撑 |
| [62] set_retain_entries(false) 清空内存历史（:195） | 支撑 |
| [63] set_console_min_level 只接受 VERBOSE 至 ASSERT 之间的级别（:232，越界返回 Err） | 支撑 |
| [64] set_console_max_verbose_level 只接受 VERBOSE_LEVEL_1 至 _6（:252） | 支撑 |
| [65] configure_log_files 同时绑定运行日志与 ToolPkg 日志两个文件路径（:273） | 支撑 |
| [66] 任一日志文件准备失败时清空两个 sink、关闭文件日志并返回错误（:293） | 支撑 |
| [67] get_log_file 返回已绑定的运行日志路径（:305） | 支撑 |
| [68] get_package_log_file 返回已绑定的 ToolPkg 日志路径（:315） | 支撑 |
| [69] get_log_file_path 未绑定时返回 `AppLogger log file is not bound` 错误（:325） | 支撑 |
| [70] reset_log_file 关闭两个日志文件、把文件内容写空并清除内存条目（:345，函数体 :344–:357） | 支撑 |
| [71] entries 返回内存日志条目的快照（:352，`.entries.clone()`） | 支撑 |
| [72] entries_json 把内存日志条目序列化为 JSON（:361） | 支撑 |
| [73] text 通过文件系统宿主读回运行日志文件的文本（:366，`readFile`） | 支撑 |
| [74] package_text 通过文件系统宿主读回 ToolPkg 日志文件的文本（:377） | 支撑 |
| [75] v 写 VERBOSE_LEVEL_1 级别的诊断（:388） | 支撑 |
| [76] v_with_level 对超出 VERBOSE_LEVEL_1 至 _6 的级别断言失败（:393，`assert!`） | 支撑 |
| [77] v_with_level 写入成功返回 0，失败返回 -1（:393） | 支撑 |
| [78] trace 写 V5，trace_detail 写 V6（:402） | 支撑 |
| [79] d 写 DEBUG，i 写 INFO（:415） | 支撑（锚行是空行，见问题 2） |
| [80] w 写 WARN，e 写 ERROR（:425） | 支撑（锚行是空行，见问题 2） |
| [81] wtf 写 ASSERT（:432） | 支撑 |
| [82] println 显式指定优先级，VERBOSE 时带 VERBOSE_LEVEL_1（:437） | 支撑 |
| [83] println_with_error 把错误链附加到日志消息（:451，`Some(error_chain(tr))` 在 :453，±5 内） | 支撑 |
| [84] get_stack_trace_string 非 ESP-IDF 用 Backtrace::capture（:461） | 支撑 |
| [85] ESP-IDF 返回 `Backtrace unavailable on ESP-IDF`（:465） | 支撑 |
| [86] is_loggable 只比较级别与控制台最低级别，忽略 tag 参数（:472，`_tag`） | 支撑 |
| [87] is_verbose_loggable 要求 VERBOSE 通过控制台阈值且级别在 V1 至当前上限内（:477） | 支撑 |
| [88] write_entry 时间戳取 TimeUtils::currentTimeMillisU128（:494） | 支撑 |
| [89] TOOLPKG_LOG_TAG 的值是 ToolPkg（:38） | 支撑 |
| [90] write_entry 在 tag 等于 TOOLPKG_LOG_TAG（忽略大小写）时额外生成一行包日志（:506，`eq_ignore_ascii_case`） | 支撑 |
| [91] write_entry 在保留历史开启时把条目追加到内存历史（:512） | 支撑 |
| [92] write_entry 把运行日志行追加到运行日志文件并把结果记入 write_result（:521） | 支撑 |
| [93] write_entry 在任一文件 sink 失败时返回 Err（:485，函数 doc 原文） | 支撑 |
| [94] 控制台输出先走 tryLogHostConsole，失败时 ERROR 与 ASSERT 走 stderr、其余走 stdout（:554） | 支撑 |
| [95] append_line 在批处理深度大于 0 时把同文件同宿主的写入合并到线程本地批（:575） | 支撑 |
| [96] LogFileWriteBatch 在 drop 时深度减 1，为 0 时取出全部攒写（:123） | 支撑 |
| [97] 取出的攒写经 append_line_with_rotation_cap 按文件刷入（:135） | 支撑 |
| [98] LogFileWriteBatch 的刷入在解开过程也会执行（:119，doc 原文 "including during error unwinding"） | 支撑 |
| [99] batch_file_writes 合并一个同步作用域内的文件写入（:176） | 支撑 |
| [100] batch_future_file_writes 只按每次同步轮询分批，future 让出或换线程前刷掉（:184） | 支撑 |
| [101] 追加时文件超过 4 MB 则轮转：旧文件移到 .1 归档并重建空文件（:654） | **存疑**（见问题 1：阈值部分无引用） |
| [102] 轮转前删掉已存在的旧 .1 归档（:642） | 支撑 |
| [103] 追加时部分写入失败会丢弃已缓存的句柄，不重试该记录（:622） | 支撑 |
| [104] 内存历史超过 4096 条时淘汰最旧记录，只保留最新 2048 条（:670） | 支撑 |
| [105] evict_log_file_oldest 只在日志文件超过 4 MB 时裁剪（:687，该行即 `size <= LOG_FILE_MAX_BYTES` 判断） | 支撑 |
| [106] 日志裁剪后写入一条 `oldest records evicted` 提示行（:699） | 支撑 |
| [107] ensure_log_file 在路径是目录时返回错误（:733） | 支撑 |
| [108] ensure_log_file 在路径缺失时建父目录并创建空文件（:743） | 支撑 |
| [109] ensure_log_file 在绑定时裁剪上次运行留下的超大日志（:751，`evict_log_file_oldest`） | 支撑 |
| [110] format_log_line 输出 `时间戳 优先级/标签: 消息`（:769） | 支撑 |
| [111] format_log_line 把 throwable 的每一行都带上相同前缀（:786） | 支撑 |
| [112] format_package_log_line 从消息里提取 toolPkgId 等 token 写成 [PKG:...]（:806） | 支撑 |
| [113] 从消息里提取 script 等 token 写成 [SCRIPT:...]（:811） | 支撑 |
| [114] 从消息里提取 plugin 等 token 写成 [PLUGIN:...]（:815） | 支撑 |
| [115] ESP-IDF 上时间戳只用 UTC 日时钟字段输出（:838） | 支撑 |
| [116] 非 ESP-IDF 上时间戳输出本地时间（:851，`with_timezone(&Local)`） | 支撑 |
| [117] priority_label 对 VERBOSE 带级别时输出 `V{级别}`，否则输出单个字符（:880） | 支撑 |
| [118] is_console_loggable 要求优先级不低于控制台最低级别，VERBOSE 还要求级别不超过上限（:893） | 支撑 |
| [119] extract_named_token 在消息里找 `name=` 标记并取到空白或逗号为止的值（:903） | 支撑 |
| [120] error_chain 把错误与各级 cause 拼成 `caused by` 链（:924） | 支撑 |
| [121] AppLogger 的测试在 AppLoggerTests.rs 文件里，用 #[path] 引入（:937；文件存在） | 支撑 |

### Stream.rs（[122]–[149]）：全部支撑

| fact | 判定 |
| --- | --- |
| [122] StreamLogger 的诊断开关默认启用（:60，`AtomicBool::new(true)`） | 支撑 |
| [123] StreamLogger::set_enabled 控制流诊断开关（:12） | 支撑 |
| [124] StreamLogger::d 把流调度与状态诊断写到 V5（:17，调 `AppLogger::trace`） | 支撑 |
| [125] StreamLogger::i 把逐项流细节写到 V6（:24，`v_with_level(..., VERBOSE_LEVEL_6)`） | 支撑 |
| [126] StreamLogger::v 把逐项流细节写到 V6（:35） | 支撑 |
| [127] StreamLogger::w 写警告级流诊断（:46） | 支撑 |
| [128] StreamLogger::e 写错误级流诊断（:53） | 支撑 |
| [129] StreamLogger 的诊断统一打 StreamFramework 标签（:20） | 支撑（锚行是 `}`，见问题 2） |
| [130] CollectFuture 与 ProducerFuture 是装箱的异步 future 类型（:63；ProducerFuture 在 :66） | 支撑 |
| [131] Stream 是拉取式异步流，Item 须 Send（:73，`type Item: Send`） | 支撑 |
| [132] Stream 的取消通常由生产者拥有，丢弃收集 future 只停止该收集器（:70，doc 原文） | 支撑 |
| [133] Stream 的 is_locked 与 buffered_count 默认返回 false 与 0（:77） | 支撑 |
| [134] Stream 的 lock、unlock 与 clear_buffer 默认是空实现（:90） | 支撑 |
| [135] Stream::collect 是唯一的必需方法，收集到生产者结束或关闭为止（:98） | 支撑 |
| [136] Box<S> 对 Stream 做转发实现（:101） | 支撑 |
| [137] StreamCollector::emit 向下游发送一个元素（:133） | 支撑 |
| [138] FnMut(T) 自动实现 StreamCollector（:138） | 支撑 |
| [139] VecStream 是内存队列支持的有限流（:148） | 支撑 |
| [140] VecStream::new 按迭代顺序收下元素（:157） | 支撑 |
| [141] VecStream::collect 先发出缓冲里的元素，再逐个发出队列元素（:206；队列循环在 :209，±5 内） | 支撑 |
| [142] VecStream 锁定时把新元素缓存在本地缓冲（:166，`try_buffer`：`locked && !closed` 时入缓冲） | 支撑（见备注：收集中 closed 恒为 false，省略 !closed 不改变行为） |
| [143] VecStream 收集结束时把流标记为已关闭（:215） | 支撑 |
| [144] FnStream 是冷流，生产者在异步收集时才运行（:221） | 支撑 |
| [145] FnStream::collect 先排空缓冲（:270） | 支撑 |
| [146] FnStream 发出元素时若锁定则进缓冲，否则直接交给收集器（:281） | 支撑（见备注：`locked` 在 collect 开始时快照；collect 持 `&mut self`，收集中无法再调 lock，快照与实时状态等价） |
| [147] FnStream 再次收集时以 `FnStream producer must only be collected once` 触发 panic（:280，`.take().expect(...)`） | 支撑 |
| [148] FnStream 收集结束时把流标记为已关闭（:289） | 支撑 |
| [149] 测试 fn_stream_starts_producer_during_collection 验证生产者在收集开始前不启动（:396） | 支撑 |

## 正文核对

- 结构：frontmatter 齐全（title / module / platforms / sources / date）；小节顺序为
  `## 概述 / ## AI 速览 / ## 核心机制 / ## 关键符号 / ## 调用链 / ## 来源`，与 SCHEMA §9.2 一致；
  `## AI 速览` 为固定第二小节；`## 来源` 存在且与 frontmatter sources 的 10 个文件一致。
- 禁用词：`可能/大概/似乎/应该/也许` 全文 0 命中。
- 引用：正文断言的引用与 facts 逐一对照，未发现超出 facts 覆盖的断言（除问题 3 的范围数字外）；
  关键符号 19 项的引用全部落在符号行或 ±5 行内；调用链 4 组 25 步的引用逐一核对无误
  （唯一同款问题见问题 1 的轮转句）。
- 跨页链接：`[[core-foundation|基础层——共享契约与数据模型]]` 格式正确（`[[id|标题]]`），
  目标页 `core-foundation` 在 batch-02 内存在。
- 平台标注：frontmatter `platforms: [all]`；平台分支行为在正文中均已注明平台——
  ESP-IDF 与非 ESP-IDF 的时间戳、栈捕获两处均以平台为条件分述，无单平台实现写成全平台结论。
- 文档声称 vs 实现：无混淆。`ArchiveUtil` 如实写为空占位 struct；
  "三个门控模块随默认构建编译"是 `default = ["full"]`（Cargo.toml:13）的直接推论，引用齐全；
  无设计约束写成已实现，无旧名、旧命令、断链。
- 范围诚实：概述明确声明只读 5 个文件 + 4 个子模块索引文件、其余模块只按 `lib.rs` 声明清点；
  正文无任何关于未读文件的实现断言；`AppLoggerTests.rs` 等 facts 外引用均已亲眼核实存在。

## 问题清单

### 问题 1（必修）：[101] 4 MB 阈值部分无引用支撑

- fact 原文：[101] "追加时文件超过 4 MB 则轮转：旧文件移到 .1 归档并重建空文件。"
  ref：`core/crates/foundation/util/src/AppLogger.rs:654`
- 代码实际内容：
  - :654 是 `rotate_log_file` 函数体内的 `.moveFile(path, &archive)`，即"旧文件移到 .1 归档"这一步；
    其 ±5 行（649–659）内没有任何关于 4 MB / 阈值的符号。
  - 4 MB 阈值检查在 `append_line_with_rotation_cap` 的 :613：
    `if writer.as_ref().unwrap().byteLength() > rotate_bytes as u64`，
    其中 `LOG_ROTATE_BYTES = LOG_FILE_MAX_BYTES = 4 * 1024 * 1024`（:630、:41）。
  - 断言本身为真，但"超过 4 MB"这半句在所引行 ±5 行内无支撑，违反 SCHEMA"引用行 ±5 行内必须出现断言中的符号名"。
- 怎么改：拆成两条 fact——阈值一条 ref :613，轮转动作一条 ref :654；
  正文"日志：写入路径、批处理与轮转"节同一句同步改成双引用，例如：
  "追加时文件超过 4 MB 则轮转（AppLogger.rs:613）：旧文件移到 .1 归档并重建空文件（AppLogger.rs:654）"。

### 问题 2（必修，小修）：[79]、[80]、[129] 的 ref 锚行不是符号行

- [79] 原文："AppLogger::d 写 DEBUG 级别，AppLogger::i 写 INFO 级别。" ref :415。
  代码实际：:415 是空行；`pub fn d` 在 :412，`pub fn i` 在 :417（均在 ±5 内，断言为真）。
  怎么改：fact 与正文同一行的 ref 均改为 :412。
- [80] 原文："AppLogger::w 写 WARN 级别，AppLogger::e 写 ERROR 级别。" ref :425。
  代码实际：:425 是空行；`pub fn w` 在 :422，`pub fn e` 在 :427。
  怎么改：fact 与正文同一行的 ref 均改为 :422。
- [129] 原文："StreamLogger 的诊断统一打 StreamFramework 标签。" ref `stream/Stream.rs:20`。
  代码实际：:20 是 `}` 闭括号；`StreamFramework` 字面量在 :19
  （`AppLogger::trace("StreamFramework", &format!(...))`）。
  怎么改：fact 与正文同一行的 ref 均改为 :19。

### 问题 3（必修，小修）：概述的范围数字无引用

- 正文原文（概述）："整 crate 共 79 个 `.rs` 文件、17,476 行"——无任何 file:line 引用，facts.json 里也没有这条。
- 代码实际内容：critic 直数复核属实（`find . -name '*.rs' | wc -l` = 79；`cat | wc -l` = 17,476；
  大纲 outline-v1.yaml 该页 notes 同样写"79 个 .rs、17,476 行"），数字为真，但按 SCHEMA"写不出引用的断言不许写"，页内断言应有引用。
- 怎么改：二选一——(a) 删去数字，只保留"其余模块本页只按 `lib.rs` 的声明做子能力清点，不描述未读实现"的范围声明；
  (b) 保留数字并注明为大纲清点（但这不是 file:line 引用，仍不合铁律，推荐选 a）。
  另同句"本页覆盖的 seed 是 `lib.rs` 等 5 个文件与 4 个子模块索引文件"数的是 9 个 .rs seed，
  frontmatter sources 另有 `Cargo.toml`，共 10 个文件，建议补"另加 Cargo.toml"以免被读成 seed 只有 9 个文件。

### 问题 4（建议，非阻断）：子能力清点漏两个公开模块

- 正文"子能力清点"分组共点了 46 个公开模块名，漏了 `AssetCopyUtils`（lib.rs:5）与 `TextSegmenter`（lib.rs:45）。
  两者 facts 已覆盖（[18]、[30]），只是正文没出现；lib.rs 公开模块共 48 个（含 3 个子树），正文未声明"仅列举部分"。
- 怎么改：在清点里补一行，例如"资产与分段：`AssetCopyUtils`（lib.rs:5）、`TextSegmenter`（lib.rs:45）"（两者行号不同，各挂各的引用，或分两行）。

### 问题 5（建议，非阻断）：[51] 措辞可更精确

- fact 原文：[51] "utf8SequenceLength 要求后续字节符合 0x80 掩码，否则返回 0。"
- 代码实际：:217 是 `(byte & 0xC0) == 0x80`——掩码是 0xC0，期望值是 0x80；"0x80 掩码"容易被读成掩码 = 0x80。
- 怎么改：改成"要求后续字节高两位为 10（`(byte & 0xC0) == 0x80`），否则返回 0"。

## 结论

**需修改。** 149 条 facts 中 148 条支撑、1 条存疑（[101] 阈值引用），无不支撑；
正文结构、禁用词、跨页链接、平台标注、范围声明全部合规。
必修项只有 3 处小修（问题 1–3），建议项 2 处（问题 4–5）；
修完后按 lint 复验即可进入评审，无需打回重写。
