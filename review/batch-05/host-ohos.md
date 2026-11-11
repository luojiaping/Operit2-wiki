---
title: OpenHarmony Host
module: hosts
platforms: [ohos]
sources: [hosts/ohos/README.md, hosts/ohos/Cargo.toml, hosts/ohos/src/lib.rs, hosts/ohos/src/terminal.rs, hosts/ohos/src/managed_runtime.rs, hosts/ohos/src/filesystem.rs, hosts/ohos/src/documents.rs, hosts/ohos/src/storage.rs, hosts/ohos/src/http.rs, hosts/ohos/src/local_inference.rs, hosts/ohos/src/system_operation.rs, hosts/ohos/src/tts_playback.rs, hosts/ohos/src/audio_playback.rs, hosts/ohos/src/bluetooth.rs]
date: 2026-11-11
---

## 概述

`operit-host-ohos-native` 是 OpenHarmony 原生 Host 实现的 crate，拥有由 `target_env = "ohos"` 选中的 Rust Host 实现（`hosts/ohos/README.md:3`）。
crate 名为 `operit-host-ohos-native`（`hosts/ohos/Cargo.toml:2`）。
版本为 0.1.0（`hosts/ohos/Cargo.toml:3`）。
声明 `publish = false`，不对外发布（`hosts/ohos/Cargo.toml:6`）。
依赖项包括 `operit-host-api`（`hosts/ohos/Cargo.toml:9`）。
依赖项包括 `operit-host-native-common`，并启用 tcp、serial、fs、http、scheduler、storage、terminal 特性（`hosts/ohos/Cargo.toml:10`）。
依赖项包括 `operit-local-models`（`hosts/ohos/Cargo.toml:11`）。
依赖项包括 `libloading` 0.8（`hosts/ohos/Cargo.toml:13`）。
README 列出的初始能力包括 POSIX 应用文件访问（`hosts/ohos/README.md:9`）。
README 列出的初始能力包括原生 HTTP（`hosts/ohos/README.md:10`）。
README 列出的初始能力包括 runtime storage（`hosts/ohos/README.md:11`）。
README 列出的初始能力包括 SQLite storage（`hosts/ohos/README.md:12`）。
README 列出的初始能力包括 PTY 会话（`hosts/ohos/README.md:13`）。
README 列出的初始能力包括经 QEMU-vroot Alpine 的托管 Python、Node、uv、pnpm 运行时（`hosts/ohos/README.md:14`）。
README 列出的初始能力包括离线 Tesseract OCR 与 Poppler PDF 光栅化（`hosts/ohos/README.md:15`）。
README 列出的初始能力包括 Flutter 自有浏览器交互（`hosts/ohos/README.md:16`）。
README 列出的初始能力包括 Sherpa ONNX 本地推理（`hosts/ohos/README.md:17`）。
README 列出的初始能力包括 ArkTS AVPlayer 生成式 TTS 播放控制（`hosts/ohos/README.md:18`）。

## AI 速览

- `OhosTerminalHost` — OpenHarmony PTY 终端 Host（`hosts/ohos/src/terminal.rs:227`）
- `OhosVrootRuntime` — QEMU-vroot 运行时的路径与安装状态（`hosts/ohos/src/terminal.rs:39`）
- `OhosTerminalBackend` — 区分 NativeShell 与 QemuVroot 两种终端后端（`hosts/ohos/src/terminal.rs:33`）
- `OhosManagedRuntimeHost` — OpenHarmony 托管运行时 Host（`hosts/ohos/src/managed_runtime.rs:18`）
- `OhosFileSystemHost` — OpenHarmony 文件系统 Host（`hosts/ohos/src/filesystem.rs:13`）
- `OhosRuntimeStorageHost` — OpenHarmony 运行时存储 Host（`hosts/ohos/src/storage.rs:7`）
- `OhosHttpHost` — OpenHarmony HTTP Host（`hosts/ohos/src/http.rs:11`）
- `OhosLocalInferenceHost` — OpenHarmony 本地推理 Host（`hosts/ohos/src/local_inference.rs:14`）
- `OhosSystemOperationHost` — OpenHarmony 系统操作 Host（`hosts/ohos/src/system_operation.rs:18`）
- `OhosTtsPlaybackHost` — OpenHarmony TTS 播放 Host（`hosts/ohos/src/tts_playback.rs:17`）
- `OhosTtsPlaybackCommand` — 含 command 与 audioPath 两个字段（`hosts/ohos/src/tts_playback.rs:8`）
- `OhosAudioPlaybackHost` — OpenHarmony 音频播放 Host（`hosts/ohos/src/audio_playback.rs:22`）
- `OhosMusicCommand` — 音乐播放命令枚举（`hosts/ohos/src/audio_playback.rs:11`）
- `OhosBluetoothHost` — OpenHarmony 蓝牙 Host（`hosts/ohos/src/bluetooth.rs:17`）
- 主入口函数是 `createRuntimeHostManager`，接受显式的 `runtimeRoot` 与 `workspaceRoot`（`hosts/ohos/src/lib.rs:44`）
- 数据流向：调用方显式传入存储根目录，`createRuntimeHostManager` 组装 `HostManager`（`hosts/ohos/src/lib.rs:44`）

## 核心机制

### README 的不宣称项：系统 TTS

API 18 SDK 不暴露公开系统文本转语音合成 API（`hosts/ohos/README.md:28`）。
OHOS Host 不宣称 `SYSTEM_TTS`（`hosts/ohos/README.md:30`）。
`supportsSystemSpeech` 返回 false（`hosts/ohos/src/tts_playback.rs:38`）。
`speakText` 返回 API 18 不提供系统 TTS 合成 Host 的错误（`hosts/ohos/src/tts_playback.rs:52`）。

### Host 组装与显式存储根

`newOhosFileSystemHost` 创建 `OhosFileSystemHost`（`hosts/ohos/src/lib.rs:38`）。
`createRuntimeHostManager` 接受显式的 `runtimeRoot` 与 `workspaceRoot`（`hosts/ohos/src/lib.rs:44`）。
OpenHarmony 应用存储根目录须传给 `operit_flutter_bridge_create_with_storage_roots_and_system_language`（`hosts/ohos/README.md:22`）。
通用 bridge 创建函数不选择应用路径（`hosts/ohos/README.md:23`）。
`NativeArchiveStagingHost` 以 `runtimeRoot` 创建（`hosts/ohos/src/lib.rs:55`）。
`OhosRuntimeStorageHost` 由 `runtimeRoot` 与 `workspaceRoot` 创建（`hosts/ohos/src/lib.rs:63`）。
`runtimeSqliteHost` 是 `runtimeStorageHost` 的 clone（`hosts/ohos/src/lib.rs:64`）。
系统操作 Host 由 `fromOwnerCallbacks` 从语言读取、截图、文本识别与系统控制四个所有者回调构造（`hosts/ohos/src/lib.rs:65`）。
`HostManager` 由 `withFileSystemWebVisitAndSystemOperationHosts` 组装文件系统、网页访问与系统操作 Host（`hosts/ohos/src/lib.rs:71`）。
`context.httpHost` 是 `OhosHttpHost` 的 new 结果（`hosts/ohos/src/lib.rs:78`）。
`context.httpServerHost` 是 `NativeHttpServerHost`（`hosts/ohos/src/lib.rs:79`）。
`context.tcpHost` 是 `NativeTcpHost`（`hosts/ohos/src/lib.rs:80`）。
`context.serialPortHost` 是 `NativeSerialPortHost`（`hosts/ohos/src/lib.rs:81`）。
`context.webSocketHost` 是 `OhosHttpHost` 的 new 结果（`hosts/ohos/src/lib.rs:82`）。
`context.managedRuntimeHost` 取调用方传入的 `managedRuntimeHost`（`hosts/ohos/src/lib.rs:83`）。
运行时组合以 `withLocalInferenceHost` 注册 `OhosLocalInferenceHost` 的 new 结果（`hosts/ohos/src/lib.rs:88`）。
服务发现 Host 是 `ServiceDiscoveryProvider` 的 default 结果（`hosts/ohos/src/lib.rs:93`）。
`OhosHostJavaScriptRuntimeHost` 是 `NativeHostJavaScriptRuntimeHost` 的重导出（`hosts/ohos/src/lib.rs:26`）。
`OhosHostRuntimeTaskSchedulerHost` 是 `NativeHostRuntimeTaskSchedulerHost` 的重导出（`hosts/ohos/src/lib.rs:28`）。

### 终端：两种后端

终端 Host 的 `PLATFORM` 为 `ohos`（`hosts/ohos/src/terminal.rs:18`）。
`backendForTerminal` 只接受 native 与 shell、qemu-vroot 与 shell 两组实现与类型配对（`hosts/ohos/src/terminal.rs:248`）。
QEMU-vroot 可执行文件路径为 `/data/app/bin/qemu-harmonix-aarch64`（`hosts/ohos/src/terminal.rs:22`）。
`OhosTerminalHost` 的 `new` 接受显式的 runtimeRoot 与 workspaceRoot（`hosts/ohos/src/terminal.rs:236`）。
`OhosTerminalHost` 以 `sessionBackends` 记录每个会话的后端（`hosts/ohos/src/terminal.rs:231`）。
`terminalInfo` 把 qemu-vroot 列为默认终端（`hosts/ohos/src/terminal.rs:343`）。
qemu-vroot 条目 available 取 `isAvailable` 的结果（`hosts/ohos/src/terminal.rs:349`）。
native 条目 available 取 `/bin/sh` 是否存在（`hosts/ohos/src/terminal.rs:355`）。
`isAvailable` 要求 qemu-vroot 可执行文件、rootfs 归档与校验和文件三者都存在（`hosts/ohos/src/terminal.rs:81`）。
`startPtySession` 对 qemu-vroot 要求工作目录为绝对路径（`hosts/ohos/src/terminal.rs:376`）。
qemu-vroot 工作目录解析把原生目录映射为 `VROOT_HOST_MOUNT_ROOT` 前缀的 guest 路径（`hosts/ohos/src/terminal.rs:332`）。
`createOrGetTypedSession` 固定走 `QEMU_VROOT_TERMINAL` 后端（`hosts/ohos/src/terminal.rs:450`）。
`executeHiddenCommand` 固定走 QemuVroot 后端（`hosts/ohos/src/terminal.rs:487`）。
`listSessions` 合并 native 与 vroot 两路会话并逐条记录后端（`hosts/ohos/src/terminal.rs:424`）。
`closePtySession` 关闭 PTY 后移除会话后端记录（`hosts/ohos/src/terminal.rs:417`）。

### QEMU-vroot Alpine rootfs：校验、安装与更新

打包的 Alpine rootfs 目录名为 `alpine-3.23.6-aarch64`（`hosts/ohos/src/terminal.rs:25`）。
打包的 Alpine rootfs 归档名为 `alpine-minirootfs-3.23.6-aarch64.tar.gz`（`hosts/ohos/src/terminal.rs:26`）。
安装标记文件名为 `.operit-rootfs.sha256`（`hosts/ohos/src/terminal.rs:28`）。
Host 根挂载点 `VROOT_HOST_MOUNT_ROOT` 为 `/mnt/host-root`（`hosts/ohos/src/terminal.rs:30`）。
`ensureReady` 在 vroot 会话启动前提取 checksum 验证的 Alpine rootfs（`hosts/ohos/src/terminal.rs:88`）。
归档安装前由 `verifyRootfsArchiveSha256` 校验归档 SHA-256（`hosts/ohos/src/terminal.rs:114`）。
`readRootfsSha256` 要求校验和为 64 位十六进制字符并转小写（`hosts/ohos/src/terminal.rs:623`）。
终端从 checksum 验证的离线 Alpine 仓库安装打包的包（`hosts/ohos/README.md:32`）。
打包安装经 apk 以 `--no-network` 离线运行（`hosts/ohos/src/terminal.rs:169`）。
rootfs 不存在时 payload 直接改名为 rootfs（`hosts/ohos/src/terminal.rs:156`）。
已存在 rootfs 时安装经 apk 做 add --upgrade，不替换用户 rootfs（`hosts/ohos/src/terminal.rs:180`）。
更新对已有 rootfs 运行 apk，用户安装的包与文件保留（`hosts/ohos/README.md:33`）。
安装后经 ./bin/busybox --install -s 安装 shell 命令（`hosts/ohos/src/terminal.rs:198`）。
宿主 asset 目录的 `resolv.conf` 不存在时创建空文件，guest 的 `etc/resolv.conf` 换成指向它的符号链接（`hosts/ohos/src/terminal.rs:208`）。
Guest DNS 由活动 OHOS 所有者网络提供（`hosts/ohos/README.md:34`）。
安装完成时把校验和写入 `VROOT_INSTALL_MARKER` 的 installing 临时文件再改名为安装标记（`hosts/ohos/src/terminal.rs:218`）。
安装期间校验归档哈希与包载荷，就绪结果由当前进程的终端实例共享（`hosts/ohos/README.md:35`）。
`verifyRootfsPayload` 要求 rootfs 内存在 `bin/busybox`、`sbin/apk`、`usr/bin/python3`、`usr/bin/node`、`usr/bin/uv`、`usr/bin/pnpm`、`usr/bin/tesseract`、`usr/bin/pdftoppm`（`hosts/ohos/src/terminal.rs:690`）。
`createVrootShell` 为 QEMU-vroot Alpine 创建 PTY 启动器（`hosts/ohos/src/terminal.rs:530`）。
vroot shell 在 guest 内执行 cd "$OPERIT_OHOS_HOST_WORKING_DIR" && exec /bin/sh -i（`hosts/ohos/src/terminal.rs:546`）。
vroot 会话默认工作目录为 `VROOT_HOST_MOUNT_ROOT` 拼接 workspaceRoot（`hosts/ohos/src/terminal.rs:550`）。

### 托管运行时：路径映射

`OhosManagedRuntimeHost` 的 `new` 接受终端 Host 与 workspaceRoot（`hosts/ohos/src/managed_runtime.rs:25`）。
托管运行时启动目标的终端为 `QEMU_VROOT_TERMINAL`，类型为 `SHELL_TERMINAL_TYPE`（`hosts/ohos/src/managed_runtime.rs:55`）。
请求未指定 cwd 时宿主工作目录取 workspaceRoot（`hosts/ohos/src/managed_runtime.rs:45`）。
`vrootHostPath` 要求 MCP 工作目录为绝对路径（`hosts/ohos/src/managed_runtime.rs:80`）。
宿主绝对路径映射为 `VROOT_HOST_MOUNT_ROOT` 前缀的 guest 路径（`hosts/ohos/src/managed_runtime.rs:87`）。
`mapVrootPath` 把宿主工作目录下的路径映射为 guest 挂载路径（`hosts/ohos/src/managed_runtime.rs:91`）。
`mapVrootEnvironment` 对每个环境变量值做同样的路径映射（`hosts/ohos/src/managed_runtime.rs:102`）。
`runtimeWorkspaceDir` 位于 workspaceRoot 下的 `.operit` 与 `managed_runtime` 两级目录并创建目录（`hosts/ohos/src/managed_runtime.rs:116`）。
`resolveRuntimeExecutable` 在显式 executablePath 非空时使用该路径（`hosts/ohos/src/managed_runtime.rs:122`）。
默认可执行文件为 Node 的 `/usr/bin/node`、Python 的 `/usr/bin/python3`、Uv 的 `/usr/bin/uv`、Pnpm 的 `/usr/bin/pnpm`（`hosts/ohos/src/managed_runtime.rs:134`）。
`ManagedRuntimeProgram::Command` 按名字原样作可执行文件（`hosts/ohos/src/managed_runtime.rs:138`）。
`runRuntimeCommand` 在 QEMU-vroot Alpine 内运行一次性命令并等待退出（`hosts/ohos/src/managed_runtime.rs:151`）。
一次性运行时命令结果的 `stderr` 为空字符串（`hosts/ohos/src/managed_runtime.rs:161`）。

### 文件系统与存储

`OhosFileSystemHost` 内部包装 `PosixFileSystemHost`，环境为 ohos（`hosts/ohos/src/filesystem.rs:23`）。
`fromPlatformActions` 接受 opener 与 sharer 两个平台回调（`hosts/ohos/src/filesystem.rs:33`）。
`validateReadableFile` 要求路径存在且为文件（`hosts/ohos/src/filesystem.rs:45`）。
`openFile` 在未注册 opener 时返回 file opener 未注册错误（`hosts/ohos/src/filesystem.rs:181`）。
`shareFile` 在未注册 sharer 时返回 file sharer 未注册错误（`hosts/ohos/src/filesystem.rs:191`）。
`OhosRuntimeStorageHost` 包装 `NativeRuntimeStorageHost` 并以 `delegate_runtime_storage` 委派（`hosts/ohos/src/storage.rs:11`）。
`OhosRuntimeStorageHost` 的 `new` 接受 runtimeRoot 与 workspaceRoot（`hosts/ohos/src/storage.rs:15`）。
`OhosHttpHost` 内部包装 `NativeHttpHost`（`hosts/ohos/src/http.rs:12`）。
`executeHttpRequest` 经 OpenHarmony 原生网络栈执行 HTTP 请求（`hosts/ohos/src/http.rs:67`）。
`openWebSocket` 经共享原生 Host 打开 OpenHarmony WebSocket（`hosts/ohos/src/http.rs:95`）。

### 文档：离线 OCR 与 PDF 光栅化

离线 OCR 回调由 OHOS Host 组装固定，而非不可用的原生 OCR 方法（`hosts/ohos/README.md:41`）。
文档工具调用经 `executeHiddenCommand` 执行，executorKey 为 ohos-documents，超时 120_000 毫秒（`hosts/ohos/src/documents.rs:23`）。
`runTool` 在超时或非零退出时返回含退出码与输出的错误（`hosts/ohos/src/documents.rs:22`）。
OCR 经 guest 内 `/usr/bin/tesseract` 离线识别，线程限制为 2，模式为 `--psm 3`（`hosts/ohos/src/documents.rs:62`）。
中文高质 OCR 语言为 `chi_sim+chi_tra+eng`（`hosts/ohos/src/documents.rs:47`）。
中文低质 OCR 语言仅为 `chi_sim`（`hosts/ohos/src/documents.rs:56`）。
拉丁语 OCR 语言为 eng，日语高质为 `jpn+eng`，韩语高质为 `kor+eng`（`hosts/ohos/src/documents.rs:48`）。
`guestPath` 把规范化后的绝对路径加 `VROOT_HOST_MOUNT_ROOT` 前缀（`hosts/ohos/src/documents.rs:16`）。
PDF 预览使用已有打印光栅通道与同一终端 Host，共享 Dart 无平台条件（`hosts/ohos/README.md:39`）。
PDF 光栅化 dpi 为 scale 乘 72（`hosts/ohos/src/documents.rs:75`）。
PDF 光栅化结果从 `pages.json` 读取有序 PNG 名（`hosts/ohos/src/documents.rs:111`）。
`renderPdf` 要求 scale 有限且为正（`hosts/ohos/src/documents.rs:92`）。

### 本地推理：Sherpa ONNX

OHOS 本地推理加载 checksum 验证的 Sherpa ONNX 引擎，该引擎由本地模型注册表选中并来自已安装运行时目录（`hosts/ohos/README.md:25`）。
`OhosLocalInferenceHost` 的 `new` 创建无状态 OHOS 本地推理 Host（`hosts/ohos/src/local_inference.rs:18`）。
本地推理经 `libloading` 的 `Library` 动态加载 Sherpa 库（`hosts/ohos/src/local_inference.rs:7`）。
`loadSherpaLibraries` 先加载 `libonnxruntime.so` 再加载 `libsherpa-onnx-c-api.so`（`hosts/ohos/src/local_inference.rs:746`）。
本地推理线程数上限为 4（`hosts/ohos/src/local_inference.rs:919`）。
`transcribeLocalSpeech` 经 `transcribeStreamingTransducer` 处理（`hosts/ohos/src/local_inference.rs:25`）。
STT 请求的驱动须为 `SherpaOnnxStreamingTransducer`（`hosts/ohos/src/local_inference.rs:315`）。
STT 特征采样率为 16_000，特征维为 80（`hosts/ohos/src/local_inference.rs:340`）。
STT 解码方法为 `greedy_search`（`hosts/ohos/src/local_inference.rs:334`）。
STT 推理 provider 为 cpu（`hosts/ohos/src/local_inference.rs:333`）。
STT 的 `max_active_paths` 为 4，`enable_endpoint` 为 0（`hosts/ohos/src/local_inference.rs:373`）。
`synthesizeLocalSpeech` 经 `synthesizeTts` 处理（`hosts/ohos/src/local_inference.rs:33`）。
TTS 合成要求文本非空（`hosts/ohos/src/local_inference.rs:791`）。
TTS 合成语速须有限且为正（`hosts/ohos/src/local_inference.rs:800`）。
`validateTtsSpeakerId` 要求 speaker 在 0 到 speakerCount 减 1 之间（`hosts/ohos/src/local_inference.rs:820`）。
TTS 驱动除 Vits、Matcha、Kitten 外均返回不支持错误（`hosts/ohos/src/local_inference.rs:576`）。
TTS 合成在引擎 `speakerCount` 与 manifest 不一致时报错（`hosts/ohos/src/local_inference.rs:704`）。
TTS 输出文件须不存在，父目录须存在（`hosts/ohos/src/local_inference.rs:893`）。
TTS 输出文件长度不超过 44 字节时判为无效 WAV（`hosts/ohos/src/local_inference.rs:583`）。
TTS 响应 `outputFormat` 为 wav（`hosts/ohos/src/local_inference.rs:591`）。
声明的模型文件逃逸模型目录时报错（`hosts/ohos/src/local_inference.rs:861`）。

### 语音分工：合成、播放与系统 TTS 缺位

TTS 提供方经 Core 生成 runtime storage 音频，一个 ArkTS `AVPlayer` 拥有播放、暂停、恢复、停止与状态查询（`hosts/ohos/README.md:27`）。
`OhosTtsPlaybackHost` 的 `new` 接受所有者 AVPlayer 控制器（`hosts/ohos/src/tts_playback.rs:22`）。
`playAudio` 以 play 命令发送音频路径（`hosts/ohos/src/tts_playback.rs:43`）。
`playAudio` 在音频路径为空时报错（`hosts/ohos/src/tts_playback.rs:43`）。
`pauseSpeech` 以 pause 命令暂停当前语音会话（`hosts/ohos/src/tts_playback.rs:59`）。
`resumeSpeech` 以 resume 命令恢复当前语音会话（`hosts/ohos/src/tts_playback.rs:64`）。
`stopSpeech` 以 stop 命令停止当前语音会话（`hosts/ohos/src/tts_playback.rs:69`）。
`speechState` 以 state 命令查询当前语音会话状态（`hosts/ohos/src/tts_playback.rs:74`）。
通用 Flutter 音频 widgets 使用所有者 audioplayers 协议适配器（`hosts/ohos/README.md:38`）。
`OhosAudioPlaybackHost` 由 `fromPlayers` 从音频播放器与音乐播放器两个所有者回调构造（`hosts/ohos/src/audio_playback.rs:29`）。
`playAudio` 经 player 回调播放本地音频文件（`hosts/ohos/src/audio_playback.rs:39`）。
`playMusic` 以 `OhosMusicCommand::Play` 发送音乐播放请求（`hosts/ohos/src/audio_playback.rs:45`）。
`musicStatus` 以 `OhosMusicCommand::Status` 查询音乐播放状态（`hosts/ohos/src/audio_playback.rs:75`）。
`OhosMusicCommand` 含 Play、Pause、Resume、Stop、Seek、SetVolume、Status 七个变体（`hosts/ohos/src/audio_playback.rs:13`）。

### 系统操作与蓝牙：所有者回调

`OhosSystemOperationHost` 由 `fromOwnerCallbacks` 从四个所有者回调构造（`hosts/ohos/src/system_operation.rs:27`）。
OhosSystemOperationHost 的 `execute` 把操作名与参数交给 controller 回调（`hosts/ohos/src/system_operation.rs:41`）。
`getSystemLanguageCode` 经 languageReader 读取系统语言代码（`hosts/ohos/src/system_operation.rs:250`）。
`captureScreenshot` 经 screenshotCapturer 截图（`hosts/ohos/src/system_operation.rs:368`）。
`recognizeText` 经文本识别回调执行（`hosts/ohos/src/system_operation.rs:373`）。
`installApp` 要求 Immediate 安装时机（`hosts/ohos/src/system_operation.rs:290`）。
`sendNotification` 以 `send_notification` 操作执行（`hosts/ohos/src/system_operation.rs:255`）。
`getDeviceInfo` 以 `device_info` 操作执行（`hosts/ohos/src/system_operation.rs:363`）。
`OhosBluetoothHost` 由 `fromController` 从平台所有者回调构造（`hosts/ohos/src/bluetooth.rs:26`）。
OhosBluetoothHost 的 `execute` 把命令与参数交给 controller 回调并解码响应（`hosts/ohos/src/bluetooth.rs:28`）。
`supportsClassicListening` 返回 true（`hosts/ohos/src/bluetooth.rs:52`）。
`requestBluetoothPermission` 以 `request_permission` 命令请求蓝牙权限（`hosts/ohos/src/bluetooth.rs:55`）。
`bluetoothState` 以 `state` 命令查询蓝牙状态（`hosts/ohos/src/bluetooth.rs:60`）。
`scanBluetoothDevices` 以 `scan` 命令扫描蓝牙设备（`hosts/ohos/src/bluetooth.rs:75`）。
`bluetoothListen` 以 `classic_listen` 命令监听经典蓝牙（`hosts/ohos/src/bluetooth.rs:95`）。
`bluetoothBleConnect` 以 `ble_connect` 命令连接 BLE 设备（`hosts/ohos/src/bluetooth.rs:156`）。

## 关键符号

- `createRuntimeHostManager` — 接受显式的 `runtimeRoot` 与 `workspaceRoot`，组装 OpenHarmony 运行时 `HostManager`（`hosts/ohos/src/lib.rs:44`）
- `newOhosFileSystemHost` — 创建 `OhosFileSystemHost`（`hosts/ohos/src/lib.rs:38`）
- `OhosTerminalHost` — OpenHarmony PTY 终端 Host（`hosts/ohos/src/terminal.rs:227`）
- `OhosVrootRuntime` — QEMU-vroot 运行时的路径与安装状态（`hosts/ohos/src/terminal.rs:39`）
- `OhosTerminalBackend` — 区分 NativeShell 与 QemuVroot 两种终端后端（`hosts/ohos/src/terminal.rs:33`）
- `OhosManagedRuntimeHost` — OpenHarmony 托管运行时 Host（`hosts/ohos/src/managed_runtime.rs:18`）
- `OhosFileSystemHost` — OpenHarmony 文件系统 Host（`hosts/ohos/src/filesystem.rs:13`）
- `OhosRuntimeStorageHost` — OpenHarmony 运行时存储 Host（`hosts/ohos/src/storage.rs:7`）
- `OhosHttpHost` — OpenHarmony HTTP Host（`hosts/ohos/src/http.rs:11`）
- `OhosLocalInferenceHost` — OpenHarmony 本地推理 Host（`hosts/ohos/src/local_inference.rs:14`）
- `OhosSystemOperationHost` — OpenHarmony 系统操作 Host（`hosts/ohos/src/system_operation.rs:18`）
- `OhosTtsPlaybackHost` — OpenHarmony TTS 播放 Host（`hosts/ohos/src/tts_playback.rs:17`）
- `OhosTtsPlaybackCommand` — 含 command 与 audioPath 两个字段（`hosts/ohos/src/tts_playback.rs:8`）
- `OhosAudioPlaybackHost` — OpenHarmony 音频播放 Host（`hosts/ohos/src/audio_playback.rs:22`）
- `OhosMusicCommand` — 音乐播放命令枚举（`hosts/ohos/src/audio_playback.rs:11`）
- `OhosBluetoothHost` — OpenHarmony 蓝牙 Host（`hosts/ohos/src/bluetooth.rs:17`）
- `ensureReady` — 在 vroot 会话启动前提取 checksum 验证的 Alpine rootfs（`hosts/ohos/src/terminal.rs:88`）
- `verifyRootfsArchiveSha256` — 归档安装前校验归档 SHA-256（`hosts/ohos/src/terminal.rs:114`）
- `readRootfsSha256` — 要求校验和为 64 位十六进制字符并转小写（`hosts/ohos/src/terminal.rs:623`）
- `verifyRootfsPayload` — 要求 rootfs 内存在 `bin/busybox`、`sbin/apk`、`usr/bin/python3`、`usr/bin/node`、`usr/bin/uv`、`usr/bin/pnpm`、`usr/bin/tesseract`、`usr/bin/pdftoppm`（`hosts/ohos/src/terminal.rs:690`）
- `createVrootShell` — 为 QEMU-vroot Alpine 创建 PTY 启动器（`hosts/ohos/src/terminal.rs:530`）
- `terminalInfo` — 把 qemu-vroot 列为默认终端（`hosts/ohos/src/terminal.rs:343`）
- `resolveRuntimeExecutable` — 在显式 executablePath 非空时使用该路径（`hosts/ohos/src/managed_runtime.rs:122`）
- `runRuntimeCommand` — 在 QEMU-vroot Alpine 内运行一次性命令并等待退出（`hosts/ohos/src/managed_runtime.rs:151`）
- `runtimeWorkspaceDir` — 位于 workspaceRoot 下的 `.operit` 与 `managed_runtime` 两级目录并创建目录（`hosts/ohos/src/managed_runtime.rs:116`）
- `runTool` — 在超时或非零退出时返回含退出码与输出的错误（`hosts/ohos/src/documents.rs:22`）
- `renderPdf` — 要求 scale 有限且为正（`hosts/ohos/src/documents.rs:92`）
- `transcribeLocalSpeech` — 经 `transcribeStreamingTransducer` 处理（`hosts/ohos/src/local_inference.rs:25`）
- `synthesizeLocalSpeech` — 经 `synthesizeTts` 处理（`hosts/ohos/src/local_inference.rs:33`）
- `loadSherpaLibraries` — 先加载 `libonnxruntime.so` 再加载 `libsherpa-onnx-c-api.so`（`hosts/ohos/src/local_inference.rs:746`）
- `validateTtsSpeakerId` — 要求 speaker 在 0 到 speakerCount 减 1 之间（`hosts/ohos/src/local_inference.rs:820`）
- `supportsSystemSpeech` — 返回 false（`hosts/ohos/src/tts_playback.rs:38`）
- `speakText` — 返回 API 18 不提供系统 TTS 合成 Host 的错误（`hosts/ohos/src/tts_playback.rs:52`）
- `supportsClassicListening` — 返回 true（`hosts/ohos/src/bluetooth.rs:52`）

## 调用链

### vroot rootfs 就绪

1. `isAvailable` 要求 qemu-vroot 可执行文件、rootfs 归档与校验和文件三者都存在（`hosts/ohos/src/terminal.rs:81`）。
2. `ensureReady` 在 vroot 会话启动前提取 checksum 验证的 Alpine rootfs（`hosts/ohos/src/terminal.rs:88`）。
3. 归档安装前由 `verifyRootfsArchiveSha256` 校验归档 SHA-256（`hosts/ohos/src/terminal.rs:114`）。
4. rootfs 不存在时 payload 直接改名为 rootfs（`hosts/ohos/src/terminal.rs:156`）。
5. 已存在 rootfs 时安装经 apk 做 add --upgrade，不替换用户 rootfs（`hosts/ohos/src/terminal.rs:180`）。
6. `verifyRootfsPayload` 要求 rootfs 内存在 `bin/busybox`、`sbin/apk`、`usr/bin/python3`、`usr/bin/node`、`usr/bin/uv`、`usr/bin/pnpm`、`usr/bin/tesseract`、`usr/bin/pdftoppm`（`hosts/ohos/src/terminal.rs:690`）。
7. 安装完成时把校验和写入 `VROOT_INSTALL_MARKER` 的 installing 临时文件再改名为安装标记（`hosts/ohos/src/terminal.rs:218`）。

### 托管运行时启动

1. `OhosManagedRuntimeHost` 的 `new` 接受终端 Host 与 workspaceRoot（`hosts/ohos/src/managed_runtime.rs:25`）。
2. 请求未指定 cwd 时宿主工作目录取 workspaceRoot（`hosts/ohos/src/managed_runtime.rs:45`）。
3. `vrootHostPath` 要求 MCP 工作目录为绝对路径（`hosts/ohos/src/managed_runtime.rs:80`）。
4. 宿主绝对路径映射为 `VROOT_HOST_MOUNT_ROOT` 前缀的 guest 路径（`hosts/ohos/src/managed_runtime.rs:87`）。
5. `resolveRuntimeExecutable` 在显式 executablePath 非空时使用该路径（`hosts/ohos/src/managed_runtime.rs:122`）。
6. 托管运行时启动目标的终端为 `QEMU_VROOT_TERMINAL`，类型为 `SHELL_TERMINAL_TYPE`（`hosts/ohos/src/managed_runtime.rs:55`）。

### 本地 TTS 合成到播放

1. `synthesizeLocalSpeech` 经 `synthesizeTts` 处理（`hosts/ohos/src/local_inference.rs:33`）。
2. TTS 响应 `outputFormat` 为 wav（`hosts/ohos/src/local_inference.rs:591`）。
3. TTS 提供方经 Core 生成 runtime storage 音频，一个 ArkTS `AVPlayer` 拥有播放、暂停、恢复、停止与状态查询（`hosts/ohos/README.md:27`）。
4. `playAudio` 以 play 命令发送音频路径（`hosts/ohos/src/tts_playback.rs:43`）。
5. `speechState` 以 state 命令查询当前语音会话状态（`hosts/ohos/src/tts_playback.rs:74`）。

### 离线 OCR

1. `guestPath` 把规范化后的绝对路径加 `VROOT_HOST_MOUNT_ROOT` 前缀（`hosts/ohos/src/documents.rs:16`）。
2. 文档工具调用经 `executeHiddenCommand` 执行，executorKey 为 ohos-documents，超时 120_000 毫秒（`hosts/ohos/src/documents.rs:23`）。
3. OCR 经 guest 内 `/usr/bin/tesseract` 离线识别，线程限制为 2，模式为 `--psm 3`（`hosts/ohos/src/documents.rs:62`）。
4. `runTool` 在超时或非零退出时返回含退出码与输出的错误（`hosts/ohos/src/documents.rs:22`）。

### Host 组装

1. `createRuntimeHostManager` 接受显式的 `runtimeRoot` 与 `workspaceRoot`（`hosts/ohos/src/lib.rs:44`）。
2. `HostManager` 由 `withFileSystemWebVisitAndSystemOperationHosts` 组装文件系统、网页访问与系统操作 Host（`hosts/ohos/src/lib.rs:71`）。
3. 运行时组合以 `withLocalInferenceHost` 注册 `OhosLocalInferenceHost` 的 new 结果（`hosts/ohos/src/lib.rs:88`）。
4. 服务发现 Host 是 `ServiceDiscoveryProvider` 的 default 结果（`hosts/ohos/src/lib.rs:93`）。

## 来源

- `hosts/ohos/README.md`
- `hosts/ohos/Cargo.toml`
- `hosts/ohos/src/lib.rs`
- `hosts/ohos/src/terminal.rs`
- `hosts/ohos/src/managed_runtime.rs`
- `hosts/ohos/src/filesystem.rs`
- `hosts/ohos/src/documents.rs`
- `hosts/ohos/src/storage.rs`
- `hosts/ohos/src/http.rs`
- `hosts/ohos/src/local_inference.rs`
- `hosts/ohos/src/system_operation.rs`
- `hosts/ohos/src/tts_playback.rs`
- `hosts/ohos/src/audio_playback.rs`
- `hosts/ohos/src/bluetooth.rs`
