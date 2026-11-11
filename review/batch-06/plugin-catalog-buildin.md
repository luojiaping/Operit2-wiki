---
title: 内置插件目录
module: plugins
platforms: [all]
sources: [plugins/packages/buildin/README.md, plugins/packages/buildin/character_cards/manifest.json, plugins/packages/buildin/workflow/manifest.json, plugins/packages/buildin/tsconfig.json, plugins/packages/buildin/change_review/manifest.json, plugins/packages/buildin/change_review/tsconfig.json, plugins/packages/buildin/daily_life/manifest.json, plugins/packages/buildin/goal_mode/manifest.json, plugins/packages/buildin/message_translation/manifest.json, plugins/packages/buildin/plan_mode/manifest.json, plugins/packages/buildin/12306.ts, plugins/packages/buildin/ai_chat.ts, plugins/packages/buildin/browser.ts, plugins/packages/buildin/crossref.ts, plugins/packages/buildin/extended_file_tools.ts, plugins/packages/buildin/operit_editor.ts, plugins/packages/buildin/super_admin.ts, plugins/packages/buildin/system_tools.ts, plugins/packages/buildin/time.ts, plugins/packages/buildin/character_cards/src/main.ts, plugins/packages/buildin/character_cards/src/memory-recall.ts, plugins/packages/buildin/character_cards/src/storage/database.ts, plugins/packages/buildin/character_cards/src/group-execution/executor.ts, plugins/packages/buildin/character_cards/src/search/usearch.ts, plugins/packages/buildin/character_cards/web/app.ts, plugins/packages/buildin/character_cards/vendor/usearch/index.cpp, plugins/packages/buildin/workflow/src/main.ts, core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs, core/crates/plugin/sdk/src/JsPackageLoader.rs]
date: 2026-11-11
---

## 概述

内置插件是 plugins/packages/buildin/ 下的 ToolPkg 源码，会被打包进 Operit2 内置插件资产（`plugins/packages/buildin/README.md:3`）。
磁盘清点：buildin 共 19 项，16 个插件加 README.md、tsconfig.json 与 resources/ 目录（仅含 character-memory.html，未见代码引用）。
16 个插件分两类：9 个单文件 .ts 包与 7 个目录包（磁盘清点，方法见 tracking/read-batch-06/plugin-catalog-buildin.txt）。

## AI 速览

- manifest.json — 目录包的清单，声明 `toolpkg_id` 与 `main` 入口（`plugins/packages/buildin/character_cards/manifest.json:6`）。
- `METADATA` — 单文件包文件内含的元数据注释块，多在文件顶部，super_admin.ts:42 例外（`plugins/packages/buildin/12306.ts:1`）（`plugins/packages/buildin/super_admin.ts:42`）。
- `enabledByDefault` — 单文件包是否默认启用，12306 拓展为 true（`plugins/packages/buildin/12306.ts:10`）。
- `enabled_by_default` — 目录包是否默认启用，角色卡为 true（`plugins/packages/buildin/character_cards/manifest.json:17`）。
- `main` — 目录包主入口，角色卡为 `dist/main.js`（`plugins/packages/buildin/character_cards/manifest.json:6`）。
- `subpackages` — 子包列表，角色卡含 `character_memory` 子包（`plugins/packages/buildin/character_cards/manifest.json:20`）。
- `wasm_modules` — 角色卡声明了 `usearch` 模块（`plugins/packages/buildin/character_cards/manifest.json:43`）。
- `public_api` — 角色卡公开 API 的路径是 `src/api.ts`（`plugins/packages/buildin/character_cards/manifest.json:7`）。
- `VectorIndex` — 角色卡记忆检索的向量索引类（`plugins/packages/buildin/character_cards/src/search/usearch.ts:3`）。
- `defaultEnabledByDefault` — 清单省略默认启用字段时的默认值来源，返回 true（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2593`）。
- `bool_field` — 单文件包解析时字段缺失返回 `false`（`core/crates/plugin/sdk/src/JsPackageLoader.rs:160`）。
- 数据流向：buildin 源码 → 打包进内置插件资产（`plugins/packages/buildin/README.md:3`）。

## 核心机制

### 目录清单

变更审阅（`com.operit.change_review`）— 回复下方列出 AI 改过的文件，可一键撤销，也能在工作区里逐行对比；默认启用（`plugins/packages/buildin/change_review/manifest.json:3`）（`plugins/packages/buildin/change_review/manifest.json:13`）。
角色卡（`com.operit.character_cards`）— 创建和编辑 AI 角色，或让多个角色一起群聊；每个角色都有自己的记忆库；默认启用（`plugins/packages/buildin/character_cards/manifest.json:3`）（`plugins/packages/buildin/character_cards/manifest.json:17`）（`plugins/packages/buildin/character_cards/manifest.json:13`）。
日常生活工具包（`com.operit.daily_life`）— 让 AI 帮你查天气、设提醒、看日期和设备状态，还能截屏；默认启用（`plugins/packages/buildin/daily_life/manifest.json:3`）（`plugins/packages/buildin/daily_life/manifest.json:13`）。
目标模式（`com.operit.goal_mode_bundle`）— 给对话定一个目标，AI 会持续推进直到真正完成，状态显示在输入框上方；默认启用（`plugins/packages/buildin/goal_mode/manifest.json:3`）（`plugins/packages/buildin/goal_mode/manifest.json:16`）。
消息翻译（`com.operit.message_translation`）— 长按任意聊天消息就能翻译，原文和译文对照显示；默认启用（`plugins/packages/buildin/message_translation/manifest.json:3`）（`plugins/packages/buildin/message_translation/manifest.json:16`）。
计划模式（`com.operit.plan_mode_bundle`）— 开启后 AI 先和你商量好计划、不改动文件，你确认后一键开始实施；默认启用（`plugins/packages/buildin/plan_mode/manifest.json:3`）（`plugins/packages/buildin/plan_mode/manifest.json:16`）。
工作流（`com.operit.workflow`）— 用可视化节点搭建自动化流程：条件分支、调用工具、定时运行，每次执行都有记录；默认禁用（`plugins/packages/buildin/workflow/manifest.json:3`）（`plugins/packages/buildin/workflow/manifest.json:17`）。
12306 拓展（`12306_ticket`）— 提供12306火车票信息查询功能，包括余票、中转、经停站等；默认启用（`plugins/packages/buildin/12306.ts:3`）（`plugins/packages/buildin/12306.ts:10`）。
AI 相互对话（ai_chat）— 调用AI模型API实现AI之间智能对话互动（`plugins/packages/buildin/ai_chat.ts:3`）（`plugins/packages/buildin/ai_chat.ts:10`）。
Browser 自动化操作（browser）— 严格对齐 Playwright MCP 默认 browser 工具面的浏览器自动化工具集；默认启用（`plugins/packages/buildin/browser.ts:12`）（`plugins/packages/buildin/browser.ts:3`）。
Crossref 学术文献查询（crossref）— Crossref 学术文献查询工具，提供 DOI 查询、关键词搜索、作者搜索等功能，帮助用户查找和获取学术文章元数据；默认启用（`plugins/packages/buildin/crossref.ts:13`）（`plugins/packages/buildin/crossref.ts:3`）。
增强文件工具（`extended_file_tools`）— 基于 v2 VFS 的增强文件工具：检查存在、压缩、解压、打开和分享。移动、复制和文件信息由内置文件工具提供；默认启用（`plugins/packages/buildin/extended_file_tools.ts:6`）。
Operit 平台编辑器（operit_editor）— 通过真实的 core command 执行入口管理 Operit2 的包、Skill、MCP、模型、偏好设置、聊天与工作区，返回实际执行结果；默认禁用（`plugins/packages/buildin/operit_editor.ts:12`）（`plugins/packages/buildin/operit_editor.ts:3`）。
超级管理员（super_admin）— 提供终端命令和会话控制；默认启用（`plugins/packages/buildin/super_admin.ts:51`）（`plugins/packages/buildin/super_admin.ts:44`）。
系统工具（`system_tools`）— 提供系统设置、应用管理、通知、位置、设备信息和蓝牙操作；默认启用（`plugins/packages/buildin/system_tools.ts:6`）。
时间（`time`）— 提供时间相关功能。实际上，激活本包的同时已经能够获取时间了；默认启用（`plugins/packages/buildin/time.ts:13`）（`plugins/packages/buildin/time.ts:3`）。

### 默认启用

合计（磁盘清点）：13 个声明默认启用，2 个声明默认禁用，1 个未声明。
AI 相互对话的 METADATA 未声明 enabledByDefault 字段（`plugins/packages/buildin/ai_chat.ts:13`）。
AI 相互对话声明了 env：`AI_API_BASE_URL`、`AI_API_KEY`、`AI_MODEL_NAME`（`plugins/packages/buildin/ai_chat.ts:13`）。
解析单文件包 METADATA 时 `enabled_by_default` 取 `enabledByDefault` 与 `enabled_by_default` 两个字段的或（`core/crates/plugin/sdk/src/JsPackageLoader.rs:98`）。
`bool_field` 在字段缺失时返回 `false`（`core/crates/plugin/sdk/src/JsPackageLoader.rs:160`）。
因此 AI 相互对话按这段解析代码不默认启用（`core/crates/plugin/sdk/src/JsPackageLoader.rs:98`）。
清单省略 `enabled_by_default` 时按 `defaultEnabledByDefault` 取 true（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:668`）。

### 单文件包与目录包的区别

单文件包是一个 .ts 文件，文件内含 `METADATA` 注释块，多在文件顶部，super_admin.ts:42 例外（`plugins/packages/buildin/12306.ts:1`）（`plugins/packages/buildin/super_admin.ts:42`）。
解析器用正则全文查找 `extract_metadata`（`core/crates/plugin/sdk/src/JsPackageLoader.rs:124`），位置不影响解析。
单文件包没有 manifest.json，元数据只在 `METADATA` 注释块里（`plugins/packages/buildin/12306.ts:1`）。
单文件包位于 buildin 根目录 tsconfig 的 include 范围内，其 include 包含根目录 `*.ts`（`plugins/packages/buildin/tsconfig.json:30`）。
根 tsconfig 的 outDir 是 `../../.out/buildin`（`plugins/packages/buildin/tsconfig.json:8`）。
目录包以 manifest.json 声明 `toolpkg_id` 与 `main` 入口（`plugins/packages/buildin/character_cards/manifest.json:6`）。
目录包清单声明 `main` 为 `dist/main.js`，磁盘上存在该文件（`plugins/packages/buildin/character_cards/manifest.json:6`）。
目录包自带 tsconfig，以 change_review 为例其 include 为 `src/**/*.ts`（`plugins/packages/buildin/change_review/tsconfig.json:13`）。
目录包可带 `subpackages`，角色卡含 `character_memory` 子包，入口是 `dist/tools.js`（`plugins/packages/buildin/character_cards/manifest.json:20`）。
目录包可声明 `wasm_modules`（`plugins/packages/buildin/character_cards/manifest.json:41`）。
目录包的 `resources` 声明资源文件（`plugins/packages/buildin/character_cards/manifest.json:24`）。
日常生活工具包含 `daily_life` 子包，入口是 `dist/tools.js`（`plugins/packages/buildin/daily_life/manifest.json:14`）。
计划模式含 `plan_mode_tools` 子包，入口是 `dist/packages/plan_mode_tools.js`（`plugins/packages/buildin/plan_mode/manifest.json:19`）。
工作流含 `workflow` 子包，入口是 `dist/tools.js`（`plugins/packages/buildin/workflow/manifest.json:20`）。
消息翻译的 `subpackages` 为空数组（`plugins/packages/buildin/message_translation/manifest.json:17`）。
工作流的 `workflow_templates` 与 `workspace_templates` 均为空数组（`plugins/packages/buildin/workflow/manifest.json:36`）。
工作流的资源含 `workflow_web`，路径是 `resources/workflow.html`（`plugins/packages/buildin/workflow/manifest.json:31`）。
清单字段的完整说明见 [[plugin-manifest|清单 manifest 与安装作用域]]。

### character_cards 为什么这么大

角色卡的 src/ 共 97 个文件，其中 .ts 文件 94 个、合计 15212 行（`plugins/packages/buildin/character_cards/src/main.ts:1`）。
对照：工作流的 src/ 共 14 个 .ts 文件、合计 2966 行（`plugins/packages/buildin/workflow/src/main.ts:1`）。
角色卡另有 web/ 前端 54 个文件，其中 .ts 文件 51 个、合计 2718 行（`plugins/packages/buildin/character_cards/web/app.ts:1`）。
角色卡的记忆查询结果类型是 `MemoryQueryResult`（`plugins/packages/buildin/character_cards/src/api.ts:222`）。
角色卡的聊天存储类 `CharacterChatStore` 定义在存储层（`plugins/packages/buildin/character_cards/src/storage/chats.ts:10`）。
角色卡有群聊执行代码，executor.ts 引用 `ToolPkg` 类型（`plugins/packages/buildin/character_cards/src/group-execution/executor.ts:1`）。
角色卡有向量检索代码，`VectorIndex` 基于 `ToolPkg.WasmInstance`（`plugins/packages/buildin/character_cards/src/search/usearch.ts:3`）。
角色卡的 `usearch` 模块以 C++ 实现，`source_language` 为 cpp（`plugins/packages/buildin/character_cards/manifest.json:45`）。
角色卡的 wasm 模块导出包括 `index_create`、`index_add_batch`、`index_search`（`plugins/packages/buildin/character_cards/manifest.json:54`）。
角色卡的 `character_memory` 子包入口是 `dist/tools.js`（`plugins/packages/buildin/character_cards/manifest.json:20`）。
角色卡的资源含 `character_memory_html` 与 `character_default_avatar`（`plugins/packages/buildin/character_cards/manifest.json:32`）。
角色卡的公开 API 在 `src/api.ts`（`plugins/packages/buildin/character_cards/manifest.json:7`）。
注：本页只回答目录级问题，character_cards 的内部实现另立页深挖。

## 关键符号

- `toolpkg_id` — 包唯一标识，角色卡为 `com.operit.character_cards`（`plugins/packages/buildin/character_cards/manifest.json:3`）。
- `main` — 目录包主入口（`plugins/packages/buildin/character_cards/manifest.json:6`）。
- `enabled_by_default` — 目录包是否默认启用（`plugins/packages/buildin/character_cards/manifest.json:17`）。
- `subpackages` — 子包列表（`plugins/packages/buildin/character_cards/manifest.json:18`）。
- `resources` — 资源声明（`plugins/packages/buildin/character_cards/manifest.json:24`）。
- `wasm_modules` — WASM 模块声明（`plugins/packages/buildin/character_cards/manifest.json:41`）。
- `public_api` — 公开 API 路径（`plugins/packages/buildin/character_cards/manifest.json:7`）。
- `METADATA` — 单文件包元数据注释块（`plugins/packages/buildin/12306.ts:1`）。
- `enabledByDefault` — 单文件包是否默认启用（`plugins/packages/buildin/12306.ts:10`）。
- `VectorIndex` — 向量索引类（`plugins/packages/buildin/character_cards/src/search/usearch.ts:3`）。
- `MemoryQueryResult` — 记忆查询结果类型（`plugins/packages/buildin/character_cards/src/api.ts:222`）。
- `CharacterChatStore` — 角色聊天存储（`plugins/packages/buildin/character_cards/src/storage/chats.ts:10`）。
- `defaultEnabledByDefault` — 清单默认启用值来源（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2593`）。
- `bool_field` — 单文件包布尔字段解析（`core/crates/plugin/sdk/src/JsPackageLoader.rs:155`）。
- `outDir` — 根 tsconfig 输出目录（`plugins/packages/buildin/tsconfig.json:8`）。
- `character_memory` — 角色卡记忆子包（`plugins/packages/buildin/character_cards/manifest.json:20`）。
- `usearch` — 向量检索 WASM 模块（`plugins/packages/buildin/character_cards/manifest.json:43`）。
- `index_search` — 向量检索导出函数（`plugins/packages/buildin/character_cards/manifest.json:54`）。
- `get_time` — 时间包工具（`plugins/packages/buildin/time.ts:17`）。
- `chat_completion` — AI 相互对话工具（`plugins/packages/buildin/ai_chat.ts:16`）。
- `workflow_templates` — 工作流模板列表（`plugins/packages/buildin/workflow/manifest.json:36`）。
- `plan_mode_tools` — 计划模式子包（`plugins/packages/buildin/plan_mode/manifest.json:19`）。
- `daily_life` — 日常生活工具子包（`plugins/packages/buildin/daily_life/manifest.json:14`）。

## 调用链

1. ToolPkg 源码放在 plugins/packages/buildin/（`plugins/packages/buildin/README.md:3`）。
2. 源码被打包进 Operit2 内置插件资产（`plugins/packages/buildin/README.md:3`）。
3. 目录包清单声明 `main` 为 `dist/main.js`（`plugins/packages/buildin/character_cards/manifest.json:6`）。
4. 目录包的子包从 `entry` 入口加载，角色卡记忆子包入口是 `dist/tools.js`（`plugins/packages/buildin/character_cards/manifest.json:20`）。
5. 根 tsconfig 声明 `outDir` 为 `../../.out/buildin`（`plugins/packages/buildin/tsconfig.json:8`）。
6. 角色卡记忆检索经 `VectorIndex` 调 WASM 实例（`plugins/packages/buildin/character_cards/src/search/usearch.ts:3`）。
7. 清单省略 `enabled_by_default` 时按 `defaultEnabledByDefault` 取 true（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:668`）。

## 来源

Seed 文件（100% 读完）：
- plugins/packages/buildin/README.md（3 行）
- plugins/packages/buildin/character_cards/manifest.json（66 行）
- plugins/packages/buildin/workflow/manifest.json（38 行）

目录核对时读过的文件：
- 7 个目录包的 manifest.json：change_review、character_cards、daily_life、goal_mode、message_translation、plan_mode、workflow
- 9 个单文件 .ts 的 METADATA 块：12306.ts、ai_chat.ts、browser.ts、crossref.ts、extended_file_tools.ts、operit_editor.ts、super_admin.ts、system_tools.ts、time.ts
- plugins/packages/buildin/tsconfig.json、plugins/packages/buildin/change_review/tsconfig.json
- core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs（defaultEnabledByDefault 相关行）、core/crates/plugin/sdk/src/JsPackageLoader.rs（parse_metadata 与 bool_field 相关行）
- character_cards 体量核对：src/main.ts、src/memory-recall.ts、src/storage/database.ts、src/group-execution/executor.ts、src/search/usearch.ts、web/app.ts、vendor/usearch/index.cpp、workflow/src/main.ts；符号定义核对：src/api.ts、src/storage/chats.ts

磁盘清点方法见 tracking/read-batch-06/plugin-catalog-buildin.txt。

相关页：[[plugin-toolpkg-overview|ToolPkg 2.0.0 总览]]、[[plugin-manifest|清单 manifest 与安装作用域]]。
