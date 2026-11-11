---
title: 第一次运行
module: intro
platforms: [windows, linux, macos, android, ios, ohos, web]
sources: [README.md, docs/device-space-lan-discovery.md, apps/flutter/app/web/README.md, apps/cli/src/cli/link.rs, apps/cli/src/cli/mod.rs, apps/cli/src/cli/transfer.rs, apps/cli/src/cli/web.rs, apps/cli/src/main.rs, apps/flutter/app/web_dev_config.yaml, core/crates/command/core/src/commands/storage.rs, core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs, core/crates/foundation/model/src/ModelConfigData.rs, core/crates/persistence/store/src/PreferencesDataStore.rs, core/crates/node/runtime/src/NodeSpaceService.rs, core/crates/node/runtime/src/peer/space_join.rs, apps/flutter/app/lib/ui/common/PeerQrCodeDialog.dart, apps/flutter/app/lib/ui/common/DeviceSpaceDiscoveryPanel.dart, apps/flutter/app/lib/ui/common/SpaceJoinWidgets.dart, apps/flutter/app/lib/l10n/generated/app_localizations_zh.dart]
date: 2026-11-11
---

# 第一次运行

## 概述

第一次运行指在本机装好环境、启动第一个 `CoreNode`、发现并配对另一台设备、加入 `Space`、再用浏览器打开 Web Access 的完整路径。Operit2 的定位见 [[intro-overview|Operit2 是什么]]。

Operit2 处于 Preview 阶段，底层结构、数据格式、插件契约与跨设备工作流仍会发生 breaking 变更（`README.md:14`）。

每个运行 `Core` 的实例称为 `CoreNode`，通过本地 `Host` 使用文件、终端、浏览器等能力；`Space` 组织节点间的协作与持久化同步，`Binding` 记录下一个由哪个节点继续任务（`README.md:18`）。`Space` 内节点地位平等，加入 `Space` 不会自动授予其他设备的系统权限（`README.md:20`）。

能力在各平台上并不相同：Rust CLI/TUI 的当前 CLI Host 主要覆盖 Windows、Linux 与 macOS（`README.md:97`）；Flutter App 的 Host 能力在 Android、Windows、Linux、macOS、iOS、OpenHarmony 与浏览器模式下各不相同（`README.md:96`）。本页只在部分平台成立的说法，都在句中注明平台。

## AI 速览

核心符号：

- `CoreNode` — 运行 Core 的实例（`README.md:18`）
- `Host` — 向 CoreNode 提供文件、终端、浏览器等本地能力的平台适配层（`README.md:18`）
- `Space` — 组织节点协作与持久化同步的范围（`README.md:18`）
- `Binding` — 记录下一个继续任务的节点（`README.md:18`）
- `PeerLink` — 承载 Space 请求与同步流量的传输层（`README.md:43`）
- `discoveryEnabled` — 发现广播的开关，关闭后设备不广播（`docs/device-space-lan-discovery.md:7`）
- `nodeId` — 发现广播与连接码中的节点标识（`docs/device-space-lan-discovery.md:9`）
- `ServiceDiscovery` — 记录发现接口、地址、守护进程错误与扫描总数的日志来源（`docs/device-space-lan-discovery.md:46`）
- `RuntimePeerService` — 记录广播总数与四类过滤总数的组件（`docs/device-space-lan-discovery.md:51`）
- `ProviderProfile` — 模型 Provider 配置，含 apiKey 与 apiKeyPool（`core/crates/foundation/model/src/ModelConfigData.rs:603`）
- `ModelConfigManager::preferenceStore` — 模型配置管理器入口，用 newWithStorage 打开偏好 store（`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:108`）
- `PreferencesDataStore::newWithStorage` — 创建 Space 偏好 store（`core/crates/persistence/store/src/PreferencesDataStore.rs:2924`）
- `SpaceJoinRequest` — 加入申请记录，状态字段是 SpaceJoinStatus（`core/crates/node/runtime/src/NodeSpaceService.rs:313`）
- `SpaceJoinStatus` — Pending、Approving、Approved、Rejected、Cancelled、Expired、Joined（`core/crates/node/runtime/src/NodeSpaceService.rs:307`）

主入口：

- `operit2`：无参数进入 TUI（`apps/cli/src/main.rs:57`）
- `operit2 cli link`：配对、发现与 Space 管理（`apps/cli/src/cli/link.rs:1299`）
- `operit2 cli web open`：打开 Web Access（`apps/cli/src/cli/web.rs:6`）
- `fvm flutter run`：启动 Flutter App（`README.md:191`）

数据流向：本节点启动监听器 → 对端通过发现或扫码拿到地址 → 配对握手验证节点与配对密钥 → 提交 Space 加入请求 → 同步记录到达目标节点后继续任务。

## 核心机制

### 环境与启动

开发入口要求 Rust stable 与 rustup、Flutter SDK 与 FVM、Node.js、Python 3（`README.md:156`）。

CLI 从仓库根目录运行：`cargo check --manifest-path apps/cli/Cargo.toml` 检查，`cargo run --manifest-path apps/cli/Cargo.toml --bin operit2 -- --help` 查看帮助（`README.md:169-170`）。

不带参数运行 `operit2` 默认进入 TUI（`README.md:175`）；`operit2 cli version` 显示 CLI、Core 与 Link 版本（`apps/cli/src/cli/mod.rs:129`）。

Flutter App 从 `apps/flutter/app` 目录运行：`fvm install --skip-pub-get`、`fvm dart pub get --enforce-lockfile`、`fvm flutter analyze`、`fvm flutter run -d windows`（`README.md:188-191`）。其中 `windows` 只是示例设备名，Android、Linux、macOS、iOS、OpenHarmony 与浏览器模式各需要自己的平台工具链（`README.md:191`）。

### CLI 入口（以 apps/cli 源码为准）

| 用途 | 命令 | 来源 |
| --- | --- | --- |
| 查看版本 | operit2 cli version | `apps/cli/src/cli/mod.rs:129` |
| 发现设备 | operit2 cli link discover [--timeout-ms \<ms\>] | `apps/cli/src/cli/link.rs:1304` |
| 生成连接码 | operit2 cli link qr [http\|ws\|tcp] [--bind \<host:port\>] [--no-discovery] | `apps/cli/src/cli/link.rs:1305` |
| 配对 | operit2 cli link pair [device-name\|connection-code] | `apps/cli/src/cli/link.rs:1303` |
| 启动监听器 | operit2 cli link listen \<http\|ws\|tcp\|serial\|bluetooth\> [--automatic-port\|--fixed-port] [--bind \<host:port\>] | `apps/cli/src/cli/link.rs:1309` |
| 交互式管理 | operit2 cli link session \<http\|ws\|tcp\> [--automatic-port\|--fixed-port] [--bind \<host:port\>] [--no-discovery] | `apps/cli/src/cli/link.rs:1313` |
| 查看 Space | operit2 cli link space show | `apps/cli/src/cli/link.rs:729` |
| 加入 Space | operit2 cli link space join [device-name\|number] | `apps/cli/src/cli/link.rs:1310` |
| 列出身份 | operit2 cli identity list | `apps/cli/src/cli/mod.rs:205` |
| 存储路径 | operit2 cli storage paths | `core/crates/command/core/src/commands/storage.rs:16` |
| 导出快照 | operit2 cli export snapshot \<path\> | `apps/cli/src/cli/transfer.rs:53` |
| 创建备份 | operit2 cli backup create \<path\> | `apps/cli/src/cli/transfer.rs:121` |
| 恢复备份 | operit2 cli backup restore \<path\> | `apps/cli/src/cli/transfer.rs:122` |
| 检查快照 | operit2 cli backup inspect \<snapshot-zip-path\> | `apps/cli/src/cli/transfer.rs:123` |
| 检查 Operit v1 快照 | operit2 cli backup inspect-operit1-snapshot \<path\> | `apps/cli/src/cli/transfer.rs:146` |
| 打开 Web Access | operit2 cli web open | `apps/cli/src/cli/web.rs:6` |

`link discover` 的默认超时是 2000 毫秒（`apps/cli/src/cli/link.rs:679`）。

README 的命令示例有两处与代码不符，以代码为准：

- README 写 `operit2 cli link serve --bind <address:port> --token <strong-token>`（`README.md:46`），但 run_link_command 的分发中没有 `serve` 子命令，`link` 的子命令清单是 discover、qr、pair、unpair、peers、prompts、listen、session、space、doctor、control、stream-probe、edge-call（`apps/cli/src/cli/link.rs:1299`）。启动监听器用 `operit2 cli link listen`（`apps/cli/src/cli/link.rs:1309`）。
- README 写 `operit2 cli link connect <url> --token <token> --save <session-name>`（`README.md:48`），run_link_command 的分发中没有 `connect` 子命令（`apps/cli/src/cli/link.rs:36`）。连接改走发现或扫码后的 `pair`。
- README 写 `operit2 cli link space join <session-name>`（`README.md:49`），代码里的 `space join` 接受设备名或编号作为选择器，不是会话名（`apps/cli/src/cli/link.rs:1310`）。

### 发现与配对

发现查询 `_operit-link._tcp.local.`，不枚举 IP 地址（`docs/device-space-lan-discovery.md:5`）。

设备仅在已配置的网络监听器运行且 `discoveryEnabled` 开启时才广播；默认监听器是 HTTP 与 WebSocket，OS 分配端口，绑定 `0.0.0.0`（`docs/device-space-lan-discovery.md:7`）。

TXT 元数据必须包含 `nodeId`、`displayName` 与 `transports`，不完整的广播会被拒绝并给出诊断（`docs/device-space-lan-discovery.md:9`）。

添加设备对话框执行 5 秒主动扫描；刷新重启共享查询并保留订阅句柄（`docs/device-space-lan-discovery.md:11`）。

本地设备与已配对设备有意从添加设备结果中排除，包括当前离线的已配对设备（`docs/device-space-lan-discovery.md:14`）。

离线的已配对网络设备按已发现地址排序重连，已保存地址作为后备；每个备选地址的连接与认证尝试有界（`docs/device-space-lan-discovery.md:19`）。

已发现的 `nodeId` 只是拨号提示；会话握手验证预期节点并证明持有现有配对密钥后，运行时把成功的地址与传输方式持久化到出站配对记录（`docs/device-space-lan-discovery.md:21`）。认证失败不改变已保存的端点，并发的解除配对或凭证替换不会被进行中的连接撤销（`docs/device-space-lan-discovery.md:25`）。

平台差异：Windows、Linux、Android 与 OHOS 使用共享原生 mDNS 提供方，守护进程与浏览器工作线程归 Host 所有（`docs/device-space-lan-discovery.md:32`）；iOS 与 macOS 使用系统 Bonjour DNS-SD 守护进程，不使用应用自有的 UDP 组播套接字；macOS CLI 安装同样的 Apple 发现 Host（`docs/device-space-lan-discovery.md:37`）。

两端都必须放行本地组播 DNS 流量（UDP 5353 到 224.0.0.251 / ff02::fb）与到已广播监听器端口的入站连接（`docs/device-space-lan-discovery.md:55`）。

扫码配对：v2 连接码携带节点 ID、显示名、实时网络地址与 5 分钟有效的随机邀请密钥（`docs/device-space-lan-discovery.md:108`）。
扫码确认通过已有的 `SPAKE2` 配对交换认证并提交 Space 加入请求，该路径不显示手动配对码对话框（`docs/device-space-lan-discovery.md:110`）。
相机扫码在 Android、iOS、macOS 与 web 上可用，其他 Host 导入图片或粘贴连接码（`docs/device-space-lan-discovery.md:103`）。

`operit2 cli link qr http --no-discovery` 在没有守护进程或 TUI 属主运行时启动 HTTP 监听器并保持到 Ctrl-C（`docs/device-space-lan-discovery.md:130`）。
`link qr` 的 `--json` 以无终端转义序列的形式输出连接信息（`docs/device-space-lan-discovery.md:135`）。
交互式 `link session` 中 `qr` 显示同一连接码，`pair <connection-code>` 完成 QR 配对，`space` 命令提交或检查加入请求（`docs/device-space-lan-discovery.md:138`）。
Flutter 扫码后点 `Confirm join` 直接连接并提交加入请求，无需输入配对码（`apps/flutter/app/lib/l10n/generated/app_localizations_zh.dart:4565`）。

### Web Access

打开页面不会自动让浏览器成为 `Space` 中的独立节点（`README.md:72`）。Web Access 不是自动加入 Space 的浏览器节点，也不是集中式 Agent Server（`README.md:99`）。

部署服务器必须为每个应用资产发送 Cross-Origin-Opener-Policy: same-origin、Cross-Origin-Embedder-Policy: require-corp、Cross-Origin-Resource-Policy: same-origin 三个响应头，线程化 Sherpa ONNX WebAssembly 才能运行本地 STT 与 TTS（`apps/flutter/app/web/README.md:9`）。

CLI 暴露的 Link Access 服务器不提供 Web 前端（`apps/flutter/app/web/README.md:14`）。

FVM 固定的 Flutter SDK 从 Flutter 应用根目录读取 `web_dev_config.yaml`，内置开发服务器位于 http://127.0.0.1:4835 并发送三个跨域隔离头，不需要单独的 Node 进程或代理端口（`apps/flutter/app/web/README.md:20`）。

Web 开发用 `fvm flutter run -d edge`，Chrome 用 `-d chrome`，手动打开浏览器用 `-d web-server` 并访问 http://127.0.0.1:4835（`apps/flutter/app/web/README.md:26`）。VS Code 选择 Operit2: Web (isolated) 后按 F5 启动 Edge，无需预启动代理任务（`apps/flutter/app/web/README.md:34`）。

跨域隔离头启用跨域隔离，不代表对远程 API 无限制的 CORS 访问，远程 API 服务器仍须通过自身 CORS 策略授权开发源（`apps/flutter/app/web/README.md:37`）。

runtime 布局：`runtime/src` 存放 TypeScript 源码，`runtime/generated` 存放生成的 JavaScript/WASM 产物与 v86 客户机运行时，`runtime/vendor` 存放 MessagePack 等第三方静态文件（`apps/flutter/app/web/README.md:47`）。

原生应用与 CLI 不打包也不提供 web 目录；设置入口与 `operit2 cli web open` 打开 https://web.operit.app/，不启动本地服务器，不把凭证放进 URL（`apps/flutter/app/web/README.md:52`）。连接另一台设备是独立的节点监听与配对操作，不是 Web Access 服务器生命周期（`apps/flutter/app/web/README.md:55`）。

两份文档在开发代理上说法不同：README 的 Web Access 双终端步骤引用 `node tools/dev_web_access_proxy.mjs`，代理监听 4836 端口（`README.md:205`），要求 Flutter 上游端口与代理的 `--upstream-port` 保持相同（`README.md:208`）；web README 则写明不需要单独的 Node 进程或代理端口，内置开发服务器直接位于 http://127.0.0.1:4835（`apps/flutter/app/web/README.md:20`）。本页的开发步骤按 web README（Web Access 的专门文档）写，README 的双终端步骤只记录在本段，不作为操作指导。另注意：`tools/dev_web_access_proxy.mjs` 在当前仓库树中不存在，README 的双终端步骤目前不可直接执行。

### 备份与迁移

快照、配置与身份数据的确切范围由当前命令帮助与格式版本决定；活动进程与实时会话留在原节点，备份不等于全部运行时状态都已迁移（`README.md:90`）。

任务交接以工具结果已持久化、下一轮模型请求尚未开始为界；目标节点拿到所需的同步记录后继续工作，不搬运进行中的模型请求、终端进程或浏览器会话（`README.md:22`）。

### 安全边界

命令参数以 `operit2 --help` 与 `operit2 cli` 的实际输出为准；不得用默认开发 token 在公网监听；不得把 token、私钥或真实业务数据放进公开日志或截图（`README.md:53`）。

README 称 API 密钥、设备私钥、配对密钥、会话与本地平台权限默认归属本地节点，加入 `Space` 不会自动复制（`README.md:128`）。`Full` 只表示放宽 AI 能力限制，不提升 `Host` 权限，也不创造操作系统没有的能力（`README.md:129`）。

Provider 配置走另一条路，与上面这句 README 原则冲突：
`ModelConfigManager` 的模型配置 store 由 `preferenceStore` 创建（`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:136`）。
`preferenceStore` 用 `PreferencesDataStore::newWithStorage` 打开偏好 store（`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:112`）。
`newWithStorage` 创建的是 `Space` 偏好 store（`core/crates/persistence/store/src/PreferencesDataStore.rs:2924`）。
`writeProvider` 把整个 `ProviderProfile` 以 `provider_<id>` 为键写入同步偏好（`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:1332`）。
`ProviderProfile` 包含 `apiKey` 与 `apiKeyPool`（`core/crates/foundation/model/src/ModelConfigData.rs:603`）。
结论：Provider 凭证存在随配置同步的实现路径，加入 `Space` 不会自动复制不能作为当前实现的保证（`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:1332`）。
范围说明：以上只核实了代码里的同步偏好写入路径，没有做真实双设备同步实验，不保证另一台设备实际收到凭证。

## 关键符号

- `CoreNode` — 运行 Core 的实例（`README.md:18`）
- `Host` — 向 CoreNode 提供本地能力的平台适配层（`README.md:18`）
- `Space` — 组织节点协作与持久化同步的范围（`README.md:18`）
- `Binding` — 记录下一个继续任务的节点（`README.md:18`）
- `PeerLink` — 承载 Space 请求与同步流量的传输层（`README.md:43`）
- `discoveryEnabled` — 发现广播的开关（`docs/device-space-lan-discovery.md:7`）
- `nodeId` — 发现广播与连接码中的节点标识（`docs/device-space-lan-discovery.md:9`）
- `ServiceDiscovery` — 记录发现接口、地址、守护进程错误与扫描总数的日志来源（`docs/device-space-lan-discovery.md:46`）
- `RuntimePeerService` — 记录广播总数与四类过滤总数的组件（`docs/device-space-lan-discovery.md:51`）
- `ProviderProfile` — 模型 Provider 配置，含 apiKey 与 apiKeyPool（`core/crates/foundation/model/src/ModelConfigData.rs:603`）
- `ModelConfigManager::preferenceStore` — 模型配置管理器入口，用 newWithStorage 打开偏好 store（`core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:108`）
- `PreferencesDataStore::newWithStorage` — 创建 Space 偏好 store（`core/crates/persistence/store/src/PreferencesDataStore.rs:2924`）
- `SpaceJoinRequest` — 加入申请记录，状态字段是 SpaceJoinStatus（`core/crates/node/runtime/src/NodeSpaceService.rs:313`）
- `SpaceJoinStatus` — 加入申请状态机（`core/crates/node/runtime/src/NodeSpaceService.rs:307`）
- `web_dev_config.yaml` — Flutter Web 开发服务器的配置，内置服务器地址 127.0.0.1:4835（`apps/flutter/app/web/README.md:18`）
- `operit2 cli link` — CLI 的配对、发现与 Space 管理入口（`apps/cli/src/cli/link.rs:36`）

## 调用链

1. 装环境：Rust stable 与 rustup、Flutter SDK 与 FVM、Node.js、Python 3（`README.md:156`）。
2. 启动本节点：`operit2` 进入 TUI（`README.md:175`），或从仓库根目录用 `cargo run --manifest-path apps/cli/Cargo.toml --bin operit2` 启动 CLI（`README.md:170`）。
3. 启动监听器：`operit2 cli link listen http`（`apps/cli/src/cli/link.rs:1309`）；设备在监听器运行且 `discoveryEnabled` 开启时才广播（`docs/device-space-lan-discovery.md:7`）。
4. 发现对端：`operit2 cli link discover`（`apps/cli/src/cli/link.rs:1304`），或在添加设备对话框里 5 秒扫描（`docs/device-space-lan-discovery.md:11`）。
5. 连接码配对——提供方：`operit2 cli link qr` 显示二维码与连接码（`apps/cli/src/cli/link.rs:195`）。
6. 连接码配对——接收方：`operit2 cli link pair <connection-code>`，`operit://` 分支配对成功后直接返回，不出现六位码提示（`apps/cli/src/cli/link.rs:122`）。
7. 手动配对：`operit2 cli link pair <device-name>` 后在接收设备上读六位码，CLI 提示输入配对码完成配对（`apps/cli/src/cli/link.rs:127`）。
8. 加入 Space：`operit2 cli link space join [device-name|number]` 只提交加入申请并打印回执（`apps/cli/src/cli/link.rs:799`）。
9. 加入审批：Space 一侧用 `link space requests incoming` 查看收到的申请，用 `link space approve [applicant-name]` 或 `reject` 做决定（`apps/cli/src/cli/link.rs:830`）。
10. 查申请状态：申请人用 `link space requests outgoing` 列出已发出的申请（`apps/cli/src/cli/link.rs:805`）。
11. 刷新申请：`link space refresh [space-name]` 对发出的申请调用 `refreshDeviceSpaceJoin` 并打印更新后的回执（`apps/cli/src/cli/link.rs:824`）。
12. 成功判据：已批准的加入申请经 `adoptApprovedMembership` 落为 `Joined`（`core/crates/node/runtime/src/peer/space_join.rs:1318`）。
13. 核对成员：用 `operit2 cli link space show` 核对 Space 名称与成员数量（`apps/cli/src/cli/link.rs:729`）。
14. Flutter 扫码：扫码后点 `Confirm join` 直接连接并提交加入请求，无需输入配对码（`apps/flutter/app/lib/l10n/generated/app_localizations_zh.dart:4565`）。
15. 用浏览器访问：`operit2 cli web open` 打开 https://web.operit.app/（`apps/cli/src/cli/web.rs:6`）；打开页面不会自动让浏览器成为 `Space` 中的独立节点（`README.md:72`）。
16. 备份：`operit2 cli export snapshot <path>` 导出快照（`apps/cli/src/cli/transfer.rs:53`），恢复用 `operit2 cli backup restore <path>`（`apps/cli/src/cli/transfer.rs:122`），检查用 `operit2 cli backup inspect <snapshot-zip-path>`（`apps/cli/src/cli/transfer.rs:123`）。

## 来源

- README.md
- docs/device-space-lan-discovery.md
- apps/flutter/app/web/README.md
- apps/cli/src/cli/link.rs
- apps/cli/src/cli/mod.rs
- apps/cli/src/cli/transfer.rs
- apps/cli/src/cli/web.rs
- apps/cli/src/main.rs
- apps/flutter/app/web_dev_config.yaml
- core/crates/command/core/src/commands/storage.rs
- core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs
- core/crates/foundation/model/src/ModelConfigData.rs
- core/crates/persistence/store/src/PreferencesDataStore.rs
- core/crates/node/runtime/src/NodeSpaceService.rs
- core/crates/node/runtime/src/peer/space_join.rs
- apps/flutter/app/lib/ui/common/PeerQrCodeDialog.dart
- apps/flutter/app/lib/ui/common/DeviceSpaceDiscoveryPanel.dart
- apps/flutter/app/lib/ui/common/SpaceJoinWidgets.dart
- apps/flutter/app/lib/l10n/generated/app_localizations_zh.dart
