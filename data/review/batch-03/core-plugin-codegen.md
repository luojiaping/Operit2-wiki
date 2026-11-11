---
title: 插件——SDK 代码生成与 IPC
module: core
platforms: [all]
sources: [core/crates/plugin/codegen/src/lib.rs, core/crates/plugin/codegen/src/declarations.rs, core/crates/plugin/codegen/src/client_codegen.rs, core/crates/plugin/codegen/src/registration.rs, core/crates/plugin/sdk-macros/src/lib.rs, core/crates/plugin/sdk-ipc/src/lib.rs, core/crates/plugin/sdk-ipc-bridge/src/lib.rs]
date: 2026-11-11
---

# 插件——SDK 代码生成与 IPC

## 概述

- `operit-plugin-codegen` 是 Operit2 的 SDK 代码生成 crate，从 Rust SDK 源码生成 TypeScript 声明树、JavaScript Tools 运行时、内置工具名枚举与四种语言的 SDK 客户端（core/crates/plugin/codegen/src/lib.rs:2）。
- 代码生成全部发生在构建时，由 build.rs 与 codegen 二进制触发，不在运行时动态生成（core/crates/plugin/sdk/build.rs:55）。
- SDK 声明的 Rust 源头是 [[core-plugin-sdk|插件——Plugin SDK]] 的 Host trait，生成的 JavaScript 运行时由 [[core-plugin-js-bridge|插件——JS 桥]] 承载（core/crates/plugin/codegen/src/runtime_bindings.rs:12）。
- `operit-plugin-sdk-ipc` 是插件 SDK 与 Core 之间的运行时通道，承载调用、订阅与推送三类交互（core/crates/plugin/sdk-ipc/src/lib.rs:9）。
- `operit-plugin-sdk-ipc-bridge` 只有 36 行，是 Operit 侧的薄桥接器，只把宿主与 Link 目标接到 `PluginSdkIpcServer` 上（core/crates/plugin/sdk-ipc-bridge/src/lib.rs:9）。

## AI 速览

- `generate_declaration_tree` — 从 Rust SDK 源码生成 TypeScript 声明树（core/crates/plugin/codegen/src/declarations.rs:125）
- `check_declaration_tree` — 校验已提交声明与重新生成结果一致（core/crates/plugin/codegen/src/declarations.rs:158）
- `generate_js_tools_runtime` — 生成 JavaScript Tools 运行时（core/crates/plugin/codegen/src/runtime_bindings.rs:288）
- `generate_builtin_tool_names` — 生成 BuiltinToolName 枚举（core/crates/plugin/codegen/src/registration.rs:21）
- `check_tool_registration_contract` — 校验工具注册与 Rust SDK 工具映射一致（core/crates/plugin/codegen/src/registration.rs:99）
- `generate_plugin_sdk_client_bindings` — 生成 Rust、Dart、Kotlin、TypeScript 四种语言的 SDK 客户端（core/crates/plugin/codegen/src/client_codegen.rs:11）
- `generate_plugin_sdk_surface` — 生成路由白名单 pluginSdkSurface()（core/crates/plugin/codegen/src/client_codegen.rs:59）
- `PluginSdkIpcMessage` — 14 个变体的 IPC 帧枚举（core/crates/plugin/sdk-ipc/src/frame.rs:10）
- `PluginSdkClient` — SDK 侧 IPC 客户端（core/crates/plugin/sdk-ipc/src/client.rs:39）
- `PluginSdkIpcServer` — Operit 侧 IPC 服务器（core/crates/plugin/sdk-ipc/src/server.rs:31）
- `PluginSdkSurface` — 对象 ID 到方法名集合的路由白名单（core/crates/plugin/sdk-ipc/src/surface.rs:8）
- `PluginSdkLinkTarget` — 只定义四个转发方法的 trait（core/crates/plugin/sdk-ipc/src/handler.rs:13）
- `OperitPluginSdkIpcBridge` — 只持有一个 PluginSdkIpcServer 的 36 行桥接器（core/crates/plugin/sdk-ipc-bridge/src/lib.rs:9）
- `js_declaration` — 声明元数据的过程宏属性（core/crates/plugin/sdk-macros/src/lib.rs:13）
- `tool_display` — 工具展示元数据的过程宏属性（core/crates/plugin/sdk-macros/src/lib.rs:58）
- 主入口：`codegen` 二进制接受命令、SDK 源码根、声明输出根三个参数（core/crates/plugin/codegen/src/main.rs:12）
- 主入口：`plugin/sdk` 的 build.rs 在构建时依次运行 generate_js_tools_runtime、generate_declaration_tree、generate_builtin_tool_names（core/crates/plugin/sdk/build.rs:55）
- 数据流向：Rust SDK 源码 → codegen → TypeScript 声明树、js_tools.js、builtin_tool_names.rs（core/crates/plugin/sdk/build.rs:55）
- 数据流向：Core 代理扫描 → 四语言客户端与路由白名单（core/crates/proxy/local/build.rs:52）
- 数据流向：插件 SDK 客户端 → PluginSdkIpcMessage 帧 → PluginSdkIpcServer → Link 目标（core/crates/plugin/sdk-ipc/src/server.rs:192）

## 核心机制

### 声明树生成

- `MODULES` 常量列出 22 个 `ModuleSpec`，每个对应一个 Rust 源文件与一个 TypeScript 声明文件（core/crates/plugin/codegen/src/declarations.rs:29）。
- storage 模块是唯一带 `additional_rust_file`（foundation/host-api/src/PluginStorage.rs）且 `nullable_wire_fields` 为 true 的模块，输出 storage.generated.d.ts（core/crates/plugin/codegen/src/declarations.rs:34）。
- `generate_declaration_tree` 先创建输出目录，再渲染整棵声明树，只把内容变化的文件写入磁盘（core/crates/plugin/codegen/src/declarations.rs:128）。
- `writeDeclarationWhenChanged` 在文件内容完全相同时跳过写入，缺失或内容不同时写入（core/crates/plugin/codegen/src/declarations.rs:142）。
- `check_declaration_tree` 比较已提交声明与重新生成结果，不一致时报错列出全部差异文件（core/crates/plugin/codegen/src/declarations.rs:158）。
- `check_declaration_tree` 比较前把回车换行统一归一化为换行，消除 Git 换行符差异（core/crates/plugin/codegen/src/declarations.rs:166）。
- `render_declaration_tree` 逐个读取各模块的 Rust 源文件并用 syn 解析，再建类型目录、逐模块生成声明文件（core/crates/plugin/codegen/src/declarations.rs:190）。
- `generate_declaration_file` 为 toolpkg.d.ts 追加 ToolPkg 运行时导入与全局 ToolPkg 声明（core/crates/plugin/codegen/src/declarations.rs:210）。
- `generate_declaration_file` 为 storage.d.ts 追加 storage.generated 的类型重导出列表（core/crates/plugin/codegen/src/declarations.rs:212）。
- `build_type_catalog` 按 Rust 类型名索引每个公开 SDK 类型的目标 TypeScript 模块与路径（core/crates/plugin/codegen/src/declarations.rs:227）。
- 同一 Rust 类型被多个模块声明时 `build_type_catalog` 断言失败（core/crates/plugin/codegen/src/declarations.rs:244）。
- `EmitContext::new` 把 impl 按 self 类型归档（core/crates/plugin/codegen/src/declarations.rs:323）。
- `EmitContext::new` 把 CoreHost trait 单独收进 root_traits（core/crates/plugin/codegen/src/declarations.rs:333）。
- `EmitContext::new` 把其余公开声明按推断的 TypeScript 路径登记（core/crates/plugin/codegen/src/declarations.rs:340）。
- `EmitContext::emit` 在输出头部写 `Generated from operit-plugin-sdk Rust declarations.`，并为跨模块类型补 import type 行（core/crates/plugin/codegen/src/declarations.rs:372）。
- `emit_scope` 在 toolpkg.d.ts 的 ToolPkg 作用域注入 ipc、wasm、ui 三个常量声明（core/crates/plugin/codegen/src/declarations.rs:393）。
- `scope_entries` 在空作用域时把 CoreHost 的方法作为根函数输出（core/crates/plugin/codegen/src/declarations.rs:506）。
- `emit_group` 按 kind 分发：interface/class 走 emit_interface_group，type 走 emit_type_group，type_map 走 emit_type_map_group，variable 走 emit_variable_group，未知 kind 直接 panic（core/crates/plugin/codegen/src/declarations.rs:528）。
- `emit_type_map_group` 要求枚举变体各带一个未命名字段，生成以变体名为键的 TypeScript interface（core/crates/plugin/codegen/src/declarations.rs:544）。
- `emit_interface_group` 把同一声明组的结构体字段与 trait/impl 方法合并输出（core/crates/plugin/codegen/src/declarations.rs:618）。
- `emit_interface_group` 为 DeviceTransportChannel 额外生成 extends AsyncIterable<DeviceTransportEvent>（core/crates/plugin/codegen/src/declarations.rs:595）。
- `emit_constructor_object` 只在存在非 receiver 关联方法时输出构造对象（core/crates/plugin/codegen/src/declarations.rs:649）。
- `emit_constructor_object` 在存在构造器时为构造对象补 prototype 字段（core/crates/plugin/codegen/src/declarations.rs:668）。
- `emit_struct_fields` 把 additionalProperties 映射字段转为索引签名（core/crates/plugin/codegen/src/declarations.rs:686）。
- `emit_struct_fields` 在组只读或字段只读时输出 readonly 修饰（core/crates/plugin/codegen/src/declarations.rs:698）。
- `group_methods` 收集 trait 方法与公开固有 impl 方法（core/crates/plugin/codegen/src/declarations.rs:740）。
- `group_methods` 跳过带 trait 的 impl（core/crates/plugin/codegen/src/declarations.rs:761）。
- `emit_type_group` 把 ToolReturnType 特判为按 ToolResultMap 键的条件类型（core/crates/plugin/codegen/src/declarations.rs:793）。
- `emit_type_group` 把枚举生成联合类型、类型别名展开底层类型、包装结构体展开内部类型或交集（core/crates/plugin/codegen/src/declarations.rs:805）。
- `emit_variable_group` 在根作用域输出 export declare，CommonJsExports 用 var 其余用 const（core/crates/plugin/codegen/src/declarations.rs:833）。
- `emit_method` 按样式输出：根函数为 export declare function，类静态方法加 static，构造器输出 constructor 关键字（core/crates/plugin/codegen/src/declarations.rs:913）。
- `emit_method` 在方法无返回值时输出 void（core/crates/plugin/codegen/src/declarations.rs:949）。
- `emit_field_type` 把 Option 字段在 nullable_wire_fields 为真时输出 `| null`，否则输出内部类型；JsOptional 输出 `| null`（core/crates/plugin/codegen/src/declarations.rs:963）。
- `emit_parameter_type` 把 Option 与 JsOptional 参数标记为可选参数（core/crates/plugin/codegen/src/declarations.rs:977）。
- `emit_path_type` 的标量映射：String/str/JsDate 映射为 string，bool 映射为 boolean，整数与浮点映射为 number，Value 映射为 unknown，JsBigInt 映射为 bigint，JsUint8Array 映射为 Uint8Array，JsAny 映射为 any（core/crates/plugin/codegen/src/declarations.rs:1129）。
- `emit_path_type` 把 JsObject 映射为 object，JsNever 映射为 never（core/crates/plugin/codegen/src/declarations.rs:1135）。
- `emit_path_type` 把 Option 在 nullable_wire_fields 时映射为 `| null`，否则为 `| undefined`，JsOptional 映射为 `| null | undefined`，JsNullable 映射为 `| null`（core/crates/plugin/codegen/src/declarations.rs:1145）。
- `emit_path_type` 把 JsFuture 映射为 Promise，JsAsyncIterable 映射为 AsyncIterable（core/crates/plugin/codegen/src/declarations.rs:1151）。
- `emit_enum_union` 把无字段枚举变体输出为字符串字面量联合，Null、Undefined、Void 三个变体分别输出 null、undefined、void（core/crates/plugin/codegen/src/declarations.rs:1301）。
- `emit_enum_union` 对带 serde tag 与 content 的枚举输出带判别字段的对象联合（core/crates/plugin/codegen/src/declarations.rs:1317）。
- `resolve_named_type` 对同一文件或 global 作用域的类型输出相对路径（core/crates/plugin/codegen/src/declarations.rs:1425）。
- `resolve_named_type` 对跨文件类型记录 import type 导入（core/crates/plugin/codegen/src/declarations.rs:1435）。
- `declaration_options` 的 kind 只接受 interface、class、type，其他值报错（core/crates/plugin/codegen/src/declarations.rs:1556）。
- `field_is_readonly` 只认字段上的 js(readonly)，未知 js 字段选项与重复 readonly 均报错（core/crates/plugin/codegen/src/declarations.rs:1577）。
- `public_item_ref` 只收公开的 struct、enum、type alias、trait（core/crates/plugin/codegen/src/declarations.rs:1613）。
- `default_item_kind` 把元组结构体与扁平交集结构体判为 type，普通结构体与 trait 判为 interface，枚举与类型别名判为 type（core/crates/plugin/codegen/src/declarations.rs:1641）。
- `is_flattened_intersection` 在全部字段带 serde flatten，或字段名为 member_1、member_2 依次编号时成立（core/crates/plugin/codegen/src/declarations.rs:1658）。
- `infer_declaration` 优先使用显式 scope/name/kind，ToolPkgBroadcastTopicKey 直接跳过不生成声明（core/crates/plugin/codegen/src/declarations.rs:1679）。
- `infer_declaration` 把 FilesHost、NetHost、SystemHost 等 Host trait 按命名空间映射（core/crates/plugin/codegen/src/declarations.rs:1700）。
- `infer_declaration` 把 ChatHost、StorageHost、StorageFacadeHost 映射到 Chat 与 Storage 命名空间（core/crates/plugin/codegen/src/declarations.rs:1719）。
- `infer_declaration` 按输出文件经 `prefixed_path` 加命名空间前缀：仅当 Rust 名以该前缀开头时进入命名空间，否则输出到根：files.d.ts 映射为 Files、network.d.ts 映射为 Net、system.d.ts 映射为 System、models.d.ts 映射为 Models、tts.d.ts 映射为 Tts、stt.d.ts 映射为 Stt、theme.d.ts 映射为 Theme、catalog.d.ts 映射为 Catalog、media.d.ts 映射为 Media（core/crates/plugin/codegen/src/declarations.rs:1736）。
- `infer_declaration` 把 software_settings.d.ts、ui.d.ts、storage.d.ts 的声明分别归入 SoftwareSettings、UI、Storage 命名空间；仅当 Rust 名以该前缀开头时进入命名空间，否则输出到根；ui.d.ts 中以 `UINode` 开头的声明直接输出原名（core/crates/plugin/codegen/src/declarations.rs:1743）。
- `infer_declaration` 把 chat.d.ts、toolpkg.d.ts 的声明分别归入 Chat、ToolPkg 命名空间（core/crates/plugin/codegen/src/declarations.rs:1756）。
- `prefixed_path` 在 Rust 名以前缀开头时剥离前缀生成两段路径，否则保留原名（core/crates/plugin/codegen/src/declarations.rs:1765）。
- `is_inherited_base_field` 把带 serde flatten 的非附加属性字段，或 base_ 开头且非可选的字段判为继承基字段（core/crates/plugin/codegen/src/declarations.rs:1810）。
- `is_additional_properties_field` 只认名为 additional_properties 或 additionalProperties 的字段（core/crates/plugin/codegen/src/declarations.rs:1820）。
- `typescript_generic_bound` 把 AsRef<str|String> 映射为 string（core/crates/plugin/codegen/src/declarations.rs:1865）。
- `typescript_generic_bound` 把 ToolPkgBroadcastTopicKey 映射为 ToolPkg.BroadcastTopic，Send/Sync/Sized 忽略，其他泛型 bound 直接 panic（core/crates/plugin/codegen/src/declarations.rs:1880）。
- `is_function_type` 在 Fn trait 对象，或 Arc/Box/Pin 包裹的 Fn 类型时成立（core/crates/plugin/codegen/src/declarations.rs:1890）。
- `emit_jsdoc` 把 Rust 文档注释输出为 JSDoc 块，裁掉首尾空行（core/crates/plugin/codegen/src/declarations.rs:2043）。
- `method_name` 去掉 Rust 方法名中的 _overload_ 后缀与 r# 前缀（core/crates/plugin/codegen/src/declarations.rs:2070）。
- `pattern_name` 要求 SDK trait 参数使用标识符模式，否则 panic（core/crates/plugin/codegen/src/declarations.rs:2081）。
- `typescript_module_path` 把 .d.ts 文件名转为 ./<模块名> 的相对导入路径（core/crates/plugin/codegen/src/declarations.rs:2261）。

### JS Tools 运行时生成

- `HOST_TRAITS` 列出 Files、Net、Net.cookies、System、System.bluetooth 映射（core/crates/plugin/codegen/src/runtime_bindings.rs:12）。
- `HOST_TRAITS` 列出 System.bluetooth.ble、System.terminal、System.music、SoftwareSettings 映射（core/crates/plugin/codegen/src/runtime_bindings.rs:21）。
- `HOST_TRAITS` 列出 Models、Tts、Stt、Theme、Catalog、Media、Chat、Storage 映射，共 17 组（core/crates/plugin/codegen/src/runtime_bindings.rs:33）。
- `parse_rust_tool_bindings` 读取 JS_TOOL_BINDINGS 常量数组（core/crates/plugin/codegen/src/runtime_bindings.rs:62）。
- 每条 JsToolBinding 含 strict_arguments、facade 与 fixed_parameters 字段（core/crates/plugin/codegen/src/runtime_bindings.rs:45）。
- JsToolBinding 的目标必须是 BuiltinToolName 变体（core/crates/plugin/codegen/src/runtime_bindings.rs:104）。
- JS_TOOL_API_VARIANTS 引用不存在的绑定时报错（core/crates/plugin/codegen/src/runtime_bindings.rs:196）。
- JS_TOOL_API_VARIANTS 同一版本号重复声明时报错（core/crates/plugin/codegen/src/runtime_bindings.rs:206）。
- `generate_js_tools_runtime` 先校验 Host trait 声明的方法集合与绑定表完全一致，缺失或多余时返回 Rust Tools bindings differ from active host traits 错误（core/crates/plugin/codegen/src/runtime_bindings.rs:298）。
- `generate_js_tools_runtime` 生成的 JavaScript 先输出 __operitToolParameterRules，再定义 Tools 命名空间（core/crates/plugin/codegen/src/runtime_bindings.rs:312）。
- 生成的 JavaScript 内嵌 chat_runtime.js、terminal_runtime.js 与 storage_runtime.js 三个手写运行时（core/crates/plugin/codegen/src/runtime_bindings.rs:400）。
- Chat 命名空间的方法挂在 __operitToolPkgApi.namespace("Tools.Chat") 下（core/crates/plugin/codegen/src/runtime_bindings.rs:471）。
- 生成输出末尾追加 compat/v1 的 9 个手写适配器与 DeviceTools.script.js（core/crates/plugin/codegen/src/runtime_bindings.rs:504）。
- 生成输出在写入前用 tree-sitter 校验 JavaScript 语法（core/crates/plugin/codegen/src/runtime_bindings.rs:513）。
- 生成输出以 __operitCanonicalTools 保存 Tools 命名空间的深拷贝（core/crates/plugin/codegen/src/runtime_bindings.rs:495）。
- AsyncIterator facade 经 __operitCreateToolStream 建流，并要求恰好一个请求参数（core/crates/plugin/codegen/src/runtime_bindings.rs:443）。
- TerminalCallback 走 __operitExecTerminalStreaming，TerminalRun 走 __operitRunTerminal，TerminalWait 走 __operitWaitTerminal（core/crates/plugin/codegen/src/runtime_bindings.rs:445）。
- Promise 与 Storage facade 走生成的 JS 函数（core/crates/plugin/codegen/src/runtime_bindings.rs:446）。
- 未知 facade 返回 Unknown result facade 错误（core/crates/plugin/codegen/src/runtime_bindings.rs:452）。
- 带 API 版本变体的方法经 __operitToolPkgApi.method().since() 或 .between() 生成版本门控函数（core/crates/plugin/codegen/src/runtime_bindings.rs:461）。
- 非 Chat 的版本变体方法再调 .build("Tools.<命名空间>.<方法>")（core/crates/plugin/codegen/src/runtime_bindings.rs:478）。
- __operitInvokeToolsBinding 先构造参数，带设备上下文时调用 __operitDeviceToolCall，否则调用 toolCall（core/crates/plugin/codegen/src/runtime_bindings.rs:389）。
- __operitToolsSelectOverload 在唯一重载时直接选它，首参为对象且存在扁平化重载时选扁平化重载，否则选参数最多的重载（core/crates/plugin/codegen/src/runtime_bindings.rs:348）。
- __operitToolsBuildParameters 按选定重载映射参数：扁平化参数展开对象字段，标量联合后缀参数映射为标量字段，最后追加固定参数（core/crates/plugin/codegen/src/runtime_bindings.rs:361）。
- 除 preserve_object_namespaces（Net、Media）内的命名空间外，扁平化参数展开对象字段时经 __operitToolsSnakeCase 转 snake_case；Net 与 Media 保留原字段名（core/crates/plugin/codegen/src/runtime_bindings.rs:371）。
- `generate_parameter_rules` 读取 JS_TOOL_PARAMETER_RULES 常量，要求恰好 4 个字段：flatten_arguments、scalar_union_suffixes、preserve_object_namespaces、argument_names（core/crates/plugin/codegen/src/runtime_bindings.rs:560）。
- `generate_parameter_rules` 要求每个参数别名是四元组且引用已声明的方法与参数，重复别名报错（core/crates/plugin/codegen/src/runtime_bindings.rs:586）。
- `argument_checks` 为 strict_arguments 的方法生成参数校验：String 参数要求非空且首尾无空白，其他路径类型用 __operitSnapshotJsonObject 快照，不支持的类型报错（core/crates/plugin/codegen/src/runtime_bindings.rs:537）。
- `read_host_method_arguments` 从 HOST_TRAITS 的 trait 中读取每个重载的有序参数名（core/crates/plugin/codegen/src/runtime_bindings.rs:640）。
- `validate_javascript_syntax` 用 tree-sitter 解析生成的 JavaScript，含错误节点时返回 generated JavaScript Tools runtime contains a syntax error 错误（core/crates/plugin/codegen/src/runtime_bindings.rs:680）。
- `runtime_method_name` 去掉方法名前的 r# 前缀与 _overload_ 后缀（core/crates/plugin/codegen/src/runtime_bindings.rs:726）。
- `pascal_case_to_snake_case` 把 PascalCase 变体名还原为 snake_case（core/crates/plugin/codegen/src/runtime_bindings.rs:733）。

### 内置工具名与注册契约

- `REGISTRATION_HELPERS` 列出 8 个注册辅助函数名：registerChatTool、registerSystemOperationTool、registerTerminalTool、registerMusicTool、registerBluetoothTool、registerMemoryTool、registerHttpTool、registerFileSystemTool（core/crates/plugin/codegen/src/registration.rs:12）。
- `generate_builtin_tool_names` 生成 BuiltinToolName 枚举（core/crates/plugin/codegen/src/registration.rs:33）。
- BuiltinToolName 枚举提供 as_str 方法（core/crates/plugin/codegen/src/registration.rs:52）。
- BuiltinToolName 枚举提供 from_name 方法（core/crates/plugin/codegen/src/registration.rs:60）。
- BuiltinToolName 枚举提供 accepts_runtime_result 方法（core/crates/plugin/codegen/src/registration.rs:71）。
- BuiltinToolName 枚举实现 Display（core/crates/plugin/codegen/src/registration.rs:86）。
- `accepts_runtime_result` 对 ExecuteInTerminalSessionStreaming 接受 TerminalStreamEventData 或 TerminalCommandResultData 两种结果（core/crates/plugin/codegen/src/registration.rs:80）。
- `required_tool_entries_in_order` 在源文件中查找 ToolResultMap 结构体，按字段顺序返回工具名与运行时结果变体（core/crates/plugin/codegen/src/registration.rs:158）。
- `runtime_result_variant` 把运行时结果类型映射为结果变体名（core/crates/plugin/codegen/src/registration.rs:180）。
- `runtime_result_variant` 把 String 结果映射为 StringResultData，Value 与 ToolResultData 映射为空（通配），其余类型映射为同名变体（core/crates/plugin/codegen/src/registration.rs:192）。
- `rust_variant_name` 把 snake_case 工具名转为 PascalCase 枚举变体名（core/crates/plugin/codegen/src/registration.rs:199）。
- `check_tool_registration_contract` 对比 ToolResultMap 要求集合与注册文件实际注册集合（core/crates/plugin/codegen/src/registration.rs:102）。
- `check_tool_registration_contract` 在缺失、多余、重复或操作配对错误时返回 ToolRegistration differs from the Rust SDK tool map 错误，错误信息列出四类差异（core/crates/plugin/codegen/src/registration.rs:133）。
- `RegistrationVisitor` 的 visit_expr_call 只处理 REGISTRATION_HELPERS 中的辅助函数调用，记录内置工具名与操作配对（core/crates/plugin/codegen/src/registration.rs:258）。
- `visit_expr_method_call` 处理 registerBuiltinTool 直接注册调用（core/crates/plugin/codegen/src/registration.rs:275）。
- `visit_expr_for_loop` 处理字面量工具名数组驱动的注册循环，循环体使用绑定变量时才记录数组元素（core/crates/plugin/codegen/src/registration.rs:290）。
- `record_operation_pair` 校验分组执行器操作与内置工具的配对（core/crates/plugin/codegen/src/registration.rs:227）。
- `record_operation_pair` 无对应契约时记录 has no contract 错误，操作不符时记录 requires 与 found 对照（core/crates/plugin/codegen/src/registration.rs:244）。
- `expected_operation_variant` 规定：ChatManager、FileSystem、Http、Memory 四族的操作与内置工具同名；PluginChatToolOperation 去掉 Chat 前缀；TtsToolOperation 去掉 Tts 前缀；ThemeToolOperation 去掉 Theme 前缀（core/crates/plugin/codegen/src/registration.rs:399）。
- `expected_operation_variant` 规定 SystemOperationToolOperation 的 DeviceInfo 对应 GetDeviceInfo，其余同名（core/crates/plugin/codegen/src/registration.rs:408）。
- `expected_operation_variant` 规定 TerminalToolOperation 的 8 个内置工具各有固定操作名：GetTerminalInfo 对应 GetTerminalInfo、CreateTerminalSession 对应 CreateSession、ExecuteInTerminalSession 对应 ExecuteInSession、ExecuteInTerminalSessionStreaming 对应 ExecuteInSessionStreaming、ExecuteHiddenTerminalCommand 对应 ExecuteHiddenCommand（core/crates/plugin/codegen/src/registration.rs:413）。
- `expected_operation_variant` 规定 TerminalToolOperation 的 CloseTerminalSession 对应 CloseSession、InputInTerminalSession 对应 InputInSession、GetTerminalSessionScreen 对应 GetSessionScreen（core/crates/plugin/codegen/src/registration.rs:419）。
- `expected_operation_variant` 规定 MusicToolOperation 的 7 个内置工具映射为 Play、Pause、Resume、Stop、Seek、SetVolume、Status（core/crates/plugin/codegen/src/registration.rs:428）。
- `expected_operation_variant` 规定 BluetoothToolOperation 的 19 个内置工具映射为去 Bluetooth 前缀的操作名，前 11 个是 RequestPermission、GetState、RequestEnable、ListBondedDevices、ScanDevices、Connect、Listen、Accept、Send、Read、SendAndRead（core/crates/plugin/codegen/src/registration.rs:445）。
- `expected_operation_variant` 规定 BluetoothToolOperation 的后 8 个是 Close、BleConnect、BleDiscoverServices、BleReadCharacteristic、BleWriteCharacteristic、BleWriteAndReadCharacteristic、BleSubscribeCharacteristic、BleReadNotifications（core/crates/plugin/codegen/src/registration.rs:455）。
- `builtin_tool_name` 把 BuiltinToolName::Variant 路径还原为 snake_case 工具名，兼容括号与分组表达式（core/crates/plugin/codegen/src/registration.rs:324）。
- `operation_variant` 取参数表达式中第一个枚举类型以 ToolOperation 结尾的路径作为操作（core/crates/plugin/codegen/src/registration.rs:372）。
- `pascal_case_to_snake_case` 把 PascalCase 变体名还原为 snake_case（core/crates/plugin/codegen/src/registration.rs:467）。

### 四语言客户端生成

- `generate_plugin_sdk_client_bindings` 为 Rust、Dart、Kotlin、TypeScript 四种语言生成 SDK 客户端（core/crates/plugin/codegen/src/client_codegen.rs:11）。
- 客户端生成共写 7 个文件：Rust generated.rs、Dart generated.dart 与 models.dart、Kotlin OperitPluginSdkGenerated.kt 与 OperitPluginSdkModels.kt、TypeScript generated.ts 与 models.ts（core/crates/plugin/codegen/src/client_codegen.rs:29）。
- `generate_plugin_sdk_surface` 只把 sdk_exposed 且协议为 Call、Factory、Watch、ReverseStream 的方法写入路由白名单，生成 pluginSdkSurface() 函数（core/crates/plugin/codegen/src/client_codegen.rs:64）。
- `collect_objects` 收集对外暴露的 SDK 对象与方法（core/crates/plugin/codegen/src/client_codegen.rs:87）。
- `collect_objects` 丢弃未标记 sdk_exposed 的方法（core/crates/plugin/codegen/src/client_codegen.rs:96）。
- `collect_objects` 把 Call 与 Factory 协议归为 Call，Watch 归为 Watch，ReverseStream 归为 Push（core/crates/plugin/codegen/src/client_codegen.rs:99）。
- `collect_objects` 丢弃 Unsupported 协议的方法（core/crates/plugin/codegen/src/client_codegen.rs:102）。
- `collect_objects` 对同名方法只保留第一个（core/crates/plugin/codegen/src/client_codegen.rs:105）。
- `collect_objects` 对 ReverseStream 方法去掉流参数（core/crates/plugin/codegen/src/client_codegen.rs:111）。
- `collect_objects` 丢弃方法为空的对象（core/crates/plugin/codegen/src/client_codegen.rs:119）。
- `call_return_type` 从 Call 的 Value/ResultValue 取值类型，Factory 返回 Object，无返回值与 ReverseStream 返回空，Watch 返回元素类型（core/crates/plugin/codegen/src/client_codegen.rs:149）。
- `write_if_changed` 只在内容与已存在文件不同时写入（core/crates/plugin/codegen/src/client_codegen.rs:177）。
- `class_name` 由 Operit 前缀加 schema_key 按 . : / - 切分后的首字母大写拼接，再加 Client 后缀（core/crates/plugin/codegen/src/client_codegen.rs:188）。
- `method_name` 把非字母数字字符换成下划线，数字开头补下划线，空名返回 method（core/crates/plugin/codegen/src/client_codegen.rs:208）。
- `validate_argument_type` 只接受标量、Option/Vec/BTreeMap/HashMap 递归类型，以及可序列化目录中的结构体与纯单元枚举，其他类型直接断言失败（core/crates/plugin/codegen/src/client_codegen.rs:231）。
- `sdk_parameters` 的 Rust 参数用 toCoreValue 编码（core/crates/plugin/codegen/src/client_codegen.rs:248）。
- `sdk_parameters` 的 Dart 参数用 dart_messagepack_encode 编码（core/crates/plugin/codegen/src/client_codegen.rs:254）。
- `sdk_parameters` 的 Kotlin 参数用 kotlin_encode_expr 编码（core/crates/plugin/codegen/src/client_codegen.rs:258）。
- `sdk_parameters` 的 TypeScript 参数用 ts_encode_expr 编码（core/crates/plugin/codegen/src/client_codegen.rs:262）。
- 四种语言的参数映射分别拼成 CoreValue::Map、Dart Map 字面量、Kotlin mapOf、TypeScript 对象字面量（core/crates/plugin/codegen/src/client_codegen.rs:268）。
- `render_rust` 的 Call 方法发 CoreCallRequest 并解码 MessagePack 返回值（core/crates/plugin/codegen/src/client_codegen.rs:310）。
- `render_rust` 的 Watch 方法返回 OperitPluginSdkTypedEventStream，Push 方法返回 Box<dyn CoreLinkPushSession>（core/crates/plugin/codegen/src/client_codegen.rs:316）。
- `rust_type` 把 serde_json::Value 映射为 CoreValue，结构体与纯单元枚举映射为 Sdk 前缀模型，其他已知类型映射为 CoreValue，未知类型原样保留（core/crates/plugin/codegen/src/client_codegen.rs:341）。
- `render_rust_models` 为可达结构体生成 Sdk 前缀的 serde 结构体，为纯单元枚举生成 SCREAMING_SNAKE_CASE 枚举（core/crates/plugin/codegen/src/client_codegen.rs:358）。
- `render_dart` 的 Call 方法走 _client.call 或 callTyped（core/crates/plugin/codegen/src/client_codegen.rs:394）。
- `render_dart` 的 Watch 方法返回 Stream，Push 方法返回 PluginSdkPushSink（core/crates/plugin/codegen/src/client_codegen.rs:418）。
- `dart_type` 把 str 映射为 String，Vec<u8> 映射为 Uint8List，整数映射为 int，浮点映射为 double（core/crates/plugin/codegen/src/client_codegen.rs:436）。
- `dart_type` 把 serde_json::Value 映射为 Object?（core/crates/plugin/codegen/src/client_codegen.rs:444）。
- `dart_class_name` 取 Rust 全限定名的最后一段，按 _ 与 - 切分后首字母大写拼接，空结果返回 PluginSdkModel（core/crates/plugin/codegen/src/client_codegen.rs:461）。
- `collect_reachable` 递归收集方法返回值与参数涉及的可序列化类型，穿透引用、Option、Vec、BTreeMap、HashMap 与结构体字段（core/crates/plugin/codegen/src/client_codegen.rs:524）。
- `render_sdk_struct` 为 Dart 结构体生成带 fromMessagePackValue 工厂与 toMessagePackValue 方法的 class（core/crates/plugin/codegen/src/client_codegen.rs:535）。
- `render_sdk_enum` 为纯单元枚举生成带 fromMessagePackValue 与 toMessagePackValue 的 Dart enum（core/crates/plugin/codegen/src/client_codegen.rs:545）。
- `render_kotlin` 的 Call 方法为 suspend fun 走 callTyped，Watch 方法返回 Flow（core/crates/plugin/codegen/src/client_codegen.rs:586）。
- `render_kotlin` 的 Push 方法返回 OperitPluginSdkPushSink（core/crates/plugin/codegen/src/client_codegen.rs:587）。
- `render_typescript` 的 Call 方法返回 Promise（core/crates/plugin/codegen/src/client_codegen.rs:622）。
- `render_typescript` 的 Watch 方法返回 AsyncIterable，Push 方法返回 Promise<OperitPluginSdkPushSink>（core/crates/plugin/codegen/src/client_codegen.rs:630）。
- `ts_type` 在 Dart 类型映射基础上把 Uint8List 换为 Uint8Array、Object? 换为 unknown、bool 换为 boolean、int/double 换为 number、String 换为 string、可空换为 | null、List 换为 Array、Map 换为 Record（core/crates/plugin/codegen/src/client_codegen.rs:644）。
- `ts_public_type` 把生成模型类型限定为 models.<模型名>，替换时只匹配完整标识符（core/crates/plugin/codegen/src/client_codegen.rs:651）。
- `render_typescript_models` 为结构体生成 interface 加 decode/encode 函数，为纯单元枚举生成字符串联合类型加 decode/encode 函数（core/crates/plugin/codegen/src/client_codegen.rs:710）。
- `render_kotlin_models` 内置 decodeBoolean、decodeString、decodeInt、decodeDouble、decodeUnit 五个解码辅助函数（core/crates/plugin/codegen/src/client_codegen.rs:740）。
- `render_kotlin_models` 为结构体生成 data class 加 decode 函数与 toMessagePackValue（core/crates/plugin/codegen/src/client_codegen.rs:754）。
- `render_kotlin_models` 为纯单元枚举生成 enum class 加 decode 与 toMessagePackValue（core/crates/plugin/codegen/src/client_codegen.rs:770）。
- `kotlin_type` 把 Uint8List 换为 ByteArray、Object? 换为 Any?、bool 换为 Boolean、int 换为 Int、double 换为 Double（core/crates/plugin/codegen/src/client_codegen.rs:783）。
- `reachable_sdk_types` 从全部对象方法的返回值与参数出发收集可达的可序列化类型集合（core/crates/plugin/codegen/src/client_codegen.rs:812）。
- 客户端生成的扫描源头是 [[core-proxy|代理生成——扫描、发射器与本地代理运行时]] 的 `scan_core_proxy`（core/crates/proxy/local/build.rs:29）。

### sdk-ipc 的帧与分工

- sdk-ipc 库重导出 PluginSdkClient、编解码函数与 PluginSdkIpcMessage（core/crates/plugin/sdk-ipc/src/lib.rs:9）。
- sdk-ipc 库重导出 PluginSdkLinkTarget、SharedPluginSdkLinkTarget、PluginSdkIpcServer 与 PluginSdkSurface（core/crates/plugin/sdk-ipc/src/lib.rs:15）。
- `PluginSdkIpcMessage` 用 serde tag type 与 content body 编码，共 14 个变体（core/crates/plugin/sdk-ipc/src/frame.rs:10）。
- `PluginSdkIpcMessage` 的调用变体是 Call 与 CallResponse，订阅打开变体是 WatchOpen（core/crates/plugin/sdk-ipc/src/frame.rs:14）。
- `PluginSdkIpcMessage` 的订阅变体是 WatchOpened、WatchSnapshot 与 WatchEvent（core/crates/plugin/sdk-ipc/src/frame.rs:24）。
- `PluginSdkIpcMessage` 的订阅关闭与推送打开变体是 WatchClose、PushOpen 与 PushOpened（core/crates/plugin/sdk-ipc/src/frame.rs:36）。
- `PluginSdkIpcMessage` 的推送变体是 PushItem、PushItemResult、PushClose 与 PushClosed（core/crates/plugin/sdk-ipc/src/frame.rs:50）。
- `PluginSdkIpcMessage` 的协议错误变体是 ProtocolError（core/crates/plugin/sdk-ipc/src/frame.rs:60）。
- `encodePluginSdkIpcMessage` 与 `decodePluginSdkIpcMessage` 复用 operit_link 的 encodeLink/decodeLink 编解码，错误包装为 CoreLinkError::internal（core/crates/plugin/sdk-ipc/src/frame.rs:69）。
- `PluginSdkClient::connect` 接受平台宿主与端点（core/crates/plugin/sdk-ipc/src/client.rs:45）。
- `PluginSdkClient::connect` 注册会话回调（会话建立、收包分发、会话关闭清理）（core/crates/plugin/sdk-ipc/src/client.rs:60）。
- `PluginSdkClient::connect` 的初始请求序号为 1（core/crates/plugin/sdk-ipc/src/client.rs:58）。
- `nextRequestId` 生成 plugin-sdk-{序号} 格式的请求 ID，序号每次加一（core/crates/plugin/sdk-ipc/src/client.rs:105）。
- `PluginSdkClient::call` 把请求登记到 pendingCalls 后发送 Call 帧（core/crates/plugin/sdk-ipc/src/client.rs:141）。
- call 发送失败时移除登记，响应通道关闭时返回错误响应（core/crates/plugin/sdk-ipc/src/client.rs:152）。
- `watchSnapshot` 发送 WatchSnapshot 帧，返回收到的第一个事件（core/crates/plugin/sdk-ipc/src/client.rs:163）。
- `watchSnapshot` 把请求登记为 Snapshot 类型的 pendingCalls（core/crates/plugin/sdk-ipc/src/client.rs:173）。
- `watch` 发送 WatchOpen（core/crates/plugin/sdk-ipc/src/client.rs:188）。
- `watch` 返回的流关闭时发送不带错误的 WatchClose（core/crates/plugin/sdk-ipc/src/client.rs:215）。
- `openPush` 发送 PushOpen（core/crates/plugin/sdk-ipc/src/client.rs:225）。
- `openPush` 把推送登记到 pendingPushOpens（core/crates/plugin/sdk-ipc/src/client.rs:234）。
- `openPush` 成功后返回序号从 0 开始的 PluginSdkPushSession（core/crates/plugin/sdk-ipc/src/client.rs:246）。
- `PluginSdkPushSession::send` 按序号递增发送 PushItem，等待 PushItemResult 确认（core/crates/plugin/sdk-ipc/src/client.rs:350）。
- `PluginSdkPushSession::close` 登记 pendingPushCloses，发送 PushClose，等待 PushClosed 确认（core/crates/plugin/sdk-ipc/src/client.rs:373）。
- `dispatchIncoming` 把 CallResponse 还给 pendingCalls（core/crates/plugin/sdk-ipc/src/client.rs:401）。
- `dispatchIncoming` 把 WatchOpened 还给 pendingWatches（core/crates/plugin/sdk-ipc/src/client.rs:408）。
- `dispatchIncoming` 的 WatchEvent 先还给快照等待者，否则发给订阅通道（core/crates/plugin/sdk-ipc/src/client.rs:416）。
- `dispatchIncoming` 在收到 WatchClose 时移除订阅，并以 WATCH_CLOSED 使等待者失败（core/crates/plugin/sdk-ipc/src/client.rs:432）。
- `dispatchIncoming` 忽略客户端方向的消息与 ProtocolError（core/crates/plugin/sdk-ipc/src/client.rs:455）。
- `failPending` 在会话关闭时清空全部订阅，使所有待处理调用、订阅、推送打开、推送条目与推送关闭失败（core/crates/plugin/sdk-ipc/src/client.rs:475）。
- `PluginSdkClient` 实现 CoreLinkClient，四个方法直通同名 inherent 方法（core/crates/plugin/sdk-ipc/src/client.rs:275）。
- `PluginSdkClient` 实现 CoreLinkSharedClient，四个方法无需可变所有权（core/crates/plugin/sdk-ipc/src/client.rs:306）。
- `PluginSdkLinkTarget` trait 只定义 call、watchSnapshot、watch、openPush 四个转发方法，不解释对象 ID、方法名、参数与返回值（core/crates/plugin/sdk-ipc/src/handler.rs:16）。
- `SharedPluginSdkLinkTarget` 是 Arc<dyn PluginSdkLinkTarget> 的别名（core/crates/plugin/sdk-ipc/src/handler.rs:31）。
- 任何实现 CoreLinkSharedClient 且 Send + Sync + 'static 的类型自动实现 PluginSdkLinkTarget，方法直通底层共享客户端（core/crates/plugin/sdk-ipc/src/handler.rs:37）。
- `PluginSdkSurface` 用对象 ID 到方法名集合的映射记录对外暴露的路由（core/crates/plugin/sdk-ipc/src/surface.rs:8）。
- `expose` 把一个调用、订阅或推送方法加入暴露路由表（core/crates/plugin/sdk-ipc/src/surface.rs:18）。
- `check` 在路由未暴露时返回 PLUGIN_SDK_ROUTE_NOT_EXPOSED 错误，错误信息包含对象与方法名（core/crates/plugin/sdk-ipc/src/surface.rs:31）。
- `PluginSdkIpcServer::new` 接受宿主、任务调度器、端点、Link 目标与路由白名单（core/crates/plugin/sdk-ipc/src/server.rs:47）。
- `start` 二次调用时返回 PLUGIN_SDK_IPC_ALREADY_STARTED 错误（core/crates/plugin/sdk-ipc/src/server.rs:71）。
- `start` 通过宿主启动监听器，并以 plugin-sdk-ipc 为任务名在宿主运行时调度一个转发工作循环（core/crates/plugin/sdk-ipc/src/server.rs:104）。
- `stop` 先取消全部会话状态并发送停机信号（core/crates/plugin/sdk-ipc/src/server.rs:142）。
- `stop` 最后停止宿主监听器（core/crates/plugin/sdk-ipc/src/server.rs:155）。
- `enqueue` 解码失败时回发 ProtocolError，否则把消息排入工作循环的无界通道（core/crates/plugin/sdk-ipc/src/server.rs:172）。
- `handleMessage` 把 Call、WatchOpen、WatchSnapshot、WatchClose、PushOpen、PushItem、PushClose 分发到各自处理函数（core/crates/plugin/sdk-ipc/src/server.rs:192）。
- `handleMessage` 收到服务端方向的消息时回发 CLIENT_MESSAGE_NOT_ALLOWED 协议错误（core/crates/plugin/sdk-ipc/src/server.rs:218）。
- `handleCall` 先校验路由是否暴露，未暴露时直接返回错误 CallResponse，否则转发给 Link 目标并回发响应（core/crates/plugin/sdk-ipc/src/server.rs:230）。
- `handleWatchSnapshot` 处理订阅快照请求（core/crates/plugin/sdk-ipc/src/server.rs:243）。
- `handleWatchSnapshot` 在路由未暴露时直接发带错误的 WatchClose（core/crates/plugin/sdk-ipc/src/server.rs:252）。
- `handleWatchSnapshot` 成功时先发带 requestId 的 WatchEvent 再发无错误的 WatchClose（core/crates/plugin/sdk-ipc/src/server.rs:266）。
- `handleWatchSnapshot` 在目标调用失败时发带错误的 WatchClose（core/crates/plugin/sdk-ipc/src/server.rs:278）。
- `handleWatchOpen` 用 registerRequest 登记请求（core/crates/plugin/sdk-ipc/src/server.rs:304）。
- `registerRequest` 以 (会话 ID, 请求 ID) 为键登记活跃请求（core/crates/plugin/sdk-ipc/src/server.rs:494）。
- `registerRequest` 对重复请求 ID 返回 REQUEST_ID_IN_USE 错误（core/crates/plugin/sdk-ipc/src/server.rs:503）。
- `forwardStream` 按序转发事件（core/crates/plugin/sdk-ipc/src/server.rs:343）。
- `forwardStream` 给每个事件打上 requestId 后转发，取消标志置位时停止（core/crates/plugin/sdk-ipc/src/server.rs:355）。
- `forwardStream` 正常结束时发送无错误的 WatchClose（core/crates/plugin/sdk-ipc/src/server.rs:367）。
- `handlePushOpen` 打开 Core 推送流后以 (会话 ID, 推送 ID) 为键保存会话句柄（core/crates/plugin/sdk-ipc/src/server.rs:397）。
- `handlePushOpen` 成功后回发 PushOpened 确认（core/crates/plugin/sdk-ipc/src/server.rs:402）。
- `handlePushItem` 在推送不存在时返回 PUSH_NOT_FOUND 错误（core/crates/plugin/sdk-ipc/src/server.rs:436）。
- `handlePushItem` 在推送已关闭时返回 PUSH_CLOSED 错误（core/crates/plugin/sdk-ipc/src/server.rs:448）。
- `handlePushClose` 在推送不存在时返回 PUSH_NOT_FOUND，已关闭时返回 PUSH_CLOSED（core/crates/plugin/sdk-ipc/src/server.rs:478）。
- `handlePushClose` 移除保存的推送会话并关闭它，回发 PushClosed 确认（core/crates/plugin/sdk-ipc/src/server.rs:486）。
- `finishRequest` 只在登记句柄一致时移除请求，返回请求是否仍可发布（core/crates/plugin/sdk-ipc/src/server.rs:518）。
- `cancelRequest` 把指定活跃请求的取消标志置位（core/crates/plugin/sdk-ipc/src/server.rs:535）。
- `cancelSessionState` 传入 None 时取消全部会话的请求并清空推送会话，传入会话 ID 时只清理该会话（core/crates/plugin/sdk-ipc/src/server.rs:553）。
- `PluginSdkIpcServer` 被释放时 Drop 调用 stop 停止宿主监听器（core/crates/plugin/sdk-ipc/src/server.rs:592）。
- 帧的底层编解码属于 [[core-rslink|RsLink——Rust 间 Link 协议层]] 的 operit_link（core/crates/plugin/sdk-ipc/src/frame.rs:69）。

### sdk-ipc-bridge 与应用接线

- `OperitPluginSdkIpcBridge` 只有 36 行，结构体只持有一个 PluginSdkIpcServer（core/crates/plugin/sdk-ipc-bridge/src/lib.rs:10）。
- `OperitPluginSdkIpcBridge::new` 接受宿主、任务调度器、端点、Link 目标与路由白名单，直接构造 PluginSdkIpcServer，不引入工具专属处理器（core/crates/plugin/sdk-ipc-bridge/src/lib.rs:19）。
- `OperitPluginSdkIpcBridge::start` 与 stop 直接转发给内部服务器，返回 Result<(), CoreLinkError>（core/crates/plugin/sdk-ipc-bridge/src/lib.rs:31）。
- `CoreApplication` 只在宿主提供 pluginSdkIpcHost 时创建 OperitPluginSdkIpcBridge，端点用 PluginSdkIpcEndpoint::standard()，目标为节点路由，路由白名单为 pluginSdkSurface()（core/crates/application/core/src/lib.rs:172）。
- 桥接器创建后立即启动（core/crates/application/core/src/lib.rs:178）。
- 创建桥接器时缺少宿主任务调度器直接返回 Plugin SDK IPC requires a Host task scheduler 错误（core/crates/application/core/src/lib.rs:167）。
- 应用侧组装见 [[core-application|应用组装——CoreApplication 门面]]（core/crates/application/core/src/lib.rs:172）。

### 构建时触发

- codegen 二进制接受命令、SDK 源码根、声明输出根三个参数，多余参数返回 unexpected codegen argument 错误（core/crates/plugin/codegen/src/main.rs:12）。
- generate-runtime 命令调用 generate_js_tools_runtime，绑定表固定为 js_sdk/runtime_bindings.rs（core/crates/plugin/codegen/src/main.rs:18）。
- generate 命令调用 generate_declaration_tree（core/crates/plugin/codegen/src/main.rs:21）。
- check 命令调用 check_declaration_tree（core/crates/plugin/codegen/src/main.rs:24）。
- 未知命令返回 unknown codegen command 错误（core/crates/plugin/codegen/src/main.rs:26）。
- plugin/sdk 的 build.rs 在构建时依次运行 generate_js_tools_runtime（输出 OUT_DIR/js_tools.js）、generate_declaration_tree（输出 OUT_DIR/types）、generate_builtin_tool_names（输出 OUT_DIR/builtin_tool_names.rs）（core/crates/plugin/sdk/build.rs:55）。
- sdk 的 build.rs 把声明输出目录定为 OUT_DIR/types，源码变化时 cargo 重新运行构建脚本（core/crates/plugin/sdk/build.rs:15）。
- proxy/local 的 build.rs 先用 scan_core_proxy 扫描 Core 代理（core/crates/proxy/local/build.rs:29）。
- proxy/local 的 build.rs 把客户端写到仓库根的 plugins/sdk/clients，把路由白名单写到 OUT_DIR/plugin_sdk_surface.rs（core/crates/proxy/local/build.rs:52）。
- tool/services 的 build.rs 在每次构建时用 check_tool_registration_contract 校验 tool_types.rs 与 ToolRegistration.rs 的一致性（core/crates/tool/services/build.rs:16）。

### 声明宏

- `js_declaration` 是过程宏属性，读取声明作用域、公开名、分类与对象级字段只读性等元数据（core/crates/plugin/sdk-macros/src/lib.rs:13）。
- `js_declaration` 不生成任何 JavaScript 运行时代码，Rust 保留原始类型与字段（core/crates/plugin/sdk-macros/src/lib.rs:11）。
- `js_declaration` 对结构体字段校验 js(readonly)：未知选项与重复 readonly 均报编译错误（core/crates/plugin/sdk-macros/src/lib.rs:28）。
- `js_declaration` 校验后删除全部 js 属性再输出原条目（core/crates/plugin/sdk-macros/src/lib.rs:37）。
- `js_declaration` 对枚举、trait、类型别名直接透传，其他条目报 js_declaration requires a struct, enum, trait, or type alias 编译错误（core/crates/plugin/sdk-macros/src/lib.rs:45）。
- `tool_display` 是作用于结构体的过程宏属性，读取每个字段的 display(action/icon/target/result) 元数据（core/crates/plugin/sdk-macros/src/lib.rs:61）。
- `tool_display` 未指定图标时默认图标为 tool（core/crates/plugin/sdk-macros/src/lib.rs:96）。
- `tool_display` 的 result 渲染器只接受空值、text、directory、fileDiff，未知值报 unknown result renderer 编译错误（core/crates/plugin/sdk-macros/src/lib.rs:104）。
- `tool_display` 为 BuiltinToolName 生成 display() 方法，按字段名返回 ToolDisplayDeclaration::builtin（core/crates/plugin/sdk-macros/src/lib.rs:111）。
- `tool_display` 删除全部 display 属性，未命名字段直接 panic（core/crates/plugin/sdk-macros/src/lib.rs:93）。

## 关键符号

- `generate_declaration_tree` — 声明树生成主入口，输出目录加渲染加条件写入（core/crates/plugin/codegen/src/declarations.rs:125）
- `check_declaration_tree` — 声明树一致性校验主入口（core/crates/plugin/codegen/src/declarations.rs:158）
- `MODULES` — 22 个 ModuleSpec 的声明模块清单（core/crates/plugin/codegen/src/declarations.rs:29）
- `EmitContext` — 声明发射上下文，收 impl、root_traits 与 named_paths（core/crates/plugin/codegen/src/declarations.rs:333）
- `generate_js_tools_runtime` — JavaScript Tools 运行时生成主入口（core/crates/plugin/codegen/src/runtime_bindings.rs:288）
- `HOST_TRAITS` — 17 组 (Rust 文件, Host trait, 命名空间) 映射（core/crates/plugin/codegen/src/runtime_bindings.rs:12）
- `generate_plugin_sdk_client_bindings` — 四语言客户端生成主入口（core/crates/plugin/codegen/src/client_codegen.rs:11）
- `generate_plugin_sdk_surface` — 路由白名单生成主入口（core/crates/plugin/codegen/src/client_codegen.rs:59）
- `collect_objects` — 对外暴露对象与方法的收集器（core/crates/plugin/codegen/src/client_codegen.rs:87）
- `generate_builtin_tool_names` — BuiltinToolName 枚举生成主入口（core/crates/plugin/codegen/src/registration.rs:21）
- `check_tool_registration_contract` — 工具注册契约校验主入口（core/crates/plugin/codegen/src/registration.rs:99）
- `REGISTRATION_HELPERS` — 8 个注册辅助函数名清单（core/crates/plugin/codegen/src/registration.rs:12）
- `expected_operation_variant` — 分组执行器操作与内置工具的配对映射表（core/crates/plugin/codegen/src/registration.rs:399）
- `PluginSdkIpcMessage` — 14 个变体的 IPC 帧枚举（core/crates/plugin/sdk-ipc/src/frame.rs:10）
- `PluginSdkClient` — SDK 侧 IPC 客户端，持有 pendingCalls、pendingWatches、pendingPushOpens 等待处理表（core/crates/plugin/sdk-ipc/src/client.rs:39）
- `PluginSdkIpcServer` — Operit 侧 IPC 服务器，持有路由白名单与活跃请求表（core/crates/plugin/sdk-ipc/src/server.rs:31）
- `PluginSdkSurface` — 对象 ID 到方法名集合的路由白名单（core/crates/plugin/sdk-ipc/src/surface.rs:8）
- `PluginSdkLinkTarget` — 只定义四个转发方法的 trait（core/crates/plugin/sdk-ipc/src/handler.rs:13）
- `OperitPluginSdkIpcBridge` — 只持有一个 PluginSdkIpcServer 的 36 行桥接器（core/crates/plugin/sdk-ipc-bridge/src/lib.rs:9）
- `js_declaration` — 声明元数据的过程宏属性（core/crates/plugin/sdk-macros/src/lib.rs:13）
- `tool_display` — 工具展示元数据的过程宏属性（core/crates/plugin/sdk-macros/src/lib.rs:58）

## 调用链

1. 构建时，plugin/sdk 的 build.rs 依次运行 generate_js_tools_runtime、generate_declaration_tree、generate_builtin_tool_names（core/crates/plugin/sdk/build.rs:55）。
2. 构建时，proxy/local 的 build.rs 用 scan_core_proxy 扫描 Core 代理，生成四语言客户端与路由白名单（core/crates/proxy/local/build.rs:52）。
3. 构建时，tool/services 的 build.rs 用 check_tool_registration_contract 校验工具注册与 Rust SDK 工具映射一致（core/crates/tool/services/build.rs:16）。
4. 应用启动时，CoreApplication 只在宿主提供 pluginSdkIpcHost 时创建 OperitPluginSdkIpcBridge（core/crates/application/core/src/lib.rs:172）。
5. 桥接器创建后立即启动，start 转发给内部 PluginSdkIpcServer（core/crates/application/core/src/lib.rs:178）。
6. 插件调用时，PluginSdkClient::call 把请求登记到 pendingCalls 后发送 Call 帧（core/crates/plugin/sdk-ipc/src/client.rs:141）。
7. 服务端收到 Call 帧后，handleCall 先校验路由是否暴露，未暴露直接返回错误 CallResponse，否则转发给 Link 目标并回发响应（core/crates/plugin/sdk-ipc/src/server.rs:230）。
8. 插件订阅时，PluginSdkClient::watch 把订阅登记到 pendingWatches 与 watches，发送 WatchOpen（core/crates/plugin/sdk-ipc/src/client.rs:188）。
9. 服务端收到 WatchOpen 后，handleWatchOpen 用 registerRequest 登记请求，forwardStream 给每个事件打上 requestId 后按序转发（core/crates/plugin/sdk-ipc/src/server.rs:304）。
10. 插件推送时，PluginSdkClient::openPush 把推送登记到 pendingPushOpens，发送 PushOpen（core/crates/plugin/sdk-ipc/src/client.rs:225）。
11. 服务端收到 PushOpen 后，handlePushOpen 打开 Core 推送流，以 (会话 ID, 推送 ID) 为键保存会话句柄，成功后回发 PushOpened 确认（core/crates/plugin/sdk-ipc/src/server.rs:397）。
12. 帧编解码全程复用 operit_link 的 encodeLink/decodeLink（core/crates/plugin/sdk-ipc/src/frame.rs:69）。

## 来源

seed 文件（7 个，共 3921 行）：

- core/crates/plugin/codegen/src/lib.rs
- core/crates/plugin/codegen/src/declarations.rs
- core/crates/plugin/codegen/src/client_codegen.rs
- core/crates/plugin/codegen/src/registration.rs
- core/crates/plugin/sdk-macros/src/lib.rs
- core/crates/plugin/sdk-ipc/src/lib.rs
- core/crates/plugin/sdk-ipc-bridge/src/lib.rs

写作时补充阅读（非 seed，用于回答大纲问题 ② 与生成触发点）：

- core/crates/plugin/codegen/src/runtime_bindings.rs
- core/crates/plugin/codegen/src/main.rs
- core/crates/plugin/sdk-ipc/src/client.rs
- core/crates/plugin/sdk-ipc/src/frame.rs
- core/crates/plugin/sdk-ipc/src/handler.rs
- core/crates/plugin/sdk-ipc/src/server.rs
- core/crates/plugin/sdk-ipc/src/surface.rs
- core/crates/plugin/sdk/build.rs
- core/crates/proxy/local/build.rs
- core/crates/tool/services/build.rs
- core/crates/application/core/src/lib.rs
