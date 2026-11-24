---
title: JS/TS 与 Wasm 运行时
module: plugins
platforms: [all]
sources: [core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs, core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js, core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs, core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs, plugins/types/quickjs-runtime.d.ts]
date: 2026-11-11
---

## 概述

外部 ToolPkg 归档加载不再经 loadToolPkgFromExternalFile（已删除），调用方直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:275`）。
`buildToolPkgRegistrationBridgeScript` 接受 `restrictHostCapabilities` 参数生成注册桥脚本（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:3`）。
桥脚本经 `installGlobal` 把 `ToolPkg` 对象安装为全局（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:674`）。
JS 运行时类型声明文件名为 quickjs-runtime.d.ts，声明了 `QuickJsTimerHandler` 等运行时全局（`plugins/types/quickjs-runtime.d.ts:20`）。
5 个 seed 文件没有给出 JS 引擎的 Rust 侧实现代码，引擎名只体现在类型声明文件名与 `QuickJsTimerHandler` 声明中（`plugins/types/quickjs-runtime.d.ts:20`）。
Rust 侧 Wasm 宿主基于 wasmi，只在非 wasm32 目标上执行（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:7`）。
SDK 自身编译为 wasm32 目标时 `callWasmExportForTarget` 返回 Wasm 宿主执行不可用错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:71`）。
ToolPkg.wasm 在注册期间不可用（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:69`）。

## AI 速览

- `callWasmExport` — Rust 侧 Wasm 导出调用入口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:10`）
- `Engine::default` — wasmi 引擎创建（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:32`）
- `__operitCreateToolPkgWasmApi` — JS 侧 ToolPkg.wasm API 工厂（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:67`）
- `__operitNativeLoadToolPkgWasm` — JS 侧取回 Wasm 模块字节与元数据的宿主函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:79`）
- `loadToolPkgFromArchiveBytes` — 归档字节加载入口，四个旧入口已删除（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:16`）
- `buildToolPkgRegistrationBridgeScript` — 注册桥脚本生成器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:3`）
- `registerMessageTransformHook` — 消息变换钩子注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:616`）
- `registerMessageStreamTransform` — 消息流变换注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:617`）
- ToolPkg.wasm 的 `call` — JS 侧 Wasm 导出调用入口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:103`）
- `parseWasmArg` — JS ABI 参数到 wasmi 标量值的转换（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:79`）
- `encodeWasmResult` — wasmi 标量结果到 JS 结果信封的转换（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:148`）
- `setTimeout` — 声明的计时器创建函数，返回 number 计时器 id（`plugins/types/quickjs-runtime.d.ts:22`）
- 主入口函数是 `callWasmExport`（Rust 侧 Wasm 调用）（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:10`）
- 数据流向一句话：归档字节由 `ZipArchive` 打开后进入解析与注册（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:39`）

## 核心机制

### JS 运行环境

JS 运行时类型声明文件 quickjs-runtime.d.ts 声明了 `QuickJsTimerHandler` 类型（`plugins/types/quickjs-runtime.d.ts:20`）。
quickjs-runtime.d.ts 把 `global` 声明为 `globalThis` 的别名（`plugins/types/quickjs-runtime.d.ts:2`）。
`Console` 的 `verbose` 接受 `VerboseLogLevel` 与任意数据（`plugins/types/quickjs-runtime.d.ts:10`）。
quickjs-runtime.d.ts 声明 `VerboseLogLevel` 为 1 至 6 的数字（`plugins/types/quickjs-runtime.d.ts:6`）。
quickjs-runtime.d.ts 声明 `setTimeout`，返回 number 计时器 id（`plugins/types/quickjs-runtime.d.ts:22`）。
quickjs-runtime.d.ts 声明 `clearTimeout` 取消计时器（`plugins/types/quickjs-runtime.d.ts:23`）。
quickjs-runtime.d.ts 声明 `setInterval`（`plugins/types/quickjs-runtime.d.ts:24`）。
quickjs-runtime.d.ts 声明 `clearInterval`（`plugins/types/quickjs-runtime.d.ts:25`）。
quickjs-runtime.d.ts 声明 `queueMicrotask`（`plugins/types/quickjs-runtime.d.ts:26`）。
`Storage` 声明 `getItem`、`setItem`、`removeItem`、`clear`、`key` 与只读 `length`（`plugins/types/quickjs-runtime.d.ts:33`）。
quickjs-runtime.d.ts 声明 `localStorage`、`sessionStorage` 与 `performance` 全局（`plugins/types/quickjs-runtime.d.ts:41`）。

### Wasm 加载与调用

ToolPkgWasmApi.js 在 `__operitCreateToolPkgWasmApi` 已定义时直接返回，不重复安装（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:3`）。
ToolPkgWasmApi.js 用 `modules` 与 `defaults` 两个 `Map` 按包身份隔离模块与默认实例（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:5`）。
模块 id 去空白并转小写后与包目标拼成键（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:74`）。
`load` 经 `__operitNativeLoadToolPkgWasm` 取回模块字节与元数据（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:79`）。
`load` 校验返回的 `bytes` 为 `Uint8Array` 且 `metadata.exports` 为数组，否则抛 `Invalid WASM module response` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:80`）。
`open` 只在首次编译时用 `new WebAssembly.Module` 编译模块字节，编译结果缓存复用（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:88`）。
`open` 用 `new WebAssembly.Instance` 以调用方传入的 `imports` 实例化已编译模块（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:91`）。
ToolPkg.wasm 的 `read` 返回模块字节的副本（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:97`）。
`call` 首次调用时创建默认实例并缓存到 `defaults`，创建失败时删除缓存并重新抛错（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:110`）。
`call` 只调用 `allowed` 清单内声明的导出，否则抛错（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:46`）。
`fn.apply` 调用导出函数并先经 `scalarArguments` 校验参数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:49`）。
标量结果为有限数字，`bigint` 结果转为十进制字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:52`）。
内存导出默认名为 `memory`，要求其为 `WebAssembly.Memory`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:41`）。
`readMemory` 按偏移与长度返回内存切片（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:56`）。
`writeMemory` 只接受 `Uint8Array` 写入（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:60`）。
`scalarArguments` 在参数为 `undefined` 或 `null` 时返回空数组（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:8`）。
`i32` 参数为整数且在 -2147483648 至 2147483647 范围内（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:15`）。
`i64` 参数转为 `BigInt` 并校验 64 位有符号范围（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:19`）。
`f32` 与 `f64` 参数有限，数字或数字字符串均转为 `Number`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:24`）。
`range` 在偏移或长度越界时抛 `RangeError`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:30`）。
导出名去空白后为空时返回 `ToolPkg WASM export name is required` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:17`）。
模块字节为空时返回 `ToolPkg WASM module bytes are empty` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:20`）。
非 wasm32 目标的 `callWasmExportForTarget` 用 `Engine::default()` 创建 wasmi 引擎（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:32`）。
模块字节经 `Module::new` 编译为模块（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:33`）。
`Linker::<()>` 的 `instantiate_and_start` 实例化并启动模块（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:37`）。
`get_func` 按导出名取函数，未找到时返回 `ToolPkg WASM export not found` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:40`）。
导出返回值超过一个时返回 `ToolPkg WASM export must return at most one value` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:50`）。
`parseWasmArg` 只接受 `i32`、`i64`、`f32`、`f64` 四种标量类型（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:79`）。
四种标量类型之外的 value_type 返回 `unsupported type` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:84`）。
`parseI32Value` 在值超出 `i32` 范围时返回 `exceeds i32 range` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:95`）。
`i64` 值接受 JSON 数字或十进制字符串形式（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:106`）。
浮点参数非有限时返回 `must be finite` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:137`）。
`encodeWasmResult` 把 `Val::I32` 结果编码为 `value_type` 为 `i32` 的 JSON 数字（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:148`）。
`Val::I64` 结果编码为 `value_type` 为 `i64` 的十进制字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:153`）。
`Val::F32` 与 `Val::F64` 结果经 `numberResult` 编码（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:155`）。
非标量返回值返回 `result type is unsupported` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:158`）。
导出无返回值时返回 `value_type` 为空、值为 null 的结果（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:161`）。
`numberResult` 在 `f64` 结果非有限时返回 `not finite` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:170`）。
`ValType::V128`、`ValType::FuncRef`、`ValType::ExternRef` 分别映射为 `v128`、`funcref`、`externref`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:187`）。
`tests` 模块内置 `PRIME_WASM` 字节数组作为演示 Wasm 模块（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:197`）。
tests 模块的 `callsPrimeDemoExports` 用内置 PRIME_WASM 演示模块验证 `isPrime` 与 `nthPrime` 导出（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:234`）。

### 注册流程

外部文件加载不再经 loadToolPkgFromExternalFile（已删除），调用方直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:275`）。
归档字节由调用方直接传入 `loadToolPkgFromArchiveBytes`，Loader 不再接收 filesystem 参数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:16`）。
外部文件加载以 `ToolPkgSourceType::EXTERNAL` 标记来源（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:123`）。
loadToolPkgFromBundledExternalAsset 已删除，捆绑外部资源加载改由调用方直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:275`）。
捆绑外部资源加载时，归档未声明安装范围默认使用 `ToolPkgConfigScope::Device`（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:482`）。
loadToolPkgFromBuiltInAsset 已删除，内置资源加载改由包注册表扫描直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:275`）。
内置资源加载以 `ToolPkgSourceType::ASSET` 标记来源（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:65`）。
loadToolPkgFromMarketFile 已删除，市场文件加载改由 RuntimePackageManager 导入路径直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs:5138`）。
市场文件加载以 `ToolPkgSourceType::MARKET` 标记来源（`core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs:5135`）。
非内置加载时，归档要求的安装范围与传入范围不一致时返回错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:32`）。
归档加载调用 `readThemeTemplates` 校验主题模板（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:37`）。
归档字节用 `ZipArchive` 打开（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:39`）。
归档字节解析入口 `loadToolPkgFromArchiveBytes` 是公开函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:16`）。
归档加载不再本地预读文本资源，文本资源由调用方以 `ToolPkgTextResourceHost` 传入（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:23`）。
主脚本直接由 `ToolPkgMainRegistrationScriptParser` 的 `parseWithTextResources` 解析注册声明（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:65`）。
主注册解析委托给 `ToolPkgMainRegistrationScriptParser` 的 `parseWithTextResources`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:65`）。
归档加载不再本地建小写键文本资源缓存，文本资源改由调用方传入的 `ToolPkgTextResourceHost` 提供（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:23`）。
归档文本资源改为由 `ToolPkgArchiveParser` 的 `readZipEntryText` 按条目名直接读取（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:44`）。
`buildToolPkgRegistrationBridgeScript` 在 `restrictHostCapabilities` 为真时把 `registrationOnly` 置为 `true` 字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:4`）。
桥脚本模板把 ToolPkgWasmApi.js 内联进来（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:678`）。
桥脚本模板把 `registrationOnly` 占位符替换为 true 或 false 字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:679`）。
桥脚本把 `capture` 对象挂到 `__operitToolPkgRegistrationCapture` 上（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:54`）。
`capture` 收集 `publicApis`、`toolboxUiModules`、`uiRoutes` 等注册桶（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:19`）。
capture 新增 `messageTransformHooks` 与 `messageStreamTransforms` 两个注册桶（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:33`）。
ToolPkg 新增 `registerMessageTransformHook` 与 `registerMessageStreamTransform` 两个注册函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:616`）。
ToolPkg.wasm 的值是 `__operitCreateToolPkgWasmApi` 的返回值（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:667`）。
`registerApi` 要求 `definition` 的 `name` 为非空字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:525`）。
`registerApi` 用 `normalizeFunctionField` 处理 `definition` 的 `function`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:527`）。
规范化后的公开 API 定义写入 `capture.publicApis`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:530`）。
`normalizeFunctionField` 要求 `definition` 的目标字段为函数引用，否则抛错（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:236`）。
函数字段经 `resolveDurableFunctionRef` 转为 durable 引用（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:240`）。
`resolveDurableFunctionRef` 先用 `OperitToolPkgExports` 的 `nameOf` 取已导出函数名（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:215`）。
`registrationOnly` 为真时 `ToolPkg.readResource` 抛错不可用（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:411`）。
`registrationOnly` 为真时浮动窗口命令抛错不可用（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:491`）。
导航 `surface` 清单包含 `toolbox`、`main_sidebar_plugins`、`app_bar`、`chat_attachments`、`chat_sidebar_tabs`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:80`）。
导航 `surface` 清单包含 `workspace` 与 `workspace_home`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:90`）。
导航 `surface` 清单还包含 `chat_input_menu`、`chat_input_menu_sections`、`chat_message_after`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:88`）。
`registerChatLifecycleHook` 要求 `definition` 的 `id` 为非空字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:620`）。
同一包重复注册聊天生命周期钩子时抛 `Duplicate chat lifecycle hook owner` 错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:623`）。
`captureMarketOrigin` 在非注册期调用时直接返回，不改动注册捕获状态（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:335`）。
插件配置目录经 `__operitNativeGetScopedPluginConfigDir` 取回（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:458`）。
插件配置目录为绝对 VFS 路径，否则抛错（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:462`）。

### 超时与取消

quickjs-runtime.d.ts 声明 `clearTimeout` 取消计时器（`plugins/types/quickjs-runtime.d.ts:23`）。
quickjs-runtime.d.ts 声明 `clearInterval`（`plugins/types/quickjs-runtime.d.ts:25`）。
`close` 把实例置为 `null`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:64`）。
`unload` 删除 `defaults` 与 `modules` 中的条目，并关闭待创建的默认实例（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:119`）。
`callWasmExport` 的参数只有模块字节、导出名与 `JsToolPkgWasmArg` 切片，无超时参数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:10`）。
ToolPkg.wasm 的 `call` 参数只有模块 id、导出名与 `args`，无超时参数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:103`）。
脚本执行超时上限的数值未在 5 个 seed 文件中给出，`callWasmExport` 的参数中无超时参数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:10`）。

## 关键符号

- `callWasmExport` — Rust 侧 Wasm 导出调用入口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:10`）
- `callWasmExportForTarget` — 按目标架构分派的 Wasm 导出调用实现（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:32`）
- `parseWasmArg` — JS ABI 参数到 wasmi 标量值的转换（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:79`）
- `encodeWasmResult` — wasmi 标量结果到 JS 结果信封的转换（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:148`）
- `numberResult` — 数值型 Wasm 结果的 JS 信封构造（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:170`）
- `wasmTypeName` — wasmi 值类型到 JS 侧类型名的映射（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:181`）
- `__operitCreateToolPkgWasmApi` — JS 侧 ToolPkg.wasm API 工厂（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:67`）
- `__operitNativeLoadToolPkgWasm` — JS 侧取回 Wasm 模块字节与元数据的宿主函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:79`）
- `scalarArguments` — JS 侧 Wasm 标量参数校验与转换（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:8`）
- `ToolPkgLoader` — ToolPkg 归档加载器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:11`）
- loadToolPkgFromExternalFile — 已删除，外部文件加载改由调用方直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:275`）
- loadToolPkgFromBundledExternalAsset — 已删除，捆绑外部资源加载改由调用方直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:275`）
- loadToolPkgFromBuiltInAsset — 已删除，内置资源加载改由包注册表扫描直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:275`）
- loadToolPkgFromMarketFile — 已删除，市场文件加载改由 RuntimePackageManager 导入路径直接调 `loadToolPkgFromArchiveBytes`（`core/crates/tool/services/src/tools/packTool/RuntimePackageManager.rs:5138`）
- `loadToolPkgFromArchiveBytes` — 归档字节解析与主脚本注册入口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:16`）
- `parseWithTextResources` — 主注册脚本解析入口（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:65`）
- `buildToolPkgRegistrationBridgeScript` — 注册桥脚本生成器（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:3`）
- `normalizeFunctionField` — 注册函数字段的规范化（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:236`）
- `resolveDurableFunctionRef` — 函数到 durable 引用的解析（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:215`）
- `registerApi` — 公开 API 注册函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:525`）
- `getToolPkgConfigDir` — 插件配置目录解析（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:451`）
- `QuickJsTimerHandler` — QuickJS 计时器回调类型（`plugins/types/quickjs-runtime.d.ts:20`）
- `VerboseLogLevel` — 1 至 6 的诊断级别类型（`plugins/types/quickjs-runtime.d.ts:6`）
- `setTimeout` — 计时器创建函数（`plugins/types/quickjs-runtime.d.ts:22`）
- `clearTimeout` — 计时器取消函数（`plugins/types/quickjs-runtime.d.ts:23`）

## 调用链

**归档加载与注册：**

1. 调用方直接以归档字节调 `loadToolPkgFromArchiveBytes` 传入归档，四个旧入口已删除（`core/crates/tool/services/src/tools/packTool/PackageRegistryScan.rs:275`）
2. 归档字节由调用方读入后传入 `loadToolPkgFromArchiveBytes`，Loader 不再接收 filesystem 参数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:16`）
3. 非内置加载时，归档要求的安装范围与传入范围不一致时返回错误（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:32`）
4. 归档加载调用 `readThemeTemplates` 校验主题模板（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:37`）
5. 归档字节用 `ZipArchive` 打开（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:39`）
6. 文本资源由调用方以 `ToolPkgTextResourceHost` 传入，不再本地预读（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:23`）
7. 主脚本直接由 `ToolPkgMainRegistrationScriptParser` 的 `parseWithTextResources` 解析注册声明（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:65`）
8. 主注册解析委托给 `ToolPkgMainRegistrationScriptParser` 的 `parseWithTextResources`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs:65`）
9. 桥脚本把 `capture` 对象挂到 `__operitToolPkgRegistrationCapture` 上（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:54`）
10. 规范化后的公开 API 定义写入 `capture.publicApis`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs:530`）

**JS 侧 Wasm 调用：**

1. `identity` 校验包目标与模块 id，注册期抛错（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:69`）
2. `load` 经 `__operitNativeLoadToolPkgWasm` 取回模块字节与元数据（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:79`）
3. `open` 首次编译并缓存 `WebAssembly.Module`（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:88`）
4. `open` 以 `imports` 实例化已编译模块（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:91`）
5. 默认实例复用自 `defaults` 缓存（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:110`）
6. `call` 只调用已声明导出（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:46`）
7. `unload` 删除缓存条目并关闭实例（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js:119`）

**Rust 侧 Wasm 调用：**

1. `callWasmExport` 校验导出名非空（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:17`）
2. `callWasmExport` 校验模块字节非空（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:20`）
3. `Engine::default()` 创建 wasmi 引擎（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:32`）
4. 模块字节经 `Module::new` 编译为模块（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:33`）
5. `Linker::<()>` 的 `instantiate_and_start` 实例化并启动模块（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:37`）
6. `get_func` 按导出名取函数（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:40`）
7. 校验导出最多返回一个值（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:50`）
8. 参数经 `parseWasmArg` 转为标量值（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:79`）
9. `Val::I32` 结果编码为 `value_type` 为 `i32` 的 JSON 数字（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:148`）
10. `Val::I64` 结果编码为 `value_type` 为 `i64` 的十进制字符串（`core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs:153`）

## 来源

- `core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmRuntime.rs`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgWasmApi.js`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgLoader.rs`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgRegistrationBridge.rs`
- `plugins/types/quickjs-runtime.d.ts`
