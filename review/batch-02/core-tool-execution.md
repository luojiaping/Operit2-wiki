---
title: 工具系统——执行与注册
module: core
platforms: [all]
sources: [core/crates/tool/README.md, core/crates/tool/services/src/lib.rs, core/crates/tool/services/src/ToolExecutionManager.rs, core/crates/tool/services/src/tools/AIToolHandler.rs, core/crates/tool/services/src/tools/ToolRegistration.rs, core/crates/tool/services/src/tools/ToolPermissionSystem.rs]
date: 2026-11-11
---

# 工具系统——执行与注册

## 概述

tool 域拥有工具契约、工具执行、内置工具、skills、包、MCP 与工具脚本。`core/crates/tool/README.md:3`
services 是当前聚合工具 crate，包含工具执行、内置工具、权限、skills、包、MCP 与 JavaScript 工具支持。`core/crates/tool/README.md:9`
README 的 Target Split 规划把 services 聚合拆为 contracts、runtime、builtin、skill、package、mcp 与 javascript 七个 crate。`core/crates/tool/README.md:13`
`executeInvocations` 是批处理主入口。`core/crates/tool/services/src/ToolExecutionManager.rs:359`
包工具由 `PackageToolExecutor` 执行，其内部实现见 [[core-tool-packages-mcp|工具系统——包、技能与 MCP]]。`core/crates/tool/services/src/tools/AIToolHandler.rs:848`

## AI 速览

`extractToolInvocations` — 从助手响应提取 XML 风格的工具调用。`core/crates/tool/services/src/ToolExecutionManager.rs:314`
`ToolRuntimeContext` — 本次执行的上下文：调用方聊天、参与者、工作区与曝光模式。`core/crates/tool/services/src/ToolExecutionManager.rs:42`
`AITool` — 模型请求的解析形态：工具名与名值对参数。`core/crates/tool/services/src/ToolExecutionManager.rs:96`
`ToolCall` — 结构化参数形态，参数以名值对映射保存。`core/crates/tool/services/src/ToolExecutionManager.rs:103`
`resolveTarget` — 解析代理入口，把代理请求还原为目标工具调用。`core/crates/tool/services/src/ToolExecutionManager.rs:110`
`ToolExposureMode` — 曝光模式：`FULL` 与 `CLI` 两档。`core/crates/tool/services/src/ToolExecutionManager.rs:36`
`ToolExecutionBatch` — 汇总结果、回填消息、展示消息与路由变更意图。`core/crates/tool/services/src/ToolExecutionManager.rs:264`
`executeInvocations` — 批处理主入口。`core/crates/tool/services/src/ToolExecutionManager.rs:359`
`executeToolInvocation` — 单次执行入口。`core/crates/tool/services/src/tools/AIToolHandler.rs:1063`
`AIToolHandler` — 注册表与执行管线：注册、可见性、hook、权限预检、执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:80`
`addToolHook` — 按 hook id 去重注册 hook。`core/crates/tool/services/src/tools/AIToolHandler.rs:322`
`AiPermissionMode` — 权限模式三档：`ReadOnly`、`WorkspaceWrite`、`Full`。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:16`
`RegisteredToolExecutor` — 四种执行契约：`Alias`、`Synchronous`、`Asynchronous`、`Shared`。`core/crates/tool/services/src/ToolExecutionManager.rs:728`
`ToolAccessSpec` — 访问声明：效果与边界。`core/crates/tool/services/src/ToolExecutionManager.rs:794`
`registerAllTools` — 先注册公开工具，再注册内部工具。`core/crates/tool/services/src/tools/ToolRegistration.rs:61`
`get_tool_catalog` — 工具目录入口。`core/crates/tool/services/src/tools/AIToolHandler.rs:1287`
数据流向：模型响应 → 解析 → 批处理 → 逐个执行 → 结果回填，步骤见 ## 调用链。

## 核心机制

### 解析

`extractToolInvocations` 从助手响应中提取 XML 风格的工具调用。`core/crates/tool/services/src/ToolExecutionManager.rs:314`
工具调用参数从 `<param>` 标签解析，参数名取自标签的 name 属性。`core/crates/tool/services/src/ToolExecutionManager.rs:320`
`unescapeXml` 剥离参数值首尾的 `<![CDATA[` 与 `]]>` 标记。`core/crates/tool/services/src/ToolExecutionManager.rs:676`
`unescapeXml` 还原 `&lt;`、`&gt;`、`&amp;`、`&quot;`、`&apos;` 五种 XML 转义。`core/crates/tool/services/src/ToolExecutionManager.rs:686`
每个 `ToolInvocation` 保留工具请求、原始文本 `rawText` 与响应内起止位置 `responseLocation`。`core/crates/tool/services/src/ToolExecutionManager.rs:251`

### 执行上下文

`ToolRuntimeContext` 记录调用方聊天、参与者、工作区路径、工作区目录列表与曝光模式。`core/crates/tool/services/src/ToolExecutionManager.rs:42`
`ToolRuntimeContext` 的 `extensionOwner` 是本次执行捕获的原生认证配置所有者。`core/crates/tool/services/src/ToolExecutionManager.rs:49`
`ToolRuntimeContext` 的 `executionData` 保存当前回合的执行数据，不持久化到消息上。`core/crates/tool/services/src/ToolExecutionManager.rs:51`
`validateExecutionContext` 要求 `extensionOwner` 非空且无首尾空白，否则拒绝进入策略分发。`core/crates/tool/services/src/ToolExecutionManager.rs:67`
两个任务局部变量保存上下文：`TOOL_RUNTIME_CONTEXT` 与 `TOOL_INVOCATION_CONTEXT`。`core/crates/tool/services/src/ToolExecutionManager.rs:28`
`ToolInvocationContext::capture` 优先取当前任务局部的调用上下文。`core/crates/tool/services/src/ToolExecutionManager.rs:189`
无任务局部上下文时，`capture` 回退到 handler 自身的 `invocationSnapshot`。`core/crates/tool/services/src/ToolExecutionManager.rs:192`
`withHook` 把 hook id 记入快照的 `activeHooks`，`isHookActive` 查询该集合。`core/crates/tool/services/src/ToolExecutionManager.rs:222`

### 代理与曝光

`resolveTarget` 只解析 `PACKAGE_PROXY_TOOL_NAME` 与 `CLI_PROXY_TOOL_NAME` 两个代理入口，其他工具名原样通过。`core/crates/tool/services/src/ToolExecutionManager.rs:110`
CLI 代理 `proxy` 要求当前回合曝光模式为 CLI，否则返回不可用错误。`core/crates/tool/services/src/ToolExecutionManager.rs:112`
代理信封只允许 `tool_name`、`params` 与四个 `__operit_package_*` 参数，其余参数报错。`core/crates/tool/services/src/ToolExecutionManager.rs:116`
代理的目标工具名必须是非空且无首尾空白的精确文本。`core/crates/tool/services/src/ToolExecutionManager.rs:122`
代理不能以另一个代理或目录条目为目标。`core/crates/tool/services/src/ToolExecutionManager.rs:123`
`PACKAGE_PROXY_TOOL_NAME` 的目标必须写成 `packageName:toolName` 格式，且方法名内不能再含冒号。`core/crates/tool/services/src/ToolExecutionManager.rs:124`
代理的 `params` 必须是 JSON 对象或其旧版文本编码，否则报错。`core/crates/tool/services/src/ToolExecutionManager.rs:134`
`ToolExposureMode` 分 `FULL` 与 `CLI` 两档：FULL 用原生工具调用标记与完整注册目录，CLI 用命令行代理模式的受限公开面。`core/crates/tool/services/src/ToolExecutionManager.rs:36`
CLI 模式下调用非公开工具时返回失败结果。`core/crates/tool/services/src/ToolExecutionManager.rs:616`
FULL 模式下调用 CLI 公开工具时，返回 CLI 模式不可用错误。`core/crates/tool/services/src/ToolExecutionManager.rs:623`
CLI 公开工具只有 `CLI_SEARCH_TOOL_NAME` 与 `CLI_PROXY_TOOL_NAME` 两个。`core/crates/tool/services/src/ToolExecutionManager.rs:644`

### 批处理

`executeInvocations` 在批处理开始前校验 `ToolRuntimeContext`。`core/crates/tool/services/src/ToolExecutionManager.rs:381`
`executeInvocations` 入口调用 `registerDefaultTools` 注册内置工具。`core/crates/tool/services/src/ToolExecutionManager.rs:404`
`executeInvocations` 按顺序逐个执行调用，串行处理整批。`core/crates/tool/services/src/ToolExecutionManager.rs:423`
批处理执行前，每个调用先经 `injectPackageCallContext` 注入包调用上下文。`core/crates/tool/services/src/ToolExecutionManager.rs:413`
批处理中每个调用经 `executeToolInvocation` 以 `ToolExecutionPolicy::Ai` 执行。`core/crates/tool/services/src/ToolExecutionManager.rs:435`
多结果合并时，失败项文本标为 `Step error`。`core/crates/tool/services/src/ToolExecutionManager.rs:458`
多个原始结果以换行拼接成一个合并字符串。`core/crates/tool/services/src/ToolExecutionManager.rs:466`
只有显示名为 `switch_core`、结果工具名为 `switch_core` 且成功时，才生成 `RouteChangeIntent`。`core/crates/tool/services/src/ToolExecutionManager.rs:518`
`RouteChangeIntent` 的 `targetNodeId` 取自结果文本去首尾空白后的内容。`core/crates/tool/services/src/ToolExecutionManager.rs:526`
同一批中后一个调用的路由意图会覆盖前一个。`core/crates/tool/services/src/ToolExecutionManager.rs:480`
`ToolExecutionBatch::new` 用 `buildToolResultMessage` 生成回填模型的消息，用 `formatToolResultForDisplay` 生成展示消息。`core/crates/tool/services/src/ToolExecutionManager.rs:273`
`ToolExecutionBatch` 汇总结果、回填消息、展示消息与路由变更意图。`core/crates/tool/services/src/ToolExecutionManager.rs:264`

### 调用管线（单次执行）

`executeToolInvocation` 先用 `ToolInvocationContext::capture` 捕获调用方上下文，再在该上下文作用域内执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:1068`
`resolveTarget` 解析失败时返回失败结果，不抛错中断批处理。`core/crates/tool/services/src/tools/AIToolHandler.rs:1081`
`resolveTarget` 失败路径在 AI 策略下仍通知请求与结果 hook。`core/crates/tool/services/src/tools/AIToolHandler.rs:1088`
曝光检查以原始请求判定，在代理目标解析之后、拦截检查之前执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:1121`
拦截检查在曝光检查之后、激活之前执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:1126`
工具未注册时先尝试激活，仍不存在返回 `Tool not found` 失败结果。`core/crates/tool/services/src/tools/AIToolHandler.rs:1131`
`getToolExecutorOrActivate` 对包名:工具名先准备 MCP 包。`core/crates/tool/services/src/tools/AIToolHandler.rs:749`
`acquireToolExecutor` 取执行器租约时先克隆注册项，不持有注册表锁等待执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:737`
AI 调用才做权限预检：`prepared.access` 为 `Some` 时调用 `executeAccessPreflightAsync`。`core/crates/tool/services/src/tools/AIToolHandler.rs:1142`
执行器真正调用在 `prepared.invoke`。`core/crates/tool/services/src/tools/AIToolHandler.rs:1148`
内置工具执行器返回的结果必须与请求同名，失败结果必须带 `error`。`core/crates/tool/services/src/tools/AIToolHandler.rs:1153`
执行器返回空结果时，整个调用以错误结束。`core/crates/tool/services/src/tools/AIToolHandler.rs:1158`
`executeTool` 以 `Direct` 策略执行并取最后一个结果。`core/crates/tool/services/src/tools/AIToolHandler.rs:1199`
`Direct` 策略的调用不经过 AI 生命周期 hook 与权限预检。`core/crates/tool/services/src/ToolExecutionManager.rs:290`

### Hook

`addToolHook` 按 hook id 去重，同 id 的 hook 只注册一次。`core/crates/tool/services/src/tools/AIToolHandler.rs:322`
`notifyHooks` 跳过当前已激活的 hook，避免同一 hook 递归重入。`core/crates/tool/services/src/tools/AIToolHandler.rs:362`
`onToolCallRequested` 在拦截检查前通知各 hook。`core/crates/tool/services/src/tools/AIToolHandler.rs:371`
`checkToolInterception` 逐个询问 hook，跳过已激活的 hook，任一 `Block` 即返回该决定。`core/crates/tool/services/src/tools/AIToolHandler.rs:387`
hook 拦截产生的失败结果 `error` 为 hook 给出的原因。`core/crates/tool/services/src/tools/AIToolHandler.rs:407`
`ToolInvocationLifecycle` 的 `Drop` 保证执行结束时恰好发布一次 `onToolExecutionFinished`。`core/crates/tool/services/src/tools/AIToolHandler.rs:145`

### 执行器契约

`ToolExecutor` 要求实现 `validateParameters`、`accessSpec` 与 `invokeAndStream` 三个方法。`core/crates/tool/services/src/ToolExecutionManager.rs:694`
`AsyncToolExecutor` 的 `invokeAndStreamAsync` 接收 `ToolInvocationContext`。`core/crates/tool/services/src/ToolExecutionManager.rs:711`
`SharedToolExecutor` 的 `prepare` 一次解码校验，`checkAccess` 为真时才声明 `access`。`core/crates/tool/services/src/ToolExecutionManager.rs:721`
`RegisteredToolExecutor` 分 `Alias`、`Synchronous`、`Asynchronous`、`Shared` 四种执行契约。`core/crates/tool/services/src/ToolExecutionManager.rs:728`
`Alias` 契约必须在取执行器前解析，直接 `prepare` 会报错。`core/crates/tool/services/src/ToolExecutionManager.rs:755`
同步与异步执行器在 `prepare` 时先校验参数，校验失败返回错误信息。`core/crates/tool/services/src/ToolExecutionManager.rs:759`
`prepare` 只在 `checkAccess` 为真时调用 `accessSpec` 取访问声明。`core/crates/tool/services/src/ToolExecutionManager.rs:761`
`ToolEffect` 只有 `READ` 与 `WRITE` 两档。`core/crates/tool/services/src/ToolExecutionManager.rs:776`
`ToolBoundary` 分 `None`、`FilePath` 与 `FilePair` 三种，文件边界各带读写效果。`core/crates/tool/services/src/ToolExecutionManager.rs:787`
`ToolAccessSpec` 由 `effect` 与 `boundary` 组成。`core/crates/tool/services/src/ToolExecutionManager.rs:794`

### 注册

`registerAllTools` 先注册公开工具，再注册内部工具。`core/crates/tool/services/src/tools/ToolRegistration.rs:61`
`registerDefaultTools` 在 `defaultToolsRegistered` 为真时直接返回。`core/crates/tool/services/src/tools/AIToolHandler.rs:711`
`registerDefaultTools` 完成注册后把 `defaultToolsRegistered` 置为真。`core/crates/tool/services/src/tools/AIToolHandler.rs:724`
`registerBuiltinTool` 重复注册同名内置工具时断言失败。`core/crates/tool/services/src/tools/AIToolHandler.rs:576`
`registerToolWithVisibility` 拒绝以内置工具名注册，要求内置工具走 `registerBuiltinTool`。`core/crates/tool/services/src/tools/AIToolHandler.rs:599`
工具可见性分 `PUBLIC` 与 `INTERNAL` 两档。`core/crates/tool/services/src/tools/AIToolHandler.rs:50`
`getPublicToolNames` 只返回可见性为 `PUBLIC` 的工具名。`core/crates/tool/services/src/tools/AIToolHandler.rs:536`
`getInternalToolNames` 只返回可见性为 `INTERNAL` 的工具名。`core/crates/tool/services/src/tools/AIToolHandler.rs:548`
`getAllToolNames` 返回全部已注册工具名，不论可见性。`core/crates/tool/services/src/tools/AIToolHandler.rs:443`
`BuiltinToolName::PackageProxy` 以 `Alias` 契约注册为内部工具。`core/crates/tool/services/src/tools/ToolRegistration.rs:932`
包工具按 `包名:工具名` 的格式注册。`core/crates/tool/services/src/tools/AIToolHandler.rs:834`
A2A 包的工具用 `A2AToolExecutor` 执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:836`
MCP 包的工具用 `MCPToolExecutor` 执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:840`
其余包工具用 `PackageToolExecutor` 执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:848`
`registerPackageActivationTool` 注册 `BuiltinToolName::UsePackage` 工具。`core/crates/tool/services/src/tools/ToolRegistration.rs:70`
`BuiltinToolName::UsePackage` 执行时先准备 MCP 包。`core/crates/tool/services/src/tools/ToolRegistration.rs:84`
`use_package` 激活包成功后调用 `registerPackageTools` 注册该包的工具。`core/crates/tool/services/src/tools/ToolRegistration.rs:103`
`sleep` 工具无 `duration_ms` 参数时默认等待 1000 毫秒。`core/crates/tool/services/src/tools/ToolRegistration.rs:114`
文件工具以异步契约注册为 `PUBLIC` 工具。`core/crates/tool/services/src/tools/ToolRegistration.rs:1530`
跨节点文件传输端点注册为内部异步工具。`core/crates/tool/services/src/tools/ToolRegistration.rs:1504`
`unregisterTool` 删除工具注册与其可见性记录。`core/crates/tool/services/src/tools/AIToolHandler.rs:260`
`unregisterMcpServerTools` 按 `服务器名:` 前缀批量删除该 MCP 服务器的工具。`core/crates/tool/services/src/tools/AIToolHandler.rs:274`

### 权限

`AiPermissionMode` 分 `ReadOnly`、`WorkspaceWrite` 与 `Full` 三档。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:16`
未保存过权限模式时，`getAiPermissionMode` 默认返回 `WorkspaceWrite`。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:23`
权限模式以 `ai_permission_mode` 为键持久化。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:110`
`ReadOnly` 只允许 `READ` 效果，`WorkspaceWrite` 与 `Full` 允许全部效果。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:43`
沙箱逃逸审批先查会话批准集：同一工具在本会话已批准则直接放行。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:213`
未安装交互审批回调时，审批请求默认拒绝。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:229`
`ALLOW_SESSION` 把工具名记入会话批准集，本会话内后续调用不再询问。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:249`
`checkSandboxEscapeApprovalAsync` 是沙箱逃逸审批的异步入口。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:191`
`Full` 模式下工作区边界检查直接通过。`core/crates/tool/services/src/tools/AIToolHandler.rs:960`
`READ` 效果的文件路径检查直接通过，不要求工作区。`core/crates/tool/services/src/tools/AIToolHandler.rs:985`
`node:` 限定路径在目标设备上按其自身能力模式执行，不受本地工作区边界限制。`core/crates/tool/services/src/tools/AIToolHandler.rs:1003`
写文件路径不在当前工作区目录内时，返回 `RequiresApproval` 而不是直接拒绝。`core/crates/tool/services/src/tools/AIToolHandler.rs:1055`
`WorkspaceWrite` 模式下，非文件边界的 `WRITE` 操作仍需一次审批。`core/crates/tool/services/src/tools/AIToolHandler.rs:920`
权限模式不允许该效果时，执行前发起沙箱逃逸审批。`core/crates/tool/services/src/tools/AIToolHandler.rs:885`
工作区边界要求审批时，执行前发起沙箱逃逸审批。`core/crates/tool/services/src/tools/AIToolHandler.rs:890`
用户拒绝审批时返回 `User cancelled the tool execution.` 错误。`core/crates/tool/services/src/tools/AIToolHandler.rs:904`
`executeAccessPreflightAsync` 读取当前权限模式失败时，返回失败结果而不是抛错。`core/crates/tool/services/src/tools/AIToolHandler.rs:868`

### 包调用上下文注入

`setPackageContextParameter` 先删除模型传入的同名参数，再写入给定值。`core/crates/tool/services/src/ToolExecutionManager.rs:554`
包调用注入覆盖 `PACKAGE_CALLER_NAME_PARAM`、`PACKAGE_CHAT_ID_PARAM` 与 `PACKAGE_CALLER_PARTICIPANT_ID_PARAM` 三个参数。`core/crates/tool/services/src/ToolExecutionManager.rs:579`
`PACKAGE_CALLER_OWNER_PARAM` 的值取自当前回合上下文的 `extensionOwner`。`core/crates/tool/services/src/ToolExecutionManager.rs:588`
包调用上下文注入只处理 `isJsPackageTool` 判定的包工具，非包工具原样返回。`core/crates/tool/services/src/ToolExecutionManager.rs:572`

### 展示名与目录

`resolveDisplayToolName` 对代理工具显示目标工具名。`core/crates/tool/services/src/ToolExecutionManager.rs:531`
工具目录中的内置工具 `source` 为 `builtin`。`core/crates/tool/services/src/tools/AIToolHandler.rs:1318`
工具目录中的包工具 `source` 为 `package`。`core/crates/tool/services/src/tools/AIToolHandler.rs:1358`
`execute_tool_call` 经 `executeToolInvocation` 以 `ToolExecutionPolicy::Direct` 执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:1386`
`reset` 清空注册表与可见性，并把 `defaultToolsRegistered` 重置为假。`core/crates/tool/services/src/tools/AIToolHandler.rs:1207`

## 关键符号

`ToolRuntimeContext` — 执行上下文结构。`core/crates/tool/services/src/ToolExecutionManager.rs:42`
`AITool` — 模型请求的解析形态。`core/crates/tool/services/src/ToolExecutionManager.rs:96`
`ToolCall` — 结构化参数形态。`core/crates/tool/services/src/ToolExecutionManager.rs:103`
`ToolInvocation` — 单次工具调用：请求、原始文本与响应位置。`core/crates/tool/services/src/ToolExecutionManager.rs:251`
`ToolExecutionBatch` — 批处理结果汇总。`core/crates/tool/services/src/ToolExecutionManager.rs:264`
`ToolExposureMode` — 曝光模式枚举。`core/crates/tool/services/src/ToolExecutionManager.rs:33`
`ToolExecutionPolicy` — 执行策略枚举：`Ai` 与 `Direct`。`core/crates/tool/services/src/ToolExecutionManager.rs:287`
`ToolExecutor` — 同步执行器契约。`core/crates/tool/services/src/ToolExecutionManager.rs:694`
`AsyncToolExecutor` — 异步执行器契约。`core/crates/tool/services/src/ToolExecutionManager.rs:705`
`SharedToolExecutor` — 共享执行器契约。`core/crates/tool/services/src/ToolExecutionManager.rs:721`
`RegisteredToolExecutor` — 注册的执行器契约枚举。`core/crates/tool/services/src/ToolExecutionManager.rs:728`
`ToolEffect` — 效果枚举：`READ` 与 `WRITE`。`core/crates/tool/services/src/ToolExecutionManager.rs:776`
`ToolBoundary` — 边界枚举。`core/crates/tool/services/src/ToolExecutionManager.rs:782`
`ToolAccessSpec` — 访问声明结构。`core/crates/tool/services/src/ToolExecutionManager.rs:794`
`AIToolHandler` — 注册表与执行管线。`core/crates/tool/services/src/tools/AIToolHandler.rs:80`
`AIToolHandlerState` — 注册表状态结构。`core/crates/tool/services/src/tools/AIToolHandler.rs:150`
`ToolRegistrationVisibility` — 可见性枚举：`PUBLIC` 与 `INTERNAL`。`core/crates/tool/services/src/tools/AIToolHandler.rs:50`
`ToolPermissionSystem` — 权限系统。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:72`
`AiPermissionMode` — 权限模式枚举。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:16`
`PermissionRequestResult` — 审批结果枚举。`core/crates/tool/services/src/tools/ToolPermissionSystem.rs:54`
`extractToolInvocations` — 解析入口。`core/crates/tool/services/src/ToolExecutionManager.rs:314`
`executeInvocations` — 批处理入口。`core/crates/tool/services/src/ToolExecutionManager.rs:359`
`executeToolInvocation` — 单次执行入口。`core/crates/tool/services/src/tools/AIToolHandler.rs:1063`
`executeTool` — `Direct` 策略执行入口。`core/crates/tool/services/src/tools/AIToolHandler.rs:1199`
`registerAllTools` — 注册全部工具。`core/crates/tool/services/src/tools/ToolRegistration.rs:61`
`registerDefaultTools` — 注册内置工具。`core/crates/tool/services/src/tools/AIToolHandler.rs:708`
`get_tool_catalog` — 工具目录入口。`core/crates/tool/services/src/tools/AIToolHandler.rs:1287`
`execute_tool_call` — JS 工具调用入口。`core/crates/tool/services/src/tools/AIToolHandler.rs:1367`
`reset` — 清空注册表。`core/crates/tool/services/src/tools/AIToolHandler.rs:1207`

## 调用链

1. 模型响应经 `extractToolInvocations` 解析为 `ToolInvocation` 列表。`core/crates/tool/services/src/ToolExecutionManager.rs:314`
2. `executeInvocations` 校验 `ToolRuntimeContext`。`core/crates/tool/services/src/ToolExecutionManager.rs:381`
3. `executeInvocations` 调用 `registerDefaultTools` 注册内置工具。`core/crates/tool/services/src/ToolExecutionManager.rs:404`
4. 每个调用经 `injectPackageCallContext` 注入包调用上下文。`core/crates/tool/services/src/ToolExecutionManager.rs:413`
5. 调用按顺序逐个执行。`core/crates/tool/services/src/ToolExecutionManager.rs:423`
6. 每个调用经 `executeToolInvocation` 以 `ToolExecutionPolicy::Ai` 执行。`core/crates/tool/services/src/ToolExecutionManager.rs:435`
7. `executeToolInvocation` 用 `ToolInvocationContext::capture` 捕获调用方上下文。`core/crates/tool/services/src/tools/AIToolHandler.rs:1068`
8. `resolveTarget` 解析失败时返回失败结果，不抛错中断批处理。`core/crates/tool/services/src/tools/AIToolHandler.rs:1081`
9. 曝光检查以原始请求判定。`core/crates/tool/services/src/tools/AIToolHandler.rs:1121`
10. 拦截检查在曝光检查之后、激活之前执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:1126`
11. 工具未注册时先尝试激活，仍不存在返回 `Tool not found` 失败结果。`core/crates/tool/services/src/tools/AIToolHandler.rs:1131`
12. `getToolExecutorOrActivate` 对包名:工具名先准备 MCP 包。`core/crates/tool/services/src/tools/AIToolHandler.rs:749`
13. `acquireToolExecutor` 取执行器租约。`core/crates/tool/services/src/tools/AIToolHandler.rs:737`
14. 权限预检：`prepared.access` 为 `Some` 时调用 `executeAccessPreflightAsync`。`core/crates/tool/services/src/tools/AIToolHandler.rs:1142`
15. 执行器真正调用在 `prepared.invoke`。`core/crates/tool/services/src/tools/AIToolHandler.rs:1148`
16. 内置工具执行器返回的结果必须与请求同名，失败结果必须带 `error`。`core/crates/tool/services/src/tools/AIToolHandler.rs:1153`
17. `ToolExecutionBatch::new` 生成回填消息与展示消息。`core/crates/tool/services/src/ToolExecutionManager.rs:273`
18. 多个原始结果以换行拼接成一个合并字符串。`core/crates/tool/services/src/ToolExecutionManager.rs:466`
19. 只有显示名为 `switch_core`、结果工具名为 `switch_core` 且成功时，才生成 `RouteChangeIntent`。`core/crates/tool/services/src/ToolExecutionManager.rs:518`
20. `execute_tool_call` 经 `executeToolInvocation` 以 `ToolExecutionPolicy::Direct` 执行。`core/crates/tool/services/src/tools/AIToolHandler.rs:1386`
21. `Direct` 策略的调用不经过 AI 生命周期 hook 与权限预检。`core/crates/tool/services/src/ToolExecutionManager.rs:290`

## 来源

- `core/crates/tool/README.md`（13 行，100% 已读）
- `core/crates/tool/services/src/lib.rs`（10 行，100% 已读）
- `core/crates/tool/services/src/ToolExecutionManager.rs`（942 行，100% 已读）
- `core/crates/tool/services/src/tools/AIToolHandler.rs`（3111 行，100% 已读）
- `core/crates/tool/services/src/tools/ToolRegistration.rs`（1784 行，100% 已读）
- `core/crates/tool/services/src/tools/ToolPermissionSystem.rs`（254 行，100% 已读）
