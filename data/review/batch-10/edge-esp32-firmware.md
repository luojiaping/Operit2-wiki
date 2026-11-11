---
title: ESP32 固件
module: edge
platforms: [esp32]
sources: 9
date: 2026-11-11
---

## 概述

- 固件是 ESP32-2432S028 的 Operit Edge 实现，分工见 [[edge-overview|Edge 总览与产品形态]]。`edge/boards/esp32/src/main.rs:65`
- 设备信息声明平台为 `esp32`、型号为 `ESP32-2432S028`。`edge/boards/esp32/src/main.rs:189`
- README 记录设备不运行工具，也不解释工具结果或状态数据。`edge/boards/esp32/README.md:7`
- 固件拥有原生设备服务，`edge.status/read` 经已配对 Link 返回 board id、expression、IP 地址与 Wi-Fi 名，配对码不包含在服务结果中。`edge/boards/esp32/README.md:20`
- README 记录 ToolPkg 在手机或桌面上作为可选配置编辑器运行，不是 Edge 运行时依赖。`edge/boards/esp32/README.md:22`

## AI 速览

- `runFirmware` — ESP-IDF 目标的固件入口。`edge/boards/esp32/src/main.rs:90`
- `connectOrSetup` — Wi-Fi 连接或设置入口。`edge/boards/esp32/src/wifi.rs:58`
- `Esp32WifiMode` — Station 模式或设置 AP 模式。`edge/boards/esp32/src/wifi.rs:24`
- `Esp32RuntimeStorageHost` 的 `new` — 以 NVS 分区打开硬件快照载体。`edge/boards/esp32/src/runtime_host.rs:26`
- `Esp32ServiceDiscoveryHost` 的 `new` — 初始化 mDNS。`edge/boards/esp32/src/runtime_host.rs:121`
- `DeviceHttpHost` — 设备 HTTP 宿主。`edge/boards/esp32/src/device_http.rs:24`
- `DeviceSpeech` — 设备拥有的语音卸载会话。`edge/boards/esp32/src/device_speech.rs:27`
- `callHandler` — 构造原生设备服务调用处理，返回 `Arc<EdgeCallHandler>`。`edge/boards/esp32/src/device_services.rs:7`
- `call` — 设备 preference 配置编辑端点。`edge/boards/esp32/src/device_preferences.rs:11`
- `WORK` — 单许可信号量，界定本地 Space 工作。`edge/boards/esp32/src/space_work.rs:5`
- `beginRecognition` — 开始识别。`edge/boards/esp32/src/device_speech.rs:204`
- `synthesize` — 合成语音文本。`edge/boards/esp32/src/device_speech.rs:266`
- `takeNativeUpdate` — 原生 UI 轮询语音相位与已完成文本。`edge/boards/esp32/src/device_speech.rs:290`
- 主入口函数为 `runFirmware`。`edge/boards/esp32/src/main.rs:90`
- 数据流向一句话：接纳后共享 Edge 返回客户端经相邻 Core 的 Binding 解析器发送带注解的调用与 watch。`edge/boards/esp32/README.md:261`
- 数据流向一句话：独立聊天方向上，固件经 Host provider 自行发送 HTTPS/HTTP 并渲染 SSE 回复。`edge/boards/esp32/README.md:59`

## 核心机制

### 配对

- Edge 配对使用接收设备上显示的六位码，串口与网络连接通用。`edge/boards/esp32/README.md:27`
- Edge 配对不需要 Edge token、`.edge-token` 文件或 `OPERIT_EDGE_TOKEN` 环境变量，旧 token 设置被忽略。`edge/boards/esp32/README.md:29`
- 配对仍验证设备与共享密钥，加入 Space 是单独的、须批准的动作。`edge/boards/esp32/README.md:33`
- Core 接收远端配对时使用同样的码确认共享握手。`edge/boards/esp32/README.md:34`
- 固件通过 mDNS 通告 `_operit-link`，Core 应用的设备扫描用它发现 ESP32。`edge/boards/esp32/src/runtime_host.rs:141`
- 注：README:14 称 `_operit-edge._tcp`，与代码通告的 `_operit-link` 不一致，以代码为准。`edge/boards/esp32/README.md:14` `edge/boards/esp32/src/runtime_host.rs:141`
- Core 应用扫描发现设备后，输入设备上显示的码开始配对。`edge/boards/esp32/README.md:14`
- mDNS 在 Wi-Fi netif 启动后才初始化，沿用同一 HostManager 注入该能力。`edge/boards/esp32/src/main.rs:259`
- mDNS 主机名为 operit-{nodeId}，通告 `_operit-link` 服务，属性含 nodeId、displayName 与 transports=tcp。`edge/boards/esp32/src/runtime_host.rs:144`
- `localAddresses` 直接读取 `WIFI_STA_DEF` 与 `WIFI_AP_DEF` 两个 netif 的地址。`edge/boards/esp32/src/runtime_host.rs:159`
- ESP32 的 `discover` 未实现，返回未实现错误。`edge/boards/esp32/src/runtime_host.rs:199`
- ESP32 的 `subscribe` 未实现，返回未实现错误。`edge/boards/esp32/src/runtime_host.rs:206`
- `pairingState` 以 `pairedPeers()` 非空判断已配对。`edge/boards/esp32/src/main.rs:354`
- `pairingState` 从 `pairingPrompts()` 取提示并经 `pairingCodeSelection.select` 选出显示的配对码。`edge/boards/esp32/src/main.rs:355`
- 配对码每 1 秒轮询刷新一次，`pairingState()` 失败时清空显示的配对码并保留上次已配对状态。`edge/boards/esp32/src/main.rs:651` `edge/boards/esp32/src/main.rs:656`
- AP 或离线启动时只丢弃未完成的配对（`discardPendingPairingsForUnsynchronizedClock`），不丢弃身份与对端。`edge/boards/esp32/src/main.rs:268`
- edge_unpair 动作对每个已配对对端调用 `removePairedPeer`，再重置设备 Space 界面、聊天路由与配对码。`edge/boards/esp32/src/main.rs:516` `edge/boards/esp32/src/main.rs:534`
- 被接纳进另一 Space 的 ESP 获得持久的 `edge` 身份，同步自有小 preference 或发送聊天不需要 `storage.provide`。`edge/boards/esp32/README.md:45`

### Wi-Fi 配置

- Wi-Fi 从设置页配置，或用 `OPERIT_WIFI_SSID` 与 `OPERIT_WIFI_PASSWORD` 配置。`edge/boards/esp32/README.md:32`
- 有 Wi-Fi 配置时先试 `tryStation`，失败则警告并切换到设置 AP；无配置时直接进入设置 AP。`edge/boards/esp32/src/wifi.rs:78`
- 密码为空时 Station 认证方式为 `AuthMethod::None`，否则为 `AuthMethod::WPAWPA2Personal`。`edge/boards/esp32/src/wifi.rs:113`
- Station 连接后等待 netif 就绪（`wait_netif_up`）。`edge/boards/esp32/src/wifi.rs:136`
- 设置 AP 的 SSID 为 `Operit-ESP32-Setup`，认证方式为 `AuthMethod::None`，最大连接数 4。`edge/boards/esp32/src/wifi.rs:145`
- 设置 AP 的网关为 192.168.4.1。`edge/boards/esp32/src/wifi.rs:159`
- Station 模式下状态栏 SSID 取配置的 Wi-Fi 名，IP 取站点 IPv4，并点亮绿灯 `LED_GREEN_PIN`。`edge/boards/esp32/src/main.rs:232`
- 设置 AP 模式下状态栏 SSID 为 `Operit-ESP32-Setup`，IP 为 192.168.4.1，并点亮红灯 `LED_RED_PIN`。`edge/boards/esp32/src/main.rs:243`
- Wi-Fi 已连接状态要求处于 Station 模式且 `stationConnected()` 为真。`edge/boards/esp32/src/main.rs:221`
- `stationConnected` 要求 Wi-Fi 已连接且站点 IPv4 非全零。`edge/boards/esp32/src/wifi.rs:41`
- 时间同步 `startTimeSync()` 只在 Station 模式下启动。`edge/boards/esp32/src/main.rs:223`
- `startTimeSync()` 的时区取编译期 `OPERIT_TIMEZONE`，缺省为 `CST-8`。`edge/boards/esp32/src/wifi.rs:32`

### 独立聊天与远端 Core 聊天

- 设备的 `chat` preference 用 `endpoint`、`model`、可选的 `apiKey` 与 `systemPrompt` 设置。`edge/boards/esp32/README.md:57`
- README 记录 `chat` 的 `endpoint` 是设备可达的完整 OpenAI 兼容流式聊天补全 URL。`edge/boards/esp32/README.md:58`
- README 记录固件经 Host provider 自行发送 HTTPS/HTTP 并渲染 SSE 回复，不调用 Core，也不要求 Binding。`edge/boards/esp32/README.md:59`
- README 记录 HTTP worker 用 ESP-IDF 证书包验证 HTTPS，并把 I/O 保持在 UI 任务之外。`edge/boards/esp32/README.md:60`
- README 记录独立文本聊天不安装设备端语言模型，仍需互联网与服务可用。`edge/boards/esp32/README.md:62`
- README 记录独立聊天的上下文是 8 条消息、6144 文本字节的 RAM 窗口，单条消息最多 2048 字节。`edge/boards/esp32/README.md:49`
- README 记录固件不创建聊天数据库、ToolPkg 或业务副本日志。`edge/boards/esp32/README.md:50`
- README 记录重启保留配置并开始一段全新的本地对话。`edge/boards/esp32/README.md:51`
- README 记录同一 Space 内其他成员断开连接不会清除直接对话。`edge/boards/esp32/README.md:52`
- README 记录 Space 变更先淘汰旧上下文再验证新设置，即使两个 Space 使用相同的模型配置。`edge/boards/esp32/README.md:53`
- README 记录来自已淘汰上下文的迟到回复不能进入新对话。`edge/boards/esp32/README.md:54`
- README 记录没有 `chat` 配置时仍可用可选的远端 Core 模式，现有 STT/TTS Stream/ReverseStream 处理保留。`edge/boards/esp32/README.md:72`
- README 记录独立文本聊天不意味着已连接 STT/TTS 处理器或已验证物理语音 I/O。`edge/boards/esp32/README.md:75`
- README 记录接纳后共享 Edge 返回客户端经相邻 Core 的 Binding 解析器发送带注解的调用与 watch，插件执行与权限检查留在 Core。`edge/boards/esp32/README.md:261`
- README 记录首个会话生成易失聊天 ID 并调用已有的显式 `ensureRoutedChat` 创建路由，Core 选择已授权执行器并拥有 Binding 与聊天元数据。`edge/boards/esp32/README.md:266`
- README 记录消息与状态订阅及发送只在创建确认成功后启用，读与发送操作从不隐式分配缺失的 Binding。`edge/boards/esp32/README.md:268`
- README 记录选定的聊天 ID 在同一 Space 内重连后保留，Space 变更或设备显式离开或解配时重置；两种聊天上下文规则的对照见 [[edge-esp32-chat|ESP32 聊天实现]]。`edge/boards/esp32/README.md:274`
- README 记录已关闭的主 watch 与意外关闭的嵌入流触发有界订阅恢复，用户发送与非幂等的新聊天请求从不重放。`edge/boards/esp32/README.md:276`
- README 记录只有有界显示数据与选定的 ID 存在于易失 Edge 内存中，设备上不持久化聊天业务副本。`edge/boards/esp32/README.md:278`
- 每 500 毫秒的路由轮询重读 Space 范围与设备 preference，并用 `chat` preference 调用 `standalone_chat::configure`。`edge/boards/esp32/src/main.rs:625` `edge/boards/esp32/src/main.rs:615`
- 路由轮询调用 `chatRoute.poll`，随后用 `edge_chat::isConnected()` 更新 Edge 就绪状态。`edge/boards/esp32/src/main.rs:634`
- README 记录远程聊天显示用 `chatMessagesWindowFlow` watch，可见文本预算 640 字节、15 行硬性文本行、每窗口最多 12 条消息行。`edge/boards/esp32/README.md:364`
- README 记录显示用 1024 字节静态文本缓冲容纳 640 字节负载与发送者标签。`edge/boards/esp32/README.md:377`
- README 记录会话元数据列表只在打开时订阅，最多保留 24 条元数据。`edge/boards/esp32/README.md:384`
- README 记录选中元数据条目只改变该 Edge 自身的视图，不改变 Core 应用选中的会话。`edge/boards/esp32/README.md:385`
- README 记录 C 草稿是 511 字节 UTF-8 显示与输入缓冲，浏览器另行持有完整草稿，上限 16,384 字节。`edge/boards/esp32/README.md:599`
- README 记录超过 2,048 字节的远端聊天发送使用已有 Link Push / ReverseStream 传输，按至多 2,048 字节的 UTF-8 块发送。`edge/boards/esp32/README.md:601`
- README 记录 Core 校验长度、显式提交与 EOF 后才委托 `sendUserMessage`，不完整的输入从不提交已收到的前缀。`edge/boards/esp32/README.md:603`
- README 记录直接模型输入保留已有的 2,048 字节上限。`edge/boards/esp32/README.md:606`

### 设备 preference：上限与合并

- CLI 用 `space preference-set <esp-id> chat <JSON>` 与 `space sync` 设置聊天，也可经通用设备 API 调用原生 `edge.preferences/read|set|remove`。`edge/boards/esp32/README.md:65`
- README 规定设备 preference 按目标设备与 Space 划分范围，最多 24 个键，纯文本文件 6144 字节。`edge/boards/esp32/README.md:67`
- README 记录 preference 协议只交换当前每键状态与删除标记，不交换无界历史。`edge/boards/esp32/README.md:68`
- `call` 只处理 target 为 `edge.preferences` 的请求，其他返回 None。`edge/boards/esp32/src/device_preferences.rs:16`
- `read` 不带 key 时返回全部 preference 值。`edge/boards/esp32/src/device_preferences.rs:29`
- `read` 带 key 时返回该键的值，缺失返回 Null。`edge/boards/esp32/src/device_preferences.rs:31`
- `keys` 返回全部 preference 键的列表。`edge/boards/esp32/src/device_preferences.rs:38`
- `set` 与 `remove` 都要求参数含 `key`，缺失时报错。`edge/boards/esp32/src/device_preferences.rs:45`
- `set` 要求参数含 `value`，缺失时报错；`remove` 以 None 值调用同一 `store.set`。`edge/boards/esp32/src/device_preferences.rs:50`
- 未知方法返回 `Unknown device preference method` 错误。`edge/boards/esp32/src/device_preferences.rs:58`
- 设备 preference 同步任务每 3 秒尝试获取 `space_work::try_acquire()` 许可，拿不到就跳过该轮，拿到才调用 `synchronizePreferences()`。`edge/boards/esp32/src/main.rs:325`

### 原生设备服务

- `callHandler` 构造原生设备服务调用处理。`edge/boards/esp32/src/device_services.rs:7`
- 调用处理按 target 分发 `edge.status`、`edge.scene`、`edge.ui`，其他 target 返回 None。`edge/boards/esp32/src/device_services.rs:13`
- edge.status 的 `health` 方法返回 `runtimeHealthSnapshot()` 的快照。`edge/boards/esp32/src/device_services.rs:30`
- edge.status/read 返回 boardId、expression、ipv4、wifiSsid 与 wifiConnected。`edge/boards/esp32/src/device_services.rs:35`
- edge.ui 的 `chat` 动作返回 `edge_chat::snapshot()`。`edge/boards/esp32/src/device_services.rs:47`
- UI 调试参数超过 120 字节或含 NUL 字节时被拒绝。`edge/boards/esp32/src/device_services.rs:53`
- UI 调试请求带 2 秒截止期，超时未确认则不重试。`edge/boards/esp32/src/device_services.rs:59`
- UI 调试回复等待 3 秒超时。`edge/boards/esp32/src/device_services.rs:61`
- `pumpUi` 只在回复通道未关闭且未过截止期时执行挂起的 UI 请求，否则报告过期请求未执行。`edge/boards/esp32/src/device_services.rs:70`
- 健康快照含 `uptimeMs`、`heapFreeBytes`、`currentTaskStackHighWaterMark` 等字段。`edge/boards/esp32/src/main.rs:708`
- README 记录健康诊断暴露响应任务的栈高水位标记，供硬件验证。`edge/boards/esp32/README.md:83`

### 存储与内存

- 运行时 NVS 命名空间为 `operit_link`，快照键为 `snapshot_v2`。`edge/boards/esp32/src/runtime_host.rs:16`
- 检测到旧版 `snapshot_v1` 或 `files` 数据时拒绝过时存储格式，数据保持原样。`edge/boards/esp32/src/runtime_host.rs:38`
- 快照超过 NVS 条目预算时返回容量耗尽错误，写明所需与可用条目数。`edge/boards/esp32/src/runtime_host.rs:93`
- README 记录 ONV3 信封与 7000 字节逻辑存储上限不变。`edge/boards/esp32/README.md:98`
- README 记录打包记录现用格式 2，含存于固件 Flash 的 847 字节不可变公开 JSON 字段名字典。`edge/boards/esp32/README.md:99`
- README 记录早于记录格式 2 的固件读不了新发布的快照，测试降级时保留匹配的固件与 NVS 备份。`edge/boards/esp32/README.md:106`
- 分配失败证据以 `ALLOCATION_FAILURE` 静态数组存于 `.rtc_noinit` 的 RTC RAM，在 panic 重启后保留。`edge/boards/esp32/src/main.rs:40`
- README 记录固件异步 Edge worker 使用 32 KiB 栈，此前 6 KiB 栈在处理配对请求时溢出。`edge/boards/esp32/README.md:80`
- README 记录独立的阻塞 worker 预留 24 KiB，为节点状态与 Link 操作多留 8 KiB 内部堆。`edge/boards/esp32/README.md:82`
- README 记录主 UI 任务为同步授权与存储解码预留 16 KiB，此前 12 KiB 预留量在受限缓存读路径上溢出。`edge/boards/esp32/README.md:85`
- 固件为整个生命周期挂载 EventFD VFS（`MountedEventfs::mount(8)`），供 Mio/Tokio 设备执行器唤醒使用。`edge/boards/esp32/src/main.rs:126`
- 物理 TFT 是固件唯一的显示输出，诊断像素镜像由 `screenMirror().disablePixelMirror()` 关闭，为配对与聊天保留堆余量。`edge/boards/esp32/src/main.rs:174`
- 串口 UART0 波特率 115_200，接收 FIFO 8192 字节。`edge/boards/esp32/src/main.rs:155`

### HTTP 传输

- 设备 HTTP 只支持 GET 与 POST 方法，其他方法被拒绝。`edge/boards/esp32/src/device_http.rs:41`
- 忽略 SSL、代理、表单字段或文件分段的请求被拒绝为不支持的设备 HTTP 选项。`edge/boards/esp32/src/device_http.rs:34`
- HTTP 连接缓冲收发各 1024 字节，读超时按请求值钳制在 1 至 45 秒，不跟随重定向。`edge/boards/esp32/src/device_http.rs:48`
- HTTPS 验证使用 ESP-IDF 证书包（`esp_crt_bundle_attach`）。`edge/boards/esp32/src/device_http.rs:52`
- `executeHttpRequest` 被拒绝，设备应用必须使用有界 HTTP 流。`edge/boards/esp32/src/device_http.rs:112`
- `downloadFiles` 被拒绝，设备宿主不提供文件下载。`edge/boards/esp32/src/device_http.rs:101`
- `imageDelivery` 返回 `HttpImageDelivery::Bytes`。`edge/boards/esp32/src/device_http.rs:98`
- 设备 HTTP 同一时间只允许一个流，第二个打开请求返回 `Device HTTP is busy` 错误。`edge/boards/esp32/src/device_http.rs:166`
- HTTP worker 线程名为 `device-http`，栈 16 KiB。`edge/boards/esp32/src/device_http.rs:173`
- `closeHttpByteStream` 置取消标志并在句柄非零时中断进行中的 HTTP I/O。`edge/boards/esp32/src/device_http.rs:186`
- 中断调用 `esp_http_client_cancel_request`。`edge/boards/esp32/src/device_http.rs:194`

### 语音传输

- 语音端点 target 为 `operit.device.speech`，音频块常量 `BLOCK` 为 4096 字节。`edge/boards/esp32/src/device_speech.rs:11`
- `watch` 只接受 target 为 operit.device.speech 且属性为 `requests` 的请求。`edge/boards/esp32/src/device_speech.rs:95`
- 语音处理器会话名非空且不超过 128 字节。`edge/boards/esp32/src/device_speech.rs:101`
- 已有语音处理器连接时，新的处理器连接被拒绝。`edge/boards/esp32/src/device_speech.rs:103`
- 就绪事件携带协议号 2（`protocol` 为 2）。`edge/boards/esp32/src/device_speech.rs:108`
- `beginRecognition` 发送 `stt.begin`，参数为采样率 16000、单声道、16 位采样。`edge/boards/esp32/src/device_speech.rs:206`
- 已有进行中的语音任务时，新的 `begin` 返回请先结束当前语音任务的错误。`edge/boards/esp32/src/device_speech.rs:187`
- `synthesize` 拒绝空文本与超过 4096 字节的文本。`edge/boards/esp32/src/device_speech.rs:267`
- PCM 块须非空、不超过 `BLOCK`（4096 字节）且长度为偶数。`edge/boards/esp32/src/device_speech.rs:252`
- 识别文本按 `stt.text` 分块到达，每块不超过 2048 字节，累计待发布文本不超过 16384 字节。`edge/boards/esp32/src/device_speech.rs:329`
- `stt.result` 把累计文本作为完整结果发布，清空待发布缓冲并结束当前任务。`edge/boards/esp32/src/device_speech.rs:344`
- `takeNativeUpdate` 的 phase 为录音中 1、任务进行中 3、空闲 0，同一结果只随 `resultId` 变化取走一次。`edge/boards/esp32/src/device_speech.rs:292`
- 取消当前语音任务时记录错误、`resultId` 加一并排空播放队列。`edge/boards/esp32/src/device_speech.rs:283`
- TTS 音频块须非空且不超过 `BLOCK`（4096 字节），否则返回无效合成音频块错误。`edge/boards/esp32/src/device_speech.rs:370`
- 播放通道为 4 槽 `mpsc` 通道。`edge/boards/esp32/src/device_speech.rs:36`
- 语音处理器事件流为 4 槽有界通道（`boundedChannel(4)`）。`edge/boards/esp32/src/device_speech.rs:106`
- 收到与当前任务 ID 不符的语音响应时返回语音请求已过期错误，迟到结果不能进入新任务。`edge/boards/esp32/src/device_speech.rs:322`
- README 记录语音协议 v2 按 2,048 字节块返回识别文本，只有最终结果发布完整有界草稿，上限 16,384 字节。`edge/boards/esp32/README.md:610`
- README 记录 Core 示例处理器拥有至多 300 秒的 PCM 与 WAV 组装。`edge/boards/esp32/README.md:612`
- README 记录语音捕获限制为 300 秒。`edge/boards/esp32/README.md:643`
- README 记录音频自检无需 Space 或语音处理器：播放一段安静的 250 ms 音调，然后捕获约三秒的麦克风采样统计。`edge/boards/esp32/README.md:662`

### 2026-10-28 验证记录

- README 记录 2026-10-28 验证中独立聊天场景 Rust 堆峰值 208,224 / 262,144 字节，远端聊天、存储恢复与语音场景峰值 212,840 / 262,144 字节，采样状态零分配失败。`edge/boards/esp32/README.md:305`
- README 记录 2026-10-28 桌面回归通过 61 个模拟器测试、29 个板级测试、116 个编辑器测试与 8 个串口调试测试。`edge/boards/esp32/README.md:307`
- README 记录 2026-10-28 构建的镜像使用 3,945,104 / 3,997,696 字节，剩余 52,592 字节。`edge/boards/esp32/README.md:310`
- README 记录同一镜像的 `.flash.text` 使用 3,324,810 / 3,342,304 字节，剩余 17,494 字节，代码映射与镜像分区容量是两个独立上限。`edge/boards/esp32/README.md:311`
- README 记录该镜像尚未再次烧录做硬件验收。`edge/boards/esp32/README.md:312`

## 关键符号

- `runFirmware` — ESP-IDF 目标的固件入口。`edge/boards/esp32/src/main.rs:90`
- `connectOrSetup` — Wi-Fi 连接或设置入口。`edge/boards/esp32/src/wifi.rs:58`
- `Esp32WifiMode` — Station 模式或设置 AP 模式。`edge/boards/esp32/src/wifi.rs:24`
- `Esp32RuntimeStorageHost` 的 `new` — 以 NVS 分区打开硬件快照载体。`edge/boards/esp32/src/runtime_host.rs:26`
- `Esp32ServiceDiscoveryHost` 的 `new` — 初始化 mDNS。`edge/boards/esp32/src/runtime_host.rs:121`
- `DeviceHttpHost` — 设备 HTTP 宿主。`edge/boards/esp32/src/device_http.rs:24`
- `DeviceSpeech` — 设备拥有的语音卸载会话。`edge/boards/esp32/src/device_speech.rs:27`
- `callHandler` — 构造原生设备服务调用处理，返回 `Arc<EdgeCallHandler>`。`edge/boards/esp32/src/device_services.rs:7`
- `call` — 设备 preference 配置编辑端点。`edge/boards/esp32/src/device_preferences.rs:11`
- `WORK` — 单许可信号量，界定本地 Space 工作。`edge/boards/esp32/src/space_work.rs:5`
- `acquire` — 等待本地 Space 工作许可。`edge/boards/esp32/src/space_work.rs:7`
- `try_acquire` — 非阻塞获取本地 Space 工作许可，拿不到返回 None。`edge/boards/esp32/src/space_work.rs:11`
- `is_busy` — 以可用许可数为 0 判断本地 Space 工作繁忙。`edge/boards/esp32/src/space_work.rs:15`
- `beginRecognition` — 开始识别。`edge/boards/esp32/src/device_speech.rs:204`
- `synthesize` — 合成语音文本。`edge/boards/esp32/src/device_speech.rs:266`
- `takeNativeUpdate` — 原生 UI 轮询语音相位与已完成文本。`edge/boards/esp32/src/device_speech.rs:290`
- `runtimeHealthSnapshot` — 健康快照。`edge/boards/esp32/src/main.rs:696`
- `ensureRoutedChat` — 远端聊天首个会话调用的显式创建路由（README 记录）。`edge/boards/esp32/README.md:267`

## 调用链

1. 启动时挂载 EventFD VFS（`MountedEventfs::mount(8)`），供 Mio/Tokio 设备执行器唤醒使用。`edge/boards/esp32/src/main.rs:126`
2. `connectOrSetup` 连接 Station Wi-Fi，失败或无配置时回落到设置 AP。`edge/boards/esp32/src/wifi.rs:58`
3. 时间同步只在 Station 模式下启动。`edge/boards/esp32/src/main.rs:223`
4. Station 模式下状态栏显示配置 SSID 与站点 IPv4，绿灯亮。`edge/boards/esp32/src/main.rs:232`
5. mDNS 在 Wi-Fi netif 启动后初始化。`edge/boards/esp32/src/main.rs:259`
6. 固件通告 `_operit-link`，Core 应用扫描发现设备后，输入设备上显示的码开始配对。`edge/boards/esp32/src/runtime_host.rs:141`
7. 配对使用接收设备上显示的六位码，串口与网络连接通用。`edge/boards/esp32/README.md:27`
8. 接纳后 preference 同步任务每 3 秒尝试取 `space_work` 许可同步设备 preference。`edge/boards/esp32/src/main.rs:325`
9. 独立聊天：`chat` preference 配好端点后，固件经 Host provider 自行发送 HTTPS/HTTP 并渲染 SSE 回复。`edge/boards/esp32/README.md:59`
10. 远端聊天：首个会话生成易失聊天 ID 并调用 `ensureRoutedChat`，Core 选择已授权执行器。`edge/boards/esp32/README.md:266`
11. 路由轮询每 500 毫秒重读 Space 范围与设备 preference，并用 `chat` preference 调用 `standalone_chat::configure`。`edge/boards/esp32/src/main.rs:625` `edge/boards/esp32/src/main.rs:615`
12. 路由轮询调用 `chatRoute.poll`，随后用 `edge_chat::isConnected()` 更新 Edge 就绪状态。`edge/boards/esp32/src/main.rs:634`
13. 语音识别由 `beginRecognition` 以 `stt.begin` 发起。`edge/boards/esp32/src/device_speech.rs:206`
14. 识别文本按 `stt.text` 分块到达，每块不超过 2048 字节，累计待发布文本不超过 16384 字节。`edge/boards/esp32/src/device_speech.rs:329`
15. `stt.result` 把累计文本作为完整结果发布，清空待发布缓冲并结束当前任务。`edge/boards/esp32/src/device_speech.rs:344`
16. 解配：edge_unpair 对每个已配对对端调用 `removePairedPeer`。`edge/boards/esp32/src/main.rs:516`

## 来源

- `edge/boards/esp32/README.md`：固件说明文档，全文 685 行，基线 AAswordman/Operit2 @ 364d1d594，2026-11-11 全文读完。
- `edge/boards/esp32/src/main.rs`：固件入口与主循环，全文 745 行。
- `edge/boards/esp32/src/runtime_host.rs`：NVS 存储后端与 mDNS 通告，全文 208 行。
- `edge/boards/esp32/src/wifi.rs`：Station 连接与设置 AP，全文 167 行。
- `edge/boards/esp32/src/device_services.rs`：原生设备服务分发，全文 74 行。
- `edge/boards/esp32/src/device_preferences.rs`：设备 preference 配置编辑端点，全文 67 行。
- `edge/boards/esp32/src/device_http.rs`：有界 HTTP 流传输，全文 200 行。
- `edge/boards/esp32/src/device_speech.rs`：语音卸载协议，全文 656 行。
- `edge/boards/esp32/src/space_work.rs`：本地 Space 工作信号量，全文 17 行。
- 范围说明：标有“README 记录/规定”的断言只以 README 文档为据，未在 seed 代码中逐行验证；其中 24 键与 6144 字节上限在 seed 文件内的 device_preferences.rs 中无对应常量，只以 README 为据；2026-10-28 的堆峰值、镜像体积与测试通过数是 README 记录的当次验证结果，不是本次写作的实测。
- 本页无全仓零命中类断言，无需写核验方法。
- 未读文件：除上述 9 个 seed 文件外，edge/boards/esp32/src/ 下其余 .rs 文件（如 edge_chat.rs、standalone_chat.rs、audio.rs、settings.rs）不在本页 seed 范围内，未读未引；独立聊天与远端聊天的完整实现细节见 [[edge-esp32-chat|ESP32 聊天实现]]。
