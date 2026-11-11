---
title: 插件——JS 桥
module: core
platforms: [all]
sources: 4
date: 2026-11-11
---

## 概述

javascript-bridge crate 只公开 `pub mod javascript` 一个模块（`core/crates/plugin/javascript-bridge/src/lib.rs:3`）。
该 crate 以 `extern crate self as operit_js_bridge` 把自身命名为 `operit_js_bridge`（`core/crates/plugin/javascript-bridge/src/lib.rs:1`）。
`JsEngine` 是 JS 执行引擎，实现 SDK 的 `JsExecutionEngine` trait（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2646`）。
`HostJsExecutionProvider` 实现 SDK 的 `JsExecutionProvider` trait，是引擎的提供方（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:91`）。
JS 通过 `__operitNative*` 宿主绑定调用宿主操作，35 个同步绑定以 `executeHostOperation` 为统一分发函数注册到 Host 运行时（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1930`）。
12 个异步宿主绑定以 `executeHostOperation` 的结果结算 Promise（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2151`）。
引擎与 SDK 的衔接点是 `JsExecutionHost`：host 与 context 同时存在时先调 `context.validate()` 再调 `host.for_toolpkg_execution_context(context)`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:303`）。
`JsExecutionHost` 与 `JsExecutionProvider` 两个 trait 的定义见 [[core-plugin-sdk|插件——Plugin SDK]]。
ToolPkg 的包模型与执行入口见 [[core-plugin-sdk|插件——Plugin SDK]]。

## AI 速览

- `JsEngine` — JS 执行引擎，SDK `JsExecutionEngine` trait 的实现（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2646`）
- `JsEngineWorker` — 持有引擎 owner 与可选执行宿主的工作体（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:76`）
- `JsEngineOwner` — 持有生命周期中断、运行时宿主、状态句柄与存活标志（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:81`）
- `JsEngineState` — 引擎状态，持有运行时、执行宿主与包上下文（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:283`）
- `PreparedJsEngine` — 未绑定引擎，`bind` 一次绑定包环境（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:788`）
- `JsPackageBinding` — 一次性包绑定，重复绑定返回错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:820`）
- `HostJsExecutionProvider` — SDK `JsExecutionProvider` trait 的实现，持有预备引擎池（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:16`）
- `HostJsExecutionEngineFactory` — 执行引擎工厂，持有执行宿主与预备引擎池（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:53`）
- `JsCallContext` — 一次调用的上下文：中断令牌、执行宿主、中间结果回调、执行监听器、环境变量覆盖、环境归属、文本资源来源与 IPC 计时（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:125`）
- `JsAsyncCallback` — 异步回调枚举，有 `ProfiledToolResult` 与 `Promise` 两种回调（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:101`）
- `JsTextResourceSource` — 文本资源来源枚举，有 `Snapshot`、`Package`、`ExecutionHost` 三种来源（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:118`）
- `JsExecutionListener` — 执行监听器 trait，定义 `on_intermediate_result` 与 `on_failed` 两个回调方法（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:47`）
- `JsIpcTiming` — IPC 计时，以 Host 调度器的单调时钟记录提交时刻（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:149`）
- `JsPendingScriptExecution` — 进行中的脚本执行，被丢弃时以会话结束完成调用（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:199`）
- `executeHostOperation` — 宿主操作统一分发函数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1930`）
- `toolPkgCallContext` — 调用身份推导：包目标、上下文键与运行时（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2421`）
- `parseToolCallValue` — 解析工具调用值：工具名、参数与设备（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:30`）
- `toolExecutionResultValue` — 生成工具执行结果信封（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:332`）
- 主入口函数：`new_toolpkg_execution_engine`（创建绑定包环境的引擎）（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:852`）
- 主入口函数：`acquire_toolpkg_execution_engine`（异步获取预备引擎）（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:114`）
- 主入口函数：`execute_toolpkg_main_registration_function`（执行 ToolPkg 主注册函数）（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:935`）
- 数据流向：JS 脚本 → `__operitNative*` 宿主绑定 → `executeHostOperation` 分发 → 执行宿主（`JsExecutionHost`）完成工具调用、包间 IPC、Core 路由或文本资源读取 → 结果结算回 JS Promise。

## 核心机制

### 引擎创建：三种构造与预备引擎池

- `JsEngine` 的 `new` 用 `JsEngineWorker::new(Some(executionHost), None)` 创建引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:841`）。
- `new_toolpkg_execution_engine` 用 `JsEngineWorker::new(Some(executionHost), Some(context))` 创建引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:852`）。
- `new_toolpkg_registration_engine` 用 `JsEngineWorker::new(None, None)` 创建仅用于注册的引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:862`）。
- `PreparedJsEngine` 的 `new` 用 `JsEngineWorker::new(None, None)` 初始化未绑定引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:788`）。
- `bind` 先调 `context.validate()` 再调 `executionHost.for_toolpkg_execution_context(&context)`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:801`）。
- 把 `JsPackageBinding` 写入 `packageBinding`，重复绑定返回 `"ToolPkg execution context is already bound"` 错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:820`）。
- `HostJsExecutionProvider` 的 `new` 通过 `defaultHostRuntimeTaskSchedulerHost()` 取得 Host 运行时任务调度器（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:22`）。
- `HostJsExecutionProvider` 的 `new` 用 `PreparedEnginePool::new` 创建预备引擎池，工厂闭包每次调用 `PreparedJsEngine::new()` 创建一个引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:25`）。
- 引擎预备失败时以 `AppLogger::e` 在 `JsEnginePool` 标签下记录 `engine_prepare_failed`（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:30`）。
- 预备任务以 `"ToolPkgEnginePrepare"` 为名提交到 Host 调度器（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:37`）。
- `HostJsExecutionProvider` 实现 `Default`，默认构造即调用 `new()`（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:44`）。
- 先执行 `context.validate()`，再向预备引擎池请求引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:147`）。
- 预备引擎池关闭时返回 `"Prepared engine pool closed during acquisition"`（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:149`）。
- 取到的预备引擎调用 `bind(host, context)` 后再返回（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:151`）。

### 提供方：工厂与 trait 实现

- `HostJsExecutionEngineFactory` 持有 `execution_host` 与 `prepared_engines` 两个字段（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:53`）。
- `HostJsExecutionEngineFactory` 的 `createExecutionEngine` 用 `JsEngine::new(self.execution_host.clone())` 创建不带包环境的引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:61`）。
- `createToolPkgExecutionEngine` 用 `JsEngine::new_toolpkg_execution_engine(self.execution_host.clone(), context)` 创建绑定包环境的引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:69`）。
- `acquireToolPkgExecutionEngine` 走 `acquirePreparedEngine` 异步获取预备引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:79`）。
- `JsExecutionProvider` 的 `create_execution_engine` 用 `JsEngine::new(execution_host)` 创建引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:93`）。
- `create_toolpkg_execution_engine` 用 `JsEngine::new_toolpkg_execution_engine(execution_host, context)` 创建引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:103`）。
- `acquire_toolpkg_execution_engine` 用 `acquirePreparedEngine` 异步获取预备引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:114`）。
- `create_package_executor` 用 `JsToolManager::new` 以 `package_runtime` 与 `HostJsExecutionEngineFactory` 创建包执行器（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:128`）。

### 引擎状态与生命周期

- `JsEngine` 结构体只含一个 `worker: JsEngineWorker` 字段（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:71`）。
- `JsEngineWorker` 持有 `owner: Arc<JsEngineOwner>` 与可选的 `executionHost`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:76`）。
- `JsEngineOwner` 持有 `lifetimeInterrupt`、`runtimeHost`、`stateHandle` 与 `alive` 四个字段（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:81`）。
- `JsEngineState` 持有 `runtime`、`executionHost` 与 `toolPkgContext`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:283`）。
- 引擎状态用 `pendingScriptExecutions` 与 `detachedCallContexts` 跟踪进行中与已分离的调用，并用 `packageBinding` 保存一次性包绑定（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:291`）。
- 只有 `toolPkgContext` 而无 host 时返回 `"ToolPkg execution context requires a real host"` 错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:306`）。
- 以 `"OperitJsEngine"` 为名、`HostJavaScriptRuntimeStateKind::Execution` 种类创建 Host JavaScript 运行时状态（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:318`）。
- 引擎状态创建时先注册宿主绑定，再评估 `buildRuntimeBootstrapScript()` 生成的引导脚本（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1077`）。
- `JsEngineOwner` 的 `destroy` 先触发生命周期中断，再以 `alive` 交换保证只释放一次 Host 运行时状态（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:617`）。
- `cancelScriptRequest` 先触发中断令牌与取消标志，再把取消步骤提交到 Host 调度器（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:400`）。
- `cancelJavaScriptExecution` 以 100 毫秒为限创建取消清理中断令牌（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1543`）。
- 取消执行时调用 `__operitCancelCallSession` 退役会话（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1549`）。
- 取消执行时调用 `cancelHostJavaScriptPromises` 取消该调用的 Promise（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1558`）。
- `activateCancelledScriptCall` 只允许显式限定的取消清理恢复已退役的调用（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:709`）。
- `JsPendingScriptExecution` 被丢弃时先清除原生调用会话，再以 `"JavaScript execution session ended before completion"` 完成调用（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:199`）。
- 未开始的请求在租约丢弃时通过 `cancelScriptRequest` 提交取消（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:266`）。
- `ExecutionScope` 的 `enter` 把生命周期中断与请求中断装入 Host 中断控制器（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:734`）。
- `selectScriptExecution` 切换线程局部的脚本归属与中断作用域（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:687`）。
- `executeWithInterrupt` 在操作结束后检查 `shouldInterrupt` 与 `didTimeOut`，超时时返回超时错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:771`）。

### 脚本执行：调用、超时与分离

- 每次脚本调用生成 `operit_call_` 前缀加 UUID 的 callId（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:470`）。
- 有限超时的请求通过 `scheduleDelayedHostRuntimeTask` 安排墙钟截止任务（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:509`）。
- `scriptRequestDeadline` 把当前时间加超时毫秒数作为请求截止时间，溢出时返回超时错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:646`）。
- `remainingScriptRequestMillis` 在剩余时间为 0 时返回 `"Before hook timed out before execution"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:655`）。
- 同步脚本执行转调内部 `executeScriptFunction`，超时参数为 `None`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:874`）。
- `timeoutMillis` 为 0 时直接返回 `"Before hook timed out before execution"` 超时错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:887`）。
- 异步脚本执行转调 worker 的异步执行并用 `textIntermediateCallback` 包装中间结果回调（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:904`）。
- `registerScriptSource` 对内容完全相同的脚本直接复用已注册的 sourceId（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1088`）。
- 新脚本注册为 `source_` 加已注册数量格式的 sourceId（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1091`）。
- 请求步骤按 `JsScriptRequestStep::Start` 启动会话，启动前检查 `cancelled` 标志（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1138`）。
- `startScriptFunctionForRequest` 加载模块并启动指定函数，不在等待期间持有状态借用（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1163`）。
- 脚本函数通过 Host 运行时调用 `__operitExecuteScriptFunction` 启动（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1258`）。
- 脚本调用通过 Host 运行时的 `__operitExecuteScriptFunction` 执行，参数依次为 callId、参数对象、sourceId、函数名、Compose 标志与包调用上下文（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1853`）。
- 已挂起调用按截止时间检查，超时则返回超时错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1605`）。
- `advanceDetachedJavaScriptExecution` 通过 `__operitGetDetachedCallIds` 取得已分离调用并逐个推进（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1647`）。
- `deliverAsyncCallback` 把异步回调结果通过 `settleHostJavaScriptPromise` 结算到 JS Promise（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1808`）。
- `resolveCurrentPackageLanguage` 通过执行宿主的 `package_language()` 解析包语言，返回空字符串时报错（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1829`）。
- `execute_script_function_on_current_thread` 只在测试配置下编译，是直接在当前线程执行的测试入口（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1296`）。
- `waitForExecutionResult` 只在测试配置下编译，在等待结果期间持续交付队列中的宿主回调（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1751`）。

### 注册执行与 Compose DSL

- ToolPkg 注册执行先评估 `buildToolPkgApiRuntimeScript()` 生成的 API 运行时脚本与 `buildToolPkgRegistrationBridgeScript(true)` 生成的注册桥脚本，再执行注册函数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1405`）。
- 注册执行完成后通过 `__operitReadRegistrationCapture` 读取注册捕获结果（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1507`）。
- 注册执行结束时重新评估 `buildToolPkgRegistrationBridgeScript(false)` 生成的运行时桥，恢复运行时桥（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1518`）。
- 注册结果的 `success` 字段为假时返回其 `message` 作为错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3567`）。
- `execute_toolpkg_main_registration_function` 转调带文本资源的注册执行，文本资源参数为 `None`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:935`）。
- Compose DSL 动作的 actionId 去空白后为空时返回 `"compose action id is required"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:971`）。
- Compose DSL 渲染以 `"__operit_render_compose_dsl"` 为入口函数名执行脚本（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1003`）。
- Compose DSL 的异步执行传入 `textResources`，中间结果分发到主线程并使用 Compose DSL 文本资源（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1027`）。

### 宿主绑定：35 同步、12 异步、7 Core 路由

- `registerHostBindings` 先注册 `__operitNativeCompileModuleFactory` 构造函数，参数为 module、exports、require 与 `__operit_call_runtime`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1888`）。
- 同步宿主绑定数组 `syncNames` 共 35 个名字（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1895`）。
- 35 个同步宿主绑定都以 `executeHostOperation` 为统一分发函数注册到 Host 运行时（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1930`）。
- `__operitNativeCallToolStructured` 以专属闭包分发结构化工具调用（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2005`）。
- 包间 IPC 要求目标包等于绑定上下文的包名，否则拒绝跨包 IPC（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2040`）。
- 依赖调用把目标运行时固定为 `"main"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2073`）。
- JS 定时器要求延迟参数是非负整数，否则返回 `"JavaScript timer delay must be a non-negative integer"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2021`）。
- `registerCoreRoute` 把一个具名 Core 路由注册为 Host 异步 JSON 函数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1866`）。
- Core 路由 `__operitNativeCallCoreRoute` 以 `registerCoreRoute` 注册为 Host 异步 JSON 函数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2095`）。
- Core 路由共 7 个名字，均以 `registerCoreRoute` 注册为 Host 异步 JSON 函数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2095`）。
- 异步宿主绑定数组 `asyncNames` 共 12 个名字（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2130`）。
- 12 个异步宿主绑定以 `executeHostOperation` 的结果结算 Promise（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2151`）。
- `exactHostJavaScriptJsonArguments` 校验结构化宿主绑定的参数个数，不符时返回 `"{name} requires {N} arguments, received {count}"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2186`）。

### 工具调用分发

- 结构化工具调用接受类型、名称、参数与归属调用 ID 四个参数，另可附第 5 个设备元数据参数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2221`）。
- 结构化工具调用在 Host 调度器的阻塞池上执行，工具执行器可做阻塞宿主调用（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2280`）。
- JS 定时器通过 `scheduleDelayedHostRuntimeTask` 安排延迟任务，到时回调结算 Promise（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2319`）。
- 包间 IPC 通过执行宿主的 `invoke_toolpkg_ipc_async` 提交，成功时以含 `success` 与 `value` 的 JSON 结算 Promise，失败时以 `buildToolPkgIpcFailure` 生成失败信封（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2359`）。
- Core 路由调用在 Host 调度器上异步执行，引擎生命周期结束时通过 `lifetime.changed()` 取消等待（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2394`）。

### 调用身份与运行时推导

- 调用身份从绑定上下文或 `__operit_ui_package_name` 参数推导 `packageTarget`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2421`）。
- 调用身份从绑定上下文或 `__operit_execution_context_key` 参数推导 `contextKey`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2424`）。
- 上下文键以 `toolpkg_provider:` 开头时运行时为 `provider`，以 `toolpkg_compose:` 等开头时为 `ui`，含子包 ID 时为 `sandbox`，其余为 `main`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2444`）。
- 运行时取值只接受 `main`、`ui`、`sandbox`、`provider`，其他值返回 `ToolPkg execution runtime is invalid` 错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2454`）。
- IPC 请求要求 channel 非空，否则返回 `"ToolPkg.ipc channel is required"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2479`）。
- IPC 请求的目标运行时只接受 `main`、`ui`、`sandbox`、`provider` 或空（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2485`）。
- `clearThreadLocalCallState` 清空当前脚本归属、活跃调用上下文、执行宿主、中间回调、监听器、环境覆盖与文本资源来源（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2505`）。
- `installThreadLocalCallContext` 把一次调用的执行宿主、中间回调、监听器、环境覆盖与文本资源来源装入线程局部状态（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2527`）。
- `packageTextResourceSource` 在有包上下文时用包的文本资源宿主，否则用执行宿主（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2554`）。

### 宿主操作工具

- `parseToolCallValue` 在工具名去空白后为空时返回 `"Tool name cannot be empty"`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:30`）。
- 工具参数必须是 JSON 对象，否则返回 `"Tool params must be a JSON object"`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:34`）。
- `JsToolCallRequest` 的 `device` 字段初始为 `None`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:37`）。
- 二进制句柄前缀常量 `BINARY_HANDLE_PREFIX` 为 `"@binary_handle:"`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:14`）。
- 二进制数据阈值常量 `BINARY_DATA_THRESHOLD` 为 `32 * 1024` 字节（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:15`）。
- 二进制结果注册表 `BINARY_DATA_REGISTRY` 是 `OnceLock<Mutex<HashMap<String, Vec<u8>>>>`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:45`）。
- 位图注册表 `BITMAP_REGISTRY` 是 `OnceLock<Mutex<HashMap<String, DynamicImage>>>`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:46`）。
- `readBinaryOrBase64` 遇到二进制句柄前缀时从注册表一次性取出字节，句柄无效时报错（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:61`）。
- `decompress` 只支持 `deflate` 算法，其他算法返回 `Unsupported algorithm` 错误（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:76`）。
- `crypto` 的 `binary` 算法分发给 `JsBinaryCrypto::execute`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:96`）。
- `crypto` 的 `md5` 只接受 `hash` 操作且输入必须恰好一个字符串（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:99`）。
- AES 解密只接受 `decrypt` 操作，其他操作返回 `Unknown AES operation` 错误（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:113`）。
- AES 解密要求输入长度是 16 的倍数，否则返回输入长度必须是 16 的倍数的错误（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:129`）。
- AES 解密按密钥长度 16/24/32 字节分别选用 Aes128、Aes192、Aes256（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:136`）。
- `imageProcessing` 支持 read、create、crop、composite、getwidth、getheight、getbase64、release 八种操作（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:170`）。
- `read` 操作把解码后的图片存入位图注册表并返回新 UUID（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:183`）。
- `getbase64` 只支持 `image/png` 与 `image/jpeg` 两种 MIME 类型（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:267`）。
- `release` 操作从位图注册表删除指定 ID 的图片（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:295`）。
- `toolExecutionResultValue` 生成的信封含 `success` 字段，失败时含 `message` 字段（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:332`）。
- 二进制数据时信封中加入 `dataType` 字段（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:344`）。
- 超过 `BINARY_DATA_THRESHOLD` 的二进制结果生成 UUID 句柄并存入注册表，信封数据为 `BINARY_HANDLE_PREFIX` 前缀加句柄（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:359`）。
- 未超过阈值的二进制结果在信封中以 base64 编码返回（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:364`）。
- `JsToolCallResultData::Value` 直接透传数据且 `dataType` 为 `None`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:371`）。

### 文本资源、中间结果与完成

- 文本资源读取按 Snapshot、Package、ExecutionHost 三种来源分发（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2944`）。
- `JsIpcTiming` 的 `new` 以 Host 调度器的单调时钟记录提交时刻（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:149`）。
- `log` 只在成功且设置了 `OPERIT_PROFILE_COMPOSE_STAGES` 环境变量时才输出成功阶段耗时，失败时总输出日志（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:167`）。
- 中间结果要求有活跃的归属调用，先调监听器的 `on_intermediate_result` 再调中间结果回调（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2796`）。
- 文本中间结果回调收到非文本值时直接 `panic`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2823`）。
- `textScriptCompletion` 把结构化脚本结果适配为文本结果（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2804`）。
- 普通脚本只接受字符串结果，非字符串的结构化结果返回序列化错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2816`）。
- `sendStructuredIntermediate` 优先发给活跃调用的回调，活跃调用不存在时发给已分离调用的回调，两者都不存在时静默丢弃（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2832`）。
- `CancelScope` 回调用于取消指定作用域的 Promise（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:108`）。
- `requireHostObject` 要求宿主载荷是结构化对象，不接受序列化 JSON 文本（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3287`）。
- `storeExecutionResult` 要求结果归属的调用仍活跃，否则返回 `"Completion requires an active owning call"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3324`）。
- `storeExecutionError` 先调执行监听器的 `on_failed`，再把错误存入原生调用会话（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3341`）。
- 插件数据目录路径必须是绝对 VFS 路径，否则返回 `"Plugin data directory must be an absolute VFS path"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2910`）。

### 环境、调用方上下文与配置

- 调用方上下文的 participantId、extensionOwner 与 chatId 写入 `__operit_package_caller_participant_id` 等参数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3369`）。
- 注册模式下环境归属取自参数 `toolPkgId`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3395`）。
- 非注册模式下优先取绑定包上下文的包名，否则取 `__operit_package_name` 参数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3425`）。
- `setHostEnvironmentValue` 要求环境变量名非空，否则返回 `"Environment variable name is required"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3444`）。
- 解析出的配置目录必须是绝对 VFS 路径，否则报错（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3497`）。
- `currentExecutionHost` 从线程局部 `CURRENT_EXECUTION_HOST` 取当前调用绑定的执行宿主，不存在时报错 `"JavaScript execution host is unavailable"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3505`）。

### Java 桥（Android 宿主）

- `__operitNativeJavaGetCurrentActivity` 恒返回 `"current activity is null"` 错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3167`）。
- `__operitNativeJavaCallStaticSuspend`、`__operitNativeJavaGetStaticField`、`__operitNativeJavaSetStaticField` 返回 `"Java host operation is not implemented: {name}"` 错误（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:3197`）。

## 关键符号

- `JsEngine` — JS 执行引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:71`）
- `JsEngineWorker` — 持有引擎 owner 与可选执行宿主（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:76`）
- `JsEngineOwner` — 持有生命周期中断、运行时宿主、状态句柄与存活标志（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:81`）
- `JsEngineState` — 引擎状态（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:283`）
- `PreparedJsEngine` — 未绑定引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:788`）
- `JsPackageBinding` — 一次性包绑定（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:820`）
- `JsCallContext` — 一次调用的上下文（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:125`）
- `JsAsyncCallback` — 异步回调枚举（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:101`）
- `JsTextResourceSource` — 文本资源来源枚举（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:118`）
- `JsExecutionListener` — 执行监听器 trait（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:47`）
- `JsIpcTiming` — IPC 计时（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:149`）
- `JsPendingScriptExecution` — 进行中的脚本执行（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:199`）
- `HostJsExecutionProvider` — SDK `JsExecutionProvider` trait 的实现（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:16`）
- `HostJsExecutionEngineFactory` — 执行引擎工厂（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:53`）
- `registerHostBindings` — 注册宿主绑定（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1888`）
- `registerCoreRoute` — 注册 Core 路由（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1866`）
- `executeHostOperation` — 宿主操作统一分发函数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1930`）
- `dispatchStructuredToolCall` — 结构化工具调用分发（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2221`）
- `toolPkgCallContext` — 调用身份推导（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2421`）
- `parseToolCallValue` — 解析工具调用值（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:30`）
- `toolExecutionResultValue` — 生成工具执行结果信封（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:332`）
- `BINARY_DATA_REGISTRY` — 二进制结果注册表（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:45`）
- `BITMAP_REGISTRY` — 位图注册表（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:46`）

## 调用链

### JS 调用宿主工具

1. JS 调用 `__operitNativeCallToolStructured`，专属闭包分发结构化工具调用（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2005`）。
2. `dispatchStructuredToolCall` 接受类型、名称、参数与归属调用 ID 四个参数，另可附第 5 个设备元数据参数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2221`）。
3. 结构化工具调用在 Host 调度器的阻塞池上执行，工具执行器可做阻塞宿主调用（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2280`）。
4. 参数经 `parseToolCallValue` 校验，工具名去空白后为空时返回 `"Tool name cannot be empty"`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:30`）。
5. 参数必须是 JSON 对象，否则返回 `"Tool params must be a JSON object"`（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:34`）。
6. 结果经 `toolExecutionResultValue` 生成信封，信封含 `success` 字段，失败时含 `message` 字段（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:332`）。
7. 超过 `BINARY_DATA_THRESHOLD` 的二进制结果生成 UUID 句柄并存入注册表，信封数据为 `BINARY_HANDLE_PREFIX` 前缀加句柄（`core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs:359`）。
8. 异步结果通过 `deliverAsyncCallback` 结算到 JS Promise（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1808`）。

### ToolPkg 注册执行

1. 宿主经 `acquire_toolpkg_execution_engine` 用 `acquirePreparedEngine` 异步获取预备引擎（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:114`）。
2. 取到的预备引擎调用 `bind(host, context)` 后再返回（`core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs:151`）。
3. 注册执行先评估 `buildToolPkgApiRuntimeScript()` 生成的 API 运行时脚本与 `buildToolPkgRegistrationBridgeScript(true)` 生成的注册桥脚本，再执行注册函数（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1405`）。
4. 注册执行完成后通过 `__operitReadRegistrationCapture` 读取注册捕获结果（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1507`）。
5. 注册执行结束时重新评估 `buildToolPkgRegistrationBridgeScript(false)` 生成的运行时桥，恢复运行时桥（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:1518`）。

### 包间 IPC

1. 调用身份从绑定上下文或 `__operit_ui_package_name` 参数推导 `packageTarget`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2421`）。
2. IPC 请求要求 channel 非空，否则返回 `"ToolPkg.ipc channel is required"`（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2479`）。
3. 包间 IPC 要求目标包等于绑定上下文的包名，否则拒绝跨包 IPC（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2040`）。
4. 包间 IPC 通过执行宿主的 `invoke_toolpkg_ipc_async` 提交，成功时以含 `success` 与 `value` 的 JSON 结算 Promise，失败时以 `buildToolPkgIpcFailure` 生成失败信封（`core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs:2359`）。

## 来源

- `core/crates/plugin/javascript-bridge/src/lib.rs`
- `core/crates/plugin/javascript-bridge/src/javascript/JsEngine.rs`
- `core/crates/plugin/javascript-bridge/src/javascript/JsExecutionProvider.rs`
- `core/crates/plugin/javascript-bridge/src/javascript/JsHostOperations.rs`
