---
title: 能力 × 平台矩阵
module: hosts
platforms: [android, ios, linux, macos, ohos, web, windows]
sources:
  - core/crates/foundation/host-contract/src/lib.rs
  - core/crates/foundation/host-contract/src/UiAutomation.rs
  - core/crates/foundation/host-api/src/HostManager.rs
  - core/crates/foundation/host-contract/README.md
  - hosts/android/src/lib.rs
  - hosts/apple/src/lib.rs
  - hosts/ios/src/lib.rs
  - hosts/linux/src/lib.rs
  - hosts/macos/src/lib.rs
  - hosts/ohos/src/lib.rs
  - hosts/web/src/lib.rs
  - hosts/windows/src/lib.rs
  - hosts/ohos/README.md
  - hosts/web/README.md
  - hosts/ios/README.md
  - hosts/README.md
  - docs/permission-access-architecture.md
  - docs/filesystem-access-boundary.md
  - docs/core-node-space-binding-architecture.md
date: 2026-11-11
---

## 概述

本页是 Operit2 能力 × 平台矩阵：能力全集取自 host-contract 的 trait 定义，平台列取自各平台 createRuntimeHostManager 的注册实测 (core/crates/foundation/host-api/src/HostManager.rs:139)。
能力全集的唯一权威来源是 host-contract 的 trait 定义与 HostManager 的注册槽位，库里不存在统一的 Host 能力清单数据文件 (core/crates/foundation/host-api/src/HostManager.rs:139)。
矩阵共 35 个能力 × 7 个平台 = 245 格：支持 140、部分支持 15、不支持 1、未查到 89，数字是生成脚本的输出(/tmp/gen_host_matrix.py)。
平台列共 7 列，由生成脚本按 hosts 下含 createRuntimeHostManager 的目录确定(/tmp/gen_host_matrix.py)。
hosts/apple 不占平台列：iOS 把 AppleFileSystemHost 重导出为 IosFileSystemHost (hosts/ios/src/lib.rs:22)。
macOS 把 AppleFileSystemHost 重导出为 MacosFileSystemHost (hosts/macos/src/lib.rs:23)。
未查到不等于不支持：Host 能力可由 Flutter native bridge、CLI 等产品方注册，不只由 hosts 内 lib.rs 注册 (hosts/README.md:38)。
各平台实现细节见 [[host-android|Android Host]]、[[host-ios|iOS Host]]、[[host-linux|Linux Host]]、[[host-apple|macOS Host]]、[[host-ohos|OpenHarmony Host]]、[[host-web|Web Host]]、[[host-windows|Windows Host]]。

## AI 速览

- `ArchiveStagingHost` — 归档暂存，8 个方法 (core/crates/foundation/host-contract/src/lib.rs:2256)
- `AudioPlaybackHost` — 音频播放，9 个方法 (core/crates/foundation/host-contract/src/lib.rs:2936)
- `BluetoothHost` — 蓝牙设备操作，20 个方法 (core/crates/foundation/host-contract/src/lib.rs:3131)
- `BrowserAutomationHost` — 浏览器自动化工具调用，1 个方法 (core/crates/foundation/host-contract/src/lib.rs:1121)
- `BrowserSessionHost` — 交互式浏览器会话，6 个方法 (core/crates/foundation/host-contract/src/lib.rs:1174)
- `ClipboardHost` — 系统剪贴板写，1 个方法 (core/crates/foundation/host-contract/src/lib.rs:3417)
- `ComposeDslWebViewHost` — Compose DSL WebView 渲染，3 个方法 (core/crates/foundation/host-contract/src/lib.rs:1352)
- `DeviceIoHost` — 板级数字 IO，2 个方法 (core/crates/foundation/host-contract/src/lib.rs:3214)
- `FileSystemHost` — 文件读写、目录、查找与压缩，24 个方法 (core/crates/foundation/host-contract/src/lib.rs:3598)
- `FloatingWindowHost` — 悬浮窗命令，1 个方法 (core/crates/foundation/host-contract/src/lib.rs:3444)
- `HostJavaScriptRuntimeHost` — JS 运行时与仿射状态执行，6 个方法 (core/crates/foundation/host-contract/src/lib.rs:2652)
- `HostRuntimeEventHost` — 运行时事件桥接，1 个方法 (core/crates/foundation/host-contract/src/lib.rs:2408)
- `HostRuntimeEventSchedulerHost` — 定时与周期调度，1 个方法 (core/crates/foundation/host-contract/src/lib.rs:2440)
- `HostRuntimeTaskSchedulerHost` — 一次性运行时任务调度，8 个方法 (core/crates/foundation/host-contract/src/lib.rs:2695)
- `HostSecretStore` — 密钥存储，3 个方法 (core/crates/foundation/host-contract/src/lib.rs:2282)
- `HttpHost` — HTTP 请求与批量下载，5 个方法，另继承 `HttpStreamHost` 的 3 个方法 (core/crates/foundation/host-contract/src/lib.rs:1625)
- `HttpServerHost` — HTTP 服务器绑定与连接服务，4 个方法 (core/crates/foundation/host-contract/src/HttpServer.rs:57)
- `LocalInferenceHost` — 本地模型推理，6 个方法 (core/crates/foundation/host-contract/src/lib.rs:3359)
- `ManagedRuntimeHost` — 托管运行时进程，9 个方法 (core/crates/foundation/host-contract/src/lib.rs:1749)
- `PluginSdkIpcHost` — 插件 SDK IPC 接入，6 个方法 (core/crates/foundation/host-contract/src/PluginSdkIpc.rs:58)
- `RobotFaceHost` — 机器人表情渲染，2 个方法 (core/crates/foundation/host-contract/src/lib.rs:3238)
- `RuntimeSqliteHost` — SQLite 连接，2 个方法 (core/crates/foundation/host-contract/src/lib.rs:2400)
- `RuntimeStorageHost` — 运行时存储读写，19 个方法 (core/crates/foundation/host-contract/src/lib.rs:2078)
- `RuntimeStorageWriteHost` — 运行时存储顺序写，1 个方法 (core/crates/foundation/host-contract/src/lib.rs:2250)
- `SerialPortHost` — 串口设备打开与字节流，2 个方法 (core/crates/foundation/host-contract/src/SerialPort.rs:19)
- `ServiceDiscoveryHost` — 服务发现与广播，5 个方法 (core/crates/foundation/host-contract/src/ServiceDiscovery.rs:31)
- `SystemOperationHost` — 系统操作，21 个方法 (core/crates/foundation/host-contract/src/lib.rs:3515)
- `TcpHost` — TCP 连接与监听，2 个方法 (core/crates/foundation/host-contract/src/Tcp.rs:26)
- `TerminalHost` — 终端会话与命令执行，30 个方法 (core/crates/foundation/host-contract/src/lib.rs:1909)
- `ToastHost` — 前端 transient 提示，1 个方法 (core/crates/foundation/host-contract/src/lib.rs:3412)
- `TtsPlaybackHost` — TTS 播放，8 个方法 (core/crates/foundation/host-contract/src/lib.rs:3292)
- `TtsSynthesisHost` — TTS 合成，2 个方法 (core/crates/foundation/host-contract/src/lib.rs:3264)
- `UiAutomationHost` — 无障碍采集与输入，3 个方法 (core/crates/foundation/host-contract/src/UiAutomation.rs:100)
- `WebSocketHost` — WebSocket 连接，4 个方法 (core/crates/foundation/host-contract/src/lib.rs:1593)
- `WebVisitHost` — 网页访问，1 个方法 (core/crates/foundation/host-contract/src/lib.rs:1105)
- Android 的 `createRuntimeHostManager` 是平台入口 (hosts/android/src/lib.rs:76)
- iOS 的 `createRuntimeHostManager` 是平台入口 (hosts/ios/src/lib.rs:41)
- Linux 的 `createRuntimeHostManager` 是平台入口 (hosts/linux/src/lib.rs:54)
- macOS 的 `createRuntimeHostManager` 是平台入口 (hosts/macos/src/lib.rs:46)
- OpenHarmony 的 `createRuntimeHostManager` 是平台入口 (hosts/ohos/src/lib.rs:43)
- Web 的 `createRuntimeHostManager` 是平台入口 (hosts/web/src/lib.rs:36)
- Windows 的 `createRuntimeHostManager` 是平台入口 (hosts/windows/src/lib.rs:36)
- 数据流向：平台方组装 HostManager → Core 经 HostManager 字段取 trait 对象调用平台实现 (core/crates/foundation/host-api/src/HostManager.rs:139)
- 槽位未注册时取用方报错：未注册 HTTP server 时 defaultHttpServerHost 返回明确错误 (core/crates/foundation/host-api/src/HostManager.rs:22)

## 核心机制

### 能力全集从哪来

host-contract 的 src 下共定义 53 个 pub trait，数字是生成脚本的枚举输出(/tmp/gen_host_matrix.py)。
其中 35 个在 HostManager 有注册槽位，是矩阵的能力行 (core/crates/foundation/host-api/src/HostManager.rs:139)。
其余 18 个是辅助 trait，无独立注册槽位，逐项列出如下。
`DiscoveryAdvertisement` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/ServiceDiscovery.rs:23)。
`DiscoverySubscription` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/ServiceDiscovery.rs:21)。
`FileAppendHandle` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:3591)。
`FileSource` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/FileSystemResource.rs:9)。
`FileTarget` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/FileSystemResource.rs:23)。
`HostJavaScriptInterruptController` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/JavaScriptExecutionInterrupt.rs:146)。
`HostJavaScriptRuntime` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:2519)。
`HostRuntimeEventRegistration` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:2406)。
`HttpServerListener` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/HttpServer.rs:51)。
`HttpStreamHost` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:1674)。
`ManagedRuntimeProcess` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:1734)。
`RuntimeSqliteConnection` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:2365)。
`RuntimeSqliteTransaction` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:2382)。
`RuntimeStorageWriteSession` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:2227)。
`SerialPortConnection` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/SerialPort.rs:7)。
`ServerWebSocket` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/HttpServer.rs:30)。
`TcpConnection` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/Tcp.rs:7)。
`TcpListener` 是辅助 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/Tcp.rs:19)。
`HttpHost` 继承 `HttpStreamHost`，本 trait 5 个方法之外另继承 3 个流方法 (core/crates/foundation/host-contract/src/lib.rs:1625)。
`HttpStreamHost` 是 `HttpHost` 的父 trait，无独立注册槽位 (core/crates/foundation/host-contract/src/lib.rs:1625)。

### 判定标准

支持指 create 函数内以平台实现注册，如 Linux 以 LinuxAudioPlaybackHost 注册 AudioPlaybackHost (hosts/linux/src/lib.rs:86)。
部分支持(调用方提供)指注册位由调用方传入的 `Arc<dyn Trait>` 参数填充，如 Linux 的 WebVisitHost 由调用方提供 (hosts/linux/src/lib.rs:57)。
部分支持(依赖调用方回调)指注册的实现由调用方传入的回调构造，如 OHOS 的 SystemOperationHost 依赖调用方回调 (hosts/ohos/src/lib.rs:65)。
部分支持(仅标准版)指只在 Android 标准版注册，特权版无此注册，如 Android 的 LocalInferenceHost (hosts/android/src/lib.rs:95)。
部分支持(已注册但行为受限)指 iOS 的 SerialPortHost 已注册，但 open 一律返回错误，提示无串口配件提供方 (hosts/ios/src/serial.rs:11)。
不支持指源码或 README 明确写不支持，本批唯一一例是 OHOS 的 TtsSynthesisHost (hosts/ohos/README.md:29)。
未查到指取数范围内无注册。
未查到不等于不支持：Host 能力可由 Flutter native bridge、CLI 等产品方注册 (hosts/README.md:38)。
取数范围是各平台 lib.rs 内的 createRuntimeHostManager，以 Android 入口为例 (hosts/android/src/lib.rs:76)。
Android 另有特权版 createPrivilegedRuntimeHostManager (hosts/android/src/lib.rs:107)。
两个 Android 版本共用 createBaseRuntimeHostManager (hosts/android/src/lib.rs:131)。
复合构造器一次填充多个槽位，如 withFileSystemWebVisitSystemOperationAndManagedRuntimeHosts 一次填充七个槽位 (core/crates/foundation/host-api/src/HostManager.rs:392)。
注册缺失的后果：未注册 HTTP server 时 defaultHttpServerHost 返回明确错误 (core/crates/foundation/host-api/src/HostManager.rs:22)。
未注册 TCP 时 defaultTcpHost 返回明确错误 (core/crates/foundation/host-api/src/HostManager.rs:32)。
defaultHttpHost 未配置时以 expect 报错 (core/crates/foundation/host-api/src/HostManager.rs:88)。
本次矩阵由写手一次性脚本生成，源码中无自动定期生成机制；全库 grep 未发现能力矩阵生成脚本(/tmp/gen_host_matrix.py)。
重新生成：任一 `hosts/<平台>/src/lib.rs` 或 host-contract trait 定义变动后，重跑生成脚本再核对本页 (/tmp/gen_host_matrix.py)。
RuntimeSqliteHost 等格的注册行只含 camelCase 字段名(如 runtimeSqliteHost)，facts.json 用字段形式措辞，矩阵表首列能力名因同一原因用 plain 文本(/tmp/gen_host_matrix.py)。

### 矩阵

分平台统计(顺序为支持/部分支持/不支持/未查到)：Android 15/5/0/15、iOS 17/3/0/15、Linux 25/1/0/9、macOS 21/1/0/13、OpenHarmony 14/4/1/16、Web 23/0/0/12、Windows 25/1/0/9(/tmp/gen_host_matrix.py)。

| 能力 | Android | iOS | Linux | macOS | OpenHarmony | Web | Windows |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ArchiveStagingHost | 支持 (hosts/android/src/lib.rs:165) | 支持 (hosts/ios/src/lib.rs:72) | 支持 (hosts/linux/src/lib.rs:84) | 支持 (hosts/macos/src/lib.rs:76) | 支持 (hosts/ohos/src/lib.rs:86) | 支持 (hosts/web/src/lib.rs:56) | 支持 (hosts/windows/src/lib.rs:67) |
| AudioPlaybackHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:2936) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:2936) | 支持 (hosts/linux/src/lib.rs:86) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:2936) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:2936) | 支持 (hosts/web/src/lib.rs:60) | 支持 (hosts/windows/src/lib.rs:69) |
| BluetoothHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3131) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3131) | 支持 (hosts/linux/src/lib.rs:87) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3131) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3131) | 支持 (hosts/web/src/lib.rs:61) | 支持 (hosts/windows/src/lib.rs:70) |
| BrowserAutomationHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1121) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1121) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1121) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1121) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1121) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1121) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1121) |
| BrowserSessionHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1174) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1174) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1174) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1174) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1174) | 支持 (hosts/web/src/lib.rs:57) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1174) |
| ClipboardHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3417) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3417) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3417) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3417) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3417) | 支持(与 SystemOperationHost 共用同一实现) (hosts/web/src/lib.rs:53) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3417) |
| ComposeDslWebViewHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1352) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1352) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1352) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1352) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1352) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1352) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1352) |
| DeviceIoHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3214) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3214) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3214) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3214) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3214) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3214) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3214) |
| FileSystemHost | 支持 (hosts/android/src/lib.rs:153) | 支持 (hosts/ios/src/lib.rs:58) | 支持 (hosts/linux/src/lib.rs:67) | 支持 (hosts/macos/src/lib.rs:59) | 部分支持(依赖调用方回调) (hosts/ohos/src/lib.rs:72) | 支持 (hosts/web/src/lib.rs:44) | 支持 (hosts/windows/src/lib.rs:49) |
| FloatingWindowHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3444) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3444) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3444) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3444) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3444) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3444) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3444) |
| HostJavaScriptRuntimeHost | 支持 (hosts/android/src/lib.rs:167) | 支持 (hosts/ios/src/lib.rs:77) | 支持 (hosts/linux/src/lib.rs:92) | 支持 (hosts/macos/src/lib.rs:80) | 支持 (hosts/ohos/src/lib.rs:91) | 支持 (hosts/web/src/lib.rs:68) | 支持 (hosts/windows/src/lib.rs:76) |
| HostRuntimeEventHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:2408) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:2408) | 支持 (hosts/linux/src/lib.rs:90) | 支持 (hosts/macos/src/lib.rs:78) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:2408) | 支持 (hosts/web/src/lib.rs:69) | 支持 (hosts/windows/src/lib.rs:73) |
| HostRuntimeEventSchedulerHost | 支持 (hosts/android/src/lib.rs:96) | 支持 (hosts/ios/src/lib.rs:75) | 支持 (hosts/linux/src/lib.rs:91) | 支持 (hosts/macos/src/lib.rs:79) | 支持 (hosts/ohos/src/lib.rs:90) | 支持 (hosts/web/src/lib.rs:65) | 支持 (hosts/windows/src/lib.rs:74) |
| HostRuntimeTaskSchedulerHost | 支持 (hosts/android/src/lib.rs:168) | 支持 (hosts/ios/src/lib.rs:79) | 支持 (hosts/linux/src/lib.rs:94) | 支持 (hosts/macos/src/lib.rs:82) | 支持 (hosts/ohos/src/lib.rs:94) | 支持 (hosts/web/src/lib.rs:67) | 支持 (hosts/windows/src/lib.rs:78) |
| HostSecretStore | 支持 (hosts/android/src/lib.rs:94) | 支持 (hosts/ios/src/lib.rs:71) | 支持 (hosts/linux/src/lib.rs:79) | 支持 (hosts/macos/src/lib.rs:71) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:2282) | 支持 (hosts/web/src/lib.rs:54) | 支持 (hosts/windows/src/lib.rs:62) |
| HttpHost | 支持 (hosts/android/src/lib.rs:155) | 支持 (hosts/ios/src/lib.rs:62) | 支持 (hosts/linux/src/lib.rs:69) | 支持 (hosts/macos/src/lib.rs:61) | 支持 (hosts/ohos/src/lib.rs:78) | 支持 (hosts/web/src/lib.rs:46) | 支持 (hosts/windows/src/lib.rs:51) |
| HttpServerHost | 支持 (hosts/android/src/lib.rs:162) | 支持 (hosts/ios/src/lib.rs:63) | 支持 (hosts/linux/src/lib.rs:81) | 支持 (hosts/macos/src/lib.rs:73) | 支持 (hosts/ohos/src/lib.rs:79) | 未查到 (core/crates/foundation/host-contract/src/HttpServer.rs:57) | 支持 (hosts/windows/src/lib.rs:64) |
| LocalInferenceHost | 部分支持(仅标准版注册，特权版无此注册) (hosts/android/src/lib.rs:95) | 支持 (hosts/ios/src/lib.rs:70) | 支持 (hosts/linux/src/lib.rs:75) | 支持 (hosts/macos/src/lib.rs:67) | 支持 (hosts/ohos/src/lib.rs:88) | 支持 (hosts/web/src/lib.rs:62) | 支持 (hosts/windows/src/lib.rs:57) |
| ManagedRuntimeHost | 支持 (hosts/android/src/lib.rs:157) | 部分支持(调用方提供) (hosts/ios/src/lib.rs:45) | 支持 (hosts/linux/src/lib.rs:71) | 支持 (hosts/macos/src/lib.rs:63) | 部分支持(调用方提供) (hosts/ohos/src/lib.rs:53) | 支持 (hosts/web/src/lib.rs:48) | 支持 (hosts/windows/src/lib.rs:53) |
| PluginSdkIpcHost | 部分支持(仅标准版注册，特权版无此注册) (hosts/android/src/lib.rs:102) | 支持 (hosts/ios/src/lib.rs:80) | 支持 (hosts/linux/src/lib.rs:95) | 支持 (hosts/macos/src/lib.rs:83) | 未查到 (core/crates/foundation/host-contract/src/PluginSdkIpc.rs:58) | 未查到 (core/crates/foundation/host-contract/src/PluginSdkIpc.rs:58) | 支持 (hosts/windows/src/lib.rs:75) |
| RobotFaceHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3238) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3238) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3238) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3238) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3238) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3238) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3238) |
| RuntimeSqliteHost | 支持 (hosts/android/src/lib.rs:159) | 支持 (hosts/ios/src/lib.rs:69) | 支持 (hosts/linux/src/lib.rs:73) | 支持 (hosts/macos/src/lib.rs:65) | 支持 (hosts/ohos/src/lib.rs:85) | 支持 (hosts/web/src/lib.rs:50) | 支持 (hosts/windows/src/lib.rs:55) |
| RuntimeStorageHost | 支持 (hosts/android/src/lib.rs:144) | 支持 (hosts/ios/src/lib.rs:48) | 支持 (hosts/linux/src/lib.rs:62) | 支持 (hosts/macos/src/lib.rs:54) | 支持 (hosts/ohos/src/lib.rs:63) | 支持 (hosts/web/src/lib.rs:37) | 支持 (hosts/windows/src/lib.rs:44) |
| RuntimeStorageWriteHost | 支持 (hosts/android/src/lib.rs:166) | 支持 (hosts/ios/src/lib.rs:73) | 支持 (hosts/linux/src/lib.rs:85) | 支持 (hosts/macos/src/lib.rs:77) | 支持 (hosts/ohos/src/lib.rs:87) | 支持 (hosts/web/src/lib.rs:55) | 支持 (hosts/windows/src/lib.rs:68) |
| SerialPortHost | 支持 (hosts/android/src/lib.rs:164) | 部分支持(已注册，open 一律报错、无原生配件提供方) (hosts/ios/src/serial.rs:11) | 支持 (hosts/linux/src/lib.rs:83) | 支持 (hosts/macos/src/lib.rs:75) | 支持 (hosts/ohos/src/lib.rs:81) | 未查到 (core/crates/foundation/host-contract/src/SerialPort.rs:19) | 支持 (hosts/windows/src/lib.rs:66) |
| ServiceDiscoveryHost | 部分支持(仅标准版注册，特权版无此注册) (hosts/android/src/lib.rs:97) | 支持 (hosts/ios/src/lib.rs:78) | 支持 (hosts/linux/src/lib.rs:93) | 支持 (hosts/macos/src/lib.rs:81) | 支持 (hosts/ohos/src/lib.rs:93) | 未查到 (core/crates/foundation/host-contract/src/ServiceDiscovery.rs:31) | 支持 (hosts/windows/src/lib.rs:77) |
| SystemOperationHost | 部分支持(调用方提供) (hosts/android/src/lib.rs:136) | 支持 (hosts/ios/src/lib.rs:60) | 支持 (hosts/linux/src/lib.rs:70) | 支持 (hosts/macos/src/lib.rs:62) | 部分支持(依赖调用方回调) (hosts/ohos/src/lib.rs:65) | 支持(与 SystemOperationHost 共用同一实现) (hosts/web/src/lib.rs:47) | 支持 (hosts/windows/src/lib.rs:52) |
| TcpHost | 支持 (hosts/android/src/lib.rs:163) | 支持 (hosts/ios/src/lib.rs:64) | 支持 (hosts/linux/src/lib.rs:82) | 支持 (hosts/macos/src/lib.rs:74) | 支持 (hosts/ohos/src/lib.rs:80) | 未查到 (core/crates/foundation/host-contract/src/Tcp.rs:26) | 支持 (hosts/windows/src/lib.rs:65) |
| TerminalHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1909) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1909) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1909) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1909) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1909) | 支持 (hosts/web/src/lib.rs:59) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:1909) |
| ToastHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3412) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3412) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3412) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3412) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3412) | 支持(与 SystemOperationHost 共用同一实现) (hosts/web/src/lib.rs:52) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3412) |
| TtsPlaybackHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3292) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3292) | 支持 (hosts/linux/src/lib.rs:89) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3292) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3292) | 支持 (hosts/web/src/lib.rs:63) | 支持 (hosts/windows/src/lib.rs:72) |
| TtsSynthesisHost | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3264) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3264) | 支持 (hosts/linux/src/lib.rs:88) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3264) | 不支持(API 18 SDK 无公开系统语音合成接口，不提供 SYSTEM_TTS) (hosts/ohos/README.md:29) | 未查到 (core/crates/foundation/host-contract/src/lib.rs:3264) | 支持 (hosts/windows/src/lib.rs:71) |
| UiAutomationHost | 未查到 (core/crates/foundation/host-contract/src/UiAutomation.rs:100) | 未查到 (core/crates/foundation/host-contract/src/UiAutomation.rs:100) | 支持 (hosts/linux/src/lib.rs:76) | 支持 (hosts/macos/src/lib.rs:68) | 未查到 (core/crates/foundation/host-contract/src/UiAutomation.rs:100) | 未查到 (core/crates/foundation/host-contract/src/UiAutomation.rs:100) | 支持 (hosts/windows/src/lib.rs:58) |
| WebSocketHost | 支持 (hosts/android/src/lib.rs:161) | 支持 (hosts/ios/src/lib.rs:66) | 支持 (hosts/linux/src/lib.rs:80) | 支持 (hosts/macos/src/lib.rs:72) | 支持 (hosts/ohos/src/lib.rs:82) | 支持 (hosts/web/src/lib.rs:58) | 支持 (hosts/windows/src/lib.rs:63) |
| WebVisitHost | 部分支持(调用方提供) (hosts/android/src/lib.rs:135) | 部分支持(调用方提供) (hosts/ios/src/lib.rs:44) | 部分支持(调用方提供) (hosts/linux/src/lib.rs:57) | 部分支持(调用方提供) (hosts/macos/src/lib.rs:49) | 部分支持(调用方提供) (hosts/ohos/src/lib.rs:46) | 支持 (hosts/web/src/lib.rs:45) | 部分支持(调用方提供) (hosts/windows/src/lib.rs:39) |

注 1：OHOS 的 TtsSynthesisHost 判为不支持，不只是未查到：API 18 SDK 无公开系统语音合成接口，OHOS 不提供 `SYSTEM_TTS` (hosts/ohos/README.md:29)。

### 已知明确的不支持与 README 差异

明确不支持只有一例：OHOS 的 TtsSynthesisHost，OHOS 不提供 `SYSTEM_TTS`，API 18 SDK 无公开系统语音合成接口 (hosts/ohos/README.md:29)。
iOS Host 报告当前未安装原生串口配件提供方 (hosts/ios/README.md:32)。
iOS 的 SerialPortHost 的 open 一律返回错误，提示无串口配件提供方 (hosts/ios/src/serial.rs:11)。
hosts/web/README.md 称 web 为 host-api 的每个 trait 提供实现 (hosts/web/README.md:3)。
注册实测与该声明不一致：Web 的 createRuntimeHostManager 注册中未查到 HttpServerHost (core/crates/foundation/host-contract/src/HttpServer.rs:57)。
Web 的 createRuntimeHostManager 注册中未查到 TcpHost (core/crates/foundation/host-contract/src/Tcp.rs:26)。
Web 的 createRuntimeHostManager 注册中未查到 SerialPortHost (core/crates/foundation/host-contract/src/SerialPort.rs:19)。
Web 的 createRuntimeHostManager 注册中未查到 ServiceDiscoveryHost (core/crates/foundation/host-contract/src/ServiceDiscovery.rs:31)。
Web 的 createRuntimeHostManager 注册中未查到 PluginSdkIpcHost (core/crates/foundation/host-contract/src/PluginSdkIpc.rs:58)。
Web 的 createRuntimeHostManager 注册中未查到 TtsSynthesisHost (core/crates/foundation/host-contract/src/lib.rs:3264)。
Web 的 createRuntimeHostManager 注册中未查到 BrowserAutomationHost (core/crates/foundation/host-contract/src/lib.rs:1121)。
Web 的 createRuntimeHostManager 注册中未查到 FloatingWindowHost (core/crates/foundation/host-contract/src/lib.rs:3444)。
Web 的 createRuntimeHostManager 注册中未查到 ComposeDslWebViewHost (core/crates/foundation/host-contract/src/lib.rs:1352)。
Web 的 createRuntimeHostManager 注册中未查到 DeviceIoHost (core/crates/foundation/host-contract/src/lib.rs:3214)。
Web 的 createRuntimeHostManager 注册中未查到 RobotFaceHost (core/crates/foundation/host-contract/src/lib.rs:3238)。
本页格子以注册实测为准，README 声明只作对照。
OHOS README 的能力清单列出 PTY sessions (hosts/ohos/README.md:13)。
OpenHarmony 的 createRuntimeHostManager 注册中未查到 TerminalHost (core/crates/foundation/host-contract/src/lib.rs:1909)。
OHOS README 的能力清单列出 ArkTS AVPlayer 生成的 TTS 播放控制 (hosts/ohos/README.md:18)。
OpenHarmony 的 createRuntimeHostManager 注册中未查到 TtsPlaybackHost (core/crates/foundation/host-contract/src/lib.rs:3292)。
这两项的缺失只针对本页取数范围；Host 能力也可由产品方注册 (hosts/README.md:38)。
iOS README 称 Flutter Runner 的终端通过 Rust 桥接调用 Arm64TerminalBridge.mm (hosts/ios/README.md:5)。
iOS 的 createRuntimeHostManager 注册中未查到 TerminalHost (core/crates/foundation/host-contract/src/lib.rs:1909)。
hosts/README.md 的目录表列出 hosts/boards 与 hosts/server (hosts/README.md:19)，但基线 hosts/ 下无这两个目录，引用时按过时项处理。
Web 的 terminal 经 v86 启动浏览器本地 Buildroot Linux 客户机 (hosts/web/README.md:68)。
Web 的 localInference 执行已安装的 Sherpa ONNX Web STT 与 TTS 包 (hosts/web/README.md:77)。

## 关键符号

- `HostManager` — 宿主能力注册表，字段是 Option 包装的 trait 对象槽位 (core/crates/foundation/host-api/src/HostManager.rs:139)
- `HostEnvironmentDescriptor` — 平台环境描述符 (core/crates/foundation/host-contract/src/lib.rs:99)
- `HostCapability` — 能力声明，含 id、displayName、scope 与 operations (core/crates/foundation/host-contract/src/lib.rs:528)
- `CapabilityScope` — 能力范围枚举 (core/crates/foundation/host-contract/src/lib.rs:510)
- `CapabilityOperation` — 能力操作枚举 (core/crates/foundation/host-contract/src/lib.rs:520)
- `withFileSystemWebVisitSystemOperationAndManagedRuntimeHosts` — 一次填充七个槽位的复合构造器 (core/crates/foundation/host-api/src/HostManager.rs:392)
- `withFileSystemWebVisitAndSystemOperationHosts` — 填充文件系统、Web 访问与系统操作三个槽位 (core/crates/foundation/host-api/src/HostManager.rs:336)
- `withFileSystemAndWebVisitHosts` — 填充文件系统与 Web 访问两个槽位 (core/crates/foundation/host-api/src/HostManager.rs:288)
- Android 的 `createRuntimeHostManager` 是平台入口 (hosts/android/src/lib.rs:76)
- Android 的 `createPrivilegedRuntimeHostManager` 是特权版入口 (hosts/android/src/lib.rs:107)
- Android 的 `createBaseRuntimeHostManager` 是两版本共用的组装函数 (hosts/android/src/lib.rs:131)
- iOS 的 `createRuntimeHostManager` 是平台入口 (hosts/ios/src/lib.rs:41)
- Linux 的 `createRuntimeHostManager` 是平台入口 (hosts/linux/src/lib.rs:54)
- macOS 的 `createRuntimeHostManager` 是平台入口 (hosts/macos/src/lib.rs:46)
- OpenHarmony 的 `createRuntimeHostManager` 是平台入口 (hosts/ohos/src/lib.rs:43)
- Web 的 `createRuntimeHostManager` 是平台入口 (hosts/web/src/lib.rs:36)
- Windows 的 `createRuntimeHostManager` 是平台入口 (hosts/windows/src/lib.rs:36)

## 调用链

1. 平台方调用本平台的 `createRuntimeHostManager`，传入运行时根与工作区根 (hosts/android/src/lib.rs:76)
2. create 函数经复合构造器或单个 with 调用填充 HostManager 槽位，如 `withFileSystemWebVisitSystemOperationAndManagedRuntimeHosts` 一次填充七个槽位 (core/crates/foundation/host-api/src/HostManager.rs:392)
3. Core 经 `HostManager` 字段取 trait 对象调用平台实现；文件系统、终端、浏览器、HTTP 和平台交互都来自该节点自己的 `HostManager` (docs/core-node-space-binding-architecture.md:51)
4. 槽位未注册时取用方报错：未注册 HTTP server 时 `defaultHttpServerHost` 返回明确错误 (core/crates/foundation/host-api/src/HostManager.rs:22)
5. 业务文件操作不直接调 `FileSystemHost`，先经 `VisualFileSystem` 解析路径 (docs/filesystem-access-boundary.md:3)
6. 权限检查在 Host 侧收口：Host 决定实际可用的系统能力，runtime 与用户批准都不能提升 Host 权限 (docs/permission-access-architecture.md:8)

## 来源

- core/crates/foundation/host-contract/src/lib.rs
- core/crates/foundation/host-api/src/HostManager.rs
- core/crates/foundation/host-contract/README.md
- core/crates/foundation/host-contract/src/HttpServer.rs
- core/crates/foundation/host-contract/src/PluginSdkIpc.rs
- core/crates/foundation/host-contract/src/SerialPort.rs
- core/crates/foundation/host-contract/src/ServiceDiscovery.rs
- core/crates/foundation/host-contract/src/Tcp.rs
- core/crates/foundation/host-contract/src/FileSystemResource.rs
- core/crates/foundation/host-contract/src/UiAutomation.rs
- core/crates/foundation/host-contract/src/JavaScriptExecutionInterrupt.rs
- hosts/android/src/lib.rs
- hosts/apple/src/lib.rs
- hosts/ios/src/lib.rs
- hosts/ios/src/serial.rs
- hosts/linux/src/lib.rs
- hosts/macos/src/lib.rs
- hosts/ohos/src/lib.rs
- hosts/web/src/lib.rs
- hosts/windows/src/lib.rs
- hosts/ohos/README.md
- hosts/web/README.md
- hosts/ios/README.md
- hosts/README.md
- docs/permission-access-architecture.md
- docs/filesystem-access-boundary.md
- docs/core-node-space-binding-architecture.md
- 矩阵生成脚本：/tmp/gen_host_matrix.py(能力 trait 枚举、HostManager 槽位解析、七平台注册解析、矩阵表与 facts 草稿生成)
- facts.json 共 344 条：脚本生成 315 条，人工追加 29 条方法与文档事实
