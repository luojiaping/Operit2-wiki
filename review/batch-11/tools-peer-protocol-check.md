---
title: 协议版本检查脚本
module: tools
platforms: [all]
sources: 7
date: 2026-11-11
---

## 概述

tools/check_peer_protocol.py 是检查 `core/peer-protocol.json` 修订记录的 Python 脚本。`tools/check_peer_protocol.py:13`
它的职责是守住已发布协议版本不可变、变更必须递增版本这一条规则。`tools/check_peer_protocol.py:2`
该脚本只把版本记录与 PR 基线比较，不计算源码 SHA-256。`tools/check_peer_protocol.py:5`
真正的 SHA-256 指纹由 Cargo 的 node-runtime 构建对标注路由契约算出并校验。`tools/check_peer_protocol.py:4`
构建指纹只对路由契约字符串算 SHA-256，源码文件内容不再进入指纹，完整覆盖范围见 [[sync-protocol-version|协议版本与构建指纹]]。`core/crates/node/runtime/build_support/peer_protocol.rs:38`
清单只保留 `revisions` 一个顶层键，不再有 sources 与 schemaRoots。`core/peer-protocol.json:2`

## AI 速览

`check_revisions` — 校验 revision 清单的结构、递增性与历史不变性。`tools/check_peer_protocol.py:17`
`main` — 解析 `--base`，读当前清单，取基线旧清单，执行校验并打印结果。`tools/check_peer_protocol.py:36`
`MANIFEST` — 检查目标 `core/peer-protocol.json`。`tools/check_peer_protocol.py:13`
`peer_protocol::generate` — 构建时对路由契约字符串算指纹并校验 revisions。`core/crates/node/runtime/build.rs:25`
`validate_revisions` — 构建侧校验末条 `hash` 等于算出的指纹。`core/crates/node/runtime/build_support/peer_protocol.rs:15`
`fingerprint` — 对路由契约字符串算 SHA-256，先写两个域分隔常量。`core/crates/node/runtime/build_support/peer_protocol.rs:6`
`PeerProtocol` — 运行时只比较 `version`。`core/crates/node/runtime/src/PeerProtocol.rs:8`
主入口：`python3 tools/check_peer_protocol.py --base <基线>`。`tools/check_peer_protocol.py:38`
数据流向：当前清单 + 基线旧清单 → `check_revisions` 校验 → 通过打印最新 `version`，失败抛 `ValueError`。`tools/check_peer_protocol.py:22`

## 核心机制

`check_revisions` 要求每条 `revision` 的 `version` 为 int 类型、严格递增且不超过 `0xFFFFFFFF`。`tools/check_peer_protocol.py:22`
`check_revisions` 要求每条 `revision` 的 `hash` 长度为 64，且字符全部取自 `0123456789abcdef`。`tools/check_peer_protocol.py:22`
`revisions` 为空时 `check_revisions` 抛 `ValueError`。`tools/check_peer_protocol.py:22`
传入 `previous` 时，当前 `revisions` 的前 `len(old)` 项必须与旧 `revisions` 完全相等，否则抛 `ValueError`。`tools/check_peer_protocol.py:32`
传入 `previous` 时，删除 sources 或 schemaRoots 等清单键不触发报错，修订记录本身仍须保持前缀不变。`tools/check_peer_protocol.py:32`
传 --base 时先用 git 的 `rev-parse` `--verify` 校验基线为有效 commit，校验失败时调用直接抛错。`tools/check_peer_protocol.py:45`
传 --base 时用 `ls-tree` 检查基线是否含清单，再用 `show` 读出旧版清单。`tools/check_peer_protocol.py:46`
基线中缺失清单仅在首次引入清单时被允许。`tools/check_peer_protocol.py:47`
未传 `--base` 时 `previous` 保持 `None`，check_revisions 只校验当前清单。`tools/check_peer_protocol.py:41`
与构建校验的关系是分工关系：脚本不计算哈希，SHA-256 指纹由 node-runtime 构建算出。`tools/check_peer_protocol.py:5`
构建扫描 core/crates/runtime/application/src，仅提取带 `operit_core_route` 注解的方法；方法体、注释与格式变化不改变指纹。`core/crates/node/runtime/build.rs:19` `core/crates/node/runtime/build.rs:183`
`fingerprint` 先写域分隔常量 `operit-peer-route-signatures-v1` 与 `operit-peer-session-fragments-v1`，各后跟一个空字节，再写路由契约内容算 SHA-256。`core/crates/node/runtime/build_support/peer_protocol.rs:8`
`route_contract` 把排序后的路由声明与方法签名编码为一个路由契约字符串，与生成的分发代码文本无关。`core/crates/node/runtime/build.rs:126`
构建侧 `validate_revisions` 要求 `revisions` 末条的 `hash` 等于构建算出的指纹，否则报错。`core/crates/node/runtime/build_support/peer_protocol.rs:15`
该报错要求追加 `version` 更高、`hash` 为新指纹的 `revision`，且不得替换已发布 `revision`。`core/crates/node/runtime/build_support/peer_protocol.rs:28`
校验通过后构建把 `version` 写进 `peer_protocol_identity.rs`，生成 `pub const VERSION: u32`。`core/crates/node/runtime/build_support/peer_protocol.rs:41`
运行时只比较协议 `version`，指纹只在编译期检查，从不嵌入协议消息。`core/crates/node/runtime/src/PeerProtocol.rs:18`
`version` 不一致时 `requireCompatible` 返回 `PEER_PROTOCOL_MISMATCH`。`core/crates/node/runtime/src/PeerProtocol.rs:20`
协议声明缺失时 `requireAdvertised` 返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`core/crates/node/runtime/src/PeerProtocol.rs:35`
替换旧哈希会改变 `revisions` 前缀，传 `--base` 的检查抛 `ValueError`。`tools/check_peer_protocol.py:33`
替换旧哈希也使末条 `hash` 与构建算出的指纹不一致，构建侧校验报错。`core/crates/node/runtime/build_support/peer_protocol.rs:27`
唯一合法的变更方式是在末尾追加更高 `version` 与新 `hash` 的 `revision`。`core/crates/node/runtime/build_support/peer_protocol.rs:28`
清单现状：`revisions` 共 32 条，从 `version` 1 开始。`core/peer-protocol.json:2`
清单现状：最新 revision 为 `version` 32，`hash` 为 `3228b217bf2f8f7a1bdfc821ddffe632e9bb3e822f6536ff46c475c0ea13bc66`。`core/peer-protocol.json:129`
`v23` 是切换至路由签名规则的首次记录，v1–v22 的历史 hash 保持原样。`docs/peer-protocol-versioning.md:21`
v24 把认证会话分块格式的显式修订标识 `operit-peer-session-fragments-v1` 纳入指纹；v24 端点要求对端同为 v24，原有身份和配对凭据保留。`docs/peer-protocol-versioning.md:34`

## 关键符号

`check_revisions(current, previous=None)` — 校验清单结构与历史不变性，失败抛 `ValueError`。`tools/check_peer_protocol.py:22`
`main()` — 解析 `--base`，读清单，取基线旧清单，执行校验并打印结果。`tools/check_peer_protocol.py:36`
`MANIFEST` — 检查目标 `core/peer-protocol.json`。`tools/check_peer_protocol.py:13`
`ROOT` — 脚本所在目录的上级目录，即仓库根目录。`tools/check_peer_protocol.py:14`
`peer_protocol::generate` — 构建时对路由契约字符串算指纹并校验 revisions。`core/crates/node/runtime/build.rs:25`
`validate_revisions` — 构建侧校验末条 `hash` 等于算出的指纹。`core/crates/node/runtime/build_support/peer_protocol.rs:15`
`fingerprint` — 对路由契约字符串算 SHA-256，先写两个域分隔常量。`core/crates/node/runtime/build_support/peer_protocol.rs:6`
`route_contract` — 把排序后的路由声明与方法签名编码为路由契约字符串。`core/crates/node/runtime/build.rs:126`
`PeerProtocol` — Core 与 Edge 配对、路由与同步共用的兼容性标识，只含 `version`。`core/crates/node/runtime/src/PeerProtocol.rs:8`
`requireCompatible` — 本地 `version` 与 `VERSION` 不一致时返回 `PEER_PROTOCOL_MISMATCH`。`core/crates/node/runtime/src/PeerProtocol.rs:20`
`requireAdvertised` — 协议声明缺失时返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`core/crates/node/runtime/src/PeerProtocol.rs:35`
`VERSION` — 构建生成的协议版本号常量，写进 `peer_protocol_identity.rs`。`core/crates/node/runtime/build_support/peer_protocol.rs:41`
`revisions` — 清单中的版本记录数组，共 32 条。`core/peer-protocol.json:2`

## 调用链

1. `main` 读当前清单（`MANIFEST`）。`tools/check_peer_protocol.py:40`
2. 用 `rev-parse` 校验基线，再用 `ls-tree` 与 `show` 取旧清单。`tools/check_peer_protocol.py:45`
3. `check_revisions` 校验 `version` 严格递增、`hash` 为 64 位小写十六进制。`tools/check_peer_protocol.py:22`
4. `check_revisions` 校验 `revisions` 非空与已发布前缀不变。`tools/check_peer_protocol.py:17`
5. 校验通过打印 `Peer protocol revision ledger OK` 与最新 `version`。`tools/check_peer_protocol.py:50`
6. [[core-node-runtime|节点——节点运行时]] 的 build.rs 调用 `peer_protocol::generate`，传入 `route_contract` 编码的路由契约字符串。`core/crates/node/runtime/build.rs:25` `core/crates/node/runtime/build.rs:126`
7. `generate` 计算指纹并调 `validate_revisions`，末条 `hash` 不符则构建 `panic`。`core/crates/node/runtime/build_support/peer_protocol.rs:34` `core/crates/node/runtime/build_support/peer_protocol.rs:40`
8. 通过后构建生成含 `VERSION` 的 `peer_protocol_identity.rs`。`core/crates/node/runtime/build_support/peer_protocol.rs:41`
9. `PeerProtocol` 通过 `include!` 引入构建生成的 `peer_protocol_identity.rs`。`core/crates/node/runtime/src/PeerProtocol.rs:5`

## 来源

`tools/check_peer_protocol.py`（54 行，全文已读）。`tools/check_peer_protocol.py:2`
`core/peer-protocol.json`（132 行，全文已读）。`core/peer-protocol.json:2`
`core/crates/node/runtime/build.rs`（全文已读，与构建时 SHA-256 校验直接相关）。`core/crates/node/runtime/build.rs:25`
`core/crates/node/runtime/build_support/peer_protocol.rs`（全文已读，与构建时 SHA-256 校验直接相关）。`core/crates/node/runtime/build_support/peer_protocol.rs:15`
`core/crates/node/runtime/src/PeerProtocol.rs`（全文已读，与运行时版本比较直接相关）。`core/crates/node/runtime/src/PeerProtocol.rs:5`
`tools/tests/test_peer_protocol.py`（全文已读，与脚本行为断言直接相关）。`tools/tests/test_peer_protocol.py:16`
`docs/peer-protocol-versioning.md`（全文已读，仅作背景对照，正文事实以代码为准）。`docs/peer-protocol-versioning.md:49`
否定性结论核验方法：2026-11-15，对基线 AAswordman/Operit2 @ ff5373fb6，用 `grep -n "hashlib\|sha256\|Sha256\|hash(" tools/check_peer_protocol.py` 在脚本全文 56 行内零命中，确认脚本本身不计算源码 SHA-256。`tools/check_peer_protocol.py:5`
时效：本页事实以基线 7a79245 为准。
