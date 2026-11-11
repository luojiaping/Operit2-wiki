---
title: Apple Host（macOS 与 iOS 共享实现）
module: hosts
platforms: [macos, ios]
sources: [hosts/apple/Cargo.toml, hosts/apple/src/lib.rs, hosts/apple/src/tools/fs/mod.rs, hosts/apple/src/tools/terminal/mod.rs, hosts/apple/src/tools/terminal/terminal_macos.rs, hosts/apple/src/tools/browser/mod.rs, hosts/apple/src/tools/runtime/mod.rs, hosts/apple/src/tools/storage/mod.rs, hosts/apple/src/tools/system/mod.rs, hosts/apple/src/tools/system/battery.rs, hosts/apple/src/tools/system/packages.rs, hosts/apple/src/tools/local_inference/mod.rs, hosts/apple/src/tools/tts/mod.rs, hosts/apple/src/tools/http/mod.rs, hosts/apple/src/tools/audio/mod.rs, hosts/apple/src/tools/bluetooth/mod.rs, hosts/apple/src/sandbox.rs, hosts/apple/src/service_discovery.rs, hosts/macos/src/lib.rs]
date: 2026-11-11
---

## 概述

Apple Host 的 crate 名为 `operit-host-apple-native`（`hosts/apple/Cargo.toml:2`）。
它是 macOS 与 iOS 共用的 Host 实现层，各能力 Host 由 `tools` 模块组织（`hosts/apple/src/lib.rs:6`）。
文件系统与 HTTP Host 在 macOS 与 iOS 上共用同一导出（`hosts/apple/src/lib.rs:24`）。
浏览器 Host 只在 macOS 下导出（`hosts/apple/src/lib.rs:23`）。
托管运行时 Host 只在 macOS 下导出（`hosts/apple/src/lib.rs:29`）。
沙盒状态由 `processIsolation` 在运行时判定，决定文件与终端的可用范围（`hosts/apple/src/sandbox.rs:6`）。
macOS 壳把 Apple Host 重命名为 Macos* 导出，并以 `createRuntimeHostManager` 组装运行时 Host 管理器（`hosts/macos/src/lib.rs:45`）。
iOS 的本地终端是报错桩，iOS 专属的终端与运行时细节见 [[host-ios|iOS Host 与 ARM64 Linux 运行时]]（`hosts/apple/src/tools/terminal/mod.rs:43`）。

## AI 速览

- `AppleFileSystemHost` — macOS 与 iOS 共用的文件系统 Host（`hosts/apple/src/lib.rs:24`）。
- `AppleTerminalHost` — macOS 的 PTY 终端 Host（`hosts/apple/src/tools/terminal/terminal_macos.rs:14`）。
- `AppleWebVisitHost` — macOS 的 Chromium 网页访问 Host（`hosts/apple/src/lib.rs:23`）。
- `AppleBrowserAutomationHost` — macOS 的 Chromium 浏览器自动化 Host（`hosts/apple/src/lib.rs:23`）。
- `AppleManagedRuntimeHost` — macOS 的托管运行时 Host（`hosts/apple/src/lib.rs:29`）。
- `AppleRuntimeStorageHost` — macOS 与 iOS 共用的运行时存储 Host（`hosts/apple/src/lib.rs:30`）。
- `AppleSystemOperationHost` — macOS 与 iOS 共用的系统操作 Host（`hosts/apple/src/lib.rs:31`）。
- `AppleHttpHost` — macOS 与 iOS 共用的 HTTP 与 WebSocket Host（`hosts/apple/src/lib.rs:26`）。
- `AppleAudioPlaybackHost` — 音频与音乐播放 Host（`hosts/apple/src/tools/audio/mod.rs:22`）。
- `AppleMusicCommand` — 音乐播放命令枚举（`hosts/apple/src/tools/audio/mod.rs:11`）。
- `AppleBluetoothHost` — 经典蓝牙与 BLE Host（`hosts/apple/src/tools/bluetooth/mod.rs:10`）。
- `AppleTtsSynthesisHost` — TTS 合成 Host（`hosts/apple/src/tools/tts/mod.rs:20`）。
- `AppleTtsPlaybackHost` — TTS 播放 Host（`hosts/apple/src/tools/tts/mod.rs:25`）。
- `AppleLocalInferenceHost` — 本地推理 Host（`hosts/apple/src/tools/local_inference/mod.rs:20`）。
- `AppleServiceDiscoveryHost` — Bonjour 服务发现 Host（`hosts/apple/src/service_discovery.rs:136`）。
- 主入口：`createRuntimeHostManager`（`hosts/macos/src/lib.rs:43`）。
- 数据流向：Core 调 `HostManager` 注册的 Host → Host 调系统命令、系统框架或应用方回调 → 结果返回 Core（`hosts/macos/src/lib.rs:55`）。

## 核心机制

### 共享与分工

- 文件系统与 HTTP Host 在 macOS 与 iOS 上共用同一份实现（`hosts/apple/src/lib.rs:24`）。
- 运行时存储与系统操作 Host 同样在两个平台上导出（`hosts/apple/src/lib.rs:30`）。
- 浏览器 Host 只在 macOS 下导出（`hosts/apple/src/lib.rs:23`）。
- 托管运行时 Host 只在 macOS 下导出（`hosts/apple/src/lib.rs:29`）。
- `chromium_browser` 模块只在 macOS 下编译（`hosts/apple/src/lib.rs:5`）。
- 开启 `arm64-runtime` 特性且目标为 macOS aarch64 时，lib.rs 把 iOS 的桥接模块引入复用（`hosts/apple/src/lib.rs:43`）。
- macOS 壳把 `AppleFileSystemHost` 重命名为 `MacosFileSystemHost` 导出（`hosts/macos/src/lib.rs:20`）。

### 沙盒判定与文件能力

- `processIsolation` 在 macOS 上读进程签名判定沙盒状态（`hosts/apple/src/sandbox.rs:6`）。
- 签名查询报告未沙盒时隔离级别为 `HostIsolation::None`（`hosts/apple/src/sandbox.rs:13`）。
- 签名查询失败时隔离级别回落为 `HostIsolation::OsAppSandbox`（`hosts/apple/src/sandbox.rs:15`）。
- 非 macOS 目标上隔离级别直接为 `HostIsolation::OsAppSandbox`（`hosts/apple/src/sandbox.rs:21`）。
- 沙盒判定检查签名授权项 `com.apple.security.app-sandbox`（`hosts/apple/src/sandbox.rs:69`）。
- `validatePath` 要求路径为非空的 Apple 平台绝对路径（`hosts/apple/src/tools/fs/mod.rs:67`）。
- 环境描述符的 `isolation` 取自 `processIsolation`（`hosts/apple/src/tools/fs/mod.rs:548`）。
- 环境描述符的 `privilege` 为 `HostPrivilege::Normal`（`hosts/apple/src/tools/fs/mod.rs:547`）。
- macOS 沙盒下容器外文件需用户选择文件夹授权，子进程仍受沙盒限制（`hosts/apple/src/tools/fs/mod.rs:626`）。
- macOS 非沙盒时 `workspaceRoots` 把物理根 `/` 映射为 VFS 的 `/virtual/macos`（`hosts/apple/src/tools/fs/mod.rs:639`）。
- macOS 下描述符追加 `screen.capture` 能力（`hosts/apple/src/tools/fs/mod.rs:645`）。
- `openFile` 优先调用已注册的 `opener` 回调打开文件（`hosts/apple/src/tools/fs/mod.rs:477`）。
- macOS 上无回调时调用 `open` 命令打开文件（`hosts/apple/src/tools/fs/mod.rs:483`）。
- 非 macOS 且无回调时打开文件报错，提示应用方未注册 Apple file opener（`hosts/apple/src/tools/fs/mod.rs:491`）。
- `shareFile` 在 macOS 上用 open -R 在 Finder 中揭示文件（`hosts/apple/src/tools/fs/mod.rs:503`）。
- iOS 上文件分享报错，要求由 Flutter 方 UI 发起（`hosts/apple/src/tools/fs/mod.rs:515`）。
- 文件查找用 `GlobBuilder` 按 pattern 匹配，并用 `WalkBuilder` 按 `maxDepth` 限制遍历深度（`hosts/apple/src/tools/fs/mod.rs:268`）。
- 代码搜索用 `RegexMatcherBuilder` 编译正则（`hosts/apple/src/tools/fs/mod.rs:348`）。
- 代码搜索以 `BinaryDetection::quit` 在 NUL 字节处停止，并以 `maxResults` 限制匹配数（`hosts/apple/src/tools/fs/mod.rs:359`）。
- 压缩用 `CompressionMethod::Deflated`（`hosts/apple/src/tools/fs/mod.rs:421`）。
- 解压用 `enclosed_name` 校验 zip 条目路径（`hosts/apple/src/tools/fs/mod.rs:457`）。
- 入门要求只有通知一项，`isRequired` 为 `true`，初始状态为 `Missing`（`hosts/apple/src/tools/fs/mod.rs:666`）。
- 能力列表含 `fs.read`、`fs.write`、`fs.search` 与 `fs.archive`（`hosts/apple/src/tools/fs/mod.rs:562`）。
- 能力列表含 `system.notifications.send`、`system.location` 与 `ocr.recognition`（`hosts/apple/src/tools/fs/mod.rs:574`）。
- 能力列表含 `runtime.process`、`runtime.storage` 与 `runtime.sqlite`（`hosts/apple/src/tools/fs/mod.rs:577`）。

### 终端：macOS 真 PTY 与 iOS 桩

- macOS 的 AppleTerminalHost 来自 `terminal_macos.rs`（`hosts/apple/src/tools/terminal/mod.rs:8`）。
- AppleTerminalHost 的 `new` 先以 `processIsolation` 判定进程是否处于 `OsAppSandbox`（`hosts/apple/src/tools/terminal/terminal_macos.rs:32`）。
- 沙盒下只注册一个 bash 适配器，`withControllingTty(false)` 关闭控制终端（`hosts/apple/src/tools/terminal/terminal_macos.rs:38`）。
- 非沙盒下注册 `/bin/bash` 与 `/bin/zsh` 两个登录 shell（`hosts/apple/src/tools/terminal/terminal_macos.rs:42`）。
- 非沙盒下默认 shell 取自 `SHELL` 环境变量，缺省为 `/bin/zsh`（`hosts/apple/src/tools/terminal/terminal_macos.rs:47`）。
- 沙盒下终端类型描述为 macOS sandbox PTY（without controlling TTY）（`hosts/apple/src/tools/terminal/terminal_macos.rs:122`）。
- 非沙盒下终端类型描述为 macOS native 登录 PTY，带作业控制（`hosts/apple/src/tools/terminal/terminal_macos.rs:124`）。
- 只接受 `terminal` 为 native 的请求，否则报 Unsupported macOS terminal 错误（`hosts/apple/src/tools/terminal/terminal_macos.rs:70`）。
- `hostForSession` 按 `ownsSession` 查找会话，未知会话报 Unknown macOS terminal session 错误（`hosts/apple/src/tools/terminal/terminal_macos.rs:83`）。
- `createOrGetSession` 使用 `primary` 解释器创建或复用会话（`hosts/apple/src/tools/terminal/terminal_macos.rs:237`）。
- 开启 `arm64-runtime` 特性时 `terminal` 为 `arm64` 的请求转交给 arm64 终端 Host（`hosts/apple/src/tools/terminal/terminal_macos.rs:101`）。
- 开启 `arm64-runtime` 特性时 `macos-arm64-` 前缀的会话 ID 转交给 arm64 终端 Host（`hosts/apple/src/tools/terminal/terminal_macos.rs:176`）。
- `executeHiddenCommand` 使用 `primary` 解释器执行隐藏命令（`hosts/apple/src/tools/terminal/terminal_macos.rs:308`）。
- iOS 下 `terminalInfo` 返回“iOS does not expose a local PTY host”错误（`hosts/apple/src/tools/terminal/mod.rs:43`）。
- iOS 下 `listSessions` 返回空列表而不报错（`hosts/apple/src/tools/terminal/mod.rs:78`）。

### 系统操作的分平台矩阵

- macOS 上用 `plutil` 读取 `OperitDistributionType`（`hosts/apple/src/tools/system/mod.rs:41`）。
- 更新目标返回 `MacosPkg` 包、`universal` 架构与 `Immediate` 安装时机（`hosts/apple/src/tools/system/mod.rs:56`）。
- 非 macOS 上更新目标返回 `None`（`hosts/apple/src/tools/system/mod.rs:61`）。
- `getSystemLanguageCode` 用 `CFLocaleCopyCurrent` 查询当前区域（`hosts/apple/src/tools/system/mod.rs:70`）。
- 区域标识中的下划线被换成连字符（`hosts/apple/src/tools/system/mod.rs:81`）。
- macOS 上调用 `osascript` 发送通知（`hosts/apple/src/tools/system/mod.rs:100`）。
- iOS 上发送通知报错，要求走应用通知层（`hosts/apple/src/tools/system/mod.rs:118`）。
- macOS 上用 `defaults` 写系统设置（`hosts/apple/src/tools/system/mod.rs:140`）。
- iOS 上修改系统设置报错，系统设置不可写（`hosts/apple/src/tools/system/mod.rs:159`）。
- macOS 上用 `defaults` 读系统设置（`hosts/apple/src/tools/system/mod.rs:178`）。
- iOS 上读取系统设置报错，系统设置不可读（`hosts/apple/src/tools/system/mod.rs:192`）。
- `installApp` 要求 `Immediate` 安装时机（`hosts/apple/src/tools/system/mod.rs:207`）。
- `installApp` 在 macOS 上走 `packages::install`（`hosts/apple/src/tools/system/mod.rs:211`）。
- iOS 上安装应用报错，应用安装对该 Host 不可用（`hosts/apple/src/tools/system/mod.rs:216`）。
- `uninstallApp` 在 macOS 上走 `packages::uninstall`，非 macOS 报错并提示用系统应用设置（`hosts/apple/src/tools/system/mod.rs:229`）。
- `listInstalledApps` 在 macOS 上走 `packages::list`，iOS 上报错称未暴露（`hosts/apple/src/tools/system/mod.rs:237`）。
- `startApp` 在 macOS 上走 `packages::start`（`hosts/apple/src/tools/system/mod.rs:255`）。
- iOS 上启动应用报错，应用启动对该 Host 不可用（`hosts/apple/src/tools/system/mod.rs:259`）。
- `stopApp` 在 macOS 上走 `packages::stop`（`hosts/apple/src/tools/system/mod.rs:273`）。
- iOS 上停止应用报错，应用停止对该 Host 不可用（`hosts/apple/src/tools/system/mod.rs:277`）。
- `getNotifications` 在两个 Apple 平台上都报错，称通知历史不对第三方 Host 暴露（`hosts/apple/src/tools/system/mod.rs:290`）。
- `getAppUsageTime` 要求 `sinceHours` 与 `limit` 大于 0（`hosts/apple/src/tools/system/mod.rs:299`）。
- macOS 上查询应用使用时长报错，称历史前台用量不暴露，Screen Time 需单独授权的集成（`hosts/apple/src/tools/system/mod.rs:310`）。
- 两个 Apple 平台上查询设备定位都报错，要求由 Flutter 方 UI 请求定位（`hosts/apple/src/tools/system/mod.rs:337`）。
- 设备名作 `deviceId`，制造商固定为 Apple（`hosts/apple/src/tools/system/mod.rs:467`）。
- macOS 上以 uname -m 取机型、以 `sw_vers` 取系统版本（`hosts/apple/src/tools/system/mod.rs:448`）。
- iOS 上机型固定为 `ios`、系统版本为空（`hosts/apple/src/tools/system/mod.rs:454`）。
- macOS 上用 screencapture -x 截图到临时路径（`hosts/apple/src/tools/system/mod.rs:349`）。
- iOS 上截图报错，要求由 Flutter 方 UI 请求截图（`hosts/apple/src/tools/system/mod.rs:366`）。
- macOS 上生成 Swift 脚本调用 Vision 的 `VNRecognizeTextRequest` 做 OCR（`hosts/apple/src/tools/system/mod.rs:398`）。
- 语言映射为 Latin 对 `en-US`、Chinese 对 `zh-Hans`、Japanese 对 `ja-JP`、Korean 对 `ko-KR`（`hosts/apple/src/tools/system/mod.rs:388`）。
- iOS 上 OCR 报错，要求由 Flutter 方 UI 请求（`hosts/apple/src/tools/system/mod.rs:431`）。

### 电池与应用包管理（macOS）

- iOS 电池快照只接受 `domain` 为 `host` 且 `platform` 为 `ios` 的事件（`hosts/apple/src/tools/system/battery.rs:8`）。
- 电池事件主题 `system.battery.low` 与 `system.battery.okay` 取 `level` 与 `charging` 字段（`hosts/apple/src/tools/system/battery.rs:13`）。
- 电源事件主题 `system.power.connected` 与 `system.power.disconnected` 取 `batteryLevel` 与 `connected` 字段（`hosts/apple/src/tools/system/battery.rs:13`）。
- 电量只接受 0 到 100 之间的有限值并四舍五入（`hosts/apple/src/tools/system/battery.rs:20`）。
- 电量或充电状态缺失时 `BatterySnapshot` 的 `value` 返回 `(-1, false)`（`hosts/apple/src/tools/system/battery.rs:30`）。
- iOS 上 `observe_ios_event` 把编码后的事件写入 `IOS_BATTERY` 静态快照（`hosts/apple/src/tools/system/battery.rs:42`）。
- macOS 上运行 pmset -g batt 并解析输出（`hosts/apple/src/tools/system/battery.rs:62`）。
- 只认 `charging`、`charged` 与 `finishing charge` 为充电中（`hosts/apple/src/tools/system/battery.rs:89`）。
- 应用列表扫描用户 Applications 与 `/Applications`，含系统应用时追加 `/System/Applications` 与 CoreServices 应用目录（`hosts/apple/src/tools/system/packages.rs:53`）。
- `scan` 遍历深度超过 4 时停止（`hosts/apple/src/tools/system/packages.rs:20`）。
- 遍历用 `plutil` 读取 `CFBundleIdentifier`，读不到时用 bundle 路径作键（`hosts/apple/src/tools/system/packages.rs:31`）。
- `start` 用 open -a 启动解析出的应用路径（`hosts/apple/src/tools/system/packages.rs:92`）。
- `stop` 先查 System Events 中的运行进程，未运行则报错（`hosts/apple/src/tools/system/packages.rs:99`）。
- `uninstall` 拒绝卸载 `/System` 与 `/Library` 下的受保护系统应用（`hosts/apple/src/tools/system/packages.rs:117`）。
- uninstall 拒绝卸载正在运行的 Host 自身（`hosts/apple/src/tools/system/packages.rs:123`）。
- uninstall 通过 Finder 把应用移到废纸篓（`hosts/apple/src/tools/system/packages.rs:127`）。
- install 接受 .app 时用 Finder 的 `duplicate` 复制到 /Applications（`hosts/apple/src/tools/system/packages.rs:159`）。
- install 复制 `.app` 成功后把 `installState` 标记为 `Completed`（`hosts/apple/src/tools/system/packages.rs:169`）。
- install 接受 .pkg、.mpkg 或 .dmg 时打开安装器并标记 `InstallerOpened`（`hosts/apple/src/tools/system/packages.rs:180`）。
- install 拒绝其他类型并列出支持的安装器类型（`hosts/apple/src/tools/system/packages.rs:173`）。

### 托管运行时（macOS 专属）

- 托管运行时 stdio 缓冲区常量 `MANAGED_RUNTIME_STDIO_BUFFER_BYTES` 为 64KB（`hosts/apple/src/tools/runtime/mod.rs:16`）。
- 托管运行时单帧下限常量 `MANAGED_RUNTIME_SINGLE_FRAME_MIN_BYTES` 为 4KB（`hosts/apple/src/tools/runtime/mod.rs:17`）。
- openPath 的 `Reveal` 动作调用 open -R（`hosts/apple/src/tools/runtime/mod.rs:118`）。
- openPath 的 `Terminal` 动作调用 open -a Terminal 打开目标所在目录（`hosts/apple/src/tools/runtime/mod.rs:124`）。
- `runtimeWorkspaceDir` 为 Library/Application Support 下的 Operit2/managed_runtime，并自动建目录（`hosts/apple/src/tools/runtime/mod.rs:141`）。
- Node 解析为 `node`，Python 解析为 `python3` 与 `python`（`hosts/apple/src/tools/runtime/mod.rs:160`）。
- Uv 解析为 `uv`，Pnpm 解析为 `pnpm`（`hosts/apple/src/tools/runtime/mod.rs:162`）。
- 子进程 `stdin`、`stdout` 与 `stderr` 全部接成管道（`hosts/apple/src/tools/runtime/mod.rs:189`）。
- 托管运行时 `stderr` 缓冲超过 400 行时丢弃最旧行（`hosts/apple/src/tools/runtime/mod.rs:222`）。
- 托管运行时 stdout 与 stderr 读取任务以 `managed-runtime-pipes` 为名提交给 `NativeHostRuntimeTaskSchedulerHost`（`hosts/apple/src/tools/runtime/mod.rs:229`）。
- 一次性执行命令并返回 `exitCode`、`stdout` 与 `stderr`（`hosts/apple/src/tools/runtime/mod.rs:258`）。
- 小于 4KB 的协议行直接写并换行，达到 4KB 的行拼成一帧写入（`hosts/apple/src/tools/runtime/mod.rs:269`）。

### 存储与 Keychain

- `AppleRuntimeStorageHost` 内部包装 `NativeRuntimeStorageHost`（`hosts/apple/src/tools/storage/mod.rs:15`）。
- 运行时存储通过 `delegate_runtime_storage` 宏委托给内部 `storage`（`hosts/apple/src/tools/storage/mod.rs:19`）。
- `defaultRuntimeRoot` 为 Library/Application Support 下的 Operit2/runtime（`hosts/apple/src/tools/storage/mod.rs:26`）。
- `defaultWorkspaceRoot` 为 Library/Application Support 下的 Operit2/workspaces（`hosts/apple/src/tools/storage/mod.rs:33`）。
- Keychain 服务名为 `Operit2.HostSecretStore`（`hosts/apple/src/tools/storage/mod.rs:80`）。
- `readSecret` 用 `get_generic_password` 读 Keychain，未找到（错误码 `-25300`）时返回 `None`（`hosts/apple/src/tools/storage/mod.rs:50`）。
- `writeSecret` 用 `set_generic_password` 写 Keychain（`hosts/apple/src/tools/storage/mod.rs:62`）。
- `deleteSecret` 用 `delete_generic_password` 删 Keychain，未找到时同样视为成功（`hosts/apple/src/tools/storage/mod.rs:69`）。
- 密钥只允许 ASCII 字母数字与 `.`、`_`、`-`，空密钥或非法字符报错（`hosts/apple/src/tools/storage/mod.rs:88`）。

### 服务发现：Bonjour

- Apple 服务发现走 Bonjour 守护进程，遵循系统本地网络权限（`hosts/apple/src/service_discovery.rs:1`）。
- `AppleServiceDiscoveryHost` 按服务类型缓存共享 `Browser`（`hosts/apple/src/service_discovery.rs:137`）。
- `serviceKind` 要求服务类型以 `.local.` 结尾（`hosts/apple/src/service_discovery.rs:160`）。
- DNS-SD 错误码 `-65570` 表示本地网络访问被拒绝（`hosts/apple/src/service_discovery.rs:150`）。
- `decodeTxt` 按长度前缀切分 TXT 记录（`hosts/apple/src/service_discovery.rs:179`）。
- TXT 记录条目以 key=value 形式拆分，缺等号时报错（`hosts/apple/src/service_discovery.rs:189`）。
- `encodeTxt` 以单字节长度前缀编码每条 TXT 属性（`hosts/apple/src/service_discovery.rs:200`）。
- 同时解码 IPv4（family 2）与 IPv6（family 30）的 Darwin 地址（`hosts/apple/src/service_discovery.rs:223`）。
- `BrowserState` 的 `snapshot` 在守护进程失败时返回错误而不返回空设备列表（`hosts/apple/src/service_discovery.rs:36`）。
- Worker 启动时以 `recv_timeout` 等待最长 3 秒的操作初始化（`hosts/apple/src/service_discovery.rs:76`）。
- `discover` 要求 `timeoutMs` 为正，超时为 0 时报错（`hosts/apple/src/service_discovery.rs:666`）。
- `discover` 刷新浏览器后等待 `timeoutMs` 再返回快照（`hosts/apple/src/service_discovery.rs:669`）。
- 已有记录通过 `callback(record)` 立即回放给订阅者（`hosts/apple/src/service_discovery.rs:700`）。
- 取消订阅时 `Drop` 实现只移除本次订阅的回调（`hosts/apple/src/service_discovery.rs:124`）。
- `supportsAdvertisement` 返回 `true`（`hosts/apple/src/service_discovery.rs:630`）。
- 调用 `DNSServiceRegister` 向 Bonjour 守护进程注册服务（`hosts/apple/src/service_discovery.rs:583`）。
- `localAddresses` 委托给 `operit_host_native_common` 的 `localNetworkAddresses`（`hosts/apple/src/service_discovery.rs:625`）。

### 浏览器（macOS 专属）

- AppleWebVisitHost 的 `visitWeb` 通过临时 Chromium 会话访问网页（`hosts/apple/src/tools/browser/mod.rs:28`）。
- 浏览器自动化请求由内部 Host 的 `executeBrowserTool` 执行（`hosts/apple/src/tools/browser/mod.rs:56`）。
- 浏览器候选路径优先读 `OPERIT_BROWSER_PATH` 环境变量（`hosts/apple/src/tools/browser/mod.rs:63`）。
- 浏览器候选路径含 Chrome、Chrome Canary、Edge、Brave 与 Chromium 的 macOS 安装路径（`hosts/apple/src/tools/browser/mod.rs:76`）。

### 音频、蓝牙、TTS 与本地推理：回调转交

- `AppleAudioPlaybackHost` 含 `player` 与 `musicPlayer` 两个回调字段（`hosts/apple/src/tools/audio/mod.rs:22`）。
- `AppleAudioPlaybackHost` 由 `fromPlayers` 构造（`hosts/apple/src/tools/audio/mod.rs:27`）。
- `AppleMusicCommand` 含 `Play`、`Pause`、`Resume`、`Stop`、`Seek`、`SetVolume` 与 `Status` 七个变体（`hosts/apple/src/tools/audio/mod.rs:14`）。
- 播放、暂停与恢复音乐分别映射为 `Play`、`Pause` 与 `Resume`（`hosts/apple/src/tools/audio/mod.rs:45`）。
- 停止与快进音乐分别映射为 `Stop` 与 `Seek`（`hosts/apple/src/tools/audio/mod.rs:55`）。
- 设置音量与查询状态分别映射为 `SetVolume` 与 `Status`（`hosts/apple/src/tools/audio/mod.rs:62`）。
- `playAudio` 直接调用 `player` 回调播放指定路径（`hosts/apple/src/tools/audio/mod.rs:37`）。
- `AppleBluetoothHost` 把蓝牙操作转交给 `AppleBluetoothController` 回调（`hosts/apple/src/tools/bluetooth/mod.rs:9`）。
- `supportsClassicListening` 固定返回 `false`（`hosts/apple/src/tools/bluetooth/mod.rs:38`）。
- 请求权限、查询状态与请求启用蓝牙分别发 `request_permission`、`state` 与 `request_enable` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:45`）。
- 列出已配对设备发 `bonded_devices` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:53`）。
- 扫描设备发 `scan` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:59`）。
- 经典蓝牙连接与监听分别发 `classic_connect` 与 `classic_listen` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:70`）。
- 接受连接发 `classic_accept` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:80`）。
- 发送数据发 `classic_send` 命令，参数含 `sessionId`、`text` 与 `dataBase64`（`hosts/apple/src/tools/bluetooth/mod.rs:89`）。
- 关闭会话发 `close` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:117`）。
- BLE 连接与发现服务分别发 `ble_connect` 与 `ble_discover_services` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:133`）。
- BLE 读特征与写特征分别发 `ble_read_characteristic` 与 `ble_write_characteristic` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:152`）。
- BLE 写后读发 `ble_write_and_read_characteristic` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:165`）。
- BLE 订阅特征发 `ble_subscribe_characteristic` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:175`）。
- BLE 读通知发 `ble_read_notifications` 命令（`hosts/apple/src/tools/bluetooth/mod.rs:183`）。
- `AppleTtsSynthesisHost` 的 `synthesizer` 字段是应用方提供的合成回调（`hosts/apple/src/tools/tts/mod.rs:20`）。
- `AppleTtsPlaybackHost` 的 `controller` 字段是应用方提供的播放控制回调（`hosts/apple/src/tools/tts/mod.rs:25`）。
- `supportsSystemSpeech` 固定返回 `true`（`hosts/apple/src/tools/tts/mod.rs:67`）。
- 播放与朗读分别映射为 `play` 与 `speak` 命令（`hosts/apple/src/tools/tts/mod.rs:74`）。
- 暂停与恢复分别映射为 `pause` 与 `resume` 命令（`hosts/apple/src/tools/tts/mod.rs:82`）。
- 停止与查询状态分别映射为 `stop` 与 `status` 命令（`hosts/apple/src/tools/tts/mod.rs:92`）。
- `AppleLocalInferenceHost` 把推理交给 `AppleLocalInferenceExecutor` 回调执行（`hosts/apple/src/tools/local_inference/mod.rs:15`）。
- `transcribeLocalSpeech` 以方法名 `transcribeLocalSpeech` 调用执行器（`hosts/apple/src/tools/local_inference/mod.rs:37`）。
- `synthesizeLocalSpeech` 以方法名 `synthesizeLocalSpeech` 调用执行器（`hosts/apple/src/tools/local_inference/mod.rs:44`）。
- 请求先序列化为 JSON 发给执行器，返回的 JSON 字符串再解码为响应（`hosts/apple/src/tools/local_inference/mod.rs:64`）。
- `AppleHttpHost` 内部持有 `NativeHttpHost`（`hosts/apple/src/tools/http/mod.rs:15`）。
- `imageDelivery` 委托给 `inner`（`hosts/apple/src/tools/http/mod.rs:62`）。
- `executeHttpRequest` 委托给 `inner`（`hosts/apple/src/tools/http/mod.rs:68`）。
- `openHttpResponseStream` 委托给 `inner`（`hosts/apple/src/tools/http/mod.rs:27`）。
- `openWebSocket` 委托给 `inner`（`hosts/apple/src/tools/http/mod.rs:104`）。

## 关键符号

- `AppleFileSystemHost` — macOS 与 iOS 共用的文件系统 Host（`hosts/apple/src/lib.rs:24`）。
- `AppleTerminalHost` — macOS 的 PTY 终端 Host（`hosts/apple/src/tools/terminal/terminal_macos.rs:14`）。
- `AppleWebVisitHost` — macOS 的 Chromium 网页访问 Host（`hosts/apple/src/lib.rs:23`）。
- `AppleBrowserAutomationHost` — macOS 的 Chromium 浏览器自动化 Host（`hosts/apple/src/lib.rs:23`）。
- `AppleManagedRuntimeHost` — macOS 的托管运行时 Host（`hosts/apple/src/lib.rs:29`）。
- `AppleRuntimeStorageHost` — macOS 与 iOS 共用的运行时存储 Host（`hosts/apple/src/lib.rs:30`）。
- `AppleSystemOperationHost` — macOS 与 iOS 共用的系统操作 Host（`hosts/apple/src/lib.rs:31`）。
- `AppleHttpHost` — macOS 与 iOS 共用的 HTTP 与 WebSocket Host（`hosts/apple/src/lib.rs:26`）。
- `AppleAudioPlaybackHost` — 音频与音乐播放 Host（`hosts/apple/src/tools/audio/mod.rs:22`）。
- `AppleMusicCommand` — 音乐播放命令枚举（`hosts/apple/src/tools/audio/mod.rs:11`）。
- `AppleBluetoothHost` — 经典蓝牙与 BLE Host（`hosts/apple/src/tools/bluetooth/mod.rs:10`）。
- `AppleTtsSynthesisHost` — TTS 合成 Host（`hosts/apple/src/tools/tts/mod.rs:20`）。
- `AppleTtsPlaybackHost` — TTS 播放 Host（`hosts/apple/src/tools/tts/mod.rs:25`）。
- `AppleLocalInferenceHost` — 本地推理 Host（`hosts/apple/src/tools/local_inference/mod.rs:20`）。
- `AppleLocalInferenceCommand` — 本地推理命令，含方法名与请求 JSON（`hosts/apple/src/tools/local_inference/mod.rs:14`）。
- `AppleTtsPlaybackCommand` — TTS 播放命令，含命令名、音频路径与播放请求（`hosts/apple/src/tools/tts/mod.rs:13`）。
- `AppleServiceDiscoveryHost` — Bonjour 服务发现 Host（`hosts/apple/src/service_discovery.rs:136`）。
- `AppleFileOpener` — 打开单个文件的回调函数类型（`hosts/apple/src/tools/fs/mod.rs:22`）。
- `createRuntimeHostManager` — macOS 的运行时 Host 管理器组装入口（`hosts/macos/src/lib.rs:43`）。
- `processIsolation` — 进程沙盒状态判定（`hosts/apple/src/sandbox.rs:6`）。

## 调用链

### macOS 运行时 Host 管理器组装

1. 调用方传入 `runtimeRoot`、`workspaceRoot` 与外部的 `webVisitHost`，调用 `createRuntimeHostManager`（`hosts/macos/src/lib.rs:45`）。
2. 以 `MacosRuntimeStorageHost::new(runtimeRoot, workspaceRoot)` 创建运行时存储 Host（`hosts/macos/src/lib.rs:51`）。
3. 同一个存储实例被 `clone` 为存储写入、SQLite 存储与密钥库 Host（`hosts/macos/src/lib.rs:53`）。
4. `withFileSystemWebVisitSystemOperationAndManagedRuntimeHosts` 一次注册文件系统、网页访问、HTTP、系统操作、托管运行时、运行时存储与 SQLite 存储（`hosts/macos/src/lib.rs:58`）。
5. 链式注册密钥库、WebSocket、HTTP 服务器、TCP 与串口 Host（`hosts/macos/src/lib.rs:65`）。
6. 链式注册归档暂存、存储写入、运行时事件、事件调度器、JS 运行时、服务发现、任务调度器与插件 SDK IPC Host（`hosts/macos/src/lib.rs:72`）。

### 文件打开

1. 调用方调 `openFile`，先校验路径为可读文件（`hosts/apple/src/tools/fs/mod.rs:477`）。
2. 已注册 `opener` 回调时直接调用回调（`hosts/apple/src/tools/fs/mod.rs:477`）。
3. macOS 上无回调时调用 `open` 命令打开文件（`hosts/apple/src/tools/fs/mod.rs:483`）。
4. 非 macOS 且无回调时返回错误（`hosts/apple/src/tools/fs/mod.rs:491`）。

### 终端会话创建（macOS）

1. AppleTerminalHost 的 `new` 先以 `processIsolation` 判定沙盒状态（`hosts/apple/src/tools/terminal/terminal_macos.rs:32`）。
2. 沙盒下只注册一个 `bash` 适配器，非沙盒下注册 `/bin/bash` 与 `/bin/zsh` 登录 shell（`hosts/apple/src/tools/terminal/terminal_macos.rs:38`）。
3. 调用方调 `createOrGetSession`，复用 `primary` 解释器的同名会话（`hosts/apple/src/tools/terminal/terminal_macos.rs:237`）。
4. 会话操作按 `ownsSession` 定位所属的底层 PTY Host（`hosts/apple/src/tools/terminal/terminal_macos.rs:83`）。

### 服务发现订阅

1. 调用方调 `subscribe`，按服务类型取共享浏览器（`hosts/apple/src/service_discovery.rs:683`）。
2. 已有记录通过 `callback(record)` 立即回放给订阅者（`hosts/apple/src/service_discovery.rs:700`）。
3. 取消订阅时 `Drop` 实现只移除本次订阅的回调（`hosts/apple/src/service_discovery.rs:124`）。

### 应用安装（macOS）

1. 调用方调 `installApp`，先要求 `Immediate` 安装时机（`hosts/apple/src/tools/system/mod.rs:207`）。
2. macOS 上转交 `packages::install`（`hosts/apple/src/tools/system/mod.rs:211`）。
3. .app 由 Finder 的 `duplicate` 复制到 /Applications（`hosts/apple/src/tools/system/packages.rs:163`）。
4. 复制成功后 `installState` 标记为 `Completed`（`hosts/apple/src/tools/system/packages.rs:169`）。
5. .pkg、.mpkg 或 .dmg 打开安装器并标记 `InstallerOpened`（`hosts/apple/src/tools/system/packages.rs:180`）。

## 来源

- hosts/apple/Cargo.toml
- hosts/apple/src/lib.rs
- hosts/apple/src/tools/fs/mod.rs
- hosts/apple/src/tools/terminal/mod.rs
- hosts/apple/src/tools/terminal/terminal_macos.rs
- hosts/apple/src/tools/browser/mod.rs
- hosts/apple/src/tools/runtime/mod.rs
- hosts/apple/src/tools/storage/mod.rs
- hosts/apple/src/tools/system/mod.rs
- hosts/apple/src/tools/system/battery.rs
- hosts/apple/src/tools/system/packages.rs
- hosts/apple/src/tools/local_inference/mod.rs
- hosts/apple/src/tools/tts/mod.rs
- hosts/apple/src/tools/http/mod.rs
- hosts/apple/src/tools/audio/mod.rs
- hosts/apple/src/tools/bluetooth/mod.rs
- hosts/apple/src/sandbox.rs
- hosts/apple/src/service_discovery.rs
- hosts/macos/src/lib.rs
