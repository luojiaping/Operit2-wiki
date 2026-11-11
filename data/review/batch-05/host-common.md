---
title: Host 共享实现
module: hosts
platforms: [android, ios, linux, macos, windows]
sources: [hosts/common/operit-host-native-common/src/lib.rs, hosts/common/operit-host-native-common/src/DaemonHost.rs, hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs, hosts/common/operit-host-native-common/src/SerialPort.rs, hosts/common/operit-host-native-common/src/ServiceDiscovery.rs, hosts/common/operit-host-native-common/src/SharedBuffer.rs, hosts/common/operit-host-native-common/src/Tcp.rs, hosts/common/operit-host-native-filesystem/src/lib.rs, hosts/common/operit-host-native-http/src/lib.rs, hosts/common/operit-host-native-storage/src/lib.rs, hosts/common/operit-host-native-terminal/src/lib.rs, hosts/common/operit-host-native-scheduler/src/lib.rs, hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs, hosts/common/operit-host-data-rescue/src/lib.rs, hosts/common/chromium_browser.rs, hosts/common/terminal_command.rs, hosts/unix/daemon.rs, hosts/plugin-sdk-client/src/lib.rs, hosts/tests/daemon.rs, docs/data-rescue.md, apps/cli/src/rescue.rs, hosts/common/operit-host-native-common/Cargo.toml, hosts/common/operit-host-native-filesystem/Cargo.toml, hosts/common/operit-host-native-http/Cargo.toml, hosts/common/operit-host-native-storage/Cargo.toml, hosts/common/operit-host-native-terminal/Cargo.toml, hosts/common/operit-host-native-scheduler/Cargo.toml, hosts/common/operit-host-native-plugin-sdk-ipc/Cargo.toml, hosts/common/operit-host-data-rescue/Cargo.toml, hosts/apple/src/lib.rs, hosts/linux/src/lib.rs, hosts/windows/src/lib.rs, hosts/android/src/lib.rs, hosts/windows/src/tools/terminal/mod.rs, hosts/android/src/http.rs, hosts/android/src/filesystem.rs, hosts/ios/src/terminal.rs]
date: 2026-11-11
---

## 概述

hosts/common 的共享实现由各平台 Host 持有使用，Android 的 HTTP 实现内部持有 `operit_host_native_common::NativeHttpHost`，Android 侧见 [[host-android|Android Host]]（`hosts/android/src/http.rs:11`）。
hosts/common 下有名为 `operit-host-native-common` 的 crate（`hosts/common/operit-host-native-common/Cargo.toml:2`）。
hosts/common 下有名为 `operit-host-native-filesystem` 的 crate（`hosts/common/operit-host-native-filesystem/Cargo.toml:2`）。
hosts/common 下有名为 `operit-host-native-http` 的 crate（`hosts/common/operit-host-native-http/Cargo.toml:2`）。
hosts/common 下有名为 `operit-host-native-storage` 的 crate（`hosts/common/operit-host-native-storage/Cargo.toml:2`）。
hosts/common 下有名为 `operit-host-native-terminal` 的 crate（`hosts/common/operit-host-native-terminal/Cargo.toml:2`）。
hosts/common 下有名为 `operit-host-native-scheduler` 的 crate（`hosts/common/operit-host-native-scheduler/Cargo.toml:2`）。
hosts/common 下有名为 `operit-host-native-plugin-sdk-ipc` 的 crate（`hosts/common/operit-host-native-plugin-sdk-ipc/Cargo.toml:2`）。
hosts/common 下有名为 `operit-host-data-rescue` 的 crate（`hosts/common/operit-host-data-rescue/Cargo.toml:2`）。
operit-host-native-common 是聚合入口，默认不启用任何 feature（`hosts/common/operit-host-native-common/Cargo.toml:9`）。
hosts/unix 只有 daemon.rs 一个 Unix 守护进程传输实现，没有独立平台意义（`hosts/unix/daemon.rs:15`）。
hosts/plugin-sdk-client 只有按目标平台选择 IPC 宿主的调度器，没有独立平台意义（`hosts/plugin-sdk-client/src/lib.rs:28`）。
hosts/tests/daemon.rs 只有 Unix daemon 传输的测试脚手架，没有独立平台意义（`hosts/tests/daemon.rs:69`）。

## AI 速览

- operit-host-native-common — 聚合共享 crate 的 feature 门控入口（`hosts/common/operit-host-native-common/src/lib.rs:24`）
- `PosixFileSystemHost` — 共享 POSIX 文件系统实现（`hosts/common/operit-host-native-filesystem/src/lib.rs:93`）
- `NativeHttpHost` — 共享原生 HTTP、WebSocket 与下载实现（`hosts/common/operit-host-native-http/src/lib.rs:31`）
- `NativeRuntimeStorageHost` — 共享运行时存储实现（`hosts/common/operit-host-native-storage/src/lib.rs:21`）
- `NativeArchiveStagingHost` — 共享归档暂存实现（`hosts/common/operit-host-native-storage/src/lib.rs:367`）
- `NativePtyTerminalHost` — 共享 POSIX PTY 终端实现（`hosts/common/operit-host-native-terminal/src/lib.rs:26`）
- `NativeHostRuntimeTaskSchedulerHost` — 共享原生任务调度器实现（`hosts/common/operit-host-native-scheduler/src/lib.rs:17`）
- `MemoryPluginSdkIpcHost` — 共享插件 SDK 内存 IPC 实现（`hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs:9`）
- `NativeRescueSession` — 离线数据救援维护会话（`hosts/common/operit-host-data-rescue/src/lib.rs:71`）
- `ChromiumBrowserAutomationHost` — 共享 Chromium 浏览器自动化实现（`hosts/common/chromium_browser.rs:34`）
- `ServiceDiscoveryProvider` — 共享 mDNS 服务发现实现（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:158`）
- `NativeTcpHost` — 共享 TCP 实现（`hosts/common/operit-host-native-common/src/Tcp.rs:13`）
- `NativeSerialPortHost` — 共享串口实现（`hosts/common/operit-host-native-common/src/SerialPort.rs:19`）
- `SharedBuffer` — 原生 Rust 与 Dart 之间的共享二进制缓冲（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:6`）
- `ControlStream` — 平台无关的本地守护进程字节流（`hosts/common/operit-host-native-common/src/DaemonHost.rs:10`）
- `TerminalManagedRuntimeProcess` — 经 PTY 启动的托管运行时进程（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:29`）
- 平台 Host 按 feature 取用重导出的共享实现（`hosts/common/operit-host-native-common/src/lib.rs:24`）
- 数据流向一句话：平台 Host 持有共享实现并调用其操作（`hosts/android/src/filesystem.rs:14`）

## 核心机制

### 聚合入口与 feature 门控

operit-host-native-common 的 `fs` feature 启用 filesystem crate 并重导出 `PosixFileSystemHost` 与 `NativeFileAppendHandle`（`hosts/common/operit-host-native-common/src/lib.rs:24`）。
operit-host-native-common 的 `http` feature 重导出 `NativeHttpHost` 与 `NativeHttpServerHost`（`hosts/common/operit-host-native-common/src/lib.rs:26`）。
operit-host-native-common 的 `scheduler` feature 重导出 `NativeHostJavaScriptRuntimeHost`（`hosts/common/operit-host-native-common/src/lib.rs:28`）。
operit-host-native-common 的 `scheduler` feature 重导出 `NativeHostRuntimeEventSchedulerHost`（`hosts/common/operit-host-native-common/src/lib.rs:30`）。
operit-host-native-common 的 `storage` feature 重导出 `NativeArchiveStagingHost`（`hosts/common/operit-host-native-common/src/lib.rs:32`）。
operit-host-native-common 的 `storage` feature 重导出 `NativeFileSecretStore` 与 `NativeRuntimeStorageHost`（`hosts/common/operit-host-native-common/src/lib.rs:34`）。
operit-host-native-common 的 `terminal` feature 重导出 `NativePtyShellCommand` 与 `NativePtyTerminalHost`（`hosts/common/operit-host-native-common/src/lib.rs:36`）。
operit-host-native-common 的 `terminal` feature 重导出 `TerminalManagedRuntimeLaunch` 与 `TerminalManagedRuntimeProcess`（`hosts/common/operit-host-native-common/src/lib.rs:40`）。
operit-host-native-common 的 `tcp` feature 重导出 `NativeTcpHost`（`hosts/common/operit-host-native-common/src/lib.rs:54`）。
operit-host-native-common 的 `serial` feature 重导出 `NativeSerialPortHost`（`hosts/common/operit-host-native-common/src/lib.rs:21`）。
`DaemonHost` 模块只在 `daemon` feature 下编译（`hosts/common/operit-host-native-common/src/lib.rs:10`）。
`AppInstaller` 模块只在 `app-install` feature 下编译（`hosts/common/operit-host-native-common/src/lib.rs:4`）。
`DartPort` 与 `SharedBuffer` 模块没有 feature 门控、始终编译（`hosts/common/operit-host-native-common/src/lib.rs:6`）。
`SerialPort` 模块在 iOS、espidf 与 wasm32 上不编译（启用 `serial` feature 时）（`hosts/common/operit-host-native-common/src/lib.rs:14`）。
`ServiceDiscovery` 模块在 espidf 与 wasm32 上不编译（`hosts/common/operit-host-native-common/src/lib.rs:42`）。
`Tcp` 模块在 espidf 与 wasm32 上不编译（启用 `tcp` feature 时）（`hosts/common/operit-host-native-common/src/lib.rs:47`）。
operit-host-native-common 重导出调度器的 `scheduleNativeBlockingTask`、`scheduleNativeServiceTask`、`scheduleNativeServiceTasks`、`NativeHostRuntimeTaskSchedulerHost` 与 `NativeTaskHandle`（`hosts/common/operit-host-native-common/src/lib.rs:58`）。

### 文件系统

PosixFileSystemHost 的 `new` 默认使用 Linux 环境描述符（`hosts/common/operit-host-native-filesystem/src/lib.rs:93`）。
PosixFileSystemHost 的 `validatePath` 要求绝对 POSIX 路径（`hosts/common/operit-host-native-filesystem/src/lib.rs:130`）。
PosixFileSystemHost 的 `openAppendFile` 先校验路径再打开追加描述符（`hosts/common/operit-host-native-filesystem/src/lib.rs:117`）。
NativeFileAppendHandle 的 `open` 创建文件并读取一次起始长度（`hosts/common/operit-host-native-filesystem/src/lib.rs:25`）。
PosixFileSystemHost 的 `findFiles` 用 glob 匹配文件（`hosts/common/operit-host-native-filesystem/src/lib.rs:320`）。
遍历深度由 `request.maxDepth` 限制（`hosts/common/operit-host-native-filesystem/src/lib.rs:338`）。
PosixFileSystemHost 的 `grepCode` 用正则匹配代码并支持上下文行（`hosts/common/operit-host-native-filesystem/src/lib.rs:407`）。
PosixFileSystemHost 的 `zipFiles` 把源路径打包为 ZIP（`hosts/common/operit-host-native-filesystem/src/lib.rs:477`）。
PosixFileSystemHost 的 `unzipFiles` 把 ZIP 解压到目标目录（`hosts/common/operit-host-native-filesystem/src/lib.rs:509`）。
PosixFileSystemHost 的 `fileInfo` 对不存在的路径返回 `exists` 为 false 的 `FileInfo`（`hosts/common/operit-host-native-filesystem/src/lib.rs:364`）。

### HTTP、WebSocket 与下载

`NativeHttpHost` 持有字节流、WebSocket 与 HTTP 客户端三张注册表（`hosts/common/operit-host-native-http/src/lib.rs:31`）。
`HttpClientPolicy` 由连接超时、读取超时、重定向、忽略证书与代理标识一个连接池（`hosts/common/operit-host-native-http/src/lib.rs:39`）。
WebSocket 发送队列容量为 64（`hosts/common/operit-host-native-http/src/lib.rs:73`）。
NativeHttpHost 的 `openWebSocket` 打开原生 WebSocket 并转发打开、消息与关闭回调（`hosts/common/operit-host-native-http/src/lib.rs:124`）。
NativeHttpHost 的 `closeWebSocket` 移除注册并置位取消信号（`hosts/common/operit-host-native-http/src/lib.rs:161`）。
NativeHttpHost 的 `imageDelivery` 返回 `HttpImageDelivery::Bytes`（`hosts/common/operit-host-native-http/src/lib.rs:417`）。
NativeHttpHost 的 `executeHttpRequest` 经共享网络任务执行缓冲请求（`hosts/common/operit-host-native-http/src/lib.rs:422`）。
NativeHttpHost 的 `downloadToFile` 把响应流式下载到目标文件（`hosts/common/operit-host-native-http/src/lib.rs:430`）。
downloadToFileAsync 写完临时文件后重命名发布到目标路径（`hosts/common/operit-host-native-http/src/lib.rs:514`）。
downloadToFileAsync 失败时删除临时文件（`hosts/common/operit-host-native-http/src/lib.rs:523`）。
NativeHttpHost 的 `downloadFiles` 批量下载多个文件并上报进度（`hosts/common/operit-host-native-http/src/lib.rs:441`）。
批量下载的并发任务数（并行上限）取 `maxConcurrency` 与文件总数中较小者（`hosts/common/operit-host-native-http/src/lib.rs:678`）。
断点续传时下载请求带 `RANGE` 头从已保留字节处继续（`hosts/common/operit-host-native-http/src/lib.rs:918`）。
`validateContentRange` 校验续传响应的起始位置与总量（`hosts/common/operit-host-native-http/src/lib.rs:1082`）。
`buildHttpStreamClient` 构建 Host 的流式 HTTP 客户端（`hosts/common/operit-host-native-http/src/lib.rs:809`）。
流式 HTTP 客户端把 `ignoreSsl` 传给 `danger_accept_invalid_certs`（`hosts/common/operit-host-native-http/src/lib.rs:819`）。
`NativeHttpServerHost` 由 `server` 子模块提供并在 http crate 入口重导出（`hosts/common/operit-host-native-http/src/lib.rs:5`）。

### 存储、归档暂存与 SQLite

`NativeRuntimeStorageHost` 用 `runtimeRoot` 与 `workspaceRoot` 两个物理根构造（`hosts/common/operit-host-native-storage/src/lib.rs:21`）。
NativeRuntimeStorageHost 的 `resolve` 把虚拟前缀映射到物理根（`hosts/common/operit-host-native-storage/src/lib.rs:524`）。
运行时存储路径必须以 `runtime/`、`workspaces/` 或 `secure/` 开头（`hosts/common/operit-host-native-storage/src/lib.rs:532`）。
`managedRoot` 把 `workspaces` 与三条 `runtime/data` 聊天目录划为托管根（`hosts/common/operit-host-native-storage/src/lib.rs:542`）。
NativeRuntimeStorageWriteSession 的 `commitInternal` 关闭文件后原子重命名发布（`hosts/common/operit-host-native-storage/src/lib.rs:35`）。
`commit` 提交时强制设备刷盘，`commitFast` 提交时不强制刷盘（`hosts/common/operit-host-native-storage/src/lib.rs:71`）。
`publishStagedFile` 先原子替换、同步时再同步父目录（`hosts/common/operit-host-native-storage/src/lib.rs:843`）。
Windows 原子发布用 `MoveFileExW` 加 `MOVEFILE_REPLACE_EXISTING` 与 `MOVEFILE_WRITE_THROUGH`（`hosts/common/operit-host-native-storage/src/lib.rs:885`）。
`ARCHIVE_STAGING_DIRECTORY_NAME` 的值是 `archive_staging`（`hosts/common/operit-host-native-storage/src/lib.rs:91`）。
`stagingRootForRuntimeRoot` 把 staging 根放在运行时父目录下的 `ARCHIVE_STAGING_DIRECTORY_NAME` 命名空间（`hosts/common/operit-host-native-storage/src/lib.rs:190`）。
遗留归档保留期为 7 天（`hosts/common/operit-host-native-storage/src/lib.rs:94`）。
NativeArchiveStagingHost 的 `createArchive` 创建带声明字节长度的待上传归档（`hosts/common/operit-host-native-storage/src/lib.rs:367`）。
NativeArchiveStagingHost 的 `appendArchive` 追加分块时不允许超过声明字节长度（`hosts/common/operit-host-native-storage/src/lib.rs:423`）。
NativeArchiveStagingHost 的 `sealArchive` 校验实际长度等于声明长度后把上传文件重命名为密封文件（`hosts/common/operit-host-native-storage/src/lib.rs:457`）。
NativeArchiveStagingHost 的 `writeExportArchive` 单块写入上限为 64 KiB（`hosts/common/operit-host-native-storage/src/lib.rs:378`）。
NativeArchiveStagingHost 的 `archiveFileReference` 只对已密封归档返回文件引用（`hosts/common/operit-host-native-storage/src/lib.rs:405`）。
NativeRuntimeStorageHost 的 `openSqliteDatabase` 在存储根下打开 SQLite 数据库（`hosts/common/operit-host-native-storage/src/lib.rs:1009`）。
SQLite 事务用 `Immediate` 行为先占写锁再读（`hosts/common/operit-host-native-storage/src/lib.rs:1082`）。
`NativeFileSecretStore` 由 storage crate 从 `secrets` 子模块重导出（`hosts/common/operit-host-native-storage/src/lib.rs:2`）。

### 终端与托管运行时

共享 PTY 宿主自报平台 `posix`、终端 `native`、默认类型 `bash`（`hosts/common/operit-host-native-terminal/src/lib.rs:26`）。
PTY 输出上限为 16 MiB（`hosts/common/operit-host-native-terminal/src/lib.rs:22`）。
NativePtyTerminalHost 的 `systemShell` 启动系统 `/bin/sh` 终端（`hosts/common/operit-host-native-terminal/src/lib.rs:223`）。
NativePtyTerminalHost 的 `customShell` 用 `NativePtyShellCommand` 配置启动一个显式 POSIX shell（`hosts/common/operit-host-native-terminal/src/lib.rs:231`）。
NativePtyTerminalHost 的 `loginShell` 创建带登录启动参数的原生 shell（`hosts/common/operit-host-native-terminal/src/lib.rs:251`）。
NativePtyTerminalHost 的 `withControllingTty` 选择 PTY 是否成为子进程的控制终端（`hosts/common/operit-host-native-terminal/src/lib.rs:245`）。
NativePtyTerminalHost 的 `probe` 以 1 行 1 列启动并关闭会话验证能力（`hosts/common/operit-host-native-terminal/src/lib.rs:272`）。
NativePtyTerminalHost 的 `executeHiddenCommand` 按执行器键复用隐藏会话（`hosts/common/operit-host-native-terminal/src/lib.rs:601`）。
NativePtyTerminalHost 的 `getSessionScreen` 返回渲染后的屏幕文本与行列数（`hosts/common/operit-host-native-terminal/src/lib.rs:676`）。
`requireNativeTerminal` 只接受 `TERMINAL` 终端实现（`hosts/common/operit-host-native-terminal/src/lib.rs:1602`）。
`ptyCommandInput` 先经 `posixCommandLine` 编码命令再按协议追加完成标记（`hosts/common/operit-host-native-terminal/src/lib.rs:848`）。
超时取消的安顿等待为 3000 毫秒（`hosts/common/operit-host-native-terminal/src/lib.rs:25`）。
`TerminalManagedRuntimeLaunch` 描述经指定终端启动的托管运行时程序（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:17`）。
`TerminalManagedRuntimeProcess` 把终端 PTY 会话适配为 `ManagedRuntimeProcess`（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:29`）。
托管运行时 PTY 会话以 `MANAGED_RUNTIME_ROWS` 行、`MANAGED_RUNTIME_COLUMNS` 列创建（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:51`）。
托管运行时启动超时为 30 秒（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:12`）。
托管运行时终端输出上限为 8 MiB（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:13`）。
托管运行时启动命令以 `stty -echo` 开头并打印就绪标记（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:276`）。
托管运行时启动命令最后以 `exec` 替换 shell 执行程序（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:286`）。
TerminalManagedRuntimeProcess 的 `waitForExit` 轮询 PTY 退出码并返回精确退出码（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:77`）。
TerminalManagedRuntimeProcess 的 `drainStderr` 返回空字符串，因为 PTY 合并传输两个终端流（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:239`）。

### 调度器与插件 SDK IPC

scheduler crate 默认启用 `javascript` feature（`hosts/common/operit-host-native-scheduler/Cargo.toml:9`）。
`NativeHostJavaScriptRuntimeHost` 由 `javascript` feature 门控导出（`hosts/common/operit-host-native-scheduler/src/lib.rs:15`）。
`NativeHostRuntimeEventSchedulerHost` 不经 `javascript` 门控导出（`hosts/common/operit-host-native-scheduler/src/lib.rs:16`）。
`NativeHostRuntimeTaskSchedulerHost` 不经 `javascript` 门控导出（`hosts/common/operit-host-native-scheduler/src/lib.rs:17`）。
`scheduleNativeBlockingTask`、`scheduleNativeServiceTask`、`scheduleNativeServiceTasks` 与 `NativeTaskHandle` 由 `task_handle` 模块导出（`hosts/common/operit-host-native-scheduler/src/lib.rs:31`）。
`LocalHostRuntimeTaskSchedulerHost` 与 `DEVICE_ASYNC_STACK_BYTES`、`DEVICE_BLOCKING_STACK_BYTES` 由 `local_task_scheduler` 模块导出（`hosts/common/operit-host-native-scheduler/src/lib.rs:26`）。
`withStackBudget` 由 `esp32-compat` feature 门控导出（`hosts/common/operit-host-native-scheduler/src/lib.rs:22`）。
`PLUGIN_SDK_IPC_MAX_FRAME_BYTES` 与帧读写函数由 `framing` 模块导出（`hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs:8`）。
`MemoryPluginSdkIpcHost` 由 `memory` 模块导出（`hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs:9`）。
`pipes` 与 `stream` 是 plugin-sdk-ipc 的公开子模块（`hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs:5`）。
`pluginSdkIpcInstanceName` 给实例名加十六进制后缀，空实例保持原地址（`hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs:13`）。

### TCP、串口、服务发现与 Dart 共享缓冲

`ControlIo` 要求 `AsyncRead`、`AsyncWrite`、`Unpin` 与 `Send`（`hosts/common/operit-host-native-common/src/DaemonHost.rs:6`）。
`ControlStream` 是 `Box<dyn ControlIo>` 类型别名（`hosts/common/operit-host-native-common/src/DaemonHost.rs:10`）。
NativeTcpHost 的 `connect` 用 `TcpStream::connect` 建立连接（`hosts/common/operit-host-native-common/src/Tcp.rs:13`）。
NativeTcpHost 的 `bind` 绑定监听地址并返回实际本地地址（`hosts/common/operit-host-native-common/src/Tcp.rs:20`）。
`NativeTcpConnection` 持有拆分后的读半部、写半部与关闭信号（`hosts/common/operit-host-native-common/src/Tcp.rs:37`）。
TCP 读取用 1024 字节暂存并只分配已接收的字节（`hosts/common/operit-host-native-common/src/Tcp.rs:85`）。
NativeSerialPortHost 的 `open` 要求端口非空且波特率非零（`hosts/common/operit-host-native-common/src/SerialPort.rs:19`）。
NativeSerialPortHost 的 `open` 打开串口时不主动拉高 DTR（`hosts/common/operit-host-native-common/src/SerialPort.rs:21`）。
Windows 打开串口时把波特率写入 DCB 的 `BaudRate`（`hosts/common/operit-host-native-common/src/SerialPort.rs:90`）。
Windows 串口打开遇 `PermissionDenied` 最多重试 4 次（`hosts/common/operit-host-native-common/src/SerialPort.rs:41`）。
`readUartChunk` 每次最多读入 4096 字节（`hosts/common/operit-host-native-common/src/SerialPort.rs:270`）。
`NetworkLeaseFactory` 是返回 `HostResult<Box<dyn Send + Sync>>` 的函数指针（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:16`）。
`ServiceDiscoveryProvider` 为每种服务类型保存一个共享 `Browser`（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:158`）。
ServiceDiscoveryProvider 的 `supportsAdvertisement` 返回 true（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:373`）。
ServiceDiscoveryProvider 的 `advertise` 发布 Host 拥有的局域网服务广告（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:378`）。
ServiceDiscoveryProvider 的 `discover` 要求 `timeoutMs` 为正（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:403`）。
ServiceDiscoveryProvider 的 `subscribe` 接受 `DiscoveryCallback` 并返回订阅句柄（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:424`）。
ServiceDiscoveryProvider 的 `localAddresses` 返回本机接口地址（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:368`）。
`localNetworkAddresses` 枚举接口地址并排序去重（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:627`）。
mDNS 后台错误由 `operit-discovery-monitor` 任务监听并记录（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:97`）。
`SharedBuffer` 用 `Bytes` 保存不可变字节并记录 `sealed` 状态（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:6`）。
SharedBuffer 的 `sealed` 创建已密封的共享缓冲（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:14`）。
SharedBuffer 的 `retain` 断言指针非空且已密封后克隆 `Bytes`（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:23`）。
`shared_allocate` 分配可变入站缓冲、初始未密封（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:44`）。
`shared_seal` 把入站缓冲发布为不可变共享存储（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:67`）。
`shared_release` 释放一个共享缓冲句柄（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:76`）。
`shared_data` 只在缓冲未密封时暴露可写存储（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:58`）。

### 共享实现与平台实现的分界线

共享实现以 trait 实现形态提供能力，平台 Host 持有并组装这些实现（`hosts/android/src/filesystem.rs:14`）。
Android 的 HTTP 实现内部持有 `operit_host_native_common::NativeHttpHost`，Android 侧见 [[host-android|Android Host]]（`hosts/android/src/http.rs:11`）。
iOS 的终端实现引用 `operit_host_native_common::NativePtyTerminalHost`，iOS 侧见 [[host-ios|iOS Host]]（`hosts/ios/src/terminal.rs:11`）。
PosixFileSystemHost 的 `openFile` 报错，共享 POSIX 文件宿主不拥有平台 `open_file`（`hosts/common/operit-host-native-filesystem/src/lib.rs:539`）。
PosixFileSystemHost 的 `shareFile` 报错，共享 POSIX 文件宿主不拥有平台 `share_file`（`hosts/common/operit-host-native-filesystem/src/lib.rs:545`）。
平台专属的 IPC 传输不在共享 crate 里，plugin-sdk-client 在 Windows 上引入 `../../windows/src/plugin_sdk_ipc.rs`（`hosts/plugin-sdk-client/src/lib.rs:7`）。
plugin-sdk-client 在 Linux 上引入 `../../linux/src/plugin_sdk_ipc.rs`（`hosts/plugin-sdk-client/src/lib.rs:12`）。
plugin-sdk-client 在 Android 上引入 `../../android/src/plugin_sdk_ipc.rs`（`hosts/plugin-sdk-client/src/lib.rs:17`）。
plugin-sdk-client 在 macOS 与 iOS 上引入 `../../apple/src/plugin_sdk_ipc.rs`（`hosts/plugin-sdk-client/src/lib.rs:22`）。
`createPluginSdkHost` 按目标平台选择平台 IPC 宿主（`hosts/plugin-sdk-client/src/lib.rs:28`）。
非 Android 上 `registerAndroidClient` 报错（`hosts/plugin-sdk-client/src/lib.rs:40`）。
Android 上 `registerAndroidClient` 注册 SDK 提供的激活客户端（`hosts/plugin-sdk-client/src/lib.rs:34`）。

### 顶层源文件：为什么不是 crate

`chromium_browser.rs` 是 hosts/common 下的顶层源文件，各平台 Host 以 #[path] 直接包含编译（`hosts/apple/src/lib.rs:4`）。
`terminal_command.rs` 是 hosts/common 下的顶层源文件，各平台 Host 与 terminal crate 以 #[path] 直接包含编译（`hosts/android/src/lib.rs:32`）。
Apple 的 macOS 目标以 #[path] 把 `../../common/chromium_browser.rs` 编为 `chromium_browser` 模块（`hosts/apple/src/lib.rs:4`）。
Linux 以 #[path] 把 `../../common/chromium_browser.rs` 编为 `chromium_browser` 模块（`hosts/linux/src/lib.rs:18`）。
Windows 以 #[path] 把 `../../common/chromium_browser.rs` 编为 `chromium_browser` 模块（`hosts/windows/src/lib.rs:7`）。
Android 以 #[path] 把 `../../common/terminal_command.rs` 编为 `terminal_command` 模块（`hosts/android/src/lib.rs:32`）。
Windows 终端工具以 #[path] 把 `../../../../common/terminal_command.rs` 编为 `terminal_command` 模块（`hosts/windows/src/tools/terminal/mod.rs:3`）。
terminal crate 以 #[path] 把 `../../terminal_command.rs` 编为 `terminal_command` 模块（`hosts/common/operit-host-native-terminal/src/lib.rs:1`）。
`posixCommandLine` 只在命令含控制字符或 `!` 时才编码（`hosts/common/terminal_command.rs:7`）。
编码后的命令以 `eval` 加 `printf '%b'` 的形式提交（`hosts/common/terminal_command.rs:29`）。
`ptyCommandInput` 先经 `posixCommandLine` 编码命令再按协议追加完成标记（`hosts/common/operit-host-native-terminal/src/lib.rs:848`）。

### Chromium 浏览器自动化

`visit_with_chromium` 分配调试端口、建临时 profile、启动浏览器、跑 CDP 访问后清理（`hosts/common/chromium_browser.rs:21`）。
`spawn_browser` 接收候选浏览器列表、调试端口与 profile 目录（`hosts/common/chromium_browser.rs:1040`）。
启动候选浏览器时传 `--headless` 参数（`hosts/common/chromium_browser.rs:1050`）。
远程调试地址绑在 `127.0.0.1`（`hosts/common/chromium_browser.rs:1055`）。
临时 profile 目录位于系统临时目录下，目录名以 `operit2_browser_` 为前缀，后接进程号与毫秒时间戳（`hosts/common/chromium_browser.rs:1035`）。
`wait_for_browser` 轮询 DevTools 端点直到就绪或超时（`hosts/common/chromium_browser.rs:1110`）。
等待浏览器 DevTools 端点最多 10 秒（`hosts/common/chromium_browser.rs:1116`）。
`wait_for_document_ready` 最多等待 20 秒（`hosts/common/chromium_browser.rs:1303`）。
ChromiumBrowserAutomationHost 的 `executeBrowserTool` 按 `toolName` 分发浏览器工具（`hosts/common/chromium_browser.rs:188`）。
`browser_navigate` 分支取 `url` 参数并导航（`hosts/common/chromium_browser.rs:194`）。
导航后等待文档就绪并额外等待 500 毫秒（`hosts/common/chromium_browser.rs:348`）。
`browser_take_screenshot` 只支持 `png` 与 `jpeg` 两种格式（`hosts/common/chromium_browser.rs:705`）。
控制台与网络事件各保留最近 300 条（`hosts/common/chromium_browser.rs:2009`）。

### Unix daemon 传输与数据救援

`control_endpoint` 把控制套接字定为目录下的 `control.sock`，不使用身份哈希（`hosts/unix/daemon.rs:15`）。
`ensure_private_dir` 把目录权限设为 `0o700`（`hosts/unix/daemon.rs:22`）。
`private_open_options` 给新建守护进程文件设 `0o600` 权限（`hosts/unix/daemon.rs:28`）。
ControlListener 的 `bind` 绑定前清理陈旧端点（`hosts/unix/daemon.rs:48`）。
绑定的控制套接字权限为 `0o600`（`hosts/unix/daemon.rs:55`）。
`connect` 连接已存在的 Unix 域套接字并返回 `ControlStream`（`hosts/unix/daemon.rs:67`）。
`spawn_detached` 把子进程放入独立进程组（`hosts/unix/daemon.rs:73`）。
`termination_signal` 等待 SIGTERM 终止信号（`hosts/unix/daemon.rs:77`）。
`../tests/daemon.rs` 只在 `cfg(test)` 下经 #[path] 编入 unix daemon 测试（`hosts/unix/daemon.rs:86`）。
测试构造每客户端 256 KiB 以上的响应验证 Unix 传输（`hosts/tests/daemon.rs:69`）。
测试 `missing_endpoint_does_not_connect` 断言缺失端点的连接报错（`hosts/tests/daemon.rs:43`）。
测试 `endpoint_is_available_after_listener_drop` 断言监听器丢弃后同一端点可重新绑定（`hosts/tests/daemon.rs:50`）。
StorageLease 的 `acquire` 在维护模式取独占锁、在普通模式取共享锁（`hosts/common/operit-host-data-rescue/src/lib.rs:29`）。
普通启动时若 `data-rescue/commit.json` 存在则拒绝启动（`hosts/common/operit-host-data-rescue/src/lib.rs:39`）。
NativeRescueSession 的 `open` 不解析启动配置即取得独占维护访问（`hosts/common/operit-host-data-rescue/src/lib.rs:71`）。
NativeRescueSession 的 `open_file_secrets` 启用 CLI profile-file 密钥契约（`hosts/common/operit-host-data-rescue/src/lib.rs:78`）。
启动描述返回体中标注布局 `operit.files.v1`（`hosts/common/operit-host-data-rescue/src/lib.rs:119`）。
`NativeRescueHost` 的 `layout` 返回 `operit.files.v1`（`hosts/common/operit-host-data-rescue/src/lib.rs:601`）。
`RescueRoots` 包含 `runtime_root`、`workspace_root` 与可选的 `cli_config_root`（`hosts/common/operit-host-data-rescue/src/lib.rs:49`）。
`SECRET_KEYS` 只注册两项密钥（`hosts/common/operit-host-data-rescue/src/lib.rs:22`）。
`Journal` 记录 `publications`、`secret_envelope` 与 `verified_files`（`hosts/common/operit-host-data-rescue/src/lib.rs:217`）。
`Publication` 记录 `staged`、`retained` 与 `had_original`（`hosts/common/operit-host-data-rescue/src/lib.rs:208`）。
`save_journal` 把日志原子写入 `runtime/commit.json`（`hosts/common/operit-host-data-rescue/src/lib.rs:487`）。
NativeRescueHost 的 `commit_restore` 校验清单后写日志再发布（`hosts/common/operit-host-data-rescue/src/lib.rs:715`）。
NativeRescueHost 的 `resume_restore` 只恢复已持久化的发布计划（`hosts/common/operit-host-data-rescue/src/lib.rs:809`）。
NativeRescueHost 的 `discard_restore` 拒绝丢弃已发布导入的日志（`hosts/common/operit-host-data-rescue/src/lib.rs:855`）。
导出前若存在未完成导入，`list_files` 直接拒绝（`hosts/common/operit-host-data-rescue/src/lib.rs:615`）。

### 数据救援、CLI rescue 与 docs/data-rescue.md 的关系

数据救援入口独立运行，不依赖 Core、SQLite、插件加载、常规启动解析或用户偏好（`docs/data-rescue.md:3`）。
CLI 入口为 `operit2 rescue describe`、`export`、`inspect`、`import` 或 `resume`（`docs/data-rescue.md:14`）。
原生归档用 `operit.files.v1` 布局，浏览器存储用独立的 `operit.browser.v1` 布局（`docs/data-rescue.md:20`）。
原生与浏览器归档在本版本中故意不互通（`docs/data-rescue.md:30`）。
CLI rescue 入口不启动 Core、不打开 SQLite（`apps/cli/src/rescue.rs:1`）。
CLI rescue 帮助列出 describe、export、inspect、import、resume 五条命令（`apps/cli/src/rescue.rs:85`）。
CLI rescue 的 import 要求 `--confirm`（`apps/cli/src/rescue.rs:150`）。
CLI rescue 的 resume 要求 `--confirm`（`apps/cli/src/rescue.rs:157`）。
CLI rescue 的 describe 在无显式根时用 `NativeRescueSession::open` 打开默认运行时，CLI 侧见 [[app-cli|CLI]]（`apps/cli/src/rescue.rs:91`）。
operit-host-data-rescue 的 crate 文档称其为 `Native Host boundary for offline rescue`（`hosts/common/operit-host-data-rescue/src/lib.rs:1`）。

## 关键符号

- `operit-host-native-common` — 聚合入口 crate（`hosts/common/operit-host-native-common/Cargo.toml:2`）
- `PosixFileSystemHost` — 共享 POSIX 文件系统实现（`hosts/common/operit-host-native-filesystem/src/lib.rs:93`）
- `NativeFileAppendHandle` — 共享追加写文件句柄（`hosts/common/operit-host-native-filesystem/src/lib.rs:25`）
- `NativeHttpHost` — 共享 HTTP、WebSocket 与下载实现（`hosts/common/operit-host-native-http/src/lib.rs:31`）
- `NativeHttpServerHost` — 共享 HTTP 服务端实现（`hosts/common/operit-host-native-http/src/lib.rs:5`）
- `HttpClientPolicy` — HTTP 连接池策略标识（`hosts/common/operit-host-native-http/src/lib.rs:39`）
- `NativeRuntimeStorageHost` — 共享运行时存储实现（`hosts/common/operit-host-native-storage/src/lib.rs:21`）
- `NativeArchiveStagingHost` — 共享归档暂存实现（`hosts/common/operit-host-native-storage/src/lib.rs:367`）
- `NativeFileSecretStore` — 共享文件密钥库实现（`hosts/common/operit-host-native-storage/src/lib.rs:2`）
- `NativePtyTerminalHost` — 共享 POSIX PTY 终端实现（`hosts/common/operit-host-native-terminal/src/lib.rs:26`）
- `NativePtyShellCommand` — 显式 POSIX shell 配置（`hosts/common/operit-host-native-terminal/src/lib.rs:231`）
- `NativeHostJavaScriptRuntimeHost` — 共享 JS 运行时实现（`hosts/common/operit-host-native-scheduler/src/lib.rs:15`）
- `NativeHostRuntimeEventSchedulerHost` — 共享运行时事件调度器实现（`hosts/common/operit-host-native-scheduler/src/lib.rs:16`）
- `NativeHostRuntimeTaskSchedulerHost` — 共享运行时任务调度器实现（`hosts/common/operit-host-native-scheduler/src/lib.rs:17`）
- `scheduleNativeServiceTask` — 调度原生服务任务（`hosts/common/operit-host-native-scheduler/src/lib.rs:31`）
- `MemoryPluginSdkIpcHost` — 共享插件 SDK 内存 IPC 实现（`hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs:9`）
- `pluginSdkIpcInstanceName` — 插件 SDK IPC 实例名构造（`hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs:13`）
- `StorageLease` — 数据救援存储租约（`hosts/common/operit-host-data-rescue/src/lib.rs:29`）
- `NativeRescueSession` — 离线数据救援维护会话（`hosts/common/operit-host-data-rescue/src/lib.rs:71`）
- `RescueRoots` — 数据救援根目录选择（`hosts/common/operit-host-data-rescue/src/lib.rs:49`）
- `Journal` — 导入发布持久化日志（`hosts/common/operit-host-data-rescue/src/lib.rs:217`）
- `ChromiumBrowserAutomationHost` — 共享 Chromium 浏览器自动化实现（`hosts/common/chromium_browser.rs:34`）
- `visit_with_chromium` — 一次性 Chromium 访问（`hosts/common/chromium_browser.rs:21`）
- `posixCommandLine` — POSIX 交互式 shell 命令编码（`hosts/common/terminal_command.rs:7`）
- `ServiceDiscoveryProvider` — 共享 mDNS 服务发现实现（`hosts/common/operit-host-native-common/src/ServiceDiscovery.rs:158`）
- `NativeTcpHost` — 共享 TCP 实现（`hosts/common/operit-host-native-common/src/Tcp.rs:13`）
- `NativeSerialPortHost` — 共享串口实现（`hosts/common/operit-host-native-common/src/SerialPort.rs:19`）
- `SharedBuffer` — 原生 Rust 与 Dart 之间的共享二进制缓冲（`hosts/common/operit-host-native-common/src/SharedBuffer.rs:6`）
- `ControlIo` — 守护进程传输字节流契约（`hosts/common/operit-host-native-common/src/DaemonHost.rs:6`）
- `ControlStream` — 平台无关的本地守护进程字节流（`hosts/common/operit-host-native-common/src/DaemonHost.rs:10`）
- `ControlListener` — Unix 域套接字控制监听器（`hosts/unix/daemon.rs:48`）
- `TerminalManagedRuntimeProcess` — 经 PTY 启动的托管运行时进程（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:29`）
- `createPluginSdkHost` — 按目标平台创建插件 SDK IPC 宿主（`hosts/plugin-sdk-client/src/lib.rs:28`）

## 调用链

1. 平台 Host 启用 feature，得到 operit-host-native-common 重导出的共享实现（`hosts/common/operit-host-native-common/src/lib.rs:24`）。
2. Android 的 HTTP 实现内部持有 `operit_host_native_common::NativeHttpHost`，Android 侧见 [[host-android|Android Host]]（`hosts/android/src/http.rs:11`）。
3. NativeHttpHost 的 `executeHttpRequest` 经共享网络任务执行缓冲请求（`hosts/common/operit-host-native-http/src/lib.rs:422`）。
4. 连接池由 `HttpClientPolicy` 标识（`hosts/common/operit-host-native-http/src/lib.rs:39`）。
5. NativeHttpHost 的 `downloadToFile` 把响应流式下载到目标文件（`hosts/common/operit-host-native-http/src/lib.rs:430`）。
6. downloadToFileAsync 写完临时文件后重命名发布到目标路径（`hosts/common/operit-host-native-http/src/lib.rs:514`）。
7. 托管运行时由 `TerminalManagedRuntimeProcess` 把终端 PTY 会话适配为 `ManagedRuntimeProcess`（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:29`）。
8. 托管运行时 PTY 会话以 `MANAGED_RUNTIME_ROWS` 行、`MANAGED_RUNTIME_COLUMNS` 列创建（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:51`）。
9. 托管运行时启动命令以 `stty -echo` 开头并打印就绪标记（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:276`）。
10. 托管运行时启动超时为 30 秒（`hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs:12`）。
11. 数据救援由 NativeRescueSession 的 `open` 不解析启动配置即取得独占维护访问（`hosts/common/operit-host-data-rescue/src/lib.rs:71`）。
12. NativeRescueHost 的 `commit_restore` 校验清单后写日志再发布（`hosts/common/operit-host-data-rescue/src/lib.rs:715`）。
13. `save_journal` 把日志原子写入 `runtime/commit.json`（`hosts/common/operit-host-data-rescue/src/lib.rs:487`）。
14. 普通启动时若 `data-rescue/commit.json` 存在则拒绝启动（`hosts/common/operit-host-data-rescue/src/lib.rs:39`）。
15. 中断的导入由 NativeRescueHost 的 `resume_restore` 只恢复已持久化的发布计划（`hosts/common/operit-host-data-rescue/src/lib.rs:809`）。
16. CLI rescue 的 describe 在无显式根时用 `NativeRescueSession::open` 打开默认运行时，CLI 侧见 [[app-cli|CLI]]（`apps/cli/src/rescue.rs:91`）。
17. 浏览器访问由 `visit_with_chromium` 分配调试端口、建临时 profile、启动浏览器、跑 CDP 访问后清理（`hosts/common/chromium_browser.rs:21`）。
18. `wait_for_browser` 轮询 DevTools 端点直到就绪或超时（`hosts/common/chromium_browser.rs:1110`）。
19. `wait_for_document_ready` 最多等待 20 秒（`hosts/common/chromium_browser.rs:1303`）。
20. Unix daemon 由 `control_endpoint` 把控制套接字定为目录下的 `control.sock`（`hosts/unix/daemon.rs:15`）。
21. ControlListener 的 `bind` 绑定前清理陈旧端点（`hosts/unix/daemon.rs:48`）。
22. `connect` 连接已存在的 Unix 域套接字并返回 `ControlStream`（`hosts/unix/daemon.rs:67`）。
23. 插件 SDK IPC 由 `createPluginSdkHost` 按目标平台选择平台 IPC 宿主（`hosts/plugin-sdk-client/src/lib.rs:28`）。


## 来源

- `hosts/common/operit-host-native-common/src/lib.rs`
- `hosts/common/operit-host-native-common/src/DaemonHost.rs`
- `hosts/common/operit-host-native-common/src/ManagedRuntimePty.rs`
- `hosts/common/operit-host-native-common/src/SerialPort.rs`
- `hosts/common/operit-host-native-common/src/ServiceDiscovery.rs`
- `hosts/common/operit-host-native-common/src/SharedBuffer.rs`
- `hosts/common/operit-host-native-common/src/Tcp.rs`
- `hosts/common/operit-host-native-filesystem/src/lib.rs`
- `hosts/common/operit-host-native-http/src/lib.rs`
- `hosts/common/operit-host-native-storage/src/lib.rs`
- `hosts/common/operit-host-native-terminal/src/lib.rs`
- `hosts/common/operit-host-native-scheduler/src/lib.rs`
- `hosts/common/operit-host-native-plugin-sdk-ipc/src/lib.rs`
- `hosts/common/operit-host-data-rescue/src/lib.rs`
- `hosts/common/chromium_browser.rs`
- `hosts/common/terminal_command.rs`
- `hosts/unix/daemon.rs`
- `hosts/plugin-sdk-client/src/lib.rs`
- `hosts/tests/daemon.rs`
- `docs/data-rescue.md`
- `apps/cli/src/rescue.rs`
- `hosts/common/operit-host-native-common/Cargo.toml`
- `hosts/common/operit-host-native-filesystem/Cargo.toml`
- `hosts/common/operit-host-native-http/Cargo.toml`
- `hosts/common/operit-host-native-storage/Cargo.toml`
- `hosts/common/operit-host-native-terminal/Cargo.toml`
- `hosts/common/operit-host-native-scheduler/Cargo.toml`
- `hosts/common/operit-host-native-plugin-sdk-ipc/Cargo.toml`
- `hosts/common/operit-host-data-rescue/Cargo.toml`
- `hosts/apple/src/lib.rs`
- `hosts/linux/src/lib.rs`
- `hosts/windows/src/lib.rs`
- `hosts/android/src/lib.rs`
- `hosts/windows/src/tools/terminal/mod.rs`
- `hosts/android/src/http.rs`
- `hosts/android/src/filesystem.rs`
- `hosts/ios/src/terminal.rs`
