---
title: PackageBuilder（随软件携带的插件开发 Skill）
module: plugins
platforms: [all]
sources: [5]
date: 2026-11-11
---

## 概述

- `PackageBuilder` 是当前 Operit 随软件携带的插件开发 Skill。`plugins/skills/external/PackageBuilder/SKILL.md:8`
- 文档声明：`PackageBuilder` 的类型和示例来自当前版本内置资源，不从云端拉取其他版本。`plugins/skills/external/PackageBuilder/SKILL.md:8`
- 文档声明：`PackageBuilder` 的描述是使用当前 Operit 随软件携带的类型定义和示例开发、打包、安装与测试插件包，并通过现有 host API 核对环境与路径。`plugins/skills/external/PackageBuilder/SKILL.md:3`
- 磁盘实况：PackageBuilder 磁盘目录只有 SKILL.md 与 skill.include.json 两个文件；SKILL.md 里的树状图是安装后呈现的逻辑树，其余内容由 skill.include.json 声明映射、随包还原。`plugins/skills/external/PackageBuilder/skill.include.json:4` `plugins/skills/external/PackageBuilder/SKILL.md:40`
- 文档声明：安装 Skill 时从随软件携带的插件归档中还原示例已使用的资源，保留完整的相对路径和原始文件；示例源码不要求对应插件已安装或启用。`plugins/skills/external/PackageBuilder/SKILL.md:40`
- 文档声明：CLI 和 App 使用同一套资源与安装逻辑。`plugins/skills/external/PackageBuilder/SKILL.md:40`
- 文档声明：包管理创作入口只准备 Skill 和包，并把需求填入聊天草稿；用户发送后才开始开发；它不自动生成、构建、安装或发布插件。`plugins/skills/external/PackageBuilder/SKILL.md:53`
- 文档声明：`ToolPkg` 是 Operit 项目中用于打包和分发工具包的标准格式；它把多个相关的工具脚本、资源文件和 UI 模块打包成一个单一的、易于分发和管理的文件。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:7`
- 文档声明：`.toolpkg` 文件本质上是一个标准的 ZIP 压缩包。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:11`
- 文档声明：Operit2 的 ToolPkg API 支持版本为 `2.0.0`；对 `1.0.0` 和 `1.0.1` 的加载支持并不完整；Operit1 完整支持 `1.0.0` 和 `1.0.1`，这两个版本主要面向 Android，是旧版 API 形式。`plugins/skills/external/PackageBuilder/SKILL.md:12`
- PackageBuilder 本身就是一个随软件携带的 Skill，Skill 的通用机制见 [[plugin-skills|Skills 机制]]。`plugins/skills/external/PackageBuilder/SKILL.md:8`

## AI 速览

- `PackageBuilder` — 当前 Operit 随软件携带的插件开发 Skill。`plugins/skills/external/PackageBuilder/SKILL.md:8`
- `api_version` — ToolPkg API 契约版本；Operit2 新建包显式填写 `2.0.0`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:173`
- `schema_version` — 清单格式版本，当前为 `1`；不是 ToolPkg API 版本。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:172`
- `toolpkg_id` — 包的唯一标识符，建议反向域名格式。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:174`
- `version` — 插件自身的发布版本，与 `api_version`、`schema_version` 分别声明。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:175`
- `main` — ToolPkg 主入口脚本路径，用于执行注册函数。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:177`
- `registerToolPkg` — 主脚本注册函数，在独立的临时 JavaScript engine 中执行，须在 60 秒内完成。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`
- `METADATA` — 每个脚本文件开头的注释块，AI 解析它得到可用工具。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:118`
- `ToolPkg.ipc` — 跨上下文共享状态与调用能力的显式通道。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:574`
- `ToolPkg.wasm.call` — 调用 WASM 模块导出函数，当前 ABI 支持 `i32`、`i64`、`f32`、`f64` 标量参数与返回值。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:309`
- `operit_editor` — 包管理工具，实际执行 core command 并返回真实结果与错误。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`
- 主入口函数：`registerToolPkg`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:343`
- 数据流向一句话：包管理创作入口只准备 Skill 和包并填入聊天草稿，用户发送后才开始开发。`plugins/skills/external/PackageBuilder/SKILL.md:53`

## 核心机制

### API 版本与跨平台

- 文档声明：Operit2 的 ToolPkg API 支持版本为 `2.0.0`；对 `1.0.0` 和 `1.0.1` 的加载支持并不完整。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:36`
- 文档声明：Operit1 完整支持 ToolPkg API `1.0.0` 和 `1.0.1`，这两个版本主要面向 Android，是旧版 API 形式。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:34`
- 文档声明：ToolPkg API `2.0.0` 面向多平台开发，基本所有公共接口都通过统一 host 能力提供跨平台兼容；常规功能直接使用当前版本接口，不必为每个平台重复实现。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:40`
- 文档声明：遇到平台特异接口时，作者要明确其适用范围，考虑并验证其他平台的安装、界面与核心功能；不能把某个平台的专用能力当作所有平台都具备的接口。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:40`
- 文档声明：`schema_version` 表示清单格式版本，`api_version` 表示 ToolPkg API 契约，`version` 表示插件自身的发布版本，三者不能混用。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:9`

### 随包资料与磁盘实况

- SKILL.md 自述的随包资料树列出 `references/` 目录，含 `PLUGIN_CREATION_WORKFLOW.md`、`SCRIPT_DEV_GUIDE.md`、`TOOLPKG_FORMAT_GUIDE.md`。`plugins/skills/external/PackageBuilder/SKILL.md:23`
- SKILL.md 自述的随包资料树列出 `types/` 目录，含 `index.d.ts`、`core.d.ts`、`toolpkg.d.ts`。`plugins/skills/external/PackageBuilder/SKILL.md:27`
- SKILL.md 自述的随包资料树列出 `examples/` 目录，含 packages/buildin/ 与 packages/external/。`plugins/skills/external/PackageBuilder/SKILL.md:32`
- 文档声明：skill.include.json 把 `PLUGIN_CREATION_WORKFLOW.md`、`SCRIPT_DEV_GUIDE.md`、`TOOLPKG_FORMAT_GUIDE.md` 三份开发文档映射到 Skill 内的 `references/` 路径。`plugins/skills/external/PackageBuilder/skill.include.json:8`
- 文档声明：skill.include.json 把 `../../../types` 映射到 Skill 内的 `types` 目录。`plugins/skills/external/PackageBuilder/skill.include.json:16`
- 文档声明：skill.include.json 把 `../../../packages/buildin` 映射到 `examples/packages/buildin`。`plugins/skills/external/PackageBuilder/skill.include.json:20`
- 文档声明：skill.include.json 把 `../../../packages/external` 映射到 `examples/packages/external`。`plugins/skills/external/PackageBuilder/skill.include.json:33`
- 文档声明：skill.include.json 的示例排除 `.sync_state.json`、`.sync_hot_reload_state.json`、`node_modules`、`dist`、`build`、`tests-dist`。`plugins/skills/external/PackageBuilder/skill.include.json:26`
- 文档声明：示例目录提供开发源码与构建配置，不携带 `dist/`、`build/`、`tests-dist/` 中的生成文件或成品包。`plugins/skills/external/PackageBuilder/SKILL.md:38`
- 文档声明：Compose UI 按普通、可读的 CommonJS JavaScript 交付，保留界面声明和回调，运行时负责 Compose 编译与缓存；不要指导用户生成或修改 Compose 内部预编译产物。`plugins/skills/external/PackageBuilder/SKILL.md:38`

### 创作入口与开发目录

- 文档声明：包管理中的"快速创作你的插件"会安装 PackageBuilder、将它设为 AI 可见，并启用 `operit_editor`；准备完成后，需求会作为聊天草稿填入输入框，用户发送后才开始与 AI 协作开发；这个入口不自动生成源码、不自动配置编译器，也不自动安装或发布成品。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:17`
- 文档声明：确定开发目录时先调用 `execute_cli_command`，参数数组为 `["skill", "show", "PackageBuilder"]`，读取 Skill 的真实目录与附件位置。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:49`
- 文档声明：查看系统工具 `get_terminal_info`；脚本内对应 `Tools.System.terminal.info()`；根据 host 返回的 `terminalType` 和可用终端信息使用正确的 shell 语法；该接口不返回下载目录或开发目录。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:50`
- 文档声明：在已选定的终端会话中查询实际工作目录及工具版本，确定用户同意使用的可写目录，记为 `<dev_root>`；路径或工具不可用时，报告具体原因并停止，不猜目录、不改用另一套执行入口。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:51`
- 文档声明：`["package", "dir"]` 返回的是安装存储目录，不是源码开发目录；`host paths` 和 `host capabilities` 当前并未通过 core command 暴露。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:54`
- 文档声明：独立插件项目放在 `<dev_root>/<package_id>/`，将 Skill 的 `types/` 完整复制到 `<dev_root>/types/`；贡献 Operit 主项目时，脚本源码位于 `plugins/packages/buildin/` 或 `plugins/packages/external/`；不要把 Skill 内的示例副本当作应用已经安装的包。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:53`
- 文档声明：教程中的 `<dev_root>`、`<artifact_host_path>`、`<package_id>`、`<runtime_package_name>` 和 `<tool_name>` 是需要用真实值替换的占位符。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:3`

### 编写与构建

- 文档声明：完整复制 Skill 的 `types/`，不从旧仓库或云端下载另一版声明；项目通过 `../types` 引用声明；位于 `src/` 的三斜线引用是 `../../types/index.d.ts`。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:74`
- 文档声明：TypeScript 输出可读的 CommonJS JavaScript；Compose UI 保留 `ctx.UI.*` 界面声明和回调，由运行时完成 Compose 编译与缓存；交付文件供用户直接编辑，不生成 Compose 内部预编译产物。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:75`
- 文档声明：网络、文件与终端操作使用 `Tools.Network`、`Tools.Files`、`Tools.System.terminal` 及其 host API；不要用平台分支实现另一套插件运行链路；声明文件的存在不代表当前 host 实现了所有能力。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:76`
- 文档声明：package.json 示例声明开发依赖 `typescript` 为 `^5.0.0`，构建命令为 `tsc -p tsconfig.json`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:64`
- 文档声明：`tsconfig.json` 示例的 `target` 为 `es2020`，`module` 为 `commonjs`，`lib` 为 `es2020`，`rootDir` 为 `src`，`outDir` 为 `dist`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:74`
- 文档声明：CommonJS 对应当前运行时模块加载方式；不能把构建时使用的 Node.js 当作脚本执行宿主。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:90`
- 文档声明：确认真实编译器可用后执行项目声明的构建命令，例如 `npm run build`；检查退出码与 `dist/` 文件，不根据命令已提交宣称构建成功。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:93`
- 文档声明：单文件脚本包保留 `METADATA` 与导出函数；ToolPkg 在归档根目录放置 manifest，并按清单路径包含编译后的入口、子包、UI、资源与二次开发源码。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:77`
- 文档声明：在 `<dev_root>/<package_id>/src/my_new_script.ts` 按第 4 章写入 `METADATA` 和导出函数，构建得到 `dist/my_new_script.js`；单文件 JS 包直接导入编译成品；ToolPkg 按格式指南打包后导入。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:97`
- 文档声明：用文件工具 `Tools.Files.zip(sourceVfsPath, artifactVfsPath, false)` 可创建不含外层目录的归档；成品扩展名为 `.toolpkg`，manifest 必须位于 ZIP 根目录。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:78`

### 脚本元数据与动态工具集

- 文档声明：脚本主要使用 TypeScript 编写，以利用其强大的类型系统，但也可以使用原生 JavaScript (ES6+)。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:7`
- 文档声明：每个脚本文件的开头都必须包含一个 `/* METADATA ... */` 注释块；这块元数据是 Operit AI 理解并调用所编写功能的唯一途径；AI 会解析 `METADATA` 中的信息，将其作为可用的"工具"呈现给大语言模型。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:118`
- 文档声明：`category` 为可选字段；未填写或为空时，系统会自动归类为 `Other`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:159`
- 文档声明：`category` 缺失、为空字符串或仅包含空白字符时，解析阶段会自动归类为 `Other`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:325`
- 文档声明：`category` 建议直接复用 `examples/packages/` 中已使用的分类，避免创建语义重复的新分类。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:319`
- 文档声明：`advice` 字段标记"仅提示/说明"的工具；`advice: true` 时，该工具不要求在脚本中有同名函数实现；运行时会跳过"工具不存在"的校验。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:165`
- 文档声明：`states` 为一个数组，每个元素是一个"状态"（State）；系统会根据运行时能力按顺序评估每个 state 的 `condition`，选择第一个为 `true` 的 state 并激活。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:173`
- 文档声明：`states` 为空时使用顶层 `tools`；`states` 非空时从上到下找第一个满足 `condition` 的 state，找不到任何匹配时回退到顶层 `tools`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:185`
- 文档声明：当 `inheritTools=true` 时以顶层 `tools` 为基底；先应用 `excludeTools` 删除指定工具；再将 state 的 `tools` 合并进来，同名覆盖，不同名新增。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:191`
- 文档声明：条件可用的 capability key 包括 `platform.name`，表示当前运行平台名称，如 `windows`、`linux`、`android`、`macos`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:206`
- 文档声明：条件可用的 capability key 包括 `android.permission_level`，表示权限等级，以字符串形式参与比较。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:213`
- 文档声明：运行时会向脚本环境提供全局函数 `getState(): string`，返回当前激活的 state 的 `id`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:219`
- 文档声明：运行时会向脚本环境提供全局函数 `getLang(): string`，返回当前使用的语言代码，如 `zh`、`en`；语言不可用时返回 `en`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:223`
- 文档声明：`METADATA` 中的 `display_name`、`description`、`tools[].description` 与参数 `description` 支持单语字符串或多语对象两种写法。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:227`
- 文档声明：全局 `Tools` 对象分命名空间提供 API：`Tools.System` 提供 `sleep`、`startApp`、`stopApp` 等系统级操作；`Tools.UI` 提供 `getPageInfo`、`pressKey`、`swipe`、`setText` 等 UI 自动化操作。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:353`
- 文档声明：`Tools.Files` 提供 `read`、`write`、`list` 等文件操作；`Tools.Network` 提供 `httpGet`、`httpPost` 等网络请求；另有 `UINode` 类表示 UI 元素。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:355`
- 文档声明：所有工具函数都是异步的，调用时必须使用 `await`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:359`
- 文档声明：`Java` 与 `Kotlin` 的桥接是需要对应 host 实现支持的专用能力，类型声明不代表每个平台都能调用 Java 或 Android 类；全平台插件的文件、网络和终端操作应使用统一 `Tools` 与 host API，不要用 Java Bridge 替代这些抽象。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:375`
- 文档声明：Java Bridge 类获取的兼容写法是 `Java.type("java.lang.StringBuilder")`；别名是 `Java.use(...)` 与 `Java.importClass(...)`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:394`
- 文档声明：`Java.callSuspend(className, methodName, ...args)` 是异步挂起调用，返回 Promise。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:398`
- 文档声明：`callSuspend` 用于调用 Kotlin `suspend` 方法，始终返回 Promise。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:465`
- 文档声明：导出名称与 `METADATA.tools[].name` 保持一致；直接返回真实工具结果，执行错误由当前运行时记录；不要把失败转换成成功返回。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:517`
- 文档声明：`Tools.UI.getPageInfo()` 返回的页面结构是一个 `UINode` 对象树；每个 `UINode` 代表屏幕上的一个 UI 元素。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:560`
- 文档声明：`UINode` 查找子元素可用 `findById`、`findByText`、`findByClass`、`findAllBy...`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:561`
- 文档声明：`UINode` 示例按资源 ID 查找搜索框：`page.findById('com.example:id/search_box')`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:574`
- 文档声明：示例按文本查找登录按钮：`page.findByText("登录")`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:577`；按类名查找全部文本视图：`page.findAllByClass('TextView')`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:580`；按内容描述查找返回按钮：`page.findByContentDesc("返回")`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:583`
- 文档声明：工具调用示例为 `await Tools.System.sleep(3000)` 等待 3 秒，`await Tools.UI.getPageInfo()` 获取当前页面信息。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:364`
- 文档声明：工具调用示例为在屏幕上滑动用 `await Tools.UI.swipe(540, 1800, 540, 900)`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:370`

### 清单 manifest 字段

- 文档声明：清单支持 `manifest.json`（标准 JSON 格式）与 `manifest.hjson`（HJSON 格式，支持注释和更宽松的语法）两种格式，清单字段的解析见 [[plugin-manifest|清单 manifest 与安装作用域]]。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:83`
- 文档声明：完整示例 manifest 中 `schema_version` 为 `1`，`api_version` 为 `2.0.0`，`toolpkg_id` 为 `com.operit.windows_bundle`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:90`
- 文档声明：`schema_version` 是清单格式版本，当前为 `1`；不是 ToolPkg API 版本。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:172`
- 文档声明：`api_version` 是 ToolPkg API 契约版本；Operit2 新建包显式填写 `2.0.0`；省略时按旧版 `1.0.0` 契约加载，启用对应适配和运行依赖；`1.0.0`、`1.0.1` 的兼容加载支持并不完整。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:173`
- 文档声明：`toolpkg_id` 是包的唯一标识符，建议使用反向域名格式，如 `com.operit.windows_bundle`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:174`
- 文档声明：`version` 是插件自身的发布版本，建议使用语义化版本，如 `0.2.0`；与 `api_version`、`schema_version` 分别声明。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:175`
- 文档声明：`main` 是 ToolPkg 主入口脚本路径，相对于 ZIP 根目录，用于执行注册函数；`main` 为必填字段。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:177`
- 文档声明：`display_name` 与 `description` 均为 `LocalizedText`，支持多语言。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:178`
- 文档声明：`workflow_templates` 是注册到宿主"工作流"入口的工作流模板列表；`workspace_templates` 是注册到宿主"工作区创建"入口的工作区模板列表。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:183`
- 文档声明：`LocalizedText` 支持简单字符串与多语言对象两种格式。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:188`
- 文档声明：子包的 `enabled_by_default` 表示是否默认启用，默认为 `false`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:236`
- 文档声明：子包脚本必须是标准的 JavaScript 文件；必须包含 `METADATA` 注释块；脚本中定义的工具会被注册为 `<subpackage_id>:<tool_name>` 格式。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:242`
- 文档声明：资源声明的字段为 `key`、`path` 与 `mime`，其中 `key` 是资源的唯一键，用于在代码中引用。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:658`
- 文档声明：WASM 模块的 `source_language` 是源语言标记，AssemblyScript 模块写 `assemblyscript`；`abi` 是调用约定标记，当前写 `scalar`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:264`
- 文档声明：WASM 模块示例的 `exports` 为 `["isPrime", "nthPrime"]`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:129`
- 文档声明：`ToolPkg.wasm.call(moduleId, exportName, args)` 已接入 native WASM runtime；当前 ABI 支持 `i32`、`i64`、`f32`、`f64` 标量参数与返回值。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:309`
- 文档声明：`i64` 结果以字符串返回；JS 传入 `i64` 时建议使用字符串，避免超过 JS safe integer 后丢精度。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:310`
- 文档声明：资源声明示例的 `key` 为 `pc_agent_zip`，`path` 为 `resources/pc_agent/operit-pc-agent.zip`，`mime` 为 `application/zip`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:121`

### 主脚本注册与执行上下文

- 文档声明：`main.js` 示例中 `registerToolPkg()` 调用 `ToolPkg.registerToolboxUiModule` 注册 UI 模块。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:343`
- 文档声明：main.js 导出 `registerToolPkg`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:460`
- 文档声明：每个 ToolPkg 的 `registerToolPkg()` 会在独立的临时 JavaScript engine 中执行，注册状态不会跨包共享；主脚本注册必须在 60 秒内完成；同步死循环和超过时限的异步注册都会被终止，并将加载错误归属到当前包，扫描随后继续处理其他包。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`
- 文档声明：注册期间禁止调用 `ToolPkg.readResource(...)` 和 `ToolPkg.wasm.call(...)`，调用会立即抛出异常；模块加载仍可使用 `require/import`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:467`
- 文档声明：`ToolPkg.registerToolboxUiModule` 的 `runtime` 运行时类型默认 `compose_dsl`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:474`
- 文档声明：`ToolPkg.registerUiRoute` 的 `route` 与 `routeId` 不填时，宿主按 `toolpkg:<toolpkg_id>:ui:<id>` 自动生成稳定路由 ID。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:479`
- 文档声明：`ToolPkg.registerNavigationEntry` 的 `surface` 挂载面当前支持 `toolbox`、`main_sidebar_plugins`、`app_bar`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:486`
- 文档声明：`ToolPkg.registerDesktopWidget` 的 `route` 与 `routeId` 是已注册路由 ID，为必填项；`render` 与 `renderRouteId` 默认等于 `route`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:491`
- 文档声明：`ToolPkg.registerAppLifecycleHook` 的 `event` 与 `function` 为必填项。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:499`
- 文档声明：`ToolPkg.registerAppLifecycleHook` 支持的 application 事件包括 `application_on_create`、`application_on_foreground`、`application_on_background`、`application_on_low_memory`、`application_on_trim_memory`、`application_on_terminate`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:511`
- 文档声明：该函数支持的 activity 事件包括 `activity_on_create`、`activity_on_start`、`activity_on_resume`、`activity_on_pause`、`activity_on_stop`、`activity_on_destroy`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:517`
- 文档声明：`main` 上下文是 `manifest.main` 指向的包入口脚本，承载包级逻辑：注册 hook、执行 hook、注册/处理包级 IPC、承载包级内存态；同一个 ToolPkg 容器共用一个包级 JS engine，内部 context key 形如 `toolpkg_main:<toolpkg_id>`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:536`
- 文档声明：`ui` 上下文是 `*.ui.js` 的 Compose DSL screen/action handler，渲染界面、响应点击、读取 UI state；每个 UI route、widget、XML render 实例有自己的 JS engine。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:537`
- 文档声明：`sandbox` 上下文是独立工具脚本、子包工具脚本、调试脚本，执行一次性工具逻辑；可以通过 IPC 调用所属 ToolPkg 的 `main`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:538`
- 文档声明：`provider` 上下文是 `ToolPkg.registerAiProvider(...)` 注册的 AI provider handler，处理自定义 AI provider 的模型列表、连接测试、发消息、token 估算；每个 ToolPkg provider 使用独立 JS engine，内部 context key 形如 `toolpkg_provider:<toolpkg_id>:<provider_id>`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:539`
- 文档声明：`ToolPkg.ipc` 的 `meta.currentRuntime` 使用 `main`、`ui`、`sandbox`、`provider` 四种字面量。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:543`
- 文档声明：跨上下文共享状态或调用能力时，显式使用 `ToolPkg.ipc`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:574`
- 文档声明：`ToolPkg.ipc.on(channel, handler)` 在当前上下文注册通道处理函数；`ToolPkg.ipc.call(channel, payload)` 的语义是非 `main` 上下文调用同包 ToolPkg main，`main` 上下文调用本地 handler；`ToolPkg.ipc.call(channel, payload, options)` 可指定 `targetRuntime` 与 `targetContextKey` 调用目标 runtime 实例。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:620`
- 文档声明：`ToolPkg.ipc` 的 payload 和返回值应使用 JSON 可序列化数据：字符串、数字、布尔值、数组、普通对象和 `null`；对象按数据复制传输，不保留引用身份、原型、方法闭包或类实例。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:623`
- 文档声明：指定 `ui`、`provider`、`sandbox` 目标时需要提供明确的 `targetContextKey`；目标不存在会直接报错。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:626`
- 文档声明：UI state 只服务当前界面展示时，放在 `ctx.useState` 与 `ctx.useMemo`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:632`
- 文档声明：`ToolPkg.registerDesktopWidget` 是桌面小部件注册接口；桌宠和其他实时悬浮工具使用独立的 `ToolPkg.ui.floatingWindows` 窗口控制接口，内容复用已注册的 Compose UI 路由；方法、平台能力、权限与生命周期见 `../FLOATING_WINDOWS.md`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1405`

### 资源、模板与 UI

- 文档声明：资源访问在子包脚本中通过 PackageManager API，在 UI 模块中通过 `ToolPkg.readResource(key)`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:664`
- 文档声明：当 `mime` 是目录类型（如 `inode/directory`、`vnd.android.document/directory`）时，`ToolPkg.readResource(key)` 会先将该目录压缩成 zip，再返回这个 zip 的临时文件路径；如果没有显式传 `outputFileName`，目录资源默认会自动补上 `.zip` 后缀。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:667`
- 文档声明：工作流模板的 `resource_key` 指向 `resources` 中某个文件资源。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:702`
- 文档声明：工作流模板的 `resource_key` 必须引用一个文件资源，不能是目录资源。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:705`
- 文档声明：工作流模板导入时，宿主重新生成工作流 `id`；执行统计字段会被重置；导入成功后会落库成正式 `Workflow`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:710`
- 文档声明：工作区模板的 `resource_key` 指向 `resources` 中某个目录资源。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:754`
- 文档声明：工作区模板的 `resource_key` 必须引用一个目录资源，常见 `mime` 可写 `inode/directory` 或 `application/x-directory`；目录内容里必须包含 `.operit/config.json`；宿主导入时会把整个目录复制到当前 chat 的 workspace 目录。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:758`
- 文档声明：`template_try` 示例同时演示 `workflow_templates`、`workspace_templates`、目录资源和最小 `main.ts`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:777`
- 文档声明：Compose DSL 是一种基于 JavaScript 的声明式 UI 框架，灵感来自 Jetpack Compose。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:987`
- 文档声明：Compose DSL 的特点包括声明式语法、组件化设计、状态管理、事件处理。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:992`
- 文档声明：Compose DSL 布局组件包括 `Column`（垂直布局）、`Row`（水平布局）、`Box`（容器）、`Spacer`（间距）。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1055`
- 文档声明：Compose DSL 基础组件包括 `Text`、`TextField`、`Button`、`IconButton`、`Switch`、`Checkbox`、`Card`、`Icon`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1065`
- 文档声明：UI 示例用 `ctx.useState` 管理 `url` 与 `token` 状态，用 ctx.callTool('windows_control:windows_test_connection', {...}) 调用工具。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1009`
- 文档声明：UI 模块通过 `ctx.getEnv('API_KEY')` 读环境变量，通过 `ctx.setEnv` 与 `ctx.setEnvs` 写环境变量。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1116`
- 文档声明：UI 模块通过 `ctx.isPackageImported`、`ctx.importPackage`、`ctx.removePackage`、`ctx.usePackage`、`ctx.listImportedPackages` 管理包。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1128`
- 文档声明：UI 模块通过 ctx.resolveToolName({packageName, subpackageId, toolName, preferImported}) 解析工具名。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1137`
- 文档声明：`ctx.navigate(route, args?)` 会触发真实路由跳转；`ctx.listRoutes()` 返回当前可导航路由列表，包含 `routeId`、`runtime` 等字段；`ctx.getHostRoutes()` 只返回宿主 Native 路由；Native 路由 ID 命名规则为 native.<Screen 对象名的 snake_case>，例如 `Screen.Toolbox` 对应 `native.toolbox`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1154`
- 文档声明：`ctx.openFilePicker(options?)` 仅使用 `picker` 指定选择来源；未传入 `picker` 时打开文档选择器。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1161`
- 文档声明：该 API 通过 Flutter `file_selector` 在 Android、iOS、Linux、macOS、Windows、Web 和 OpenHarmony 使用各平台的文件选择器；不适用该 `picker` 的选项会直接报错；结果提供平台文件路径或浏览器对象 URL。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1173`
- 文档声明：`ctx.saveFile(options)` 将 UTF-8 文本交给宿主的跨平台文件保存服务，由用户在系统保存界面选择位置。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1177`
- 文档声明：`ToolPkg.registerToolboxUiModule(...)` 仍然保留；宿主内部把它自动映射为注册一个 `compose_dsl` UI route 与自动挂载一个 `toolbox` 导航入口；旧接口不会自动创建主侧边栏插件入口，需要主侧边栏插件入口时额外调用 `ToolPkg.registerNavigationEntry(...)` 并使用 `surface` 为 `main_sidebar_plugins`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1193`
- 文档声明：UI 模块可用 `getLang()` 取当前语言，返回 `zh` 或 `en`；可用 `ctx.getCurrentPackageName()`、`ctx.getCurrentToolPkgId()`、`ctx.getCurrentUiModuleId()`、`ctx.getModuleSpec()` 取当前包与模块信息。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1201`
- 文档声明：子包环境变量声明示例中，`TIMEOUT` 为可选环境变量，`defaultValue` 为 `30000`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:930`
- 文档声明：命名规范为 `toolpkg_id` 使用反向域名格式，如 `com.operit.windows_bundle`；子包 id 使用小写字母和下划线，如 `windows_control`；资源 key 使用小写字母和下划线，如 `pc_agent_zip`；UI 模块 id 使用小写字母和下划线，如 `windows_setup`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1272`

### 首次安装与测试

- 文档声明：首次安装命令包括 `["package", "list"]`、`["package", "import", "<artifact_host_path>"]`、`["package", "enable", "<package_id>"]`、`["package", "show", "<runtime_package_name>"]`、`["package", "exec", "<runtime_package_name>:<tool_name>", "{}"]`、`["log", "package"]`。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:86`
- 文档声明：导入结果给出 `packageName`、`packageFormat` 和 `storedPath`；以实际解析结果确认身份，不根据文件名猜包 id。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:94`
- 文档声明：ToolPkg 容器 id 与可执行子包名不同；从 `package list` 和 `package show` 读取实际工具名；只注册 UI、hook 或 provider 的包不一定有可执行工具。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:95`
- 文档声明：启用后重新读取 `package list` 的真实 `enabled` 状态；不能把启用命令自身的文字或请求参数当作状态证明。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:96`
- 文档声明：`package exec` 会激活对应工具包并执行导出工具；根据该工具声明填写 JSON 参数，检查返回内容；UI、hook、provider 必须在对应应用场景验证。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:97`
- 文档声明：调试小片段时，将它写成有 `METADATA` 和导出函数的独立测试包，按导入、启用、执行、查看日志的流程测试；`operit_editor` 不提供脚本直跑工具。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:98`
- 文档声明：每一步出现错误即停止并定位原因；不要根据"命令已调用"宣称安装、启用或测试成功。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:99`
- 文档声明：`operit_editor` 的 `operit_editor` 工具实际调用 `Tools.SoftwareSettings.exec(args)`，与系统工具 `execute_cli_command` 使用同一 core command 执行入口，返回真实命令结果并传播执行错误；传入 `args` CLI 字符串数组（也接受数组的 JSON 字符串），不含 `operit2` 可执行文件名；自然语言 `query` 已移除，不会被转换成编辑动作。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`
- 文档声明：同名包重新安装会被拒绝，更新需要按创作流程第 5 节完成明确授权的替换操作。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:110`
- 文档声明：`package import` 接收成品文件，不接收源码目录，并拒绝重复的已注册包名。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:615`
- 文档声明：Core command 参数数组不含 `operit2`；脚本可调用 `Tools.SoftwareSettings.exec(args)`，AI 可直接调用系统工具 `execute_cli_command`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:613`
- 文档声明：调试时把不确定的逻辑缩为有 `METADATA` 和导出函数的独立测试包，通过 `package import/enable/list/show/exec` 验证真实行为。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:599`
- 文档声明：`operit_editor` 的 `operit_editor` 工具实际执行 `args` 指定的 core command，`args: []` 读取实际命令帮助；它不提供任意脚本片段直跑功能。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:600`
- 文档声明：查看 `["log", "package"]`、`["log", "show"]` 的实际日志，保存原始失败信息；工具调用失败后停止并定位，不切换另一套执行链路。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:601`

### 同 ID 更新与发布

- 文档声明：当前 `package import` 拒绝重复的已注册包名，不提供覆盖安装或自动热更新；更新步骤是用户明确授权后的替换操作，不是失败后的自动处理。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:103`
- 文档声明：同 ID 更新第一步是在删除已安装版本之前完成新版本构建，核验归档，并在开发目录保留源码及所需旧版本成品。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:105`
- 文档声明：同 ID 更新第二步是用 `package list` 和 `package show` 记录容器、子包的真实名称及启用状态；向用户说明删除与重新安装的影响并获得确认。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:106`
- 文档声明：同 ID 更新第三步是调用 `["package", "delete", "<package_id>"]`，确认删除成功；只对本次要更新的外部包执行该操作，不删除其他包。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:107`
- 文档声明：同 ID 更新第四步是调用 `["package", "import", "<artifact_host_path>"]`，确认新版本导入成功；导入失败时保留错误并停止，不自动改变包 id 或执行其他安装路径。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:108`
- 文档声明：同 ID 更新第五步是按用户确认的配置逐项恢复容器及子包的启用状态，再读取列表核验，并重新测试工具、UI 与 hook。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:109`
- 文档声明：不要宣称包管理已经具有一键继续开发、合并开发或覆盖安装功能；创作入口目前接入的是新建需求草稿；继续开发需要明确定位原项目并按上述流程处理。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:111`
- 文档声明：发布方式一是直接发布本地插件，页面处理当前成品，在当前 GitHub 账号的 `OperitForge` 仓库保存 Release 资产并登记市场条目。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:117`
- 文档声明：发布方式二是引用 GitHub Release 资产，选择自己仓库的 Release 与资产；页面核对所选资产与当前本地成品，并提交登记。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:118`
- 文档声明：引用 Release 时，Operit 会下载所选资产并与当前本地插件计算 SHA-256 比对；市场服务还会确认该 Release 的创建者就是当前 Operit 登录的 GitHub 账号。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:39`
- 文档声明：发布需要登录、用户确认及真实服务响应，不是创作入口自动完成的动作；交付时分别列出源码目录、成品路径、包 id、安装与启用状态、已执行的测试和结果，以及发布状态；未测试或未发布的环节要明确标注。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:120`
- 文档声明：已安装的 Skill 更新资料时，当前创作准备流程会复用已经安装的 PackageBuilder，不会自动覆盖它的附件；更新应用资源不会同步改写用户已安装的 Skill。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:34`
- 文档声明：要使用当前版本的内置资料，先核对 `["skill", "show", "PackageBuilder"]` 返回的目录并备份用户修改；获得用户确认后执行 skill delete、skill load、skill visible true、skill show 四步。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:36`

### 旧版迁移检查

- 文档声明：为 Operit2 新建 ToolPkg 要显式声明 `"api_version": "2.0.0"`，使用本 Skill 的当前版本类型；不能把旧版兼容加载当作完整支持，也不能只修改旧包版本号就宣称完成迁移。`plugins/skills/external/PackageBuilder/SKILL.md:14`
- 文档声明：解析器接受旧版本号不等于完整实现旧接口；旧包需要逐项验证所用能力，不能仅凭导入成功宣称兼容；迁移旧包需要同步检查接口、路径和平台语义，不能只修改版本号。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:7`
- 文档声明：不能通过仅改 manifest 版本号把旧 Android 插件视为已完成迁移；需要检查实际接口与平台行为；`api_version` 是 ToolPkg 清单字段，不是单文件脚本的元数据字段。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:13`
- 文档声明：接受某个版本号、成功导入包和完整支持该版本的接口是不同的事情；旧包迁移不能只改版本号，还需检查接口、路径与平台行为。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:38`
- 文档声明：省略 `api_version` 时按旧版 `1.0.0` 契约加载，启用对应适配和运行依赖；`1.0.0`、`1.0.1` 的兼容加载支持并不完整。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:173`

### 内置同步与示例

- 文档声明：资源同步脚本仅适用于贡献 Operit 主仓库，不是安装后的 Skill 自带命令；源码位于 `plugins/packages/buildin/` 和 `plugins/packages/external/`；资源同步脚本为 `plugins/tools/sync_plugin_packages.py`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:818`
- 文档声明：同步脚本查看计划的命令是 `python plugins/tools/sync_plugin_packages.py --source runtime --dry-run --no-hot-reload`，不写入资源。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:824`
- 文档声明：同步脚本构建并同步内置与 external 资源的命令是 `python plugins/tools/sync_plugin_packages.py --source runtime --no-hot-reload`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:827`
- 文档声明：同步脚本会生成当前 SDK 类型、按包的构建契约处理源码，并更新 `core/crates/runtime/application/assets/plugins/buildin/` 与 `external/`；此步骤服务于应用资源构建，不等于向正在运行的应用安装插件。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:830`
- 文档声明：贡献主项目时，通过第 4.2 节的同步脚本生成 `core/crates/runtime/application/assets/plugins/buildin/` 和 `external/` 中的资源；应用构建会嵌入这些资源；内置资源同步不是运行时安装命令。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1246`
- 文档声明：`examples/packages/buildin/time.ts` 是单文件工具包示例，含 `METADATA`、参数与导出函数。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:545`
- 文档声明：`examples/packages/buildin/operit_editor.ts` 是实际执行平台编辑命令的包；`operit_editor` 工具将 `args` 字符串数组传给 `Tools.SoftwareSettings.exec(args)`，与 `execute_cli_command` 使用同一执行入口，返回真实结果与错误，不接受自然语言 `query`。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:546`
- 文档声明：`examples/packages/external/template_try/` 演示 ToolPkg 清单、工作流模板、工作区模板和资源注册。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:547`
- 文档声明：`examples/packages/buildin/workflow/` 是较完整的 ToolPkg 项目，包含 UI、公共接口和构建说明。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:548`
- 文档声明：PackageBuilder 的示例路径为 `examples/packages/`，不是旧版根目录 `examples/`；随软件携带的示例提供源码与构建配置，排除 `dist/`、`build/`、`tests-dist/` 生成目录；阅读 Skill 的示例不会自动将该包安装到当前 runtime。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1373`
- 文档声明：贡献主项目时对应 Rust 源码为 `core/crates/command/core/src/commands/package.rs`（包命令）、`core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs`（运行时包管理）、`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs`（ToolPkg 解析）、`core/crates/runtime/application/build.rs`（内置包与 Skill 附件的资源嵌入）。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1389`
- 文档声明：格式指南更新日志 `v1.0.0`（2024-02-14）是初始版本：支持子包、UI 模块、资源文件，支持多语言，提供 Compose DSL UI 框架。此为指南文档的版本记录，与 api_version 无关。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1396`
- 文档声明：版本管理建议使用语义化版本号 `MAJOR.MINOR.PATCH`，如 `1.2.3`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1262`

### 调试与故障排查

- 文档声明：调试用 `["log", "package"]`、`["log", "show"]` 和 `["log", "path"]` 查看当前 runtime 日志；不要依赖某个平台的日志命令。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1355`
- 文档声明：包无法导入时检查 `manifest.json` 格式是否正确、确认 `toolpkg_id` 是否唯一、验证 ZIP 文件结构是否正确。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1329`
- 文档声明：子包无法加载时检查 `entry` 路径是否正确、确认脚本文件包含有效的 `METADATA`、查看应用日志获取详细错误信息。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1334`
- 文档声明：资源无法访问时检查资源 `key` 是否正确、确认资源 `path` 在 ZIP 中存在、验证资源文件没有损坏。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1339`
- 文档声明：UI 模块不显示时检查 `main.js` 是否导出 `registerToolPkg`、是否调用了 `ToolPkg.registerToolboxUiModule(...)`、确认 `runtime` 类型正确、确认 `screen` 传的是已导入的模块函数、验证 UI 脚本语法正确。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:1344`

## 关键符号

- `PackageBuilder` — 当前 Operit 随软件携带的插件开发 Skill。`plugins/skills/external/PackageBuilder/SKILL.md:8`
- `api_version` — ToolPkg API 契约版本；Operit2 新建包显式填写 `2.0.0`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:173`
- `schema_version` — 清单格式版本，当前为 `1`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:172`
- `toolpkg_id` — 包的唯一标识符，建议反向域名格式。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:174`
- `version` — 插件自身的发布版本，与 `api_version`、`schema_version` 分别声明。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:175`
- `main` — ToolPkg 主入口脚本路径，用于执行注册函数。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:177`
- `registerToolPkg` — 主脚本注册函数。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:343`
- `ToolPkg.registerToolboxUiModule` — 注册 Compose DSL 工具箱 UI 模块。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:344`
- `ToolPkg.registerUiRoute` — 注册 UI 路由。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:478`
- `ToolPkg.registerNavigationEntry` — 注册导航入口。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:486`
- `ToolPkg.registerDesktopWidget` — 注册桌面小部件。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:491`
- `ToolPkg.registerAppLifecycleHook` — 注册应用生命周期钩子。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:498`
- `ToolPkg.registerMessageProcessingPlugin` — 注册消息处理插件。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:501`
- `ToolPkg.registerXmlRenderPlugin` — 注册 XML 渲染插件。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:503`
- `ToolPkg.registerInputMenuTogglePlugin` — 注册输入菜单开关插件。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:506`
- `ToolPkg.registerAiProvider` — 注册自定义 AI provider。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:539`
- `ToolPkg.ipc` — 跨上下文通道。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:574`
- `ToolPkg.wasm.call` — 调用 WASM 导出函数。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:309`
- `ToolPkg.readResource` — 读资源。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:664`
- `METADATA` — 脚本元数据注释块。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:118`
- `states` — 动态工具集。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:173`
- `getState` — 返回当前激活 state 的 id。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:219`
- `getLang` — 返回当前语言代码。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:223`
- `Tools` — 全局工具对象，分 `System`、`UI`、`Files`、`Network` 命名空间。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:353`
- `UINode` — UI 元素对象树节点。`plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md:560`
- `operit_editor` — 包管理工具。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`
- `execute_cli_command` — 系统工具，与 `operit_editor` 使用同一 core command 执行入口。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:19`
- `Tools.Files.zip` — 创建不含外层目录的归档。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:78`
- `enabled_by_default` — 子包是否默认启用，默认为 `false`。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:236`
- `LocalizedText` — 多语言文本类型。`plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md:188`
- `ctx.UI` — Compose DSL 界面声明入口。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:75`

## 调用链

1. 包管理"快速创作你的插件"安装 PackageBuilder、设为 AI 可见、启用 `operit_editor`，需求填入聊天草稿。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:17`
2. 调用 `execute_cli_command`，参数 `["skill", "show", "PackageBuilder"]`，读取 Skill 真实目录；用 `get_terminal_info` 与终端 host 信息确定用户同意的 `<dev_root>`。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:49`
3. 确定稳定的 package id，在 `<dev_root>/<package_id>/` 保存项目，把本 Skill 的 `types/` 完整复制到 `<dev_root>/types/`。`plugins/skills/external/PackageBuilder/SKILL.md:45`
4. 用 TypeScript 编写源码并输出 CommonJS JavaScript，保留 `.ts`、`tsconfig.json` 和最终产物。`plugins/skills/external/PackageBuilder/SKILL.md:47`
5. 按 `manifest` 清单路径打包：`Tools.Files.zip(sourceVfsPath, artifactVfsPath, false)` 生成不含外层目录的 `.toolpkg` 归档，manifest 位于 ZIP 根目录。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:78`
6. 调用 `operit_editor` 执行 `["package", "import", "<artifact_host_path>"]` 导入成品，再执行 `["package", "enable", "<package_id>"]` 启用。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:86`
7. 用 ["package", "list"] 与 `["package", "show", "<runtime_package_name>"]` 核对真实工具名与 `enabled` 状态。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:94`
8. 用 `["package", "exec", "<runtime_package_name>:<tool_name>", "{}"]` 执行导出工具，用 `["log", "package"]` 查看日志。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:90`
9. 同 ID 更新时，先获用户确认，再依次执行删除、重新导入、按记录恢复启用状态、重新测试。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:106`
10. 本地测试通过后，用户在 Artifact 市场发布页面选择直接发布本地插件或引用 GitHub Release 资产。`plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md:115`

## 来源

- `plugins/skills/external/PackageBuilder/SKILL.md`
- `plugins/skills/external/PackageBuilder/skill.include.json`
- `plugins/docs/package_builder/PLUGIN_CREATION_WORKFLOW.md`
- `plugins/docs/package_builder/SCRIPT_DEV_GUIDE.md`
- `plugins/docs/package_builder/TOOLPKG_FORMAT_GUIDE.md`
