---
title: 从 Operit1 迁移
module: dev
platforms: [all]
sources: 19
date: 2026-11-11
---

## 概述

- Operit2 把迁移视作个人设备连续性的一部分，CLI 提供身份、存储路径、快照导出与恢复、备份检查入口。`README.md:85`
- 快照、配置与身份数据的确切范围由当前命令帮助与格式版本决定。`README.md:90`
- 活动进程与实时会话留在原节点，有备份不等于全部运行时状态已能无缝迁移。`README.md:92`
- Operit2 处于 Preview 阶段，底层结构、数据格式、插件契约与跨设备工作流仍会发生 breaking change。`README.md:14`
- 详细的 Operit1→Operit2 FAQ 在 Operit-wiki 附录草稿里，本页不重写，只写 CLI 入口与边界。wiki-drafts/appendix-operit1-to-operit2-faq.md:2
- 导入器的结构细节见 [[core-runtime-data|Runtime——数据与插件宿主]]。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:351`

## AI 速览

- `import_operit1_snapshot` — 导入 Operit1 快照的 CLI 处理函数，先预检再写入。`apps/cli/src/cli/transfer.rs:257`
- `inspectOperit1Snapshot` — 服务层预检入口，读快照返回导入前预览。`core/crates/runtime/application/src/services/SnapshotImportManager.rs:127`
- `importOperit1Snapshot` — 服务层导入入口，导入一份密封快照并发布进度事件。`core/crates/runtime/application/src/services/SnapshotImportManager.rs:152`
- `Operit1SnapshotPreview` — 导入前预览，含聊天数、消息数与文件数。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:120`
- `Operit1SnapshotImportResult` — 导入后计数，含聊天、消息、记忆与文件数。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:145`
- `Operit1ToOperit2ChatArchiveBridge` — 聊天桥接枚举，Room V10/V20/V21 桥接到 Operit2 SQLite V29。`core/crates/runtime/application/src/data/backup/Operit1RoomSchemaMigration.rs:31`
- `exportToBackupDir` — Operit1 侧导出快照的入口。（一代）app/src/main/java/com/ai/assistance/operit/data/backup/RawSnapshotBackupManager.kt:105
- 主入口函数：`import_operit1_snapshot`。`apps/cli/src/cli/transfer.rs:257`
- 数据流向：Operit1 快照包 → 预检 → 模型配置 → 语音、偏好、文件、聊天、统计 → Operit2 运行时存储。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:410`

## 核心机制

### 快照检查与导入

- operit2 cli backup inspect-operit1-snapshot <snapshot-zip-path> 调用 `inspectOperit1Snapshot` 做导入前预检。`apps/cli/src/cli/transfer.rs:153`
- operit2 cli import operit1-snapshot <snapshot-zip-path> 由 `import_operit1_snapshot` 处理。`apps/cli/src/cli/transfer.rs:106`
- 导入时先调 `inspectOperit1Snapshot` 预览，再调 `importOperit1Snapshot` 写入。`apps/cli/src/cli/transfer.rs:263`
- CLI 的 import 子命令分发到 `run_import_command`，backup 子命令分发到 `run_backup_command`。`apps/cli/src/cli/mod.rs:173`
- 预检输出打印 Package、Chats、Messages 三项计数。`apps/cli/src/cli/transfer.rs:160`
- 预检输出打印 Detected domains，即源快照中实际检测到的域名。`apps/cli/src/cli/transfer.rs:168`
- 预检输出打印模型配置数，逐个列出模型配置名与 configId。`apps/cli/src/cli/transfer.rs:170`
- 预检输出逐个打印 datastore 文件名与 key 数。`apps/cli/src/cli/transfer.rs:175`
- 导入输出打印 Imported chats、Imported messages、Imported memories、Imported files、Imported external files、Imported workspaces 六项计数。`apps/cli/src/cli/transfer.rs:276`
- 导入输出在模型配置存在跳过字段时打印 Skipped fields。`apps/cli/src/cli/transfer.rs:284`
- 快照格式版本 `FORMAT_VERSION` 为 1。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:13`
- 清单条目 `ENTRY_MANIFEST` 为 manifest.json。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:14`
- `ENTRY_MODEL_CONFIGS` 位于 payload/files/datastore/model_configs.preferences_pb，`ENTRY_FUNCTIONAL_CONFIGS` 位于 payload/files/datastore/functional_configs.preferences_pb。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:15`
- 快照内路径前缀分三类：DataStore 在 `ENTRY_DATASTORE_PREFIX`，普通文件在 `ENTRY_FILES_PREFIX`，外部文件在 `ENTRY_EXTERNAL_FILES_PREFIX`。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:19`
- manifest 含 `formatVersion`、`packageName`、`createdAt` 三个字段。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:40`
- manifest 的 formatVersion 与 `FORMAT_VERSION` 不符时报 Unsupported Operit1 snapshot formatVersion。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:109`
- 归档条目数上限为 100_000，单条 DataStore 条目上限为 64 MiB，manifest 上限为 1 MiB，三个上限分别由 `MAX_ARCHIVE_ENTRY_COUNT`、`MAX_DATASTORE_ENTRY_BYTES`、`MAX_MANIFEST_BYTES` 定义。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:23`
- Operit1 快照包名须以 com.ai.assistance.operit 开头，`isSupportedSnapshotPackageName` 做此前缀校验。（一代）app/src/main/java/com/ai/assistance/operit/data/backup/RawSnapshotBackupManager.kt:34
- Operit1 快照 ZIP 文件名前缀 `ZIP_PREFIX` 为 operit_raw_snapshot_。（一代）app/src/main/java/com/ai/assistance/operit/data/backup/RawSnapshotBackupManager.kt:41
- `exportToBackupDir` 是 Operit1 侧导出快照的入口。（一代）app/src/main/java/com/ai/assistance/operit/data/backup/RawSnapshotBackupManager.kt:105
- Operit1 设置页备份功能在 ChatBackupSettingsScreen.kt:989 调用 `exportToBackupDir` 导出快照。（一代）app/src/main/java/com/ai/assistance/operit/ui/features/settings/screens/ChatBackupSettingsScreen.kt:989
- Operit1 导入时包名不匹配抛 Backup package mismatch。（一代）app/src/main/java/com/ai/assistance/operit/data/backup/RawSnapshotBackupManager.kt:412

### 哪些数据能带过来、哪些不能

- 导入先执行 `importAllModelConfigsFromParsed`，导入全部模型配置。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:427`
- 导入随后执行 `importSpeechPreferences`，导入语音偏好。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:435`
- 导入随后执行 `importDataStorePreferences`，导入 DataStore 偏好。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:443`
- 导入随后执行 `importSnapshotFiles`，复制快照文件。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:450`
- 导入随后执行 `importChatDatabase`，导入聊天数据库。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:458`
- 导入最后执行 `importTokenStatistics`，导入 token 统计。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:460`
- 聊天桥接枚举 `Operit1ToOperit2ChatArchiveBridge` 含 `Operit1RoomV10ToOperit2SqliteV29`、`Operit1RoomV20ToOperit2SqliteV29`、`Operit1RoomV21ToOperit2SqliteV29` 三个变体。`core/crates/runtime/application/src/data/backup/Operit1RoomSchemaMigration.rs:31`
- 三个聊天桥接变体的 Operit2 目标 SQLite schema 版本均为 29。`core/crates/runtime/application/src/data/backup/Operit1RoomSchemaMigration.rs:40`
- Room V10 走 `buildChatArchiveFromOperit1RoomV10Database` 构建，Room V20 与 V21 走 `buildChatArchiveFromOperit1RoomV20Database` 构建。`core/crates/runtime/application/src/data/backup/operit1/Operit1ChatMigration.rs:13`
- `buildOperit2CharacterCards` 从解析后的快照构建 Operit2 角色卡。`core/crates/runtime/application/src/data/backup/operit1/Operit1CharacterCards.rs:44`
- `buildOperit2CharacterGroups` 构建 Operit2 角色组。`core/crates/runtime/application/src/data/backup/operit1/Operit1CharacterCards.rs:539`
- `buildOperit2TtsConfig` 从解析后的快照构建 TTS 配置。`core/crates/runtime/application/src/data/backup/operit1/Operit1CharacterCards.rs:592`
- `buildOperit1ProviderProfile` 构建模型提供方档案。`core/crates/runtime/application/src/data/backup/operit1/Operit1ModelMigration.rs:64`
- `buildOperit1PluginMemoryRecords` 构建角色插件记忆记录。`core/crates/runtime/application/src/data/backup/operit1/Operit1MemoryStorage.rs:162`
- 导入后计数含 `importedChats`、`importedMessages`、`importedMemories`、`importedMemoryLinks`。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:148`
- 导入后计数含 `importedFiles`、`importedExternalFiles`、`importedWorkspaces`、`importedWorkspaceFiles`。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:154`
- `active_prompt_type`、`active_prompt_id`、`active_character_card_id`、`active_character_group_id`、`active_memory_space_id`、`memory_space_list` 属于不采纳的偏好键。`core/crates/runtime/application/src/data/backup/operit1/Operit1PreferenceMigration.rs:236`
- `enable_thinking_mode` 与 `thinking_quality_level` 没有迁移目标，思考改为按模型设置，全局思考开关与质量等级不迁移。`core/crates/runtime/application/src/data/backup/operit1/Operit1PreferenceMigration.rs:245`
- `isDataStoreEntry` 判定条目以 `ENTRY_DATASTORE_PREFIX` 开头且以 .preferences_pb 结尾。`core/crates/runtime/application/src/data/backup/operit1/Operit1DataStorePreferences.rs:31`
- `TOOLPKG_API_VERSION_1_0_0` 为 1.0.0，标注 original contract；`TOOLPKG_API_VERSION_1_0_1` 为 1.0.1，标注 legacy contract。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:4`
- `TOOLPKG_API_VERSION_2_0_0` 为 2.0.0，是 Operit2 的 ToolPkg API 契约，`CURRENT_TOOLPKG_API_VERSION` 指向 2.0.0。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:10`

### 数据救援流程

- 数据救援入口按平台区分：Android 长按启动器图标选 数据救援；iOS 用 Data Rescue 主屏幕快捷方式且须在 App 完全关闭时使用；OpenHarmony 启动 DataRescueAbility。`docs/data-rescue.md:8`
- 数据救援入口按平台区分：Windows 从开始菜单选 Operit2 Data Rescue 或用 --data-rescue 启动；macOS 用原生菜单命令或 --data-rescue；Linux 用桌面项或 --data-rescue。`docs/data-rescue.md:11`
- Web 数据救援打开 data-rescue.html 或用 ?mode=data-rescue。`docs/data-rescue.md:13`
- CLI 数据救援用 operit2 rescue describe、export、inspect、import、resume。`docs/data-rescue.md:14`
- rescue CLI 入口不启动 Core、不打开 SQLite。`apps/cli/src/rescue.rs:1`
- rescue 帮助列出 describe、export、inspect、import、resume 五条命令，import 与 resume 带 --confirm。`apps/cli/src/rescue.rs:85`
- rescue 的 export、inspect、import 接受 --runtime-root、--workspace-root、--confirm 三个选项。`apps/cli/src/rescue.rs:22`
- 顶层帮助把 operit2 rescue <command> 列为导出、检查、导入或恢复数据救援的入口。`apps/cli/src/cli/mod.rs:1785`
- Flutter 维护界面是独立路由，不构造 `CoreApplicationService`、`RuntimeBootstrapManager`、常规日志路径与常规业务 UI。`docs/data-rescue.md:16`
- 原生平台用 `operit.files.v1` 归档布局，浏览器用 `operit.browser.v1` 归档布局；归档是普通 ZIP 文件，不需要密码；每次恢复前按声明大小与 SHA-256 校验每个 payload。`docs/data-rescue.md:20`
- 恢复先暂存校验再发布，原目录保留在生成的 `.operit-retained-*` 路径（原生平台）与 `data-rescue/retained-*`（浏览器）。`docs/data-rescue.md:24`
- 正常进程持有租约时维护界面报告具体锁错误，Android 提供停止正常进程的命令，iOS 须冷启动。`docs/data-rescue.md:26`
- 导入保留被置换的原生根与应用自有条目，持久的中断发布阻塞正常启动，仅由显式 `resume` 推进。`docs/data-rescue.md:28`
- 原生与浏览器归档在本版本中故意不互通。`docs/data-rescue.md:30`
- 恢复入口标签为 从备份恢复，导出、源读取、清单检查、完整性校验、暂存恢复、恢复文件验证、发布、中断导入完成、目标保存均报告实测阶段计数。`docs/data-rescue.md:34`

## 关键符号

- `import_operit1_snapshot` — 导入 Operit1 快照的 CLI 处理函数，先预检再写入。`apps/cli/src/cli/transfer.rs:257`
- `inspectOperit1Snapshot` — 服务层预检入口，读快照返回导入前预览。`core/crates/runtime/application/src/services/SnapshotImportManager.rs:127`
- `importOperit1Snapshot` — 服务层导入入口，导入一份密封快照并发布进度事件。`core/crates/runtime/application/src/services/SnapshotImportManager.rs:152`
- `Operit1SnapshotPreview` — 导入前预览，含 formatVersion、packageName、createdAt、chatCount、messageCount。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:120`
- `Operit1SnapshotImportResult` — 导入后计数，含聊天、消息、记忆与文件数。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:145`
- `Operit1ToOperit2ChatArchiveBridge` — 聊天桥接枚举，Room V10/V20/V21 桥接到 Operit2 SQLite V29。`core/crates/runtime/application/src/data/backup/Operit1RoomSchemaMigration.rs:31`
- `FORMAT_VERSION` — Operit1 快照格式版本，值为 1。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:13`
- `ENTRY_MANIFEST` — 快照清单条目，为 manifest.json。`core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs:14`
- `isDataStoreEntry` — 判定条目是否为 Operit1 DataStore 偏好 payload。`core/crates/runtime/application/src/data/backup/operit1/Operit1DataStorePreferences.rs:31`
- `TOOLPKG_API_VERSION_2_0_0` — Operit2 的 ToolPkg API 契约版本 2.0.0。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:10`
- `CURRENT_TOOLPKG_API_VERSION` — 当前 SDK 暴露的 ToolPkg API 契约版本，指向 2.0.0。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:13`
- `exportToBackupDir` — Operit1 侧导出快照的入口。（一代）app/src/main/java/com/ai/assistance/operit/data/backup/RawSnapshotBackupManager.kt:105
- `isSupportedSnapshotPackageName` — Operit1 快照包名前缀校验。（一代）app/src/main/java/com/ai/assistance/operit/data/backup/RawSnapshotBackupManager.kt:34

## 调用链

1. 在 Operit1 设置页备份功能调用 `exportToBackupDir` 导出快照。（一代）app/src/main/java/com/ai/assistance/operit/ui/features/settings/screens/ChatBackupSettingsScreen.kt:989
2. operit2 cli backup inspect-operit1-snapshot <snapshot-zip-path> 预检，`inspectOperit1Snapshot` 返回预览。`apps/cli/src/cli/transfer.rs:153`
3. operit2 cli import operit1-snapshot <snapshot-zip-path> 先调 `inspectOperit1Snapshot` 预览，再调 `importOperit1Snapshot` 写入。`apps/cli/src/cli/transfer.rs:263`
4. 导入按模型配置、语音偏好、DataStore 偏好、文件、聊天库、token 统计顺序执行。`core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs:427`
5. 导入完成后打印 Imported chats、Imported messages、Imported memories、Imported files、Imported external files、Imported workspaces 六项计数。`apps/cli/src/cli/transfer.rs:276`
6. 数据救援走独立入口 operit2 rescue describe、export、inspect、import、resume，import 与 resume 带 --confirm。`apps/cli/src/rescue.rs:85`

## 来源

- seed 文件：README.md，全文已读；docs/data-rescue.md，全文已读。`README.md:1`
- 直接相关的 Operit2 文件：apps/cli/src/cli/transfer.rs、apps/cli/src/cli/mod.rs、apps/cli/src/rescue.rs、core/crates/runtime/application/src/services/SnapshotImportManager.rs、core/crates/runtime/application/src/data/backup/Operit1SnapshotImportManager.rs、core/crates/runtime/application/src/data/backup/operit1/Operit1SnapshotArchive.rs、core/crates/runtime/application/src/data/backup/Operit1RoomSchemaMigration.rs、core/crates/runtime/application/src/data/backup/operit1/Operit1ChatMigration.rs、core/crates/runtime/application/src/data/backup/operit1/Operit1PreferenceMigration.rs、core/crates/runtime/application/src/data/backup/operit1/Operit1DataStorePreferences.rs、core/crates/runtime/application/src/data/backup/operit1/Operit1CharacterCards.rs、core/crates/runtime/application/src/data/backup/operit1/Operit1ModelMigration.rs、core/crates/runtime/application/src/data/backup/operit1/Operit1MemoryStorage.rs、core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs，以上均已按引用行核验。`README.md:1`
- 直接相关的一代文件（来源仓库：一代，AAswordman/Operit @ dbf71916）：app/src/main/java/com/ai/assistance/operit/data/backup/RawSnapshotBackupManager.kt、app/src/main/java/com/ai/assistance/operit/ui/features/settings/screens/ChatBackupSettingsScreen.kt，均已按引用行核验。`README.md:1`
- 详细的 Operit1→Operit2 FAQ 在 Operit-wiki 附录草稿里，本页不重写。wiki-drafts/appendix-operit1-to-operit2-faq.md:2
- 源码基线：AAswordman/Operit2 @ 364d1d594；一代 AAswordman/Operit @ dbf71916。`README.md:1`
- 否定性核验方法（2026-11-12，对基线 364d1d594）：在 Operit2 仓库内对 docs/*.md 与 README.md 执行 grep -i faq，零命中，Operit2 仓库内无迁移 FAQ 正文；对 core/crates/runtime/application/src/data/backup/operit1/ 执行 ls 与 grep -i thinking，思考过程无独立迁移文件，全局思考开关见 Operit1PreferenceMigration.rs:245-247 的不采纳注释。`core/crates/runtime/application/src/data/backup/operit1/Operit1PreferenceMigration.rs:245`
- 草稿勘误：wiki-drafts 附录草稿所写的聊天桥接目标为 SQLite V27、含独立思考过程迁移文件，两处在基线 364d1d594 上均已过时：桥接目标为 V29，思考过程无独立迁移文件，全局思考开关不迁移。`core/crates/runtime/application/src/data/backup/Operit1RoomSchemaMigration.rs:40`
