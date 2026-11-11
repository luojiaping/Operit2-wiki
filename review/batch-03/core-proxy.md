---
title: 代理生成——扫描、发射器与本地代理运行时
module: core
platforms: [all]
sources: 6
date: 2026-11-11
---

## 概述

Proxy crates 负责 core-app 本地代理面及其代码生成器（`core/crates/proxy/README.md:3`）。
代理生成是面向本地 core app 调用的根注册扫描，路由生成是面向 Rust 内部路由调用的注解驱动扫描，两者属于不同领域（`core/crates/proxy/README.md:5`）。
Proxy crates 对本地调用使用共享 link 值协议（`core/crates/proxy/README.md:17`）。
README 声明的边界：Proxy crates 不得成为 router、space runtime、access server 或 peer-link 生命周期的所有者（`core/crates/proxy/README.md:17`）。
README 声明的边界：生成的本地代理分发不得查询路由运行时状态，也不得决定一次调用或 watch 是否跨节点，该决定属于 Rust 内部路由包装器（`core/crates/proxy/README.md:19`）。

## AI 速览

- `scan_core_proxy` — 从 15 个显式注册的源根扫描源码，生成语言无关的代理 IR（`core/crates/proxy/scan/src/lib.rs:96`）
- `CoreProxyRegisteredRoots` — 14 个源码根与 proxy manifest 目录的显式注册表（`core/crates/proxy/scan/src/lib.rs:22`）
- `CoreProxyScanOutput` — 一次扫描的产物：objects、序列化类型定义、错误类型定义（`core/crates/proxy/scan/src/lib.rs:88`）
- `stable_target` — schema 键到目标地址的映射：`core/{schema_key}`（`core/crates/proxy/scan/src/lib.rs:244`）
- `write_rust_proxy_artifacts` — 写出 Rust 分发代码与 schema JSON（`core/crates/proxy/rust-codegen/src/lib.rs:16`）
- `write_dart_proxy_artifacts` — 写出 Flutter Dart 模型与客户端（`core/crates/proxy/dart-codegen/src/lib.rs:44`）
- `LocalCoreProxy` — 本地代理运行时：持有应用、分发调用、管理流池（`core/crates/proxy/local/src/lib.rs:36`）
- `LocalApplicationBridgeTarget` — 应用自有 Link 请求的桥契约（`core/crates/proxy/bridge/src/lib.rs:12`）
- `LocalApplicationSharedClient` — 桥目标到共享 Link 客户端的适配器（`core/crates/proxy/bridge/src/lib.rs:36`）
- `CoreStreamPool` — 代理自有的流池，收养与打开流（`core/crates/proxy/local/src/lib.rs:49`）
- 主入口（扫描）：`scan_core_proxy`（`core/crates/proxy/scan/src/lib.rs:96`）
- 主入口（Rust 发射）：`write_rust_proxy_artifacts`（`core/crates/proxy/rust-codegen/src/lib.rs:16`）
- 主入口（Dart 发射）：`write_dart_proxy_artifacts`（`core/crates/proxy/dart-codegen/src/lib.rs:44`）
- 主入口（运行时）：`new` 接收 `OperitApplication`（`core/crates/proxy/local/src/lib.rs:128`）
- 数据流向：源码 → `scan_core_proxy` → 代理 IR（`core/crates/proxy/scan/src/lib.rs:96`）
- 数据流向：代理 IR → Rust 发射器 → `generated_core_dispatch.rs`（`core/crates/proxy/rust-codegen/src/lib.rs:25`）
- 数据流向：代理 IR → `write_dart_proxy_artifacts`（`core/crates/proxy/dart-codegen/src/lib.rs:44`）
- 数据流向：Dart 发射器写出 `CoreProxyModels.g.dart`（`core/crates/proxy/dart-codegen/src/lib.rs:55`）
- 数据流向：对象地址由 `stable_target` 生成（`core/crates/proxy/scan/src/lib.rs:215`）

## 核心机制

### 扫描：从源码到代理 IR

- `CoreProxyRegisteredRoots` 显式登记 14 个源码根目录，外加 proxy manifest 目录（`core/crates/proxy/scan/src/lib.rs:22`）
- CoreProxyRegisteredRoots::from_proxy_manifest_dir 从 proxy crate 路径派生各根目录，例如 runtime 根指向 `../../runtime/application/src`（`core/crates/proxy/scan/src/lib.rs:44`）
- `CoreProxyScanConfig` 包装根注册表（`core/crates/proxy/scan/src/lib.rs:69`）。
`from_proxy_manifest_dir` 由 proxy crate 路径创建标准扫描配置（`core/crates/proxy/scan/src/lib.rs:80`）。
- 本文件重导出 `operit_rslink_codegen` 的全部符号，代理 IR 类型来自该共享库，见 [[core-rslink|RsLink]]（`core/crates/proxy/scan/src/lib.rs:17`）。
- `scan_core_proxy` 为 15 个源根各指定 crate 名，例如 runtime 根为 `operit_runtime`、proxy 根为 `operit_proxy_local`、model 根为 `operit_model`（`core/crates/proxy/scan/src/lib.rs:97`）
- 扫描从 `CARGO_CFG_TARGET_ARCH` 读取目标架构，缺失时 panic，并对受限根调用 `enforce_host_platform_boundaries` 做宿主平台边界检查（`core/crates/proxy/scan/src/lib.rs:126`）。
- `emit_source_tree_rerun_if_changed` 递归遍历源树，把每个目录与文件登记为 `cargo:rerun-if-changed`（`core/crates/proxy/scan/src/lib.rs:233`）
- `collect_serializable_type_definitions` 从全部源根收集可序列化类型定义（`core/crates/proxy/scan/src/lib.rs:149`）
- `serializable_types` 只保留 `supports_serialize` 的类型，`deserializable_types` 只保留 `supports_deserialize` 的类型（`core/crates/proxy/scan/src/lib.rs:161`）
- `collect_type_registry` 从全部源根收集类型注册表（`core/crates/proxy/scan/src/lib.rs:167`）
- `object_specs` 以 core proxy、runtime、store、tool、provider、node runtime 六个根为对象规约来源（`core/crates/proxy/scan/src/lib.rs:171`）
- `collect_public_object_types` 从全部源根收集公开对象类型（`core/crates/proxy/scan/src/lib.rs:176`）
- 每个对象规约由 `scan_object` 扫描，输入为可序列化类型集合、可反序列化类型集合与类型注册表（`core/crates/proxy/scan/src/lib.rs:184`）
- `discover_factory_object_specs` 从已扫描对象、对象规约与公开对象类型中发现工厂对象规约（`core/crates/proxy/scan/src/lib.rs:192`）
- `mark_factory_methods` 在已扫描对象上标记工厂方法（`core/crates/proxy/scan/src/lib.rs:200`）
- 工厂规约同样经 `scan_object` 扫描后追加到 objects（`core/crates/proxy/scan/src/lib.rs:205`）
- 扫描完成后 objects 按 `schema_key` 排序（`core/crates/proxy/scan/src/lib.rs:212`）
- 每个对象的 `object_id` 由 `stable_target` 生成；重复 `object_id` 触发 `Duplicate Core target` 断言（`core/crates/proxy/scan/src/lib.rs:215`）。
- `stable_target` 把 schema 名直接编码为 `core/{schema_key}`，不用注册表索引或哈希（`core/crates/proxy/scan/src/lib.rs:244`）
- `CoreProxyScanOutput` 携带 proxy manifest 目录、objects、序列化类型定义与错误类型定义（`core/crates/proxy/scan/src/lib.rs:88`）

### Rust 发射器：生成分发代码与 schema

- `write_rust_proxy_artifacts` 写出生成的 Rust 代理分发与 schema 产物（`core/crates/proxy/rust-codegen/src/lib.rs:16`）。
Rust 发射器渲染 schema JSON 与生成的 Rust 分发代码，写入 `generated_core_dispatch.rs`，并返回 schema JSON 字符串（`core/crates/proxy/rust-codegen/src/lib.rs:23`）。
- schema 产物写到仓库根 core/generated/core_proxy_schema.json；仓库根由 proxy manifest 目录上溯四级得到，要求 proxy/local 位于 `core/crates/proxy` 之下（`core/crates/proxy/rust-codegen/src/lib.rs:36`）
- `write_generated_file` 仅在内容字节变化时才写文件（`core/crates/proxy/rust-codegen/src/lib.rs:45`）
- local crate 通过 `include!` 引入 OUT_DIR/generated_core_dispatch.rs 中的生成分发代码（`core/crates/proxy/local/src/lib.rs:22`）
- `pluginSdkSurface()` 返回由显式源码注解生成的 SDK 路由面 `PluginSdkSurface`（`core/crates/proxy/local/src/lib.rs:29`）

### Dart 发射器：生成 Flutter 模型与客户端

- `write_dart_proxy_artifacts` 把生成的 Dart 产物写到生成目录（`core/crates/proxy/dart-codegen/src/lib.rs:44`）。
- 生成目录为 apps/flutter/app/lib/core/proxy/generated/，仓库根由 manifest 目录上溯四级得到（`core/crates/proxy/dart-codegen/src/lib.rs:48`）
- 生成的 Dart 产物为 `CoreProxyModels.g.dart` 与 `CoreProxyClients.g.dart`（`core/crates/proxy/dart-codegen/src/lib.rs:55`）
- 生成的 Dart 文件以 `// GENERATED CODE - DO NOT MODIFY BY HAND` 开头（`core/crates/proxy/dart-codegen/src/lib.rs:2084`）
- `render_dart_models` 先收录从对象方法可达的可序列化类型，再经 `include_source_tree_model_types` 额外收录 operit_node_runtime 的源码树模型类型（`core/crates/proxy/dart-codegen/src/lib.rs:76`，同文件 :79 调用该额外收录函数，函数定义在 :338）。
- 模型类型按 `full_type` 排序（`core/crates/proxy/dart-codegen/src/lib.rs:84`）。
- 生成的模型文件导入 `dart:async`、`dart:typed_data`、`CoreLinkCodec` 与 `CoreLinkProtocol`（`core/crates/proxy/dart-codegen/src/lib.rs:84`）
- `fromCoreLinkError` 从 `CoreLinkError` 构造 `CoreProxyErrorDetails`（`core/crates/proxy/dart-codegen/src/lib.rs:137`）
- 错误详情模型的字段为 `errorType`、`message`、`variant`、`kind`、`httpStatus`、`remoteMessage`、`fields`（`core/crates/proxy/dart-codegen/src/lib.rs:165`）
- 结构体模型生成 Dart 类，文档注明对应的 Rust 类型（`core/crates/proxy/dart-codegen/src/lib.rs:640`）。
- 结构体模型提供 `fromJson` 工厂（`core/crates/proxy/dart-codegen/src/lib.rs:657`）
- 结构体模型提供 `toJson`（`core/crates/proxy/dart-codegen/src/lib.rs:693`）
- 结构体模型提供 `fromMessagePack` 工厂做直接 MessagePack 解码（`core/crates/proxy/dart-codegen/src/lib.rs:732`）
- 解码时缺失且无 serde 默认值的字段抛 `FormatException`（`core/crates/proxy/dart-codegen/src/lib.rs:762`）
- `dart_field_default_expr` 只为带 serde default 的字段返回默认值表达式（`core/crates/proxy/dart-codegen/src/lib.rs:32`）
- `dart_default_value` 给 Dart 类型提供默认值：`String` 为 `''`、`int` 为 `0`、`double` 为 `0.0`、`bool` 为 `false`、`Uint8List` 为 `Uint8List(0)`、`List` 为 `const []`、`Map` 为 `const {}`、可空类型与其余类型为 `null`（`core/crates/proxy/dart-codegen/src/lib.rs:17`）
- 纯单元枚举生成 Dart enum，各变体带 json 名（`core/crates/proxy/dart-codegen/src/lib.rs:792`）。
- 未知枚举值抛 `ArgumentError`（`core/crates/proxy/dart-codegen/src/lib.rs:816`）。
- 纯单元枚举的 `fromMessagePack` 委托给 `fromJson`（`core/crates/proxy/dart-codegen/src/lib.rs:820`）
- 带标签枚举的生成类持有 `tag` 字段，记录当前变体（`core/crates/proxy/dart-codegen/src/lib.rs:890`）
- 无字段变体生成无参工厂（`core/crates/proxy/dart-codegen/src/lib.rs:866`）
- 带字段变体生成要求传入字段的工厂（`core/crates/proxy/dart-codegen/src/lib.rs:883`）
- 非单元的普通枚举在模型渲染中被跳过，不生成任何内容（`core/crates/proxy/dart-codegen/src/lib.rs:118`）
- `GeneratedCoreProxyClients` 类持有 `OperitRuntimeBridge`（`core/crates/proxy/dart-codegen/src/lib.rs:202`）。
- 对象 getter 排除 `FactoryMethodConstruct` 构造的对象（`core/crates/proxy/dart-codegen/src/lib.rs:208`）
- 请求 ID 由 `nextCoreLinkRequestId` 分配；`_coreProxyArgs` 先合并 `objectArgs` 再合并调用参数（`core/crates/proxy/dart-codegen/src/lib.rs:200`）
- `chatRuntimeHolderMain` 额外生成 `chatRuntimeHolderMainForSlot`，以 `__core_instance_id` 传入槽位 ID（`core/crates/proxy/dart-codegen/src/lib.rs:222`）
- `dart_namespace_prefixes` 收集每个 schema 键的全部带点前缀，作为 Dart 命名空间（`core/crates/proxy/dart-codegen/src/lib.rs:257`）
- 每个 schema 命名空间生成一个 Dart 类（`core/crates/proxy/dart-codegen/src/lib.rs:299`）。
- 对象客户端类持有 `bridge`、`objectId` 与 `objectArgs`（`core/crates/proxy/dart-codegen/src/lib.rs:356`）。
- 对象客户端的工厂方法按 `factory_protocol` 分派到 `render_dart_factory_method`（`core/crates/proxy/dart-codegen/src/lib.rs:362`）
- 对象客户端的调用方法与 watch 方法按 `call_protocol` 与 `watch_protocol` 分派（`core/crates/proxy/dart-codegen/src/lib.rs:370`）
- 对象客户端的反向流方法按 `reverse_stream_protocol` 分派（`core/crates/proxy/dart-codegen/src/lib.rs:376`）
- `application` 对象额外生成 `runCoreCommand`，经 `bridge.callApplication` 执行 CLI 风格的 Core 命令（`core/crates/proxy/dart-codegen/src/lib.rs:386`）
- 反向流方法返回 `Future<void>`，经 `bridge.push` 发送 `CorePushRequest`（`core/crates/proxy/dart-codegen/src/lib.rs:445`）。
反向流方法逐项 `sink.add`，最后在 `finally` 中关闭 sink（`core/crates/proxy/dart-codegen/src/lib.rs:460`）。
- 调用方法返回 Future<返回类型>（`core/crates/proxy/dart-codegen/src/lib.rs:481`）。
调用方法经 bridge 发送 `CoreCallRequest`（`core/crates/proxy/dart-codegen/src/lib.rs:494`）。
- 登记表中的方法走 `callControlBytes`，其余走 `callBytes`（`core/crates/proxy/dart-codegen/src/lib.rs:488`）。
- `control_call_registry` 只含一对（`services.runtimeHostInteractionService`，`respondOwnerHostInteraction`）（`core/crates/proxy/dart-codegen/src/lib.rs:518`）
- `void` 返回用 `decodeNativeCoreVoidResult` 解码，其余返回用 `decodeNativeCoreResult` 解码，并以 `bridge.openEmbeddedCoreStream` 作为嵌入流工厂（`core/crates/proxy/dart-codegen/src/lib.rs:505`）
- 工厂方法由 `render_dart_factory_method` 生成（`core/crates/proxy/dart-codegen/src/lib.rs:525`）。
工厂参数以 `__core_factory_arg_{index}` 为键传入（`core/crates/proxy/dart-codegen/src/lib.rs:550`）。
工厂方法返回目标 schema 键的新代理实例，工厂目标对象必须已生成（`core/crates/proxy/dart-codegen/src/lib.rs:565`）。
- watch 方法由 `render_dart_watch_method` 生成（`core/crates/proxy/dart-codegen/src/lib.rs:576`）。
watch 方法经 bridge.watchStream 发起请求，并过滤掉 `Completed` 事件（`core/crates/proxy/dart-codegen/src/lib.rs:609`）。
- 完整流用 `CoreLinkStreamEventValueDecoder` 解码；增量列表 watch 用 `CoreLinkListEventDecoder`；其余 watch 用 `CoreLinkEventValueDecoder`（`core/crates/proxy/dart-codegen/src/lib.rs:602`）
- `dart_type` 把 `Vec<u8>`、`CoreBuffer` 与 `operit_link::CoreBuffer` 映射为 `Uint8List`（`core/crates/proxy/dart-codegen/src/lib.rs:1513`）
- `dart_type` 把 Option<T> 映射为 T?（`core/crates/proxy/dart-codegen/src/lib.rs:1516`）
- `dart_type` 把 `Vec` 与 `HashSet` 映射为 `List`，把 `HashMap` 与 `BTreeMap` 映射为 `Map`（`core/crates/proxy/dart-codegen/src/lib.rs:1530`）。
- `dart_type` 把 `()` 映射为 `void`、`bool` 映射为 `bool`、Rust 整数映射为 `int`、`f32`/`f64` 映射为 `double`（`core/crates/proxy/dart-codegen/src/lib.rs:1546`）
- 把 `String` 与 `&str` 映射为 `String`，`serde_json::Value` 映射为 `Object?`（`core/crates/proxy/dart-codegen/src/lib.rs:1552`）
- 把未知类型映射为 `Object?`（`core/crates/proxy/dart-codegen/src/lib.rs:1577`）
- 内嵌 Core 流在编码端只读，编码时抛 `UnsupportedError`（`core/crates/proxy/dart-codegen/src/lib.rs:1740`）。

### 本地代理运行时：分发调用与管理流

- `LocalCoreProxy` 以 `Mutex<OperitApplication>` 持有应用，并以 `Arc<OperitApplication>` 保留 `applicationServices` 共享实时服务（`core/crates/proxy/local/src/lib.rs:36`）
- 代理持有 `coreStreamPool`，用于收养与打开流（`core/crates/proxy/local/src/lib.rs:49`）。
- `new` 接收 `OperitApplication`，用 `chatRuntimeHolder` 创建 `spaceRuntime`（`core/crates/proxy/local/src/lib.rs:131`）。
- `toolPkgShutdown` 取自包管理器的 `executionEngineShutdown`，用于释放容器拥有的执行引擎 worker（`core/crates/proxy/local/src/lib.rs:138`）
- `new` 新建一个 `CoreStreamPool` 作为代理自有的流池（`core/crates/proxy/local/src/lib.rs:152`）。
- `installCoreCommandExecutor` 只在非 wasm32 目标上编译，wasm32 目标不安装 core 命令执行器（`core/crates/proxy/local/src/lib.rs:163`）
- 在非 wasm32 目标上，`installCoreCommandExecutor` 安装 core 命令执行器；`hostManager.coreCommandExecutor` 已设置时返回 `None`，不重复安装（`core/crates/proxy/local/src/lib.rs:167`）。
- core 命令执行器以任务名 `core-tool-command` 调度 `operit_command_core::run_core_command`（`core/crates/proxy/local/src/lib.rs:192`）。
- 未预设执行器时安装闭包；实际执行 Core 命令时要求 Host 调度器，缺少任务调度宿主时报错 `Core command execution requires a task scheduler host`（`core/crates/proxy/local/src/lib.rs:185`）。安装时在同文件 :170 创建闭包，调度器检查在闭包内 :180–187；安装本身 :213–215 只写执行器并返回运行时，不检查调度器。
- `generatedTargetForSchema` 把 schema 键映射为稳定的目标字符串，`generatedTargetForType` 把具体运行时类型名映射为生成的本地对象 ID（`core/crates/proxy/local/src/lib.rs:76`）
- `bindCoreNodeToolRuntime` 经 `toolRuntimeSupport` 安装服务端 CoreNode 工具能力，不占用应用分发锁（`core/crates/proxy/local/src/lib.rs:87`）
- `bindCoreRouteChangeHandler` 安装 AI 回合完成后使用的路由变更控制器（`core/crates/proxy/local/src/lib.rs:98`）
- `bindDeviceToolRuntime` 把设备工具运行时绑定委托给 `toolRuntimeSupport`（`core/crates/proxy/local/src/lib.rs:67`）
- `localApplicationSharedClient` 为 `core/application` 缓存共享客户端，存活时直接复用（`core/crates/proxy/local/src/lib.rs:248`）。
- `coreNodeLocalRuntime` 构建共享节点能力容器（`core/crates/proxy/local/src/lib.rs:256`）。
- 组装时用共享客户端、应用客户端、运行时存储宿主与 `generatedTargetForSchema` 组装 `CoreNodeLocalRuntime`（`core/crates/proxy/local/src/lib.rs:272`）。
- 组装时挂接 `peerServices`，并把绑定闭包与 `openPush` 闭包传入（`core/crates/proxy/local/src/lib.rs:278`）。
- `runtimeStorageHost` 在未设置 `RuntimeStorageHost` 时 panic（`core/crates/proxy/local/src/lib.rs:230`）
- 截至基线 364d1d594，fileSystemHost() 在未设置 `FileSystemHost` 时 panic（`core/crates/proxy/local/src/lib.rs:283`）；上游 053c6686 已改成 filesystem() -> Arc<VisualFileSystem>（同文件 :283），调用 hostManager.vfs().expect("LocalCoreProxy requires VFS")。
- CoreLinkSharedClient::call 经 `dispatchCall` 分发，成功返回 `CoreCallResponse::ok`，失败返回 `CoreCallResponse::err`（`core/crates/proxy/local/src/lib.rs:320`）
- `dispatchCall` 把请求交给生成的 `generated_dispatch_core_proxy_call`，在 `isolation::future` 中执行，并把捕获的流附件收养进流池（`core/crates/proxy/local/src/lib.rs:429`）
- 异步 watch 快照在 `withCoreStreamCapture` 与 `isolation::future` 中调用生成的 `generated_dispatch_core_proxy_watch_snapshot_async`，错误消息后追加请求上下文（`core/crates/proxy/local/src/lib.rs:336`）。
- `watch` 目标为 `CORE_STREAM_TARGET` 时从流池打开匿名流源，否则走生成的 watch 分发（`core/crates/proxy/local/src/lib.rs:350`）
- `dispatchWatchSnapshot` 是同步分发器，调用生成的 `generated_dispatch_core_proxy_watch_snapshot`（`core/crates/proxy/local/src/lib.rs:448`）
- `dispatchWatch` 是同步分发器，目标为 `CORE_STREAM_TARGET` 时从流池打开，否则调用生成的 `generated_dispatch_core_proxy_watch`（`core/crates/proxy/local/src/lib.rs:458`）
- `watchSnapshotSync` 对外暴露同步 watch 快照分发（`core/crates/proxy/local/src/lib.rs:437`）
- `watchSync` 对外暴露同步 watch 流分发（`core/crates/proxy/local/src/lib.rs:443`）
- `openPushLocal` 直接在本地 Core 代理上打开调用方拥有的输入流（`core/crates/proxy/local/src/lib.rs:107`）
- `isReverseStreamRequest` 判断一次 push 请求是否为生成的反向流方法（`core/crates/proxy/local/src/lib.rs:116`）
- `openReverseStream` 委托给生成的 `generated_open_reverse_stream`（`core/crates/proxy/local/src/lib.rs:121`）
- `adoptCoreStreamAttachments` 把序列化流源转交给代理自有的流池（`core/crates/proxy/local/src/lib.rs:467`）
- `openCoreStreamWatch` 从流池打开匿名流源（`core/crates/proxy/local/src/lib.rs:472`）
- `shutdownToolPkgExecutionEngines` 调用 `toolPkgShutdown` 释放容器拥有的执行引擎 worker，不占用异步应用锁（`core/crates/proxy/local/src/lib.rs:158`）

### 桥：应用自有请求的分发边界

- `LocalApplicationBridgeTarget` 分发应用自有的 Link 请求，不进入服务对象路由（`core/crates/proxy/bridge/src/lib.rs:12`）
- `LocalApplicationBridgeTarget` 包含 `callLocalApplication` 与 `watchLocalApplicationSnapshot` 两个方法（`core/crates/proxy/bridge/src/lib.rs:15`）
- 桥契约还包含 `watchLocalApplication` 与 `openLocalApplicationPush` 两个方法（`core/crates/proxy/bridge/src/lib.rs:27`）。
- `LocalApplicationSharedClient` 把一个 `LocalApplicationBridgeTarget` 适配为共享 Link 客户端，绑定到一个 `application_object_id`（`core/crates/proxy/bridge/src/lib.rs:36`）
- 目标不匹配时客户端返回 `LOCAL_APPLICATION_TARGET_REQUIRED` 错误（`core/crates/proxy/bridge/src/lib.rs:51`）。
- LocalApplicationSharedClient::call 先校验 target，不一致返回 `targetError`，否则委托给桥目标的 `callLocalApplication`（`core/crates/proxy/bridge/src/lib.rs:68`）
- `watchSnapshot` 先校验 target，不一致返回 `targetError`，否则委托给桥目标的 `watchLocalApplicationSnapshot`（`core/crates/proxy/bridge/src/lib.rs:77`）
- `watch` 先校验 target，不一致返回 `targetError`，否则委托给桥目标的 `watchLocalApplication`（`core/crates/proxy/bridge/src/lib.rs:85`）
- `openPush` 先校验 target，不一致返回 `targetError`，否则委托给桥目标的 `openLocalApplicationPush`（`core/crates/proxy/bridge/src/lib.rs:96`）
- `LocalCoreProxy` 的 `callLocalApplication` 经 `dispatchCall` 分发，不重新进入服务端服务对象路由（`core/crates/proxy/local/src/lib.rs:374`）
- `watchLocalApplicationSnapshot` 加锁后用生成的 `generated_dispatch_application_watch_snapshot` 读取快照，不经过代理分发器（`core/crates/proxy/local/src/lib.rs:390`）
- `watchLocalApplication` 加锁后用生成的 `generated_dispatch_application_watch` 打开 watch，并传入流附件收养器（`core/crates/proxy/local/src/lib.rs:408`）
- `openLocalApplicationPush` 经 `openPushLocal` 打开生成的应用输入流（`core/crates/proxy/local/src/lib.rs:416`）

## 关键符号

- `CoreProxyRegisteredRoots`：14 个源码根与 proxy manifest 目录的显式注册表（`core/crates/proxy/scan/src/lib.rs:22`）
- `CoreProxyScanConfig`：扫描配置，包装一个根注册表（`core/crates/proxy/scan/src/lib.rs:69`）
- `CoreProxyScanOutput`：一次扫描的产物（`core/crates/proxy/scan/src/lib.rs:88`）
- `scan_core_proxy`：扫描入口，从注册根生成代理 IR（`core/crates/proxy/scan/src/lib.rs:96`）
- `stable_target`：schema 键到 `core/{schema_key}` 的映射（`core/crates/proxy/scan/src/lib.rs:244`）
- `write_rust_proxy_artifacts`：写出 Rust 分发代码与 schema JSON（`core/crates/proxy/rust-codegen/src/lib.rs:16`）
- `write_dart_proxy_artifacts`：写出 Dart 模型与客户端（`core/crates/proxy/dart-codegen/src/lib.rs:44`）
- `LocalCoreProxy`：本地代理运行时（`core/crates/proxy/local/src/lib.rs:34`）
- `CoreStreamPool`：代理自有的流池（`core/crates/proxy/local/src/lib.rs:49`）
- `LocalApplicationBridgeTarget`：应用自有 Link 请求的桥契约（`core/crates/proxy/bridge/src/lib.rs:12`）
- `LocalApplicationSharedClient`：桥目标到共享 Link 客户端的适配器（`core/crates/proxy/bridge/src/lib.rs:36`）
- `GeneratedCoreProxyClients`：生成的 Dart 客户端容器（`core/crates/proxy/dart-codegen/src/lib.rs:202`）
- `CoreProxyErrorDetails`：生成的 Dart 错误详情模型（`core/crates/proxy/dart-codegen/src/lib.rs:126`）
- `dart_type`：Rust 类型到 Dart 类型的映射（`core/crates/proxy/dart-codegen/src/lib.rs:1512`）
- `control_call_registry`：必须走控制调用的登记表（`core/crates/proxy/dart-codegen/src/lib.rs:518`）
- `dispatchCall`：本地调用分发的统一入口（`core/crates/proxy/local/src/lib.rs:426`）
- `generatedTargetForSchema`：schema 键到稳定目标字符串的映射（`core/crates/proxy/local/src/lib.rs:76`）

## 调用链

1. `scan_core_proxy` 读取 `CoreProxyScanConfig` 中的根注册表（`core/crates/proxy/scan/src/lib.rs:96`）
2. 扫描对受限根调用 `enforce_host_platform_boundaries` 做宿主平台边界检查（`core/crates/proxy/scan/src/lib.rs:126`）。
3. 扫描收集可序列化类型定义（`core/crates/proxy/scan/src/lib.rs:149`）。
4. 扫描收集错误类型定义（`core/crates/proxy/scan/src/lib.rs:152`）。
5. 扫描收集类型注册表（`core/crates/proxy/scan/src/lib.rs:167`）。
6. `object_specs` 给出对象规约（`core/crates/proxy/scan/src/lib.rs:171`）。
7. `scan_object` 逐个扫描成代理对象（`core/crates/proxy/scan/src/lib.rs:184`）。
8. `discover_factory_object_specs` 发现工厂对象规约（`core/crates/proxy/scan/src/lib.rs:192`）
9. `mark_factory_methods` 标记工厂方法（`core/crates/proxy/scan/src/lib.rs:200`）
10. 对象按 `schema_key` 排序（`core/crates/proxy/scan/src/lib.rs:212`）。
11. `stable_target` 生成对象地址（`core/crates/proxy/scan/src/lib.rs:215`）。
12. `write_rust_proxy_artifacts` 写出生成的 Rust 代理分发与 schema 产物（`core/crates/proxy/rust-codegen/src/lib.rs:16`）。
13. `write_dart_proxy_artifacts` 写出生成的 Dart 产物（`core/crates/proxy/dart-codegen/src/lib.rs:44`）。
14. `new` 接收 `OperitApplication`，建成运行时（`core/crates/proxy/local/src/lib.rs:128`）。
15. Dart 客户端经 bridge.callBytes 发送 `CoreCallRequest`（`core/crates/proxy/dart-codegen/src/lib.rs:494`）
16. `dispatchCall` 把请求交给生成的 `generated_dispatch_core_proxy_call`（`core/crates/proxy/local/src/lib.rs:429`）。
17. watch 请求经生成的 watch 分发打开流，流附件由 `adoptCoreStreamAttachments` 收养进 `coreStreamPool`（`core/crates/proxy/local/src/lib.rs:467`）

## 来源

- `core/crates/proxy/README.md`
- `core/crates/proxy/scan/src/lib.rs`
- `core/crates/proxy/local/src/lib.rs`
- `core/crates/proxy/bridge/src/lib.rs`
- `core/crates/proxy/rust-codegen/src/lib.rs`
- `core/crates/proxy/dart-codegen/src/lib.rs`
