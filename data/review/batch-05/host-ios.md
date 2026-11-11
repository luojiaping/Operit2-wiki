---
title: iOS Host 与 ARM64 Linux 运行时
module: hosts
platforms: [ios]
sources: [hosts/ios/README.md, hosts/ios/Cargo.toml, hosts/ios/src/lib.rs, hosts/ios/src/terminal.rs, hosts/ios/src/bridge.rs, hosts/ios/src/managed_runtime.rs, hosts/ios/src/serial.rs]
date: 2026-11-11
---

## 概述

iOS Host 的 crate 名为 `operit-host-ios-native`，版本为 `0.1.0`，是 Operit2 在 iOS 上的 Host 实现（`hosts/ios/Cargo.toml:2`）。
iOS 终端的主后端是 ARM64 Linux 运行时（`hosts/ios/src/terminal.rs:92`）。
Flutter Runner 的终端通过 Rust 桥接调用 `Arm64TerminalBridge.mm`，使用原版 Alpine AArch64 软件包（`hosts/ios/README.md:5`）。
独立运行时的分层细节见 [[host-ios-linux-runtime|iOS 内嵌 ARM64 Linux 运行时（vendored）]]，其位置在 `linux-runtime` 子目录（`hosts/ios/README.md:5`）。
Host 目录通过运行时 bind mount 以原始绝对路径共享（`hosts/ios/README.md:15`）。
shell 与原生文件工具立即读写同一批文件（`hosts/ios/README.md:19`）。
iOS Host 当前报告没有已安装的原生串口 accessory provider（`hosts/ios/README.md:32`）。
`IosSerialPortHost` 的 `open` 接收 `port` 与 `_baud_rate`，恒返回 `Err`（`hosts/ios/src/serial.rs:11`）。
模拟器使用 `/Users/...` 路径，iOS 在更新期间可以更改容器 UUID（`hosts/ios/README.md:24`）。
iOS README 记录原生 bootstrap 通道把已持久化的 runtime/workspace 根恢复到当前容器（`hosts/ios/README.md:25`）。

## AI 速览

- `IosTerminalHost` — iOS 终端 Host，双后端 PTY 终端（`hosts/ios/src/terminal.rs:40`）。
- `IosManagedRuntimeHost` — iOS 托管运行时 Host，在 ARM64 rootfs 内启动托管进程（`hosts/ios/src/managed_runtime.rs:18`）。
- `IosSerialPortHost` — iOS 串口 Host，`open` 恒返回错误（`hosts/ios/src/serial.rs:7`）。
- `createRuntimeHostManager` — 组装 iOS 运行时 Host 管理器的入口（`hosts/ios/src/lib.rs:41`）。
- `callArm64Terminal` — Rust 到原生 ARM64 终端的 JSON 桥接调用（`hosts/ios/src/bridge.rs:36`）。
- `arm64RuntimeConfigurationId` — 读取原生运行时配置代次（`hosts/ios/src/bridge.rs:46`）。
- `IosRuntimeStorageHost` — iOS 运行时存储 Host（`hosts/ios/src/lib.rs:48`）。
- 主入口：`createRuntimeHostManager` 接收运行时根、workspace 根、网页访问 Host 与托管运行时 Host，返回组装好的 `HostManager`（`hosts/ios/src/lib.rs:41`）。
- 数据流向：终端请求发给 `callArm64Terminal`（`hosts/ios/src/terminal.rs:216`）。
- 数据流向：桥接再经原生 `Arm64TerminalBridge.mm` 进入 ARM64 Linux 运行时（`hosts/ios/README.md:5`）。

## 核心机制

### 终端双后端

- `IosTerminalBackend` 只有 `Arm64` 与 `SystemShell` 两个变体（`hosts/ios/src/terminal.rs:26`）。
- 主后端始终是 `Arm64`（`hosts/ios/src/terminal.rs:92`）。
- (`ARM64_TERMINAL`, `SHELL_TERMINAL_TYPE`) 映射为 `Arm64`（`hosts/ios/src/terminal.rs:100`）。
- 仅在 `systemShellAvailable` 为真时，(`SYSTEM_SHELL_TERMINAL`, `SHELL_TERMINAL_TYPE`) 映射为 `SystemShell`（`hosts/ios/src/terminal.rs:104`）。
- 系统 shell 不可用时，请求 (`SYSTEM_SHELL_TERMINAL`, `SHELL_TERMINAL_TYPE`) 返回 “iOS system /bin/sh is unavailable because this host cannot start a privileged PTY” 错误（`hosts/ios/src/terminal.rs:107`）。
- `IosTerminalHost` 的 `new` 用 `systemShell.probe("/")` 探测系统 shell，`systemShellAvailable` 取探测是否成功（`hosts/ios/src/terminal.rs:57`）。
- 终端信息把 `arm64` 终端标为可用，描述为 “Operit ARM64 Linux shell using the configured root filesystem”（`hosts/ios/src/terminal.rs:352`）。
- 终端信息把系统 shell 的可用性记为 `systemShellAvailable`，描述为 “iOS system /bin/sh; requires a jailbroken or otherwise privileged host”（`hosts/ios/src/terminal.rs:348`）。
- macOS 专用的 `arm64Only` 把 `systemShellAvailable` 设为 false，只用 Linux 后端（`hosts/ios/src/terminal.rs:72`）。
- 非 macOS 目标上 `PLATFORM` 为 `ios`，macOS 目标上 `PLATFORM` 为 `macos`（`hosts/ios/src/terminal.rs:18`）。

### 桥接与配置代次

- Rust 声明外部函数 `operit_ios_arm64_terminal_call`，接收命令与请求 JSON 的 C 字符串，返回原生分配的 C 字符串（`hosts/ios/src/bridge.rs:10`）。
- macOS 目标把 `operit_ios_arm64_terminal_call` 链接为 `operit_macos_arm64_terminal_call`（`hosts/ios/src/bridge.rs:10`）。
- `callArm64Terminal` 把请求编码为 JSON 后调用原生终端函数，再解码原生响应（`hosts/ios/src/bridge.rs:36`）。
- 桥接返回空指针时返回 “ARM64 terminal bridge returned no response” 错误（`hosts/ios/src/bridge.rs:60`）。
- 原生响应先复制字节，再用 `operit_ios_arm64_terminal_free` 释放原生分配（`hosts/ios/src/bridge.rs:66`）。
- 响应含 `error` 字段时，该字段作为 `HostError` 返回（`hosts/ios/src/bridge.rs:72`）。
- 响应缺少 `result` 字段时返回 “ARM64 terminal bridge response has no result” 错误（`hosts/ios/src/bridge.rs:76`）。
- 流式执行以 `terminalExecute` 为命令调用流式原生函数，并把 `receive` 作为输出回调传入（`hosts/ios/src/bridge.rs:131`）。
- 输出回调收到无效帧（长度非零但指针为空，或长度超过 `isize::MAX`）时记录 “ARM64 terminal returned an invalid output frame” 错误并返回 false（`hosts/ios/src/bridge.rs:94`）。
- 输出回调用 `catch_unwind` 包裹调用方回调，回调 panic 时记录 “ARM64 terminal output callback panicked” 错误（`hosts/ios/src/bridge.rs:108`）。
- `arm64RuntimeConfigurationId` 查询 `arm64RuntimeState`，`configured` 为 false 时返回 `None`（`hosts/ios/src/bridge.rs:47`）。
- 运行时状态缺少配置标识时返回 “ARM64 runtime state has no configuration identifier” 错误（`hosts/ios/src/bridge.rs:56`）。
- 配置标识变化时仅丢弃 ARM64 会话的注册，系统 shell 会话保留；新标识取自 `arm64RuntimeConfigurationId`（`hosts/ios/src/terminal.rs:151`）。
- ARM64 会话启动在取 `sessionId` 前用 `requireArm64Configuration` 校验创建响应（`hosts/ios/src/terminal.rs:225`）。
- `requireArm64Configuration` 在响应 `configurationId` 与当前配置不一致时返回错误（`hosts/ios/src/terminal.rs:165`）。
- `listSessions` 发送 `terminalList`，只保留 `configurationId` 与当前代次一致的 ARM64 会话（`hosts/ios/src/terminal.rs:505`）。

### 会话操作

- ARM64 会话启动发送 `terminalStart`，携带 `sessionName`、`terminalType`（`SHELL_TERMINAL_TYPE`）、`workingDir`、`rows` 与 `cols`（`hosts/ios/src/terminal.rs:216`）。
- ARM64 的 `terminalCreateOrGet` 响应同样经过 `requireArm64Configuration` 校验（`hosts/ios/src/terminal.rs:254`）。
- ARM64 会话内执行发送 `terminalExecute`，输出取自 `outputBytes` 字段（`hosts/ios/src/terminal.rs:291`）。
- ARM64 流式执行调用 `callArm64TerminalStreaming` 传输输出回调，命令结果仍从响应取 `outputBytes` 与 `exitCode`（`hosts/ios/src/terminal.rs:572`）。
- ARM64 会话读取发送 `terminalRead`，返回 `bytes` 字段的字节（`hosts/ios/src/terminal.rs:386`）。
- ARM64 写入按 16 KiB 分块重试，截止时间为 30 秒（`hosts/ios/src/terminal.rs:412`）。
- ARM64 写入每块发送 `terminalWrite`，用 `acceptedBytes` 校验原生侧接受的字节数（`hosts/ios/src/terminal.rs:417`）。
- ARM64 会话调整大小发送 `terminalResize`，携带 `rows` 与 `cols`（`hosts/ios/src/terminal.rs:448`）。
- ARM64 退出码轮询发送 `terminalPoll`，`exitCode` 为 null 或缺失时返回 `None`（`hosts/ios/src/terminal.rs:468`）。
- ARM64 会话屏幕查询发送 `terminalScreen`，内容取自 `contentBytes` 字段（`hosts/ios/src/terminal.rs:678`）。
- ARM64 会话关闭发送 `terminalClose`，随后移除会话注册（`hosts/ios/src/terminal.rs:490`）。
- 关闭会话返回 `TerminalCloseOutput`，`success` 为 true，消息为 “iOS terminal session closed”（`hosts/ios/src/terminal.rs:661`）。
- 隐藏命令执行先创建或复用名为 `hidden:{executorKey}` 的会话，再在该会话内执行命令（`hosts/ios/src/terminal.rs:600`）。
- ARM64 会话收到 `interrupt` 控制时发送 `terminalSignal`，`signal` 为 2（`hosts/ios/src/terminal.rs:642`）。
- `controlSequence` 把 `interrupt` 映射为 U+0003，把 `eof` 映射为 U+0004，把 `newline` 映射为换行符（`hosts/ios/src/terminal.rs:845`）。
- iOS 终端输入同时传入文本与控制序列时返回错误，文本与控制序列均缺失时也返回错误（`hosts/ios/src/terminal.rs:633`）。
- `terminalText` 用 `String::from_utf8_lossy` 把 PTY 字节解码为文本（`hosts/ios/src/terminal.rs:813`）。
- `requiredText` 去除首尾空白，空白值返回错误（`hosts/ios/src/terminal.rs:759`）。
- `positiveDimension` 拒绝为零的行列尺寸（`hosts/ios/src/terminal.rs:771`）。
- `shellTerminalType` 只接受 `shell` 类型，其他值返回错误（`hosts/ios/src/terminal.rs:749`）。
- 未注册的会话标识返回 “iOS terminal session backend is not registered” 错误（`hosts/ios/src/terminal.rs:186`）。
- 会话列表仅在 `systemShellAvailable` 为真时追加系统 shell 会话（`hosts/ios/src/terminal.rs:516`）。

### Bind Mount 与工作目录

- Host 目录通过运行时 bind mount 以原始绝对路径共享（`hosts/ios/README.md:15`）。
- 同路径 bind mount 与 Android 的同路径 bind mount 一致（`hosts/ios/README.md:16`）。
- Documents 目录与 Operit2 应用支持目录对每个 shell 可用（`hosts/ios/README.md:16`）。
- 创建会话时也可以挂载一个 Host 工作目录（`hosts/ios/README.md:18`）。
- shell 与原生文件工具立即读写同一批文件（`hosts/ios/README.md:19`）。
- 挂载在每次启动时重建，不涉及 workspace 复制或基于哈希的 MCP 路径（`hosts/ios/README.md:20`）。
- ARM64 后端解析工作目录时发送 `terminalWorkspaceMount`，`hostDirectory` 与 `mountPoint` 取同一目录值（`hosts/ios/src/terminal.rs:328`）。
- 系统 shell 后端解析工作目录时直接调用 `resolveHostDirectory`，不经过挂载（`hosts/ios/src/terminal.rs:336`）。
- 托管运行时目录挂载向原生侧发送 `managedRuntimeMount`，携带 `hostDirectory` 与 `mountPoint`（`hosts/ios/src/terminal.rs:82`）。
- Host 父目录以自身绝对路径挂载，即 `mountManagedRuntimeDirectory(hostParent, hostParent)`（`hosts/ios/src/managed_runtime.rs:102`）。
- `mountRuntimeWorkingDirectory` 拒绝非绝对路径的 Host 工作目录（`hosts/ios/src/managed_runtime.rs:86`）。

### 托管运行时

- `ARM64_RUNTIME_WORKSPACE` 为 `/root/.operit/managed_runtime`（`hosts/ios/src/managed_runtime.rs:14`）。
- `runtimeWorkspaceDir` 返回 `ARM64_RUNTIME_WORKSPACE`（`hosts/ios/src/managed_runtime.rs:122`）。
- 带工作目录的启动请求先经 `mountRuntimeWorkingDirectory` 挂载 Host 工作目录，会话与进程工作目录均取该目录（`hosts/ios/src/managed_runtime.rs:51`）。
- 无工作目录的启动请求以 `/root` 为会话工作目录，以 `ARM64_RUNTIME_WORKSPACE` 为进程工作目录，并要求创建进程工作目录（`hosts/ios/src/managed_runtime.rs:62`）。
- 运行时可执行文件映射为：`Node` 对应 `/usr/bin/node`，`Python` 对应 `/usr/bin/python3`，`Uv` 对应 `/usr/bin/uv`，`Pnpm` 对应 `/usr/bin/pnpm`（`hosts/ios/src/managed_runtime.rs:138`）。
- `executablePath` 非空时直接返回该路径，不使用程序默认值（`hosts/ios/src/managed_runtime.rs:132`）。
- `runRuntimeCommand` 启动进程后等待退出、取 stdout 文本，`stderr` 返回空字符串（`hosts/ios/src/managed_runtime.rs:160`）。
- `startProcess` 用 `buildLaunch` 构建启动描述后启动 `TerminalManagedRuntimeProcess`（`hosts/ios/src/managed_runtime.rs:115`）。
- `hostManager.managedRuntimeHost` 设置为传入的 `managedRuntimeHost` 参数（`hosts/ios/src/lib.rs:67`）。

### 存储与路径恢复

- ARM64 安装器把打包的 `arm64-rootfs.tar.gz` 一次性导入应用数据容器内的 `Library/Application Support/operit-arm64/rootfs-arm64`（`hosts/ios/README.md:9`）。
- 后续启动复用已导入的 rootfs，`/root`、shell 配置与装入 `/usr` 的软件在进程重启与保留应用数据的应用更新后保留（`hosts/ios/README.md:11`）。
- 删除应用数据会同时删除该 Alpine 文件系统（`hosts/ios/README.md:13`）。
- `/root` 这类仅 Linux 路径属于持久化 Alpine 文件系统（`hosts/ios/README.md:21`）。
- 真机上 Host 路径以应用的 `/var/mobile/...` 容器路径开头（`hosts/ios/README.md:23`）。
- 模拟器使用 `/Users/...` 路径，iOS 在更新期间可以更改容器 UUID（`hosts/ios/README.md:24`）。
- iOS README 记录原生 bootstrap 通道把已持久化的 runtime/workspace 根恢复到当前容器（`hosts/ios/README.md:25`）。
- 脚本对终端自有文件使用 `$HOME`，对共享文件使用 Host 提供的当前绝对 workspace 路径（`hosts/ios/README.md:26`）。
- 运行时存储 Host 由 `IosRuntimeStorageHost::new(runtimeRoot, workspaceRoot)` 创建（`hosts/ios/src/lib.rs:48`）。
- 同一 `IosRuntimeStorageHost` 实例被克隆用作运行时存储写 Host、运行时 SQLite Host 与 Host 密钥库（`hosts/ios/src/lib.rs:48`）。
- 归档暂存 Host 由 `NativeArchiveStagingHost` 以 `runtimeStorageHost` 的 `runtimeRootDir()` 创建，缺失时以 “iOS runtime storage root must be configured” 报错（`hosts/ios/src/lib.rs:54`）。

### 串口现状

- Core 通过 `SerialPortHost` 打开串口端点（`hosts/ios/README.md:31`）。
- iOS Host 当前报告没有已安装的原生串口 accessory provider（`hosts/ios/README.md:32`）。
- `IosSerialPortHost` 的 `open` 接收 `port` 与 `_baud_rate`，恒返回 `Err`（`hosts/ios/src/serial.rs:11`）。
- `open` 的错误文本说明 iOS Host 对该端口没有串口 accessory provider，需要原生 accessory transport（`hosts/ios/src/serial.rs:13`）。
- `hostManager.serialPortHost` 设置为 `IosSerialPortHost`（`hosts/ios/src/lib.rs:65`）。
- 原生 accessory provider 可以实现同一 `SerialPortHost` 契约，无需改动 Core 的串口 Link 协议（`hosts/ios/src/serial.rs:6`）。
- 实现一个 accessory provider 并在 host manager 注册后，现有的 Link 成帧与配对协议无需 Core 增加平台分支即可启用（`hosts/ios/README.md:33`）。
- 该串口说明不表示 iOS 上存在不受限的 USB/UART 访问（`hosts/ios/README.md:35`）。

### Host 组装

- `createRuntimeHostManager` 接收 `runtimeRoot`、`workspaceRoot`、`webVisitHost` 与 `managedRuntimeHost`，返回 `HostManager`，仅在 `target_os = "ios"` 下编译（`hosts/ios/src/lib.rs:41`）。
- 组装 iOS Host 管理器时调用 `installAppleLogSink` 安装 Apple 日志 sink（`hosts/ios/src/lib.rs:47`）。
- `HostManager` 由 `IosFileSystemHost`、`webVisitHost` 与 `IosSystemOperationHost` 构建（`hosts/ios/src/lib.rs:57`）。
- `hostManager.httpHost` 与 `hostManager.webSocketHost` 均使用 `IosHttpHost`（`hosts/ios/src/lib.rs:62`）。
- `hostManager.httpServerHost` 使用 `NativeHttpServerHost`，`hostManager.tcpHost` 使用 `NativeTcpHost`（`hosts/ios/src/lib.rs:64`）。
- `IosPluginSdkIpcHost` 是 `MemoryPluginSdkIpcHost`，iOS 插件在应用沙箱内执行并共享同一进程（`hosts/ios/src/lib.rs:37`）。
- lib.rs 注释说明容器长临时路径下的文件系统 socket 超出 `SUN_LEN`，同一处把 `IosPluginSdkIpcHost` 定义为 `MemoryPluginSdkIpcHost`（`hosts/ios/src/lib.rs:36`）。
- Apple 侧共享实现（文件系统、HTTP、系统操作等）见 [[host-apple|Apple Host（macOS 与 iOS 共享实现）]]（`hosts/ios/src/lib.rs:57`）。
- iOS Host 依赖路径为 `../../core/crates/foundation/host-api` 的 `operit-host-api`（`hosts/ios/Cargo.toml:10`）。
- iOS Host 依赖路径为 `../apple` 的 `operit-host-apple-native`（`hosts/ios/Cargo.toml:11`）。
- iOS Host 依赖 `operit-host-native-common`，开启 `tcp`、`storage`、`terminal` 三个 feature（`hosts/ios/Cargo.toml:12`）。

## 关键符号

- `IosTerminalHost` — iOS 终端 Host，双后端 PTY 终端（`hosts/ios/src/terminal.rs:40`）。
- `IosTerminalBackend` — 终端后端枚举，只有 `Arm64` 与 `SystemShell`（`hosts/ios/src/terminal.rs:26`）。
- `IosTerminalState` — 终端会话注册表，保存配置代次与会话后端映射（`hosts/ios/src/terminal.rs:32`）。
- `IosManagedRuntimeHost` — iOS 托管运行时 Host，在 ARM64 rootfs 内启动托管进程（`hosts/ios/src/managed_runtime.rs:18`）。
- `IosSerialPortHost` — iOS 串口 Host，`open` 恒返回错误（`hosts/ios/src/serial.rs:7`）。
- `IosRuntimeStorageHost` — iOS 运行时存储 Host（`hosts/ios/src/lib.rs:48`）。
- `IosPluginSdkIpcHost` — iOS 插件 SDK IPC Host，内存通道（`hosts/ios/src/lib.rs:37`）。
- `createRuntimeHostManager` — 组装 iOS 运行时 Host 管理器的入口（`hosts/ios/src/lib.rs:41`）。
- `callArm64Terminal` — Rust 到原生 ARM64 终端的 JSON 桥接调用（`hosts/ios/src/bridge.rs:36`）。
- `callArm64TerminalStreaming` — 流式桥接调用（`hosts/ios/src/bridge.rs:120`）。
- `arm64RuntimeConfigurationId` — 读取原生运行时配置代次（`hosts/ios/src/bridge.rs:46`）。
- `decodeResponse` — 解码原生桥接响应（`hosts/ios/src/bridge.rs:59`）。
- `operit_ios_arm64_terminal_call` — 原生 ARM64 终端调用外部函数（`hosts/ios/src/bridge.rs:10`）。
- `operit_ios_arm64_terminal_execute_streaming` — 原生流式执行外部函数（`hosts/ios/src/bridge.rs:20`）。
- `ARM64_RUNTIME_WORKSPACE` — 托管运行时 workspace 常量，`/root/.operit/managed_runtime`（`hosts/ios/src/managed_runtime.rs:14`）。
- `ARM64_TERMINAL` — ARM64 终端标识常量，`arm64`（`hosts/ios/src/terminal.rs:21`）。
- `PLATFORM` — 平台标识常量，iOS 上为 `ios`（`hosts/ios/src/terminal.rs:18`）。

## 调用链

1. `createRuntimeHostManager` 接收 `runtimeRoot`、`workspaceRoot`、`webVisitHost` 与 `managedRuntimeHost`，返回组装好的 `HostManager`（`hosts/ios/src/lib.rs:41`）。
2. `HostManager` 由 `IosFileSystemHost`、`webVisitHost` 与 `IosSystemOperationHost` 构建（`hosts/ios/src/lib.rs:57`）。
3. `hostManager.serialPortHost` 设置为 `IosSerialPortHost`（`hosts/ios/src/lib.rs:65`）。
4. 终端创建：发送 `terminalStart`（`hosts/ios/src/terminal.rs:216`）。
5. 终端创建：创建响应在取 `sessionId` 前用 `requireArm64Configuration` 校验（`hosts/ios/src/terminal.rs:225`）。
6. 工作目录解析：ARM64 后端发送 `terminalWorkspaceMount`，`hostDirectory` 与 `mountPoint` 取同一目录值（`hosts/ios/src/terminal.rs:328`）。
7. 会话内执行：发送 `terminalExecute`，输出取自 `outputBytes`（`hosts/ios/src/terminal.rs:291`）。
8. 流式执行：调用 `callArm64TerminalStreaming` 传输输出回调（`hosts/ios/src/terminal.rs:572`）。
9. 托管进程启动：`buildLaunch` 挂载 Host 工作目录后，`startProcess` 启动 `TerminalManagedRuntimeProcess`（`hosts/ios/src/managed_runtime.rs:115`）。
10. 配置变化：取回当前配置标识，变化时仅丢弃 ARM64 会话的注册（`hosts/ios/src/terminal.rs:151`）。
11. 配置变化：未注册的会话标识返回 “iOS terminal session backend is not registered” 错误（`hosts/ios/src/terminal.rs:186`）。
12. 串口打开：`IosSerialPortHost` 的 `open` 恒返回错误，说明没有串口 accessory provider（`hosts/ios/src/serial.rs:13`）。

## 来源

- `hosts/ios/README.md`
- `hosts/ios/Cargo.toml`
- `hosts/ios/src/lib.rs`
- `hosts/ios/src/terminal.rs`
- `hosts/ios/src/bridge.rs`
- `hosts/ios/src/managed_runtime.rs`
- `hosts/ios/src/serial.rs`
