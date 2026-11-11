---
title: 主题的安装、作用域与同步
module: theme
platforms: [all]
sources: [5]
date: 2026-11-11
---

## 概述

- 本页讲主题模板如何安装、作用域如何决定、主题配置如何随 Space 同步，见 [[plugin-theme|主题即插件（theme-as-ToolPkg）]]。`docs/theme-v1-contract.md:3`
- ToolPkg 的 manifest 通过 `themes` 声明多个主题模板；安装、作用域、同步、更新和卸载全部由现有包管理系统负责。`docs/theme-v1-contract.md:3`
- 主题模板本身不带独立安装器：主题模块不独立寻找 manifest，也不执行脚本、安装包或创建独立归档存储。`docs/theme-v1-contract.md:37`
- 从模板创建的外观配置是独立配置：后续渲染读取配置与外观资源，不再依赖来源插件是否安装，也不会随来源模板更新而改写配置。`docs/theme-v1-contract.md:51`
- 主题偏好走通用偏好存储：文档写明 `Tools.Storage.dataStore` 暴露已有的 Rust `PreferencesDataStore`，参与和 Rust 偏好管理器相同的 Space 合并执行器。`docs/plugin-storage.md:3`

## AI 速览

- `themes` — ToolPkg manifest 声明多个主题模板。`docs/theme-v1-contract.md:3`
- `ToolPkgArchiveParser::readThemeTemplates` — 通过普通 ToolPkg manifest 解析器枚举模板并校验资源。`docs/theme-v1-contract.md:37`
- `previewToolPkgTheme` — 读取当前注册包，验证模板和媒体，返回规范化视觉 JSON 与资源。`docs/theme-v1-contract.md:47`
- `ThemeTemplateService` — 把模板图片和字体复制到外观资源池并创建独立配置。`docs/theme-v1-contract.md:47`
- `ThemeConfigManager.create` — 创建独立外观配置。`docs/theme-v1-contract.md:47`
- `apply` — 选中新创建的外观配置。`docs/theme-v1-contract.md:47`
- `themePaletteJson` — 可选的完整明暗配色外观字段。`docs/theme-v1-contract.md:49`
- `Tools.Storage.dataStore` — 暴露 Rust `PreferencesDataStore` 的插件偏好入口。`docs/plugin-storage.md:3`
- `withSchema` — 为每个版本声明一个可移植规则数组。`docs/plugin-storage.md:22`
- `withMigration` — 注册用户偏好文件的格式迁移，目标格式版本为 5。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:36`
- `migrateLegacyThemePreferences` — 解码旧主题偏好。`core/crates/runtime/application/src/data/preferences/ThemePreferenceSnapshot.rs:643`
- `migrateLegacyThemeSnapshot` — 迁移历史主题快照并去掉当前 schema 不再拥有的字段。`core/crates/runtime/application/src/data/preferences/ThemePreferenceSnapshot.rs:656`
- `PreferenceMergeStore` — 绑定共享合并声明与其所属偏好 store。`core/crates/persistence/store/src/PreferenceMerge.rs:31`
- PreferenceMergeSchema 的 `owner` — 按路径解析偏好 owner。`core/crates/persistence/store/src/PreferenceMerge.rs:76`
- `declarePlugin` — 登记插件偏好合并声明。`core/crates/persistence/store/src/PreferenceMerge.rs:92`
- `applyDeclaredOperations` — 重放一个数据集并提交业务状态。`core/crates/persistence/store/src/PreferenceMerge.rs:466`
- `rewriteReferences` — 按规范身份映射重写已声明引用。`core/crates/persistence/store/src/PreferenceMerge.rs:620`
- `resolveIdentity` — 沿别名映射传递解析身份。`core/crates/persistence/store/src/PreferenceMerge.rs:809`
- 主入口（外观创建）：`previewToolPkgTheme` → `ThemeTemplateService` → `ThemeConfigManager.create` 和 `apply`。`docs/theme-v1-contract.md:47`
- 主入口（偏好合并）：`applyOperations` 接受 history 与 incoming 操作，返回引用映射或错误字符串。`core/crates/persistence/store/src/PreferenceMerge.rs:407`
- 数据流向（外观）：模板 → 复制到外观资源池 → 独立配置 → Space 同步。`docs/theme-v1-contract.md:51`
- 数据流向（偏好）：`Tools.Storage.dataStore` 的写操作进入与 Rust 偏好管理器相同的 Space 合并执行器。`docs/plugin-storage.md:3`

## 核心机制

### 安装与作用域

- ToolPkg 的 manifest 通过 `themes` 声明多个主题模板，并与 `main`、`subpackages`、`resources`、`workspace_templates` 共存；发行格式只有 `.toolpkg`。`docs/theme-v1-contract.md:3`
- 安装、作用域、同步、更新和卸载全部由现有包管理系统负责。`docs/theme-v1-contract.md:3`
- 主题模块不独立寻找 manifest，也不执行脚本、安装包或创建独立归档存储。`docs/theme-v1-contract.md:37`
- 模板 `id` 在同一个包中唯一；节点选择使用 `toolpkg_id:template_id` 身份；`path` 和 `preview` 是 manifest 所在目录的相对路径。`docs/theme-v1-contract.md:27`
- 模板及视觉定义不包含平台列表、协议字段、主题 API 版本或最低／最高应用版本；包的 `api_version` 和 `version` 沿用 ToolPkg 本身的含义，主题模块不增加版本格式要求。`docs/theme-v1-contract.md:31`
- 新建外观配置时，模板来源每次打开新建对话框时通过 `packageManager().getToolPkgContainerRuntimes()` 动态读取。`docs/theme-v1-contract.md:45`
- 安装、卸载、更新和 device / space 归属由普通插件管理系统负责。`docs/theme-v1-contract.md:45`
- 插件用 `ToolPkg.getSpaceDataDir()` 取同步文件夹，或用本地数据目录存设备自有偏好；Space 不能注入设备自有偏好操作。`docs/plugin-storage.md:36`
- JSON 偏好文件排除在整文件同步之外；SQLite/对象开启器拒绝偏好文件。`docs/plugin-storage.md:36`

### 从模板创建外观配置

- `ToolPkgArchiveParser::readThemeTemplates` 通过普通 ToolPkg manifest 解析器枚举模板，再调用 `validate_declared_theme_templates` 校验其资源；没有 `themes` 的普通包返回空集合。`docs/theme-v1-contract.md:37`
- `normalize_draft` 按视觉 schema 展开编辑态默认值；`parse_theme` 校验完整视觉状态；显式非法值、未知视觉字段、远程资源路径及非法九宫格切片会报错。`docs/theme-v1-contract.md:33`
- 文档写明 Rust `operit-plugin-theme` 为每个模板检查资源存在性、实际大小、视觉关系、PNG/JPEG 解码、受限静态 SVG、九宫格像素范围及静态 TrueType 字体结构；`ValidatedThemeTemplate` 和 `ThemeValidationReceipt` 只表示对应模板的渲染校验结果，`trust` 为 `Untrusted`。`docs/theme-v1-contract.md:35`
- 选择模板后，`previewToolPkgTheme(packageName, templateId)` 读取当前注册包，验证模板和媒体，返回规范化视觉 JSON 与资源。`docs/theme-v1-contract.md:47`
- `ThemeTemplateService` 将模板图片和字体复制到既有 `runtime/data/user_assets/theme` 资源池，把包内相对引用替换为外观资源引用。`docs/theme-v1-contract.md:47`
- 再通过原有 `ThemeConfigManager.create` 和 `apply` 创建并选中独立配置。`docs/theme-v1-contract.md:47`
- 创建不会修改继承来源或此前选中的命名配置。`docs/theme-v1-contract.md:49`
- 完整明暗配色作为可选的 `themePaletteJson` 外观字段保存；用户重新选择配色时清除完整配色，使用原有种子配色逻辑。`docs/theme-v1-contract.md:49`
- 配置和复制后的资源沿用原有 Space 同步。`docs/theme-v1-contract.md:51`
- 后续渲染读取配置与外观资源，不再依赖来源插件是否安装，也不会随来源模板更新而改写配置。`docs/theme-v1-contract.md:51`
- 没有独立主题库、共享模板选择、只读锁定、主题专用卸载约束或模板恢复页面。`docs/theme-v1-contract.md:51`
- 外观资源或配色加载失败时，客户端展示明确错误及“重试”“重置外观”操作；重试读取原有值；重置只由用户点击触发，保留头像与已保存配置，并显式选中自定义外观；错误不会触发自动替换。`docs/theme-v1-contract.md:55`
- 应用旧版配置时清除其没有声明的新增外观字段，避免沿用此前模板的输入框样式。`docs/theme-v1-contract.md:55`
- Studio 通过 `export_toolpkg_from_theme_transfer` 创建包含模板的普通 ToolPkg；编辑既有包时保留其他 manifest 能力、其他模板及原有资源；导出只更新所选模板及用户修改的包元数据。`docs/theme-v1-contract.md:39`

### 偏好 owner 声明与物化协调

- `PreferenceMergeStore` 绑定一条共享数据声明与其所属偏好 store，字段为 `path`、`encrypted`、`open` 与 `merge`。`core/crates/persistence/store/src/PreferenceMerge.rs:31`
- 无目录 owner 的合并描述符 `version` 为 1，`catalog` 为 None，`references` 为空，`projection` 为 None。`core/crates/persistence/store/src/PreferenceMerge.rs:50`
- PreferenceMergeSchema 的 `owner` 回退到 `CoreSpaceStore::preferenceSyncStore` 解析路径的 owner。`core/crates/persistence/store/src/PreferenceMerge.rs:76`
- 插件偏好路径要求规范路径等于传入路径且以 `.preferences.json` 结尾，否则返回 Invalid synchronized plugin preference path 错误。`core/crates/persistence/store/src/PreferenceMerge.rs:81`
- `runtimeStorageOwnership(path)` 不为 `RuntimeStorageOwnership::Space` 时返回 None。`core/crates/persistence/store/src/PreferenceMerge.rs:85`
- `declarePlugin` 先经 `validatePluginDeclaration` 校验，再把合并声明写入已登记 owner 或新建一个 owner；已加密的 owner 拒绝插件偏好声明。`core/crates/persistence/store/src/PreferenceMerge.rs:92`
- `validateDeclaration` 要求合并声明的 `version` 为 1 且 `references` 不超过 256 条，否则返回 Invalid preference merge declaration 错误。`core/crates/persistence/store/src/PreferenceMerge.rs:119`
- 聚合校验限制目录不超过 64 个、引用总数不超过 256 条、投影不超过 64 个，否则返回声明超出资源限制错误。`core/crates/persistence/store/src/PreferenceMerge.rs:188`
- `combineDeclarations` 要求两份声明的 `version`、`catalog`、`projection` 相同且较长一方的 `references` 以较短一方为前缀，否则拒绝合并。`core/crates/persistence/store/src/PreferenceMerge.rs:249`
- 合并声明冲突时返回 Conflicting preference merge declarations 错误。`core/crates/persistence/store/src/PreferenceMerge.rs:254`
- `isMergeMetadata` 把 domain 为 `preferences` 且 operation 为 `alias` 的操作，或 payload key 为 `PLUGIN_MERGE_DECLARATION_KEY` 或 `PluginPreferenceSchema::KEY` 的操作判定为合并元数据。`core/crates/persistence/store/src/PreferenceMerge.rs:23`
- `applyDeclaredOperations` 重放一个数据集，并把业务状态、原始身份与归档意图一起提交。`core/crates/persistence/store/src/PreferenceMerge.rs:466`
- 重放前调用 `store.migrateSyncedEntries(version, preferences, &mut entries)` 对同步条目执行迁移。`core/crates/persistence/store/src/PreferenceMerge.rs:516`
- `PreferenceMergeOutcome` 记录 `paths`、`operations`、`skipped` 与 `result`；`skipped` 表示布局已显式退役该目标，原始记录仍留在日志中。`core/crates/persistence/store/src/PreferenceMerge.rs:262`
- `applyIndependentOperations` 对每个数据集独立应用；稳定引用不合并提交或失败边界。`core/crates/persistence/store/src/PreferenceMerge.rs:269`
- `registry` 构造的注册表由普通同步与最终比较/纠正共享。`core/crates/persistence/store/src/PreferenceMerge.rs:308`
- `applyOperations` 接受 `history` 与 `incoming` 操作，返回引用映射或错误字符串。`core/crates/persistence/store/src/PreferenceMerge.rs:407`
- `declaredAliases` 只解析已显式记录的别名决定，绝不从内容推断身份。`core/crates/persistence/store/src/PreferenceMerge.rs:435`
- `rewriteReferences` 按执行器的规范身份映射重写已声明的引用。`core/crates/persistence/store/src/PreferenceMerge.rs:620`
- 引用路径走完时，被引用的值必须是字符串或 null，否则返回 Declared preference reference must be a string or null 错误。`core/crates/persistence/store/src/PreferenceMerge.rs:764`
- `resolveIdentity` 沿别名映射传递解析身份。`core/crates/persistence/store/src/PreferenceMerge.rs:809`
- 别名映射成环时返回 Cyclic preference identity mapping 错误。`core/crates/persistence/store/src/PreferenceMerge.rs:818`
- 合并把一个身份别名到存活的规范身份时，该决定持久化在数据库的合并映射里，对插件不可见：别名根键或子键下的本地提交被重定向到规范行，打开已合并数据库时会把旧写入者留在退役键下的行移回规范身份。`docs/plugin-storage.md:34`
- 每个偏好文件与内存数据库各有自己的事务边界；跨这些文件与内存引擎的多 owner 业务操作不是单个原子事务。`docs/plugin-storage.md:57`

### schema 迁移在哪里执行

- `withSchema(version, steps)` 为每个版本声明一个可移植规则数组，从版本 0 开始；规则包括 `rename_key`、`rename_field`、`split_object`、`split_records`、`drop_key`、`decode_json`、`set_object_field`。`docs/plugin-storage.md:22`
- 新版本应追加步骤而不是重写已发布步骤；声明持久化在引擎自有元数据里，包含在导出的初始化事务中，由后台同步恢复，无需启动插件；普通编辑回调保留当前格式。`docs/plugin-storage.md:22`
- 插件改动已发布契约时，引擎自动解析有效契约：最高版本胜出，版本相同时按字典序最大的规范 JSON 排序；引擎只选一条完整链条，不拼接步骤，不降级已存格式，不重跑已应用版本；同一解析同时规范检查点重放与同步。`docs/plugin-storage.md:24`
- 文档写明原生引擎通过 `Transaction::migration::Context` 对完整数据与旧原子事务执行同一套规则；它保留事务身份、业务优先级、修改作用域与原子边界，并校验 `m(Apply(A,T)) = Apply(m(A),m_A(T))`。`docs/plugin-storage.md:26`
- 状态迁移与声明发布共享一次持久提交并保留原始业务 revision；不支持的规则保持待处理等待引擎升级，独立 owner 继续；任意 JavaScript schema 回调会被拒绝。`docs/plugin-storage.md:26`
- 这些声明描述的是格式迁移；跨文件所有权变更仍是布局迁移，使用共享原生布局机制：提交目标、发布其路由或退役决定、保留本地进度；带编号的格式步骤不意味着旧路径退役。`docs/plugin-storage.md:28`
- 第一个插件 schema 是 v1；不存在未发布的插件 v2 格式，也不存在 v1 到 v2 的迁移；已发布的备份格式各有独立版本号。`docs/plugin-storage.md:55`
- Rust 侧执行点：`store` 打开 `USER_PREFERENCES_PATH` 时以 `withMigration(5, Self::migration)` 注册迁移，目标格式版本为 5。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:36`
- `migratePreferences` 的 3 分支先调用 `migrateLegacyThemePreferences` 解码旧主题偏好，再逐条处理 `THEME_CONFIG_PREFIX` 开头的配置。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:58` `core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:90`
- 逐条配置反序列化为 `ThemeConfig` 后调用 `migrateLegacyThemeSnapshot` 迁移快照，再经 `validateConfig` 校验后写回。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:98`
- 4 分支把 `chat_style` 拆分为 `user_chat_style` 与 `ai_chat_style`，只在新键缺失时继承旧值。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:106`
- 4 分支同时把已存配置快照里的 `chatStyle` 拆分为 `userChatStyle` 与 `aiChatStyle`，已显式设置的值不被覆盖。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:124`
- 插件与偏好文件是两套版本体系：插件侧是 v1/v2，第一个插件 schema 是 v1，不存在未发布的 v2 格式与 v1 到 v2 的迁移。`docs/plugin-storage.md:55`
- 偏好文件侧是 format 0–5：`store` 打开 `USER_PREFERENCES_PATH` 时以 `withMigration(5, Self::migration)` 注册迁移，目标格式版本为 5。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:36`
- 原先只搜 `withSchema` 会漏检：`withSchema(3` 的两处生产代码命中分别是同步偏好布局与包管理器偏好，均非主题偏好迁移；真正的主题偏好迁移走 `withMigration`。`core/crates/runtime/application/src/data/preferences/PreferenceSpaceMerge.rs:196` `core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs:338` `core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:36`
- `data()` 返回不可变快照；`get()` 把已存的 `null` 与缺失键（`undefined`）区分开；`edit()` 接受同步或异步回调，通过原生偏好事务发布变更；回调抛异常时不发布任何偏好变更。`docs/plugin-storage.md:20`
- 原生快照校验拒绝并发编辑且不重跑回调；回调结束后可变视图不可再用。`docs/plugin-storage.md:20`

### 插件 dataStore 与 Rust PreferencesDataStore 是否同一套合并执行器

- 是同一套：文档写明 `Tools.Storage.dataStore` 暴露已有的 Rust `PreferencesDataStore`，使用原生偏好操作日志，参与和 Rust 偏好管理器相同的 Space 合并执行器。`docs/plugin-storage.md:3`
- 它不使用对象表、插件专属合并引擎或整文件 last-write-wins 同步。`docs/plugin-storage.md:3`
- 插件提供的有界纯数据合并声明随偏好日志保留，并适配到已有的原生 `PreferenceMerge` 执行器；Space 重放期间不运行 TypeScript 合并回调。`docs/plugin-storage.md:32`
- `declarePlugin` 把插件合并声明写入已登记 owner 或新建一个 owner。`core/crates/persistence/store/src/PreferenceMerge.rs:92`

## 关键符号

- `themes` — ToolPkg manifest 声明多个主题模板。`docs/theme-v1-contract.md:3`
- `toolpkg_id:template_id` — 包内模板的节点选择身份。`docs/theme-v1-contract.md:27`
- `normalize_draft` — 按视觉 schema 展开编辑态默认值。`docs/theme-v1-contract.md:33`
- `parse_theme` — 校验完整视觉状态。`docs/theme-v1-contract.md:33`
- `ValidatedThemeTemplate` — 对应模板的渲染校验结果。`docs/theme-v1-contract.md:35`
- `ThemeValidationReceipt` — 对应模板的渲染校验回执。`docs/theme-v1-contract.md:35`
- `ToolPkgArchiveParser::readThemeTemplates` — 枚举并校验包内声明的模板。`docs/theme-v1-contract.md:37`
- `validate_declared_theme_templates` — 校验已声明主题模板的资源。`docs/theme-v1-contract.md:37`
- `export_toolpkg_from_theme_transfer` — 从主题传输导出包含模板的普通 ToolPkg。`docs/theme-v1-contract.md:39`
- `packageManager().getToolPkgContainerRuntimes()` — 动态读取模板来源。`docs/theme-v1-contract.md:45`
- `previewToolPkgTheme` — 读取当前注册包并返回规范化视觉 JSON 与资源。`docs/theme-v1-contract.md:47`
- `ThemeTemplateService` — 复制模板图片和字体到外观资源池。`docs/theme-v1-contract.md:47`
- `ThemeConfigManager.create` — 创建独立外观配置。`docs/theme-v1-contract.md:47`
- `themePaletteJson` — 可选的完整明暗配色外观字段。`docs/theme-v1-contract.md:49`
- `Tools.Storage.dataStore` — 暴露 Rust `PreferencesDataStore` 的插件偏好入口。`docs/plugin-storage.md:3`
- `PreferencesDataStore` — Rust 偏好存储，类型化 JSON 存 `.preferences.json` 文件。`docs/plugin-storage.md:3`
- `withSchema` — 声明各版本的可移植迁移规则。`docs/plugin-storage.md:22`
- `store` — 打开用户偏好文件并注册格式迁移。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:36`
- `withMigration` — 注册用户偏好文件的格式迁移。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:36`
- `USER_PREFERENCES_PATH` — 用户偏好文件的存储路径。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:36`
- `migratePreferences` — 按版本号执行用户偏好迁移。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:58`
- `migrateLegacyThemePreferences` — 解码旧主题偏好。`core/crates/runtime/application/src/data/preferences/ThemePreferenceSnapshot.rs:643`
- `migrateLegacyThemeSnapshot` — 迁移历史主题快照并去掉当前 schema 不再拥有的字段。`core/crates/runtime/application/src/data/preferences/ThemePreferenceSnapshot.rs:656`
- `chat_style` — 旧版聊天样式键，4 分支拆分为用户与 AI 两键。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:106`
- `user_chat_style` — 拆分出的用户聊天样式键。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:106`
- `ai_chat_style` — 拆分出的 AI 聊天样式键。`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs:106`
- `rename_key` — 迁移规则：重命名键。`docs/plugin-storage.md:22`
- `decode_json` — 迁移规则：解码 JSON 字符串。`docs/plugin-storage.md:22`
- `Transaction::migration::Context` — 原生引擎执行迁移规则的上下文。`docs/plugin-storage.md:26`
- `ToolPkg.getSpaceDataDir()` — 取插件的同步文件夹。`docs/plugin-storage.md:36`
- `PreferenceMergeStore` — 绑定共享合并声明与其所属偏好 store。`core/crates/persistence/store/src/PreferenceMerge.rs:31`
- `isMergeMetadata` — 判定操作是否为合并元数据。`core/crates/persistence/store/src/PreferenceMerge.rs:23`
- `PLUGIN_MERGE_DECLARATION_KEY` — 合并声明在操作 payload 中的键。`core/crates/persistence/store/src/PreferenceMerge.rs:23`
- `PluginPreferenceSchema::KEY` — 插件偏好 schema 在操作 payload 中的键。`core/crates/persistence/store/src/PreferenceMerge.rs:23`
- PreferenceMergeSchema 的 `owner` — 按路径解析偏好 owner。`core/crates/persistence/store/src/PreferenceMerge.rs:76`
- `declarePlugin` — 登记插件偏好合并声明。`core/crates/persistence/store/src/PreferenceMerge.rs:92`
- `validateDeclaration` — 校验单份合并声明。`core/crates/persistence/store/src/PreferenceMerge.rs:119`
- `validateSchema` — 校验整份合并 schema 的聚合限制。`core/crates/persistence/store/src/PreferenceMerge.rs:168`
- `combineDeclarations` — 保留两份声明中较完整的一份。`core/crates/persistence/store/src/PreferenceMerge.rs:249`
- `PreferenceMergeOutcome` — 单个数据集的合并执行结果。`core/crates/persistence/store/src/PreferenceMerge.rs:262`
- `applyIndependentOperations` — 对每个数据集独立应用合并操作。`core/crates/persistence/store/src/PreferenceMerge.rs:269`
- `registry` — 构造普通同步与最终比较/纠正共享的注册表。`core/crates/persistence/store/src/PreferenceMerge.rs:308`
- `applyOperations` — 汇总各数据集的合并执行结果。`core/crates/persistence/store/src/PreferenceMerge.rs:407`
- `declaredAliases` — 只解析已显式记录的别名决定。`core/crates/persistence/store/src/PreferenceMerge.rs:435`
- `applyDeclaredOperations` — 重放一个数据集并提交业务状态。`core/crates/persistence/store/src/PreferenceMerge.rs:466`
- `migrateSyncedEntries` — 对同步条目执行迁移。`core/crates/persistence/store/src/PreferenceMerge.rs:516`
- `rewriteReferences` — 按规范身份映射重写已声明引用。`core/crates/persistence/store/src/PreferenceMerge.rs:620`
- `rewriteReferenceValue` — 按有界显式选择器重写已声明引用值。`core/crates/persistence/store/src/PreferenceMerge.rs:750`
- `resolveIdentity` — 沿别名映射传递解析身份。`core/crates/persistence/store/src/PreferenceMerge.rs:809`
- `referenceKey` — 为规范身份映射构造带命名空间的键。`core/crates/persistence/store/src/PreferenceMerge.rs:826`

## 调用链

主题安装 → 外观配置：

1. 用户新建外观配置，选择默认外观、当前外观、继承已有配置，或已安装 ToolPkg 声明的模板。`docs/theme-v1-contract.md:45`
2. 模板来源每次打开新建对话框时通过 `packageManager().getToolPkgContainerRuntimes()` 动态读取。`docs/theme-v1-contract.md:45`
3. `previewToolPkgTheme(packageName, templateId)` 读取当前注册包，验证模板和媒体，返回规范化视觉 JSON 与资源。`docs/theme-v1-contract.md:47`
4. `ThemeTemplateService` 把模板图片和字体复制到 `runtime/data/user_assets/theme` 资源池，把包内相对引用替换为外观资源引用。`docs/theme-v1-contract.md:47`
5. `ThemeConfigManager.create` 和 `apply` 创建并选中独立配置。`docs/theme-v1-contract.md:47`
6. 配置和复制后的资源沿用原有 Space 同步；后续渲染不再依赖来源插件是否安装。`docs/theme-v1-contract.md:51`

偏好写操作 → 合并执行器：

1. 插件 `edit()` 回调通过原生偏好事务发布变更；回调抛异常时不发布任何偏好变更。`docs/plugin-storage.md:20`
2. `withSchema(version, steps)` 声明持久化在引擎自有元数据里，包含在导出的初始化事务中，由后台同步恢复，无需启动插件。`docs/plugin-storage.md:22`
3. 文档写明原生引擎通过 `Transaction::migration::Context` 对完整数据与旧原子事务执行同一套规则。`docs/plugin-storage.md:26`
4. 重放前调用 `store.migrateSyncedEntries(version, preferences, &mut entries)` 对同步条目执行迁移。`core/crates/persistence/store/src/PreferenceMerge.rs:516`
5. `declaredAliases` 只解析已显式记录的别名决定，绝不从内容推断身份。`core/crates/persistence/store/src/PreferenceMerge.rs:435`
6. `rewriteReferences` 按执行器的规范身份映射重写已声明的引用。`core/crates/persistence/store/src/PreferenceMerge.rs:620`
7. `applyIndependentOperations` 对每个数据集独立应用；稳定引用不合并提交或失败边界。`core/crates/persistence/store/src/PreferenceMerge.rs:269`

## 来源

- Seed 文件（基线 AAswordman/Operit2 @ `364d1d594`，2026-11-12 全文读完，合计 2084 行）：`docs/theme-v1-contract.md`（55 行）、`docs/plugin-storage.md`（80 行）、`core/crates/persistence/store/src/PreferenceMerge.rs`（828 行）、`core/crates/runtime/application/src/data/preferences/UserPreferencesManager.rs`（189 行）、`core/crates/runtime/application/src/data/preferences/ThemePreferenceSnapshot.rs`（932 行）。
- 主题契约见 [[core-plugin-theme|插件——主题 v1 契约]]；主题即插件见 [[plugin-theme|主题即插件（theme-as-ToolPkg）]]。
- “主题偏好 schema 3→4 迁移”已定位（2026-11-12，基线 `364d1d594`）：`UserPreferencesManager.rs:36` 的 `store` 以 `.withMigration(5, Self::migration)` 打开 `USER_PREFERENCES_PATH`；`migratePreferences` 的 3 分支（`:89`–`:103`）调用 `migrateLegacyThemePreferences`（`ThemePreferenceSnapshot.rs:643`）解码旧主题偏好，再逐条对 `theme_config_*` 配置做 `migrateLegacyThemeSnapshot`（`ThemePreferenceSnapshot.rs:656`）并 `validateConfig`；4 分支（`:104` 起）把 `chat_style` 拆分为 `user_chat_style` / `ai_chat_style`。原 grep 只搜 `withSchema` 未覆盖 `withMigration`，因而漏检；`withSchema(3` 的生产代码命中另有所指：`PreferenceSpaceMerge.rs:196`（同步偏好布局，`core/crates/runtime/application/src/data/preferences/PreferenceSpaceMerge.rs`）与 `RuntimePackageManager.rs:338`（包管理器偏好，`core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs`），均非主题偏好迁移。
- 结论：大纲备注的“主题偏好 schema 3→4 迁移”已有实现，本页按上述锚点写该迁移；插件 `withSchema`（v1/v2）与偏好文件 format（0–5）是两套版本体系。
- 合并执行器无主题专属代码：`grep -ni "theme" core/crates/persistence/store/src/PreferenceMerge.rs` 零命中；`grep -rni "theme" core/crates/persistence/store/src/` 的命中只在 `RuntimeStorageRepository.rs` 的 `themeAssetsDirPath` 与测试文件里以 "theme" 作示例键。
- 快照字段数：本页不写任何主题快照字段数；三份 seed 均未给出字段口径，`grep -n "78"` 在三份 seed 内零命中。
- 限定：本页不写“粗粒度触发、跨端同步、revision 水位线”三链模型，五份 seed 未逐行给出该模型的定义与实现锚点；revision 在 seed 内只出现两次：`docs/plugin-storage.md:26` 的“保留原始业务 revision”与 `core/crates/persistence/store/src/PreferenceMerge.rs:480` 的 `Revision::fromOperation` 排序；本页只写到文档声明与代码声明的范围，不写实机验证结论；文档来源的断言在正文以“文档写明”标出，与 Rust 代码实现事实区分。
- 测试覆盖核验（2026-11-12，`grep -c "#[test]"`）：`PreferenceSpaceMerge.rs` 11 个测试，含重放用例 `:525` 与 `:707`；`ThemeConfigManager.tests.rs` 48 个测试，含 4 分支迁移 `:1106` 与同步快照迁移 `:1243`；上述测试文件只作佐证，不作正文引用。
