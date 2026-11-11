---
title: 插件——Plugin SDK
module: core
platforms: [all]
sources: 7
date: 2026-11-11
---

## 概述

Plugin SDK 是 Operit2 插件体系的公开契约层，定义 ToolPkg 包模型、包管理器、hook 注册与 JavaScript SDK 类型（`core/crates/plugin/sdk/src/lib.rs:5`）。
宿主通过注入执行引擎工厂、资源源、文件系统宿主与包状态解析器四组接口使用它（`core/crates/plugin/sdk/src/PackageManager.rs:34`）。时效标注：以上为截至基线 364d1d594 的描述，第三组输入为 `fileSystemHost: Arc<dyn FileSystemHost>`（`core/crates/plugin/sdk/src/PackageManager.rs:37`）；上游 053c6686 已改为 filesystem: Arc<VisualFileSystem>（同文件 :37），并将同一 VFS 实例传给 ToolPkgManager（ToolPkgManager.rs:95、103），四组输入为执行引擎工厂、资源源、Arc<VisualFileSystem>、包状态解析器，第三组是 VFS 实例而非平台文件系统 Host；直接传入旧 Arc<dyn FileSystemHost> 与当前签名不匹配。
包有两种形态：普通 JavaScript 包（`ToolPackage`）与 ToolPkg 容器（.toolpkg 归档或目录，含 manifest、main 脚本与子包）（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:629`）。
ToolPkg 的执行与管理（包工具调用、MCP 桥接）见 [[core-tool-packages-mcp|工具系统——包、技能与 MCP]]。
本页不展开 `JsExecutionHost` 与 `JsExecutionProvider` 两个 trait 的分工：两者定义于 `core/crates/plugin/sdk/src/javascript.rs`，不在本页 seed 文件内。

## AI 速览

- `ToolPkgManifest` — ToolPkg 清单文件模型（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:641`）
- `ToolPkgContainerRuntime` — ToolPkg 容器的运行时记录（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:523`）
- `ToolPkgLoadResult` — 解析一条 ToolPkg 的产物：容器包、子包、容器运行时、市场来源（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:633`）
- `ToolPkgManager` — 容器运行时、资源与执行引擎的管理者（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:87`）
- `PluginPackageManager` — JavaScript 包与 ToolPkg 状态的对外管理器（`core/crates/plugin/sdk/src/PackageManager.rs:23`）
- `ToolPkgHookDispatcher` — hook 分发的契约，只有一个方法 `dispatchToolPkgHook`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:211`）
- `ToolPkgHookInvocation` — 一次 hook 调用的完整输入（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:190`）
- `CoreHost` — 插件调用工具与完成执行的宿主契约（`core/crates/plugin/sdk/src/js_sdk/core.rs:171`）
- `ToolCatalog` — 设备发现返回的公开工具名与模式列表（`core/crates/plugin/sdk/src/js_sdk/core.rs:59`）
- 主入口函数：ToolPkgArchiveParser 的 `parseToolPkgFromIndexedEntries`（解析）（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:825`）
- 主入口函数：PluginPackageManager 的 `registerToolPkg`（注册）（`core/crates/plugin/sdk/src/PackageManager.rs:85`）
- 主入口函数：ToolPkgManager 的 `dispatchToolPkgHook`（执行 hook）（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:932`）
- 数据流向：`.toolpkg` 归档或目录 → manifest 与 main 脚本 → `ToolPkgLoadResult` → 注册进容器与子包两张运行时表 → 依赖排序 → 按需取 main 脚本与 JS 引擎执行 hook 或 Compose DSL 界面。

## 核心机制

### 包模型：ToolPkg 清单

- `ToolPkgManifest` 含 `schema_version`、`toolpkg_id`、`version` 与 `api_version`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:645`）。
- `ToolPkgManifest` 含 `public_api`、`requires` 与 `main`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:653`）。
- ToolPkgManifest 含 display_name、`description`、`author`、`logo` 与 `license`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:663`）。
- `ToolPkgManifest` 含 `enabled_by_default`、`market_only` 与 `installation_scope`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:671`）。
- `ToolPkgManifest` 含 `subpackages`、`themes`、`resources` 与 `wasm_modules`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:677`）。
- `ToolPkgManifest` 含 `workspace_templates`，并以 `#[serde(flatten)]` 收纳全部扩展字段（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:684`）。
- schema_version 省略时默认 1（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2587`）。
- 省略 `api_version` 的清单按 1.0.0 解析（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:648`；缺省值函数见 `core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:65`）。
- enabled_by_default 省略时默认 true（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2593`）。
- `ToolPkgSourceType` 只有 `ASSET`、`MARKET`、`EXTERNAL` 三种，默认 `ASSET`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:19`）。
- `findManifestEntry` 先找根目录的 `manifest.hjson`，找不到再找 `manifest.json`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2508`）。
- 根目录没有清单时，findManifestEntry 再按子目录 `manifest.hjson`、子目录 manifest.json 的顺序找（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2521`）。

### 清单校验规则

- 解析时先校验 manifest 的 api_version 是否受支持，不支持直接失败（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:854`）。
- `manifest.toolpkg_id` 为空时解析失败（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:871`）。
- `manifest.public_api` 必须引用包内已存在的 TypeScript 文件（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:881`）。
- `manifest.main` 为空且声明了 public_api 或子包时解析失败（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:916`）。
- 声明了子包但一个都未成功加载时解析失败（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1015`）。
- wasm 模块的 `abi` 只接受 `scalar` 与 `memory`，其他值解析失败（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1094`）。
- 一个 ToolPkg 最多注册一个 chat lifecycle hook，超过一个解析失败（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1433`）。
- v1 契约自动补两条兼容依赖：`com.operit.workflow` 最低 0.2.0、`com.operit.character_cards` 最低 0.1.0（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2271`）。
- 兼容提供方自身不得使用 v1 契约，否则解析失败（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2291`）。
- validateProtectedEntryPolicy 的函数体直接返回 `Ok`，未执行保护策略校验（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1835`）。

### 包管理：三层状态与条件状态

- `PluginPackageManager` 持有 `activatedPackages`、`availablePackages`、`enabledPackageNames`、`activePackageStateIds` 四组集合与一个内嵌 `ToolPkgManager`（`core/crates/plugin/sdk/src/PackageManager.rs:24`）。
- `registerPackage` 注册或替换一个 JavaScript 包定义，包名先经 `normalizePackageName` 规整（`core/crates/plugin/sdk/src/PackageManager.rs:78`）。
- `setEnabledPackageNames` 整体替换启用包集合，空名被过滤（`core/crates/plugin/sdk/src/PackageManager.rs:182`）。
- `enablePackage` 只在内存中标记启用（`core/crates/plugin/sdk/src/PackageManager.rs:205`）。
- `disablePackage` 同时移除激活记录与启用标记（`core/crates/plugin/sdk/src/PackageManager.rs:211`）。
- `activatePackage` 标记包在当前请求或提示会话内激活（`core/crates/plugin/sdk/src/PackageManager.rs:219`）。
- `selectPackageState` 用包状态解析器选定条件状态并记录状态 id，返回应用状态后的包（`core/crates/plugin/sdk/src/PackageManager.rs:244`）。
- `effectivePackage` 返回当前可解析条件状态应用后的包定义（`core/crates/plugin/sdk/src/PackageManager.rs:254`）。
- `effectiveTool` 只选调用方指定的可执行项，其余脚本借用不复制（`core/crates/plugin/sdk/src/PackageManager.rs:264`）。
- `mergeToolRefsForState` 按 `inherit_tools` 继承基础工具、按 exclude_tools 剔除、再按状态自带 `tools` 覆盖（`core/crates/plugin/sdk/src/PackageManager.rs:310`）。
- `normalizePackageName` 只做 `trim`，不做大小写折叠（`core/crates/plugin/sdk/src/PackageManager.rs:323`）。
- `updatePackageStateResolver` 更换包状态解析器后清空已记录的状态选择（`core/crates/plugin/sdk/src/PackageManager.rs:58`）。

### 注册：名字冲突与先发布后撤销

- `registerToolPkg` 先经 `canRegisterToolPkg` 校验，失败返回 false；成功后注册容器包与全部可执行子包（`core/crates/plugin/sdk/src/PackageManager.rs:85`）。
- 容器名为空、已是容器或已是可用包时不可注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:230`）。
- 子包名为空、与容器冲突、与可用包冲突或与已注册子包冲突时不可注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:239`）。
- `registerToolPkg` 登记容器运行时、记录修订指纹并返回可执行子包（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:251`）。
- registerToolPkg 先发布替换再撤销容器执行上下文，避免竞态创建者绑定旧元数据（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:269`）。
- `removePackage` 删一个包或整个 ToolPkg 容器，并同步清理启用、激活与状态记录（`core/crates/plugin/sdk/src/PackageManager.rs:156`）。

### 依赖解析：拓扑排序与问题码

- `resolveToolPkgDependencies` 把前置排在依赖方之前，并为每个未满足依赖标注问题（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:373`）。
- 依赖不存在时问题码为 `missing`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:385`）。
- 版本越界时问题码为 `version_incompatible`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:391`）。
- 依赖未启用时问题码为 `disabled`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:392`）。
- 循环或自依赖等无法解析时问题码为 `unresolved`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:423`）。
- `getEnabledToolPkgContainerRuntimes` 只返回无依赖问题且自身或任一子包已启用的容器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:442`）。
- `isEnabledToolPkgContainer` 只在容器及其传递前置都可执行时返回真（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:362`）。
- `ToolPkgDependencyIssue` 记录依赖 id、问题码、要求版本上下限、已安装版本与是否启用（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:697`）。
- `ToolPkgManifestRequirement` 含 `id`、`description`、`min_version` 与 `max_version`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:706`）。

### Hook 系统：挂载点

- ToolPkgMainRegistration 含 `toolboxUiModules`、`uiRoutes`、`chatComposerSlots`、`navigationEntries`、`desktopWidgets` 五组 UI 注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:454`）。
- ToolPkgMainRegistration 含 `appLifecycleHooks`、`messageProcessingPlugins`、`xmlRenderPlugins`、`inputMenuTogglePlugins` 四组 hook 注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:462`）。
- ToolPkgMainRegistration 含 `chatInputHooks`、`chatViewHooks`、`chatMessageHooks`、`chatLifecycleHooks` 四组聊天 hook 注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:470`）。
- ToolPkgMainRegistration 含 `promptInputHooks`、`promptHistoryHooks` 与 `promptEstimateHistoryHooks` 三组提示词 hook 注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:488`）。
- ToolPkgMainRegistration 含 `systemPromptComposeHooks`、`toolPromptComposeHooks`、`promptFinalizeHooks`、`promptEstimateFinalizeHooks` 与 `summaryGenerateHooks` 五组提示词 hook 注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:496`）。
- `ToolPkgAppLifecycleHookRegistration` 含容器包名、`hookId`、事件名、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:11`）。
- `ToolPkgMessageProcessingHookRegistration` 含容器包名、`pluginId`、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:22`）。
- `ToolPkgXmlRenderHookRegistration` 另含 `tag` 字段，按标签分派渲染函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:32`）。
- `ToolPkgInputMenuToggleHookRegistration` 含容器包名、`pluginId`、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:43`）。
- `ToolPkgChatInputHookRegistration` 含容器包名、`hookId`、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:53`）。
- `ToolPkgChatViewHookRegistration` 含容器包名、`hookId`、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:63`）。
- `ToolPkgChatMessageHookRegistration` 含容器包名、`hookId`、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:73`）。
- `ToolPkgManifestExtensionRegistration` 含容器包名、扩展键、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:83`）。
- `ToolPkgChatMessageMenuItemRegistration` 含容器包名、`itemId`、标题、图标、排序、`senders`、函数名、函数源码与可选对话框（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:103`）。
- `ToolPkgChatRuntimeHookRegistration` 含容器包名、`hookId`、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:116`）。
- `ToolPkgToolLifecycleHookRegistration` 含容器包名、`hookId`、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:126`）。
- `ToolPkgPromptHookRegistration` 含容器包名、`hookId`、函数名与可选函数源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:136`）。
- `ToolPkgAiProviderRegistration` 含 `providerId`、`displayName` 与 `description`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:147`）。
- ToolPkgAiProviderRegistration 含 `listModels` 与 `sendMessage` 两组函数名与源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:150`）。
- ToolPkgAiProviderRegistration 含 `testConnection` 与 `calculateInputTokens` 两组函数名与源码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:154`）。
- `ToolPkgChatLifecycleHookRegistration` 的注释强调 `hookId` 标识实际注册且启用的包，`functionName` 标识真实导出的 main hook 函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:166`）。
- `ToolPkgHostEventRegistration` 含容器包名、`hookId`、来源、触发条件、函数名、函数源码与启用开关（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:180`）。

### Hook 分发：调用输入与超时语义

- `ToolPkgHookInvocation` 含 `containerPackageName`、`functionName`、`event` 与 `eventName`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:192`）。
- ToolPkgHookInvocation 含 `pluginId`、`inlineFunctionSource`、`eventPayload`、`executionContextKey` 与 `runtimeKind`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:196`）。
- ToolPkgHookInvocation 含 `envOverrides` 与 `timestampMs`，`timeoutMillis` 只约束显式定时的 before hook（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:201`）。
- `ToolPkgHookDispatcher` 只有一个方法 `dispatchToolPkgHook`，按启用包名集合与一次调用入参执行 hook（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:211`）。
- dispatchToolPkgHook 有 `timeoutMillis` 时走带超时的执行入口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:943`）。
- dispatchToolPkgHook 无 timeoutMillis 时走普通执行入口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:957`）。
- `dispatchToolPkgHookAsync` 是 `dispatchToolPkgHook` 的异步包装（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:977`）。
- hook 参数含 `event` 与 `eventName`，`eventName` 省略时取 `event`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:1011`）。
- hook 参数含 `eventPayload`、`timestampMs` 与 `functionName`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:1025`）。
- hook 参数含 `toolPkgId`、`containerPackageName` 与 `__operit_toolpkg_api_version`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:1036`）。
- resolveToolPkgExecutionContextKey 未指定执行上下文键时默认 toolpkg_main:{容器包名}（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:1129`）。
- `decodeToolPkgHookResult` 把空串当字符串返回，能解析为 JSON 的返回 JSON 值，否则返回原字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:226`）。
- `addToolPkgRuntimeChangeListener` 注册监听器后立即推送一次当前活跃容器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:455`）。
- `notifyToolPkgRuntimeChangeListeners` 向全部已注册监听器推送活跃容器列表（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:472`）。

### Compose DSL：UI 声明

- `ToolPkgUiModuleRuntime` 含 `id`、`runtime`、`screen`、`screenExport`、`title` 与 `keepAlive`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:57`）。
- 注册的 UI 路由未声明 `runtime` 时，解析器以 `TOOLPKG_RUNTIME_COMPOSE_DSL` 补默认值（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1243`）。
- 工具箱 UI 模块与导航条目的路由 id 由 `buildToolPkgRouteId` 按容器包名与模块 id 生成（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1204`）。
- 嵌入式 UI surface 的导航路由 id 必须以 toolpkg:{容器包名}:ui: 开头（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1359`）。
- 嵌入式 UI surface 的导航路由必须使用 `TOOLPKG_RUNTIME_COMPOSE_DSL` 运行时（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1369`）。
- 聊天输入框插槽只接受 `TOOLPKG_CHAT_COMPOSER_SLOT_ABOVE_INPUT` 一个 slot 值（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1314`）。
- `ToolPkgSubpackageRuntime` 含 `packageName`、`containerPackageName`、`subpackageId`、`entryPath` 四个身份字段（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:226`）。
- ToolPkgSubpackageRuntime 还含 `displayName`、`description`、`enabledByDefault` 与 `toolCount`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:233`）。
- `ToolPkgManifestSubpackage` 只含 `id` 与 `entry` 两个字段（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:714`）。
- `ToolPkgManifestTheme` 含 `id`、`path`、`preview` 与 `files`，拒绝未知字段（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:724`）。

### 执行引擎与租约

- `createExecutionEngine` 创建不带 ToolPkg 包环境的隔离 JS 引擎（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:23`）。
- `createToolPkgExecutionEngine` 按 `ToolPkgExecutionContext` 创建隔离 JS 引擎（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:27`）。
- `acquireToolPkgExecutionEngine` 异步获取已准备好的包引擎（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:34`）。
- `ToolPkgAssetSource` 按资源名返回内嵌 ToolPkg 归档字节（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:41`）。
- `ToolPkgExecutionEngineEntry` 把一个缓存 JS 引擎与所属容器包名、活跃租约数与容器持有标记绑在一起（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:49`）。
- `ToolPkgExecutionEngineLease` 在 `Drop` 时释放执行租约（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:65`）。
- `getToolPkgExecutionEngine` 取缓存引擎或新建一个，不计租约（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:542`）。
- `acquireToolPkgExecutionEngine` 为一个执行上下文计一次租约（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:552`）。
- `leaseToolPkgExecutionEngine` 取引擎与租约对象，租约 Drop 时释放（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:558`）。
- `leaseToolPkgMainExecutionEngine` 以 toolpkg_main:{包名} 为上下文键租用容器持有的 main realm（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:568`）。
- `revokeContainerExecutionContexts` 撤销一个容器的全部上下文，包括已租出的上下文（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:778`）。
- `updateExecutionEngineFactory` 更换引擎工厂并销毁全部缓存引擎（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:119`）。
- `shutdownExecutionEngines` 结束 Core 生命周期内的全部引擎，包括在途与容器持有的 realm，并拒绝此后调度的旧工作（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:130`）。
- getToolPkgMainScriptInternal 只返回已启用容器的 main 脚本，未启用或 main 入口为空时返回 `None`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:495`）。
- `getRegisteredToolPkgMainScript` 不检查启用状态，只要求 main 入口非空（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:504`）。
- readToolPkgTextResource 先按容器名找运行时，找不到再按子包 id 找所属容器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:521`）。
- readToolPkgTextResource 要求容器本身或其任一子包在启用名集合中，否则返回 `None`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:530`）。
- `EXTERNAL` 与 `MARKET` 来源的目录源直接读文件（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:864`）。
- `.toolpkg` 文件源先读整个归档文件，再按条目名取资源（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:881`）。
- `ASSET` 来源从内嵌归档字节中按条目名读资源（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:893`）。
- `normalizeToolPkgEntryPath` 拒绝空路径、绝对路径与含 `..` 的路径（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:1142`）。

### JS SDK：宿主契约与工具目录

- `JsonObject` 是保留完整值的 JSON 对象类型别名（`core/crates/plugin/sdk/src/js_sdk/core.rs:9`）。
- `ToolParams` 以 `flatten` 的 `BTreeMap` 存任意具名参数（`core/crates/plugin/sdk/src/js_sdk/core.rs:22`）。
- `ToolConfig` 含工具类别、工具名、参数与流式中间结果回调（`core/crates/plugin/sdk/src/js_sdk/core.rs:32`）。
- `ToolCatalogParameter` 含参数名、类型、描述、是否必填与默认值（`core/crates/plugin/sdk/src/js_sdk/core.rs:40`）。
- `ToolCatalogEntry` 含工具名、描述、参数列表、类别、来源与所属包名（`core/crates/plugin/sdk/src/js_sdk/core.rs:52`）。
- `ToolCatalog` 是设备发现返回的公开工具名与模式列表（`core/crates/plugin/sdk/src/js_sdk/core.rs:59`）。
- `DeviceToolOptions` 的 `timeoutMs` 含连接与权限检查在内，默认 120000 毫秒；`signal` 用于中止时关闭远程执行流（`core/crates/plugin/sdk/src/js_sdk/core.rs:64`）。
- BaseResult 以 `success` 与 `error` 报告操作是否成功（`core/crates/plugin/sdk/src/js_sdk/core.rs:83`）。
- `ToolResult` 分 `String`、`Boolean`、`Number`、`Dynamic` 四种结果（`core/crates/plugin/sdk/src/js_sdk/core.rs:153`）。
- CoreHost 提供按类别与工具名调用工具的重载 `toolCall_overload_1`（`core/crates/plugin/sdk/src/js_sdk/core.rs:177`）。
- CoreHost 提供动态工具名调用 `toolCall_overload_6`（`core/crates/plugin/sdk/src/js_sdk/core.rs:210`）。
- CoreHost 的 `complete` 完成工具执行，返回值必须可 JSON 序列化（`core/crates/plugin/sdk/src/js_sdk/core.rs:216`）。
- LodashApi 提供 `isEmpty`、`isString`、`isNumber`、`isBoolean`、`isObject`、`isArray` 六组类型判断（`core/crates/plugin/sdk/src/js_sdk/core.rs:233`）。
- LodashApi 提供 `forEach` 与 `map` 两组集合迭代（`core/crates/plugin/sdk/src/js_sdk/core.rs:244`）。
- `DataUtilsApi` 提供 `parseJson`、`stringifyJson` 与 `formatDate` 三组数据转换（`core/crates/plugin/sdk/src/js_sdk/core.rs:260`）。
- `AbortSignal` 含 `aborted` 与 `reason` 两个字段，是每个插件运行时的标准取消信号（`core/crates/plugin/sdk/src/js_sdk/core.rs:272`）。
- `AbortController` 暴露 `signal` 字段（`core/crates/plugin/sdk/src/js_sdk/core.rs:292`）。
- AbortController 的 `abort` 恰好取消一次，可带原因（`core/crates/plugin/sdk/src/js_sdk/core.rs:300`）。

## 关键符号

- `ToolPkgManifest` — ToolPkg 清单文件模型（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:641`）
- `ToolPkgContainerRuntime` — ToolPkg 容器的运行时记录（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:523`）
- `ToolPkgLoadResult` — 解析一条 ToolPkg 的产物（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:633`）
- `ToolPkgMainRegistration` — main 脚本注册的全部贡献汇总（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:446`）
- `ToolPkgMainRegistrationParseResult` — main 注册解析结果，只有 `Success` 与 `Failure`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:513`）
- `ToolPkgArchiveParser` — ToolPkg 归档解析器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:795`）
- ToolPkgEntryIndex — 归档条目归一化索引（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:735`）
- `ToolPkgManager` — 容器运行时、资源与执行引擎的管理者（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:87`）
- `PluginPackageManager` — JavaScript 包与 ToolPkg 状态的对外管理器（`core/crates/plugin/sdk/src/PackageManager.rs:23`）
- `PackageStateResolver` — 解析一个包当前条件状态的宿主接口（`core/crates/plugin/sdk/src/PackageManager.rs:14`）
- `ToolPkgExecutionEngineFactory` — 创建 ToolPkg 执行引擎的宿主接口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:20`）
- `ToolPkgAssetSource` — 内嵌 ToolPkg 归档字节的宿主接口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:41`）
- `ToolPkgHookDispatcher` — hook 分发的契约（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:211`）
- `ToolPkgHookInvocation` — 一次 hook 调用的完整输入（`core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs:190`）
- `CoreHost` — 插件调用工具的宿主契约（`core/crates/plugin/sdk/src/js_sdk/core.rs:171`）
- `ToolCatalog` — 设备发现返回的公开工具列表（`core/crates/plugin/sdk/src/js_sdk/core.rs:59`）

## 调用链

1. 宿主创建 `PluginPackageManager`，注入执行引擎工厂、资源源、文件系统宿主与包状态解析器（`core/crates/plugin/sdk/src/PackageManager.rs:34`）。时效标注：以上为截至基线 364d1d594 的描述，第三组输入为 `fileSystemHost: Arc<dyn FileSystemHost>`（`core/crates/plugin/sdk/src/PackageManager.rs:37`）；上游 053c6686 已改为 filesystem: Arc<VisualFileSystem>（同文件 :37），并将同一 VFS 实例传给 ToolPkgManager（ToolPkgManager.rs:95、103），四组输入为执行引擎工厂、资源源、Arc<VisualFileSystem>、包状态解析器，第三组是 VFS 实例而非平台文件系统 Host；直接传入旧 Arc<dyn FileSystemHost> 与当前签名不匹配。
2. 解析 ToolPkg：ToolPkgArchiveParser 的 `parseToolPkgFromIndexedEntries` 建条目索引、找 manifest、校验 api_version 与清单字段、解析子包与 main 注册，产出 ToolPkgLoadResult（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:825`）。
3. 注册：PluginPackageManager 的 `registerToolPkg` 先经 `canRegisterToolPkg` 校验名字冲突，再由 ToolPkgManager 的 `registerToolPkg` 登记容器与子包两张运行时表（`core/crates/plugin/sdk/src/PackageManager.rs:85`）。
4. 启用与依赖排序：setEnabledPackageNames 替换启用集合，`resolveToolPkgDependencies` 做拓扑排序并标注问题码，getEnabledToolPkgContainerRuntimes 取可执行容器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:373`）。
5. 执行 hook：ToolPkgManager 的 `dispatchToolPkgHook` 经 prepareToolPkgHook 取 main 脚本、租用执行引擎、组装事件参数，再调脚本函数执行（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:932`）。
6. 读资源：readToolPkgTextResource 按包名或子包 id 找容器并校验启用状态，再按来源类型读文本资源（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:521`）。
7. 读 main 脚本：getToolPkgMainScriptInternal 只返回已启用容器的 main 脚本（`core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs:495`）。

## 来源

- `core/crates/plugin/README.md`
- `core/crates/plugin/sdk/src/lib.rs`
- `core/crates/plugin/sdk/src/PackageManager.rs`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgManager.rs`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgHooks.rs`
- `core/crates/plugin/sdk/src/js_sdk/core.rs`
