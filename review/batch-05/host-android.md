---
title: Android Host
module: hosts
platforms: [android]
sources: [hosts/README.md, hosts/android/Cargo.toml, hosts/android/src/lib.rs, hosts/android/src/terminal.rs, hosts/android/src/terminal_privilege.rs, hosts/android/src/managed_runtime.rs, hosts/android/src/filesystem.rs, hosts/android/src/document_filesystem.rs, hosts/android/src/local_inference.rs, hosts/android/src/secret_store.rs, hosts/android/src/service_discovery.rs, hosts/android/src/system_operation.rs, hosts/android/src/tts_playback.rs, hosts/android/src/tts_synthesis.rs, hosts/android/src/web_visit.rs, hosts/android/src/bluetooth.rs]
date: 2026-11-11
---

## 概述

`hosts` 目录存放 `operit-host-api` trait 的具体实现，运行时代码通过 `HostManager` 消费这些实现（`hosts/README.md:3`）。
`hosts/android` 是 Android 原生 Host 实现目录（`hosts/README.md:13`）。
Android Host crate 名为 `operit-host-android-native`（`hosts/android/Cargo.toml:2`）。
`operit-host-android-native` 声明 `publish = false`，不对外发布（`hosts/android/Cargo.toml:6`）。
Host crate 不拥有 Access 配对、会话、签名与设备信任（`hosts/README.md:46`）。
Host crate 不拥有 `operit-link` 信封语义（`hosts/README.md:48`）。
Host crate 不拥有 Flutter UI 状态与 WebView 控件（`hosts/README.md:49`）。
`hosts/android/src/terminal.rs` 拥有 PTY 执行，Flutter 拥有 xterm 视图与附加逻辑（`hosts/README.md:125`）。

## AI 速览

- `AndroidTerminalHost` — Android PTY 终端 Host（`hosts/android/src/terminal.rs:69`）
- `AndroidFileSystemHost` — Android 文件系统 Host（`hosts/android/src/filesystem.rs:12`）
- `AndroidManagedRuntimeHost` — Android 托管运行时 Host（`hosts/android/src/managed_runtime.rs:20`）
- `AndroidSystemOperationHost` — Android 系统操作 Host（`hosts/android/src/system_operation.rs:21`）
- `AndroidLocalInferenceHost` — Android 本地推理 Host（`hosts/android/src/local_inference.rs:14`）
- `AndroidBluetoothHost` — Android 蓝牙 Host（`hosts/android/src/bluetooth.rs:25`）
- `AndroidTtsPlaybackHost` — Android TTS 播放 Host（`hosts/android/src/tts_playback.rs:17`）
- `AndroidTtsSynthesisHost` — Android TTS 合成 Host（`hosts/android/src/tts_synthesis.rs:11`）
- `AndroidWebVisitHost` — Android 网页访问 Host（`hosts/android/src/web_visit.rs:7`）
- `AndroidHostSecretStoreBridge` — 保存 `JavaVM` 与 host 引用的 JNI 桥接（`hosts/android/src/secret_store.rs:8`）
- `ShellPrivileges` — 只描述已批准的特权，不发起授权请求（`hosts/android/src/terminal_privilege.rs:5`）
- `ShellTransport` — 为一次系统 shell 会话选择一种传输（`hosts/android/src/terminal_privilege.rs:11`）
- `AndroidPtyProcess` — 区分本地子进程与 Shizuku 远程进程（`hosts/android/src/terminal.rs:99`）
- 主入口函数之一是 `createRuntimeHostManager`，组装 Android 自有的运行时 `HostManager`（`hosts/android/src/lib.rs:75`）
- 另一主入口是 `createPrivilegedRuntimeHostManager`，组装不含应用自有 JNI 注册的特权 Android Host（`hosts/android/src/lib.rs:106`）
- `createBaseRuntimeHostManager` 组装应用与独立模块所有者共享的 Android 能力（`hosts/android/src/lib.rs:130`）
- 运行时代码经 `HostManager` 消费 Android Host 的能力实现（`hosts/README.md:3`）
- 需要 Java 侧能力的调用经 JNI 桥接发出，例如特权查询经 JNI 方法 `terminalPrivilegeOperation` 发给 Java 侧桥接对象（`hosts/android/src/terminal_privilege.rs:60`）

## 核心机制

### Host 组装：应用组合与特权组合

`createRuntimeHostManager` 组装 Android 自有的运行时 `HostManager`（`hosts/android/src/lib.rs:75`）。
`createRuntimeHostManager` 以 `AndroidRuntimeStorageHost` 作 Host 密钥库（`hosts/android/src/lib.rs:79`）。
运行时组合注册 `AndroidLocalInferenceHost`（`hosts/android/src/lib.rs:94`）。
运行时组合以 `acquireMulticastLease` 作 `ServiceDiscovery` 的网络租约来源（`hosts/android/src/lib.rs:98`）。
运行时组合注册 `AndroidPluginSdkIpcHost`（`hosts/android/src/lib.rs:101`）。
`createPrivilegedRuntimeHostManager` 组装不含应用自有 JNI 注册的特权 Android Host（`hosts/android/src/lib.rs:106`）。
特权组合以 NativeFileSecretStore(secretRoot) 作 Host 密钥库（`hosts/android/src/lib.rs:120`）。
特权组合使用 `NativeHostRuntimeEventSchedulerHost` 作运行时事件调度 Host（`hosts/android/src/lib.rs:123`）。
`createBaseRuntimeHostManager` 组装应用与独立模块所有者共享的 Android 能力（`hosts/android/src/lib.rs:130`）。
基础组合以 `AndroidFileSystemHost`、`AndroidHttpHost` 与 `AndroidManagedRuntimeHost` 装配 `HostManager`（`hosts/android/src/lib.rs:151`）。
基础组合注册 `NativeHttpServerHost`、`NativeTcpHost` 与 `NativeSerialPortHost`（`hosts/android/src/lib.rs:162`）。
基础组合注册 `AndroidHostJavaScriptRuntimeHost` 与 `AndroidHostRuntimeTaskSchedulerHost`（`hosts/android/src/lib.rs:166`）。
归档暂存 Host 使用 `archiveRuntimeRoot`，因为 Android 共享存储以 ENOSYS 拒绝 flock，模块运行时根目录是私有的（`hosts/android/src/lib.rs:145`）。
`createBaseRuntimeHostManager` 的 `webVisitHost` 由调用方传入（`hosts/android/src/lib.rs:133`）。
Android Host crate 依赖 `operit-host-api`（`hosts/android/Cargo.toml:11`）。
Android Host crate 依赖 `operit-host-native-common`，并启用 tcp、serial、fs、http、scheduler、storage 特性（`hosts/android/Cargo.toml:12`）。
`jni` 0.21 只在 `target_os` 为 android 时作为依赖引入（`hosts/android/Cargo.toml:19`）。

### 终端：两种实现

`terminalInfo` 把 `PROOT_TERMINAL` 列为默认终端、`PRIMARY_TERMINAL_TYPE` 列为默认终端类型（`hosts/android/src/terminal.rs:267`）。
`ANDROID_SYSTEM_TERMINAL` 与 shell 列为可用终端类型（`hosts/android/src/terminal.rs:277`）。
Android Host 只接受 `PROOT_TERMINAL` 与 bash、`ANDROID_SYSTEM_TERMINAL` 与 shell 两组实现与类型配对（`hosts/android/src/terminal.rs:1536`）。
`normalizeAndroidTerminalType` 只接受 bash 与 shell 两种终端类型（`hosts/android/src/terminal.rs:1524`）。
bash 会话的初始工作目录是 /root（`hosts/android/src/terminal.rs:1557`）。
shell 会话的初始工作目录取自 `OPERIT_ANDROID_INTERNAL_ROOT`（`hosts/android/src/terminal.rs:1558`）。
bash 会话执行 `source $HOME/common.sh && start_shell`（`hosts/android/src/terminal.rs:1655`）。
bash 会话设置 `PROOT_LOADER`、TERM 为 xterm-256color、LANG 为 en_US.UTF-8（`hosts/android/src/terminal.rs:1671`）。
shell 会话执行 `exec /system/bin/sh -i`（`hosts/android/src/terminal.rs:1756`）。
Root 传输的系统 shell 脚本先校验 id -u 为 0，否则 exit 126（`hosts/android/src/terminal.rs:1782`）。
shell 会话的启动输入内嵌 `system_shell_init.sh` 的内容（`hosts/android/src/terminal.rs:1828`）。
PTY 提示标记前缀是 `\x1b]133;OperitPrompt=`（`hosts/android/src/terminal.rs:27`）。
`androidPtyPromptCommand` 在每次提示时输出 base64 编码的 $PWD 与退出码（`hosts/android/src/terminal.rs:1838`）。
PTY 输出缓冲上限 `PTY_OUTPUT_LIMIT` 为 16 MiB（`hosts/android/src/terminal.rs:26`）。
PTY 输出缓冲超过 `PTY_OUTPUT_LIMIT` 时从队首丢弃旧字节（`hosts/android/src/terminal.rs:759`）。
新建 PTY 会话时 `waitForInitialAndroidPtyPrompt` 等待初始提示最长 10000 毫秒（`hosts/android/src/terminal.rs:691`）。
PTY 命令执行以 `quietPeriod` 150 毫秒静默期确认提示标记后的命令完成（`hosts/android/src/terminal.rs:929`）。
会话已有命令在运行时，再次执行返回 Terminal session already has a command in progress 错误（`hosts/android/src/terminal.rs:433`）。
超时命令取消时先向 PTY 写 `b"\x03"`，再以 `COMMAND_CANCEL_SETTLE_TIMEOUT_MS` 为限等待 shell 就绪（`hosts/android/src/terminal.rs:977`）。
超时命令中断失败时会话关闭并移除，错误文本含 could not be interrupted（`hosts/android/src/terminal.rs:469`）。
隐藏命令固定使用 `PRIMARY_TERMINAL_TYPE`（bash），空 `executorKey` 记为 default（`hosts/android/src/terminal.rs:502`）。
同名会话仍存在时直接复用，返回结果的 `isNewSession` 为 false（`hosts/android/src/terminal.rs:377`）。
`createOrGetSession` 在默认 `PRIMARY_TERMINAL_TYPE` 上创建或复用会话（`hosts/android/src/terminal.rs:354`）。
会话列表只包含未退出的会话，条目 `sessionKind` 为 pty（`hosts/android/src/terminal.rs:344`）。
会话屏幕输出的 rows 取自内容行数，cols 取自最长行的字符数（`hosts/android/src/terminal.rs:582`）。
PTY 读取器收到 `\x1b[6n` 光标位置查询时回写当前行列（`hosts/android/src/terminal.rs:779`）。
PTY 读取器先经 `stripAndroidPtyDeviceStatusReports` 得命令块，再经 `stripAndroidPtyPromptMarkers` 得可见块（`hosts/android/src/terminal.rs:739`）。
bash 工作目录用 `TerminalWorkingDirectory` 的 `resolveLinuxGuestDirectory` 解析（`hosts/android/src/terminal.rs:244`）。
shell 工作目录解析先调用 `terminal_privilege` 的 `privileges`，再经 `androidSystemShellWorkingDirectory` 映射（`hosts/android/src/terminal.rs:251`）。
Shizuku 系统 shell 把应用私有目录下的工作目录映射到 /sdcard（`hosts/android/src/terminal.rs:1725`）。
`android_documents` 资源的工作目录经文档提供方的 `resolveNativeDirectory` 解析为原生目录（`hosts/android/src/terminal.rs:46`）。
非 `android_documents` 后端的终端文件系统后端被拒绝（`hosts/android/src/terminal.rs:42`）。
本地 PTY 子进程在 Android 上以 `forkpty` 创建（`hosts/android/src/terminal.rs:2020`）。
非 Android 目标上返回 Android PTY is only available on Android target 错误（`hosts/android/src/terminal.rs:2005`）。
lib.rs 导出 `androidPrivilegedPtyOperation`（`hosts/android/src/lib.rs:36`）。
`androidPrivilegedPtyOperation` 为特权 Binder 服务提供 PTY 原语，不调用应用运行时（`hosts/android/src/terminal.rs:2231`）。
特权 PTY 支持 start 操作（`hosts/android/src/terminal.rs:2243`）。
特权 PTY 的 poll 操作调用 `pollPidExitCode` 返回 exitCode（`hosts/android/src/terminal.rs:2282`）。
特权 PTY 的 close 操作调用 `terminateAndroidPtyProcess` 终止本地进程（`hosts/android/src/terminal.rs:2285`）。
特权 PTY 调整窗口时调用 `setPtyWindowSize`（`hosts/android/src/terminal.rs:2297`）。
特权 PTY 启动以 `forkPtyExecve` 创建进程，响应含 pid 与 fd（`hosts/android/src/terminal.rs:2279`）。

### 终端特权：Root、Shizuku、App 的边界

`ShellPrivileges` 只描述已批准的特权，不发起授权请求（`hosts/android/src/terminal_privilege.rs:5`）。
`ShellPrivileges` 含 `root_su_arguments` 与 `shizuku_authorized` 两个字段（`hosts/android/src/terminal_privilege.rs:8`）。
`ShellPrivileges` 的 `select` 按 Root、Shizuku、App 顺序选择传输（`hosts/android/src/terminal_privilege.rs:24`）。
Root 的 su 参数为空或首项为空时 `select` 返回 Android Root terminal has no su executable 错误（`hosts/android/src/terminal_privilege.rs:25`）。
无 Root 参数且 Shizuku 未授权时选择 `ShellTransport::App`（`hosts/android/src/terminal_privilege.rs:29`）。
进程 euid 为 0 时 `privileges` 直接返回 `root_su_arguments` 为空、`shizuku_authorized` 为 false 的 `ShellPrivileges`（`hosts/android/src/terminal_privilege.rs:38`）。
模块已拥有 Root 进程时不需要应用 JVM 或 su 子进程（`hosts/android/src/terminal_privilege.rs:37`）。
特权查询经 JNI 方法 `terminalPrivilegeOperation` 发给 Java 侧桥接对象（`hosts/android/src/terminal_privilege.rs:60`）。
非 Android 目标上特权调用返回 Android terminal privileges require Android 错误（`hosts/android/src/terminal_privilege.rs:90`）。
Shizuku PTY 以 operation start 请求创建，响应给出 pid、readFd 与 writeFd（`hosts/android/src/terminal.rs:1913`）。
Shizuku 进程退出码经 `terminal_privilege` 的 `call` 发 operation poll 查询（`hosts/android/src/terminal.rs:2187`）。
本地 PTY 进程退出码用 `waitpid` 加 WNOHANG 轮询（`hosts/android/src/terminal.rs:2213`）。
终止本地 PTY 进程时先发 SIGHUP 再发 SIGKILL（`hosts/android/src/terminal.rs:1966`）。
终止 Shizuku 会话经 `terminal_privilege` 的 `call` 发 operation close（`hosts/android/src/terminal.rs:1952`）。
调整 Shizuku 会话窗口大小经 `terminal_privilege` 的 `call` 发 operation resize（`hosts/android/src/terminal.rs:1989`）。

### 托管运行时

`AndroidManagedRuntimeHost` 的 `runtimeWorkspaceDir` 位于 `OPERIT_ANDROID_INTERNAL_ROOT` 下的 managed_runtime（`hosts/android/src/managed_runtime.rs:113`）。
`resolveRuntimeExecutable` 在 `executablePath` 非空时使用该路径，否则按程序取默认值（`hosts/android/src/managed_runtime.rs:126`）。
默认可执行文件为 Node 的 /usr/bin/node、Python 的 /usr/bin/python3、Uv 的 /usr/bin/uv、Pnpm 的 /usr/bin/pnpm（`hosts/android/src/managed_runtime.rs:129`）。
`ManagedRuntimeProgram::Command` 按名字原样作可执行文件（`hosts/android/src/managed_runtime.rs:132`）。
解析出的可执行文件经 `validateRootfsExecutable` 校验（`hosts/android/src/managed_runtime.rs:137`）。
托管运行时进程经 `buildAndroidProotCommand` 构建并设置 `PROOT_NO_SECCOMP` 为 1（`hosts/android/src/managed_runtime.rs:150`）。
托管运行时 stderr 缓冲超过 400 行时丢弃最旧行（`hosts/android/src/managed_runtime.rs:188`）。
两个管道读取任务经 `scheduleServiceTasks` 以 managed-runtime-pipes 调度，调度失败时杀死子进程并返回错误（`hosts/android/src/managed_runtime.rs:196`）。
一次性运行时命令以 `PROOT_NO_SECCOMP` 为 1 执行并返回 `RuntimeCommandOutput`（`hosts/android/src/managed_runtime.rs:220`）。
`readStdoutLine` 用 `recv_timeout` 等待一行，超时或断开时返回 None（`hosts/android/src/managed_runtime.rs:62`）。
`kill` 在 `try_wait` 显示进程仍在运行时调用 `child.kill`（`hosts/android/src/managed_runtime.rs:99`）。
`writeManagedRuntimeLine` 按 `MANAGED_RUNTIME_SINGLE_FRAME_MIN_BYTES` 分发大小帧写入（`hosts/android/src/managed_runtime.rs:234`）。
`MANAGED_RUNTIME_SINGLE_FRAME_MIN_BYTES` 为 4 KiB（`hosts/android/src/managed_runtime.rs:15`）。

### 文件系统：原生路径与文档资源

`AndroidFileSystemHost` 内部包装 `PosixFileSystemHost`（`hosts/android/src/filesystem.rs:14`）。
`AndroidFileSystemHost` 的 `envLabel` 返回 android（`hosts/android/src/filesystem.rs:36`）。
Root 进程的环境描述把 privilege 标为 `AndroidRoot`、isolation 标为 None（`hosts/android/src/filesystem.rs:45`）。
Root 进程的 `android.fileManagement`、`android.root`、`android.shizuku`、`android.batteryOptimization` 四项入职要求标记为已满足（`hosts/android/src/filesystem.rs:48`）。
`validatePath` 要求路径参数非空（`hosts/android/src/filesystem.rs:58`）。
非资源路径不是绝对路径时返回 Path must be an absolute Android path 错误（`hosts/android/src/filesystem.rs:67`）。
`listFiles` 对资源路径调用 `document_filesystem` 的 `call`，对非资源路径调用 inner 的 `listFiles`（`hosts/android/src/filesystem.rs:73`）。
文档写入时内容以 base64 编码传输（`hosts/android/src/filesystem.rs:115`）。
文档字节响应经 `decodeBytes` 做 base64 解码（`hosts/android/src/filesystem.rs:245`）。
`appendFileBytes` 直接调用 inner 的 `appendFileBytes`，不经过文档资源分支（`hosts/android/src/filesystem.rs:129`）。
`openFile` 先校验路径，无 presentation 回调时走文档调用（`hosts/android/src/filesystem.rs:217`）。
`shareFile` 先校验路径，有 presentation 回调时转交给回调（`hosts/android/src/filesystem.rs:232`）。
文档文件系统调用经 JNI `fileSystemResourceOperation` 发给 Java 侧已拥有的运行时 Host（`hosts/android/src/document_filesystem.rs:13`）。
响应 ok 不为 true 或缺少 value 时 `decode_response` 返回错误（`hosts/android/src/document_filesystem.rs:34`）。
非 Android 目标上文档文件系统调用返回 Android document filesystem is unavailable on this platform 错误（`hosts/android/src/document_filesystem.rs:29`）。

### 密钥、发现与本地推理

`AndroidHostSecretStoreBridge` 以 `OnceLock` 加 Mutex 保存全局唯一的 `JavaVM` 与 `GlobalRef`（`hosts/android/src/secret_store.rs:13`）。
`setAndroidHostSecretStoreBridge` 注册 `JavaVM` 与 host 引用（`hosts/android/src/secret_store.rs:39`）。
桥接未注册时 `androidHostSecretStoreBridge` 返回 Android host secret store bridge is not registered 错误（`hosts/android/src/secret_store.rs:63`）。
`clearAndroidHostSecretStoreBridge` 清空桥接并清除运行时事件调度接收端（`hosts/android/src/secret_store.rs:48`）。
`readSecret` 经 Java 的 `readHostSecret` 读取密钥字节（`hosts/android/src/secret_store.rs:105`）。
`readHostSecret` 返回 null 时读取结果为 None（`hosts/android/src/secret_store.rs:112`）。
密钥写入经 Java 的 `writeHostSecret` 方法（`hosts/android/src/secret_store.rs:141`）。
密钥删除经 Java 的 `deleteHostSecret` 方法（`hosts/android/src/secret_store.rs:159`）。
`systemLanguageCode` 经 Java 的 `systemLanguageCode` 方法读取系统语言代码（`hosts/android/src/secret_store.rs:80`）。
`replaceHostRuntimeEventSchedules` 以 JSON 把 `AlarmManager` 调度交给应用 Host 对账（`hosts/android/src/secret_store.rs:168`）。
`acquireMulticastLease` 在共享守护进程建 socket 前获取 Wi-Fi 组播访问（`hosts/android/src/service_discovery.rs:14`）。
组播租约获取调用 Java 的 `acquireDiscoveryMulticastLock`，得到 `WifiManager` `MulticastLock`（`hosts/android/src/service_discovery.rs:21`）。
`MulticastLock` 为空时租约的锁为 None，对应 Ethernet-only Android Host（`hosts/android/src/service_discovery.rs:27`）。
组播租约释放时调用同一把锁的 release（`hosts/android/src/service_discovery.rs:58`）。
组播锁释放失败时以 `tryLogHostConsole` 记录 `ServiceDiscovery` 错误（`hosts/android/src/service_discovery.rs:64`）。
`transcribeLocalSpeech` 与 `synthesizeLocalSpeech` 经 Android Sherpa ONNX Host 处理（`hosts/android/src/local_inference.rs:27`）。
`callLocalInferenceHost` 按 `methodName` 调用方法（`hosts/android/src/local_inference.rs:41`）。
本地推理经 `call_method` 按 `methodName` 调用桥接方法（`hosts/android/src/local_inference.rs:67`）。
本地推理请求以 `serde_json` 序列化（`hosts/android/src/local_inference.rs:47`）。

### 系统操作：已接通与未接通

系统操作 Host 的 `new` 接受 `settingReader`、`settingWriter` 与 `packageOperation` 三个所有者回调（`hosts/android/src/system_operation.rs:28`）。
`forPrivilegedRuntime` 以显式启动时语言构造独立 Host（`hosts/android/src/system_operation.rs:40`）。
应用更新目标按架构选 APK：aarch64 取 arm64-v8a，arm 取 armeabi-v7a，安装时机为 Immediate（`hosts/android/src/system_operation.rs:72`）。
`getSystemLanguageCode` 优先返回构造时给定的 language，否则调用 `androidHostSystemLanguageCode`（`hosts/android/src/system_operation.rs:85`）。
`sendNotification` 返回错误，要求 Android UI host bridge（`hosts/android/src/system_operation.rs:97`）。
`getNotifications` 返回错误，要求 Android notification host bridge（`hosts/android/src/system_operation.rs:161`）。
`getDeviceLocation` 返回错误，要求 Android location host bridge（`hosts/android/src/system_operation.rs:179`）。
`getDeviceInfo` 返回错误，要求 Android device info host bridge（`hosts/android/src/system_operation.rs:189`）。
`captureScreenshot` 返回错误，要求 Android screen capture host bridge（`hosts/android/src/system_operation.rs:195`）。
`recognizeText` 返回错误，要求 Android OCR host bridge（`hosts/android/src/system_operation.rs:203`）。
`installApp` 要求 Immediate 时机，再以 install_app 请求包操作（`hosts/android/src/system_operation.rs:121`）。
`startApp` 转交给 `startAppWithActivity` 且 activity 为 None（`hosts/android/src/system_operation.rs:144`）。
`listInstalledApps` 以 list_installed_apps 请求包操作（`hosts/android/src/system_operation.rs:133`）。
`uninstallApp` 以 uninstall_app 请求包操作（`hosts/android/src/system_operation.rs:126`）。
`stopApp` 以 stop_app 请求包操作（`hosts/android/src/system_operation.rs:155`）。
应用使用时长查询以 get_app_usage_time 请求包操作（`hosts/android/src/system_operation.rs:172`）。

### 语音、网页访问与蓝牙

`AndroidTtsPlaybackHost` 由所有者应用的控制器驱动（`hosts/android/src/tts_playback.rs:22`）。
`supportsSystemSpeech` 返回 true（`hosts/android/src/tts_playback.rs:43`）。
`playAudio` 以 play 命令发送音频路径（`hosts/android/src/tts_playback.rs:48`）。
`speakText` 以 speak 命令发送语音请求（`hosts/android/src/tts_playback.rs:53`）。
`pauseSpeech` 以 pause 命令暂停当前语音会话（`hosts/android/src/tts_playback.rs:58`）。
`resumeSpeech` 以 resume 命令恢复当前语音会话（`hosts/android/src/tts_playback.rs:63`）。
`stopSpeech` 以 stop 命令停止当前语音会话（`hosts/android/src/tts_playback.rs:68`）。
`speechState` 以 state 命令查询当前语音会话状态（`hosts/android/src/tts_playback.rs:73`）。
`synthesizeSpeech` 把请求转交给所有者提供的合成器回调（`hosts/android/src/tts_synthesis.rs:20`）。
`AndroidWebVisitHost` 的 `visitWeb` 返回错误，要求 Android WebView host bridge（`hosts/android/src/web_visit.rs:11`）。
`execute` 把命令与参数交给 controller 回调并解码响应（`hosts/android/src/bluetooth.rs:30`）。
`supportsClassicListening` 返回 true（`hosts/android/src/bluetooth.rs:45`）。
`requestBluetoothPermission` 以 request_permission 命令请求蓝牙权限（`hosts/android/src/bluetooth.rs:48`）。
`bluetoothState` 以 state 命令查询蓝牙状态（`hosts/android/src/bluetooth.rs:52`）。
`requestEnableBluetooth` 以 request_enable 命令请求启用蓝牙（`hosts/android/src/bluetooth.rs:56`）。
`listBluetoothBondedDevices` 以 bonded_devices 命令列出已配对设备（`hosts/android/src/bluetooth.rs:60`）。
`scanBluetoothDevices` 以 scan 命令扫描蓝牙设备（`hosts/android/src/bluetooth.rs:67`）。
`bluetoothConnect` 以 classic_connect 命令连接经典蓝牙（`hosts/android/src/bluetooth.rs:74`）。
`bluetoothListen` 以 classic_listen 命令监听经典蓝牙（`hosts/android/src/bluetooth.rs:81`）。
`bluetoothAccept` 以 classic_accept 命令接受经典蓝牙连接（`hosts/android/src/bluetooth.rs:88`）。
`bluetoothSend` 以 classic_send 命令发送经典蓝牙数据（`hosts/android/src/bluetooth.rs:94`）。
`bluetoothRead` 以 classic_read 命令读取经典蓝牙数据（`hosts/android/src/bluetooth.rs:107`）。
`bluetoothSendAndRead` 发送后读取经典蓝牙数据（`hosts/android/src/bluetooth.rs:110`）。
`bluetoothClose` 以 close 命令关闭蓝牙会话（`hosts/android/src/bluetooth.rs:129`）。
`bluetoothBleConnect` 以 ble_connect 命令连接 BLE 设备（`hosts/android/src/bluetooth.rs:136`）。
`bluetoothBleDiscoverServices` 以 ble_discover_services 命令发现 BLE 服务（`hosts/android/src/bluetooth.rs:142`）。
`bluetoothBleReadCharacteristic` 以 ble_read_characteristic 命令读取 BLE 特征值（`hosts/android/src/bluetooth.rs:157`）。
`bluetoothBleWriteCharacteristic` 以 ble_write_characteristic 命令写入 BLE 特征值（`hosts/android/src/bluetooth.rs:164`）。
`bluetoothBleWriteAndReadCharacteristic` 以 ble_write_and_read_characteristic 命令写入并读取 BLE 特征值（`hosts/android/src/bluetooth.rs:172`）。
`bluetoothBleSubscribeCharacteristic` 以 ble_subscribe_characteristic 命令订阅 BLE 特征值（`hosts/android/src/bluetooth.rs:182`）。
`bluetoothBleReadNotifications` 以 ble_read_notifications 命令读取 BLE 通知（`hosts/android/src/bluetooth.rs:190`）。

### 与模块应用的关系

`createBaseRuntimeHostManager` 组装应用与独立模块所有者共享的 Android 能力（`hosts/android/src/lib.rs:130`）。
特权组合以 NativeFileSecretStore(secretRoot) 作 Host 密钥库（`hosts/android/src/lib.rs:120`）。
模块已拥有 Root 进程时不需要应用 JVM 或 su 子进程（`hosts/android/src/terminal_privilege.rs:37`）。
Android Host 的能力由应用与独立模块所有者共享，模块应用侧的打包与启动见 [[app-android-module|Android 模块应用]]（`hosts/android/src/lib.rs:130`）。

## 关键符号

- `createRuntimeHostManager` — 组装 Android 自有的运行时 `HostManager`（`hosts/android/src/lib.rs:75`）
- `createPrivilegedRuntimeHostManager` — 组装不含应用自有 JNI 注册的特权 Android Host（`hosts/android/src/lib.rs:106`）
- `createBaseRuntimeHostManager` — 组装应用与独立模块所有者共享的 Android 能力（`hosts/android/src/lib.rs:130`）
- `AndroidTerminalHost` — Android PTY 终端 Host（`hosts/android/src/terminal.rs:69`）
- `AndroidFileSystemHost` — Android 文件系统 Host（`hosts/android/src/filesystem.rs:12`）
- `AndroidManagedRuntimeHost` — Android 托管运行时 Host（`hosts/android/src/managed_runtime.rs:20`）
- `AndroidSystemOperationHost` — Android 系统操作 Host（`hosts/android/src/system_operation.rs:21`）
- `AndroidLocalInferenceHost` — Android 本地推理 Host（`hosts/android/src/local_inference.rs:14`）
- `AndroidBluetoothHost` — Android 蓝牙 Host（`hosts/android/src/bluetooth.rs:25`）
- `AndroidTtsPlaybackHost` — Android TTS 播放 Host（`hosts/android/src/tts_playback.rs:17`）
- `AndroidTtsSynthesisHost` — Android TTS 合成 Host（`hosts/android/src/tts_synthesis.rs:11`）
- `AndroidWebVisitHost` — Android 网页访问 Host（`hosts/android/src/web_visit.rs:7`）
- `AndroidHostSecretStoreBridge` — 保存 `JavaVM` 与 host 引用的 JNI 桥接（`hosts/android/src/secret_store.rs:8`）
- `ShellPrivileges` — 只描述已批准的特权，不发起授权请求（`hosts/android/src/terminal_privilege.rs:5`）
- `ShellTransport` — 为一次系统 shell 会话选择一种传输（`hosts/android/src/terminal_privilege.rs:11`）
- `AndroidPtyProcess` — 区分本地子进程与 Shizuku 远程进程（`hosts/android/src/terminal.rs:99`）
- `terminalInfo` — 把 `PROOT_TERMINAL` 列为默认终端、`PRIMARY_TERMINAL_TYPE` 列为默认终端类型（`hosts/android/src/terminal.rs:267`）
- `androidPrivilegedPtyOperation` — 为特权 Binder 服务提供 PTY 原语，不调用应用运行时（`hosts/android/src/terminal.rs:2231`）
- `setAndroidHostSecretStoreBridge` — 注册 `JavaVM` 与 host 引用（`hosts/android/src/secret_store.rs:39`）
- `clearAndroidHostSecretStoreBridge` — 清空桥接并清除运行时事件调度接收端（`hosts/android/src/secret_store.rs:48`）
- `acquireMulticastLease` — 在共享守护进程建 socket 前获取 Wi-Fi 组播访问（`hosts/android/src/service_discovery.rs:14`）
- `AndroidPtyProcess` 的 Shizuku 进程退出码经 `terminal_privilege` 的 `call` 发 operation poll 查询（`hosts/android/src/terminal.rs:2187`）

## 调用链

### 终端命令执行

1. 命令写入 PTY 后等待提示标记，`quietPeriod` 150 毫秒静默期确认完成（`hosts/android/src/terminal.rs:929`）。
2. 会话已有命令在运行时，再次执行返回 Terminal session already has a command in progress 错误（`hosts/android/src/terminal.rs:433`）。
3. 超时命令取消时先向 PTY 写 `b"\x03"`，再以 `COMMAND_CANCEL_SETTLE_TIMEOUT_MS` 为限等待 shell 就绪（`hosts/android/src/terminal.rs:977`）。
4. 超时命令中断失败时会话关闭并移除，错误文本含 could not be interrupted（`hosts/android/src/terminal.rs:469`）。

### 特权传输选择

1. 进程 euid 为 0 时 `privileges` 直接返回 `root_su_arguments` 为空、`shizuku_authorized` 为 false 的 `ShellPrivileges`（`hosts/android/src/terminal_privilege.rs:38`）。
2. 否则特权查询经 JNI 方法 `terminalPrivilegeOperation` 发给 Java 侧桥接对象（`hosts/android/src/terminal_privilege.rs:60`）。
3. `ShellPrivileges` 的 `select` 按 Root、Shizuku、App 顺序选择传输（`hosts/android/src/terminal_privilege.rs:24`）。
4. 无 Root 参数且 Shizuku 未授权时选择 `ShellTransport::App`（`hosts/android/src/terminal_privilege.rs:29`）。
5. Shizuku PTY 以 operation start 请求创建，响应给出 pid、readFd 与 writeFd（`hosts/android/src/terminal.rs:1913`）。

### 文档资源读写

1. `listFiles` 对资源路径调用 `document_filesystem` 的 `call`，对非资源路径调用 inner 的 `listFiles`（`hosts/android/src/filesystem.rs:73`）。
2. 文档文件系统调用经 JNI `fileSystemResourceOperation` 发给 Java 侧已拥有的运行时 Host（`hosts/android/src/document_filesystem.rs:13`）。
3. 文档写入时内容以 base64 编码传输（`hosts/android/src/filesystem.rs:115`）。
4. 文档字节响应经 `decodeBytes` 做 base64 解码（`hosts/android/src/filesystem.rs:245`）。
5. 响应 ok 不为 true 或缺少 value 时 `decode_response` 返回错误（`hosts/android/src/document_filesystem.rs:34`）。

### 托管运行时执行

1. `resolveRuntimeExecutable` 在 `executablePath` 非空时使用该路径，否则按程序取默认值（`hosts/android/src/managed_runtime.rs:126`）。
2. 解析出的可执行文件经 `validateRootfsExecutable` 校验（`hosts/android/src/managed_runtime.rs:137`）。
3. 托管运行时进程经 `buildAndroidProotCommand` 构建并设置 `PROOT_NO_SECCOMP` 为 1（`hosts/android/src/managed_runtime.rs:150`）。
4. 两个管道读取任务经 `scheduleServiceTasks` 以 managed-runtime-pipes 调度（`hosts/android/src/managed_runtime.rs:196`）。
5. `readStdoutLine` 用 `recv_timeout` 等待一行，超时或断开时返回 None（`hosts/android/src/managed_runtime.rs:62`）。

### Host 组装

1. `createRuntimeHostManager` 组装 Android 自有的运行时 `HostManager`（`hosts/android/src/lib.rs:75`）。
2. `createPrivilegedRuntimeHostManager` 组装不含应用自有 JNI 注册的特权 Android Host（`hosts/android/src/lib.rs:106`）。
3. `createBaseRuntimeHostManager` 组装应用与独立模块所有者共享的 Android 能力（`hosts/android/src/lib.rs:130`）。

## 来源

- `hosts/README.md`
- `hosts/android/Cargo.toml`
- `hosts/android/src/lib.rs`
- `hosts/android/src/terminal.rs`
- `hosts/android/src/terminal_privilege.rs`
- `hosts/android/src/managed_runtime.rs`
- `hosts/android/src/filesystem.rs`
- `hosts/android/src/document_filesystem.rs`
- `hosts/android/src/local_inference.rs`
- `hosts/android/src/secret_store.rs`
- `hosts/android/src/service_discovery.rs`
- `hosts/android/src/system_operation.rs`
- `hosts/android/src/tts_playback.rs`
- `hosts/android/src/tts_synthesis.rs`
- `hosts/android/src/web_visit.rs`
- `hosts/android/src/bluetooth.rs`
