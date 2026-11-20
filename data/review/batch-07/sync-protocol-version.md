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
- 最新协议版本为 `version` 26。`core/peer-protocol.json:104`
- 协议版本不匹配返回 `PEER_PROTOCOL_MISMATCH`。`docs/peer-protocol-versioning.md:91`
- 缺少协议声明返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`docs/peer-protocol-versioning.md:92`
- 同步总览见 [[sync-overview|同步总览：Space 持久化同步]]。`docs/peer-protocol-versioning.md:3`

## AI 速览

- `core/peer-protocol.json` — 协议版本及 SHA-256 指纹的唯一记录。`docs/peer-protocol-versioning.md:9`
- `operit_core_route` — 构建只提取带此注解的方法签名与路由元数据。`docs/peer-protocol-versioning.md:10`
- `revisions` — 版本与 hash 的历史记录，共 26 条。`core/peer-protocol.json:2`
- 最新记录为 `version` 26，hash 为 `bb3372520ca577f16c2ba1b2ff265d777eac047fa50f844a1baf928481cd0cf9`。`core/peer-protocol.json:104`
- `operit-peer-session-fragments-v1` — v24 纳入指纹的认证会话分块修订标识。`docs/peer-protocol-versioning.md:30`
- `maxMessageBytes` — 只限制一条物理 Link 报文，不再是认证后逻辑消息的大小上限。`docs/peer-protocol-versioning.md:42`
- `PEER_PROTOCOL_MISMATCH` — 协议版本不匹配时返回的错误。`docs/peer-protocol-versioning.md:91`
- `PEER_PROTOCOL_UPGRADE_REQUIRED` — 缺少协议声明时返回的错误。`docs/peer-protocol-versioning.md:92`
- `protocolVersion` — 设备资料中的协议版本字段。`docs/peer-protocol-versioning.md:89`
- `PeerProtocol::VERSION` — 连接与业务同步统一使用它判断兼容性；同步收据没有独立版本。`docs/peer-protocol-versioning.md:36`
- 主入口函数：`synchronizeConsistency`。`core/crates/node/runtime/src/SyncConsistency.rs:35`
- 数据流向一句话：构建时扫描 `core/crates/runtime/application/src` 中带 `operit_core_route` 注解的方法，提取签名与路由元数据算 SHA-256 指纹。`docs/peer-protocol-versioning.md:10`
- 数据流向一句话：业务同步通过 `$node.sync` 的 `protocol` 方法读取最终目标的协议版本。`docs/peer-protocol-versioning.md:87`

## 核心机制

- 构建扫描 `core/crates/runtime/application/src`，仅提取带 `operit_core_route` 注解的方法。`docs/peer-protocol-versioning.md:10`
- 指纹提取方法签名：方法名、参数名与类型、返回类型和泛型等签名信息。`docs/peer-protocol-versioning.md:12`
- 指纹提取路由元数据：目标类型及路由地址、binding、call/watch/push 类型、生命周期、权限、创建规则和反向流元素类型。`docs/peer-protocol-versioning.md:13`
- 提取结果排序并按固定格式编码后计算指纹，生成的 Rust 分发代码本身不参与哈希。`docs/peer-protocol-versioning.md:16`
- 文件完整内容不参与指纹；函数体、普通注释、文档、格式、未注解的方法（包括 `sync*` 方法）、无关 DTO、类型别名及自定义编解码实现的改动均不触发协议版本更新。`docs/peer-protocol-versioning.md:18`
- 旧的 `sources` 全文扫描与 `schemaRoots` 泛类型扫描已经移除。`docs/peer-protocol-versioning.md:21`
- `v23` 是切换至路由签名规则的首次记录，v1–v22 的历史 hash 保持原样。`docs/peer-protocol-versioning.md:21`
- 后续只有路由契约变化才会触发自动版本检查。`docs/peer-protocol-versioning.md:22`
- 签名中引用类型的内部字段以及底层报文格式不自动展开扫描，这类修改若破坏互通，需要开发者在同一份 `revisions` 记录中主动追加协议版本。`docs/peer-protocol-versioning.md:24`
- Hash 仅供构建和开发检查使用，不随握手、同步请求或设备资料发送，运行时也不比较。`docs/peer-protocol-versioning.md:28`
- v24 将认证会话分块格式的显式修订标识 `operit-peer-session-fragments-v1` 纳入指纹。`docs/peer-protocol-versioning.md:30`
- 连接始终要求双方使用同一个当前协议版本；原有身份和配对凭据保留。`docs/peer-protocol-versioning.md:32`
- `maxMessageBytes` 继续限制一条物理 Link 报文，不再作为认证后的逻辑消息大小上限。`docs/peer-protocol-versioning.md:42`
- hello 声明本端帧上限，认证 transcript 同时绑定双方帧上限，双向使用较小值。`docs/peer-protocol-versioning.md:43`
- 每块有效负载最多 64 KiB，适用于现有 TCP、HTTP、WebSocket、串口和蓝牙载体。`docs/peer-protocol-versioning.md:45`
- 每块仍通过同一个 `$peer.session/data` 认证信封发送，加密明文前 16 字节依次为大端 u64 的完整消息字节数与当前块偏移，头和内容一起接受 `AEAD` 认证，`nonce` 逐块递增。`docs/peer-protocol-versioning.md:47`
- 接收端检查长度、偏移、认证和顺序，只在收齐后向 Call、Watch、Push 分发完整的原始逻辑消息，上层接口不感知分块。`docs/peer-protocol-versioning.md:50`
- 部分接收状态跨 receive future 取消保留，断线或认证失败后释放，不交付半条消息。`docs/peer-protocol-versioning.md:53`
- 内存按已接收的数据增长，不按对端声明的总长度预分配；完整消息仍需能放入接收端内存。`docs/peer-protocol-versioning.md:54`
- 物理分块的认证接收及成功写入均计入通道活动，持续传输不会仅因尚未重组完成而触发心跳超时。`docs/peer-protocol-versioning.md:55`
- 本机制不建立额外连接，不自动重试或断点续传；网络中断仍向调用方报告失败。`docs/peer-protocol-versioning.md:56`
- 新 hash 填写构建实际给出的 64 位小写十六进制值。`docs/peer-protocol-versioning.md:66`
- 按文档规定，Cargo 构建检查路由契约指纹与当前记录一致；CI 将版本记录与 PR / push 的基线比较，拒绝覆盖历史 hash、回退版本或不递增版本的修改。`docs/peer-protocol-versioning.md:75`
- 文档给出的本地检查命令为 `python3 tools/check_peer_protocol.py --base HEAD`。`docs/peer-protocol-versioning.md:79`
- 文档给出的本地检查命令为 `cargo check --manifest-path core/Cargo.toml -p operit-node-runtime --no-default-features --features peer-runtime`。`docs/peer-protocol-versioning.md:80`
- 此前未声明统一协议版本的 Core 或 Edge 程序需要升级一次；已有设备身份和配对凭据保留。`docs/peer-protocol-versioning.md:102`
- 此后软件版本变化、协议版本不变时，不要求厂商同步升级。`docs/peer-protocol-versioning.md:103`
- 配对安全报文、投影分页及持久化记录的内部格式不构成另一套设备兼容性协商；破坏互通的修改统一追加 `core/peer-protocol.json` 中的协议版本。`docs/peer-protocol-versioning.md:104`
- v26 统一连接、路由和业务同步的兼容性判断；同步收据和时钟摘要只传递业务数据，不再声明或检查独立的格式版本、一致性版本。`docs/peer-protocol-versioning.md:34`
- 仅语义变化也必须递增同一个版本，此时 hash 可以不变；路由指纹没有变化时，新修订可以沿用当前 hash。`docs/peer-protocol-versioning.md:25`

## 关键符号

- `operit_core_route` — 构建只提取带此注解的方法签名与路由元数据。`docs/peer-protocol-versioning.md:10`
- `revisions` — 版本与 hash 的历史记录，共 26 条。`core/peer-protocol.json:2`
- `operit-peer-session-fragments-v1` — v24 纳入指纹的认证会话分块修订标识。`docs/peer-protocol-versioning.md:30`
- `maxMessageBytes` — 只限制一条物理 Link 报文。`docs/peer-protocol-versioning.md:42`
- `$peer.session/data` — 认证会话分块的发送信封。`docs/peer-protocol-versioning.md:47`
- `PEER_PROTOCOL_MISMATCH` — 协议版本不匹配时返回的错误。`docs/peer-protocol-versioning.md:91`
- `PEER_PROTOCOL_UPGRADE_REQUIRED` — 缺少协议声明时返回的错误。`docs/peer-protocol-versioning.md:92`
- `protocolVersion` — 设备资料中的协议版本字段，拓扑状态比较它。`docs/peer-protocol-versioning.md:89`
- `$node.sync` 的 `protocol` 方法 — 读取最终目标协议版本的方法，适用于中继路由。`docs/peer-protocol-versioning.md:87`
- `PeerProtocol::VERSION` — 连接与业务同步统一使用它判断兼容性；同步收据没有独立版本。`docs/peer-protocol-versioning.md:36`
- `consistencyReports` — 同时向远端发 `PeerSyncMethod::SyncConsistency` 并在本地调 `syncConsistency`。`core/crates/node/runtime/src/SyncConsistency.rs:25`
- `reportsAtExchange` — 要求本地与远端报告的 `boundary` 分别等于各自收据的 `digest`。`core/crates/node/runtime/src/SyncConsistency.rs:129`
- `verifyReports` — 校验两侧报告无错误，返回 `correctionPlans` 是否为空。`core/crates/node/runtime/src/SyncConsistency.rs:163`

## 调用链

1. 修改协议相关源码：按文档规定，修改协议相关源码后运行正常的 Cargo 构建或检查。`docs/peer-protocol-versioning.md:60`
2. 指纹变化：按文档规定，指纹变化时构建失败并打印新的 SHA-256。`docs/peer-protocol-versioning.md:61`
3. 追加记录：修改后在 `revisions` 末尾追加记录，将 `version` 递增并填写当前 hash；仅语义变化也必须递增同一个版本，此时 hash 可以不变。历史记录保持原样。`docs/peer-protocol-versioning.md:62`
4. 回归验证：再次构建并执行 Core / Edge 互通回归；发布软件时无需再额外递增协议版本。`docs/peer-protocol-versioning.md:64`
5. 配对与重连：新配对与已有凭据重连都声明协议版本，版本纳入认证 transcript。`docs/peer-protocol-versioning.md:85`
6. 投影协商：空间投影协商声明同一协议版本，供 Core 与 Edge 准入及控制同步使用。`docs/peer-protocol-versioning.md:86`
7. 业务同步：业务同步通过 `$node.sync` 的 `protocol` 方法读取最终目标的协议版本，适用于中继路由。`docs/peer-protocol-versioning.md:87`
8. 拓扑比较：拓扑状态比较设备资料中的 `protocolVersion`，Edge 无需伪造 Core 软件版本。`docs/peer-protocol-versioning.md:89`
9. 版本不匹配：协议版本不匹配返回 `PEER_PROTOCOL_MISMATCH`。`docs/peer-protocol-versioning.md:91`
10. 缺少声明：缺少协议声明返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`docs/peer-protocol-versioning.md:92`
11. 旧资料兼容：旧资料仍能反序列化，未声明版本显示未知，不会根据软件版本推断协议版本。`docs/peer-protocol-versioning.md:92`
12. 一致性取数：`consistencyReports` 同时向远端发 `PeerSyncMethod::SyncConsistency` 并在本地调 `syncConsistency`。`core/crates/node/runtime/src/SyncConsistency.rs:25`
13. 边界校验：`reportsAtExchange` 要求本地与远端报告的 `boundary` 分别等于各自收据的 `digest`。`core/crates/node/runtime/src/SyncConsistency.rs:129`
14. 完成校验：`verifyReports` 在任一侧有 `errors` 时返回错误。`core/crates/node/runtime/src/SyncConsistency.rs:159`
15. 完成判定：有未决 `pendingOwners` 时 `verifyReports` 返回未完成。`core/crates/node/runtime/src/SyncConsistency.rs:242`

## 来源

- `docs/peer-protocol-versioning.md`
- `core/peer-protocol.json`
- `core/crates/node/runtime/src/SyncConsistency.rs`

构建与 CI 流程的描述引自 `docs/peer-protocol-versioning.md`；检查脚本 `tools/check_peer_protocol.py` 与构建支持文件 `core/crates/node/runtime/build_support/peer_protocol.rs` 不在本页 seed 范围内，未逐行核验。
