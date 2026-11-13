---
title: 模型目录与模型识别
module: model
platforms: [all]
sources: 5
date: 2026-11-11
---

## 概述

- 模型目录是运行时从 models.dev 下载的数据：拉取模型、添加模型和对话时用到的价格、上下文长度、能力与思考档位来自该目录，程序里不再编译模型数据快照（文档说法，未在代码验证）。`docs/model-catalog.md:4`
- 对话时用到的价格、上下文长度、能力与思考档位来自该目录，调用侧见 [[model-chat-send|模型调用与聊天发送契约]]。`docs/model-catalog.md:4`
- 目录分两个文件下载，存到本机节点本地运行时存储，首次使用时从本地读取。`core/crates/runtime/application/src/services/ModelCatalogService.rs:204`
- 没有模型列表接口的服务商（`OPENAI_CODEX`）不请求服务商模型列表接口，模型行来自 `ModelCatalog.rs` 里手工维护的固定列表。`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:410`
- 固定列表不等于绕过目录初始化与下载：`requireCatalog` 与 `refreshCatalogIfStale` 在服务商列表抓取之前执行，能力解析仍要求 models.dev 目录就绪。`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:394`
- `ModelSpecResolver::new` 对非 `LOCAL_MODEL` 服务商先要求完整目录。`core/crates/runtime/application/src/data/preferences/ModelSpecResolver.rs:99`
- 本地运行的模型不依赖此目录（文档说法，本页 seed 代码未验证）。`docs/model-catalog.md:19`

## AI 速览

- `PROVIDER_CATALOG_URL` — 服务商目录的下载地址 `https://models.dev/api.json`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:24`
- `LAB_CATALOG_URL` — 厂商目录的下载地址 `https://models.dev/models.json`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:25`
- `STALE_AFTER_MS` — 过期阈值 24 小时。`core/crates/runtime/application/src/services/ModelCatalogService.rs:31`
- `RETRY_AFTER_MS` — 失败后 30 分钟内不自动重试。`core/crates/runtime/application/src/services/ModelCatalogService.rs:33`
- `CHECK_EVERY_MS` — 进程运行期间每小时检查一次目录年龄。`core/crates/runtime/application/src/services/ModelCatalogService.rs:35`
- `currentCatalog` — 返回在用目录，首次调用时从本地存储读入。`core/crates/runtime/application/src/services/ModelCatalogService.rs:60`
- `requireCatalog` — 等待首次完整目录。`core/crates/runtime/application/src/services/ModelCatalogService.rs:71`
- `catalogStatus` — 返回目录的 `updatedAt` 与 `lastError`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:103`
- `refreshCatalog` — 立即下载目录并返回状态。`core/crates/runtime/application/src/services/ModelCatalogService.rs:113`
- `refreshCatalogIfStale` — 仅在本地副本缺失或超过一天时下载。`core/crates/runtime/application/src/services/ModelCatalogService.rs:122`
- `startKeepingFresh` — 调度定期检查任务。`core/crates/runtime/application/src/services/ModelCatalogService.rs:139`
- `MODEL_CATALOG_MODEL_ROWS` — 无模型列表接口的服务商的固定模型列表，共 20 行，全部属于 `OPENAI_CODEX`。`core/crates/foundation/model/collects/ModelCatalog.rs:3`
- 主入口函数是 `requireCatalog`：等待首次完整目录。`core/crates/runtime/application/src/services/ModelCatalogService.rs:71`
- 另一主入口是 `refreshCatalogIfStale`：仅在本地副本缺失或超过一天时下载。`core/crates/runtime/application/src/services/ModelCatalogService.rs:122`
- 数据流向一句话：`PROVIDER_CATALOG_URL` 与 `LAB_CATALOG_URL` 下载到本机缓存，经 `ModelsDevCatalog::parse` 解析成在用目录。`core/crates/runtime/application/src/services/ModelCatalogService.rs:204`
- 无模型列表接口的服务商改用 `MODEL_CATALOG_MODEL_ROWS` 固定列表。`core/crates/foundation/model/collects/ModelCatalog.rs:3`

## 核心机制

### 数据来源

- 服务商目录从 `https://models.dev/api.json` 下载，厂商目录从 `https://models.dev/models.json` 下载。`core/crates/runtime/application/src/services/ModelCatalogService.rs:24`
- 文档称 `api.json` 是各服务商的模型，`models.json` 是各厂商的模型，补充没有服务商列出、但账号可以调用的模型（文档说法，未在代码验证）。`docs/model-catalog.md:8`
- 两个目录文件下载后经 `ModelsDevCatalog::parse` 解析成在用目录。`core/crates/runtime/application/src/services/ModelCatalogService.rs:204`
- 文档称目录保存在设备本地 `runtime/cache/models_dev/`，不参与 Space 同步（文档说法，未在代码验证）。`docs/model-catalog.md:10`
- 目录文件按 `RUNTIME_MODELS_DEV_CACHE_DIR_PATH` 加文件名寻址。`core/crates/runtime/application/src/services/ModelCatalogService.rs:297`
- 服务商目录文件名为 `api.json`，厂商目录文件名为 `models.json`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:26`
- 完成标记文件名为 `downloaded.json`，常量 `STAMP_FILE`，最后写入。`core/crates/runtime/application/src/services/ModelCatalogService.rs:29`
- 时间戳文件内容为含 `updatedAt` 的 JSON。`core/crates/runtime/application/src/services/ModelCatalogService.rs:247`

### 过期与刷新

- 目录超过 24 小时视为过期，`STALE_AFTER_MS` 为 24 小时。`core/crates/runtime/application/src/services/ModelCatalogService.rs:31`
- 文档称用户拉取模型时过期的目录先重新下载，进程运行期间每小时检查一次（文档说法；24 小时过期阈值与每小时检查已由代码验证）。`docs/model-catalog.md:12`
- 进程运行期间按 `CHECK_EVERY_MS`（1 小时）检查目录年龄。`core/crates/runtime/application/src/services/ModelCatalogService.rs:35`
- 本地目录缺失下载时间，或下载时间距今超过 `STALE_AFTER_MS` 时，需要重新下载。`core/crates/runtime/application/src/services/ModelCatalogService.rs:171`
- 下载失败后 30 分钟内不自动重试：`needsDownload` 在 `lastFailureAt` 距今不足 `RETRY_AFTER_MS` 时返回 false。`core/crates/runtime/application/src/services/ModelCatalogService.rs:163`
- `refreshCatalog` 立即下载目录并返回状态。`core/crates/runtime/application/src/services/ModelCatalogService.rs:113`
- 文档称用户可通过 `refreshModelCatalog` 手动重试；该符号未出现在本页 seed 代码中（文档说法，未在代码验证）。`docs/model-catalog.md:15`

### 首次使用与失败处理

- `currentCatalog` 首次调用时经 `loadStoredCatalog` 从本地存储读入目录。`core/crates/runtime/application/src/services/ModelCatalogService.rs:60`
- `loadStoredCatalog` 在时间戳文件不存在时不加载目录，返回空。`core/crates/runtime/application/src/services/ModelCatalogService.rs:259`
- 时间戳文件中的 `updatedAt` 是目录的下载时间。`core/crates/runtime/application/src/services/ModelCatalogService.rs:270`
- 本地保存的两个目录文件读回后经 `ModelsDevCatalog::parse` 解析。`core/crates/runtime/application/src/services/ModelCatalogService.rs:279`
- `requireCatalog` 等待首次完整目录，并发调用共用正在进行的下载。`core/crates/runtime/application/src/services/ModelCatalogService.rs:71`
- `requireCatalog` 的新调用可不受后台重试间隔限制重试首次下载失败。`core/crates/runtime/application/src/services/ModelCatalogService.rs:70`
- 文档称用户再次操作会立即重试首次下载，不受后台 30 分钟重试间隔限制；并发操作共用正在进行的下载及其结果（文档说法；立即重试与共用下载已由代码验证）。`docs/model-catalog.md:18`
- 目录不可用时 `requiredCatalogResult` 返回报错，提示目录未就绪、需先下载 models.dev。`core/crates/runtime/application/src/services/ModelCatalogService.rs:92`
- 代码注释说明目录不可用时上报错误，而不是把缺失事实解释为能力关闭。`core/crates/runtime/application/src/services/ModelCatalogService.rs:91`
- 文档称首次安装或目录缓存缺失时，远程模型的能力解析等待完整目录下载成功，再返回模型列表、添加模型或读取模型配置（文档说法；等待完整目录的机制已由代码验证）。`docs/model-catalog.md:16`
- 下载失败时记录 `lastError` 与 `lastFailureAt`，在用目录保持不变。`core/crates/runtime/application/src/services/ModelCatalogService.rs:194`
- 下载成功时在用目录被替换，`updatedAt` 更新，`lastError` 与 `lastFailureAt` 清空。`core/crates/runtime/application/src/services/ModelCatalogService.rs:186`
- `catalogStatus` 返回 `ModelCatalogStatus`，含 `updatedAt` 与 `lastError`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:103`
- 文档称下载失败原因通过 `getModelCatalogStatus` 提供给界面；该符号未出现在本页 seed 代码中（文档说法，未在代码验证）。`docs/model-catalog.md:14`
- 本地目录读入失败时记录 `lastError` 并记一条警告日志。`core/crates/runtime/application/src/services/ModelCatalogService.rs:290`
- 静态 `DOWNLOAD` 锁串行化下载，后台检查与拉取不会重复下载。`core/crates/runtime/application/src/services/ModelCatalogService.rs:51`
- `download` 以 GET 请求拉取目录文件，请求头 `User-Agent` 为 `Operit`，连接超时 15 秒，读取超时 60 秒。`core/crates/runtime/application/src/services/ModelCatalogService.rs:214`
- `download` 在 HTTP 状态码不在 200-299 时返回带状态码的错误。`core/crates/runtime/application/src/services/ModelCatalogService.rs:214`
- `storeCatalog` 先保存两个目录文件，再写入为目录标注下载时间的 stamp。`core/crates/runtime/application/src/services/ModelCatalogService.rs:233`

### 固定列表：没有模型列表接口的服务商

- 固定列表以 `pub const MODEL_CATALOG_MODEL_ROWS` 字符串常量手工维护。`core/crates/foundation/model/collects/ModelCatalog.rs:3`
- 固定列表的表头注释说明其为无模型列表接口的服务商的固定列表，列依次为 provider、model、billing、input、cached input、output、per request、currency、context K、image、audio、video、builtin web search、tool call、structured tools。`core/crates/foundation/model/collects/ModelCatalog.rs:2`
- 固定列表共 20 行模型记录，全部属于 `OPENAI_CODEX`。`core/crates/foundation/model/collects/ModelCatalog.rs:3`
- 固定列表首行是 `OPENAI_CODEX` 的 `gpt-5.3-codex-spark`：TOKEN 计费，输入价 1.75、缓存输入价 0.175、输出价 14，上下文 128K，支持图片、内置联网搜索、工具调用与结构化工具，不支持音频与视频输入。`core/crates/foundation/model/collects/ModelCatalog.rs:4`
- 固定列表中 `gpt-5.4` 的输入价为 2.5、缓存输入价 0.25、输出价 15（USD，TOKEN 计费），上下文为 1050K，支持图片、内置联网搜索、工具调用与结构化工具，不支持音频与视频输入。`core/crates/foundation/model/collects/ModelCatalog.rs:5`
- 固定列表最后一行是 `OPENAI_CODEX` 的 `gpt-6-sol-fast`。`core/crates/foundation/model/collects/ModelCatalog.rs:23`
- 固定列表的列定义中没有思考档位相关列。`core/crates/foundation/model/collects/ModelCatalog.rs:2`

### 识别规则（文档说法）

- 文档称模型匹配在 `ModelsDevCatalog.rs`，按顺序查找，先找到的生效（文档说法；该文件不在本页 seed 清单中，未在代码验证）。`docs/model-catalog.md:25`
- 文档称服务商自己在 models.dev 里的条目优先：服务商按接口地址对应到 models.dev 的 `api` 字段；models.dev 没有记录地址的官方服务商按服务商类型对应，只限接口地址在该厂商自己的服务器上（文档说法，未在代码验证）。`docs/model-catalog.md:27`
- 文档称不分服务商按去掉 `/` 前缀的小写模型 ID 查找，上下文与能力取多数条目的说法，条目的 `canonical_model_id` 也算该模型的 ID（文档说法，未在代码验证）。`docs/model-catalog.md:31`
- 文档称 `-pro-max` 与 `-pro`、`-mini`、`:batch`、`-2507` 等变体不会被当成同一个模型；价格只取对应服务商自己的条目，不使用其他服务商的价格（文档说法，未在代码验证）。`docs/model-catalog.md:39`
- 文档称目录识别不了的模型使用添加时服务商列表自带的信息（目前只有 OpenRouter 提供），再使用默认值（文档说法，未在代码验证）。`docs/model-catalog.md:47`
- 文档称本机安装的本地模型不参与识别，按本地运行配置描述（文档说法，本页 seed 代码未验证）。`docs/model-catalog.md:48`

### 用户设置与目录（文档说法）

- 文档称模型配置里的 `*Override` 字段只保存用户改过的值，按字段区分；没改过的字段在读取时按目录计算，目录更新后已添加模型里用户没改过的字段跟着更新（文档说法，未在代码验证）。`docs/model-catalog.md:44`
- 文档称保存时和目录值相同的字段不会记为用户设置；上下文按整千 token 比较，因为设置页按整千显示（文档说法，未在代码验证）。`docs/model-catalog.md:46`

### 思考档位（文档说法）

- 文档称模型能怎么思考取自 models.dev 条目的 `reasoning` 和 `reasoning_options`：一个开关、若干 effort 档位、一个 token 预算，或者都没有；厂商目录（`models.json`）不记录思考控制（文档说法，未在代码验证）。`docs/model-catalog.md:52`
- 文档称思考档位统一成 `off`、`enabled`、`minimal`、`low`、`medium`、`high`、`xhigh`、`max`，界面在各种语言下都显示这些写法（文档说法，未在代码验证）。`docs/model-catalog.md:60`
- 文档称档位按模型保存为 `ModelProfile.thinkingLevel`；没设置过的模型沿用最近一次在任意模型上设置的档位，换成该模型最接近的一档（文档说法，未在代码验证）。`docs/model-catalog.md:63`
- 文档称目录没有或说得不对的模型，用户可自己描述为 `ModelProfile.thinkingOverride`，描述整体替换目录的说法（文档说法，未在代码验证）。`docs/model-catalog.md:66`
- 文档称本机运行的本地模型由内置运行时处理，每个模型都可开关思考（文档说法，本页 seed 代码未验证）。`docs/model-catalog.md:67`
- 文档给出命令行 `operit2 model catalog-status`、`operit2 model catalog-refresh` 与 `operit2 model thinking <provider-id> <model-id> [档位]`（文档说法，未在代码验证）。`docs/model-catalog.md:101`
- 文档称 `provider-model-available-list` 的输出列出每个模型识别成的目录模型（文档说法，未在代码验证）。`docs/model-catalog.md:106`

## 关键符号

- `PROVIDER_CATALOG_URL`：服务商目录下载地址 `https://models.dev/api.json`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:24`
- `LAB_CATALOG_URL`：厂商目录下载地址 `https://models.dev/models.json`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:25`
- `PROVIDER_CATALOG_FILE`：服务商目录文件名 `api.json`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:26`
- `LAB_CATALOG_FILE`：厂商目录文件名 `models.json`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:27`
- `STAMP_FILE`：完成标记文件名 `downloaded.json`，最后写入。`core/crates/runtime/application/src/services/ModelCatalogService.rs:29`
- `STALE_AFTER_MS`：过期阈值，24 小时。`core/crates/runtime/application/src/services/ModelCatalogService.rs:31`
- `RETRY_AFTER_MS`：失败后不自动重试的间隔，30 分钟。`core/crates/runtime/application/src/services/ModelCatalogService.rs:33`
- `CHECK_EVERY_MS`：进程运行期间检查目录年龄的间隔，1 小时。`core/crates/runtime/application/src/services/ModelCatalogService.rs:35`
- `DOWNLOAD`：串行化下载的静态互斥锁。`core/crates/runtime/application/src/services/ModelCatalogService.rs:51`
- `currentCatalog`：返回在用目录（`Option<Arc<ModelsDevCatalog>>`），首次调用时从本地存储读入。`core/crates/runtime/application/src/services/ModelCatalogService.rs:60`
- `requireCatalog`：等待首次完整目录，返回 `Result<Arc<ModelsDevCatalog>, String>`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:71`
- `requiredCatalogResult`：目录缺失时返回未就绪报错。`core/crates/runtime/application/src/services/ModelCatalogService.rs:92`
- `catalogStatus`：返回 `ModelCatalogStatus`（`updatedAt` 与 `lastError`）。`core/crates/runtime/application/src/services/ModelCatalogService.rs:103`
- `refreshCatalog`：立即下载目录并返回状态。`core/crates/runtime/application/src/services/ModelCatalogService.rs:113`
- `refreshCatalogIfStale`：仅在本地副本缺失或超过一天时下载。`core/crates/runtime/application/src/services/ModelCatalogService.rs:122`
- `startKeepingFresh`：调度 `model-catalog-refresh` 任务启动定期检查。`core/crates/runtime/application/src/services/ModelCatalogService.rs:139`
- `checkAndReschedule`：执行过期检查后按 `CHECK_EVERY_MS` 安排下一次检查。`core/crates/runtime/application/src/services/ModelCatalogService.rs:150`
- `needsDownload`：判断本地目录是否缺失、过期且不在失败冷却期内。`core/crates/runtime/application/src/services/ModelCatalogService.rs:163`
- `downloadCatalog`：下载两个目录文件、保存并投入使用；失败时保留在用目录。`core/crates/runtime/application/src/services/ModelCatalogService.rs:175`
- `fetchCatalog`：下载两个目录文件并经 `ModelsDevCatalog::parse` 解析。`core/crates/runtime/application/src/services/ModelCatalogService.rs:204`
- `download`：以 GET 请求拉取单个目录文件，连接超时 15 秒，读取超时 60 秒。`core/crates/runtime/application/src/services/ModelCatalogService.rs:214`
- `storeCatalog`：先保存两个目录文件，再写入为目录标注下载时间的 stamp。`core/crates/runtime/application/src/services/ModelCatalogService.rs:233`
- `loadStoredCatalog`：从本地存储读回目录与下载时间；时间戳缺失时返回空。`core/crates/runtime/application/src/services/ModelCatalogService.rs:259`
- `cachePath`：把目录文件定位在 `RUNTIME_MODELS_DEV_CACHE_DIR_PATH` 之下。`core/crates/runtime/application/src/services/ModelCatalogService.rs:297`
- `MODEL_CATALOG_MODEL_ROWS`：无模型列表接口的服务商的固定模型列表，手工维护的字符串常量。`core/crates/foundation/model/collects/ModelCatalog.rs:3`

## 调用链

1. `startKeepingFresh` 调度名为 `model-catalog-refresh` 的任务启动定期检查。`core/crates/runtime/application/src/services/ModelCatalogService.rs:139`
2. `checkAndReschedule` 执行 `refreshCatalogIfStale` 后按 `CHECK_EVERY_MS` 安排下一次检查。`core/crates/runtime/application/src/services/ModelCatalogService.rs:150`
3. `currentCatalog` 首次调用时经 `loadStoredCatalog` 从本地存储读入目录。`core/crates/runtime/application/src/services/ModelCatalogService.rs:60`
4. 时间戳文件不存在时 `loadStoredCatalog` 不加载目录，返回空。`core/crates/runtime/application/src/services/ModelCatalogService.rs:259`
5. 需要能力解析时 `requireCatalog` 等待首次完整目录。`core/crates/runtime/application/src/services/ModelCatalogService.rs:71`
6. 目录缺失且下载失败时 `requiredCatalogResult` 返回报错，不把缺失事实解释为能力关闭。`core/crates/runtime/application/src/services/ModelCatalogService.rs:92`
7. `needsDownload` 为 true 时触发 `downloadCatalog`；为 false 时直接返回。`core/crates/runtime/application/src/services/ModelCatalogService.rs:128`
8. `fetchCatalog` 下载两个目录文件并经 `ModelsDevCatalog::parse` 解析。`core/crates/runtime/application/src/services/ModelCatalogService.rs:204`
9. `storeCatalog` 先保存两个目录文件，再写入为目录标注下载时间的 stamp。`core/crates/runtime/application/src/services/ModelCatalogService.rs:233`
10. 下载成功后在用目录被替换，`updatedAt` 更新。`core/crates/runtime/application/src/services/ModelCatalogService.rs:186`
11. 下载失败时记录 `lastError` 与 `lastFailureAt`，在用目录保持不变。`core/crates/runtime/application/src/services/ModelCatalogService.rs:194`
12. `catalogStatus` 返回 `updatedAt` 与 `lastError`。`core/crates/runtime/application/src/services/ModelCatalogService.rs:103`
13. 没有模型列表接口的服务商（`OPENAI_CODEX`）跳过服务商列表抓取，模型行来自固定列表；但该路径仍先执行 `requireCatalog` 与过期刷新，能力解析要求 models.dev 目录就绪。`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:394`

## 来源

- `docs/model-catalog.md`
- `core/crates/runtime/application/src/services/ModelCatalogService.rs`
- `core/crates/foundation/model/collects/ModelCatalog.rs`
- 三份 seed 文件合计 428 行（文档 106 行、服务 298 行、固定列表 24 行），与大纲 `est_lines: 428` 一致；源码基线为 `AAswordman/Operit2 @ 364d1d594`（2026-11-11，本地 checkout 已核验 `git rev-parse HEAD`）。
- 为核实固定列表与目录初始化的关系，另读 `core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs` 与 `ModelSpecResolver.rs`（基线 364d1d594；非本页 seed）。`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:389`
- 价格、上下文长度、能力、思考档位的来源，识别规则，用户设置与目录的关系，思考档位，命令行均为文档说法，本页两份代码 seed 未验证对应实现。`docs/model-catalog.md:4`
- 否定性结论核验方法（2026-11-12，基线 364d1d594）：对三份 seed 文件执行 `grep -rn "getModelCatalogStatus|refreshModelCatalog|ModelProfile|ThinkingDialect"`，仅 `docs/model-catalog.md` 命中，两份代码文件零命中；`grep -rn "thinking|reasoning"` 同样仅文档命中；固定列表列定义逐字读 `ModelCatalog.rs` 第 2 行表头注释，无思考档位相关列；`grep -c "^OPENAI_CODEX"` 得 20 行且无其他服务商行；代码中 `local` 仅出现在 `node-local runtime storage`（`ModelCatalogService.rs` 第 4 行与第 295 行），无本地模型路径的表述，本地模型不依赖目录的说法只来自文档。`core/crates/foundation/model/collects/ModelCatalog.rs:2`
- 未读文件：文档提到的 `core/crates/foundation/model/src/ModelsDevCatalog.rs` 不在本页 seed 清单中，未读未引。`docs/model-catalog.md:25`
- 文档提到的 `core/crates/provider/services/src/chat/llmprovider/ThinkingDialect.rs` 同样不在本页 seed 清单中，未读未引。`docs/model-catalog.md:55`
- 文档中"模型连接检测结果"一节超出本页四问范围，未写入正文。`docs/model-catalog.md:69`
- 三份 seed 文件中无平台分支表述，`platforms: [all]` 指 Core 侧目录服务本身不区分 Host。
