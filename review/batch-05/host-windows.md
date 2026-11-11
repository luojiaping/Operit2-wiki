---
title: Windows Host
module: hosts
platforms: [windows]
sources: [hosts/windows/Cargo.toml, hosts/windows/src/lib.rs, hosts/windows/src/daemon.rs, hosts/windows/src/process.rs, hosts/windows/src/tools/terminal/mod.rs, hosts/windows/src/tools/fs/mod.rs, hosts/windows/src/tools/runtime/mod.rs, hosts/windows/src/tools/storage/mod.rs, hosts/windows/src/tools/system/mod.rs, hosts/windows/src/tools/system/application_update.rs, hosts/windows/src/tools/system/application_update.ps1, hosts/windows/src/tools/system/packages.rs, hosts/windows/src/tools/browser/mod.rs, hosts/windows/src/tools/http/mod.rs, hosts/windows/src/tools/audio/mod.rs, hosts/windows/src/tools/bluetooth/mod.rs, hosts/windows/src/tools/tts/mod.rs, hosts/windows/src/tools/mci.rs, hosts/windows/src/plugin_sdk_ipc.rs, hosts/windows/src/plugin_sdk_pipe.rs]
date: 2026-11-11
---

## 概述

Windows Host crate 名为 `operit-host-windows-native`（`hosts/windows/Cargo.toml:2`）。
`operit-host-windows-native` 声明 `publish` 为 false，不对外发布（`hosts/windows/Cargo.toml:6`）。
`createRuntimeHostManager` 组装 Windows 自有的运行时 `HostManager`（`hosts/windows/src/lib.rs:34`）。
Windows Host 的终端默认 PowerShell（`hosts/windows/src/tools/terminal/mod.rs:31`）。
Windows Bash 只解析随包提供的 bash/bin/bash.exe（`hosts/windows/src/tools/terminal/mod.rs:693`）。
Windows Host 的 daemon 控制端点是命名管道，不使用文件系统 socket 探测（`hosts/windows/src/daemon.rs:29`）。
Windows Host 的 Plugin SDK IPC 走命名管道，管道路径由 `pipeName` 映射（`hosts/windows/src/plugin_sdk_ipc.rs:84`）。
对照阅读 [[host-android|Android Host]]、[[host-apple|Apple Host]]。

## AI 速览

- `WindowsTerminalHost` — Windows PTY 终端 Host（`hosts/windows/src/lib.rs:30`）
- `WindowsFileSystemHost` — Windows 文件系统 Host（`hosts/windows/src/lib.rs:25`）
- `WindowsSystemOperationHost` — Windows 系统操作 Host（`hosts/windows/src/lib.rs:29`）
- `WindowsManagedRuntimeHost` — Windows 托管运行时 Host（`hosts/windows/src/lib.rs:27`）
- `WindowsRuntimeStorageHost` — Windows 运行时存储 Host（`hosts/windows/src/lib.rs:28`）
- `WindowsHttpHost` — Windows HTTP Host（`hosts/windows/src/lib.rs:26`）
- `WindowsAudioPlaybackHost` — Windows 音频播放 Host（`hosts/windows/src/lib.rs:22`）
- `WindowsBluetoothHost` — Windows 蓝牙 Host（`hosts/windows/src/lib.rs:23`）
- `WindowsTtsSynthesisHost` — Windows TTS 合成 Host（`hosts/windows/src/lib.rs:31`）
- `WindowsTtsPlaybackHost` — Windows TTS 播放 Host（`hosts/windows/src/lib.rs:31`）
- `WindowsPluginSdkIpcHost` — Windows Plugin SDK IPC Host（`hosts/windows/src/lib.rs:21`）
- `WindowsWebVisitHost` — Windows 网页访问 Host（`hosts/windows/src/lib.rs:24`）
- `WindowsBrowserAutomationHost` — Windows 浏览器自动化 Host（`hosts/windows/src/lib.rs:24`）
- `WindowsHostRuntimeEventHost` — Windows 运行时事件 Host（`hosts/windows/src/lib.rs:17`）
- 主入口是 `createRuntimeHostManager`，组装 Windows 自有的运行时 `HostManager`（`hosts/windows/src/lib.rs:34`）
- 数据流向：运行时组合把 Windows 各 Host 注册进 `HostManager`（`hosts/windows/src/lib.rs:47`）

## 核心机制

### 组装

运行时组合注册 `WindowsFileSystemHost`、`WindowsHttpHost`、`WindowsSystemOperationHost` 与 `WindowsManagedRuntimeHost`（`hosts/windows/src/lib.rs:47`）。
`WindowsHttpHost` 同时注册为 WebSocket Host（`hosts/windows/src/lib.rs:56`）。
运行时组合注册 `NativeHttpServerHost`、`NativeTcpHost` 与 `NativeSerialPortHost`（`hosts/windows/src/lib.rs:57`）。
运行时组合注册 `WindowsAudioPlaybackHost`、`WindowsBluetoothHost`、`WindowsTtsSynthesisHost` 与 `WindowsTtsPlaybackHost`（`hosts/windows/src/lib.rs:62`）。
运行时组合注册 `WindowsPluginSdkIpcHost`（`hosts/windows/src/lib.rs:68`）。
运行时组合注册 `ServiceDiscoveryProvider` 作服务发现 Host（`hosts/windows/src/lib.rs:70`）。
运行时存储 Host 由 `WindowsRuntimeStorageHost` 创建（`hosts/windows/src/lib.rs:42`）。
运行时存储 Host 经 `withHostSecretStore` 注册为 Host 密钥库（`hosts/windows/src/lib.rs:55`）。
Windows Host 依赖 `operit-host-native-common`，启用 tcp、serial、fs、http、scheduler、storage 与 app-install 特性（`hosts/windows/Cargo.toml:21`）。
daemon 模块只在 `daemon` 特性启用时编译（`hosts/windows/src/lib.rs:4`）。

### 终端：PowerShell 默认，随包 Bash

Windows 终端的 `PLATFORM` 为 windows，`TERMINAL` 为 native，默认终端类型 `PRIMARY_TERMINAL_TYPE` 为 powershell（`hosts/windows/src/tools/terminal/mod.rs:31`）。
`normalizeTerminalType` 只接受 powershell 与 bash 两种终端类型（`hosts/windows/src/tools/terminal/mod.rs:1621`）。
`terminalInfo` 用 `bundledBashExecutable` 判断随包 Bash 是否可用（`hosts/windows/src/tools/terminal/mod.rs:105`）。
PowerShell 类型的可用性由 `commandStarts` 探测 powershell.exe 执行版本查询的结果决定（`hosts/windows/src/tools/terminal/mod.rs:115`）。
`bundledBashExecutable` 只解析运行程序同目录下的 bash/bin/bash.exe（`hosts/windows/src/tools/terminal/mod.rs:693`）。
PTY 会话经 portable-pty 的 `native_pty_system` 打开（`hosts/windows/src/tools/terminal/mod.rs:575`）。
`windowsPtyCommand` 以 powershell.exe 加 -NoLogo、-NoProfile、-ExecutionPolicy Bypass、-NoExit 启动 PowerShell（`hosts/windows/src/tools/terminal/mod.rs:706`）。
`ptyCommand` 为 Bash 类型解析 `bundledBashExecutable` 的可执行文件（`hosts/windows/src/tools/terminal/mod.rs:658`）。
Bash 会话的 `PROMPT_COMMAND` 在每次提示时输出 `OperitPrompt` 标记（`hosts/windows/src/tools/terminal/mod.rs:678`）。
`ptyCommandLine` 把 Bash 命令交给 terminal_command 的 `posixCommandLine` 编码（`hosts/windows/src/tools/terminal/mod.rs:641`）。
含控制字符的 PowerShell 命令经 Base64 编码后由 `Invoke-Expression` 执行（`hosts/windows/src/tools/terminal/mod.rs:647`）。
PTY 输出缓冲上限 `PTY_OUTPUT_LIMIT` 为 1 MiB（`hosts/windows/src/tools/terminal/mod.rs:25`）。
`appendPtyOutput` 在缓冲超过 `PTY_OUTPUT_LIMIT` 时从队首丢弃旧字节（`hosts/windows/src/tools/terminal/mod.rs:740`）。
PTY 提示标记前缀 `PTY_PROMPT_MARKER_PREFIX` 的值为 ESC ] 133 ; OperitPrompt =（`hosts/windows/src/tools/terminal/mod.rs:26`）。
`findLastPtyPromptMarker` 在 PTY 输出中定位最后一个提示标记（`hosts/windows/src/tools/terminal/mod.rs:991`）。
提示标记载荷以冒号分隔，冒号前为退出码、后为工作目录（`hosts/windows/src/tools/terminal/mod.rs:1006`）。
新建 PTY 会话等待初始提示最长 10000 毫秒（`hosts/windows/src/tools/terminal/mod.rs:615`）。
命令完成以 `quietPeriod` 150 毫秒静默期确认提示标记后的命令完成（`hosts/windows/src/tools/terminal/mod.rs:851`）。
会话已有命令运行时再次执行返回 Terminal session already has a command in progress 错误（`hosts/windows/src/tools/terminal/mod.rs:345`）。
命令超时时返回 exitCode -1 与 timedOut true（`hosts/windows/src/tools/terminal/mod.rs:921`）。
超时取消先向 PTY 写 0x03，再以 `COMMAND_CANCEL_SETTLE_TIMEOUT_MS` 为限等待 shell 就绪（`hosts/windows/src/tools/terminal/mod.rs:936`）。
`createOrGetSession` 在默认 powershell 类型上创建或复用会话（`hosts/windows/src/tools/terminal/mod.rs:264`）。
同名会话仍存在时直接复用，返回结果的 `isNewSession` 为 false（`hosts/windows/src/tools/terminal/mod.rs:286`）。
`executeHiddenCommand` 执行隐藏命令并返回 `HiddenTerminalCommandOutput`（`hosts/windows/src/tools/terminal/mod.rs:407`）。
隐藏命令的空 `executorKey` 记为 default（`hosts/windows/src/tools/terminal/mod.rs:417`）。
隐藏命令固定使用 `PRIMARY_TERMINAL_TYPE`，即 PowerShell（`hosts/windows/src/tools/terminal/mod.rs:414`）。
`listSessions` 枚举 PTY 会话并用 `try_wait` 刷新退出状态（`hosts/windows/src/tools/terminal/mod.rs:236`）。
会话列表条目的 `sessionKind` 为 pty（`hosts/windows/src/tools/terminal/mod.rs:254`）。
会话屏幕输出的 rows 取自内容行数，cols 取自最长行的字符数（`hosts/windows/src/tools/terminal/mod.rs:494`）。
`pollPtyExitCode` 对不存在的会话返回 PTY session does not exist 错误（`hosts/windows/src/tools/terminal/mod.rs:203`）。
PTY 子进程退出码经 `try_wait` 查询（`hosts/windows/src/tools/terminal/mod.rs:212`）。
`PtySession` 析构时先 kill 再 wait 回收子进程（`hosts/windows/src/tools/terminal/mod.rs:73`）。
会话输入在未提供 input 且 control 经 `normalizeControl` 后为空时返回错误（`hosts/windows/src/tools/terminal/mod.rs:448`）。
`controlToSequence` 把 enter、tab、esc 与方向键映射为控制序列（`hosts/windows/src/tools/terminal/mod.rs:1530`）。
`normalizeControl` 把 return 与 escape 归一化为 enter 与 esc（`hosts/windows/src/tools/terminal/mod.rs:1584`）。

### 进程与后台命令

`background_command` 以 `CREATE_NO_WINDOW` 创建后台命令，不分配 Windows 控制台窗口（`hosts/windows/src/process.rs:10`）。
Reveal 动作调用 `explorer.exe`，非目录目标附加 /select, 参数（`hosts/windows/src/tools/runtime/mod.rs:122`）。
Terminal 动作启动 `cmd.exe` 加 /k（`hosts/windows/src/tools/runtime/mod.rs:129`）。
托管运行时工作目录位于 `LOCALAPPDATA` 下的 app.operit/Operit2/managed-runtime（`hosts/windows/src/tools/runtime/mod.rs:149`）。
托管运行时按程序名解析 `node.exe`、`python.exe`、`uv.exe` 或 `pnpm.cmd`（`hosts/windows/src/tools/runtime/mod.rs:174`）。
托管运行时子进程的 stdin、stdout、stderr 均以 `Stdio` 的 piped 模式连接（`hosts/windows/src/tools/runtime/mod.rs:201`）。
托管运行时 stderr 缓冲上限 400 行，超限丢弃旧行（`hosts/windows/src/tools/runtime/mod.rs:238`）。
`runRuntimeCommand` 运行一次性托管运行时命令并捕获输出（`hosts/windows/src/tools/runtime/mod.rs:261`）。
`writeManagedRuntimeLine` 按 4 KiB 阈值区分大小帧写入（`hosts/windows/src/tools/runtime/mod.rs:286`）。

### daemon：命名管道控制端点

`control_endpoint` 把身份控制端点解析为命名管道路径，不使用文件系统 socket 探测（`hosts/windows/src/daemon.rs:29`）。
控制端点路径格式为 operit2- 加身份哈希加 -control 的命名管道名（`hosts/windows/src/daemon.rs:30`）。
`ensure_private_dir` 用 `create_dir_all` 创建 daemon 目录（`hosts/windows/src/daemon.rs:35`）。
`private_open_options` 返回未附加额外权限设置的 `OpenOptions`，daemon 文件继承身份目录的 Windows 权限（`hosts/windows/src/daemon.rs:39`）。
`cleanup_endpoint` 直接返回成功，把命名管道生命周期留给内核与打开的句柄（`hosts/windows/src/daemon.rs:45`）。
`create_pipe` 以 SDDL D:P(A;;GA;;;{sid}) 创建仅当前进程用户可访问的管道（`hosts/windows/src/daemon.rs:103`）。
daemon 管道创建时以 `reject_remote_clients` 为 true 拒绝远程客户端（`hosts/windows/src/daemon.rs:128`）。
`ControlListener` 的 `bind` 独占该身份的管道名（`hosts/windows/src/daemon.rs:143`）。
`accept` 在交出已连接实例前先调用 `create_pipe` 创建下一个管道实例（`hosts/windows/src/daemon.rs:151`）。
`connect` 在管道忙时等待 20 毫秒后重试连接（`hosts/windows/src/daemon.rs:160`）。
`spawn_detached` 以 `DETACHED_PROCESS` 与 `CREATE_NEW_PROCESS_GROUP` 标志启动 daemon，不带控制台且不挂接调用方进程组（`hosts/windows/src/daemon.rs:175`）。
`termination_signal` 同时监听控制台关闭、注销与系统关机三类 Windows 信号（`hosts/windows/src/daemon.rs:181`）。

### 与 Unix 平台的不同（Windows 侧事实）

Windows daemon 控制端点是命名管道，不使用文件系统 socket 探测（`hosts/windows/src/daemon.rs:29`）。
Windows 后台命令以 `CREATE_NO_WINDOW` 创建，不分配控制台窗口（`hosts/windows/src/process.rs:10`）。
Windows daemon 脱离调用方用 `DETACHED_PROCESS` 与 `CREATE_NEW_PROCESS_GROUP` 标志（`hosts/windows/src/daemon.rs:175`）。
Windows 终止信号监听控制台关闭、注销与系统关机（`hosts/windows/src/daemon.rs:181`）。
Windows Bash 只解析随包提供的 bash/bin/bash.exe（`hosts/windows/src/tools/terminal/mod.rs:693`）。
Windows 文件路径校验只接受绝对 Windows 路径（`hosts/windows/src/tools/fs/mod.rs:42`）。
Windows 密钥经 `CredReadW` 存取 Windows Credential Manager（`hosts/windows/src/tools/storage/mod.rs:53`）。
Windows Plugin SDK IPC 走命名管道，管道路径由 `pipeName` 映射（`hosts/windows/src/plugin_sdk_ipc.rs:84`）。

### 文件系统与存储

文件系统 Host 的 `envLabel` 为 windows（`hosts/windows/src/tools/fs/mod.rs:34`）。
文件系统 Host 的 `environmentDescriptor` 返回 `HostEnvironmentDescriptor` 的 windows 描述（`hosts/windows/src/tools/fs/mod.rs:39`）。
`validatePath` 只接受绝对路径，非绝对路径报错 Path must be an absolute Windows path（`hosts/windows/src/tools/fs/mod.rs:42`）。
用 `ShellExecuteW` 以系统默认应用打开文件（`hosts/windows/src/tools/fs/mod.rs:482`）。
在独立平台任务线程上以 `COINIT_APARTMENTTHREADED` 初始化 COM（`hosts/windows/src/tools/fs/mod.rs:467`）。
通过 PowerShell 调用 Shell 项的 `InvokeVerb` 打开 Windows 分享面板（`hosts/windows/src/tools/fs/mod.rs:522`）。
代码搜索以 `BinaryDetection` 的 quit 模式在 NUL 字节处停止（`hosts/windows/src/tools/fs/mod.rs:339`）。
压缩使用 `CompressionMethod` 的 Deflated 方法（`hosts/windows/src/tools/fs/mod.rs:401`）。
`zipFiles` 把文件或目录打包为 ZIP（`hosts/windows/src/tools/fs/mod.rs:389`）。
`unzipFiles` 解压 ZIP 到目标目录（`hosts/windows/src/tools/fs/mod.rs:421`）。
默认运行时根目录为 `APPDATA` 下的 Operit2/runtime（`hosts/windows/src/tools/storage/mod.rs:28`）。
默认工作区根目录为 `APPDATA` 下的 Operit2/workspaces（`hosts/windows/src/tools/storage/mod.rs:36`）。
`readSecret` 用 `CredReadW` 读 Windows Credential Manager，未找到返回 None（`hosts/windows/src/tools/storage/mod.rs:53`）。
`writeSecret` 以 Operit2 为用户名写入凭据（`hosts/windows/src/tools/storage/mod.rs:76`）。
凭据持久化级别为 `CRED_PERSIST_LOCAL_MACHINE`（`hosts/windows/src/tools/storage/mod.rs:88`）。
`deleteSecret` 用 `CredDeleteW` 删除凭据，未找到时不报错（`hosts/windows/src/tools/storage/mod.rs:106`）。
密钥键只允许 ASCII 字母数字与 . _ -（`hosts/windows/src/tools/storage/mod.rs:130`）。
`windowsSecretTargetName` 把密钥键拼为 Operit2: 加键名的目标名（`hosts/windows/src/tools/storage/mod.rs:133`）。

### 系统操作

`applicationUpdateTarget` 转发给 application_update 的 `target`（`hosts/windows/src/tools/system/mod.rs:40`）。
`installApp` 按 `AppInstallTiming` 分流：Immediate 立即安装，AfterProcessExit 走 application_update 的 `prepare`（`hosts/windows/src/tools/system/mod.rs:68`）。
`request_windows_install_app` 先尝试 `installPortableApp` 安装便携应用（`hosts/windows/src/tools/system/mod.rs:570`）。
.msix 与 .appx 包经 `Add-AppxPackage` 安装，.msi 包经 msiexec 安装并接受退出码 0、1641 与 3010（`hosts/windows/src/tools/system/mod.rs:588`）。
.exe 安装只打开安装程序，状态记为 `installer_opened`，安装结果未经验证（`hosts/windows/src/tools/system/mod.rs:594`）。
通知经 `ToastNotificationManager` 以 app.operit.operit2 为 ID 创建通知器发出（`hosts/windows/src/tools/system/mod.rs:150`）。
通知激活地址为 operit2://notification/open-app，打开指定会话时带 chatId 参数（`hosts/windows/src/tools/system/mod.rs:165`）。
系统语言经 `GetUserDefaultLocaleName` 读取（`hosts/windows/src/tools/system/mod.rs:468`）。
系统设置命名空间 system、secure、global 映射到 `HKCU` 下 Software\Operit2 的子键（`hosts/windows/src/tools/system/mod.rs:543`）。
Windows Host 明确表示不暴露历史前台使用时长且未配置使用记录器（`hosts/windows/src/tools/system/mod.rs:779`）。
定位用 WinRT `Geolocator` 完成（`hosts/windows/src/tools/system/mod.rs:791`）。
定位结果的 provider 为 `windows-geolocator`（`hosts/windows/src/tools/system/mod.rs:853`）。
截图用 PowerShell 的 `CopyFromScreen` 截取整个虚拟桌面（`hosts/windows/src/tools/system/mod.rs:214`）。
文本识别用 Windows.Media.Ocr 的 `OcrEngine` 的 `TryCreateFromLanguage` 创建引擎（`hosts/windows/src/tools/system/mod.rs:296`）。
OCR 语言映射为 en-US、zh-Hans、ja、ko 四种标签（`hosts/windows/src/tools/system/mod.rs:391`）。
OCR 高质量模式把图片放大 2 倍，但放大后宽或高超过 4096 时不放大（`hosts/windows/src/tools/system/mod.rs:353`）。
通知历史通过 `UserNotificationListener` 的 Current 实例读取（`hosts/windows/src/tools/system/mod.rs:684`）。
读取通知历史前须请求监听权限，未获 Allowed 即报错（`hosts/windows/src/tools/system/mod.rs:690`）。
`listInstalledApps` 调用 packages 的 `list` 枚举已安装应用（`hosts/windows/src/tools/system/mod.rs:78`）。
`uninstallApp` 转发给 packages 的 `operation`（`hosts/windows/src/tools/system/mod.rs:73`）。
`startApp` 转发给 packages 的 `operation`（`hosts/windows/src/tools/system/mod.rs:81`）。
`stopApp` 转发给 packages 的 `operation`（`hosts/windows/src/tools/system/mod.rs:85`）。
应用目录枚举注册表 Uninstall 项与 `Get-AppxPackage` 的 Appx 包（`hosts/windows/src/tools/system/packages.rs:8`）。
Win32 应用 ID 前缀为 win32:，Appx 应用 ID 前缀为 appx:（`hosts/windows/src/tools/system/packages.rs:10`）。
`Resolve-App` 要求应用恰好匹配一项，否则报错（`hosts/windows/src/tools/system/packages.rs:14`）。
`Resolve-Executable` 从注册表 DisplayIcon 或安装目录解析应用可执行文件（`hosts/windows/src/tools/system/packages.rs:19`）。
受保护的系统组件不允许经 uninstall 卸载（`hosts/windows/src/tools/system/packages.rs:89`）。
启动 Appx 应用时经 explorer 打开 `shell:AppsFolder` 入口（`hosts/windows/src/tools/system/packages.rs:64`）。
`stop` 拒绝停止当前操作宿主自身的进程（`hosts/windows/src/tools/system/packages.rs:75`）。
MSI 应用卸载经 `msiexec.exe` 加 /x 执行（`hosts/windows/src/tools/system/packages.rs:97`）。
`list` 按 includeSystemApps 过滤是否包含系统应用（`hosts/windows/src/tools/system/packages.rs:33`）。

### 应用更新

更新目标返回 `AfterProcessExit` 时序，MSI 安装对应 `WindowsMsi`，否则对应 `WindowsZip`（`hosts/windows/src/tools/system/application_update.rs:34`）。
`installation` 经 PowerShell 的 `Get-OperitInstallation` 查询当前可执行文件的 MSI 归属（`hosts/windows/src/tools/system/application_update.rs:21`）。
`prepare` 要求更新包为绝对路径的可读文件（`hosts/windows/src/tools/system/application_update.rs:49`）。
便携版安装的更新经 `installPortableApp` 处理，非 ZIP 包报错（`hosts/windows/src/tools/system/application_update.rs:55`）。
MSI 安装只接受扩展名为 msi 的更新包（`hosts/windows/src/tools/system/application_update.rs:60`）。
更新助手启动后等待其 ready 确认再返回，安装状态为 `RestartRequired`（`hosts/windows/src/tools/system/application_update.rs:85`）。
更新助手以 installer-令牌.ready 与 installer-令牌.log 两个文件与主进程握手（`hosts/windows/src/tools/system/application_update.rs:67`）。
更新脚本以 UpgradeCode {A60B4E40-8A60-4BCD-AB33-DA7D939E436D} 识别 Operit MSI 产品族（`hosts/windows/src/tools/system/application_update.ps1:2`）。
`Get-OperitRegisteredFolder` 从 HKCU 的 Software\Operit\Operit2\Installer 读取 `InstallLocation`（`hosts/windows/src/tools/system/application_update.ps1:16`）。
`Get-OperitInstallation` 要求当前用户恰好注册一个 Operit MSI 产品（`hosts/windows/src/tools/system/application_update.ps1:45`）。
`Assert-OperitMsiUpdate` 校验更新包的 UpgradeCode、产品名 Operit2 与厂商 Operit（`hosts/windows/src/tools/system/application_update.ps1:98`）。
更新包必须是按用户安装的 x64 MSI（`hosts/windows/src/tools/system/application_update.ps1:102`）。
更新 MSI 文件名必须为 operit2-app-windows-x86_64-加版本号加 .msi（`hosts/windows/src/tools/system/application_update.ps1:105`）。
MSI 更新必须包含更新的产品版本与新的产品代码（`hosts/windows/src/tools/system/application_update.ps1:110`）。
更新助手发布 ready 标记后等待父进程完全退出（`hosts/windows/src/tools/system/application_update.ps1:144`）。
等待期间若发现同安装的另一实例在运行，更新中止并报错（`hosts/windows/src/tools/system/application_update.ps1:147`）。
父进程退出后更新助手重新核对已安装产品与更新包的身份（`hosts/windows/src/tools/system/application_update.ps1:152`）。
更新以 `msiexec.exe` 加 /qn /norestart 静默安装（`hosts/windows/src/tools/system/application_update.ps1:159`）。
msiexec 返回 3010 时更新结果记为 `system_restart_required` 并提示重启 Windows（`hosts/windows/src/tools/system/application_update.ps1:162`）。
安装成功后更新助手重新启动可执行文件（`hosts/windows/src/tools/system/application_update.ps1:172`）。
更新结果以 JSON 写入日志路径加 .result.json 的文件（`hosts/windows/src/tools/system/application_update.ps1:117`）。

### MCI 与音频

MCI 命令经 `runPlatformTask` 在 windows-mci 平台任务线程上执行 `mciSendStringW`（`hosts/windows/src/tools/mci.rs:8`）。
MCI 查询响应缓冲为 256 个 UTF-16 单元（`hosts/windows/src/tools/mci.rs:10`）。
MCI 错误文本经 `mciGetErrorStringW` 取回，缓冲 512 个 UTF-16 单元（`hosts/windows/src/tools/mci.rs:24`）。
`mciCommand` 发无响应命令，`mciCommandWithResponse` 发带响应查询的命令（`hosts/windows/src/tools/mci.rs:42`）。
MCI 别名在其整个生命周期内保持在同一可复用平台线程上（`hosts/windows/src/tools/mci.rs:5`）。
单次音频以 operit_audio_ 加 UUID 为别名打开音频文件（`hosts/windows/src/tools/audio/mod.rs:120`）。
单次音频播放结束后 500 毫秒由延迟任务关闭 MCI 别名（`hosts/windows/src/tools/audio/mod.rs:133`）。
`playMusic` 只接受 sourceType 为 path 的音乐源（`hosts/windows/src/tools/audio/mod.rs:153`）。
音乐音量 0 到 1 映射为 MCI 的 `setaudio` 0 到 1000（`hosts/windows/src/tools/audio/mod.rs:100`）。
循环播放时 MCI 命令为 play 加 from 加 `repeat`（`hosts/windows/src/tools/audio/mod.rs:173`）。
音乐状态经 MCI 查询 `mode` 与 `position` 得到（`hosts/windows/src/tools/audio/mod.rs:45`）。
音乐总时长经 MCI 查询 `length` 得到（`hosts/windows/src/tools/audio/mod.rs:54`）。
无活动音乐会话时 `pauseMusic` 返回已停止的空闲状态（`hosts/windows/src/tools/audio/mod.rs:205`）。
seek 先查 MCI 的 mode，播放中则以 play 从新位置继续（`hosts/windows/src/tools/audio/mod.rs:238`）。
`setMusicVolume` 经 `setMusicVolumeForAlias` 更新当前会话音量（`hosts/windows/src/tools/audio/mod.rs:254`）。
`musicStatus` 经 `statusForSession` 返回当前音乐状态（`hosts/windows/src/tools/audio/mod.rs:264`）。
`quotedMciPath` 拒绝含双引号的音频路径（`hosts/windows/src/tools/audio/mod.rs:285`）。

### TTS

`WindowsTtsPlaybackHost` 报告 `supportsSystemSpeech` 为 true（`hosts/windows/src/tools/tts/mod.rs:59`）。
合成只支持 wav 输出格式（`hosts/windows/src/tools/tts/mod.rs:202`）。
合成经 PowerShell 调用 System.Speech 的 `SpeechSynthesizer` 完成（`hosts/windows/src/tools/tts/mod.rs:272`）。
合成输出由 `SetOutputToWaveFile` 写为 WAV 文件（`hosts/windows/src/tools/tts/mod.rs:291`）。
语速换算为 System.Speech 的 Rate：(speed 减 1) 乘 10，范围负 10 到 10（`hosts/windows/src/tools/tts/mod.rs:443`）。
Windows System.Speech 合成只支持 pitch 1.0（`hosts/windows/src/tools/tts/mod.rs:456`）。
新的朗读请求在已有合成或播放进行中且未指定 interrupt 时返回 busy 错误（`hosts/windows/src/tools/tts/mod.rs:100`）。
朗读中途被新请求打断时，旧合成的临时音频文件会被删除（`hosts/windows/src/tools/tts/mod.rs:123`）。
TTS 播放以 operit_tts_ 加 UUID 为 MCI 别名（`hosts/windows/src/tools/tts/mod.rs:369`）。
TTS 临时文件位于系统临时目录下的 operit_tts 目录（`hosts/windows/src/tools/tts/mod.rs:421`）。
TTS 播放 Host 的 `playAudio` 直接播放已生成的语音音频文件（`hosts/windows/src/tools/tts/mod.rs:64`）。
`speechState` 返回当前语音播放状态（`hosts/windows/src/tools/tts/mod.rs:188`）。
`stopSpeech` 递增 generation 使进行中的合成失效并停止播放（`hosts/windows/src/tools/tts/mod.rs:180`）。

### 蓝牙

Windows Host 声明 `supportsClassicListening` 为 true（`hosts/windows/src/tools/bluetooth/mod.rs:100`）。
Windows 蓝牙无需单独请求权限，返回 windows_bluetooth_permission_not_required（`hosts/windows/src/tools/bluetooth/mod.rs:103`）。
`bluetoothState` 按是否枚举到蓝牙电台返回 unavailable 或 enabled（`hosts/windows/src/tools/bluetooth/mod.rs:111`）。
Windows 上启用蓝牙必须在系统设置中更改，`requestEnableBluetooth` 返回错误（`hosts/windows/src/tools/bluetooth/mod.rs:122`）。
Windows 蓝牙扫描只返回 `classic` 设备（`hosts/windows/src/tools/bluetooth/mod.rs:146`）。
Windows 蓝牙扫描结果的 `includesBle` 为 false（`hosts/windows/src/tools/bluetooth/mod.rs:158`）。
扫描在枚举后按 `durationMs` 睡眠等待查询完成（`hosts/windows/src/tools/bluetooth/mod.rs:157`）。
已配对设备列表只含已认证或已记住的设备（`hosts/windows/src/tools/bluetooth/mod.rs:128`）。
经典蓝牙连接经 WinSock 的 `connect` 建立（`hosts/windows/src/tools/bluetooth/mod.rs:177`）。
经典蓝牙套接字以 `AF_BTH` 地址族、`SOCK_STREAM` 类型与 `BTHPROTO_RFCOMM` 协议创建（`hosts/windows/src/tools/bluetooth/mod.rs:865`）。
经典蓝牙监听先 `bind` 套接字（`hosts/windows/src/tools/bluetooth/mod.rs:219`）。
经典蓝牙监听以 `listen` 积压 1 建立（`hosts/windows/src/tools/bluetooth/mod.rs:232`）。
经典蓝牙会话 ID 前缀为 windows-bt-classic-（`hosts/windows/src/tools/bluetooth/mod.rs:190`）。
蓝牙监听会话 ID 前缀为 windows-bt-listener-（`hosts/windows/src/tools/bluetooth/mod.rs:239`）。
`bluetoothAccept` 只接受监听会话，非监听会话返回错误（`hosts/windows/src/tools/bluetooth/mod.rs:251`）。
BLE 连接经 `BluetoothLEDevice` 的 `FromBluetoothAddressAsync` 建立（`hosts/windows/src/tools/bluetooth/mod.rs:388`）。
BLE 会话 ID 前缀为 windows-ble-（`hosts/windows/src/tools/bluetooth/mod.rs:392`）。
BLE 服务发现使用 `BluetoothCacheMode` 的 Uncached 模式（`hosts/windows/src/tools/bluetooth/mod.rs:417`）。
BLE 特征值写入使用 `WriteWithResponse` 选项（`hosts/windows/src/tools/bluetooth/mod.rs:527`）。
BLE 订阅经客户端特征配置描述符写入 `Notify` 启用通知（`hosts/windows/src/tools/bluetooth/mod.rs:612`）。
蓝牙电台枚举经 `BluetoothFindFirstRadio` 完成（`hosts/windows/src/tools/bluetooth/mod.rs:781`）。
WinSock 以 `WSAStartup` 0x0202 初始化一次（`hosts/windows/src/tools/bluetooth/mod.rs:852`）。

### 浏览器与 HTTP

浏览器候选路径优先取 `OPERIT_BROWSER_PATH` 环境变量（`hosts/windows/src/tools/browser/mod.rs:57`）。
浏览器候选包括 `msedge.exe`、`chrome.exe` 与 `chromium.exe` 及 Edge 与 Chrome 的 Program Files 路径（`hosts/windows/src/tools/browser/mod.rs:65`）。
`WindowsWebVisitHost` 的 `visitWeb` 经 `visit_with_chromium` 访问网页（`hosts/windows/src/tools/browser/mod.rs:30`）。
`WindowsBrowserAutomationHost` 的 `executeBrowserTool` 转发给内部 Chromium 自动化 Host（`hosts/windows/src/tools/browser/mod.rs:51`）。
`WindowsHttpHost` 内部持有 `NativeHttpHost` 并转发请求（`hosts/windows/src/tools/http/mod.rs:60`）。
`executeHttpRequest` 与 `imageDelivery` 均转发给内部原生 HTTP Host（`hosts/windows/src/tools/http/mod.rs:67`）。

### Plugin SDK IPC：命名管道

Plugin SDK 激活 URI 为 `operit2://plugin-sdk`（`hosts/windows/src/plugin_sdk_ipc.rs:33`）。
Plugin SDK 管道就绪等待超时为 30 秒（`hosts/windows/src/plugin_sdk_ipc.rs:34`）。
`WindowsPluginSdkIpcHost` 从 `OPERIT_PLUGIN_SDK_INSTANCE` 环境变量取实例名（`hosts/windows/src/plugin_sdk_ipc.rs:60`）。
`pipeName` 把端点名映射为命名管道路径，点号替换为下划线（`hosts/windows/src/plugin_sdk_ipc.rs:84`）。
Plugin SDK 会话 ID 格式为 `plugin-sdk-windows-` 加序号（`hosts/windows/src/plugin_sdk_ipc.rs:95`）。
`activate` 先以 `WaitNamedPipeW` 探测管道，若已存在直接返回（`hosts/windows/src/plugin_sdk_ipc.rs:168`）。
管道不存在且未指定实例时，经 `ShellExecuteW` 打开 operit2 协议 URI 启动 Operit（`hosts/windows/src/plugin_sdk_ipc.rs:179`）。
已指定实例但管道不存在时报错，要求先启动选定的 Plugin SDK 实例（`hosts/windows/src/plugin_sdk_ipc.rs:172`）。
监听器以 `CreateNamedPipeW` 创建双工命名管道，实例数不限（`hosts/windows/src/plugin_sdk_ipc.rs:238`）。
监听器已启动时再次启动返回错误（`hosts/windows/src/plugin_sdk_ipc.rs:227`）。
客户端连接经 `CreateFileW` 以读写方式打开已存在的命名管道（`hosts/windows/src/plugin_sdk_ipc.rs:296`）。
会话附加时把管道文件克隆为独立的读写句柄（`hosts/windows/src/plugin_sdk_ipc.rs:131`）。
`stopListener` 停止监听器并关闭监听器拥有的会话（`hosts/windows/src/plugin_sdk_ipc.rs:343`）。
管道异步操作以 `CreateEventW` 创建手动复位事件等待完成（`hosts/windows/src/plugin_sdk_pipe.rs:25`）。
管道操作完成等待以 25 毫秒轮询事件（`hosts/windows/src/plugin_sdk_pipe.rs:39`）。
会话关闭时以 `CancelIoEx` 取消未完成的管道操作（`hosts/windows/src/plugin_sdk_pipe.rs:50`）。
管道接受时已连接的客户端直接返回成功（`hosts/windows/src/plugin_sdk_pipe.rs:139`）。
管道读以 `ReadFile` 发起重叠读取（`hosts/windows/src/plugin_sdk_pipe.rs:85`）。
管道写以 `WriteFile` 发起重叠写入（`hosts/windows/src/plugin_sdk_pipe.rs:112`）。
管道写的 `flush` 为空操作，每次写已等待内核完成（`hosts/windows/src/plugin_sdk_pipe.rs:128`）。

## 关键符号

- `createRuntimeHostManager` — 组装 Windows 自有的运行时 `HostManager`（`hosts/windows/src/lib.rs:34`）
- `WindowsTerminalHost` — Windows PTY 终端 Host（`hosts/windows/src/lib.rs:30`）
- `WindowsFileSystemHost` — Windows 文件系统 Host（`hosts/windows/src/lib.rs:25`）
- `WindowsSystemOperationHost` — Windows 系统操作 Host（`hosts/windows/src/lib.rs:29`）
- `WindowsManagedRuntimeHost` — Windows 托管运行时 Host（`hosts/windows/src/lib.rs:27`）
- `WindowsRuntimeStorageHost` — Windows 运行时存储 Host（`hosts/windows/src/lib.rs:28`）
- `WindowsHttpHost` — Windows HTTP Host（`hosts/windows/src/lib.rs:26`）
- `WindowsAudioPlaybackHost` — Windows 音频播放 Host（`hosts/windows/src/lib.rs:22`）
- `WindowsBluetoothHost` — Windows 蓝牙 Host（`hosts/windows/src/lib.rs:23`）
- `WindowsTtsSynthesisHost` — Windows TTS 合成 Host（`hosts/windows/src/lib.rs:31`）
- `WindowsTtsPlaybackHost` — Windows TTS 播放 Host（`hosts/windows/src/lib.rs:31`）
- `WindowsPluginSdkIpcHost` — Windows Plugin SDK IPC Host（`hosts/windows/src/lib.rs:21`）
- `WindowsWebVisitHost` — Windows 网页访问 Host（`hosts/windows/src/lib.rs:24`）
- `WindowsBrowserAutomationHost` — Windows 浏览器自动化 Host（`hosts/windows/src/lib.rs:24`）
- `WindowsHostRuntimeEventHost` — Windows 运行时事件 Host（`hosts/windows/src/lib.rs:17`）
- `control_endpoint` — 把身份控制端点解析为命名管道路径（`hosts/windows/src/daemon.rs:29`）
- `ControlListener` — 拥有待接受管道实例的 daemon 控制监听器（`hosts/windows/src/daemon.rs:136`）
- `spawn_detached` — 以脱离标志启动 daemon（`hosts/windows/src/daemon.rs:173`）
- `termination_signal` — 监听控制台关闭、注销与系统关机（`hosts/windows/src/daemon.rs:180`）
- `background_command` — 以 `CREATE_NO_WINDOW` 创建后台命令（`hosts/windows/src/process.rs:8`）
- `createPtySession` — 创建 PTY 会话（`hosts/windows/src/tools/terminal/mod.rs:567`）
- `normalizeTerminalType` — 只接受 powershell 与 bash 两种终端类型（`hosts/windows/src/tools/terminal/mod.rs:1620`）
- `bundledBashExecutable` — 解析随包 Bash 可执行文件（`hosts/windows/src/tools/terminal/mod.rs:688`）
- `findLastPtyPromptMarker` — 定位最后一个 PTY 提示标记（`hosts/windows/src/tools/terminal/mod.rs:991`）
- `validatePath` — 只接受绝对 Windows 路径（`hosts/windows/src/tools/fs/mod.rs:42`）
- `readSecret` — 用 `CredReadW` 读 Windows Credential Manager（`hosts/windows/src/tools/storage/mod.rs:51`）
- `writeSecret` — 以 Operit2 为用户名写入凭据（`hosts/windows/src/tools/storage/mod.rs:73`）
- `applicationUpdateTarget` — 转发给 application_update 的 `target`（`hosts/windows/src/tools/system/mod.rs:37`）
- `target` — 解析本应用副本的更新包格式（`hosts/windows/src/tools/system/application_update.rs:31`）
- `prepare` — 校验更新包为绝对路径的可读文件（`hosts/windows/src/tools/system/application_update.rs:49`）
- `Get-OperitInstallation` — 查询当前可执行文件的 MSI 归属（`hosts/windows/src/tools/system/application_update.ps1:48`）
- `Assert-OperitMsiUpdate` — 校验更新包属于 Operit MSI 产品族（`hosts/windows/src/tools/system/application_update.ps1:96`）
- `Invoke-OperitMsiUpdate` — 运行一次无人值守升级（`hosts/windows/src/tools/system/application_update.ps1:129`）
- `mciCommand` — 发无响应 MCI 命令（`hosts/windows/src/tools/mci.rs:42`）
- `mciCommandWithResponse` — 发带响应查询的 MCI 命令（`hosts/windows/src/tools/mci.rs:47`）
- `statusForSession` — 经 MCI 查询音乐会话状态（`hosts/windows/src/tools/audio/mod.rs:40`）
- `synthesizeSpeech` — 合成一句语音为 WAV 文件（`hosts/windows/src/tools/tts/mod.rs:196`）
- `speakText` — 朗读一句文本（`hosts/windows/src/tools/tts/mod.rs:87`）
- `supportsClassicListening` — 声明支持经典蓝牙入站监听（`hosts/windows/src/tools/bluetooth/mod.rs:100`）
- `bluetoothBleConnect` — 经 WinRT 建立 BLE 连接（`hosts/windows/src/tools/bluetooth/mod.rs:383`）
- `pipeName` — 把端点名映射为命名管道路径（`hosts/windows/src/plugin_sdk_ipc.rs:79`）
- `activate` — 探测命名管道是否已存在（`hosts/windows/src/plugin_sdk_ipc.rs:166`）
- `startListener` — 启动 Plugin SDK IPC 监听器（`hosts/windows/src/plugin_sdk_ipc.rs:217`）
- `connect` — 连接 Plugin SDK 命名管道（`hosts/windows/src/plugin_sdk_ipc.rs:289`）
- `PipeIo` — 在双工命名管道上做独立重叠读写（`hosts/windows/src/plugin_sdk_pipe.rs:71`）
- `accept` — 接受一个重叠管道连接（`hosts/windows/src/plugin_sdk_pipe.rs:133`）

## 调用链

### 应用更新（MSI 安装）

1. `installApp` 在 `AfterProcessExit` 时序下调用 application_update 的 `prepare`（`hosts/windows/src/tools/system/mod.rs:68`）
2. `prepare` 校验更新包为绝对路径的可读文件（`hosts/windows/src/tools/system/application_update.rs:49`）
3. prepare 校验 MSI 安装只接受扩展名为 msi 的更新包（`hosts/windows/src/tools/system/application_update.rs:60`）
4. 更新助手启动后等待其 ready 确认再返回，安装状态为 `RestartRequired`（`hosts/windows/src/tools/system/application_update.rs:85`）
5. 更新助手发布 ready 标记后等待父进程完全退出（`hosts/windows/src/tools/system/application_update.ps1:144`）
6. 更新以 `msiexec.exe` 加 /qn /norestart 静默安装（`hosts/windows/src/tools/system/application_update.ps1:159`）
7. 安装成功后更新助手重新启动可执行文件（`hosts/windows/src/tools/system/application_update.ps1:172`）

### 终端命令执行

1. `createOrGetSession` 在默认 powershell 类型上创建或复用会话（`hosts/windows/src/tools/terminal/mod.rs:264`）
2. `ptyCommandLine` 把 Bash 命令交给 terminal_command 的 `posixCommandLine` 编码（`hosts/windows/src/tools/terminal/mod.rs:641`）
3. 含控制字符的 PowerShell 命令经 Base64 编码后由 `Invoke-Expression` 执行（`hosts/windows/src/tools/terminal/mod.rs:647`）
4. `findLastPtyPromptMarker` 在 PTY 输出中定位最后一个提示标记（`hosts/windows/src/tools/terminal/mod.rs:991`）
5. 命令完成以 `quietPeriod` 150 毫秒静默期确认提示标记后的命令完成（`hosts/windows/src/tools/terminal/mod.rs:851`）
6. 命令超时时返回 exitCode -1 与 timedOut true（`hosts/windows/src/tools/terminal/mod.rs:921`）

### Plugin SDK IPC

1. `activate` 先以 `WaitNamedPipeW` 探测管道，若已存在直接返回（`hosts/windows/src/plugin_sdk_ipc.rs:168`）
2. 管道不存在且未指定实例时，经 `ShellExecuteW` 打开 operit2 协议 URI 启动 Operit（`hosts/windows/src/plugin_sdk_ipc.rs:179`）
3. 客户端连接经 `CreateFileW` 以读写方式打开已存在的命名管道（`hosts/windows/src/plugin_sdk_ipc.rs:296`）
4. 会话附加时把管道文件克隆为独立的读写句柄（`hosts/windows/src/plugin_sdk_ipc.rs:131`）
5. 管道读以 `ReadFile` 发起重叠读取（`hosts/windows/src/plugin_sdk_pipe.rs:85`）
6. 管道写以 `WriteFile` 发起重叠写入（`hosts/windows/src/plugin_sdk_pipe.rs:112`）

### TTS 朗读

1. 新的朗读请求在已有合成或播放进行中且未指定 interrupt 时返回 busy 错误（`hosts/windows/src/tools/tts/mod.rs:100`）
2. 合成经 PowerShell 调用 System.Speech 的 `SpeechSynthesizer` 完成（`hosts/windows/src/tools/tts/mod.rs:272`）
3. 合成输出由 `SetOutputToWaveFile` 写为 WAV 文件（`hosts/windows/src/tools/tts/mod.rs:291`）
4. TTS 播放以 operit_tts_ 加 UUID 为 MCI 别名（`hosts/windows/src/tools/tts/mod.rs:369`）
5. `speechState` 返回当前语音播放状态（`hosts/windows/src/tools/tts/mod.rs:188`）

### daemon 启动

1. `control_endpoint` 把身份控制端点解析为命名管道路径（`hosts/windows/src/daemon.rs:29`）
2. `ControlListener` 的 `bind` 独占该身份的管道名（`hosts/windows/src/daemon.rs:143`）
3. `accept` 在交出已连接实例前先调用 `create_pipe` 创建下一个管道实例（`hosts/windows/src/daemon.rs:151`）
4. `spawn_detached` 以 `DETACHED_PROCESS` 与 `CREATE_NEW_PROCESS_GROUP` 标志启动 daemon（`hosts/windows/src/daemon.rs:175`）
5. `termination_signal` 同时监听控制台关闭、注销与系统关机三类 Windows 信号（`hosts/windows/src/daemon.rs:181`）

## 来源

- hosts/windows/Cargo.toml
- hosts/windows/src/lib.rs
- hosts/windows/src/daemon.rs
- hosts/windows/src/process.rs
- hosts/windows/src/tools/terminal/mod.rs
- hosts/windows/src/tools/fs/mod.rs
- hosts/windows/src/tools/runtime/mod.rs
- hosts/windows/src/tools/storage/mod.rs
- hosts/windows/src/tools/system/mod.rs
- hosts/windows/src/tools/system/application_update.rs
- hosts/windows/src/tools/system/application_update.ps1
- hosts/windows/src/tools/system/packages.rs
- hosts/windows/src/tools/browser/mod.rs
- hosts/windows/src/tools/http/mod.rs
- hosts/windows/src/tools/audio/mod.rs
- hosts/windows/src/tools/bluetooth/mod.rs
- hosts/windows/src/tools/tts/mod.rs
- hosts/windows/src/tools/mci.rs
- hosts/windows/src/plugin_sdk_ipc.rs
- hosts/windows/src/plugin_sdk_pipe.rs
