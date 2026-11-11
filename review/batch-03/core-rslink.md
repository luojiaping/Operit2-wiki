---
title: RsLink——Rust 间 Link 协议层
module: core
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

- `Rslink` 是 Operit2 Core 内可复用的 Rust-to-link-to-Rust 协议层（`core/crates/rslink/README.md:3`）。
- 它提供纯协议与共享类型转换基础，供 `proxy`、`route`、CLI local core 与 route-space 的 Rust 流程复用（`core/crates/rslink/README.md:5`）。
- 它解决的问题是：上述四类 Rust 流程都要在 Rust 值与 Link 值之间往返，`Rslink` 把值转换、调用构造、流桥接与路由守卫做成一份共享基础，而不是各写一份（`core/crates/rslink/README.md:5`）。
- 边界：`Rslink` 不是 core-app 代理运行时、节点路由或 Dart 输出，三者分别位于 `proxy`、`node` 与 proxy emitter crate（`core/crates/rslink/README.md:14`）。
- 两个子 crate 分工：`runtime` 提供把 Rust 值转为 Link 值再转回的运行时辅助（`core/crates/rslink/README.md:9`）。
- 两个子 crate 分工：`codegen` 提供代码生成器使用的共享 IR、类型解析、命名与 schema 基础（`core/crates/rslink/README.md:10`）。
- 本页是纯 Rust 协议层，平台维度为 all；后台任务经宿主提供的运行时任务调度器执行（`core/crates/rslink/runtime/src/lib.rs:579`）。

## AI 速览

- `CoreStreamPool` — 进程内流源注册表（`core/crates/rslink/runtime/src/lib.rs:27`）。
- `CoreReverseStreamSession` — 一次生成反向流调用的运行时端点（`core/crates/rslink/runtime/src/lib.rs:113`）。
- `CoreStreamAttachmentAdopter` — 流附件收养回调类型（`core/crates/rslink/runtime/src/lib.rs:24`）。
- `to_core_value` — Rust 值编码为 Link 值（`core/crates/rslink/runtime/src/lib.rs:224`）。
- `from_core_response_value` — Link 响应值解码为调用方返回类型（`core/crates/rslink/runtime/src/lib.rs:252`）。
- `core_route_call_request` — 构造内部 Link 调用请求（`core/crates/rslink/runtime/src/lib.rs:273`）。
- `core_route_watch_request` — 构造内部 Link watch 请求（`core/crates/rslink/runtime/src/lib.rs:283`）。
- `core_route_call_response` — 经路由运行时执行调用（`core/crates/rslink/runtime/src/lib.rs:319`）。
- `core_flow_event_stream` — Flow 转 Link 事件流（`core/crates/rslink/runtime/src/lib.rs:414`）。
- `core_state_flow_event_stream` — StateFlow 转 Link 事件流（`core/crates/rslink/runtime/src/lib.rs:445`）。
- `core_state_flow_from_stream` — 事件流重建本地 StateFlow（`core/crates/rslink/runtime/src/lib.rs:486`）。
- `core_route_proxy_watch` — 路由代理 watch（`core/crates/rslink/runtime/src/lib.rs:648`）。
- `TypeResolver` — codegen 的类型解析器（`core/crates/rslink/codegen/src/lib.rs:17`）。
- `collect_type_registry` — codegen 的类型注册表收集（`core/crates/rslink/codegen/src/lib.rs:17`）。
- 主入口：注解生成的路由调用经 `core_route_call_response` 进入已安装的 `CoreRouteRuntime`（`core/crates/rslink/runtime/src/lib.rs:319`）。
- 数据流向：Rust 值经 `to_core_value` 编码为 `CoreValue` 发出 Link 请求或事件（`core/crates/rslink/runtime/src/lib.rs:224`）。
- 数据流向：对端用 `from_core_response_value` 把 Link 响应值解码回 Rust 值（`core/crates/rslink/runtime/src/lib.rs:252`）。
- 数据流向：流以内嵌描述符往返，源由 `CoreStreamPool` 登记（`core/crates/rslink/runtime/src/lib.rs:27`）。

## 核心机制

### 值转换

- `to_core_value` 把可序列化运行时值转为原生 Link 值模型，失败返回内部错误（`core/crates/rslink/runtime/src/lib.rs:224`）。
- `to_core_arg_value` 把调用方参数转为 Link 请求值，失败返回 `INVALID_ARGS` 错误（`core/crates/rslink/runtime/src/lib.rs:229`）。
- `to_named_core_arg_value` 在转换失败的 `INVALID_ARGS` 错误中带上参数名（`core/crates/rslink/runtime/src/lib.rs:235`）。
- `core_arg_entry` 把命名调用方参数转为 `(String, CoreValue)` 的 map 条目（`core/crates/rslink/runtime/src/lib.rs:244`）。
- `decode_core_arg` 从参数 map 中取出并移除指定名参数，缺失时按 `CoreValue::Null` 解码（`core/crates/rslink/runtime/src/lib.rs:214`）。
- `object_args` 只接受 `CoreValue::Map` 与 `CoreValue::Null`，其余值返回 `INVALID_ARGS` 错误（`core/crates/rslink/runtime/src/lib.rs:202`）。
- `from_core_response_value` 把 Link 响应值解码为生成调用方的返回类型，失败返回 `INVALID_RESPONSE` 错误（`core/crates/rslink/runtime/src/lib.rs:252`）。
- `decode_core_call_response` 从 `CoreCallResponse` 的 result 解码调用方返回类型（`core/crates/rslink/runtime/src/lib.rs:342`）。
- `decode_core_call_unit_response` 把成功响应映射为 `()`，失败原样返回（`core/crates/rslink/runtime/src/lib.rs:361`）。
- `core_value_map` 从 `(String, CoreValue)` 字段集合构造 `CoreValue::Map`（`core/crates/rslink/runtime/src/lib.rs:263`）。
- `core_call_error` 以 `COMMAND_ERROR` 码与附带 details 构造命令错误（`core/crates/rslink/runtime/src/lib.rs:258`）。

### 路由调用构造

- `core_route_call_request` 以 `nextCoreRouteRequestId` 生成请求 id、以 `CORE_INTERNAL_TARGET` 为目标构造 `CoreCallRequest`（`core/crates/rslink/runtime/src/lib.rs:273`）。
- `core_route_watch_request` 以同样方式构造内部 Link watch 请求（`core/crates/rslink/runtime/src/lib.rs:283`）。
- `core_route_args` 复用 `core_value_map` 构造路由参数，传输优化由 Link 负责（`core/crates/rslink/runtime/src/lib.rs:268`）。
- `core_route_call_response` 用 `core_route_call_request` 构造请求，并记录 `wrapper.call` 追踪日志（`core/crates/rslink/runtime/src/lib.rs:319`）。
- `core_route_error_uses_local_source` 在错误码为 `CORE_NODE_UNREACHABLE`、`PEER_LINK_CLOSED`、`PEER_RESPONSE_CLOSED`、`PEER_SEND_FAILED`、`PEER_WATCH_SOURCE_CLOSED` 之一时返回 true（`core/crates/rslink/runtime/src/lib.rs:351`）。
- `generated_proxy_request_id` 用宿主时钟毫秒生成 `core-proxy-{millis}` 格式的代理请求 id（`core/crates/rslink/runtime/src/lib.rs:1378`）。

### 流与 watch

- `core_event_stream_channel` 创建一对无界 Core 事件流通道（发送端与接收端）（`core/crates/rslink/runtime/src/lib.rs:366`）。
- `core_flow_event_stream` 把 `Flow` 转为 Link Core 事件流（`core/crates/rslink/runtime/src/lib.rs:414`）。
- `Flow` 订阅以 `FlowCancellation` 与 `subscribeWithCancellation` 进行，取消时关闭事件流（`core/crates/rslink/runtime/src/lib.rs:429`）。
- `core_state_flow_event_stream` 把 `StateFlow` 转为 Link Core 事件流（`core/crates/rslink/runtime/src/lib.rs:445`）。
- `core_route_state_flow_event_stream` 把本地路由 `StateFlow` 转为事件流（`core/crates/rslink/runtime/src/lib.rs:480`）。
- `require_empty_core_stream_attachments` 返回一个断言附件为空的 adopter，路由值不得捕获匿名 Core 流（`core/crates/rslink/runtime/src/lib.rs:375`）。
- `send_core_watch_value_with_attachments` 在编码 watch 更新时用 `withCoreStreamCaptureSync` 捕获流附件（`core/crates/rslink/runtime/src/lib.rs:390`）。
- watch 值编码用 `CoreValue::incrementalEvent` 对照上一值生成事件（`core/crates/rslink/runtime/src/lib.rs:398`）。
- 测试验证 watch 首次发送快照、变化后发送增量，且增量可还原为新值（`core/crates/rslink/runtime/src/lib.rs:1403`）。

### StateFlow 重建

- `core_state_flow_from_stream` 从远程 Link Core 事件流重建本地 `StateFlow`（`core/crates/rslink/runtime/src/lib.rs:486`）。
- 从流重建 StateFlow 时，流提前结束返回 `WATCH_STREAM_EMPTY` 错误（`core/crates/rslink/runtime/src/lib.rs:509`）。
- 从流重建 StateFlow 时，首个事件已完成返回 `WATCH_STREAM_COMPLETED` 错误（`core/crates/rslink/runtime/src/lib.rs:549`）。
- 从流重建 StateFlow 时，首个事件为增量返回 `WATCH_STREAM_DELTA_FIRST` 错误（`core/crates/rslink/runtime/src/lib.rs:556`）。
- StateFlow 重建任务以 `core-rslinkrs-state-flow` 为名调度到宿主运行时任务调度器（`core/crates/rslink/runtime/src/lib.rs:579`）。

### 路由代理 watch

- `core_route_state_flow` 经 CoreRouteRuntime::watch 打开注解生成的 `StateFlow` watch（`core/crates/rslink/runtime/src/lib.rs:719`）。
- 路由代理 watch 要求上游首个事件为 `Snapshot`，否则返回 `WATCH_SNAPSHOT_REQUIRED` 错误（`core/crates/rslink/runtime/src/lib.rs:669`）。
- 路由代理 watch 在 `snapshot` 参数为 true 时只转发首个快照即返回（`core/crates/rslink/runtime/src/lib.rs:677`）。
- `adopt_routed_watch_value` 在编码路由 watch 值时捕获流附件并交给 adopter 注册（`core/crates/rslink/runtime/src/lib.rs:637`）。
- `core_route_state_flow_with_local_source` 接受本地 `StateFlow` 作为路由 watch 的本地源（`core/crates/rslink/runtime/src/lib.rs:778`）。
- 带本地源的路由 watch 经 `runtime.watchWithLocalSource` 打开（`core/crates/rslink/runtime/src/lib.rs:813`）。
- `core_route_state_flow_value_decoder` 为路由 StateFlow 值创建带流源注册表的解码器（`core/crates/rslink/runtime/src/lib.rs:818`）。
- `adopt_core_stream_attachments` 把捕获的流源按 streamId 登记进路由流源注册表（`core/crates/rslink/runtime/src/lib.rs:863`）。

### 反向流

- `core_route_reverse_stream` 接受 `CoreRouteRuntime`、方法名、参数与 `ReverseStream<T>` 输入，其中 `T` 须实现 `Serialize` 与 `Send`（`core/crates/rslink/runtime/src/lib.rs:296`）。
- 反向流路由以 `CorePushRequest` 经 `runtime.openPush` 建立 Push 会话，逐项发送输入值后关闭会话（`core/crates/rslink/runtime/src/lib.rs:305`）。
- `CoreReverseStreamSession` 持有 `Box<dyn CoreReverseStreamSender>` 与一个 oneshot 完成接收端（`core/crates/rslink/runtime/src/lib.rs:113`）。
- `CoreReverseStreamSender` trait 要求实现 `send` 与 `close`：`send` 解码并投递一个 Link 值，`close` 完成类型化流输入（`core/crates/rslink/runtime/src/lib.rs:122`）。
- `TypedCoreReverseStreamSender<T>` 用 `ReverseStreamSender<T>` 桥接类型化反向流生产者（`core/crates/rslink/runtime/src/lib.rs:129`）。
- 反向流条目解码失败时返回 `INVALID_REVERSE_STREAM_ITEM` 错误（`core/crates/rslink/runtime/src/lib.rs:141`）。
- `CoreReverseStreamSession` 的 `new` 以类型化反向流发送端与完成接收端创建会话（`core/crates/rslink/runtime/src/lib.rs:157`）。
- `pushItem` 把一个 Link 值按序投递进反向流（`core/crates/rslink/runtime/src/lib.rs:171`）。
- `close` 关闭发送端后等待运行时消费者的完成结果（`core/crates/rslink/runtime/src/lib.rs:176`）。
- 对已关闭的反向流会话再次调用 `close` 返回 `REVERSE_STREAM_CLOSED` 错误（`core/crates/rslink/runtime/src/lib.rs:181`）。
- `CoreReverseStreamSession` 的 `CoreLinkPushSession` 实现把 `send` 转给 `pushItem`、把 `close` 转给 `CoreReverseStreamSession::close`（`core/crates/rslink/runtime/src/lib.rs:192`）。
- `core_reverse_stream_channel` 创建一对类型化反向流通道（`core/crates/rslink/runtime/src/lib.rs:1373`）。

### 内嵌流

- `CoreStreamPool` 以 `StdMutex` 保护的 `HashMap` 按 streamId 登记 `Arc<CoreStreamSource>`（`core/crates/rslink/runtime/src/lib.rs:27`）。
- `CoreStreamPool` 的 `new` 创建一个空的本地流源池（`core/crates/rslink/runtime/src/lib.rs:33`）。
- `adoptAll` 逐个收养序列化 Core 值时捕获的全部流附件（`core/crates/rslink/runtime/src/lib.rs:40`）。
- `adopt` 在同一 `streamId` 已有不同源时只记 duplicate 日志，不替换已有源（`core/crates/rslink/runtime/src/lib.rs:95`）。
- `openCoreStreamWatch` 只接受 `propertyName` 为 `openCoreStream` 的 watch 请求（`core/crates/rslink/runtime/src/lib.rs:47`）。
- `openCoreStreamWatch` 在 `propertyName` 不是 `openCoreStream` 时返回 `CoreLinkError::watchNotFound`（`core/crates/rslink/runtime/src/lib.rs:51`）。
- `openCoreStreamWatch` 从请求参数中解出 `streamId` 字符串（`core/crates/rslink/runtime/src/lib.rs:51`）。
- 路由内嵌流描述符只解析 target 为 `CORE_STREAM_TARGET` 且 `propertyName` 为 `openCoreStream` 的描述符（`core/crates/rslink/runtime/src/lib.rs:906`）。
- `core_route_embedded_stream_source` 创建一个经路由 watch 打开内嵌流的本地 `CoreStreamSource`（`core/crates/rslink/runtime/src/lib.rs:951`）。
- 内嵌流打开参数写入源方法、源模式与源参数三项（`core/crates/rslink/runtime/src/lib.rs:1103`）。
- `core_route_embedded_stream_open_args` 在打开参数不是 map 时返回 `INVALID_ARGS` 错误（`core/crates/rslink/runtime/src/lib.rs:1091`）。
- `routed_state_flow_embedded_stream_opens_through_route_runtime` 测试验证路由流值在重序列化时保留内嵌流源（`core/crates/rslink/runtime/src/lib.rs:1639`）。
- `stream_pool_keeps_one_source_for_duplicate_logical_stream_id` 测试验证同一逻辑 `streamId` 的重复附件只保留第一个源（`core/crates/rslink/runtime/src/lib.rs:1686`）。

### 诊断与事件流

- `core_value_shape` 把 `CoreValue` 归纳为 null、bool、signed、unsigned、float、string、bytes、list、map 九种粗粒度形状（`core/crates/rslink/runtime/src/lib.rs:1114`）。
- `core_value_trace_field` 把单个 Core 值格式化为紧凑追踪字段字符串（`core/crates/rslink/runtime/src/lib.rs:1228`）。
- `core_stream_id_argument` 从 Link 参数 map 中读取 `streamId` 字符串（`core/crates/rslink/runtime/src/lib.rs:1243`）。
- `forward_core_event_stream` 经宿主运行时调度器把 Core 事件流转发到无界发送端（`core/crates/rslink/runtime/src/lib.rs:1254`）。
- 字符串流的每个值转为 `CoreEventKind::Changed` 事件（`core/crates/rslink/runtime/src/lib.rs:1296`）。
- 字符串事件流结束时发送 `CoreEventKind::Completed` 事件（`core/crates/rslink/runtime/src/lib.rs:1310`）。
- 事件流条目经 `to_core_value` 编码（`core/crates/rslink/runtime/src/lib.rs:1336`）。
- 编码后的条目以 `CoreEventKind::Changed` 发出（`core/crates/rslink/runtime/src/lib.rs:1348`）。
- 事件流结束时发送 `CoreEventKind::Completed` 事件（`core/crates/rslink/runtime/src/lib.rs:1360`）。
- 设置 `OPERIT_PROFILE_COMPOSE_STAGES` 环境变量时，每个事件写一条 stderr 性能行（`core/crates/rslink/runtime/src/lib.rs:1333`）。
- 文件顶行声明 `#![allow(non_snake_case)]`，本文件符号使用 camelCase 命名（`core/crates/rslink/runtime/src/lib.rs:1`）。
- 文件包含 `#[cfg(test)]` 测试模块（`core/crates/rslink/runtime/src/lib.rs:1384`）。

### codegen：IR 与类型解析为谁服务

- codegen 的共享 IR 与类型解析供代码生成器使用（`core/crates/rslink/README.md:10`）。
- 共享 IR 与类型解析的模块声明：`build_model`、`build_type_resolver`、`build_utils` 三个内部模块（`core/crates/rslink/codegen/src/lib.rs:11`）。
- 本文件以 `pub use build_model::*` 全量重导出 `build_model` 的公开符号（`core/crates/rslink/codegen/src/lib.rs:15`）。
- 从 `build_type_resolver` 重导出 `TypeResolver`、`collect_type_registry`、`collect_serializable_type_definitions` 与 `collect_error_type_definitions`（`core/crates/rslink/codegen/src/lib.rs:17`）。
- 从 `build_type_resolver` 重导出 `is_supported_arg_type`、`is_supported_return_type` 与 `normalize_type`（`core/crates/rslink/codegen/src/lib.rs:19`）。
- 从 `build_utils` 重导出 `dispatch_name_from_schema_key`、`full_type_for_source_with_crate`、`identifier_words`、`lower_first`、`module_path_for_source_with_crate` 与 `parent_module_path`（`core/crates/rslink/codegen/src/lib.rs:23`）。
- Dart 输出等生成器位于 proxy emitter crate，`Rslink` 自身不做 Dart 输出（`core/crates/rslink/README.md:14`）。
- 范围说明：本页 seed 只含 lib.rs 的模块声明与重导出，IR 结构与类型解析的实现在 `build_model`、`build_type_resolver`、`build_utils` 内，不在本页 seed 内，本页不展开其内部结构（`core/crates/rslink/codegen/src/lib.rs:11`）。

## 关键符号

- `CoreStreamPool` — 进程内流源注册表（`core/crates/rslink/runtime/src/lib.rs:27`）。
- `CoreStreamAttachmentAdopter` — 流附件收养回调类型（`core/crates/rslink/runtime/src/lib.rs:24`）。
- `CoreReverseStreamSession` — 一次生成反向流调用的运行时端点（`core/crates/rslink/runtime/src/lib.rs:113`）。
- `CoreReverseStreamSender` — 类型化反向流发送端 trait（`core/crates/rslink/runtime/src/lib.rs:120`）。
- `TypedCoreReverseStreamSender<T>` — 类型化反向流生产者桥接（`core/crates/rslink/runtime/src/lib.rs:129`）。
- `to_core_value` — Rust 值编码为 Link 值（`core/crates/rslink/runtime/src/lib.rs:224`）。
- `from_core_response_value` — Link 响应值解码为调用方返回类型（`core/crates/rslink/runtime/src/lib.rs:252`）。
- `decode_core_arg` — 从参数 map 取出并移除指定名参数（`core/crates/rslink/runtime/src/lib.rs:214`）。
- `object_args` — 从请求载荷提取字符串键参数 map（`core/crates/rslink/runtime/src/lib.rs:202`）。
- `core_route_call_request` — 构造内部 Link 调用请求（`core/crates/rslink/runtime/src/lib.rs:273`）。
- `core_route_watch_request` — 构造内部 Link watch 请求（`core/crates/rslink/runtime/src/lib.rs:283`）。
- `core_route_call_response` — 经路由运行时执行调用（`core/crates/rslink/runtime/src/lib.rs:319`）。
- `decode_core_call_response` — 解码路由调用返回（`core/crates/rslink/runtime/src/lib.rs:342`）。
- `core_route_error_uses_local_source` — 路由错误是否留本地源判定（`core/crates/rslink/runtime/src/lib.rs:349`）。
- `core_event_stream_channel` — 无界 Core 事件流通道对（`core/crates/rslink/runtime/src/lib.rs:366`）。
- `core_flow_event_stream` — Flow 转 Link 事件流（`core/crates/rslink/runtime/src/lib.rs:414`）。
- `core_state_flow_event_stream` — StateFlow 转 Link 事件流（`core/crates/rslink/runtime/src/lib.rs:445`）。
- `core_state_flow_from_stream` — 事件流重建本地 StateFlow（`core/crates/rslink/runtime/src/lib.rs:486`）。
- `core_route_proxy_watch` — 路由代理 watch（`core/crates/rslink/runtime/src/lib.rs:648`）。
- `core_route_state_flow` — 注解生成的 StateFlow watch（`core/crates/rslink/runtime/src/lib.rs:719`）。
- `core_route_state_flow_with_local_source` — 带本地源的 StateFlow watch（`core/crates/rslink/runtime/src/lib.rs:778`）。
- `core_route_reverse_stream` — 类型化反向流路由（`core/crates/rslink/runtime/src/lib.rs:293`）。
- `core_route_embedded_stream_source` — 经路由 watch 打开内嵌流的本地源（`core/crates/rslink/runtime/src/lib.rs:951`）。
- `core_route_embedded_stream_open_args` — 内嵌流打开参数补源头元数据（`core/crates/rslink/runtime/src/lib.rs:1086`）。
- `core_reverse_stream_channel` — 类型化反向流通道对（`core/crates/rslink/runtime/src/lib.rs:1373`）。
- `generated_proxy_request_id` — 代理请求 id 生成（`core/crates/rslink/runtime/src/lib.rs:1378`）。
- `TypeResolver` — codegen 的类型解析器（`core/crates/rslink/codegen/src/lib.rs:17`）。
- `collect_type_registry` — codegen 的类型注册表收集（`core/crates/rslink/codegen/src/lib.rs:17`）。
- `collect_serializable_type_definitions` — codegen 的可序列化类型定义收集（`core/crates/rslink/codegen/src/lib.rs:17`）。
- `collect_error_type_definitions` — codegen 的错误类型定义收集（`core/crates/rslink/codegen/src/lib.rs:17`）。

## 调用链

1. 注解生成的调用方用 `core_route_call_request` 构造指向 `CORE_INTERNAL_TARGET` 的调用请求（`core/crates/rslink/runtime/src/lib.rs:273`）。
2. `core_route_call_response` 把请求交给已安装的 `CoreRouteRuntime` 执行（`core/crates/rslink/runtime/src/lib.rs:319`）。
3. `decode_core_call_response` 从响应 result 解码调用方返回类型（`core/crates/rslink/runtime/src/lib.rs:342`）。
4. 注解生成的 watch 用 `core_route_watch_request` 构造 watch 请求（`core/crates/rslink/runtime/src/lib.rs:283`）。
5. `core_route_state_flow` 经 CoreRouteRuntime::watch 打开 watch（`core/crates/rslink/runtime/src/lib.rs:719`）。
6. `core_state_flow_from_stream` 等首个快照事件，重建本地 `StateFlow` 后续增量跟进（`core/crates/rslink/runtime/src/lib.rs:486`）。
7. 反向流：以 `CorePushRequest` 经 `runtime.openPush` 建 Push 会话，逐项发送后关闭（`core/crates/rslink/runtime/src/lib.rs:305`）。
8. 内嵌流：值序列化时捕获的流源由 `adoptAll` 收养（`core/crates/rslink/runtime/src/lib.rs:40`）。
9. 内嵌流：解码遇描述符时，`routed_core_stream_source_for_descriptor` 只解析 `CORE_STREAM_TARGET` 与 `openCoreStream` 的描述符（`core/crates/rslink/runtime/src/lib.rs:906`）。
10. 内嵌流：`core_route_embedded_stream_source` 创建本地源，经路由 watch 重开内嵌流（`core/crates/rslink/runtime/src/lib.rs:951`）。
11. 生成器侧：`TypeResolver` 与 `collect_type_registry` 等符号供代码生成器消费（`core/crates/rslink/codegen/src/lib.rs:17`）。
12. 生成器侧：注解生成的路由用运行时辅助发起调用（`core/crates/rslink/runtime/src/lib.rs:272`）。

相关条目：[[core-overview|Core 总览与 crate 边界]]、[[core-proxy|代理生成——扫描、发射器与本地代理运行时]]、[[core-node-runtime|节点——节点运行时]]。

## 来源

- `core/crates/rslink/README.md`
- `core/crates/rslink/runtime/src/lib.rs`
- `core/crates/rslink/codegen/src/lib.rs`
