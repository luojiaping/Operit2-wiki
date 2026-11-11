---
title: 工具系统——包、技能与 MCP
module: core
platforms: [all]
sources: 6
date: 2026-11-11
---

## 概述

本页讲工具系统的三类执行入口与一层 JS 适配：SDK 包工具由 `PackageToolExecutor` 执行，技能由 `SkillManager` 扫描、安装与删除，MCP 服务器由 `MCPManager` 注册与建连、由 `MCPToolExecutor` 调用，`ToolJsRuntime` 把包管理器适配进 SDK 的 JS 运行时契约并提供 ToolPkg IPC。

包格式与加载器不在本页，在 [[core-plugin-sdk|插件——Plugin SDK]]；JS 桥的完整机制在 [[core-plugin-js-bridge|插件——JS 桥]]；工具注册与执行器选择见 [[core-tool-execution|工具系统——执行与注册]]。

三类入口的命名都以冒号分段：包工具是 `packageName:toolName`（core/crates/tool/services/src/tools/PackageToolExecutor.rs:35），MCP 工具是 `server_name:tool_name`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:339）。

JS 执行引擎由 Host 提供：包执行器经 `host.runtimeDependencies().js_execution_provider()` 创建（core/crates/tool/services/src/tools/PackageToolExecutor.rs:81），具体 JS 引擎随 Host 而异；Core 侧的适配与调度逻辑本身是平台无关的 Rust 代码。

## AI 速览

- `PackageToolExecutor` — 绑定一个包名，执行单个 SDK 包的工具调用（core/crates/tool/services/src/tools/PackageToolExecutor.rs:15）
- `PackageManagerJsRuntime` — 把 `RuntimePackageManager` 适配为 SDK 的 `JsPackageRuntime` 契约（core/crates/tool/services/src/tools/ToolJsRuntime.rs:35）
- `SkillPackage` — 一个技能的记录：名、描述、目录、SKILL.md 路径（core/crates/tool/services/src/tools/skill/SkillPackage.rs:6）
- `SkillManager` — 扫描、安装、删除技能，生成技能激活提示词（core/crates/tool/services/src/tools/skill/SkillManager.rs:53）
- `MCPManager` — 进程内全局单例，注册 MCP 服务器并缓存桥接客户端（core/crates/tool/services/src/tools/mcp/MCPManager.rs:20）
- `MCPToolExecutor` — 按 `server_name:tool_name` 把调用发往 MCP 服务器并转换结果（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:339）
- `MCPBridgeClient` — `mcp_runtime::plugins` 的桥接客户端，承载与 MCP 服务器的通信（core/crates/tool/services/src/tools/mcp/MCPManager.rs:5）
- `materializeToolPkgResource` — 把 ToolPkg 资源物化为文件并返回 VFS 路径（core/crates/tool/services/src/tools/ToolJsRuntime.rs:180）
- `invokeToolPkgIpc` — 调用 ToolPkg IPC 目标，带分阶段计时（core/crates/tool/services/src/tools/ToolJsRuntime.rs:244）
- `inferToolPkgRuntime` — 按上下文键前缀推断 ToolPkg 运行时种类（core/crates/tool/services/src/tools/ToolJsRuntime.rs:552）
- 主入口函数：包工具 `PackageToolExecutor::invokeAndStreamAsync`（core/crates/tool/services/src/tools/PackageToolExecutor.rs:79），技能 `SkillManager::refreshAvailableSkills`（core/crates/tool/services/src/tools/skill/SkillManager.rs:53），MCP `MCPToolExecutor::invoke`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:337）
- 数据流向一句话：模型发 `packageName:toolName` 或 `server_name:tool_name` 调用 → 对应执行器校验 → 包调用进 Host JS 执行器或技能提示词进上下文、MCP 调用经桥接客户端发往服务器 → 结构化结果转回 `ToolResult`。

## 核心机制

### 包工具执行

- `PackageToolExecutor` 绑定一个包名与共享的 `RuntimePackageManager`，为单个 SDK 包提供执行器（core/crates/tool/services/src/tools/PackageToolExecutor.rs:15）
- 包工具名必须是 `packageName:toolName` 的两段形式，两段都不能为空，否则返回 `Invalid package tool format` 错误（core/crates/tool/services/src/tools/PackageToolExecutor.rs:35）
- 工具名首段必须等于执行器绑定的 `packageName`，否则返回 `Package mismatch` 错误（core/crates/tool/services/src/tools/PackageToolExecutor.rs:44）
- 参数名重复时校验失败，报错 `Duplicate package tool parameter`（core/crates/tool/services/src/tools/PackageToolExecutor.rs:53）
- 包工具的 `accessSpec` 声明 `effect` 为 `READ`、`boundary` 为 `None`（core/crates/tool/services/src/tools/PackageToolExecutor.rs:68）
- 每次调用都新建一个 `PackageManagerJsRuntime`，并经 Host 的 `js_execution_provider` 创建包执行器（core/crates/tool/services/src/tools/PackageToolExecutor.rs:81）
- `packageToolCallRequest` 把 `AITool` 转成 `JsPackageToolCallRequest`，参数变为 `name` 到 `value` 的映射（core/crates/tool/services/src/tools/PackageToolExecutor.rs:97）
- `packageToolResult` 把 `JsPackageToolCallResult` 转成 `ToolResult`，文本结果经 `stringResultData` 包装（core/crates/tool/services/src/tools/PackageToolExecutor.rs:111）
- 包工具校验只核对通用命名空间边界，不从过期包元数据中选取工具（core/crates/tool/services/src/tools/PackageToolExecutor.rs:33）

### 技能加载与管理

- `SkillPackage` 由 `name`、`description`、`directory` 与 `skillFile` 四个字段组成，`directory` 与 `skillFile` 均为 `PathBuf`（core/crates/tool/services/src/tools/skill/SkillPackage.rs:6）
- `SkillManager` 在 `device` 与 `space` 两个位置扫描技能（core/crates/tool/services/src/tools/skill/SkillManager.rs:58）
- 同一技能名同时出现在两处位置时视为所有权冲突，从结果中移除并报错 `Skill ownership conflict`（core/crates/tool/services/src/tools/skill/SkillManager.rs:70）
- `device` 位置的技能会登记到 `ExtensionStore`，元数据 `visible` 为 `true`（core/crates/tool/services/src/tools/skill/SkillManager.rs:81）
- 登记记录的 `scope` 或 `sourceName` 与扫描结果不一致时，技能不予加载并报错 `Skill content does not match its registered location`（core/crates/tool/services/src/tools/skill/SkillManager.rs:91）
- `space` 位置的技能只认 `ExtensionStore` 中 `scope` 为 `space` 的记录（core/crates/tool/services/src/tools/skill/SkillManager.rs:123）
- `space` 位置磁盘上有目录但不在记录中的技能会被跳过（core/crates/tool/services/src/tools/skill/SkillManager.rs:154）
- 技能文件优先取 `SKILL.md`，不存在时改用 `skill.md`（core/crates/tool/services/src/tools/skill/SkillManager.rs:156）
- 两个文件都不存在时报错 `Missing SKILL.md in {目录}`（core/crates/tool/services/src/tools/skill/SkillManager.rs:181）
- `SKILL.md` 前置元数据中 `name` 为空时，用目录名作为技能名（core/crates/tool/services/src/tools/skill/SkillManager.rs:188）
- 同名技能重复扫描时报错 `Duplicate scanned skill name`（core/crates/tool/services/src/tools/skill/SkillManager.rs:204）
- `getAvailableSkills` 返回 `refreshAvailableSkills` 扫描到的有效技能包集合（core/crates/tool/services/src/tools/skill/SkillManager.rs:233）
- `getSkillLoadErrors` 返回扫描过程的错误集合（core/crates/tool/services/src/tools/skill/SkillManager.rs:247）
- `getBundledExternalSkillCandidates` 列出已打包但尚未安装的外部技能（core/crates/tool/services/src/tools/skill/SkillManager.rs:252）
- `importBundledExternalSkill` 导入已安装的技能时报错 `Skill already exists in an installation location`（core/crates/tool/services/src/tools/skill/SkillManager.rs:305）
- 快速插件创建所用的内置技能名为 `PackageBuilder`（core/crates/tool/services/src/tools/skill/SkillManager.rs:14）
- `ensureQuickPluginCreatorBundledSkill` 在 `PackageBuilder` 技能不存在时导入它，已存在则直接返回（core/crates/tool/services/src/tools/skill/SkillManager.rs:372）
- `readSkillContent` 读取已安装技能的 `SKILL.md` 文件内容（core/crates/tool/services/src/tools/skill/SkillManager.rs:387）
- `getSkillSystemPrompt` 生成的提示词以 `Using package (Skill): {技能名}` 与 `Use Time` 开头，并写明执行策略与描述（core/crates/tool/services/src/tools/skill/SkillManager.rs:405）
- 提示词包含 `SKILL.md` 路径与技能目录（core/crates/tool/services/src/tools/skill/SkillManager.rs:414）
- 提示词包含技能目录的目录树与 `SKILL.md` 全文（core/crates/tool/services/src/tools/skill/SkillManager.rs:422）
- `deleteSkill` 删除 `ExtensionStore` 中的 `skill` 记录，返回删除是否成功（core/crates/tool/services/src/tools/skill/SkillManager.rs:439）
- 技能根目录取自 `paths.skills_dir()`（core/crates/tool/services/src/tools/skill/SkillManager.rs:587）

### 技能压缩包导入

- 导入技能压缩包时先解压到 `.import_tmp_{毫秒时间戳}` 临时目录（core/crates/tool/services/src/tools/skill/SkillManager.rs:457）
- 导入完成后删除临时目录（core/crates/tool/services/src/tools/skill/SkillManager.rs:473）
- 导入时压缩包内只有一个子目录，则以它为搜索根（core/crates/tool/services/src/tools/skill/SkillManager.rs:495）
- 导入时可指定压缩包内的子目录作为搜索起点（core/crates/tool/services/src/tools/skill/SkillManager.rs:500）
- `safeChildPath` 只接受 `Normal` 路径组件，其他组件报错 `Invalid import path`（core/crates/tool/services/src/tools/skill/SkillManager.rs:845）
- 导入时先找搜索根下的直接 `SKILL.md`，找不到则递归查找最多 10 个（core/crates/tool/services/src/tools/skill/SkillManager.rs:512）
- 递归查找不到 `SKILL.md` 时，导入报错 `No SKILL.md found in the imported zip`（core/crates/tool/services/src/tools/skill/SkillManager.rs:520）
- 指定子目录导入时找不到 `SKILL.md`，报错 `No SKILL.md found in the selected import path`（core/crates/tool/services/src/tools/skill/SkillManager.rs:518）
- 导入的技能名优先取 `SKILL.md` 元数据的 `name`（core/crates/tool/services/src/tools/skill/SkillManager.rs:529）
- 导入命名都为空时用 `skill` 作为目录名（core/crates/tool/services/src/tools/skill/SkillManager.rs:554）
- 导入目标已存在同名技能时报错 `Skill already exists in an installation location`（core/crates/tool/services/src/tools/skill/SkillManager.rs:560）

### 技能元数据解析

- 解析技能元数据时先读开头的 `---` frontmatter 块（core/crates/tool/services/src/tools/skill/SkillManager.rs:613）
- frontmatter 中 `name` 或 `description` 缺失时，扫描文件前 40 行补齐（core/crates/tool/services/src/tools/skill/SkillManager.rs:622）
- 导入打包技能资产时，相对路径只接受 `Normal` 组件，否则报错 `Invalid plugin type asset path`（core/crates/tool/services/src/tools/skill/SkillManager.rs:665）
- 写入打包技能前，先清空技能目录的全部子项（core/crates/tool/services/src/tools/skill/SkillManager.rs:684）
- 目录树文本按目录在前、文件在后排序，同类按名称不区分大小写排序（core/crates/tool/services/src/tools/skill/SkillManager.rs:713）
- 解压 zip 时拒绝 `enclosed_name` 为空的条目，报错 `Zip entry is outside target dir`（core/crates/tool/services/src/tools/skill/SkillManager.rs:750）

### MCP 服务器注册与连接

- `MCPManager` 是进程内全局单例，`INSTANCE` 为 `OnceLock`（core/crates/tool/services/src/tools/mcp/MCPManager.rs:20）
- `getInstance` 每次调用都用传入的 `HostManager` 更新共享状态的 `context`（core/crates/tool/services/src/tools/mcp/MCPManager.rs:38）
- 管理器内部状态含 `clientCache`、`serverConfigCache` 与 `connectionFailureReasons` 三个按名索引的表（core/crates/tool/services/src/tools/mcp/MCPManager.rs:15）
- `isServerRegistered` 检查服务器名是否在 `serverConfigCache` 中（core/crates/tool/services/src/tools/mcp/MCPManager.rs:49）
- `getRegisteredServers` 返回全部已注册 MCP 服务器配置的克隆（core/crates/tool/services/src/tools/mcp/MCPManager.rs:55）
- `getLastConnectionFailureReason` 返回某服务器最近一次连接失败的原因（core/crates/tool/services/src/tools/mcp/MCPManager.rs:69）
- `getClientForMetadata` 不发起网络 I/O，未缓存时新建一个未连接的 `MCPBridgeClient` 返回（core/crates/tool/services/src/tools/mcp/MCPManager.rs:79）
- `getOrCreateClient` 优先返回 `ping` 成功的缓存客户端（core/crates/tool/services/src/tools/mcp/MCPManager.rs:94）
- 重连失败时记录失败原因并从缓存移除客户端（core/crates/tool/services/src/tools/mcp/MCPManager.rs:110）
- 未注册的服务器名返回 `None` 并记录 `Server is not registered in MCPManager.`（core/crates/tool/services/src/tools/mcp/MCPManager.rs:130）
- `registerServer` 注册或替换配置，同时清除失败原因与缓存客户端（core/crates/tool/services/src/tools/mcp/MCPManager.rs:162）
- `registerServerFromEndpoint` 用 `capabilities` `["tools"]` 注册服务器（core/crates/tool/services/src/tools/mcp/MCPManager.rs:182）
- `unregisterServer` 移除配置与失败原因并断开缓存客户端（core/crates/tool/services/src/tools/mcp/MCPManager.rs:192）
- `shutdown` 断开全部缓存客户端（core/crates/tool/services/src/tools/mcp/MCPManager.rs:201）

### MCP 工具调用

- MCP 工具名须为 `server_name:tool_name`，少于两段报错（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:339）
- 实际工具名取冒号后全部段落拼接（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:350）
- 取不到客户端时报错 `Cannot connect to MCP server '{服务器}': {原因}`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:355）
- 客户端未激活时报错，提示先用 `use_package` 工具激活该包（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:370）
- 调用前从工具定义的 `inputSchema.properties` 取参数声明（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:282）
- 未在 `properties` 中声明的顶层参数会被过滤掉（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:289）
- 保留的参数按声明的 `type` 经 `MCPToolParameter::smartConvert` 转换（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:296）
- 无可用 `properties` 时保留全部参数，不猜测哪些有效（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:276）
- 结果超过 `MAX_TEXT_RESULT_LENGTH` 时截断并追加改用文件操作或分页的提示（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:81）
- 结果的 `content` 数组各项以换行连接成文本（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:112）
- 除 `content` 外的键序列化为 JSON 元数据；元数据与内容同时存在时以空行连接（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:133）
- `text` 内容若本身是 JSON 对象或数组则重新序列化，否则原样返回（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:163）
- 图片超过内联上限时保存到文件，并提示用 `read_file` 查看（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:186）
- 图片在预算内时注册到 `ImagePoolManager` 返回 media link，同时保存一份文件副本（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:208）
- 图片预算耗尽时返回 `[Image omitted: attachment limit reached]`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:197）
- 图片数据解码失败时返回占位说明，不产生死链接（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:174）
- `resource` 内容有 `text` 时直接返回 `text`，否则返回 `[Resource: {uri}]`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:224）
- 未知内容类型返回 `[Unknown content type '{类型}': {内容}]`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:227）
- 图片解码只接受 `Png`、`Jpeg`、`Gif` 与 `WebP`，其中 `Png` 与 `Jpeg` 须能读出尺寸（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:237）
- 图片扩展名映射：`Jpeg`→`jpg`、`Gif`→`gif`、`WebP`→`webp`，其余→`png`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:259）
- 图片保存文件名格式为 `mcp-{毫秒时间戳}-{uuid}.{扩展名}`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:59）
- 图片保存目标需要 `turn` 快照、运行时存储 Host 与文件目录，任一缺失则不持久化（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:45）
- `getToolInfo` 经 `getClientForMetadata` 取工具列表，按名查找工具定义（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:269）
- 参数值含 `U+FFFD` 替换字符时视为参数完整性违规（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:320）
- 含 `U+FFFD` 的参数调用在到达 MCP 服务器前被阻止并报错（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:448）
- MCP 工具的 `accessSpec` 声明 `effect` 为 `WRITE`、`boundary` 为 `None`（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:468）
- `invokeAndStreamAsync` 在调用前解析图片保存目标（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:474）
- 包工具声明 `READ` 而 MCP 工具声明 `WRITE`，两者权限边界声明不对称，见走查记录（core/crates/tool/services/src/tools/PackageToolExecutor.rs:68）

### JS 运行时与 ToolPkg IPC

- `PackageManagerJsRuntime` 把 `RuntimePackageManager` 适配为 SDK 的 `JsPackageRuntime` 契约（core/crates/tool/services/src/tools/ToolJsRuntime.rs:35）
- 包语言取 Host 系统语言码并解析为支持的语言码（core/crates/tool/services/src/tools/ToolJsRuntime.rs:57）
- `select_tool` 先要求注册表就绪，再检查包已启用，否则报错 `Package is disabled`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:77）
- `select_tool` 返回工具定义、激活状态 `id` 与 ToolPkg 子包运行时（core/crates/tool/services/src/tools/ToolJsRuntime.rs:83）
- ToolPkg 执行引擎在注册表锁外创建，避免创建过程重入包目录（core/crates/tool/services/src/tools/ToolJsRuntime.rs:100）
- ToolPkg IPC 分发函数名为 `__operit_toolpkg_runtime_dispatch__`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:21）
- 分发函数在 `channel` 为 `$route` 时走 `__operitInvokeToolPkgRouteLocal`，否则走 `__operitInvokeToolPkgIpcLocal`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:26）
- `materializeToolPkgResource` 把 ToolPkg 资源物化为文件，返回 `/operitapp/data` 下的 VFS 路径（core/crates/tool/services/src/tools/ToolJsRuntime.rs:180）
- 资源输出文件名取请求指定值，否则取包声明值，并只保留 `basename`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:129）
- 有容器运行时直接从容器复制资源，否则解析子包运行时复制（core/crates/tool/services/src/tools/ToolJsRuntime.rs:148）
- 三种路径都找不到目标时报错 `ToolPkg resource target not found`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:158）
- `resolveJsToolName` 中工具名已含冒号时原样返回（core/crates/tool/services/src/tools/ToolJsRuntime.rs:187）
- 按 `package_name` 解析时包不存在报错 `Package not found`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:201）
- `package_name` 与 `subpackage_id` 同时给出时报错（core/crates/tool/services/src/tools/ToolJsRuntime.rs:213）
- 按 `subpackage_id` 解析时找首选包名，找不到报错 `ToolPkg subpackage not found`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:206）
- ToolPkg IPC 计时只在 `OPERIT_PROFILE_COMPOSE_STAGES` 环境变量存在时启用（core/crates/tool/services/src/tools/ToolJsRuntime.rs:250）
- 未给目标上下文键且运行时为 `main` 时，默认上下文键为 `toolpkg_main:{目标}`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:307）
- 请求的运行时与上下文键推断的运行时不一致时报错（core/crates/tool/services/src/tools/ToolJsRuntime.rs:324）
- `main` 目标的上下文键必须等于 `toolpkg_main:{目标}`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:331）
- 依赖调用方必须是与提供方不同的前置 `main` 运行时（core/crates/tool/services/src/tools/ToolJsRuntime.rs:345）
- IPC 目标的 ToolPkg 容器不存在时报错 `ToolPkg container not found`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:343）
- IPC 目标包被禁用时报错 `ToolPkg package is disabled`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:350）
- 非 `main` 目标取不到已激活的执行引擎时报错 `ToolPkg runtime is not active`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:388）
- 执行前校验引擎仍是当前引擎，否则报错执行上下文已被释放或替换（core/crates/tool/services/src/tools/ToolJsRuntime.rs:402）
- 依赖调用要求调用方与提供方都启用（core/crates/tool/services/src/tools/ToolJsRuntime.rs:507）
- 调用方必须在 `requires` 中声明对提供方的依赖（core/crates/tool/services/src/tools/ToolJsRuntime.rs:515）
- 提供方版本必须落在调用方声明的 `minVersion` 与 `maxVersion` 范围内，否则报错 `Dependency version mismatch`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:527）
- 提供方必须发布 `public_api`，否则报错（core/crates/tool/services/src/tools/ToolJsRuntime.rs:538）
- 依赖方法必须在提供方的 `publicApis` 中，否则报错 `Public API not found`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:547）
- 上下文键 `toolpkg_main:` 前缀对应 `main` 运行时，`toolpkg_provider:` 对应 `provider` 运行时（core/crates/tool/services/src/tools/ToolJsRuntime.rs:554）
- 上下文键 `toolpkg_compose:`、`toolpkg_compose_dsl:` 与 `toolpkg_xml_render:` 前缀对应 `ui` 运行时，`toolpkg_sandbox:` 对应 `sandbox` 运行时（core/crates/tool/services/src/tools/ToolJsRuntime.rs:561）
- `requiredText` 要求非空字符串（core/crates/tool/services/src/tools/ToolJsRuntime.rs:578）

## 关键符号

- `PackageToolExecutor` — 单个 SDK 包的工具执行器（core/crates/tool/services/src/tools/PackageToolExecutor.rs:15）
- `PackageManagerJsRuntime` — 包管理器到 SDK JS 运行时契约的适配器（core/crates/tool/services/src/tools/ToolJsRuntime.rs:35）
- `SkillPackage` — 技能记录：名、描述、目录、SKILL.md 路径（core/crates/tool/services/src/tools/skill/SkillPackage.rs:6）
- `SkillManager` — 技能扫描、安装、删除与提示词生成（core/crates/tool/services/src/tools/skill/SkillManager.rs:53）
- `MCPManager` — MCP 服务器注册表与客户端缓存（core/crates/tool/services/src/tools/mcp/MCPManager.rs:20）
- `MCPToolExecutor` — MCP 工具调用执行器（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:339）
- `MCPBridgeClient` — 与 MCP 服务器通信的桥接客户端（core/crates/tool/services/src/tools/mcp/MCPManager.rs:5）
- `ImageSaveTarget` — MCP 图片载荷的文件持久化目标（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:43）
- `JsPackageToolCallRequest` — SDK 包工具调用请求（core/crates/tool/services/src/tools/PackageToolExecutor.rs:97）
- `JsPackageToolCallResult` — SDK 包工具调用结果（core/crates/tool/services/src/tools/PackageToolExecutor.rs:111）
- `TOOLPKG_IPC_DISPATCH_FUNCTION_NAME` — ToolPkg IPC 分发函数名 `__operit_toolpkg_runtime_dispatch__`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:21）

## 调用链

### 包工具调用

1. 模型发 `packageName:toolName` 调用，`PackageToolExecutor::validateParameters` 核对两段格式、包名归属与参数名去重（core/crates/tool/services/src/tools/PackageToolExecutor.rs:35）
2. `invokeAndStreamAsync` 新建 `PackageManagerJsRuntime`，经 Host 的 `js_execution_provider` 创建包执行器（core/crates/tool/services/src/tools/PackageToolExecutor.rs:81）
3. `packageToolCallRequest` 把调用转成 `JsPackageToolCallRequest`（core/crates/tool/services/src/tools/PackageToolExecutor.rs:97）
4. 包执行器执行 JS 工具并返回 `JsPackageToolCallResult`（core/crates/tool/services/src/tools/PackageToolExecutor.rs:86）
5. `packageToolResult` 转回 `ToolResult`（core/crates/tool/services/src/tools/PackageToolExecutor.rs:111）

### 技能激活

1. `SkillManager::refreshAvailableSkills` 扫描 `device` 与 `space` 两个位置（core/crates/tool/services/src/tools/skill/SkillManager.rs:58）
2. 扫描按 `SKILL.md` 优先、`skill.md` 兜底解析元数据，冲突与缺失记入错误集合（core/crates/tool/services/src/tools/skill/SkillManager.rs:156）
3. `getSkillSystemPrompt` 生成含目录树与 `SKILL.md` 全文的激活提示词（core/crates/tool/services/src/tools/skill/SkillManager.rs:405）

### MCP 工具调用

1. 模型发 `server_name:tool_name` 调用，`MCPToolExecutor::invoke` 按冒号切分服务器名与工具名（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:339）
2. `MCPManager::getOrCreateClient` 取缓存客户端或建连（core/crates/tool/services/src/tools/mcp/MCPManager.rs:94）
3. 客户端未激活时报错，提示先用 `use_package` 工具激活该包（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:370）
4. 参数按 `inputSchema.properties` 过滤并按声明类型转换（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:282）
5. `callToolWithArguments` 发起调用，响应按 `content` 项提取为文本（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:386）
6. 超长结果截断并追加提示（core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:81）

### ToolPkg IPC 调用

1. `invokeToolPkgIpc` 确认上下文键与运行时种类一致（core/crates/tool/services/src/tools/ToolJsRuntime.rs:324）
2. 校验容器存在且包已启用，依赖调用须过 `validateDependencyCall`（core/crates/tool/services/src/tools/ToolJsRuntime.rs:343）
3. `main` 目标租用主执行引擎并读主入口脚本，非 `main` 目标取已激活引擎（core/crates/tool/services/src/tools/ToolJsRuntime.rs:388）
4. 执行前校验引擎仍是当前引擎（core/crates/tool/services/src/tools/ToolJsRuntime.rs:402）
5. 引擎执行分发函数，结果经 `decode_js_execution_result_value` 解码（core/crates/tool/services/src/tools/ToolJsRuntime.rs:492）

## 来源

- core/crates/tool/services/src/tools/PackageToolExecutor.rs
- core/crates/tool/services/src/tools/skill/SkillManager.rs
- core/crates/tool/services/src/tools/skill/SkillPackage.rs
- core/crates/tool/services/src/tools/mcp/MCPManager.rs
- core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs
- core/crates/tool/services/src/tools/ToolJsRuntime.rs
