---
title: Linux Host
module: hosts
platforms: [linux]
sources: [hosts/linux/Cargo.toml, hosts/linux/src/lib.rs, hosts/linux/src/tools/terminal/mod.rs, hosts/linux/src/tools/fs/mod.rs, hosts/linux/src/tools/runtime/mod.rs, hosts/linux/src/tools/storage/mod.rs, hosts/linux/src/tools/system/mod.rs, hosts/linux/src/tools/system/packages.rs, hosts/linux/src/tools/browser/mod.rs, hosts/linux/src/tools/http/mod.rs, hosts/linux/src/tools/audio/mod.rs, hosts/linux/src/tools/bluetooth/mod.rs, hosts/linux/src/tools/tts/mod.rs, hosts/linux/src/plugin_sdk_ipc.rs]
date: 2026-11-11
---

## 概述

Linux Host 由 crate `operit-host-linux-native` 提供（`hosts/linux/Cargo.toml:2`）。
`operit-host-linux-native` 声明 `publish = false`，不对外发布（`hosts/linux/Cargo.toml:6`）。
`createRuntimeHostManager` 接收 `runtimeRoot`、`workspaceRoot` 与 `webVisitHost` 三个参数（`hosts/linux/src/lib.rs:51`）。
daemon 模块通过 #[path] 指向 hosts/unix/daemon.rs 的共享实现，细节见 [[host-common|Host 公共实现]]（`hosts/linux/src/lib.rs:6`）。
`daemon` 模块只在启用 `daemon` 特性且目标为 Linux 时编译（`hosts/linux/src/lib.rs:5`）。
终端、文件系统、系统操作、音频、蓝牙由 Linux 自有实现提供，Android 的同名 tools 见 [[host-android|Android Host]]（`hosts/linux/src/lib.rs:42`）。
HTTP 服务器、TCP 与串口 Host 直接取自 operit-host-native-common（`hosts/linux/src/lib.rs:75`）。

## AI 速览

- `LinuxTerminalHost` — Linux PTY 终端 Host（`hosts/linux/src/tools/terminal/mod.rs:28`）
- `LinuxFileSystemHost` — Linux 文件系统 Host（`hosts/linux/src/tools/fs/mod.rs:19`）
- `LinuxManagedRuntimeHost` — Linux 托管运行时 Host（`hosts/linux/src/tools/runtime/mod.rs:20`）
- `LinuxRuntimeStorageHost` — Linux 运行时存储与密钥 Host（`hosts/linux/src/tools/storage/mod.rs:13`）
- `LinuxSystemOperationHost` — Linux 系统操作 Host（`hosts/linux/src/tools/system/mod.rs:19`）
- `LinuxHttpHost` — Linux HTTP 与 WebSocket Host，内部持有 `NativeHttpHost`（`hosts/linux/src/tools/http/mod.rs:12`）
- `LinuxAudioPlaybackHost` — Linux 音频播放 Host，只持有单个音乐会话（`hosts/linux/src/tools/audio/mod.rs:12`）
- `LinuxBluetoothHost` — Linux 蓝牙 Host（`hosts/linux/src/tools/bluetooth/mod.rs:63`）
- `LinuxTtsSynthesisHost` — 无状态 TTS 合成器（`hosts/linux/src/tools/tts/mod.rs:13`）
- `LinuxTtsPlaybackHost` — 持有播放状态的 TTS 播放 Host（`hosts/linux/src/tools/tts/mod.rs:23`）
- `LinuxPluginSdkIpcHost` — Linux 插件 SDK IPC Host（`hosts/linux/src/plugin_sdk_ipc.rs:112`）
- `LinuxWebVisitHost` — Linux 网页访问 Host（`hosts/linux/src/tools/browser/mod.rs:13`）
- `LinuxBrowserAutomationHost` — Linux 浏览器自动化 Host（`hosts/linux/src/tools/browser/mod.rs:37`）
- 主入口是 `createRuntimeHostManager`，接收 `runtimeRoot`、`workspaceRoot` 与 `webVisitHost` 三个参数（`hosts/linux/src/lib.rs:51`）
- 数据流向：`HostManager` 由 `LinuxFileSystemHost` 等 Linux tools 装配（`hosts/linux/src/lib.rs:63`）

## 核心机制

### Host 组装：一个入口与两类 tools

`HostManager` 用 `LinuxFileSystemHost`、`LinuxHttpHost`、`LinuxSystemOperationHost` 与 `LinuxManagedRuntimeHost` 装配（`hosts/linux/src/lib.rs:63`）。
同一份 `LinuxRuntimeStorageHost` 实例兼任 Host 密钥库与 `runtimeSqliteHost`（`hosts/linux/src/lib.rs:60`）。
第二个 `LinuxHttpHost` 实例注册为 WebSocket Host（`hosts/linux/src/lib.rs:73`）。
HTTP 服务器、TCP 与串口 Host 直接取自 operit-host-native-common（`hosts/linux/src/lib.rs:75`）。
`LinuxHostJavaScriptRuntimeHost` 是 operit-host-native-common 的 `NativeHostJavaScriptRuntimeHost` 的重导出（`hosts/linux/src/lib.rs:29`）。
`LinuxHostRuntimeEventSchedulerHost` 与 `LinuxHostRuntimeTaskSchedulerHost` 是 operit-host-native-common 的重导出（`hosts/linux/src/lib.rs:31`）。
服务发现 Host 使用 operit-host-native-common 的 `ServiceDiscoveryProvider`（`hosts/linux/src/lib.rs:86`）。
`LinuxPluginSdkIpcHost` 注册为插件 SDK IPC Host（`hosts/linux/src/lib.rs:88`）。
Linux Host crate 依赖 `operit-host-api`（`hosts/linux/Cargo.toml:20`）。
Linux Host crate 依赖 `operit-host-native-common`，并启用 `tcp`、`serial`、`fs`、`http`、`scheduler`、`storage`、`app-install` 特性（`hosts/linux/Cargo.toml:21`）。
Linux Host crate 依赖 `operit-host-native-plugin-sdk-ipc`（`hosts/linux/Cargo.toml:22`）。
Linux Host crate 依赖 `portable-pty` 0.9.0（`hosts/linux/Cargo.toml:23`）。
`libc` 与 `zbus` 只在 `target_os` 为 linux 时作为依赖引入（`hosts/linux/Cargo.toml:33`）。

### 与 Android/Windows 同名 tools 的对照口径

`LinuxHttpHost` 内部持有 `NativeHttpHost`（`hosts/linux/src/tools/http/mod.rs:12`）。
存储操作由 `delegate_runtime_storage` 宏转发给共享的 `NativeRuntimeStorageHost`（`hosts/linux/src/tools/storage/mod.rs:18`）。
终端、文件系统、系统操作、音频、蓝牙由 Linux 自有实现提供（`hosts/linux/src/lib.rs:42`）。
TTS 由 Linux 自有实现提供（`hosts/linux/src/lib.rs:47`）。

### 终端：只要 bash 的 PTY

`LinuxTerminalHost` 是 Linux PTY 终端 Host（`hosts/linux/src/tools/terminal/mod.rs:28`）。
`PLATFORM` 为 linux，`TERMINAL` 为 native，`PRIMARY_TERMINAL_TYPE` 为 bash（`hosts/linux/src/tools/terminal/mod.rs:24`）。
`terminalInfo` 的 `types` 只含一项，`terminalType` 为 bash，描述为 Linux bash terminal（`hosts/linux/src/tools/terminal/mod.rs:94`）。
`normalizeTerminalType` 只接受 `PRIMARY_TERMINAL_TYPE`（`hosts/linux/src/tools/terminal/mod.rs:1251`）。
`requireNativeTerminal` 只接受 `TERMINAL` 这一种终端实现（`hosts/linux/src/tools/terminal/mod.rs:1259`）。
`linuxPtyCommand` 构造 bash `--noprofile` `--norc` -i 子进程（`hosts/linux/src/tools/terminal/mod.rs:584`）。
PTY 环境设置 `TERM` 为 xterm-256color、`COLORTERM` 为 truecolor、`LANG` 为 C.UTF-8、`PS1` 为 $PWD $ （`hosts/linux/src/tools/terminal/mod.rs:590`）。
`PROMPT_COMMAND` 在每次提示时输出 base64 编码的工作目录与退出码（`hosts/linux/src/tools/terminal/mod.rs:593`）。
PTY 输出缓冲上限 `PTY_OUTPUT_LIMIT` 为 1024 * 1024 字节（`hosts/linux/src/tools/terminal/mod.rs:19`）。
PTY 输出缓冲超限时从队首丢弃旧字节（`hosts/linux/src/tools/terminal/mod.rs:613`）。
新建会话等待初始提示最长 10000 毫秒（`hosts/linux/src/tools/terminal/mod.rs:561`）。
同一个终端会话同一时间只允许一条命令在执行（`hosts/linux/src/tools/terminal/mod.rs:309`）。
命令超时时返回 exitCode -1 与 timedOut true（`hosts/linux/src/tools/terminal/mod.rs:785`）。
取消超时命令时写入 \x03（`hosts/linux/src/tools/terminal/mod.rs:800`）。
取消超时命令的等待上限 `COMMAND_CANCEL_SETTLE_TIMEOUT_MS` 为 3000 毫秒（`hosts/linux/src/tools/terminal/mod.rs:22`）。
`listSessions` 遍历全部 PTY 会话并刷新退出码（`hosts/linux/src/tools/terminal/mod.rs:202`）。
会话列表条目的 `sessionKind` 为 pty（`hosts/linux/src/tools/terminal/mod.rs:220`）。
新建终端会话默认尺寸为 24 行 80 列（`hosts/linux/src/tools/terminal/mod.rs:264`）。
`executorKey` 为空时默认取 default（`hosts/linux/src/tools/terminal/mod.rs:367`）。
隐藏会话名形如 `hidden:{executorLabel}`（`hosts/linux/src/tools/terminal/mod.rs:491`）。
`hiddenPtySessionId` 按 `executorKey` 复用已存在的隐藏会话（`hosts/linux/src/tools/terminal/mod.rs:472`）。
input 与 control 至少一个非空（`hosts/linux/src/tools/terminal/mod.rs:399`）。
`getSessionScreen` 返回会话当前屏幕内容与行列数（`hosts/linux/src/tools/terminal/mod.rs:433`）。
PTY 提示标记前缀为 \x1b]133;OperitPrompt=（`hosts/linux/src/tools/terminal/mod.rs:20`）。

### 文件系统：绝对路径与桌面工具

`LinuxFileSystemHost` 是 Linux 文件系统 Host（`hosts/linux/src/tools/fs/mod.rs:19`）。
Linux 文件系统的 `envLabel` 返回 linux（`hosts/linux/src/tools/fs/mod.rs:33`）。
Linux 文件系统的 `environmentDescriptor` 返回 `HostEnvironmentDescriptor::linux()`（`hosts/linux/src/tools/fs/mod.rs:37`）。
`validatePath` 拒绝非绝对路径（`hosts/linux/src/tools/fs/mod.rs:46`）。
`openAppendFile` 委托给 `NativeFileAppendHandle`（`hosts/linux/src/tools/fs/mod.rs:29`）。
复制目录时要求 recursive 标志（`hosts/linux/src/tools/fs/mod.rs:211`）。
`fileInfo` 对不存在的目标返回 exists 为 false 而不是报错（`hosts/linux/src/tools/fs/mod.rs:279`）。
owner 与 group 字段为空字符串（`hosts/linux/src/tools/fs/mod.rs:311`）。
`zipFiles` 把文件或目录打包为 zip（`hosts/linux/src/tools/fs/mod.rs:388`）。
`unzipFiles` 把 zip 解包到目标目录（`hosts/linux/src/tools/fs/mod.rs:420`）。
`openFile` 用 xdg-open 打开文件（`hosts/linux/src/tools/fs/mod.rs:450`）。
分享请求用 xdg-email 发起（`hosts/linux/src/tools/fs/mod.rs:468`）。
权限字符串由 `permissions_string` 生成（`hosts/linux/src/tools/fs/mod.rs:511`）。

### 托管运行时：直接执行系统里的解释器

`LinuxManagedRuntimeHost` 是 Linux 托管运行时 Host（`hosts/linux/src/tools/runtime/mod.rs:20`）。
Reveal 动作对目录调用 xdg-open（`hosts/linux/src/tools/runtime/mod.rs:118`）。
Terminal 动作启动 x-terminal-emulator（`hosts/linux/src/tools/runtime/mod.rs:123`）。
`runtimeWorkspaceDir` 为 $HOME 下的 .local/share/operit2/managed_runtime（`hosts/linux/src/tools/runtime/mod.rs:143`）。
Node 映射为 node、Python 映射为 python3、Uv 映射为 uv、Pnpm 映射为 pnpm（`hosts/linux/src/tools/runtime/mod.rs:166`）。
`startRuntimeProcess` 启动带管道 stdio 的托管运行时子进程（`hosts/linux/src/tools/runtime/mod.rs:180`）。
托管运行时 stdout 与 stderr 读取任务以 `managed-runtime-pipes` 调度（`hosts/linux/src/tools/runtime/mod.rs:237`）。
托管运行时 stderr 缓冲上限为 400 行（`hosts/linux/src/tools/runtime/mod.rs:229`）。
`runRuntimeCommand` 执行一次性托管运行时命令（`hosts/linux/src/tools/runtime/mod.rs:252`）。
`MANAGED_RUNTIME_SINGLE_FRAME_MIN_BYTES` 为 4 * 1024（`hosts/linux/src/tools/runtime/mod.rs:17`）。
单行达到 `MANAGED_RUNTIME_SINGLE_FRAME_MIN_BYTES` 时按整帧写入（`hosts/linux/src/tools/runtime/mod.rs:277`）。

### 存储与密钥：XDG 目录与 0600 密钥文件

`LinuxRuntimeStorageHost` 持有 `NativeRuntimeStorageHost` 与 `secretRoot`（`hosts/linux/src/tools/storage/mod.rs:13`）。
存储操作由 `delegate_runtime_storage` 宏转发给共享的 `NativeRuntimeStorageHost`（`hosts/linux/src/tools/storage/mod.rs:18`）。
`defaultRuntimeRoot` 优先取 XDG_DATA_HOME 下的 operit2/runtime（`hosts/linux/src/tools/storage/mod.rs:25`）。
`defaultWorkspaceRoot` 优先取 XDG_DATA_HOME 下的 operit2/workspaces（`hosts/linux/src/tools/storage/mod.rs:39`）。
Host 密钥根目录优先取 XDG_STATE_HOME 下的 operit2/secrets（`hosts/linux/src/tools/storage/mod.rs:158`）。
`new` 接收显式 `runtimeRoot` 与 `workspaceRoot`（`hosts/linux/src/tools/storage/mod.rs:53`）。
密钥文件以 0o600 权限与 `O_NOFOLLOW` 标志写入（`hosts/linux/src/tools/storage/mod.rs:90`）。
密钥根目录以 0o700 权限创建（`hosts/linux/src/tools/storage/mod.rs:122`）。
`validateSecretKey` 只允许字母数字与 . _ -（`hosts/linux/src/tools/storage/mod.rs:190`）。

### 系统操作与包管理

`LinuxSystemOperationHost` 是 Linux 系统操作 Host（`hosts/linux/src/tools/system/mod.rs:19`）。
`applicationUpdateTarget` 返回 `LinuxTarGz` 包与 `Immediate` 安装时序（`hosts/linux/src/tools/system/mod.rs:34`）。
系统语言按 LC_ALL、LC_MESSAGES、LANG 的顺序取（`hosts/linux/src/tools/system/mod.rs:323`）。
`getSystemLanguageCode` 委托给 `get_linux_system_language_code`（`hosts/linux/src/tools/system/mod.rs:38`）。
通知发送调用 notify-send（`hosts/linux/src/tools/system/mod.rs:48`）。
修改系统设置经 gsettings set 执行（`hosts/linux/src/tools/system/mod.rs:434`）。
读取系统设置经 gsettings get 执行（`hosts/linux/src/tools/system/mod.rs:452`）。
setting 须为 schema:key 形式（`hosts/linux/src/tools/system/mod.rs:483`）。
`installApp` 要求安装时序为 Immediate（`hosts/linux/src/tools/system/mod.rs:86`）。
`installApp` 把安装交给 `packages::install`（`hosts/linux/src/tools/system/mod.rs:87`）。
`uninstallApp` 交给 `packages::uninstall`（`hosts/linux/src/tools/system/mod.rs:91`）。
`listInstalledApps` 交给 `packages::list`（`hosts/linux/src/tools/system/mod.rs:95`）。
`startApp` 交给 `packages::start`（`hosts/linux/src/tools/system/mod.rs:99`）。
`stopApp` 交给 `packages::stop`（`hosts/linux/src/tools/system/mod.rs:103`）。
通知查询调用 dunstctl history（`hosts/linux/src/tools/system/mod.rs:343`）。
Linux 不提供历史前台使用时长（`hosts/linux/src/tools/system/mod.rs:508`）。
高精度定位请求精度等级 8，否则请求 6（`hosts/linux/src/tools/system/mod.rs:519`）。
定位结果的 `provider` 为 geoclue2（`hosts/linux/src/tools/system/mod.rs:575`）。
定位不提供 civic 地址，city 与 province 为空（`hosts/linux/src/tools/system/mod.rs:579`）。
设备 ID 取自 /etc/machine-id，系统名取自 /etc/os-release 的 PRETTY_NAME（`hosts/linux/src/tools/system/mod.rs:591`）。
发行版名与内核版本拼进 `androidVersion` 字段（`hosts/linux/src/tools/system/mod.rs:622`）。
`sdkVersion` 为 0，`screenDensity` 为 1.0（`hosts/linux/src/tools/system/mod.rs:623`）。
无电池设备返回电池电量 -1 与未充电（`hosts/linux/src/tools/system/mod.rs:756`）。
截图调用 gnome-screenshot -f（`hosts/linux/src/tools/system/mod.rs:163`）。
文字识别调用 tesseract（`hosts/linux/src/tools/system/mod.rs:187`）。
tesseract 语言映射为 Latin 对 eng、Chinese 对 chi_sim、Japanese 对 jpn、Korean 对 kor（`hosts/linux/src/tools/system/mod.rs:281`）。

### 包管理：desktop 文件即应用

应用扫描根目录包含用户 applications 目录、XDG_DATA_DIRS、flatpak 与 snapd 的 desktop 目录（`hosts/linux/src/tools/system/packages.rs:48`）。
`list` 只收录 Type 为 Application 的条目，排除 Hidden 条目，NoDisplay 条目仅在 `include` 为 false 时排除（`hosts/linux/src/tools/system/packages.rs:130`）。
`start` 用 gio launch 启动桌面应用（`hosts/linux/src/tools/system/packages.rs:143`）。
`stop` 对 Flatpak 应用调用 flatpak kill（`hosts/linux/src/tools/system/packages.rs:178`）。
停止非 X-Flatpak 应用时，可执行文件不可为 env、sh、bash、flatpak、snap（`hosts/linux/src/tools/system/packages.rs:162`）。
向可执行文件匹配的进程发送 kill -TERM（`hosts/linux/src/tools/system/packages.rs:202`）。
`install` 先尝试 `AppInstaller::installPortableApp` 安装便携包（`hosts/linux/src/tools/system/packages.rs:219`）。
install 接受 .deb、.rpm、.flatpakref、.flatpak、.snap，用 xdg-open 打开系统安装器（`hosts/linux/src/tools/system/packages.rs:237`）。
打开系统安装器后报告 `installState` 为 `InstallerOpened`（`hosts/linux/src/tools/system/packages.rs:245`）。
明确拒绝把 `AppImage` 当作可安装包（`hosts/linux/src/tools/system/packages.rs:237`）。
`uninstall` 对 Flatpak 应用调用 `flatpak` uninstall --noninteractive -y（`hosts/linux/src/tools/system/packages.rs:252`）。
Snap 应用用 pkexec snap remove 卸载（`hosts/linux/src/tools/system/packages.rs:260`）。
dpkg-query -S 查 .desktop 文件的属主包（`hosts/linux/src/tools/system/packages.rs:265`）。
Debian 包用 pkexec apt-get remove -y 卸载（`hosts/linux/src/tools/system/packages.rs:273`）。
RPM 包归属用 rpm -qf --qf %{NAME} 查询（`hosts/linux/src/tools/system/packages.rs:275`）。
`valid_package` 校验包名字符集（`hosts/linux/src/tools/system/packages.rs:292`）。

### 浏览器与 HTTP

Linux 网页访问的 `visitWeb` 调用 `visit_with_chromium`（`hosts/linux/src/tools/browser/mod.rs:29`）。
`visitWeb` 传入 --no-sandbox 与 --disable-dev-shm-usage 两个 Chromium 参数（`hosts/linux/src/tools/browser/mod.rs:32`）。
浏览器自动化 Host 用同样的两个 Chromium 参数构造 `ChromiumBrowserAutomationHost`（`hosts/linux/src/tools/browser/mod.rs:44`）。
`browser_candidates` 优先取 `OPERIT_BROWSER_PATH` 环境变量（`hosts/linux/src/tools/browser/mod.rs:68`）。
`LinuxBrowserAutomationHost` 是 `ChromiumBrowserAutomationHost` 的包装（`hosts/linux/src/tools/browser/mod.rs:37`）。
`LinuxHttpHost` 内部持有 `NativeHttpHost`（`hosts/linux/src/tools/http/mod.rs:12`）。
`executeHttpRequest` 转发给 `inner`（`hosts/linux/src/tools/http/mod.rs:68`）。
`openWebSocket` 由 Linux HTTP Host 的 `WebSocketHost` 实现提供（`hosts/linux/src/tools/http/mod.rs:95`）。

### 音频：ffplay 音乐与 xdg-open 单条音频

`LinuxAudioPlaybackHost` 只持有单个音乐会话（`hosts/linux/src/tools/audio/mod.rs:12`）。
单条音频播放用 xdg-open 启动（`hosts/linux/src/tools/audio/mod.rs:148`）。
音乐播放启动 ffplay -nodisp -autoexit（`hosts/linux/src/tools/audio/mod.rs:44`）。
`sourceType` 只接受 path、url、uri 三种（`hosts/linux/src/tools/audio/mod.rs:171`）。
音乐音量必须在 0 到 1 之间（`hosts/linux/src/tools/audio/mod.rs:178`）。
暂停时终止当前音乐进程并记录暂停位置（`hosts/linux/src/tools/audio/mod.rs:215`）。
跳转时暂停状态只更新记录位置，播放状态重启进程跳到新位置（`hosts/linux/src/tools/audio/mod.rs:264`）。
`stopMusic` 终止进程并取走音乐会话（`hosts/linux/src/tools/audio/mod.rs:247`）。
音乐状态的 `durationMs` 恒为 None（`hosts/linux/src/tools/audio/mod.rs:97`）。

### 蓝牙：bluetoothctl 管状态，BlueZ 管 BLE，libc 管 RFCOMM

`LinuxBluetoothHost` 是 Linux 蓝牙 Host（`hosts/linux/src/tools/bluetooth/mod.rs:63`）。
`supportsClassicListening` 返回 true（`hosts/linux/src/tools/bluetooth/mod.rs:117`）。
`requestBluetoothPermission` 返回 linux_bluetooth_permission_not_required（`hosts/linux/src/tools/bluetooth/mod.rs:122`）。
`bluetoothState` 用 bluetoothctl show 判断控制器与电源状态（`hosts/linux/src/tools/bluetooth/mod.rs:127`）。
`requestEnableBluetooth` 执行 bluetoothctl power on（`hosts/linux/src/tools/bluetooth/mod.rs:144`）。
`listBluetoothBondedDevices` 用 bluetoothctl paired-devices 列出已配对设备（`hosts/linux/src/tools/bluetooth/mod.rs:149`）。
蓝牙扫描开启后等待 durationMs 再关闭（`hosts/linux/src/tools/bluetooth/mod.rs:169`）。
扫描结果的 `source` 为 linux.bluez，`rssi` 为 None（`hosts/linux/src/tools/bluetooth/mod.rs:180`）。
`BTPROTO_RFCOMM` 常量值为 3（`hosts/linux/src/tools/bluetooth/mod.rs:37`）。
UUID 00001101-0000-1000-8000-00805f9b34fb 映射到 RFCOMM 通道 1（`hosts/linux/src/tools/bluetooth/mod.rs:748`）。
经典连接会话 ID 以 linux-bt-classic- 开头（`hosts/linux/src/tools/bluetooth/mod.rs:222`）。
监听会话 ID 以 linux-bt-listener- 开头（`hosts/linux/src/tools/bluetooth/mod.rs:270`）。
BLE 连接经 `Connection::system` 走 BlueZ 系统总线（`hosts/linux/src/tools/bluetooth/mod.rs:843`）。
BLE 会话 ID 以 linux-ble- 开头（`hosts/linux/src/tools/bluetooth/mod.rs:444`）。
订阅用 `StartNotify` 开启通知（`hosts/linux/src/tools/bluetooth/mod.rs:612`）。
BLE 服务发现先调用 `wait_for_bluez_services` 等待服务就绪（`hosts/linux/src/tools/bluetooth/mod.rs:478`）。
`bluetoothSendAndRead` 先调 `bluetoothSend` 再调 `bluetoothRead`（`hosts/linux/src/tools/bluetooth/mod.rs:396`）。
蓝牙载荷要求 `text` 与 `dataBase64` 二选一（`hosts/linux/src/tools/bluetooth/mod.rs:833`）。
关闭会话返回 linux_bluetooth_session_closed:{sessionId}（`hosts/linux/src/tools/bluetooth/mod.rs:422`）。

### TTS：espeak-ng 合成，aplay 播放

`LinuxTtsSynthesisHost` 是无状态合成器（`hosts/linux/src/tools/tts/mod.rs:13`）。
`LinuxTtsPlaybackHost` 持有播放状态（`hosts/linux/src/tools/tts/mod.rs:23`）。
`supportsSystemSpeech` 返回 true（`hosts/linux/src/tools/tts/mod.rs:57`）。
Linux 系统 TTS 只支持 wav 输出（`hosts/linux/src/tools/tts/mod.rs:207`）。
语音合成调用 espeak-ng（`hosts/linux/src/tools/tts/mod.rs:215`）。
语速换算为 175.0 * speed 词每分钟，范围 80 到 450（`hosts/linux/src/tools/tts/mod.rs:257`）。
音调换算为 50.0 * pitch，范围 0 到 99（`hosts/linux/src/tools/tts/mod.rs:271`）。
voice 与 locale 不可同时指定（`hosts/linux/src/tools/tts/mod.rs:287`）。
合成输出路径位于系统临时目录下的 `operit_tts`（`hosts/linux/src/tools/tts/mod.rs:246`）。
播放用 aplay 播放音频文件（`hosts/linux/src/tools/tts/mod.rs:374`）。
暂停向播放进程发 -STOP 信号（`hosts/linux/src/tools/tts/mod.rs:153`）。
恢复向播放进程发 -CONT 信号（`hosts/linux/src/tools/tts/mod.rs:174`）。

### 插件 SDK IPC：D-Bus 会话总线传管道

`LinuxPluginSdkIpcHost` 是 Linux 插件 SDK IPC Host（`hosts/linux/src/plugin_sdk_ipc.rs:112`）。
D-Bus 服务名为 `org.operit.PluginSdk`，对象路径为 `/org/operit/PluginSdk`（`hosts/linux/src/plugin_sdk_ipc.rs:11`）。
`new` 从 `OPERIT_PLUGIN_SDK_INSTANCE` 环境变量取实例名（`hosts/linux/src/plugin_sdk_ipc.rs:121`）。
`withInstance` 为每个应用配置生成独立的 D-Bus 服务名（`hosts/linux/src/plugin_sdk_ipc.rs:127`）。
`validate` 只接受标准 endpoint 名称（`hosts/linux/src/plugin_sdk_ipc.rs:137`）。
默认实例调用 `StartServiceByName` 请求 D-Bus 启动服务（`hosts/linux/src/plugin_sdk_ipc.rs:181`）。
监听器在对象路径上导出 `Endpoint` 并认领服务名（`hosts/linux/src/plugin_sdk_ipc.rs:209`）。
`Open` 调用返回一对管道文件描述符（`hosts/linux/src/plugin_sdk_ipc.rs:237`）。
`pipe` 用 `pipe2` 与 `O_CLOEXEC` 创建匿名管道（`hosts/linux/src/plugin_sdk_ipc.rs:85`）。
`send` 把帧发给会话管道（`hosts/linux/src/plugin_sdk_ipc.rs:254`）。
`stopListener` 在监听器未启动时报错（`hosts/linux/src/plugin_sdk_ipc.rs:264`）。

### daemon：共享实现，Linux 只引入

`daemon` 模块只在启用 `daemon` 特性且目标为 Linux 时编译（`hosts/linux/src/lib.rs:5`）。
daemon 模块通过 #[path] 指向 hosts/unix/daemon.rs 的共享实现（`hosts/linux/src/lib.rs:6`）。
`daemon` 特性启用 `dep:tokio` 与 operit-host-native-common 的 `daemon` 特性（`hosts/linux/Cargo.toml:10`）。
daemon 能力的实现细节见 [[host-common|Host 公共实现]]（`hosts/linux/src/lib.rs:6`）。

## 关键符号

- `operit-host-linux-native` — Linux Host crate（`hosts/linux/Cargo.toml:2`）
- `createRuntimeHostManager` — 组装 Linux 运行时 `HostManager` 的主入口（`hosts/linux/src/lib.rs:51`）
- `LinuxTerminalHost` — Linux PTY 终端 Host（`hosts/linux/src/tools/terminal/mod.rs:28`）
- `LinuxFileSystemHost` — Linux 文件系统 Host（`hosts/linux/src/tools/fs/mod.rs:19`）
- `LinuxManagedRuntimeHost` — Linux 托管运行时 Host（`hosts/linux/src/tools/runtime/mod.rs:20`）
- `LinuxRuntimeStorageHost` — Linux 运行时存储与密钥 Host（`hosts/linux/src/tools/storage/mod.rs:13`）
- `LinuxSystemOperationHost` — Linux 系统操作 Host（`hosts/linux/src/tools/system/mod.rs:19`）
- `LinuxHttpHost` — Linux HTTP 与 WebSocket Host（`hosts/linux/src/tools/http/mod.rs:12`）
- `LinuxAudioPlaybackHost` — Linux 音频播放 Host（`hosts/linux/src/tools/audio/mod.rs:12`）
- `LinuxBluetoothHost` — Linux 蓝牙 Host（`hosts/linux/src/tools/bluetooth/mod.rs:63`）
- `LinuxTtsSynthesisHost` — Linux TTS 合成 Host（`hosts/linux/src/tools/tts/mod.rs:13`）
- `LinuxTtsPlaybackHost` — Linux TTS 播放 Host（`hosts/linux/src/tools/tts/mod.rs:23`）
- `LinuxPluginSdkIpcHost` — Linux 插件 SDK IPC Host（`hosts/linux/src/plugin_sdk_ipc.rs:112`）
- `LinuxWebVisitHost` — Linux 网页访问 Host（`hosts/linux/src/tools/browser/mod.rs:13`）
- `LinuxBrowserAutomationHost` — Linux 浏览器自动化 Host（`hosts/linux/src/tools/browser/mod.rs:37`）
- `PTY_OUTPUT_LIMIT` — PTY 输出缓冲上限，1024 * 1024 字节（`hosts/linux/src/tools/terminal/mod.rs:19`）
- `PTY_PROMPT_MARKER_PREFIX` — PTY 提示标记前缀（`hosts/linux/src/tools/terminal/mod.rs:20`）
- `validateSecretKey` — 校验 Host 密钥 key，只允许字母数字与 . _ -（`hosts/linux/src/tools/storage/mod.rs:190`）
- `bluez_connection` — 建立 BlueZ 系统总线连接（`hosts/linux/src/tools/bluetooth/mod.rs:842`）
- `rfcomm_channel` — 解析 RFCOMM 通道号（`hosts/linux/src/tools/bluetooth/mod.rs:747`）

## 调用链

### 终端执行一条命令

1. `createOrGetSession` 新建或复用 bash 会话（`hosts/linux/src/tools/terminal/mod.rs:229`）
2. 同一会话同一时间只允许一条命令在执行（`hosts/linux/src/tools/terminal/mod.rs:309`）
3. 新建会话等待初始提示最长 10000 毫秒（`hosts/linux/src/tools/terminal/mod.rs:561`）
4. 命令超时时返回 exitCode -1 与 timedOut true（`hosts/linux/src/tools/terminal/mod.rs:785`）
5. 取消超时命令时写入 \x03（`hosts/linux/src/tools/terminal/mod.rs:800`）
6. PTY 输出缓冲超限时从队首丢弃旧字节（`hosts/linux/src/tools/terminal/mod.rs:613`）

### 安装一个应用

1. `installApp` 要求安装时序为 Immediate（`hosts/linux/src/tools/system/mod.rs:86`）
2. `install` 先尝试 `AppInstaller::installPortableApp` 安装便携包（`hosts/linux/src/tools/system/packages.rs:219`）
3. install 接受 .deb、.rpm、.flatpakref、.flatpak、.snap，用 xdg-open 打开系统安装器（`hosts/linux/src/tools/system/packages.rs:237`）
4. 打开系统安装器后报告 `installState` 为 `InstallerOpened`（`hosts/linux/src/tools/system/packages.rs:245`）

### 合成并播放一句语音

1. Linux 系统 TTS 只支持 wav 输出（`hosts/linux/src/tools/tts/mod.rs:207`）
2. 语音合成调用 espeak-ng（`hosts/linux/src/tools/tts/mod.rs:215`）
3. 合成输出路径位于系统临时目录下的 `operit_tts`（`hosts/linux/src/tools/tts/mod.rs:246`）
4. 播放用 aplay 播放音频文件（`hosts/linux/src/tools/tts/mod.rs:374`）
5. 暂停向播放进程发 -STOP 信号（`hosts/linux/src/tools/tts/mod.rs:153`）
6. 恢复向播放进程发 -CONT 信号（`hosts/linux/src/tools/tts/mod.rs:174`）

### 连接一个 BLE 设备

1. `bluetoothState` 用 bluetoothctl show 判断控制器与电源状态（`hosts/linux/src/tools/bluetooth/mod.rs:127`）
2. 蓝牙扫描开启后等待 durationMs 再关闭（`hosts/linux/src/tools/bluetooth/mod.rs:169`）
3. BLE 连接经 `Connection::system` 走 BlueZ 系统总线（`hosts/linux/src/tools/bluetooth/mod.rs:843`）
4. BLE 会话 ID 以 linux-ble- 开头（`hosts/linux/src/tools/bluetooth/mod.rs:444`）
5. BLE 服务发现先调用 `wait_for_bluez_services` 等待服务就绪（`hosts/linux/src/tools/bluetooth/mod.rs:478`）
6. 订阅用 `StartNotify` 开启通知（`hosts/linux/src/tools/bluetooth/mod.rs:612`）
7. 蓝牙载荷要求 `text` 与 `dataBase64` 二选一（`hosts/linux/src/tools/bluetooth/mod.rs:833`）

## 来源

- `hosts/linux/Cargo.toml`
- `hosts/linux/src/lib.rs`
- `hosts/linux/src/tools/terminal/mod.rs`
- `hosts/linux/src/tools/fs/mod.rs`
- `hosts/linux/src/tools/runtime/mod.rs`
- `hosts/linux/src/tools/storage/mod.rs`
- `hosts/linux/src/tools/system/mod.rs`
- `hosts/linux/src/tools/system/packages.rs`
- `hosts/linux/src/tools/browser/mod.rs`
- `hosts/linux/src/tools/http/mod.rs`
- `hosts/linux/src/tools/audio/mod.rs`
- `hosts/linux/src/tools/bluetooth/mod.rs`
- `hosts/linux/src/tools/tts/mod.rs`
- `hosts/linux/src/plugin_sdk_ipc.rs`
