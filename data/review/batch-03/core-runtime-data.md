---
title: Runtime——数据与插件宿主
module: core
platforms: [all]
sources: 6
date: 2026-11-11
---

## 概述

- 本页覆盖 core/crates/runtime/application 内的两块宿主职责：数据侧的 Operit1 快照导入迁移与插件侧的内置插件注册和 ToolPkg 会话创建钩子（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:326`）。
- 数据侧的导入器是 `Operit1SnapshotImportManager`，它把 Operit1（Android 一代）的备份快照解析后写入 Operit2 运行时存储（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:328`）。
- 插件侧的注册表是 `PluginRegistry`，它是内置运行时插件的全局注册表（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:19`）。
- 快照源自 Android 一代应用：内部路径以 `com.ai.assistance.operit` 开头（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:104`）。
- 默认头像为 `file:///android_asset/operit.png`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:111`）。
- 偏好分层在本页 seed 内只在导入侧可见，详见“偏好数据的导入侧分流”小节；AgreementPreferences.rs 全文件只有一行空 struct 声明，不含分层实现（`core/crates/runtime/application/src/data/preferences/AgreementPreferences.rs:1`）。

## AI 速览

- `Operit1SnapshotImportManager` — Operit1 快照导入器，持 paths 与三个存储宿主（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:328`）。
- `inspectSnapshotSource` — 读快照返回导入前预览（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:351`）。
- `importSnapshotSource` — 整快照导入，返回导入后计数（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:382`）。
- `Operit1SnapshotPreview` — 导入前预览，含聊天数、消息数与文件数（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:119`）。
- `Operit1SnapshotImportResult` — 导入后计数，含聊天、消息、统计、记忆与文件数（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:146`）。
- `Operit1SnapshotImportProgress` — 导入进度，含 stage、title、detail、progress、active（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:165`）。
- `PluginRegistry` — 内置插件全局注册表（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:19`）。
- `OperitPlugin` — 运行时插件契约：`id`() 与 `register`()（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:10`）。
- `ToolboxPlugin` — id 为 `builtin.toolbox`、注册为空实现的内置插件（`core/crates/runtime/application/src/plugins/toolbox/ToolboxPlugin.rs:6`）。
- 构建期生成的插件资产引入点，全文件只有一行 `include!`（`core/crates/runtime/application/src/plugins/BuiltinPluginAssets.rs:1`）。
- `snapshot()` — 会话创建前钩子桥的快照入口（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:73`）。
- `CHAT_LIFECYCLE_BEFORE_CREATE` — 唯一创建生命周期阶段 `before_create`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:20`）。
- `AgreementPreferences` — 空 struct，全文件只有一行声明（`core/crates/runtime/application/src/data/preferences/AgreementPreferences.rs:1`）。
- 主入口函数：数据侧为 `importSnapshotSource`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:382`）。
- 主入口函数：插件侧为 `initializeBuiltins`（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:46`）。
- 数据流向：快照源 → 解析 → 模型配置 → 语音、偏好、文件、聊天、统计 → 运行时存储（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:410`）。
- 数据流向：插件侧为注册 → 一次性初始化 → 安装 → 会话创建前钩子分发（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:59`）。

## 核心机制

### Operit1 快照导入

- 快照格式版本 `FORMAT_VERSION` 为 1（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:75`）。
- 清单条目 `ENTRY_MANIFEST` 为 `manifest.json`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:76`）。
- 模型配置条目位于 `payload/files/datastore/model_configs.preferences_pb`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:77`）。
- 角色卡、角色组、提示词标签条目分别为 `character_cards`、`character_groups`、`prompt_tags.preferences_pb`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:79`）。
- 语音服务条目为 `speech_services_preferences.preferences_pb`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:82`）。
- 用户偏好条目为 `user_preferences.preferences_pb`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:84`）。
- 聊天数据库条目为 `payload/databases/app_database`，WAL 与 SHM 边车为同名加 `-wal` 与 `-shm`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:85`）。
- ObjectBox 默认数据条目为 `payload/files/objectbox/data.mdb`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:88`）。
- 快照内路径前缀分四类：datastore 在 `payload/files/datastore/`，普通文件在 `payload/files/`，工作区文件在 `payload/files/workspace/`，外部文件在 `payload/external_files/`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:89`）。
- Operit1 内部文件前缀列出 4 条 Android 路径，包名 `com.ai.assistance.operit` 及其 `.debug` 变体（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:104`）。
- 外部下载前缀为 `/storage/emulated/0/Download/Operit/`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:110`）。
- 快照条目复制缓冲区为 256 * 1024 字节（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:102`）。
- 导入首先进入 parse 阶段，解析清单、配置与数据索引，进度 0.08（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:415`）。
- model_config 阶段调 `importAllModelConfigsFromParsed` 迁移全部模型配置（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:427`）。
- structured_preferences 阶段只调 `importSpeechPreferences` 迁移语音配置，仅导入 TTS 配置（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:435`）。
- preferences 阶段调 `importDataStorePreferences` 迁移偏好设置（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:440`）。
- files 阶段调 `importSnapshotFiles` 迁移资源文件（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:450`）。
- chats 阶段调 `importChatDatabase` 迁移聊天记录，随后调 `importTokenStatistics`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:456`）。
- `importSpeechPreferences` 只采纳语音配置，旧角色卡、角色组、提示词标签与记忆记录仍留在源数据（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:482`）。
- 预览的 `detectedDomains` 报告源中实际检测到的域，包括恢复时永不采纳的旧域（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:127`）。
- 导入结果的 `importedMemories` 计数角色插件实际采纳的记忆记录（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:150`）。
- 导入结果的 `importedMemoryLinks` 计数采纳的记忆链接数，不是源快照中存在的链接数（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:152`）。
- 空闲导入进度 stage 为 `idle`，title 为 `等待导入`，progress 为 0.0，active 为 false（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:173`）。
- 完成导入进度 stage 为 `completed`，progress 为 1.0，active 为 false（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:198`）。
- 进度节流在完成数达到总数、首次发布或距上次发布达到 `OPERIT1_PROGRESS_REPORT_INTERVAL_MS` 时才发布进度（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:274`）。
- 进度节流间隔 `OPERIT1_PROGRESS_REPORT_INTERVAL_MS` 为 250 毫秒（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:103`）。
- `observeOperit1SnapshotImportProgress` 返回导入进度的 `StateFlow` 供订阅（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:218`）。
- 导入进度经 `operit1SnapshotImportProgressFlow().set_value` 发布（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:235`）。
- 聊天数据库条目 `ENTRY_DATABASE` 暂存到 `OPERIT1_SNAPSHOT_SQLITE_INSPECTION_PATH`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:973`）。
- WAL 与 SHM 边车仅当快照中存在对应条目时才暂存（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:956`）。
- 暂存的聊天库经 sqliteHost 的 `openSqliteDatabase` 打开，再经 `prepareOperit1RoomImport` 规范化（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:990`）。
- 暂存条目经 `writeArchiveEntryToStorage` 写入暂存路径，操作完成后经 storageHost 的 `delete` 删除（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:939`）。
- 聊天解析用 `buildChatArchiveFromOperit1ToOperit2DatabaseBridge` 从旧库构建归档（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:711`）。
- 角色与记忆导入由 chats 阶段的 importChatDatabase 内调 `importCharactersAndMemory` 完成（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:717`）。
- 归档绑定由 `resolveOperit1ArchiveBindings` 解析（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:718`）。
- 归档绑定由 `publishOperit1ArchiveBindings` 发布（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:759`）。
- 聊天归档经 ChatHistoryManager 的 `importChatArchiveWithProgress` 写入并带进度回调（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:743`）。
- `importTokenStatistics` 仅当桥为 `Operit1RoomV21ToOperit2SqliteV29` 时导入，否则返回 (0, 0)（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:783`）。
- token 用量从 `token_usage_records` 表读取（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:794`）。
- 定价模型从 `token_stats_models` 表读取（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:806`）。
- 文件复制按 `buildSnapshotFileCopyPlan` 逐条进行（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:870`）。
- 复制经 `copyEntriesTo` 逐条回调，由 `writeArchiveReaderToStorage` 写入目标存储（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:886`）。
- 导入器文件末尾用 `include!` 引入 6 个 `operit1` 子文件，子文件内的映射表与转换细节不在本页 seed 内（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:1010`）。
- 导入器文件末尾还用 `include!` 引入 `Operit1CharacterPluginMigration.rs`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:1019`）。

### 单个模型配置导入

- `inspectModelConfigSnapshotSource` 只读模型配置预览（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:492`）。
- `importModelConfigSnapshotSource` 按 `configId` 与 `modelId` 导入单个模型配置（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:501`）。
- 模型配置的 `modelId` 须在其 `modelIds` 内，否则报错（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:529`）。
- 配置的 `apiEndpoint` 非空，否则报错缺少服务地址（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:535`）。
- 单配置导入用 `buildOperit1ProviderProfile` 以 `DEFAULT_PROVIDER_ID` 构建供应商档案（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:538`）。
- 单配置导入调用 ModelConfigManager 的 `replaceDefaultProviderProfile` 替换默认供应商档案（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:545`）。
- 单配置导入调用 FunctionalConfigManager::setModelForFunction(FunctionType::CHAT, DEFAULT_PROVIDER_ID, modelId) 绑定聊天功能模型（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:551`）。
- 导入结果 `Operit1ModelConfigImportResult` 含 `providerId`、`providerTypeId`、`providerName`、`modelId`、`importedModelCount`、`chatBindingUpdated`、`skippedFields`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:318`）。

### 偏好数据的导入侧分流

- 导入只统计含非未采纳键的偏好文件，未采纳键由 `isOperit1UnadoptedPreferenceKey` 过滤（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:580`）。
- `user_preferences` 文件先跑 UserPreferencesManager 的 `migratePreferences`(1)，再经 `UserPreferencesManager::store` 写入（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:601`）。
- `ENTRY_USER_PREFERENCES` 在写入前还跑 `migratePreferences`(2) 与 `migratePreferences`(3)（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:638`）。
- `api_settings` 文件跑 ApiPreferences 的 `migratePreferences`(1) 后经 `ApiPreferences::store` 写入（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:607`）。
- `github_auth` 文件先跑 `migrateOperit1GitHubUserInfo`，再跑 GitHubAuthPreferences 的 `migratePreferences`(1)（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:614`）。
- `current_chat_id` 文件写入 `CoreNodeStateStore`，路径为 `CURRENT_CHAT_ID_PREFERENCES_PATH`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:618`）。
- 其余偏好文件默认写入 `PreferencesDataStore::new(filePath)`（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:625`）。
- 非字符串偏好值经 `toTargetNativePreferenceEntry` 转为目标原生条目（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:632`）。
- 导入时 `active_theme_config_id` 置为 `Value::Null`，因为导入的普通外观不属于目标已选保存主题（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:650`）。
- 偏好存储的落盘实现见 [[core-persistence-store|持久化——store 聚合 crate]]（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:625`）。

### 插件注册表

- `OperitPlugin` trait 要求 `Send` 与 `Sync`，含 `id`() 与 `register`() 两个方法（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:10`）。
- 注册表用 `PLUGINS`、`INSTALLED_PLUGIN_IDS`、`BUILTINS_INITIALIZED` 三个 `OnceLock` 全局静态量保存状态（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:19`）。
- `register` 按 id 去重替换：先 `retain` 掉同 id 的已注册插件再 `push`（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:27`）。
- `register` 记录 `plugin.registry.register` 日志并带 `pluginId`（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:34`）。
- `initializeBuiltins` 用 `BUILTINS_INITIALIZED` 布尔门控保证内置插件只初始化一次（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:46`）。
- 初始化注册 `ToolboxPlugin` 与 ToolPkgCommonBridgePlugin 的 `new`(toolpkg_runtime)，随后调 `installAll`（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:59`）。
- 克隆插件列表并记录 `plugin.registry.install.scan` 日志，含 `pluginCount`（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:75`）。
- 每个插件只安装一次：已安装 id 集合 `insert` 成功才调 `plugin.register()`（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:90`）。
- `ToolboxPlugin` 实现 `OperitPlugin`，id 为 `builtin.toolbox`（`core/crates/runtime/application/src/plugins/toolbox/ToolboxPlugin.rs:6`）。
- ToolboxPlugin 的 `register`() 为空实现（`core/crates/runtime/application/src/plugins/toolbox/ToolboxPlugin.rs:10`）。
- BuiltinPluginAssets.rs 全文件只有一行 `include!`，引入构建期生成的 `builtin_plugin_assets.rs`（`core/crates/runtime/application/src/plugins/BuiltinPluginAssets.rs:1`）。

### ToolPkg 会话创建钩子桥

- `CHAT_LIFECYCLE_RUNTIME` 是进程级 `Mutex<Option<ToolPkgBridgeRuntime>>`，`OperitApplication` 为进程级所有者，主、浮窗、分离聊天槽共享同一运行时（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:17`）。
- `CHAT_LIFECYCLE_BEFORE_CREATE` 为 `before_create`，是唯一支持的创建生命周期阶段（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:20`）。
- `ToolPkgChatCreationKind` 分 `New` 与 `Branch` 两类，序列化为小写（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:26`）。
- `ToolPkgChatCreationChat` 含 `id`、`title`、`workspaceId`、`parentChatId`，只携带通用已分配草稿身份（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:37`）。
- `ToolPkgChatCreationDraft` 含 `creationKind`、`chat`、`sourceChatId`、`sourceMessageTimestamp`、`input`，不含角色、群组、记忆或完整扩展映射字段（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:48`）。
- `ToolPkgChatLifecycleDispatchContext` 持有分离的已就绪运行时快照，`await` 期间不保留包管理器互斥锁（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:55`）。
- `register` 覆盖当前运行时，应用重启后合法替换前任所有者（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:64`）。
- `snapshot` 返回 `ToolPkgChatLifecycleDispatchContext`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:73`）。
- 运行时未注册时报错 `Chat lifecycle runtime is not registered`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:84`）。
- `dispatchBeforeCreate` 先调 `validateCreationDraft` 校验草稿，再按序执行各所有者钩子（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:95`）。
- 无钩子时直接返回空 `BTreeMap`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:102`）。
- 钩子超时预算取自 ApiPreferences 的 `getToolPkgPreHookTimeoutSeconds`，经 `ToolPkgPreHookTimeout::fromSeconds` 换算（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:105`）。
- 每个钩子经 `ToolPkgPreHookTimeout::runHook` 以 `TOOLPKG_EVENT_CHAT_LIFECYCLE` 与 `CHAT_LIFECYCLE_BEFORE_CREATE` 事件执行（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:112`）。
- 同一包名重复出现时报错 `Duplicate chat lifecycle hook owner`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:130`）。
- 草稿校验要求草稿 id 非空（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:155`）。
- 草稿校验要求 `sourceChatId` 与 `parentChatId` 与草稿 id 不同（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:168`）。
- `New` 创建不得带 `sourceMessageTimestamp`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:180`）。
- `Branch` 创建必须带 `sourceChatId` 与正数 `sourceMessageTimestamp`，且 `parentChatId` 等于 `sourceChatId`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:192`）。
- `collectLifecycleHooks` 跳过无钩子的容器，空包名报错（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:208`）。
- 每包多于 1 个聊天生命周期钩子即报 `Duplicate chat lifecycle hook owner`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:213`）。
- 钩子 id 或函数为空时报错（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:220`）。
- 包名重复时报 `Duplicate chat lifecycle hook owner`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:233`）。
- 载荷只把选中所有者自己的源扩展放进 `sourceExtension`，非对象源扩展报错（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:256`）。
- 创建载荷含 `eventName`、`creationKind`、`chat`、`sourceChatId`、`sourceMessageTimestamp`、`input`、`sourceExtension` 七个键（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:268`）。
- 钩子返回 `undefined` 时报错 `Lifecycle handler returned undefined`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:274`）。
- 钩子须返回恰好含 `extension` 一个字段的 JSON 对象（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:283`）。
- `extension` 为对象时返回 `Some`，为 `null` 时返回 `None`，其他类型报错（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:291`）。
- 桥的包工具与 MCP 执行细节见 [[core-tool-packages-mcp|工具系统——包、技能与 MCP]]（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:112`）。
- 桥文件末尾含 `#[cfg(test)]` 测试模块，含新建、分支、源扩展隔离与重复所有者等测试（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:293`）。

## 关键符号

- `Operit1SnapshotImportManager` — Operit1 快照导入器（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:326`）。
- `Operit1SnapshotPreview` — 导入前预览（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:119`）。
- `Operit1SnapshotImportResult` — 导入后计数（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:146`）。
- `Operit1SnapshotImportProgress` — 导入进度（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:165`）。
- `Operit1ModelConfigImportResult` — 单配置导入结果（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:318`）。
- `inspectSnapshotSource` — 读快照返回预览（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:351`）。
- `importSnapshotSource` — 整快照导入（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:382`）。
- `importModelConfigSnapshotSource` — 按 configId 与 modelId 导入单个模型配置（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:501`）。
- `AgreementPreferences` — 空 struct，全文件只有一行声明（`core/crates/runtime/application/src/data/preferences/AgreementPreferences.rs:1`）。
- `PluginRegistry` — 内置插件全局注册表（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:19`）。
- `OperitPlugin` — 运行时插件契约（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:10`）。
- `ToolboxPlugin` — 内置工具箱插件，注册为空实现（`core/crates/runtime/application/src/plugins/toolbox/ToolboxPlugin.rs:6`）。
- 构建期生成的插件资产引入点，全文件只有一行 `include!`（`core/crates/runtime/application/src/plugins/BuiltinPluginAssets.rs:1`）。
- `snapshot()` — 会话创建前钩子桥的快照入口（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:73`）。
- `ToolPkgChatLifecycleDispatchContext` — 分离的已就绪运行时快照（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:55`）。
- `ToolPkgChatCreationDraft` — 会话创建草稿（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:48`）。
- `validateCreationDraft` — 草稿校验（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:155`）。
- `collectLifecycleHooks` — 收集已启用容器的生命周期钩子（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:208`）。
- `parseCreationResult` — 解析钩子返回结果（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:272`）。

## 调用链

### 快照导入

1. `inspectSnapshotSource` 解析快照并返回 `Operit1SnapshotPreview`，含数据库计数（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:351`）。
2. `importSnapshotSource` 启动整快照导入（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:382`）。
3. parse 阶段解析清单、配置与数据索引，进度 0.08（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:415`）。
4. model_config 阶段调 `importAllModelConfigsFromParsed`，进度 0.22（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:427`）。
5. structured_preferences 阶段调 `importSpeechPreferences`，进度 0.36（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:435`）。
6. preferences 阶段调 `importDataStorePreferences`，进度 0.50（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:440`）。
7. files 阶段调 `importSnapshotFiles`，进度 0.60（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:450`）。
8. chats 阶段调 `importChatDatabase`，随后调 `importTokenStatistics`，进度 0.64（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:456`）。
9. 聊天库经 `withStagedOperit1ChatDatabase` 暂存到检查路径（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:968`）。
10. 暂存库经 `openSqliteDatabase` 打开、经 `prepareOperit1RoomImport` 规范化后导入（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:990`）。
11. 导入完成时发布 `completed` 进度，progress 为 1.0（`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:198`）。

### 会话创建前钩子分发

1. ToolPkgChatLifecycleHookBridge 的 `register` 绑定进程级运行时（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:64`）。
2. `snapshot()` 取分离的已就绪运行时快照并收集已启用钩子（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:73`）。
3. `dispatchBeforeCreate` 先调 `validateCreationDraft` 校验草稿（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:95`）。
4. 无钩子时直接返回空 `BTreeMap`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:102`）。
5. 超时预算取自 ApiPreferences 的 `getToolPkgPreHookTimeoutSeconds`（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:105`）。
6. 每个钩子经 `ToolPkgPreHookTimeout::runHook` 按序执行（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:112`）。
7. 钩子结果由 `parseCreationResult` 解析（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:272`）。
8. 全部钩子成功后返回按包名分组的扩展映射（`core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs:130`）。

### 内置插件初始化

1. `initializeBuiltins` 用布尔门控保证只初始化一次（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:46`）。
2. 注册 `ToolboxPlugin` 与 ToolPkgCommonBridgePlugin 的 `new`(toolpkg_runtime)（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:59`）。
3. 逐个安装未安装插件，每个插件只调一次 `register()`（`core/crates/runtime/application/src/plugins/PluginRegistry.rs:90`）。

## 来源

- `core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs`（1019 行）
- `core/crates/runtime/application/src/data/preferences/AgreementPreferences.rs`（1 行）
- `core/crates/runtime/application/src/plugins/PluginRegistry.rs`（104 行）
- `core/crates/runtime/application/src/plugins/BuiltinPluginAssets.rs`（1 行）
- `core/crates/runtime/application/src/plugins/toolpkg/ToolPkgChatLifecycleHookBridge.rs`（563 行）
- `core/crates/runtime/application/src/plugins/toolbox/ToolboxPlugin.rs`（11 行）
