---
title: 节点——PeerLink 传输与路由宏
module: core
platforms: [all]
sources: 5
date: 2026-11-11
---

# 节点——PeerLink 传输与路由宏

## 概述

- 本页讲节点之间搬运标准 Link 操作的传输层与路由宏，不讲配对、授权、路由决策、持久化与全局 Host 查找，那些不在传输契约内（`core/crates/node/peer-link/src/lib.rs:3`）。
- 传输层分三层组织：`PeerTransport` 枚举定载体（`core/crates/node/peer-link/src/lib.rs:23`）。
- `PeerLink` 是传输契约 trait（`core/crates/node/peer-link/src/lib.rs:128`）。
- `PeerConnection` 是一条双向连接的 trait（`core/crates/node/peer-link/src/lib.rs:96`）。
- `PeerListener` 是监听器 trait（`core/crates/node/peer-link/src/lib.rs:114`）。
- `HostPeerLink` 在 transport 子模块里实现（`core/crates/node/peer-link/src/lib.rs:11`）。
- 各载体的具体实现在 transport 子模块，本页 seed 只含 lib.rs 的契约层，不展开各载体的实现细节（`core/crates/node/peer-link/src/lib.rs:10`）。
- 载体是否可用取决于 Host 装了什么：`detectTransport` 在 Host 未安装 TCP Host 时直接返回 "TCP Host is not installed" 错误（`core/crates/node/peer-link/src/lib.rs:164`）。
- 发现与配对节流由节点运行时的 `HostRuntimePeerService` 承载，详见 [[core-node-runtime|节点——节点运行时]]（`core/crates/node/runtime/src/peer/discovery.rs:5`）。
- 路由宏在编译期给被注解方法生成包装器与路由元数据，运行时由包装器决定本地执行还是远端调用（`core/crates/node/route-macros/src/lib.rs:86`）。
- peer-protocol.json 是一份清单文件，列出 peer 协议相关的源码路径、修订版本与模式根目录（`core/peer-protocol.json:2`）。

## AI 速览

- `PeerTransport` — 五种载体枚举：Http、WebSocket、Tcp、Serial、Bluetooth（`core/crates/node/peer-link/src/lib.rs:23`）
- `PeerLink` — 传输契约，I/O 用显式传入的 Host（`core/crates/node/peer-link/src/lib.rs:126`）
- `PeerConnection` — 一条双向连接，须保序并保留未完整输入（`core/crates/node/peer-link/src/lib.rs:96`）
- `PeerListener` — 只接受连接，不意味鉴权或配对成功（`core/crates/node/peer-link/src/lib.rs:114`）
- `PeerMessage` — untagged 请求/响应信封，保留 Call、Watch、Push（`core/crates/node/peer-link/src/lib.rs:50`）
- `PeerEndpoint` — 节点身份与传输地址，nodeId 只是寻址元数据（`core/crates/node/peer-link/src/lib.rs:41`）
- `detectTransport` — 一次即弃 TCP 探测判定载体（`core/crates/node/peer-link/src/lib.rs:160`）
- `HostPeerLink` — transport 子模块提供的 PeerLink 实现（`core/crates/node/peer-link/src/lib.rs:11`）
- `subscribeDiscovery` — 订阅 `_operit-link._tcp.local.` 的 mDNS 发现（`core/crates/node/runtime/src/peer/discovery.rs:18`）
- `PairingThrottle` — 内存令牌桶，限制确认与新建配对（`core/crates/node/runtime/src/peer/pairing_throttle.rs:76`）
- `pairingSource` — 以实测来源地址分桶，串口与蓝牙各共用一桶（`core/crates/node/runtime/src/peer/pairing_throttle.rs:142`）
- `operit_core_route` — 路由宏属性，生成包装器与路由元数据（`core/crates/node/route-macros/src/lib.rs:86`）
- `__operit_core_binding_` 加原方法名 — 生成的元数据函数，返回 binding 名（`core/crates/node/route-macros/src/lib.rs:163`）
- `__operit_core_permission_` 加原方法名 — 生成的元数据函数，返回 permission 字符串（`core/crates/node/route-macros/src/lib.rs:164`）
- 主入口：传输侧是 PeerLink 的 `connect`（`core/crates/node/peer-link/src/lib.rs:129`）。
- 主入口：监听侧是 PeerLink 的 `listen`（`core/crates/node/peer-link/src/lib.rs:138`）。
- 主入口：路由侧是 `operit_core_route` 注解（`core/crates/node/route-macros/src/lib.rs:86`）。
- 数据流向：调用方经 PeerLink 的 `connect` 建连（`core/crates/node/peer-link/src/lib.rs:129`）。
- 数据流向：连接上传输 `PeerMessage` 信封，保留 Call、Watch、Push 三种操作（`core/crates/node/peer-link/src/lib.rs:50`）。
- 数据流向：路由宏包装器按 `shouldRoute` 决定本地执行或远端调用（`core/crates/node/route-macros/src/lib.rs:256`）。
- 数据流向：发现订阅 `_operit-link._tcp.local.` 服务，配对走令牌桶节流（`core/crates/node/runtime/src/peer/discovery.rs:18`）。

## 核心机制

### 传输契约与载体

- `PeerTransport` 只选 Host 传输方式，不定义另一种应用协议（`core/crates/node/peer-link/src/lib.rs:22`）。
- 单条消息默认上限 4 MiB（`core/crates/node/peer-link/src/lib.rs:14`）。
- 超限消息返回 `MESSAGE_TOO_LARGE_ERROR`，调用方按容量上限归类，不按鉴权故障归类（`core/crates/node/peer-link/src/lib.rs:18`）。
- `receive` 返回 None 表示连接已结束，而不是当前无消息（`core/crates/node/peer-link/src/lib.rs:107`）。
- `close` 是幂等的，唤醒等待中的 I/O；丢弃连接也必须释放 Host 资源（`core/crates/node/peer-link/src/lib.rs:109`）。
- `accept` 返回 None 表示监听器已关闭（`core/crates/node/peer-link/src/lib.rs:120`）。
- `localAddress` 返回实际绑定的 socket，含 Host 选定的端口；非网络传输没有 socket 地址（`core/crates/node/peer-link/src/lib.rs:117`）。
- `listen` 只需本地 endpoint，远端 endpoint 在 accept 时到达（`core/crates/node/peer-link/src/lib.rs:138`）。
- `connect` 接收显式传入的 HostManager、source、target 与 transport（`core/crates/node/peer-link/src/lib.rs:129`）。
- `decode` 先由 `MessageDirection::read` 一次判定方向，不做推测性请求解码（`core/crates/node/peer-link/src/lib.rs:57`）。
- 方向判定读 `body` 字段，再查 `result` 字段：存在为 Response，不存在为 Request（`core/crates/node/peer-link/src/lib.rs:83`）。
- `decodeOwned` 直接从单个自有传输帧保留二进制参数（`core/crates/node/peer-link/src/lib.rs:65`）。
- 串口帧计数器返回四个数：有效帧、CRC 错误、噪声字节、过期未完整 UART 帧（`core/crates/node/peer-link/src/lib.rs:147`）。

### 载体探测

- `detectTransport` 用一次即弃 TCP 连接判定对端说哪种 Link 载体（`core/crates/node/peer-link/src/lib.rs:160`）。
- 配对可从裸 `ip:port` 开始，无需用户先选传输方式（`core/crates/node/peer-link/src/lib.rs:152`）。
- 探测 socket 在真实传输连接前关闭（`core/crates/node/peer-link/src/lib.rs:158`）。
- 探测请求是 `GET /link`，带 `Upgrade: websocket` 与固定的 RFC 6455 示例 `Sec-WebSocket-Key`（`core/crates/node/peer-link/src/lib.rs:180`）。
- 探测读等待 5 秒超时（`core/crates/node/peer-link/src/lib.rs:191`）。
- 对端无字节关闭时判定为 Tcp，即帧式接收方丢弃了无法解析的长度头（`core/crates/node/peer-link/src/lib.rs:198`）。
- 响应头不是 `HTTP/` 前缀时判定为 Tcp（`core/crates/node/peer-link/src/lib.rs:208`）。
- 响应状态码 101 时判定为 WebSocket，其余 HTTP 状态判定为 Http（`core/crates/node/peer-link/src/lib.rs:214`）。
- 探测的三种判定结果是 Http、WebSocket、Tcp；Serial 与 Bluetooth 不走这次探测（`core/crates/node/peer-link/src/lib.rs:214`）。

### 发现与重连

- mDNS 端点只是拨号提示，只有已有的配对密钥能授权地址变更（`core/crates/node/runtime/src/peer/discovery.rs:1`）。
- 发现订阅 `_operit-link._tcp.local.` 服务（`core/crates/node/runtime/src/peer/discovery.rs:18`）。
- 发现记录由 `rememberDiscoveryRecords` 按 fullName 留存，配对与未配对节点都保留（`core/crates/node/runtime/src/peer/discovery.rs:7`）。
- 订阅失败记一条警告并返回 None（`core/crates/node/runtime/src/peer/discovery.rs:25`）。
- 重连先试新发现的地址，再试已保存的 endpoint，非网络载体不受发现影响（`core/crates/node/runtime/src/peer/discovery.rs:32`）。
- 发现地址的传输由地址前缀推导：http:// 对应 Http，ws:// 对应 WebSocket，其余对应 Tcp（`core/crates/node/runtime/src/peer/discovery.rs:41`）。
- 已保存的 endpoint 若不在候选列表中，追加在列表末尾（`core/crates/node/runtime/src/peer/discovery.rs:47`）。
- 只有已鉴权的地址才会被提交：sessionId 或 sessionSecret 不符时返回 PEER_PAIRING_CHANGED 错误（`core/crates/node/runtime/src/peer/discovery.rs:56`）。
- 并发的操作方编辑优先于正在进行的连接：endpoint 或 transport 已被改动时直接返回 Ok，不做变更（`core/crates/node/runtime/src/peer/discovery.rs:58`）。
- 地址与传输已与目标一致时直接返回 Ok，不做任何事（`core/crates/node/runtime/src/peer/discovery.rs:60`）。
- 地址更新成功后记日志并调用 `changed()`（`core/crates/node/runtime/src/peer/discovery.rs:62`）。

### 配对节流

- 六位配对码只有在攻击者只有少量在线尝试次数时才安全（`core/crates/node/runtime/src/peer/pairing_throttle.rs:3`）。
- 仅靠每笔待配对的计数器不够，因为每次新会话都会拿到新码，攻击者能轮换会话直到某次猜中（`core/crates/node/runtime/src/peer/pairing_throttle.rs:5`）。
- 节流状态故意只放内存，重启 CoreNode 即清空（`core/crates/node/runtime/src/peer/pairing_throttle.rs:10`）。
- 全局确认桶容量 10，每小时回补 1 个令牌（`core/crates/node/runtime/src/peer/pairing_throttle.rs:20`）。
- 单来源确认桶容量 5，每十分钟回补 1 个令牌（`core/crates/node/runtime/src/peer/pairing_throttle.rs:25`）。
- 单来源新建配对桶容量 4，每分钟回补 1 个令牌（`core/crates/node/runtime/src/peer/pairing_throttle.rs:29`）。
- 全局新建配对桶容量 6，每分钟回补 1 个令牌（`core/crates/node/runtime/src/peer/pairing_throttle.rs:33`）。
- `MAX_SOURCE_BUCKETS` 常量为 512，不是无条件硬上限（`core/crates/node/runtime/src/peer/pairing_throttle.rs:37`）。
- 新来源先插入 `sourceConfirmations` 桶（`core/crates/node/runtime/src/peer/pairing_throttle.rs:91`）。
- 任一桶 `available` 为假时直接返回，不消费也不清理；全局桶耗尽后持续用新来源进拒绝分支，来源表可增长到 512 以上（`core/crates/node/runtime/src/peer/pairing_throttle.rs:96`）。
- 只有成功消费令牌后才调 `prune` 清理（`core/crates/node/runtime/src/peer/pairing_throttle.rs:101`）。
- `prune` 在桶数超限时先丢弃已完全回补的桶，再按最小键删除，直到回到上限内（`core/crates/node/runtime/src/peer/pairing_throttle.rs:126`）。
- `refill` 按流逝的墙钟时间回补令牌，并用饱和减法容忍时钟回拨（`core/crates/node/runtime/src/peer/pairing_throttle.rs:53`）。
- 回补后的令牌数不超过容量上限（`core/crates/node/runtime/src/peer/pairing_throttle.rs:57`）。
- 确认先查两只桶：`globalConfirmations` 与 `sourceConfirmations` 都允许时才消费，任一桶不允许时不消费另一只桶的额度（`core/crates/node/runtime/src/peer/pairing_throttle.rs:89`）。
- 确认与新建配对使用互不共享的四只桶，配对流量不会互相消耗对方的额度（`core/crates/node/runtime/src/peer/pairing_throttle.rs:76`）。
- 来源识别用实测地址：网络传输取 `remoteAddress` 的 IP，串口与蓝牙各共用一个以传输命名的桶（`core/crates/node/runtime/src/peer/pairing_throttle.rs:142`）。

### 路由宏

- `operit_core_route` 是过程宏属性，注解在方法上（`core/crates/node/route-macros/src/lib.rs:86`）。
- `binding` 参数是必需的标识符，缺失时编译报错（`core/crates/node/route-macros/src/lib.rs:45`）。
- `permission` 省略时默认为空字符串（`core/crates/node/route-macros/src/lib.rs:54`）。
- `permission` 必须写成 caller:capability 或 target:capability，否则编译报错（`core/crates/node/route-macros/src/lib.rs:69`）。
- `create_binding` 必须是非空字符串，否则编译报错（`core/crates/node/route-macros/src/lib.rs:51`）。
- `sdk` 是一个无值的开关标志（`core/crates/node/route-macros/src/lib.rs:34`）。
- 原实现改名为 `__operit_core_local_` 加原方法名，包装器保留原方法签名（`core/crates/node/route-macros/src/lib.rs:107`）。
- 被路由方法最多接受一个 ReverseStream 输入，且必须是 async 方法（`core/crates/node/route-macros/src/lib.rs:120`）。
- 被路由方法必须声明 `binding` 参数，否则编译报错（`core/crates/node/route-macros/src/lib.rs:130`）。
- 生成的元数据函数：`__operit_core_binding_` 加原方法名，返回 binding 名；`__operit_core_permission_` 加原方法名，返回 permission 字符串（`core/crates/node/route-macros/src/lib.rs:163`）。
- 生成的辅助函数：调用辅助 `__operit_core_route_call_` 加原方法名，订阅辅助 `__operit_core_route_watch_snapshot_` 与 `__operit_core_route_watch_` 加原方法名（`core/crates/node/route-macros/src/lib.rs:165`）。
- 路由参数排除反向流输入，逐个经 `core_arg_entry` 序列化（`core/crates/node/route-macros/src/lib.rs:170`）。
- 反向流路由：包装器先问 `shouldRoute`，命中时走 `core_route_reverse_stream`（`core/crates/node/route-macros/src/lib.rs:187`）。
- 反向流方法生成 `__operit_core_route_push_` 加原方法名的推送辅助函数（`core/crates/node/route-macros/src/lib.rs:276`）。
- 对反向流方法做值调用时返回 `REVERSE_STREAM_REQUIRES_PUSH` 错误，要求改走 Push 传输（`core/crates/node/route-macros/src/lib.rs:307`）。
- 返回状态流的包装器用 `shouldRouteWatch` 与 `shouldUseLocalWatchSource` 决定走远端订阅还是本地源订阅（`core/crates/node/route-macros/src/lib.rs:236`）。
- 远端订阅经 `core_route_state_flow` 建立（`core/crates/node/route-macros/src/lib.rs:199`）。
- 本地源订阅经 `core_route_state_flow_with_local_source` 建立，本地实现作为数据源传入（`core/crates/node/route-macros/src/lib.rs:214`）。
- 状态流远端订阅失败时，生成的包装器以 panic 报错，而不是返回错误（`core/crates/node/route-macros/src/lib.rs:207`）。
- 状态流本地源订阅失败时，生成的包装器同样以 panic 报错（`core/crates/node/route-macros/src/lib.rs:223`）。
- 异步调用包装器：`shouldRoute` 命中时经 `core_route_call_response` 发起远端调用并按声明的返回类型解码（`core/crates/node/route-macros/src/lib.rs:256`）。
- 远端调用响应解码失败时经 expect 解包，失败即 panic（`core/crates/node/route-macros/src/lib.rs:589`）。
- 同步方法不走路由，包装器直接调本地实现（`core/crates/node/route-macros/src/lib.rs:271`）。
- unit 返回值编码为 `CoreValue::Null`（`core/crates/node/route-macros/src/lib.rs:483`）。
- 成功时经 `to_core_value` 编码，失败时转为 `CoreLinkError::internal`（`core/crates/node/route-macros/src/lib.rs:493`）。
- `operit_plugin_sdk_expose` 原样返回被注解项，不做任何改写（`core/crates/node/route-macros/src/lib.rs:97`）。
- `operit_core_internal` 原样返回被注解项，只做内部方法标记（`core/crates/node/route-macros/src/lib.rs:620`）。
- `before_change_route` 标记在 Core 路由变更前立即调用的生命周期回调（`core/crates/node/route-macros/src/lib.rs:626`）。
- `after_change_route` 标记在 Core 路由到达目标后调用的生命周期回调（`core/crates/node/route-macros/src/lib.rs:632`）。

### peer-protocol 清单

- `sources` 列出 38 条 peer 协议相关源码路径（`core/peer-protocol.json:2`）。
- `sources` 含 `core/crates/node/peer-link/src`（`core/peer-protocol.json:4`）。
- sources 含 `core/crates/node/route-macros/src`（`core/peer-protocol.json:35`）。
- sources 含 `core/crates/node/runtime/src/peer` 目录（`core/peer-protocol.json:18`）。
- `revisions` 数组从 version 1 起编号（`core/peer-protocol.json:42`）。
- 截至基线 364d1d594，最新修订为 `version` 15（`core/peer-protocol.json:100`）；上游 053c6686 已是 version 19（同文件 :116）。
- 截至基线 364d1d594，`schemaRoots` 列出 7 个模式根目录（`core/peer-protocol.json:104`）；上游 053c6686 已是 8 个（:120 起，新增 foundation/vfs）。
- 清单的消费方式不在本页 seed 范围内：本页 seed 不含读取该清单的构建脚本，不对清单的用途做断言（`core/peer-protocol.json:2`）。

## 关键符号

- `PeerTransport` — 五种载体枚举（`core/crates/node/peer-link/src/lib.rs:23`）
- `PeerListenerCapabilities` — 入站传输与 LAN 发现能力（`core/crates/node/peer-link/src/lib.rs:33`）
- `PeerEndpoint` — 节点身份与传输地址（`core/crates/node/peer-link/src/lib.rs:41`）
- `PeerMessage` — 请求/响应信封（`core/crates/node/peer-link/src/lib.rs:50`）
- MessageDirection 的 `read` — 读 body 再查 result 判定方向（`core/crates/node/peer-link/src/lib.rs:83`）
- `PeerConnection` — 双向连接 trait（`core/crates/node/peer-link/src/lib.rs:96`）
- `PeerListener` — 监听器 trait（`core/crates/node/peer-link/src/lib.rs:114`）
- `PeerLink` — 传输契约 trait（`core/crates/node/peer-link/src/lib.rs:126`）
- `HostPeerLink` — transport 子模块提供的实现（`core/crates/node/peer-link/src/lib.rs:11`）
- `detectTransport` — 一次即弃 TCP 探测判定载体（`core/crates/node/peer-link/src/lib.rs:160`）
- `classifyEndpoint` — 发 WebSocket 升级探测并读状态码判定（`core/crates/node/peer-link/src/lib.rs:172`）
- `serialFrameCounters` — 串口帧四元计数器（`core/crates/node/peer-link/src/lib.rs:147`）
- `DEFAULT_MAX_PEER_MESSAGE_BYTES` — 单条消息默认上限 4 MiB（`core/crates/node/peer-link/src/lib.rs:14`）
- `MESSAGE_TOO_LARGE_ERROR` — 超限错误文本（`core/crates/node/peer-link/src/lib.rs:18`）
- `subscribeDiscovery` — mDNS 发现订阅（`core/crates/node/runtime/src/peer/discovery.rs:15`）
- HostRuntimePeerService 的 `rememberDiscoveryRecords` — 按 fullName 留存发现记录（`core/crates/node/runtime/src/peer/discovery.rs:7`）
- `reconnectionEndpoints` — 新发现地址优先于已保存 endpoint（`core/crates/node/runtime/src/peer/discovery.rs:32`）
- `saveAuthenticatedEndpoint` — 只提交已鉴权地址（`core/crates/node/runtime/src/peer/discovery.rs:52`）
- `PairingThrottle` — 内存令牌桶节流器（`core/crates/node/runtime/src/peer/pairing_throttle.rs:76`）
- `TokenBucket` — 定容令牌桶，按墙钟回补（`core/crates/node/runtime/src/peer/pairing_throttle.rs:40`）
- `pairingSource` — 以实测来源地址分桶（`core/crates/node/runtime/src/peer/pairing_throttle.rs:142`）
- `operit_core_route` — 路由宏属性（`core/crates/node/route-macros/src/lib.rs:86`）
- `CoreRouteArguments` — 路由注解参数解析（`core/crates/node/route-macros/src/lib.rs:10`）
- `validate_permission` — permission 格式校验（`core/crates/node/route-macros/src/lib.rs:62`）
- `expand_core_route` — 生成包装器与路由元数据（`core/crates/node/route-macros/src/lib.rs:100`）
- `operit_plugin_sdk_expose` — 插件 SDK 暴露标记，原样返回（`core/crates/node/route-macros/src/lib.rs:97`）

## 调用链

1. 配对发起方先调 `detectTransport` 做一次即弃 TCP 探测，判定对端载体（`core/crates/node/peer-link/src/lib.rs:160`）。
2. 探测发 `GET /link` 升级请求并读响应头：无字节关闭或非 HTTP 前缀判 Tcp，状态码 101 判 WebSocket，其余判 Http（`core/crates/node/peer-link/src/lib.rs:180`）。
3. 探测读等待 5 秒超时（`core/crates/node/peer-link/src/lib.rs:191`）。
4. 探测 socket 关闭后，调用方按判定结果经 PeerLink 的 `connect` 建连，传入显式 Host、source、target 与 transport（`core/crates/node/peer-link/src/lib.rs:129`）。
5. 建连后双方收发 `PeerMessage` 信封（`core/crates/node/peer-link/src/lib.rs:50`）。
6. 监听侧经 `listen` 只传本地 endpoint，远端 endpoint 在 accept 时到达（`core/crates/node/peer-link/src/lib.rs:138`）。
7. 局域网发现：`subscribeDiscovery` 订阅 `_operit-link._tcp.local.` 服务（`core/crates/node/runtime/src/peer/discovery.rs:18`）。
8. 发现记录由 `rememberDiscoveryRecords` 按 fullName 留存（`core/crates/node/runtime/src/peer/discovery.rs:7`）。
9. 重连时先试新发现的地址，再试已保存的 endpoint（`core/crates/node/runtime/src/peer/discovery.rs:32`）。
10. 新发现地址被采用前，`saveAuthenticatedEndpoint` 核对 sessionId 与 sessionSecret，不符返回 PEER_PAIRING_CHANGED（`core/crates/node/runtime/src/peer/discovery.rs:56`）。
11. 配对确认与新建各过两只令牌桶，先查后扣（`core/crates/node/runtime/src/peer/pairing_throttle.rs:89`）。
12. 异步路由方法先由包装器问 `shouldRoute`，命中则远端调用，否则本地执行（`core/crates/node/route-macros/src/lib.rs:256`）。
13. 状态流订阅：包装器按 `shouldRouteWatch` 与 `shouldUseLocalWatchSource` 分流远端订阅与本地源订阅（`core/crates/node/route-macros/src/lib.rs:236`）。
14. 反向流路由：包装器按 `shouldRoute` 命中后走 `core_route_reverse_stream`（`core/crates/node/route-macros/src/lib.rs:187`）。
15. 路由元数据：`__operit_core_binding_` 加原方法名，返回 binding 名；`__operit_core_permission_` 加原方法名，返回 permission（`core/crates/node/route-macros/src/lib.rs:163`）。

## 来源

- core/crates/node/peer-link/src/lib.rs
- core/crates/node/route-macros/src/lib.rs
- core/crates/node/runtime/src/peer/discovery.rs
- core/crates/node/runtime/src/peer/pairing_throttle.rs
- core/peer-protocol.json
