---
title: 局域网发现、配对与加入 Space
module: sync
platforms: [android, ios, macos, windows, linux, ohos]
sources: [4]
date: 2026-11-11
---

## 概述

- 本页讲同一局域网内的设备如何被发现、如何配对、如何加入对方的 Space。`docs/device-space-lan-discovery.md:5`
- 发现查询 `_operit-link._tcp.local.`，不枚举 IP 地址。`docs/device-space-lan-discovery.md:5`
- 设备仅在已配置的网络监听器运行且 `discoveryEnabled` 启用时才广播。`docs/device-space-lan-discovery.md:7`
- 默认监听器为 HTTP 与 WebSocket，监听 OS 分配的端口并绑定 `0.0.0.0`。`docs/device-space-lan-discovery.md:8`
- 已发现的 `nodeId` 只是拨号提示，不是授权依据。`docs/device-space-lan-discovery.md:21`
- 配对本身不授予 Space 成员资格与业务权限：配对授权方向、Space 成员准入、业务权限分别检查，单向配对不产生反向授权。`docs/link-access-architecture.md:99`
- 加入复用任一方向的当前配对，配对建立方向只是传输历史，不是申请人权限；配对侧的批准仍是唯一的成员同意。`core/crates/node/runtime/src/peer/space_join.rs:172`
- 加入成功后成员关系进入 Space 同步，见 [[sync-overview|同步总览：Space 持久化同步]]。`core/crates/node/runtime/src/peer/space_join.rs:1323`

## AI 速览

- `subscribeDiscovery` — 经 Host 订阅局域网发现服务并缓存记录。`core/crates/node/runtime/src/peer/discovery.rs:18`
- `rememberDiscoveryRecords` — 为已配对与未配对节点保留当前服务端的端点。`core/crates/node/runtime/src/peer/discovery.rs:7`
- `reconnectionEndpoints` — 在已保存端点之前尝试新发现的地址。`core/crates/node/runtime/src/peer/discovery.rs:32`
- `saveAuthenticatedEndpoint` — 只提交已认证的地址。`core/crates/node/runtime/src/peer/discovery.rs:51`
- `PeerMessage` — Transport 公共消息，其未加标签的序列化直接保留 Link 信封。`docs/link-access-architecture.md:51`
- `CoreLinkRequest` — Link 请求，含 Call、Watch、Push 三个变体。`docs/link-access-architecture.md:57`
- `CoreLinkResponse` — Link 响应，含 Call、Watch、Push 三个变体。`docs/link-access-architecture.md:62`
- `CoreLinkClient` — Link 客户端，入口为 `call`、`watchSnapshot`、`watch`、`openPush`。`docs/link-access-architecture.md:69`
- `CoreLinkSharedClient` — 共享 Link 客户端，入口与 `CoreLinkClient` 相同。`docs/link-access-architecture.md:69`
- `RoutedCoreRequest<T>` — 带 Space 路由元数据的请求，字段含 `spaceId`、`originNodeId`、`targetNodeId`、`ttl`、`routeKind`、`payload`。`docs/link-access-architecture.md:126`
- `refresh` — 加入请求的轮询入口：提交、查状态、采纳已批准的成员关系。`core/crates/node/runtime/src/peer/space_join.rs:1296`
- `request` — 加入请求入口，先执行 `prepareRequest`，再执行 `refresh`。`core/crates/node/runtime/src/peer/space_join.rs:555`
- `prepareSubmission` — 新建加入请求并保存到 OUTBOUND。`core/crates/node/runtime/src/peer/space_join.rs:613`
- `receive` — 网关侧接收加入命令的入口，接受 `requestJoin`、`cancelJoin` 与 `joinStatus`。`core/crates/node/runtime/src/peer/space_join.rs:734`
- `reconcile` — 加入记录的对账入口，依次执行 `expire`、`recoverCommittedApproval` 与 `assign`。`core/crates/node/runtime/src/peer/space_join.rs:313`
- `assignReviewer` — 评审员指派，本地节点有评审能力时优先选本地节点。`core/crates/node/runtime/src/peer/space_join.rs:232`
- `canReview` — 评审能力判定，要求节点未断开且同时具备加入与批准能力。`core/crates/node/runtime/src/peer/space_join.rs:166`
- `joinSnapshot` — 读取对端 Space 快照。`core/crates/node/runtime/src/peer/space_join.rs:1428`
- `callPeerSpace` — 在直接配对的对端上调用一个明确的 Space 方法。`core/crates/node/runtime/src/peer/space_join.rs:1460`
- `adoptApprovedMembership` — 采纳已批准的成员关系。`core/crates/node/runtime/src/peer/space_join.rs:1316`
- `cancel` — 取消加入请求，先持久化取消意图再发送取消。`core/crates/node/runtime/src/peer/space_join.rs:1411`
- `purgeDevice` — 配对被遗忘时退役加入申请与评审状态。`core/crates/node/runtime/src/peer/space_join.rs:676`
- `decide` — 评审员决策入口，要求本设备具备评审能力。`core/crates/node/runtime/src/peer/space_join.rs:1211`
- 主入口函数：`request`。`core/crates/node/runtime/src/peer/space_join.rs:555`
- 数据流向一句话：mDNS 发现提供拨号提示，配对建立已认证会话，`refresh` 轮询加入请求直至采纳已批准的成员关系。`core/crates/node/runtime/src/peer/space_join.rs:1296`

## 核心机制

- TXT 元数据必须包含 `nodeId`、`displayName` 与 `transports`。`docs/device-space-lan-discovery.md:9`
- 不完整的广播被拒绝并给出诊断信息，不编造协议数据。`docs/device-space-lan-discovery.md:10`
- 添加设备对话框执行 5 秒主动扫描。`docs/device-space-lan-discovery.md:11`
- 刷新时重启共享查询，同时保留订阅句柄，不只读旧快照，也不创建竞争的浏览器。`docs/device-space-lan-discovery.md:12`
- 本地设备与已配对设备被有意排除在添加设备结果之外，包括当前离线的已配对设备。`docs/device-space-lan-discovery.md:14`
- 被排除设备的已解析端点仍可供连接层使用。`docs/device-space-lan-discovery.md:16`
- 可用性工作线程即使在添加设备对话框关闭时也订阅同一个 Host 浏览器。`docs/device-space-lan-discovery.md:17`
- 离线的已配对网络设备用排序后的已发现地址重连，已保存地址作为后备。`docs/device-space-lan-discovery.md:18`
- 每个备选地址各获得一次有界的连接与认证尝试。`docs/device-space-lan-discovery.md:20`
- 会话握手核验期望节点并证明持有已有配对密钥后，运行时把成功的地址与 transport 持久化到出站配对记录。`docs/device-space-lan-discovery.md:22`
- 端点持久化包含 OS 分配监听端口的变化，不需要新的配对码。`docs/device-space-lan-discovery.md:24`
- 认证失败时已保存的端点保持不变。`docs/device-space-lan-discovery.md:25`
- 并发的解除配对或凭据替换不会被进行中的连接撤销。`docs/device-space-lan-discovery.md:26`
- 已建立的通道复用到失败为止，发现不会为在线对端再开一条通道。`docs/device-space-lan-discovery.md:27`
- Windows、Linux、Android 与 OHOS 使用共享的原生 mDNS 提供方。`docs/device-space-lan-discovery.md:32`
- Android 在守护进程打开套接字前获取 Wi-Fi 组播锁，在关闭后释放。`docs/device-space-lan-discovery.md:34`
- 纯以太网 Android 硬件没有 Wi-Fi 组播过滤器可获取。`docs/device-space-lan-discovery.md:35`
- iOS 与 macOS 使用系统 Bonjour DNS-SD 守护进程，不使用应用自有的 UDP 组播套接字。`docs/device-space-lan-discovery.md:37`
- IPv4 与 IPv6 地址观察器保留发现服务时所在的接口。`docs/device-space-lan-discovery.md:39`
- Flutter 应用在 iOS 与 macOS 上声明 `_operit-link._tcp` 与本地网络权限说明。`docs/device-space-lan-discovery.md:41`
- `ServiceDiscovery` 日志记录所选的原生浏览接口、已解析地址与端口、守护进程错误、广播与扫描总数。`docs/device-space-lan-discovery.md:46`
- Apple 权限拒绝被明确报告，不会变成一次空的成功扫描。`docs/device-space-lan-discovery.md:48`
- `RuntimePeerService` 记录原始广播总数与本地、已配对、无效、可添加四类过滤总数。`docs/device-space-lan-discovery.md:51`
- 两端都必须放行本地组播 DNS 流量（UDP 5353 到 `224.0.0.251` / `ff02::fb`）与到已广播监听端口的入站连接。`docs/device-space-lan-discovery.md:55`
- AP/客户端隔离、组播过滤与防火墙策略属于网络配置问题，不由另一发现协议绕过。`docs/device-space-lan-discovery.md:57`
- v2 连接码携带节点 ID、显示名、实时网络地址与 5 分钟有效的随机邀请密钥。`docs/device-space-lan-discovery.md:108`
- 扫描器在打开连接前只显示一个 Confirm join 操作。`docs/device-space-lan-discovery.md:109`
- 二维码确认经已有的 SPAKE2 配对交换认证并提交 Space 加入请求，该路径两端都不显示手动配对码对话框。`docs/device-space-lan-discovery.md:110`
- 同意绑定到所显示的 Space 与当前配对，旧邀请不能授权加入另一 Space。`docs/device-space-lan-discovery.md:113`
- 二维码地址来自活动监听套接字与 Host 当前网络接口，通配符绑定、端口 0、环回与无作用域 IPv6 链路本地地址从不发布。`docs/device-space-lan-discovery.md:119`
- Host 枚举接口时不启动 mDNS 浏览器或广播，因此二维码连接在发现关闭时仍可用。`docs/device-space-lan-discovery.md:121`
- 连接码不绕过防火墙，也不在隔离网络之间建立连通性。`docs/device-space-lan-discovery.md:123`
- CLI 命令 `operit2 cli link qr` 渲染黑白终端二维码。`docs/device-space-lan-discovery.md:129`
- Link 的三个基础操作是 Call、Watch、Push。`docs/link-access-architecture.md:3`
- 当前五种 transport 已统一承载标准 Link 消息，共享客户端具备完整三个操作族；路由行为和 Host 边界仍有待清理项。`docs/link-access-architecture.md:5`
- `CoreLinkRequest` 的 Call 变体为 `CoreCallRequest`。`docs/link-access-architecture.md:57`
- `CoreLinkRequest` 的 Watch 变体为 Snapshot、Open、Close。`docs/link-access-architecture.md:58`
- `CoreLinkRequest` 的 Push 变体为 Open、Item、Close。`docs/link-access-architecture.md:59`
- `CoreLinkResponse` 的 Watch 变体为 Snapshot、Opened、Event、Closed 或错误。`docs/link-access-architecture.md:62`
- `CoreLinkResponse` 的 Push 变体为 Opened、ItemAccepted、Closed 或错误。`docs/link-access-architecture.md:63`
- `watchSnapshot` 属于 Watch，`openPush`、发送 item 与关闭属于 Push 的生命周期，不增加基础操作族。`docs/link-access-architecture.md:66`
- `RuntimePeerService` 与 `PeerRouter` 都具备对应的节点通信入口。`docs/link-access-architecture.md:70`
- `SessionSpaceClient` 的 `openPush` 为输入流分配独立请求 ID，重校绑定的 Space 接入身份，再经同一已认证 Peer runtime 打开 Push。`docs/link-access-architecture.md:73`
- 控制目标 `$peer.pairing` 用于身份握手与配对确认。`docs/link-access-architecture.md:88`
- 控制目标 `$peer.session` / `data` 承载加密后的标准 Link 消息。`docs/link-access-architecture.md:89`
- 控制目标 `$peer.space-channel` 用于认证配对会话中的 Space 通道管理。`docs/link-access-architecture.md:90`
- 控制目标 `$peer.keepalive` / `ping` 用于会话保活。`docs/link-access-architecture.md:91`
- 会话先编码内层 `PeerMessage` 并加密，再用 `$peer.session/data` Call 的二进制 args 发送；接收侧检查序号与认证标签，解密后恢复原始 Call、Watch、Push 消息。`docs/link-access-architecture.md:93`
- 匿名连接不能进入普通业务 dispatch，认证后每个业务入口仍重校授权。`docs/link-access-architecture.md:98`
- `PeerStateStore` 的 `PAIRING_SERVICE_VERSION` 为 1，是持久化凭据格式，已有配对继续有效。`docs/link-access-architecture.md:103`
- `Hello` 的 `pairingProtocol` 与 `HelloReply` 的 `pairingProtocol` 协商新配对流程，当前为 2；新建配对要求双方都支持 2。`docs/link-access-architecture.md:105`
- 旧版本配对收到 `PAIRING_PROTOCOL_UPGRADE_REQUIRED`，需要先升级，而不是静默退回旧确认方式。`docs/link-access-architecture.md:106`
- finish 阶段把六位配对码作为 SPAKE2（Ed25519 group）口令，不再发送可用 root 离线校验的 HMAC。`docs/link-access-architecture.md:110`
- 确认次数同时受单个 pending 的 5 次上限与跨会话令牌桶限制，`start` 也受创建速率限制。`docs/link-access-architecture.md:114`
- `routeKind` 取值为 Target、SpaceRoute、SpaceBinding 三种。`docs/link-access-architecture.md:129`
- `peer/dispatch.rs` 在 Call、Watch、Push Open 的标准请求 args 中编码完整的 `RoutedCoreRequest`。`docs/link-access-architecture.md:133`
- HTTP、WebSocket、TCP、Serial、Bluetooth 五种 transport 共用 `FramedPeerConnection` 消息层。`docs/link-access-architecture.md:155`
- MessagePack 是产品 Link 的统一编码。`docs/link-access-architecture.md:161`
- HTTP、WebSocket、TCP 使用同一个网络监听端口，每种 transport 只注册自己的处理器。`docs/link-access-architecture.md:167`
- 端口为 0 时只分配一次，后续 transport 使用实际端口；移除一种 transport 保留其它处理器，最后一种关闭后才释放端口。`docs/link-access-architecture.md:172`
- 裸 `ip:port` 用一次一次性 TCP 探测连接分类，发送 WebSocket 升级请求后按首个响应判定载体。`docs/link-access-architecture.md:185`
- 探测判定规则为：`HTTP/… 101` 是 WebSocket，任何其他 `HTTP/…` 状态是 HTTP，无字节即断开是 TCP。`docs/link-access-architecture.md:186`
- 判定后地址按载体规范化，pending 配对记录保存规范化后的端点，后续重拨与观测地址刷新使用同一路径。`docs/link-access-architecture.md:189`
- Transport 只通过 Host API 执行 I/O，不持有配对、Space 策略或业务 dispatch。`docs/link-access-architecture.md:234`
- 目标不可达必须保持目标语义并明确报告错误，禁止静默改成本机执行。`docs/link-access-architecture.md:237`
- 待清理项：不可达 Binding 改成本机，位置在 `CoreNodeRouter.rs` 的 `effectiveBinding`，本次请求的有效执行节点被静默替换。`docs/link-access-architecture.md:247`
- 待清理项：部分路由失败后更换下一跳重发，位置在 `route_forwarding.rs` 的 `forwardOperation`，普通 target 可重提交，设备工具与硬件 target 被排除。`docs/link-access-architecture.md:248`
- 待清理项：串口地址规范化包含平台判断，位置在 `peer-link/src/transport/serial.rs` 的 `endpointKey`，Windows 端口规范化仍位于 transport，Host 边界未完全收敛。`docs/link-access-architecture.md:249`
- Transport 消息协议与共享 Link 客户端已覆盖 Call、Watch、Push，Router 执行路径与 Host 边界仍需要代码层整改。`docs/link-access-architecture.md:251`
- `subscribeDiscovery` 的回调把每条记录交给 `rememberDiscoveryRecords`。`core/crates/node/runtime/src/peer/discovery.rs:20`
- `reconnectionEndpoints` 仅在已保存 transport 是网络 transport 时使用已发现记录。`core/crates/node/runtime/src/peer/discovery.rs:35`
- `reconnectionEndpoints` 按记录属性 `nodeId` 等于目标节点筛选已发现记录。`core/crates/node/runtime/src/peer/discovery.rs:37`
- 已发现对端地址以 `http://` 开头映射为 `PeerTransport` 的 Http，以 `ws://` 开头映射为 WebSocket，其余映射为 Tcp。`core/crates/node/runtime/src/peer/discovery.rs:40`
- 已保存端点在未包含于列表时作为后备追加到末尾。`core/crates/node/runtime/src/peer/discovery.rs:47`
- `saveAuthenticatedEndpoint` 在当前 `sessionId` 或 `sessionSecret` 与原始记录不同时返回 `PEER_PAIRING_CHANGED` 错误。`core/crates/node/runtime/src/peer/discovery.rs:55`
- saveAuthenticatedEndpoint 在当前端点或 transport 已被操作员改动时直接返回成功，不覆盖操作员的改动。`core/crates/node/runtime/src/peer/discovery.rs:59`
- saveAuthenticatedEndpoint 在当前端点与 transport 已等于新地址时直接返回成功，不重复写回。`core/crates/node/runtime/src/peer/discovery.rs:60`
- saveAuthenticatedEndpoint 经 `updateOutboundEndpointLocked` 写回新端点与 transport。`core/crates/node/runtime/src/peer/discovery.rs:62`
- 加入请求的存活期常量 `LIFETIME_MS` 为 15 分钟。`core/crates/node/runtime/src/peer/space_join.rs:21`
- 评审员离线宽限期常量 `OFFLINE_GRACE_MS` 为 30000 毫秒。`core/crates/node/runtime/src/peer/space_join.rs:22`
- 入站、出站、收件箱与结果四类加入记录分别由 `INBOUND`、`OUTBOUND`、`INBOX`、`RESULTS` 四个常量指向各自的运行时路径。`core/crates/node/runtime/src/peer/space_join.rs:17`
- `prepareRequest` 先以 `PairingDirection` 的 Either 校验与目标设备的当前配对。`core/crates/node/runtime/src/peer/space_join.rs:564`
- `prepareRequest` 在存在到同一设备的活动出站请求时直接返回该请求的 requestId，不新建请求。`core/crates/node/runtime/src/peer/space_join.rs:565`
- 新建的 `SpaceJoinRequest` 状态为 Pending，`expiresAt` 为当前时间加 `LIFETIME_MS`。`core/crates/node/runtime/src/peer/space_join.rs:625`
- 新建记录经 `saveRecord` 保存到 OUTBOUND。`core/crates/node/runtime/src/peer/space_join.rs:630`
- 在 `cancelRequested` 为真时先执行 `cancelRemote`，结果非活动时直接返回该结果。`core/crates/node/runtime/src/peer/space_join.rs:1298`
- 调用对端前以 `PairingDirection` 的 Either 重新校验与目标设备的配对。`core/crates/node/runtime/src/peer/space_join.rs:1304`
- 已提交时调用 `joinStatus` 并传入请求 id，未提交时调用 `requestJoin` 并传入 `submissionValue` 的提交内容。`core/crates/node/runtime/src/peer/space_join.rs:1305`
- 经 `callPeerSpace` 调用目标设备，并用 `remote.validate` 校验远端回复。`core/crates/node/runtime/src/peer/space_join.rs:1310`
- 重读最新本地记录，本地状态已非活动、已请求取消或状态已变化时直接返回最新本地请求，不应用远端回复。`core/crates/node/runtime/src/peer/space_join.rs:1312`
- 远端状态为 Approved 时要求附带成员收据，经 `adoptApprovedMembership` 采纳成员关系后把状态置为 Joined。`core/crates/node/runtime/src/peer/space_join.rs:1316`
- 发布前把远端请求的 `canApprove` 置为 false。`core/crates/node/runtime/src/peer/space_join.rs:1321`
- 经 `publishOutgoingResponse` 发布状态，发布结果为 Joined 时调用 `afterJoined`，其失败只记警告日志，不让刷新失败。`core/crates/node/runtime/src/peer/space_join.rs:1323`
- 收据的 Space id 须等于目标 Space id，且本地设备与目标设备都是该 Space 成员。`core/crates/node/runtime/src/peer/space_join.rs:1335`
- 采纳前经 `joinSnapshot` 重读当前目标快照，不用过时的批准快照，并校验目标 Space 仍包含申请人。`core/crates/node/runtime/src/peer/space_join.rs:1344`
- 源 Space 于批准后新增成员时（`currentMembers` 不是 `approvedMembers` 的子集）拒绝采纳，要求提交新的合并请求。`core/crates/node/runtime/src/peer/space_join.rs:1352`
- 采纳时导入设备画像与拓扑记录，应用控制操作后执行 `adopt` 采纳快照的 Space。`core/crates/node/runtime/src/peer/space_join.rs:1357`
- `receive` 在分派前以 `PairingDirection` 的 Either 校验与对端的当前配对。`core/crates/node/runtime/src/peer/space_join.rs:731`
- 入站待处理加入请求达到 64 个活动未过期请求时返回 Too many pending join requests 错误。`core/crates/node/runtime/src/peer/space_join.rs:871`
- 同一申请人到同一目标已有活动加入请求时返回 An active join request already exists 错误。`core/crates/node/runtime/src/peer/space_join.rs:874`
- `expire` 把目标 Space id 与当前 Space id 不符的 Pending 请求置为 Cancelled，把 `expiresAt` 已到的 Pending 请求置为 Expired。`core/crates/node/runtime/src/peer/space_join.rs:89`
- `canReview` 要求节点未断开，且同时具备 `network.members.join` 与 `network.approval` 能力。`core/crates/node/runtime/src/peer/space_join.rs:166`
- 当前评审员有能力且可达时保持指派并清空 `unavailableSince`，不在同等接近的对端之间来回切换。`core/crates/node/runtime/src/peer/space_join.rs:241`
- 评审员不可达且未满 `OFFLINE_GRACE_MS` 时保持原指派。`core/crates/node/runtime/src/peer/space_join.rs:247`
- 本地节点有评审能力时优先选本地节点，跳数为 0。`core/crates/node/runtime/src/peer/space_join.rs:250`
- 评审员变更时 `assignmentVersion` 加一。`core/crates/node/runtime/src/peer/space_join.rs:269`
- `reviewerHops` 等于所选节点的跳数加一。`core/crates/node/runtime/src/peer/space_join.rs:277`
- 快照读取要求对端支持快照分页，否则返回 `SPACE_PROTOCOL_INCOMPATIBLE` 错误。`core/crates/node/runtime/src/peer/space_join.rs:1435`
- 导出读取最多尝试 3 次（`0..3`）。`core/crates/node/runtime/src/peer/space_join.rs:1439`
- 仅在导出变化（`SPACE_EXPORT_CHANGED`）时重读，否则返回当次结果。`core/crates/node/runtime/src/peer/space_join.rs:1452`
- 取消发送后请求仍活动时调用 `refresh` 继续轮询。`core/crates/node/runtime/src/peer/space_join.rs:1418`
- purgePeerRecords 删除该设备的 INBOUND、OUTBOUND 与 INBOX 三类加入记录。`core/crates/node/runtime/src/peer/space_join.rs:696`
- `decide` 要求本设备具备评审能力，否则返回 This device cannot approve Space join requests 错误。`core/crates/node/runtime/src/peer/space_join.rs:1211`
- 网关在本地评审员有能力且 `qrJoinConsent` 匹配当前 Space 且未过期时直接批准该加入请求。`core/crates/node/runtime/src/peer/space_join.rs:819`

## 关键符号

- `subscribeDiscovery` — 经 Host 订阅 `_operit-link._tcp.local.`，回调把记录交给 `rememberDiscoveryRecords`。`core/crates/node/runtime/src/peer/discovery.rs:18`
- `rememberDiscoveryRecords` — 为已配对与未配对节点保留当前服务端的端点。`core/crates/node/runtime/src/peer/discovery.rs:7`
- `reconnectionEndpoints` — 在已保存端点之前尝试新发现的地址，保留非网络载体。`core/crates/node/runtime/src/peer/discovery.rs:32`
- `saveAuthenticatedEndpoint` — 只提交已认证的地址，不恢复已删除或已替换的凭据。`core/crates/node/runtime/src/peer/discovery.rs:51`
- `PeerMessage` — Transport 公共消息，其未加标签的序列化直接保留 Link 信封。`docs/link-access-architecture.md:51`
- `CoreLinkRequest` — Link 请求，Call 变体为 `CoreCallRequest`，Watch 变体为 Snapshot、Open、Close，Push 变体为 Open、Item、Close。`docs/link-access-architecture.md:57`
- `CoreLinkResponse` — Link 响应，Watch 变体为 Snapshot、Opened、Event、Closed 或错误，Push 变体为 Opened、ItemAccepted、Closed 或错误。`docs/link-access-architecture.md:62`
- `CoreLinkClient` — Link 客户端，入口为 `call`、`watchSnapshot`、`watch`、`openPush`。`docs/link-access-architecture.md:69`
- `CoreLinkSharedClient` — 共享 Link 客户端，入口与 `CoreLinkClient` 相同。`docs/link-access-architecture.md:69`
- `SessionSpaceClient` 的 `openPush` — 为输入流分配独立请求 ID，重校绑定的 Space 接入身份，再经同一已认证 Peer runtime 打开 Push。`docs/link-access-architecture.md:73`
- `RoutedCoreRequest<T>` — 带 Space 路由元数据的请求，字段含 `spaceId`、`originNodeId`、`targetNodeId`、`ttl`、`routeKind`、`payload`。`docs/link-access-architecture.md:126`
- `FramedPeerConnection` — 五种 transport 共用的消息层。`docs/link-access-architecture.md:155`
- `PAIRING_SERVICE_VERSION` — `PeerStateStore` 的持久化凭据格式版本，值为 1。`docs/link-access-architecture.md:103`
- `LIFETIME_MS` — 加入请求的存活期常量，为 15 分钟。`core/crates/node/runtime/src/peer/space_join.rs:21`
- `OFFLINE_GRACE_MS` — 评审员离线宽限期常量，为 30000 毫秒。`core/crates/node/runtime/src/peer/space_join.rs:22`
- `INBOUND` — 入站加入记录的运行时路径常量。`core/crates/node/runtime/src/peer/space_join.rs:17`
- `OUTBOUND` — 出站加入记录的运行时路径常量。`core/crates/node/runtime/src/peer/space_join.rs:17`
- `INBOX` — 收件箱加入记录的运行时路径常量。`core/crates/node/runtime/src/peer/space_join.rs:17`
- `RESULTS` — 结果加入记录的运行时路径常量。`core/crates/node/runtime/src/peer/space_join.rs:17`
- `request` — 加入请求入口，先执行 `prepareRequest`，再执行 `refresh`。`core/crates/node/runtime/src/peer/space_join.rs:555`
- `refresh` — 加入请求的轮询入口。`core/crates/node/runtime/src/peer/space_join.rs:1296`
- `prepareRequest` — 加入请求准备入口，先校验当前配对。`core/crates/node/runtime/src/peer/space_join.rs:564`
- `prepareSubmission` — 新建加入请求并保存到 OUTBOUND。`core/crates/node/runtime/src/peer/space_join.rs:613`
- `receive` — 网关侧接收加入命令的入口。`core/crates/node/runtime/src/peer/space_join.rs:734`
- `reconcile` — 加入记录的对账入口。`core/crates/node/runtime/src/peer/space_join.rs:313`
- `expire` — Pending 请求的过期与取消处理。`core/crates/node/runtime/src/peer/space_join.rs:89`
- `canReview` — 评审能力判定。`core/crates/node/runtime/src/peer/space_join.rs:166`
- `assignReviewer` — 评审员指派。`core/crates/node/runtime/src/peer/space_join.rs:232`
- `paired` — 任一方向当前配对的校验。`core/crates/node/runtime/src/peer/space_join.rs:172`
- `joinSnapshot` — 读取对端 Space 快照。`core/crates/node/runtime/src/peer/space_join.rs:1428`
- `callPeerSpace` — 在直接配对的对端上调用一个明确的 Space 方法。`core/crates/node/runtime/src/peer/space_join.rs:1460`
- `adoptApprovedMembership` — 采纳已批准的成员关系。`core/crates/node/runtime/src/peer/space_join.rs:1316`
- `cancel` — 取消加入请求。`core/crates/node/runtime/src/peer/space_join.rs:1405`
- `purgeDevice` — 配对被遗忘时退役加入申请与评审状态。`core/crates/node/runtime/src/peer/space_join.rs:676`
- `decide` — 评审员决策入口。`core/crates/node/runtime/src/peer/space_join.rs:1211`

## 调用链

1. 发现订阅：`subscribeDiscovery` 经 Host 订阅 `_operit-link._tcp.local.`。`core/crates/node/runtime/src/peer/discovery.rs:18`
2. 记录缓存：回调把每条记录交给 `rememberDiscoveryRecords`。`core/crates/node/runtime/src/peer/discovery.rs:20`
3. 重连选址：reconnectionEndpoints 在已保存端点之前尝试新发现的地址，已保存端点作为后备追加到末尾。`core/crates/node/runtime/src/peer/discovery.rs:47`
4. 地址提交：握手认证成功后 saveAuthenticatedEndpoint 经 `updateOutboundEndpointLocked` 写回新端点与 transport。`core/crates/node/runtime/src/peer/discovery.rs:62`
5. 发起加入：`request` 先执行 `prepareRequest`，再执行 `refresh`。`core/crates/node/runtime/src/peer/space_join.rs:555`
6. 准备提交：`prepareRequest` 先以 `PairingDirection` 的 Either 校验与目标设备的当前配对。`core/crates/node/runtime/src/peer/space_join.rs:564`
7. 新建记录：新建的 `SpaceJoinRequest` 状态为 Pending，`expiresAt` 为当前时间加 `LIFETIME_MS`，经 `saveRecord` 保存到 OUTBOUND。`core/crates/node/runtime/src/peer/space_join.rs:625`
8. 轮询入口：从 OUTBOUND 读取同意投影，状态非活动时直接返回本地请求。`core/crates/node/runtime/src/peer/space_join.rs:1296`
9. 取消优先：在 `cancelRequested` 为真时先执行 `cancelRemote`，结果非活动时直接返回该结果。`core/crates/node/runtime/src/peer/space_join.rs:1298`
10. 配对重校：调用对端前以 `PairingDirection` 的 Either 重新校验与目标设备的配对。`core/crates/node/runtime/src/peer/space_join.rs:1304`
11. 提交或查状态：已提交时调用 `joinStatus` 并传入请求 id，未提交时调用 `requestJoin` 并传入 `submissionValue` 的提交内容。`core/crates/node/runtime/src/peer/space_join.rs:1305`
12. 远端调用与校验：经 `callPeerSpace` 调用目标设备，并用 `remote.validate` 校验远端回复。`core/crates/node/runtime/src/peer/space_join.rs:1310`
13. 本地优先：重读最新本地记录，本地状态已非活动、已请求取消或状态已变化时直接返回最新本地请求，不应用远端回复。`core/crates/node/runtime/src/peer/space_join.rs:1312`
14. 批准采纳：远端状态为 Approved 时要求附带成员收据，经 `adoptApprovedMembership` 采纳成员关系后把状态置为 Joined。`core/crates/node/runtime/src/peer/space_join.rs:1316`
15. 发布状态：经 `publishOutgoingResponse` 发布状态，发布结果为 Joined 时调用 `afterJoined`，其失败只记警告日志，不让刷新失败。`core/crates/node/runtime/src/peer/space_join.rs:1323`
16. 网关接收：`receive` 接受 `requestJoin`、`cancelJoin` 与 `joinStatus` 三种方法。`core/crates/node/runtime/src/peer/space_join.rs:734`
17. 网关对账：`reconcile` 依次执行 `expire`、`recoverCommittedApproval` 与 `assign`。`core/crates/node/runtime/src/peer/space_join.rs:313`
18. 评审指派：当前评审员有能力且可达时保持指派并清空 `unavailableSince`。`core/crates/node/runtime/src/peer/space_join.rs:241`
19. 评审决策：`decide` 要求本设备具备评审能力，否则返回 This device cannot approve Space join requests 错误。`core/crates/node/runtime/src/peer/space_join.rs:1211`

## 来源

- `docs/device-space-lan-discovery.md`
- `docs/link-access-architecture.md`
- `core/crates/node/runtime/src/peer/discovery.rs`
- `core/crates/node/runtime/src/peer/space_join.rs`
