---
title: 协议版本检查脚本
module: tools
platforms: [all]
sources: 7
date: 2026-11-11
---

## 概述

`tools/check_peer_protocol.py` 是检查 `core/peer-protocol.json` 修订记录的 Python 脚本。`tools/check_peer_protocol.py:13`
它的职责是守住已发布协议版本不可变、变更必须递增版本这一条规则。`tools/check_peer_protocol.py:2`
该脚本只把版本记录与 PR 基线比较，不计算源码 SHA-256。`tools/check_peer_protocol.py:5`
真正的 SHA-256 指纹由 Cargo 的 node-runtime 构建算出并校验。`tools/check_peer_protocol.py:4`
在基线 364d1d594 下，构建指纹覆盖 `sources` 列出的 38 条协议源路径，完整覆盖范围见 [[sync-protocol-version|协议版本与构建指纹]]。`core/peer-protocol.json:2`
时效标注：本页事实以基线 364d1d594 为准；上游 main（fa999a948）已移除清单的 sources 与 schemaRoots，构建指纹改用路由契约，详见核心机制末尾。

## AI 速览

`check_revisions` — 校验 revision 清单的结构、递增性与历史不变性。`tools/check_peer_protocol.py:17`
`main` — 解析 `--base`，读当前清单，取基线旧清单，执行校验并打印结果。`tools/check_peer_protocol.py:40`
`MANIFEST` — 检查目标 `core/peer-protocol.json`。`tools/check_peer_protocol.py:13`
`peer_protocol::generate` — 构建时计算协议指纹并校验 revisions（基线 364d1d594；上游 main 改为传入路由契约字符串）。`core/crates/node/runtime/build.rs:23`
`validate_revisions` — 构建侧校验末条 `hash` 等于算出的指纹。`core/crates/node/runtime/build_support/peer_protocol.rs:28`
`PeerProtocol` — 运行时只比较 `version`。`core/crates/node/runtime/src/PeerProtocol.rs:8`
主入口：`python3 tools/check_peer_protocol.py --base <基线>`。`.github/workflows/peer-protocol.yml:24`
数据流向：当前清单 + 基线旧清单 → `check_revisions` 校验 → 通过打印最新 `version`，失败抛 `ValueError`。`tools/check_peer_protocol.py:22`

## 核心机制

`check_revisions` 要求每条 `revision` 的 `version` 为 int 类型、严格递增且不超过 `0xFFFFFFFF`。`tools/check_peer_protocol.py:22`
`check_revisions` 要求每条 `revision` 的 `hash` 长度为 64，且字符全部取自 `0123456789abcdef`。`tools/check_peer_protocol.py:22`
`check_revisions` 要求全部 `revision` 的 `hash` 互不重复。`tools/check_peer_protocol.py:17`
`revisions` 为空时 `check_revisions` 抛 `ValueError`。`tools/check_peer_protocol.py:22`
传入 `previous` 时，当前 `revisions` 的前 `len(old)` 项必须与旧 `revisions` 完全相等，否则抛 `ValueError`。`tools/check_peer_protocol.py:34`
基线 364d1d594 下，传入 `previous` 时，`sources` 或 `schemaRoots` 变化且未追加新 `revision` 时抛 `ValueError`。`tools/check_peer_protocol.py:36`
传 `--base` 时先用 `git rev-parse --verify` 校验基线为有效 commit，校验失败时调用直接抛错。`tools/check_peer_protocol.py:42` `tools/check_peer_protocol.py:48`
传 `--base` 时用 `git ls-tree` 检查基线是否含清单，再用 `git show` 读出旧版清单。`tools/check_peer_protocol.py:42` `tools/check_peer_protocol.py:50`
基线中缺失清单仅在首次引入清单时被允许。`tools/check_peer_protocol.py:47`
未传 `--base` 时 `previous` 保持 `None`，check_revisions 只校验当前清单。`tools/check_peer_protocol.py:45`
与构建校验的关系是分工关系：脚本不计算哈希，SHA-256 指纹由 node-runtime 构建算出。`tools/check_peer_protocol.py:5`
以下构建指纹细节均为基线 364d1d594 的历史机制，上游 main（fa999a948）已改用路由契约指纹，见本节末尾的时效标注。
构建收集 `sources` 下的 Rust 源文件，跳过测试目录与测试文件，只收 .rs 文件。`core/crates/node/runtime/build_support/peer_protocol.rs:83`
构建把每个源文件的仓库相对路径名与文件内容纳入 SHA-256 指纹。`core/crates/node/runtime/build_support/peer_protocol.rs:95`
`part` 在哈希中先写长度再写内容，路径名与内容各自带 8 字节大端长度前缀。`core/crates/node/runtime/build_support/peer_protocol.rs:22`
`schemaRoots` 下可序列化 DTO 的线稿形状以 `wire-schema:` 前缀纳入同一指纹。`core/crates/node/runtime/build_support/peer_protocol.rs:103`
生成的路由目录文本以 `generated-route-catalog` 为名纳入同一指纹。`core/crates/node/runtime/build_support/peer_protocol.rs:110`
构建侧 `validate_revisions` 要求 `revisions` 末条的 `hash` 等于构建算出的指纹，否则报错。`core/crates/node/runtime/build_support/peer_protocol.rs:28`
该报错要求追加 `version` 更高、`hash` 为新指纹的 `revision`，且不得替换已发布 `revision`。`core/crates/node/runtime/build_support/peer_protocol.rs:43`
校验通过后构建把 `version` 写进 `peer_protocol_identity.rs`，生成 `pub const VERSION: u32`。`core/crates/node/runtime/build_support/peer_protocol.rs:113`
运行时只比较协议 `version`，指纹只在编译期检查，从不嵌入协议消息。`core/crates/node/runtime/src/PeerProtocol.rs:18`
`version` 不一致时 `requireCompatible` 返回 `PEER_PROTOCOL_MISMATCH`。`core/crates/node/runtime/src/PeerProtocol.rs:20`
协议声明缺失时 `requireAdvertised` 返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`core/crates/node/runtime/src/PeerProtocol.rs:29`
替换旧哈希会改变 `revisions` 前缀，传 `--base` 的检查抛 `ValueError`。`tools/check_peer_protocol.py:37`
替换旧哈希也使末条 `hash` 与构建算出的指纹不一致，构建侧校验报错。`core/crates/node/runtime/build_support/peer_protocol.rs:42`
唯一合法的变更方式是在末尾追加更高 `version` 与新 `hash` 的 `revision`。`core/crates/node/runtime/build_support/peer_protocol.rs:43`
清单现状（基线 364d1d594）：`revisions` 共 15 条，从 `version` 1 开始。`core/peer-protocol.json:42`
清单现状（基线 364d1d594）：最新 revision 为 `version` 15，`hash` 为 `6e1cd3450e8812471bfd25830cf769c1ce2e2181387b3b1a1357ea259952e80d`。`core/peer-protocol.json:101`
清单现状（基线 364d1d594）：`sources` 共 38 条。`core/peer-protocol.json:2`
清单现状（基线 364d1d594）：`schemaRoots` 共 7 条。`core/peer-protocol.json:104`
时效标注（上游 main fa999a948，与基线 364d1d594 不同）：清单只保留 revisions 一个顶层键，不再有 sources 与 schemaRoots；最新 revision 已到 version 23。
时效标注（上游 main fa999a948）：构建时把排序后的路由声明与标注的方法签名编码为一个路由契约字符串，传给构建支持模块；路由实现体、注释与格式变化不再改变指纹。
时效标注（上游 main fa999a948）：指纹只对该路由契约字符串算 SHA-256，先写入域分隔常量 operit-peer-route-signatures-v1 与一个空字节，再写契约内容；源码文件内容与 DTO 线稿形状不再进入指纹。
时效标注（上游 main fa999a948）：检查脚本不再校验 sources 与 schemaRoots 的覆盖变化，模块说明改为构建校验标注的路由契约 SHA-256。

## 关键符号

`check_revisions(current, previous=None)` — 校验清单结构与历史不变性，失败抛 `ValueError`。`tools/check_peer_protocol.py:22`
`main()` — 解析 `--base`，读清单，取基线旧清单，执行校验并打印结果。`tools/check_peer_protocol.py:40`
`MANIFEST` — 检查目标 `core/peer-protocol.json`。`tools/check_peer_protocol.py:13`
`ROOT` — 脚本所在目录的上级目录，即仓库根目录。`tools/check_peer_protocol.py:14`
`peer_protocol::generate` — 构建时计算协议指纹并校验 revisions（基线 364d1d594；上游 main 改为传入路由契约字符串）。`core/crates/node/runtime/build.rs:23`
`validate_revisions` — 构建侧校验末条 `hash` 等于算出的指纹。`core/crates/node/runtime/build_support/peer_protocol.rs:28`
`part` — 把名字与内容按长度前缀方式写入 SHA-256（基线 364d1d594 的旧哈希算法；上游 main 已改用路由契约指纹）。`core/crates/node/runtime/build_support/peer_protocol.rs:21`
`collect` — 递归收集协议源下的 .rs 文件，跳过测试目录与测试文件（基线 364d1d594 的旧机制；上游 main 已移除该收集步骤）。`core/crates/node/runtime/build_support/peer_protocol.rs:5`
`PeerProtocol` — Core 与 Edge 配对、路由与同步共用的兼容性标识，只含 `version`。`core/crates/node/runtime/src/PeerProtocol.rs:8`
`requireCompatible` — 本地 `version` 与 `VERSION` 不一致时返回 `PEER_PROTOCOL_MISMATCH`。`core/crates/node/runtime/src/PeerProtocol.rs:19`
`requireAdvertised` — 协议声明缺失时返回 `PEER_PROTOCOL_UPGRADE_REQUIRED`。`core/crates/node/runtime/src/PeerProtocol.rs:28`
`VERSION` — 构建生成的协议版本号常量，写进 `peer_protocol_identity.rs`。`core/crates/node/runtime/build_support/peer_protocol.rs:114`
`revisions` — 清单中的版本记录数组，共 15 条。`core/peer-protocol.json:42`
`sources` — 清单中的协议源路径数组，共 38 条（基线 364d1d594 的清单结构；上游 main 已移除该键）。`core/peer-protocol.json:2`
`schemaRoots` — 清单中的线稿 schema 根路径数组，共 7 条（基线 364d1d594 的清单结构；上游 main 已移除该键）。`core/peer-protocol.json:104`

## 调用链

1. `Peer Protocol Compatibility` 工作流在 `pull_request` 与 `push` 到 `main` 或 `master` 时运行。`.github/workflows/peer-protocol.yml:4`
2. CI 用 PR 基线或 push 前提交作 `--base` 运行检查脚本，基线为空或全零时改用无参数运行。`.github/workflows/peer-protocol.yml:24`
3. `main` 读当前清单（`MANIFEST`）。`tools/check_peer_protocol.py:44`
4. `main` 用 git rev-parse 校验基线，再用 git ls-tree 与 git show 取旧清单。`tools/check_peer_protocol.py:40`
5. `check_revisions` 校验 `version` 严格递增、`hash` 为 64 位小写十六进制且唯一。`tools/check_peer_protocol.py:22`
6. `check_revisions` 校验 `revisions` 非空、已发布前缀不变、覆盖变更须追加版本。`tools/check_peer_protocol.py:17`
7. 校验通过打印 `Peer protocol revision ledger OK` 与最新 `version`。`tools/check_peer_protocol.py:54`
8. CI 随后运行 `tools/tests/test_peer_protocol.py` 的单元测试。`.github/workflows/peer-protocol.yml:29`
9. CI 最后用 `cargo check -p operit-node-runtime --features peer-runtime` 触发构建侧指纹校验。`.github/workflows/peer-protocol.yml:31`
10. 在基线 364d1d594 下，[[core-node-runtime|节点——节点运行时]] 的 `build.rs` 调用 `peer_protocol::generate`，传入路由目录与方法签名文本；上游 main 改为传入路由契约字符串。`core/crates/node/runtime/build.rs:23`
11. `generate` 计算指纹并调 `validate_revisions`，末条 `hash` 不符则构建 `panic`。`core/crates/node/runtime/build_support/peer_protocol.rs:112`
12. 通过后构建生成含 `VERSION` 的 `peer_protocol_identity.rs`。`core/crates/node/runtime/build_support/peer_protocol.rs:113`
13. `PeerProtocol` 通过 `include!` 引入构建生成的 `peer_protocol_identity.rs`。`core/crates/node/runtime/src/PeerProtocol.rs:5`

## 来源

`tools/check_peer_protocol.py`（58 行，全文已读）。`tools/check_peer_protocol.py:2`
`core/peer-protocol.json`（113 行，全文已读）。`core/peer-protocol.json:2`
`core/crates/node/runtime/build.rs`（全文已读，与构建时 SHA-256 校验直接相关）。`core/crates/node/runtime/build.rs:23`
`core/crates/node/runtime/build_support/peer_protocol.rs`（全文已读，与构建时 SHA-256 校验直接相关）。`core/crates/node/runtime/build_support/peer_protocol.rs:28`
`core/crates/node/runtime/src/PeerProtocol.rs`（全文已读，与运行时版本比较直接相关）。`core/crates/node/runtime/src/PeerProtocol.rs:5`
`.github/workflows/peer-protocol.yml`（全文已读，与脚本调用方式直接相关）。`.github/workflows/peer-protocol.yml:24`
`tools/tests/test_peer_protocol.py`（全文已读，与脚本行为断言直接相关）。`tools/tests/test_peer_protocol.py:16`
`docs/peer-protocol-versioning.md`（全文已读，仅作背景对照，正文事实以代码为准）。`docs/peer-protocol-versioning.md:43`
否定性结论核验方法：2026-11-12，对基线 AAswordman/Operit2 @ 364d1d594，用 `grep -n "hashlib\|sha256\|Sha256\|hash(" tools/check_peer_protocol.py` 在脚本全文 58 行内零命中，确认脚本本身不计算源码 SHA-256。`tools/check_peer_protocol.py:5`
时效：上游 main（fa999a948）已改变本页机制，见核心机制末尾的时效标注；本页事实仍以基线 364d1d594 为准。
