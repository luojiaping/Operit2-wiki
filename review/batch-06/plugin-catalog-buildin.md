---
title: 内置插件目录
module: plugins
platforms: [all]
sources: [plugins/packages/buildin/README.md, plugins/packages/buildin/character_cards/manifest.json, plugins/packages/buildin/workflow/manifest.json, plugins/packages/buildin/tsconfig.json, plugins/packages/buildin/change_review/manifest.json, plugins/packages/buildin/change_review/tsconfig.json, plugins/packages/buildin/daily_life/manifest.json, plugins/packages/buildin/goal_mode/manifest.json, plugins/packages/buildin/message_translation/manifest.json, plugins/packages/buildin/plan_mode/manifest.json, plugins/packages/buildin/ai_chat.ts, plugins/packages/buildin/automatic_ui_base/manifest.json, plugins/packages/buildin/automatic_ui_base/src/tools.ts, plugins/packages/buildin/browser.ts, plugins/packages/buildin/crossref.ts, plugins/packages/buildin/extended_file_tools.ts, plugins/packages/buildin/operit_editor.ts, plugins/packages/buildin/super_admin/manifest.json, plugins/packages/buildin/system_tools.ts, plugins/packages/buildin/time.ts, plugins/packages/buildin/character_cards/src/main.ts, plugins/packages/buildin/character_cards/src/memory-recall.ts, plugins/packages/buildin/character_cards/src/storage/database.ts, plugins/packages/buildin/character_cards/src/group-execution/executor.ts, plugins/packages/buildin/character_cards/src/search/usearch.ts, plugins/packages/buildin/character_cards/web/app.ts, plugins/packages/buildin/character_cards/vendor/usearch/index.cpp, plugins/packages/buildin/workflow/src/main.ts, core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs, core/crates/plugin/sdk/src/JsPackageLoader.rs, plugins/packages/buildin/docs_editor/manifest.json]
date: 2026-11-11
---

## 概述

内置插件是 plugins/packages/buildin/ 下的 ToolPkg 源码，会被打包进 Operit2 内置插件资产（`plugins/packages/buildin/README.md:3`）。
磁盘清点：buildin 共 20 项，17 个插件加 README.md、tsconfig.json 与 resources/ 目录（仅含 character-memory.html，未见代码引用）。
17 个插件分两类：7 个单文件 .ts 包与 10 个目录包（磁盘清点，方法见 tracking/read-batch-06/plugin-catalog-buildin.txt）。

## AI 速览

- manifest.json — 目录包的清单，声明 `toolpkg_id` 与 `main` 入口（`plugins/packages/buildin/character_cards/manifest.json:6`）。
- `METADATA` — 单文件包文件内含的元数据注释块，多在文件顶部（`plugins/packages/buildin/ai_chat.ts:1`）。
- `enabledByDefault` — 单文件包是否默认启用，browser 为 true（`plugins/packages/buildin/browser.ts:13`）。
- `enabled_by_default` — 目录包是否默认启用，角色卡为 true（`plugins/packages/buildin/character_cards/manifest.json:17`）。
- `main` — 目录包主入口，角色卡为 `dist/main.js`（`plugins/packages/buildin/character_cards/manifest.json:6`）。
- `subpackages` — 子包列表，角色卡含 `character_memory` 子包（`plugins/packages/buildin/character_cards/manifest.json:20`）。
- `wasm_modules` — 角色卡声明了 `usearch` 模块（`plugins/packages/buildin/character_cards/manifest.json:43`）。
- `public_api` — 角色卡公开 API 的路径是 `src/api.ts`（`plugins/packages/buildin/character_cards/manifest.json:7`）。
- `VectorIndex` — 角色卡记忆检索的向量索引类（`plugins/packages/buildin/character_cards/src/search/usearch.ts:3`）。
- `defaultEnabledByDefault` — 清单省略默认启用字段时的默认值来源，返回 true（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2834`）。
- `bool_field` — 单文件包解析时字段缺失返回 `false`（`core/crates/plugin/sdk/src/JsPackageLoader.rs:187`）（`core/crates/plugin/sdk/src/JsPackageLoader.rs:196`）。
- 数据流向：buildin 源码 → 打包进内置插件资产（`plugins/packages/buildin/README.md:3`）。

## 核心机制

### 目录清单

变更审阅（`com.operit.change_review`）— 回复下方列出 AI 改过的文件，可一键撤销，也能在工作区里逐行对比；默认启用（`plugins/packages/buildin/change_review/manifest.json:3`）（`plugins/packages/buildin/change_review/manifest.json:13`）。
角色卡（`com.operit.character_cards`）— 创建和编辑 AI 角色，或让多个角色一起群聊；每个角色都有自己的记忆库；默认启用（`plugins/packages/buildin/character_cards/manifest.json:3`）（`plugins/packages/buildin/character_cards/manifest.json:17`）（`plugins/packages/buildin/character_cards/manifest.json:13`）。
日常生活工具包（`com.operit.daily_life`）— 让 AI 帮你查天气、设提醒、看日期和设备状态，还能截屏；默认启用（`plugins/packages/buildin/daily_life/manifest.json:3`）（`plugins/packages/buildin/daily_life/manifest.json:13`）。
Office 文档（`com.operit.office`）— 离线打开、编辑及保存 DOCX、PPTX 和 PDF；默认禁用（`plugins/packages/buildin/docs_editor/manifest.json:3`）（`plugins/packages/buildin/docs_editor/manifest.json:4`）（`plugins/packages/buildin/docs_editor/manifest.json:9`）。
目标模式（`com.operit.goal_mode_bundle`）— 给对话定一个目标，AI 会持续推进直到真正完成，状态显示在输入框上方；默认启用（`plugins/packages/buildin/goal_mode/manifest.json:3`）（`plugins/packages/buildin/goal_mode/manifest.json:16`）。
消息翻译（`com.operit.message_translation`）— 长按任意聊天消息就能翻译，原文和译文对照显示；默认启用（`plugins/packages/buildin/message_translation/manifest.json:3`）（`plugins/packages/buildin/message_translation/manifest.json:16`）。
计划模式（`com.operit.plan_mode_bundle`）— 开启后 AI 先和你商量好计划、不改动文件，你确认后一键开始实施；默认启用（`plugins/packages/buildin/plan_mode/manifest.json:3`）（`plugins/packages/buildin/plan_mode/manifest.json:16`）。
工作流（`com.operit.workflow`）— 用可视化节点搭建自动化流程：条件分支、调用工具、定时运行，每次执行都有记录；默认禁用（`plugins/packages/buildin/workflow/manifest.json:3`）（`plugins/packages/buildin/workflow/manifest.json:17`）。
自动化基础工具（Automatic_ui_base）— 操作设备系统界面和其他应用的基础 UI 自动化工具。默认关闭；需要平台提供整机自动化权限（`plugins/packages/buildin/automatic_ui_base/src/tools.ts:10`）；包默认禁用（`plugins/packages/buildin/automatic_ui_base/manifest.json:12`）。
AI 相互对话（ai_chat）— 调用AI模型API实现AI之间智能对话互动（`plugins/packages/buildin/ai_chat.ts:4`）（`plugins/packages/buildin/ai_chat.ts:11`）。
Browser 自动化操作（browser）— 严格对齐 Playwright MCP 默认 browser 工具面的浏览器自动化工具集；默认启用（`plugins/packages/buildin/browser.ts:13`）（`plugins/packages/buildin/browser.ts:4`）。
Crossref 学术文献查询（crossref）— Crossref 学术文献查询工具，提供 DOI 查询、关键词搜索、作者搜索等功能，帮助用户查找和获取学术文章元数据；默认启用（`plugins/packages/buildin/crossref.ts:14`）（`plugins/packages/buildin/crossref.ts:4`）。
增强文件工具（`extended_file_tools`）— 基于 v2 VFS 的增强文件工具：检查存在、压缩、解压、打开和分享。移动、复制和文件信息由内置文件工具提供；默认启用（`plugins/packages/buildin/extended_file_tools.ts:7`）。
Operit 平台编辑器（operit_editor）— 通过真实的 core command 执行入口管理 Operit2 的包、Skill、MCP、模型、偏好设置、聊天与工作区，返回实际执行结果；默认启用（`plugins/packages/buildin/operit_editor.ts:13`）（`plugins/packages/buildin/operit_editor.ts:4`）。
超级管理员（`com.operit.super_admin`）— 独立命令执行与持久交互终端，命令结束后闲置 10 分钟自动清理，交互终端须显式关闭；默认启用（`plugins/packages/buildin/super_admin/manifest.json:3`）（`plugins/packages/buildin/super_admin/manifest.json:9`）（`plugins/packages/buildin/super_admin/manifest.json:12`）。
系统工具（`system_tools`）— 提供系统设置、应用管理、通知、位置、设备信息和蓝牙操作；默认启用（`plugins/packages/buildin/system_tools.ts:7`）。
时间（`time`）— 提供时间相关功能。实际上，激活本包的同时已经能够获取时间了；默认启用（`plugins/packages/buildin/time.ts:14`）（`plugins/packages/buildin/time.ts:4`）。

### 默认启用

合计（磁盘清点）：13 个声明默认启用，3 个声明默认禁用，1 个未声明。
AI 相互对话的 METADATA 未声明 enabledByDefault 字段（`plugins/packages/buildin/ai_chat.ts:14`）。
AI 相互对话声明了 env：`AI_API_BASE_URL`、`AI_API_KEY`、`AI_MODEL_NAME`（`plugins/packages/buildin/ai_chat.ts:14`）。
解析单文件包 METADATA 时 `enabled_by_default` 取 `enabledByDefault` 与 `enabled_by_default` 两个字段的或（`core/crates/plugin/sdk/src/JsPackageLoader.rs:109`）。
`bool_field` 在字段缺失时返回 `false`（`core/crates/plugin/sdk/src/JsPackageLoader.rs:187`）（`core/crates/plugin/sdk/src/JsPackageLoader.rs:196`）。
因此 AI 相互对话按这段解析代码不默认启用（`core/crates/plugin/sdk/src/JsPackageLoader.rs:109`）。
清单省略 `enabled_by_default` 时按 `defaultEnabledByDefault` 取 true（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:714`）。

### 单文件包与目录包的区别

单文件包是一个 .ts 文件，文件内含 `METADATA` 注释块，多在文件顶部（`plugins/packages/buildin/ai_chat.ts:1`）。
解析器用正则全文查找 `extract_metadata`（`core/crates/plugin/sdk/src/JsPackageLoader.rs:156`），位置不影响解析。
单文件包没有 manifest.json，元数据只在 `METADATA` 注释块里（`plugins/packages/buildin/ai_chat.ts:1`）。
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

角色卡的 src/ 共 107 个文件，其中 .ts 文件 104 个、合计 16518 行（`plugins/packages/buildin/character_cards/src/main.ts:1`）。
对照：工作流的 src/ 共 14 个 .ts 文件、合计 2967 行（`plugins/packages/buildin/workflow/src/main.ts:1`）。
角色卡另有 web/ 前端 3 个文件，其中 .ts 文件 2 个、合计 283 行（`plugins/packages/buildin/character_cards/web/app.ts:1`）。
注：角色卡 src/ 的统计按上游 0f08fd43 清点，2026-11-15 对 ff5373fb6 复核无变化（102 个文件、99 个 .ts、15830 行）；web/ 按 ff5373fb6 重清点为 3 个文件、2 个 .ts、229 行；2026-11-18 对 753366ff4 复核：src/ 仍 102 个文件、99 个 .ts、合计 15865 行，web/ 仍 3 个文件、2 个 .ts、合计 236 行；行数只计 .ts 文件（src/ 另有 3 个 .json 文件不计）；2026-11-19 对 f9b7555 复核：src/ 仍 102 个文件、99 个 .ts、合计 15925 行，web/ 仍 3 个文件、2 个 .ts、合计 236 行。
角色卡的记忆查询结果类型是 `MemoryQueryResult`（`plugins/packages/buildin/character_cards/src/api.ts:256`）。
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
- `METADATA` — 单文件包元数据注释块（`plugins/packages/buildin/ai_chat.ts:1`）。
- `enabledByDefault` — 单文件包是否默认启用（`plugins/packages/buildin/browser.ts:13`）。
- `VectorIndex` — 向量索引类（`plugins/packages/buildin/character_cards/src/search/usearch.ts:3`）。
- `MemoryQueryResult` — 记忆查询结果类型（`plugins/packages/buildin/character_cards/src/api.ts:256`）。
- `CharacterChatStore` — 角色聊天存储（`plugins/packages/buildin/character_cards/src/storage/chats.ts:10`）。
- `defaultEnabledByDefault` — 清单默认启用值来源（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:2834`）。
- `bool_field` — 单文件包布尔字段解析（`core/crates/plugin/sdk/src/JsPackageLoader.rs:187`）。
- `outDir` — 根 tsconfig 输出目录（`plugins/packages/buildin/tsconfig.json:8`）。
- `character_memory` — 角色卡记忆子包（`plugins/packages/buildin/character_cards/manifest.json:20`）。
- `usearch` — 向量检索 WASM 模块（`plugins/packages/buildin/character_cards/manifest.json:43`）。
- `index_search` — 向量检索导出函数（`plugins/packages/buildin/character_cards/manifest.json:54`）。
- `get_time` — 时间包工具（`plugins/packages/buildin/time.ts:18`）。
- `chat_completion` — AI 相互对话工具（`plugins/packages/buildin/ai_chat.ts:17`）。
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
7. 清单省略 `enabled_by_default` 时按 `defaultEnabledByDefault` 取 true（`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:714`）。

## 来源

Seed 文件（100% 读完）：
- plugins/packages/buildin/README.md（11 行）
- plugins/packages/buildin/character_cards/manifest.json（66 行）
- plugins/packages/buildin/workflow/manifest.json（38 行）

目录核对时读过的文件：
- 10 个目录包的 manifest.json：automatic_ui_base、change_review、character_cards、daily_life、docs_editor、goal_mode、message_translation、plan_mode、super_admin、workflow
- 7 个单文件 .ts 的 METADATA 块：ai_chat.ts、browser.ts、crossref.ts、extended_file_tools.ts、operit_editor.ts、system_tools.ts、time.ts
- plugins/packages/buildin/tsconfig.json、plugins/packages/buildin/change_review/tsconfig.json
- core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs（defaultEnabledByDefault 相关行）、core/crates/plugin/sdk/src/JsPackageLoader.rs（parse_metadata 与 bool_field 相关行）
- character_cards 体量核对：src/main.ts、src/memory-recall.ts、src/storage/database.ts、src/group-execution/executor.ts、src/search/usearch.ts、web/app.ts、vendor/usearch/index.cpp、workflow/src/main.ts；符号定义核对：src/api.ts、src/storage/chats.ts

磁盘清点方法见 tracking/read-batch-06/plugin-catalog-buildin.txt。
2026-11-15 基线前移至 ff5373fb6：12306.ts 已删除（buildin 内无此文件），新增 automatic_ui_base.ts（迁移自 Operit 1 的 Automatic_ui_base 设备自动化包）；operit_editor.ts 的 enabledByDefault 由 false 改为 true；character_cards 的 web/ 由 54 个文件缩减为 3 个；ToolPkgParser.rs 相关行号重映射（:668→:680、:2593→:2752）。
2026-11-18 基线前移至 753366ff4：character_cards 的 version 由 0.2.0 改为 0.2.2；src/ 行数 15830→15865、web/ 行数 229→236（均按 find + wc -l 重清点）；api.ts 新增一行致 MemoryQueryResult 行号 222→223；database.ts 的 readMemorySettings 改由 normalizeMemorySettings 处理设置（本页无相关事实，未立新事实）。
2026-11-19 基线前移至 f9b7555：character_cards 的 version 由 0.2.2 改为 0.2.3；src/ 行数 15865→15925（仍 102 个文件、99 个 .ts，按 find + wc -l 重清点；ui-contributions.ts +61、model-binding.ts +13、chat-storage.ts +5、domain.ts -17、public-api.ts -2），web/ 行数仍 236、workflow src/ 仍 2966 行；goal_mode 的 manifest 新增 public_api 字段、MCPLocalServer 的 ServerConfig 新增 bearerToken、ToolPkgManifest 新增 optional_requires、导航 surface 新增 workspace_file、manifest.license 指向缺失文件时不再导致加载失败（以上均未立新事实）。
2026-11-19 基线前移至 6192d22e3：character_cards 的 version 由 0.2.3 改为 0.2.5；src/ 行数 15925→15971、web/ 行数 236→283、workflow src/ 行数 2966→2967（均按 find + wc -l 重清点，文件数不变）；9 个单文件 .ts 包的 METADATA 各新增 api_version 2.0.0 一行，行号 +1；JsPackageLoader 新增 api_version 解析（省略时默认 1.0.0 并校验）与子包继承容器 api_version（ToolPkgParser 子包解析改走 parse_metadata_with_default_api_version），本页无相关事实、未立新事实。
2026-11-21 基线前移至 7fdb667：automatic_ui_base.ts 改为目录包 automatic_ui_base/（子包 src/tools.ts 的 enabledByDefault 由 false 改为 true，包级 manifest 的 enabled_by_default 为 false；README 同步改写）；单文件包 9→8、目录包 7→8，插件总数仍 16；character_cards 的 version 由 0.2.5 改为 0.2.6，src/ 行数 15971→16206（105 个文件、102 个 .ts，新增 group-avatar.ts、group-avatar-image.ts、storage/avatars.ts，按 find + wc -l 重清点），web/ 仍 283 行、workflow src/ 仍 2967 行。
2026-11-21 基线前移至 2dafe6b：新增目录包 docs_editor（Office 文档编辑器，com.operit.office，0.1.5，默认禁用）；单文件包仍 8、目录包 8→9，插件总数 16→17；character_cards 的 version 由 0.2.6 改为 0.2.7，src/ 行数 16206→16207（105 个文件、102 个 .ts，按 find + wc -l 重清点），web/ 仍 283 行、workflow src/ 仍 2967 行。
2026-11-25 基线前移至 62dacc0：super_admin.ts 改为目录包 super_admin/（toolpkg_id com.operit.super_admin，version 1.0.0，manifest 的 enabled_by_default 为 true，新增闲置 10 分钟自动关闭会话）；单文件包 8→7、目录包 9→10，插件总数仍 17；character_cards 的 version 由 0.2.9 改为 0.2.10，src/ 行数 16364→16297（仍 106 个文件、103 个 .ts，按 find + wc -l 重清点；api.ts +17、search/state.ts +18、storage/memory-repository.ts +13、memory-search.ts +8、public-api.ts +6、model.ts +5、domain.ts +1、runtime-tools/memory.ts -66、search/text-index.ts -39、ui-memory-workspace.ts -17、operations.ts -8、canonical.ts -3、search/chunks.ts -2），web/ 仍 283 行、workflow src/ 仍 2967 行；api.ts 新增 MemoryPageOptions、MemoryLinkView，memory.graph/memory.list 支持分页、新增 memory.links 接口、memory.chunks 新增 start 参数（以上均未立新事实）；README.md 新增 super_admin 段落致 automatic_ui_base 段落下移（行号 5→9）。
2026-11-25 基线前移至 f020fc4：character_cards 的 version 由 0.2.10 改为 0.2.12，src/ 行数 16297→16441（107 个文件、104 个 .ts，按 find + wc -l 重清点；新增 group-execution/public-turn.ts 102 行、api.ts +23、public-api.ts +14、native-transport.ts +5），web/ 仍 283 行、workflow src/ 仍 2967 行；api.ts 新增 ChatPresentation、ChatGroupTurnRequest/Reply/Status，新增 chat.presentation 与 chat.groupTurn 公开 API（以上均未立新事实）。
2026-11-25 基线前移至 d0f7619：character_cards 的 version 由 0.2.12 改为 0.2.13；src/ 行数 16441→16442（仍 107 个文件、104 个 .ts，按 find + wc -l 重清点；public-api.ts +1，新增 `export { groupTurnApi }` 重导出），web/ 仍 283 行、workflow src/ 仍 2967 行；ai_chat_presentation（外部包，本页未收录）的 version 由 0.2.0 改为 0.2.1，src/ui.ts 更名为 src/settings.ui.ts（以上均未立新事实）。
2026-11-27 基线前移至 7a79245：super_admin 的 version 由 1.0.0 改为 1.0.1，中文描述改写为独立命令执行与持久交互终端（命令结束后闲置 10 分钟自动清理，交互终端须显式关闭）；character_cards 的 src/ 行数 16442→16518（仍 107 个文件、104 个 .ts，按 find + wc -l 重清点；memory-jobs/analysis.ts +27、group-execution/executor.ts +22、service-runtime.ts +20、domain.ts +11、storage/chats.ts +10、group-execution/hooks.ts +9、chat-lifecycle.ts +9、configuration-reads.ts +2、ui-entity-native.ts +2、storage/database.ts +1、operations.ts -25、repository.ts -12），web/ 仍 283 行、workflow src/ 仍 2967 行；browser.ts 的 handle_dialog 更名为 dialog、run_code 改为异步 JavaScript 函数体、新增 take_screenshot，character_cards 的 executor.ts 的 submit 改为仅替换已取消 settled 序列并新增 stopForHistoryTruncate，database.ts 新增 deleteSelections 调用，automatic_ui_base 的 focus_window 描述新增 Android 虚拟屏幕句（以上均未立新事实）。

相关页：[[plugin-toolpkg-overview|ToolPkg 2.0.0 总览]]、[[plugin-manifest|清单 manifest 与安装作用域]]。
