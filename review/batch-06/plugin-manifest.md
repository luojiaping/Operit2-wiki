---
title: 清单 manifest 与安装作用域
module: plugins
platforms: [all]
sources: [7]
date: 2026-11-11
---

## 概述

- manifest 是 ToolPkg 包的清单文件，解析结构体为 `ToolPkgManifest`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:641`
- 清单入口优先查找 `manifest.hjson`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2506`
- 清单入口在无 `manifest.hjson` 时查找 `manifest.json`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2510`
- `.hjson` 清单用 json5 解析。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2554`
- 文档声明：`schema_version`、`api_version` 与 `version` 是三个不同的标识。`plugins/docs/V1_COMPATIBILITY.md:22`
- 文档声明：`2.0.0` 面向多平台设计。`plugins/docs/V1_COMPATIBILITY.md:12`
- 文档声明：`1.0.0` 与 `1.0.1` 是主要面向 Android 的旧版 API 形态。`plugins/docs/V1_COMPATIBILITY.md:9`

## AI 速览

- `ToolPkgManifest` — 清单解析结构体，字段全称以它为准。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:641`
- `ToolPkgConfigScope` — `installation_scope` 字段使用的安装作用域类型。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:674`
- `installation_scope` 只接受 `device` 与 `space` 两个取值。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:3167`
- `ToolPkgArchiveParser` 的 `readInstallationScope` — 在注册脚本执行前读取安装限制。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:800`
- `ToolPkgApiVersion` — 解析后的 `major.minor.patch` 版本值。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:25`
- `requireSupportedToolPkgApiVersion` — 校验声明的 api_version 是否在支持清单内。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:84`
- `applyCompatibilityRequirements` — 为主版本为 1 的包追加兼容 requires。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2283`
- `ToolPkgContainerRuntime` — 加载后保留 `version` 与 `apiVersion` 的运行时记录。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:525`
- 主入口函数：`ToolPkgArchiveParser` 的 `readInstallationScope`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:802`
- 数据流向一句话：加载时 api_version 必须通过 `requireSupportedToolPkgApiVersion` 校验。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:854`

## 核心机制

### 字段清单

- `ToolPkgManifest` 的 `schema_version` 字段在 JSON 中写作 `schema_version`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:642`
- 省略 `schema_version` 时 `defaultSchemaVersion` 返回 1。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:642`
- `toolpkg_id` 为必填字段，空值加载失败。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:871`
- `ToolPkgManifest` 的 `version` 字段保存插件版本号。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:646`
- `ToolPkgManifest` 的 `api_version` 字段在 JSON 中写作 `api_version`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:646`
- 省略 `api_version` 时取 `defaultToolPkgApiVersionText` 的返回值。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:648`
- `defaultToolPkgApiVersionText` 返回 `TOOLPKG_API_VERSION_1_0_0`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:65`
- `public_api` 指向分发给依赖包的自包含 TypeScript 客户端。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:650`
- `public_api` 必须指向包内已存在的 `.ts` 文件。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:880`
- `requires` 是 `Vec<ToolPkgManifestRequirement>`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:654`
- `ToolPkgManifestRequirement` 的 `min_version` 是可选的版本下限。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:707`
- `ToolPkgManifestRequirement` 的 `max_version` 是可选的版本上限。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:707`
- `main` 是主脚本入口字段。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:656`
- `main` 为空且声明 public_api 或 `subpackages` 时加载失败。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:916`
- `display_name` 与 `description` 均为 `LocalizedText`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:658`
- `author` 接受单个字符串或字符串列表。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:661`
- `license` 引用包内分发的协议文本。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:665`
- 省略 `enabled_by_default` 时 `defaultEnabledByDefault` 返回 true。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:668`
- `market_only` 是 manifest 布尔字段。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:671`
- `ToolPkgManifestSubpackage` 只有 `id` 与 `entry` 两个字段。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:714`
- `ToolPkgManifestTheme` 的元素含 `id`、`path`、`preview` 与 `files`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:722`
- `ToolPkgManifestResource` 的元素含 `key`、`path` 与 `mime`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:731`
- `ToolPkgManifestWasmModule` 的元素含 `id`、`path`、`exports`、`source_language` 与 `abi`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:743`
- wasm 模块路径必须指向 `.wasm` 文件。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1079`
- wasm 模块的 `abi` 只接受 `scalar` 与 `memory`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1093`
- `workspace_templates` 是 manifest 字段。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:684`
- 未知字段经 flatten 保留进 `extensionFields`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:686`
- `extensionFields` 的类型为 `BTreeMap<String, Value>`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:687`
- `ToolPkgContainerDetails` 含 `logoResourceKey` 与 `logoMimeType`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgPackageModels.rs:29`

### 安装作用域

- `installation_scope` 在 JSON 中写作 `installation_scope`，类型为 `Option<crate::javascript::ToolPkgConfigScope>`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:674`
- `installation_scope` 把安装限制为一个明确的 `device` 或 `space` 作用域。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:672`
- `installation_scope` 只接受 `device` 与 `space` 两个取值。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:3167`
- `installation_scope` 取 `workspace`、`local`、`SPACE`、true 或 1 时解析失败。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:3171`
- `installation_scope` 省略时字段值为 None。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:674`
- `readInstallationScope` 在注册脚本执行前读取安装限制。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:800`
- 声明的 `installation_scope` 会被写回运行时 `manifestExtensions` 的 `installation_scope` 键。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1289`

### 环境变量与配置归属

- 子包脚本声明的环境变量名会传给 `main` 注册解析。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1181`
- 文档声明：历史 V1 `SoftwareSettings` 声明保持不变。`plugins/docs/V1_COMPATIBILITY.md:88`
- 文档声明：`readEnvironmentVariable` 与 `writeEnvironmentVariable` 在 `1.0.0` 与 `1.0.1` 下保留原签名。`plugins/docs/V1_COMPATIBILITY.md:89`
- 文档声明：V2 通过 `Tools.Models`、`Tools.Tts`、`Tools.Theme` 与 `Tools.Catalog` 暴露已配置资源。`plugins/docs/V1_COMPATIBILITY.md:95`
- 文档声明：旧版 `SoftwareSettings` 管理明确排除在本次修复之外。`plugins/docs/V1_COMPATIBILITY.md:204`
- 文档声明：`getCallerParticipantId` 的值属于已认证的配置提供方。`plugins/docs/V1_COMPATIBILITY.md:153`
- 文档声明：`registerChatMessageMenuItem` 与 `registerChatRuntimeHook` 覆盖 `1.0.1` 与 `2.0.0`。`plugins/docs/V1_COMPATIBILITY.md:137`

### 版本兼容

- `CURRENT_TOOLPKG_API_VERSION` 为 `2.0.0`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:13`
- SDK 支持的 `api_version` 只有 `1.0.0`、`1.0.1` 与 `2.0.0`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:121`
- 加载时 api_version 必须通过 `requireSupportedToolPkgApiVersion` 校验。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:854`
- 未列入支持清单的 api_version 加载时被拒绝。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:84`
- 兼容 requires 只对 api_version 主版本为 1 的包追加。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2283`
- v1 包加载时自动追加 `com.operit.workflow`（>= `0.2.0`）为 requires。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2268`
- v1 包加载时自动追加 `com.operit.character_cards`（>= `0.1.0`）为 requires。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2272`
- 文档声明：Operit2 支持的 ToolPkg API 版本是 `2.0.0`，`1.0.0` 与 `1.0.1` 的加载兼容不完整。`plugins/docs/V1_COMPATIBILITY.md:5`
- 文档声明：Operit1 完全支持 `1.0.0` 与 `1.0.1`。`plugins/docs/V1_COMPATIBILITY.md:9`
- 文档声明：新 Operit2 包显式声明 `api_version` 为 `2.0.0`。`plugins/docs/V1_COMPATIBILITY.md:20`
- 文档声明：解析器接受显式声明的 `1.0.0`、`1.0.1` 与 `2.0.0`，原始版本保留用于注册与执行。`plugins/docs/V1_COMPATIBILITY.md:36`
- 文档声明：未知版本在显式接纳前仍被拒绝。`plugins/docs/V1_COMPATIBILITY.md:38`
- 文档声明：省略 `api_version` 时按 `1.0.0` 合同加载。`plugins/docs/V1_COMPATIBILITY.md:40`
- 文档声明：`1.0.0` 不能调用 `Chat.call`，`2.0.0` 保留现有实现。`plugins/docs/V1_COMPATIBILITY.md:130`
- 文档声明：这不是每个历史插件都能原样运行的主张。`plugins/docs/V1_COMPATIBILITY.md:385`
- 文档声明：已移除的 v1 `SoftwareSettings` 模型/角色/语音/沙箱管理方法未被兼容适配器覆盖。`plugins/docs/V1_COMPATIBILITY.md:389`
- 文档声明：FFmpeg 与 Tasker 命名空间不在当前生成的 `Tools` 表面。`plugins/docs/V1_COMPATIBILITY.md:390`

### 三份示例 manifest

- `character_cards` 的 `api_version` 为 `2.0.0`。`plugins/packages/buildin/character_cards/manifest.json:5`
- `workflow` 的 `api_version` 为 `2.0.0`。`plugins/packages/buildin/workflow/manifest.json:5`
- `moss_atelier` 的 `api_version` 为 `2.0.0`。`plugins/packages/external/moss_atelier/manifest.json:5`
- character_cards 的 `logo` 字段取值为 `package_logo`。`plugins/packages/buildin/character_cards/manifest.json:16`
- character_cards 的 `resources` 包含键为 `package_logo` 的资源。`plugins/packages/buildin/character_cards/manifest.json:26`
- character_cards 的 `enabled_by_default` 为 true。`plugins/packages/buildin/character_cards/manifest.json:17`
- `workflow` 的 `enabled_by_default` 为 false。`plugins/packages/buildin/workflow/manifest.json:17`
- moss_atelier 的 `enabled_by_default` 为 false。`plugins/packages/external/moss_atelier/manifest.json:17`
- character_cards 声明 wasm 模块 `usearch`，`abi` 为 `memory`。`plugins/packages/buildin/character_cards/manifest.json:46`
- character_cards 的 subpackage `character_memory` 入口为 `dist/tools.js`。`plugins/packages/buildin/character_cards/manifest.json:21`
- `workflow` 的 subpackage `workflow` 入口为 `dist/tools.js`。`plugins/packages/buildin/workflow/manifest.json:21`
- `workflow` 的 `workflow_templates` 为空数组。`plugins/packages/buildin/workflow/manifest.json:36`
- `workflow` 的 `workspace_templates` 为空数组。`plugins/packages/buildin/workflow/manifest.json:37`
- moss_atelier 的 `themes` 包含 `id` 为 `moss` 的主题。`plugins/packages/external/moss_atelier/manifest.json:28`
- moss_atelier 的 themes 包含 `id` 为 `dune` 的主题。`plugins/packages/external/moss_atelier/manifest.json:47`

## 关键符号

- `ToolPkgManifest` — 清单解析结构体。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:641`
- `ToolPkgManifestRequirement` — 一条 requires 声明，含 `id`、`min_version` 与 `max_version`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:707`
- `ToolPkgManifestSubpackage` — 一个子包声明，含 `id` 与 `entry`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:714`
- `ToolPkgManifestTheme` — 一个主题声明，含 `id`、`path`、`preview` 与 `files`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:722`
- `ToolPkgManifestResource` — 一个资源声明，含 `key`、`path` 与 `mime`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:731`
- `ToolPkgManifestWasmModule` — 一个 wasm 模块声明，含 `id`、`path`、`exports`、`source_language` 与 `abi`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:743`
- `ToolPkgConfigScope` — 安装作用域类型，`installation_scope` 字段使用它。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:674`
- `ToolPkgContainerRuntime` — 加载后保留 `version` 与 `apiVersion` 的运行时记录。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:525`
- `ToolPkgContainerDetails` — 容器公开信息，含 `logoResourceKey` 与 `logoMimeType`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgPackageModels.rs:29`
- `ToolPkgApiVersion` — 解析后的 `major.minor.patch` 版本值。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:25`
- `requireSupportedToolPkgApiVersion` — 校验声明的 api_version 是否在支持清单内。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:84`
- `defaultToolPkgApiVersionText` — 省略 `api_version` 时返回 `TOOLPKG_API_VERSION_1_0_0`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:65`
- `supportedToolPkgApiVersions` — 列出 SDK 支持的 api_version。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:71`
- `CURRENT_TOOLPKG_API_VERSION` — 当前 SDK 暴露的 `2.0.0` 合同。`core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs:13`

## 调用链

1. `findManifestEntry` 定位清单入口，缺失时报错。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:849`
2. 解析清单文本为 `ToolPkgManifest`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:641`
3. `requireSupportedToolPkgApiVersion` 校验声明的 api_version。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:854`
4. `applyCompatibilityRequirements` 为主版本为 1 的包追加兼容 `requires`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:857`
5. 子包脚本声明的环境变量名传给 `main` 注册解析。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1181`
6. 声明的 `installation_scope` 写回运行时 `manifestExtensions`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:1289`
7. 加载结果为 `ToolPkgLoadResult`，含 `containerRuntime`。`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:629`

## 来源

- `core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgPackageModels.rs`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgApiVersion.rs`
- `plugins/docs/V1_COMPATIBILITY.md`
- `plugins/packages/buildin/character_cards/manifest.json`
- `plugins/packages/buildin/workflow/manifest.json`
- `plugins/packages/external/moss_atelier/manifest.json`
