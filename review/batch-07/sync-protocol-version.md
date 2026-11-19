---
title: 协议版本与构建指纹
module: sync
platforms: [all]
sources: [3]
date: 2026-11-11
---

## 概述

- Core 与 Edge 共用一个整数协议版本。`docs/peer-protocol-versioning.md:3`
- 软件发布版本、厂商固件版本和协议版本各自独立。`docs/peer-protocol-versioning.md:4`
- 运行时只比较协议版本，相同则继续配对、重连、路由和同步，配对见 [[sync-discovery-join|局域网发现、配对与加入 Space]]。`docs/peer-protocol-versioning.md:4`
- 协议版本不同返回明确的协议不兼容错误。`docs/peer-protocol-versioning.md:4`
- 软件版本仍用于展示，不参与兼容判断。`docs/peer-protocol-versioning.md:4`
- `core/peer-protocol.json` 是协议版本及 SHA-256 指纹的唯一记录。`docs/peer-protocol-versioning.md:9`
- 构建只扫描带 `operit_core_route` 注解的方法签名与路由元数据。`docs/peer-protocol-versioning.md:10`
- 旧的 `sources` 全文扫描与 `schemaRoots` 泛类型扫描已经移除。`docs/peer-protocol-versioning.md:21`
- 最新协议版本为 `version` 25。`core/peer-protocol.json:100`
- 协议版本不匹配返回 `PEER_PROTOCOL_MISMATCH`。`docs/peer-protocol-versioning.md:86`
- 缺少协议声明返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`docs/peer-protocol-versioning.md:87`
- 同步总览见 [[sync-overview|同步总览：Space 持久化同步]]。`docs/peer-protocol-versioning.md:3`

## AI 速览

- `core/peer-protocol.json` — 协议版本及 SHA-256 指纹的唯一记录。`docs/peer-protocol-versioning.md:9`
- `operit_core_route` — 构建只提取带此注解的方法签名与路由元数据。`docs/peer-protocol-versioning.md:10`
- `revisions` — 版本与 hash 的历史记录，共 25 条。`core/peer-protocol.json:2`
- 最新记录为 `version` 25，hash 为 `f486dc9b423430fcc85db351d317e0373ea4a72557778f3a6b997fee7c9f251b`。`core/peer-protocol.json:101`
- `operit-peer-session-fragments-v1` — v24 纳入指纹的认证会话分块修订标识。`docs/peer-protocol-versioning.md:28`
- `maxMessageBytes` — 只限制一条物理 Link 报文，不再是认证后逻辑消息的大小上限。`docs/peer-protocol-versioning.md:40`
- `PEER_PROTOCOL_MISMATCH` — 协议版本不匹配时返回的错误。`docs/peer-protocol-versioning.md:86`
- `PEER_PROTOCOL_UPGRADE_REQUIRED` — 缺少协议声明时返回的错误。`docs/peer-protocol-versioning.md:87`
- `protocolVersion` — 设备资料中的协议版本字段。`docs/peer-protocol-versioning.md:85`
- `requireConsistencySupport` — 要求本地与远端时钟的 `consistencyVersion` 均为 8 的一致性门。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- `consistencyVersion` — 同步内容一致性校验的内部版本号，当前为 8。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- 主入口函数：`requireConsistencySupport`。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- 数据流向一句话：构建时扫描 `core/crates/runtime/application/src` 中带 `operit_core_route` 注解的方法，提取签名与路由元数据算 SHA-256 指纹。`docs/peer-protocol-versioning.md:10`
- 数据流向一句话：业务同步通过 `$node.sync` 的 `protocol` 方法读取最终目标的协议版本。`docs/peer-protocol-versioning.md:84`

## 核心机制

- 构建扫描 `core/crates/runtime/application/src`，仅提取带 `operit_core_route` 注解的方法。`docs/peer-protocol-versioning.md:10`
- 指纹提取方法签名：方法名、参数名与类型、返回类型和泛型等签名信息。`docs/peer-protocol-versioning.md:12`
- 指纹提取路由元数据：目标类型及路由地址、binding、call/watch/push 类型、生命周期、权限、创建规则和反向流元素类型。`docs/peer-protocol-versioning.md:13`
- 提取结果排序并按固定格式编码后计算指纹，生成的 Rust 分发代码本身不参与哈希。`docs/peer-protocol-versioning.md:16`
- 文件完整内容不参与指纹；函数体、普通注释、文档、格式、未注解的方法（包括 `sync*` 方法）、无关 DTO、类型别名及自定义编解码实现的改动均不触发协议版本更新。`docs/peer-protocol-versioning.md:18`
- 旧的 `sources` 全文扫描与 `schemaRoots` 泛类型扫描已经移除。`docs/peer-protocol-versioning.md:21`
- `v23` 是切换至路由签名规则的首次记录，v1–v22 的历史 hash 保持原样。`docs/peer-protocol-versioning.md:21`
- 后续只有路由契约变化才会触发自动版本检查。`docs/peer-protocol-versioning.md:22`
- 签名中引用类型的内部字段以及底层报文格式不自动展开扫描，破坏互通的修改需要开发者主动评估并调整协议契约和版本。`docs/peer-protocol-versioning.md:23`
- Hash 仅供构建和开发检查使用，不随握手、同步请求或设备资料发送，运行时也不比较。`docs/peer-protocol-versioning.md:26`
- v24 将认证会话分块格式的显式修订标识 `operit-peer-session-fragments-v1` 纳入指纹。`docs/peer-protocol-versioning.md:28`
- `v24` 端点要求对端同为 v24；原有身份和配对凭据保留。`docs/peer-protocol-versioning.md:30`
- `maxMessageBytes` 继续限制一条物理 Link 报文，不再作为认证后的逻辑消息大小上限。`docs/peer-protocol-versioning.md:40`
- hello 声明本端帧上限，认证 transcript 同时绑定双方帧上限，双向使用较小值。`docs/peer-protocol-versioning.md:41`
- 每块有效负载最多 64 KiB，适用于现有 TCP、HTTP、WebSocket、串口和蓝牙载体。`docs/peer-protocol-versioning.md:43`
- 每块仍通过同一个 `$peer.session/data` 认证信封发送，加密明文前 16 字节依次为大端 u64 的完整消息字节数与当前块偏移，头和内容一起接受 `AEAD` 认证，`nonce` 逐块递增。`docs/peer-protocol-versioning.md:45`
- 接收端检查长度、偏移、认证和顺序，只在收齐后向 Call、Watch、Push 分发完整的原始逻辑消息，上层接口不感知分块。`docs/peer-protocol-versioning.md:48`
- 部分接收状态跨 receive future 取消保留，断线或认证失败后释放，不交付半条消息。`docs/peer-protocol-versioning.md:51`
- 内存按已接收的数据增长，不按对端声明的总长度预分配；完整消息仍需能放入接收端内存。`docs/peer-protocol-versioning.md:52`
- 物理分块的认证接收及成功写入均计入通道活动，持续传输不会仅因尚未重组完成而触发心跳超时。`docs/peer-protocol-versioning.md:53`
- 本机制不建立额外连接，不自动重试或断点续传；网络中断仍向调用方报告失败。`docs/peer-protocol-versioning.md:54`
- 新 hash 填写构建实际给出的 64 位小写十六进制值。`docs/peer-protocol-versioning.md:63`
- 按文档规定，Cargo 构建检查路由契约指纹与当前记录一致；CI 将版本记录与 PR / push 的基线比较，拒绝覆盖历史 hash、回退版本或不递增版本的修改。`docs/peer-protocol-versioning.md:72`
- 文档给出的本地检查命令为 `python3 tools/check_peer_protocol.py --base HEAD`。`docs/peer-protocol-versioning.md:76`
- 文档给出的本地检查命令为 `cargo check --manifest-path core/Cargo.toml -p operit-node-runtime --no-default-features --features peer-runtime`。`docs/peer-protocol-versioning.md:77`
- 这是首次引入统一协议版本，此前未声明该版本的 Core 或 Edge 程序需要升级一次，已有设备身份和配对凭据保留。`docs/peer-protocol-versioning.md:90`
- 此后软件版本变化、协议版本不变时，不要求厂商同步升级。`docs/peer-protocol-versioning.md:91`
- 原有配对安全协议、投影分页协议和同步记录格式的内部版本继续保留，其修改也纳入总指纹。`docs/peer-protocol-versioning.md:92`
- 任一侧 `consistencyVersion` 不是 8 时，`requireConsistencySupport` 返回错误，消息为“{side} peer cannot verify synchronized contents; a compatible version is required”。`core/crates/node/runtime/src/SyncConsistency.rs:24`
- 测试确认 `consistencyVersion` 为 0 至 7、缺失或空对象时 `requireConsistencySupport` 均返回错误。`core/crates/node/runtime/src/SyncConsistency.rs:291`

## 关键符号

- `operit_core_route` — 构建只提取带此注解的方法签名与路由元数据。`docs/peer-protocol-versioning.md:10`
- `revisions` — 版本与 hash 的历史记录，共 25 条。`core/peer-protocol.json:2`
- `operit-peer-session-fragments-v1` — v24 纳入指纹的认证会话分块修订标识。`docs/peer-protocol-versioning.md:28`
- `maxMessageBytes` — 只限制一条物理 Link 报文。`docs/peer-protocol-versioning.md:40`
- `$peer.session/data` — 认证会话分块的发送信封。`docs/peer-protocol-versioning.md:45`
- `PEER_PROTOCOL_MISMATCH` — 协议版本不匹配时返回的错误。`docs/peer-protocol-versioning.md:86`
- `PEER_PROTOCOL_UPGRADE_REQUIRED` — 缺少协议声明时返回的错误。`docs/peer-protocol-versioning.md:87`
- `protocolVersion` — 设备资料中的协议版本字段，拓扑状态比较它。`docs/peer-protocol-versioning.md:85`
- `$node.sync` 的 `protocol` 方法 — 读取最终目标协议版本的方法，适用于中继路由。`docs/peer-protocol-versioning.md:84`
- `consistencyVersion` — 同步内容一致性校验的内部版本号，当前为 8。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- `requireConsistencySupport` — 要求本地与远端时钟的 `consistencyVersion` 均为 8。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- `consistencyReports` — 同时向远端发 `PeerSyncMethod::SyncConsistency` 并在本地调 `syncConsistency`。`core/crates/node/runtime/src/SyncConsistency.rs:37`
- `reportsAtExchange` — 要求本地与远端报告的 `boundary` 分别等于各自收据的 `digest`。`core/crates/node/runtime/src/SyncConsistency.rs:141`
- `verifyReports` — 校验两侧报告无错误，返回 `correctionPlans` 是否为空。`core/crates/node/runtime/src/SyncConsistency.rs:175`

## 调用链

1. 修改协议相关源码：按文档规定，修改协议相关源码后运行正常的 Cargo 构建或检查。`docs/peer-protocol-versioning.md:58`
2. 指纹变化：按文档规定，指纹变化时构建失败并打印新的 SHA-256。`docs/peer-protocol-versioning.md:59`
3. 追加记录：修改后在 `revisions` 末尾追加记录，将 `version` 递增并填写新 hash，历史记录保持原样。`docs/peer-protocol-versioning.md:60`
4. 回归验证：再次构建并执行 Core / Edge 互通回归；发布软件时无需再额外递增协议版本。`docs/peer-protocol-versioning.md:61`
5. 配对与重连：新配对与已有凭据重连都声明协议版本，版本纳入认证 transcript。`docs/peer-protocol-versioning.md:82`
6. 投影协商：空间投影协商声明同一协议版本，供 Core 与 Edge 准入及控制同步使用。`docs/peer-protocol-versioning.md:83`
7. 业务同步：业务同步通过 `$node.sync` 的 `protocol` 方法读取最终目标的协议版本，适用于中继路由。`docs/peer-protocol-versioning.md:84`
8. 拓扑比较：拓扑状态比较设备资料中的 `protocolVersion`，Edge 无需伪造 Core 软件版本。`docs/peer-protocol-versioning.md:85`
9. 版本不匹配：协议版本不匹配返回 `PEER_PROTOCOL_MISMATCH`。`docs/peer-protocol-versioning.md:86`
10. 缺少声明：缺少协议声明返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`docs/peer-protocol-versioning.md:87`
11. 旧资料兼容：旧资料仍能反序列化，未声明版本显示未知，不会根据软件版本推断协议版本。`docs/peer-protocol-versioning.md:87`
12. 一致性取数：`consistencyReports` 同时向远端发 `PeerSyncMethod::SyncConsistency` 并在本地调 `syncConsistency`。`core/crates/node/runtime/src/SyncConsistency.rs:37`
13. 边界校验：`reportsAtExchange` 要求本地与远端报告的 `boundary` 分别等于各自收据的 `digest`。`core/crates/node/runtime/src/SyncConsistency.rs:141`
14. 完成校验：`verifyReports` 在任一侧有 `errors` 时返回错误。`core/crates/node/runtime/src/SyncConsistency.rs:171`
15. 完成判定：有未决 `pendingOwners` 时 `verifyReports` 返回未完成。`core/crates/node/runtime/src/SyncConsistency.rs:254`

## 来源

- `docs/peer-protocol-versioning.md`
- `core/peer-protocol.json`
- `core/crates/node/runtime/src/SyncConsistency.rs`

构建与 CI 流程的描述引自 `docs/peer-protocol-versioning.md`；检查脚本 `tools/check_peer_protocol.py` 与构建支持文件 `core/crates/node/runtime/build_support/peer_protocol.rs` 不在本页 seed 范围内，未逐行核验。
