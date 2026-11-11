---
title: MCP 集成
module: plugins
platforms: [all]
sources: [10]
date: 2026-11-11
---

## 概述

- 转成的 `ToolPackage` 的 `category` 为 `MCP`。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:118`
- 工具的 `script` 为 MCPJS 占位脚本，由 `generateScriptPlaceholder` 生成。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:103`
- 占位脚本含服务器名、工具名与 endpoint，标记为 `MCPJS`。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:124`
- MCP 服务器的工具经 `toToolPackage` 转成 `ToolPackage`，成为 Agent 可调用的工具。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:73`
- `MCPToolExecutor` 实现 `AsyncToolExecutor`，承接 Agent 的工具调用。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:424`
- MCP 服务器的本地配置由 `MCPLocalServer` 管理。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:12`
- MCP 服务器的安装由 `MCPRepository` 负责。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:25`
- MCP 服务器的运行期注册表与桥接客户端缓存由 `MCPManager` 持有。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:9`
- 执行路径独立：MCP 走 `MCPToolExecutor`，不走 ToolPkg 脚本执行，ToolPkg 的总览见 [[plugin-toolpkg-overview|ToolPkg 2.0.0 总览]]。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:424`

## AI 速览

- `MCPManager` — 进程内共享的服务器注册表与桥接客户端缓存。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:9`
- `MCPServerConfig` — 一台 MCP 服务器的注册配置。`core/crates/tool/services/src/tools/mcp/MCPServerConfig.rs:6`
- `MCPPackage` — 一台服务器的工具集合视图。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:11`
- `MCPTool` — 一个 MCP 工具的名称、描述与参数。`core/crates/tool/services/src/tools/mcp/MCPTool.rs:4`
- `MCPToolParameter` — 一个 MCP 工具参数的名称、类型、描述、必填与默认值。`core/crates/tool/services/src/tools/mcp/MCPToolParameter.rs:4`
- `MCPToolExecutor` — MCP 工具的执行器，实现 `AsyncToolExecutor`。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:424`
- `MCPLocalServer` — MCP 服务器配置、元数据与运行状态的本地存储。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:12`
- `MCPRepository` — MCP 服务器的安装仓库。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:25`
- `MCPConfig` — 本地 MCP 配置文档，含服务器表与插件元数据表。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:18`
- `ServerConfig` — 一台服务器的启动命令或远程地址等部署字段。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:26`
- `ServerStatus` — 一台服务器的运行状态与缓存工具。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:56`
- `MCPBridgeClient` — 与一台 MCP 服务器通信的桥接客户端。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:30`
- 主入口函数：MCPManager 的 `getInstance`。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:25`
- 数据流向一句话：工具元数据经 `toToolPackage` 转成 `ToolPackage` 供 Agent 调用。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:73`

## 核心机制

- mcp 模块导出 `MCPPackage`、`MCPManager`、`MCPServerConfig`。`core/crates/tool/services/src/tools/mcp/mod.rs:5`
- mcp 模块导出 `MCPTool`、`MCPToolExecutor`、`MCPToolParameter`。`core/crates/tool/services/src/tools/mcp/mod.rs:14`
- mcp_runtime 模块导出 `MCPLocalServer`、`MCPRepository` 与 `plugins`。`core/crates/tool/services/src/tools/mcp_runtime/mod.rs:4`
- `MCPServerConfig` 的字段为 `name`、`endpoint`、`description`、`capabilities`、`extraData`。`core/crates/tool/services/src/tools/mcp/MCPServerConfig.rs:6`
- MCPManager 的 `registerServerFromEndpoint` 从服务器名、endpoint 与描述注册服务器。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:170`
- 从 endpoint 注册服务器时，默认 `capabilities` 含 `"tools"`。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:182`
- MCPManager 的 `registerServer` 注册或替换服务器配置并清除该服务器的失败原因。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:159`
- 注册服务器时，该服务器的 `clientCache` 缓存客户端被移除。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:165`
- MCPManager 的 `getInstance` 返回进程内共享的单例管理器。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:25`
- MCPLocalServer 的 `addOrUpdateMCPServer` 添加或替换命令型服务器条目。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:170`
- `addOrUpdateMCPServer` 在命令为空时返回错误。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:175`
- MCPLocalServer 的 `addOrUpdateMCPServerConfig` 先经 `sanitizeServerConfig` 校验再添加或替换完整服务器配置。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:214`
- 在 `command` 为空且 `url` 缺失时判定配置无效。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:600`
- MCPLocalServer 的 `mergeConfigFromJson` 从 JSON 配置导入服务器条目，`mcpServers` 为空时返回错误。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:251`
- 返回 `addedCount` 作为成功写入的服务器条目数（含覆盖同名已有条目）。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:270`
- MCPLocalServer 的 `getConfigFilePath` 返回配置文件的绝对路径。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:276`
- MCPLocalServer 的 `getConfigDirectory` 返回本地 MCP 插件运行文件目录。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:282`
- MCPLocalServer 的 `removeMCPServer` 删除服务器配置、元数据与运行状态。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:226`
- 删除服务器时，该服务器的 `pluginDir` 经 `deleteFile` 一并删除。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:238`
- MCPLocalServer 的 `isServerEnabled` 按 `disabled` 取反，未配置的服务器返回 `true`。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:451`
- MCPLocalServer 的 `setServerEnabled` 通过改写 `disabled` 启用或禁用服务器。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:460`
- MCPLocalServer 的 `isServerLikelyRunning` 按 `lastStartTime` 大于 0 且不早于 `lastStopTime` 判断服务器在运行。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:446`
- 只在 `toolsCachedTime` 距今不足 24 小时时认可缓存。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:417`
- MCPLocalServer 的 `cacheServerTools` 存储某服务器最新发现的工具。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:384`
- MCPLocalServer 的 `getCachedTools` 返回某服务器缓存的工具元数据。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:394`
- 缓存工具时，`toolsCachedTime` 更新为当前时间。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:370`
- MCPLocalServer 的 `getServerStatus` 返回单个服务器的运行状态。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:430`
- MCPLocalServer 的 `getAllServerStatus` 返回全部服务器的运行状态。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:436`
- MCPManager 的 `getLastConnectionFailureReason` 返回某服务器最近一次连接失败详情。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:65`
- MCPManager 的 `unregisterServer` 移除服务器配置与失败原因并断开缓存客户端。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:190`
- MCPManager 的 `shutdown` 断开全部缓存的桥接客户端。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:201`
- MCPRepository 的 `installMCPServerWithObject` 从仓库 URL 与元数据对象安装 MCP 服务器。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:79`
- MCPRepository 的 `installMCPServerFromZip` 从本地 zip 与元数据对象安装 MCP 服务器。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:100`
- `installMCPServerWithObjectForFlutter` 供 Flutter 桥调用，从仓库 URL 安装 MCP 服务器。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:121`
- `installMCPServerFromZipForFlutter` 供 Flutter 桥调用，从本地 zip 安装 MCP 服务器。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:143`
- `extractOwnerAndRepo` 只接受 `github.com` 及其子域。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:501`
- 仓库 zip 按默认分支从 GitHub 归档地址下载。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:325`
- `getGithubDefaultBranch` 查询 `api.github.com` 的仓库接口取默认分支。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:550`
- 仓库下载的 `CONNECT_TIMEOUT_SECONDS` 为 15 秒、`READ_TIMEOUT_SECONDS` 为 30 秒。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:20`
- `resolvePluginRoot` 要求归档解压后恰好含一个根目录。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:338`
- `deployInstalledPlugin` 在 `mcpConfig` 为空时从项目生成配置。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:367`
- 安装部署时，插件的服务器配置经 `addOrUpdateMCPServerConfig` 写入。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:378`
- 安装部署时，插件元数据经 `savePluginMetadata` 保存。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:379`
- 安装部署完成后调用 `reloadConfigurations` 重载配置。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:380`
- 部署步骤失败时安装返回 `InstallResult` 的 `Error`。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:88`
- `InstallResult` 分 `Success` 与 `Error` 两种结果。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:35`
- `InstallProgress` 含 `Preparing`、`Downloading`、`Extracting` 进度事件。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:48`
- `InstallProgress` 含 `Finished` 进度事件。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:48`
- MCPLocalServer 的 `readMCPConfig` 从 `ExtensionStore` 的 `mcp` 记录读取配置。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:681`
- 同一服务器 id 出现在两处时报 MCP ownership conflict 错误。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:689`
- `scope` 为 `space` 的记录只接受远程服务器：`url` 缺失或为空、或 `command` 非空时写入均被拒（同时声明 `url` 与 `command` 也会被拒），报错为 `Local MCP can only belong to this device:` 后接记录 id。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:709`
- 导入的每台服务器恰好声明 `command` 与 `url` 其一，否则返回错误。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:762`
- `scope` 为 `space` 时命令型本地服务器导入被拒绝，报错为 `Local MCP can only belong to this device:` 后接服务器 id。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:767`
- `scope` 为 `space` 的导入完成后调用 `moveScope` 迁移记录归属。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:779`
- 已存在的服务器 id 重复导入时返回 MCP already exists 错误。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:755`
- 缺失元数据的服务器会被补一份默认 `metadata`。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:661`
- 补全的默认元数据以服务器 id 生成显示名，`author` 为 `Unknown`、`version` 为 `1.0.0`。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:666`
- MCPLocalServer 的 `exportConfigAsJson` 把 MCP 配置与服务器状态导出为一个 JSON 文档。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:527`
- MCPLocalServer 的 `importConfigFromJson` 从导出的 JSON 文档导入 MCP 配置与服务器状态。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:539`
- MCPLocalServer 的 `getPluginConfig` 把单个插件服务器配置导出为 JSON 文档。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:493`
- MCPLocalServer 的 `savePluginConfig` 接受完整 MCP 配置 JSON 或单个服务器 JSON 保存插件配置。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:504`
- MCPPackage 的 `loadFromServer` 新建 `MCPBridgeClient` 并连接服务器，连接失败时返回带 `errorMessage` 的 `LoadResult`。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:29`
- 连接失败时，`errorMessage` 取自桥接客户端的 `getLastConnectionFailureDetail`。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:35`
- MCPPackage 的 `fromToolMetadata` 不做同步网络 I/O，直接用传入的工具元数据构建包。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:48`
- `fromToolMetadata` 在工具元数据为空时返回含空 `mcpTools` 的 `MCPPackage` 且无错误。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:49`
- `parseMcpTool` 要求工具含非空 `name`，缺失或为空的工具被丢弃。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:134`
- 从 `inputSchema` 的 `properties` 解析参数，从 `required` 解析必填参数名集合。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:144`
- 在参数未声明类型时默认 `parameter_type` 为 `string`。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:174`
- 按 `required` 集合设定每个参数的 `required`。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:176`
- MCPToolParameter 的 `smartConvert` 按声明的 `typeName` 转换字符串参数：`string` 原样保留，`number` 解析为数值，`boolean` 按是否等于 `true` 转换，`integer` 解析为整数。`core/crates/tool/services/src/tools/mcp/MCPToolParameter.rs:31`
- 声明为 `float` 或 `double` 的字符串解析为浮点数，声明为 `array` 与 `object` 的解析为 JSON 数组与对象。`core/crates/tool/services/src/tools/mcp/MCPToolParameter.rs:40`
- MCPToolParameter 的 `convertParameterValue` 只对字符串值调用 `smartConvert`。`core/crates/tool/services/src/tools/mcp/MCPToolParameter.rs:13`
- MCPToolExecutor 的 `getToolInfo` 从元数据客户端取指定工具的定义。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:266`
- `convertParameterTypes` 在无可用 `properties` 时保留参数而不猜测过滤。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:276`
- `properties` 未声明的顶层参数名被过滤掉。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:286`
- 参数转换按声明的 `type` 调用 `smartConvert` 转换参数值。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:294`
- MCPToolExecutor 的 `validateParameters` 校验工具名是否符合 `server_name:tool_name` 格式。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:425`
- 含 U+FFFD 替换字符的参数在调用前被拦截，不会到达 MCP 服务器。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:452`
- MCPToolExecutor 的 `accessSpec` 声明 `effect` 为 `ToolEffect` 的 `WRITE`、`boundary` 为 `ToolBoundary` 的 `None`。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:466`
- 调用成功时用 `extractContentFromResult` 提取结果内容。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:392`
- 结果中 `content` 之外的字段作为元数据文本保留。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:123`
- 把 `type` 为 `text` 的内容项转为文本。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:150`
- 处理 `image` 内容项。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:163`
- 处理 `resource` 内容项，优先返回其中 `text`。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:214`
- resource 内容项无文本时返回 `uri` 标注。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:222`
- `decodeValidatedImage` 只接受 PNG、JPEG、GIF、WebP 四种图片格式。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:237`
- `registerImageBytes` 把图片字节注册进 `ImagePoolManager` 并返回媒体链接。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:249`
- `imageFileExtension` 按图片格式取文件扩展名，JPEG 取 `jpg`、GIF 取 `gif`、WebP 取 `webp`、其余取 `png`。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:257`
- `save` 把图片写进调用方当前文件目录，文件名为 mcp-{timestampMs}-{uuid}.{extension}。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:59`
- `resolve` 在无 turn 快照时返回 `None`。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:46`
- `resolve` 取 turn 快照的文件目录作为图片保存目标。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:46`
- `truncateResult` 按 `ToolExecutionLimits` 的 `MAX_TEXT_RESULT_LENGTH` 截断过长结果。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:81`

## 关键符号

- `MCPManager` — 进程内共享的服务器注册表与桥接客户端缓存。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:9`
- MCPManager 的 `getInstance` — 返回共享管理器。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:25`
- MCPManager 的 `registerServer` — 注册或替换服务器配置。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:159`
- MCPManager 的 `registerServerFromEndpoint` — 从 endpoint 注册服务器。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:170`
- MCPManager 的 `getOrCreateClient` — 取缓存客户端或新建并连接。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:84`
- MCPManager 的 `getClientForMetadata` — 取元数据客户端，不发起网络 I/O。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:75`
- MCPManager 的 `getRegisteredServers` — 返回全部已注册服务器配置。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:55`
- MCPManager 的 `isServerRegistered` — 判断服务器是否已注册。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:45`
- MCPManager 的 `getLastConnectionFailureReason` — 取最近连接失败详情。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:65`
- MCPManager 的 `unregisterServer` — 移除服务器并断开客户端。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:190`
- MCPManager 的 `shutdown` — 断开全部缓存客户端。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:201`
- `MCPServerConfig` — 服务器注册配置，字段 `name`、`endpoint`、`description`、`capabilities`、`extraData`。`core/crates/tool/services/src/tools/mcp/MCPServerConfig.rs:6`
- `MCPPackage` — 一台服务器的工具集合视图。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:11`
- MCPPackage 的 `loadFromServer` — 连接服务器并加载工具。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:29`
- MCPPackage 的 `fromToolMetadata` — 用工具元数据构建包，不做网络 I/O。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:48`
- MCPPackage 的 `toToolPackage` — 把 MCP 工具转成 `ToolPackage`。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:73`
- `MCPTool` — 工具的名称、描述与参数。`core/crates/tool/services/src/tools/mcp/MCPTool.rs:4`
- `MCPToolParameter` — 工具参数的名称、类型、描述、必填与默认值。`core/crates/tool/services/src/tools/mcp/MCPToolParameter.rs:4`
- MCPToolParameter 的 `smartConvert` — 按声明类型转换字符串参数。`core/crates/tool/services/src/tools/mcp/MCPToolParameter.rs:26`
- `MCPToolExecutor` — MCP 工具的执行器。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:67`
- MCPToolExecutor 的 `invoke` — 按 `server_name:tool_name` 分发调用。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:341`
- MCPToolExecutor 的 `validateParameters` — 校验工具名格式与参数是否含 U+FFFD 替换字符。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:425`
- MCPToolExecutor 的 `accessSpec` — 声明写效应与无边界。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:466`
- `MCPLocalServer` — 配置、元数据与运行状态的本地存储。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:12`
- `MCPConfig` — 本地 MCP 配置文档。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:18`
- `ServerConfig` — 服务器部署字段。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:26`
- `PluginMetadata` — 插件展示元数据。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:46`
- `ServerStatus` — 服务器运行状态。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:56`
- `CachedToolInfo` — 缓存的工具元数据。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:72`
- MCPLocalServer 的 `addOrUpdateMCPServer` — 添加或替换命令型服务器。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:170`
- MCPLocalServer 的 `addOrUpdateMCPServerConfig` — 添加或替换完整服务器配置。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:209`
- MCPLocalServer 的 `removeMCPServer` — 删除服务器及其本地文件。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:226`
- MCPLocalServer 的 `mergeConfigFromJson` — 从 JSON 导入服务器条目。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:251`
- MCPLocalServer 的 `mergeConfigFromJsonWithScope` — 按作用域导入服务器条目。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:742`
- MCPLocalServer 的 `isServerEnabled` — 判断服务器是否启用。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:451`
- MCPLocalServer 的 `setServerEnabled` — 启用或禁用服务器。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:460`
- MCPLocalServer 的 `hasValidToolCache` — 判断工具缓存是否有效。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:403`
- MCPLocalServer 的 `getConfigFilePath` — 返回配置文件路径。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:276`
- MCPLocalServer 的 `getConfigDirectory` — 返回插件目录。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:282`
- MCPLocalServer 的 `exportConfigAsJson` — 导出配置与状态。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:527`
- MCPLocalServer 的 `importConfigFromJson` — 导入配置与状态。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:539`
- `MCPRepository` — MCP 服务器的安装仓库。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:25`
- MCPRepository 的 `installMCPServerWithObject` — 从仓库 URL 安装。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:79`
- MCPRepository 的 `installMCPServerFromZip` — 从本地 zip 安装。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:100`
- `InstallResult` — 安装结果，`Success` 或 `Error`。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:35`
- `InstallProgress` — 安装进度事件。`core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs:44`
- `MCPBridgeClient` — 与一台 MCP 服务器通信的桥接客户端。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:30`

## 调用链

1. 配置写入：MCPLocalServer 的 `addOrUpdateMCPServer` 添加或替换命令型服务器条目。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:170`
2. 配置读取：`readMCPConfig` 从 `ExtensionStore` 的 `mcp` 记录读取配置。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:681`
3. 配置写回时，`scope` 为 `space` 的记录只接受远程服务器（`url` 缺失或为空、或 `command` 非空时均被拒）。`core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs:709`
4. 注册：MCPManager 的 `registerServer` 注册或替换服务器配置。`core/crates/tool/services/src/tools/mcp/MCPManager.rs:159`
5. 发现：MCPPackage 的 `loadFromServer` 连接服务器并取工具元数据。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:29`
6. 转换：MCPPackage 的 `toToolPackage` 把 MCP 工具转成 `ToolPackage`。`core/crates/tool/services/src/tools/mcp/MCPPackage.rs:73`
7. 激活：未激活的服务调用时返回错误，提示用 `use_package` 工具以包名激活。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:370`
8. 分发：MCPToolExecutor 的 `invoke` 把工具名按冒号切分，取服务器名与工具名。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:338`
9. 连接：通过 `getOrCreateClient` 获取桥接客户端。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:351`
10. 执行：调用 `callToolWithArguments` 执行远程工具。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:386`
11. 结果提取：成功时用 `extractContentFromResult` 提取结果内容。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:392`
12. 结果截断：提取出的内容经 `truncateResult` 截断。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:400`
13. 图片：图片内容经 `registerImageBytes` 注册进 `ImagePoolManager` 并返回媒体链接。`core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs:249`

## 来源

- `core/crates/tool/services/src/tools/mcp/MCPManager.rs`
- `core/crates/tool/services/src/tools/mcp/MCPPackage.rs`
- `core/crates/tool/services/src/tools/mcp/MCPToolExecutor.rs`
- `core/crates/tool/services/src/tools/mcp/MCPToolParameter.rs`
- `core/crates/tool/services/src/tools/mcp/MCPServerConfig.rs`
- `core/crates/tool/services/src/tools/mcp/MCPTool.rs`
- `core/crates/tool/services/src/tools/mcp/mod.rs`
- `core/crates/tool/services/src/tools/mcp_runtime/MCPLocalServer.rs`
- `core/crates/tool/services/src/tools/mcp_runtime/MCPRepository.rs`
- `core/crates/tool/services/src/tools/mcp_runtime/mod.rs`
