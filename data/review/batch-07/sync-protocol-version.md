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
- 协议版本不同返回明确的协议不兼容错误。`docs/peer-protocol-versioning.md:5`
- 软件版本仍用于展示，不参与兼容判断。`docs/peer-protocol-versioning.md:5`
- `core/peer-protocol.json` 是协议版本及 SHA-256 指纹的唯一记录。`docs/peer-protocol-versioning.md:9`
- 协议版本不匹配返回 `PEER_PROTOCOL_MISMATCH`。`docs/peer-protocol-versioning.md:53`
- 缺少协议声明返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`docs/peer-protocol-versioning.md:53`
- 同步总览见 [[sync-overview|同步总览：Space 持久化同步]]。`docs/peer-protocol-versioning.md:3`

## AI 速览

- `core/peer-protocol.json` — 协议版本及 SHA-256 指纹的唯一记录。`docs/peer-protocol-versioning.md:9`
- `sources` — 参与检查的源文件或目录清单，共 38 条。`core/peer-protocol.json:2`
- `revisions` — 版本与 hash 的历史记录，共 15 条。`core/peer-protocol.json:42`
- 最新记录为 `version` 15，hash 为 `6e1cd3450e8812471bfd25830cf769c1ce2e2181387b3b1a1357ea259952e80d`。`core/peer-protocol.json:101`
- `schemaRoots` — 可序列化 DTO 扫描根，共 7 条。`core/peer-protocol.json:104`
- `PEER_PROTOCOL_MISMATCH` — 协议版本不匹配时返回的错误。`docs/peer-protocol-versioning.md:53`
- `PEER_PROTOCOL_UPGRADE_REQUIRED` — 缺少协议声明时返回的错误。`docs/peer-protocol-versioning.md:53`
- `protocolVersion` — 设备资料中的协议版本字段。`docs/peer-protocol-versioning.md:52`
- `requireConsistencySupport` — 要求本地与远端时钟的 `consistencyVersion` 均为 7 的一致性门。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- `consistencyVersion` — 同步内容一致性校验的内部版本号，当前为 7。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- 主入口函数：`requireConsistencySupport`。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- 数据流向一句话：构建时按 `sources` 收集 Rust 文件算 SHA-256 指纹。`docs/peer-protocol-versioning.md:10`
- 数据流向一句话：业务同步通过 `$node.sync` 的 `protocol` 方法读取最终目标的协议版本。`docs/peer-protocol-versioning.md:51`

## 核心机制

- `sources` 列出参与检查的源文件或目录。`docs/peer-protocol-versioning.md:9`
- 按文档规定，构建递归收集 Rust 文件，按仓库相对路径排序，统一 CRLF/LF，并将路径、长度和内容纳入哈希。`docs/peer-protocol-versioning.md:10`
- 按文档规定，测试目录及独立测试文件不参与收集。`docs/peer-protocol-versioning.md:11`
- 按文档规定，选中文件中的注释与内联测试也会影响指纹。`docs/peer-protocol-versioning.md:12`
- 指纹覆盖 Link 编解码、配对与认证会话、空间准入和权限、同步记录及事务应用，事务模型见 [[sync-transaction-model|事务模型与同步契约]]。`docs/peer-protocol-versioning.md:14`
- 指纹覆盖 Core / Edge 路由和设备服务协议。`docs/peer-protocol-versioning.md:15`
- 指纹聚合从应用源码扫描出的完整路由目录（binding、路由种类、生命周期、权限、创建规则和反向流类型）与路由方法签名。`docs/peer-protocol-versioning.md:15`
- JSON 同步 RPC 收集完整方法实现，覆盖其动态字段和处理逻辑。`docs/peer-protocol-versioning.md:16`
- `schemaRoots` 扫描可序列化 DTO 的字段、serde 属性、类型别名及自定义编解码实现。`docs/peer-protocol-versioning.md:17`
- 方法签名不变但报文字段变化时，`schemaRoots` 扫描捕获该变化。`docs/peer-protocol-versioning.md:18`
- 普通方法体变化不影响结构指纹。`docs/peer-protocol-versioning.md:18`
- 新协议实现文件必须加入 `sources`，不能只维护 DTO 而漏掉路由或同步行为。`docs/peer-protocol-versioning.md:19`
- Hash 仅供构建和开发检查使用，不随握手、同步请求或设备资料发送，运行时也不比较。`docs/peer-protocol-versioning.md:21`
- 新 hash 填写构建实际给出的 64 位小写十六进制值。`docs/peer-protocol-versioning.md:30`
- 按文档规定，Cargo 构建检查源码指纹与当前记录一致；CI 将版本记录与 PR / push 的基线比较，拒绝覆盖历史 hash、回退版本或不递增版本的修改。`docs/peer-protocol-versioning.md:39`
- 文档给出的本地检查命令为 `python3 tools/check_peer_protocol.py --base HEAD`。`docs/peer-protocol-versioning.md:43`
- 文档给出的本地检查命令为 `cargo check --manifest-path core/Cargo.toml -p operit-node-runtime --no-default-features --features peer-runtime`。`docs/peer-protocol-versioning.md:44`
- 构建指纹的源文件清单包含 `core/crates/foundation/link/src` 与 `core/crates/node/peer-link/src`。`core/peer-protocol.json:3`
- 构建指纹的源文件清单包含 `core/crates/node/runtime/src/SyncConsistency.rs`。`core/peer-protocol.json:17`
- 构建指纹的源文件清单包含 `edge/sdk/contract/src`、`edge/sdk/node/src` 与 `edge/sdk/proxy/src`。`core/peer-protocol.json:28`
- `schemaRoots` 包含 `core/crates/foundation/model/src` 与 `core/crates/persistence/store/src`。`core/peer-protocol.json:108`
- 这是首次引入统一协议版本，此前未声明该版本的 Core 或 Edge 程序需要升级一次，已有设备身份和配对凭据保留。`docs/peer-protocol-versioning.md:57`
- 此后软件版本变化、协议版本不变时，不要求厂商同步升级。`docs/peer-protocol-versioning.md:58`
- 原有配对安全协议、投影分页协议和同步记录格式的内部版本继续保留，其修改也纳入总指纹。`docs/peer-protocol-versioning.md:59`
- 任一侧 `consistencyVersion` 不是 7 时，`requireConsistencySupport` 返回错误，消息为“{side} peer cannot verify synchronized contents; a compatible version is required”。`core/crates/node/runtime/src/SyncConsistency.rs:24`
- 测试确认 `consistencyVersion` 为 0 至 6、缺失或空对象时 `requireConsistencySupport` 均返回错误。`core/crates/node/runtime/src/SyncConsistency.rs:256`

## 关键符号

- `sources` — 参与检查的源文件或目录清单，共 38 条。`core/peer-protocol.json:2`
- `revisions` — 版本与 hash 的历史记录，共 15 条。`core/peer-protocol.json:42`
- `schemaRoots` — 可序列化 DTO 扫描根，共 7 条。`core/peer-protocol.json:104`
- `PEER_PROTOCOL_MISMATCH` — 协议版本不匹配时返回的错误。`docs/peer-protocol-versioning.md:53`
- `PEER_PROTOCOL_UPGRADE_REQUIRED` — 缺少协议声明时返回的错误。`docs/peer-protocol-versioning.md:53`
- `protocolVersion` — 设备资料中的协议版本字段，拓扑状态比较它。`docs/peer-protocol-versioning.md:52`
- `$node.sync` 的 `protocol` 方法 — 读取最终目标协议版本的方法，适用于中继路由。`docs/peer-protocol-versioning.md:51`
- `consistencyVersion` — 同步内容一致性校验的内部版本号，当前为 7。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- `requireConsistencySupport` — 要求本地与远端时钟的 `consistencyVersion` 均为 7。`core/crates/node/runtime/src/SyncConsistency.rs:22`
- `consistencyReports` — 同时向远端发 `PeerSyncMethod::SyncConsistency` 并在本地调 `syncConsistency`。`core/crates/node/runtime/src/SyncConsistency.rs:37`
- `reportsAtExchange` — 要求本地与远端报告的 `boundary` 分别等于各自收据的 `digest`。`core/crates/node/runtime/src/SyncConsistency.rs:121`
- `verifyReports` — 校验两侧报告无错误且无未决 `pendingOwners`。`core/crates/node/runtime/src/SyncConsistency.rs:149`

## 调用链

1. 修改协议相关源码：按文档规定，修改协议相关源码后运行正常的 Cargo 构建或检查。`docs/peer-protocol-versioning.md:25`
2. 指纹变化：按文档规定，指纹变化时构建失败并打印新的 SHA-256。`docs/peer-protocol-versioning.md:26`
3. 追加记录：修改后在 `revisions` 末尾追加记录，将 `version` 递增并填写新 hash，历史记录保持原样。`docs/peer-protocol-versioning.md:27`
4. 回归验证：再次构建并执行 Core / Edge 互通回归；发布软件时无需再额外递增协议版本。`docs/peer-protocol-versioning.md:28`
5. 配对与重连：新配对与已有凭据重连都声明协议版本，版本纳入认证 transcript。`docs/peer-protocol-versioning.md:49`
6. 投影协商：空间投影协商声明同一协议版本，供 Core 与 Edge 准入及控制同步使用。`docs/peer-protocol-versioning.md:50`
7. 业务同步：业务同步通过 `$node.sync` 的 `protocol` 方法读取最终目标的协议版本，适用于中继路由。`docs/peer-protocol-versioning.md:51`
8. 拓扑比较：拓扑状态比较设备资料中的 `protocolVersion`，Edge 无需伪造 Core 软件版本。`docs/peer-protocol-versioning.md:52`
9. 版本不匹配：协议版本不匹配返回 `PEER_PROTOCOL_MISMATCH`。`docs/peer-protocol-versioning.md:53`
10. 缺少声明：缺少协议声明返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`docs/peer-protocol-versioning.md:53`
11. 旧资料兼容：旧资料仍能反序列化，未声明版本显示未知，不会根据软件版本推断协议版本。`docs/peer-protocol-versioning.md:54`
12. 一致性取数：`consistencyReports` 同时向远端发 `PeerSyncMethod::SyncConsistency` 并在本地调 `syncConsistency`。`core/crates/node/runtime/src/SyncConsistency.rs:37`
13. 边界校验：`reportsAtExchange` 要求本地与远端报告的 `boundary` 分别等于各自收据的 `digest`。`core/crates/node/runtime/src/SyncConsistency.rs:121`
14. 完成校验：`verifyReports` 在任一侧有 `errors` 时返回错误。`core/crates/node/runtime/src/SyncConsistency.rs:149`
15. 完成校验：`verifyReports` 在任一侧有未决 `pendingOwners` 时返回错误。`core/crates/node/runtime/src/SyncConsistency.rs:152`

## 来源

- `docs/peer-protocol-versioning.md`
- `core/peer-protocol.json`
- `core/crates/node/runtime/src/SyncConsistency.rs`

构建与 CI 流程的描述引自 `docs/peer-protocol-versioning.md`；检查脚本 `tools/check_peer_protocol.py` 与构建支持文件 `core/crates/node/runtime/build_support/peer_protocol.rs` 不在本页 seed 范围内，未逐行核验。
