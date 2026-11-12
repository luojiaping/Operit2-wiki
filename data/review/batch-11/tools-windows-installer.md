---
title: Windows MSI 安装器与卸载数据清理
module: tools
platforms: [windows]
sources: 7
date: 2026-11-11
---

## 概述

- 本页讲 Windows 平台的 Operit2 MSI 安装包、完整卸载界面与独立数据清理工具 Operit2DataCleanup.exe。`tools/windows-installer/README-Windows.txt:1`
- MSI 安装版在 Windows 上卸载时默认保留用户数据。`tools/windows-installer/README-Windows.txt:6`
- MSI 安装版的完整卸载界面提供勾选“同时永久删除本机用户数据”的选项，查看实际数据目录并确认后才会执行数据清理。`tools/windows-installer/README-Windows.txt:6`
- 只显示系统简化界面的卸载入口会保留数据。`tools/windows-installer/README-Windows.txt:8`
- 压缩包版运行 Operit2DataCleanup.exe，查看实际目录，确认后永久清理本机用户数据。`tools/windows-installer/README-Windows.txt:13`
- MSI 安装版的完整卸载界面使用 UserDataCleanup 生成清理计划。`tools/windows-installer/ui/SetupWindow.xaml.cs:71`
- 压缩包版的独立清理工具以当前程序所在目录构造 UserDataCleanup。`tools/windows-installer/cleanup/Program.cs:58`
- 本页只覆盖 Windows 平台。`tools/windows-installer/README-Windows.txt:1`

## AI 速览

- `UserDataCleanup` — 解析启动配置、生成并校验清理计划、执行删除与凭据清理的类。`tools/windows-installer/shared/UserDataCleanup.cs:30`
- `CleanupPlan` — 清理计划，包含 Directories、BootstrapPath、BootstrapContent 三个属性。`tools/windows-installer/shared/UserDataCleanup.cs:16`
- `CleanupWindow` — 独立清理工具窗口。`tools/windows-installer/cleanup/Program.cs:20`
- `SetupWindow` — MSI 内嵌安装、修复与卸载界面。`tools/windows-installer/ui/SetupWindow.xaml.cs:13`
- `MsiContractTests.Verify` — 检查已编译 MSI 的条件与顺序，不安装也不执行自定义操作。`tools/windows-installer/tests/MsiContractTests.cs:8`
- `build_windows_msi` — 打包流程的入口函数，接受发布目录与目标路径。`tools/build_scripts/build_windows_msi.py:103`
- MSI 安装的界面入口为 Package.wxs 声明的 EmbeddedUI。`tools/windows-installer/Package.wxs:62`
- 独立清理工具的主入口为 Program.Main，启动 CleanupWindow。`tools/windows-installer/cleanup/Program.cs:13`
- 独立清理工具窗口的标题为 Operit2 用户数据清理，窗口为 760×640。`tools/windows-installer/cleanup/Program.cs:32`
- 清理计划由 CreatePlan 从启动配置 local_runtime_storage.json 生成。`tools/windows-installer/shared/UserDataCleanup.cs:72`
- 删除执行顺序为 ValidatePlan 复核、clearCredentials 清除凭据、DeleteTree 删除目录。`tools/windows-installer/shared/UserDataCleanup.cs:119`

## 核心机制

### MSI 安装版与压缩包版：卸载数据的方式有何不同

- MSI 安装版在 Windows 设置 → 应用 → 已安装的应用中卸载，也可以通过开始菜单的 Operit2 Uninstall，或再次打开 MSI → 卸载应用。`tools/windows-installer/README-Windows.txt:4`
- MSI 安装版的完整卸载界面提供勾选“同时永久删除本机用户数据”的选项，查看实际数据目录并确认后才会执行数据清理。`tools/windows-installer/README-Windows.txt:6`
- 只显示系统简化界面的卸载入口需要清理数据时，使用完整卸载界面，或先运行本目录的 Operit2DataCleanup.exe，再卸载应用。`tools/windows-installer/README-Windows.txt:9`
- 压缩包版清理数据前先退出所有 Operit2 窗口、后台进程和命令行。`tools/windows-installer/README-Windows.txt:12`
- 压缩包版清理结束后可以删除解压的程序目录。`tools/windows-installer/README-Windows.txt:14`
- 需要先删除程序、稍后清理时，可先将 Operit2DataCleanup.exe 单独保存到其他目录。`tools/windows-installer/README-Windows.txt:15`
- MSI 普通卸载会清除属于当前安装副本的桌面、开始菜单和 operit2:// 协议入口。`tools/windows-installer/README-Windows.txt:32`
- 独立清理工具只负责数据，不卸载 MSI，不删除其他副本的程序或快捷方式。`tools/windows-installer/README-Windows.txt:33`
- 删除程序目录不会自动删除存放在 AppData 或自定义位置的用户数据。`tools/windows-installer/README-Windows.txt:34`
- 无人值守 MSI 默认保留数据，命令为 msiexec /x {ProductCode} /qn。`tools/windows-installer/README-Windows.txt:37`
- 无人值守 MSI 明确要求清理数据时使用 msiexec /x {ProductCode} /qn OPERIT_DELETE_USER_DATA=1。`tools/windows-installer/README-Windows.txt:38`
- 无人值守 MSI 请使用当前用户身份执行，关闭所有 Operit2 进程，并在运行前备份自定义目录。`tools/windows-installer/README-Windows.txt:39`
- 自动升级、同版本覆盖安装、修复均不会清理用户数据。`tools/windows-installer/README-Windows.txt:40`
- DeleteData 属性在 Operation 为 Remove 且 DeleteUserData 复选框勾选时为真。`tools/windows-installer/ui/SetupWindow.xaml.cs:24`
- DeleteUserData 与 CleanupDetailsButton 只在 removing 时可见。`tools/windows-installer/ui/SetupWindow.xaml.cs:46`
- 卸载成功且勾选删除数据时，结果文案为本机用户数据和 Operit2 凭据已删除，其他设备与云端的数据未被修改。`tools/windows-installer/ui/SetupWindow.xaml.cs:192`
- 卸载成功且未勾选删除数据时，结果文案为聊天记录和个人设置已保留。`tools/windows-installer/ui/SetupWindow.xaml.cs:192`
- OperitPrepareRemoval 在 InstallInitialize 之前执行，条件为 Installed AND REMOVE="ALL" AND NOT UPGRADINGPRODUCTCODE。`tools/windows-installer/Package.wxs:37`
- OperitFinishRemoval 在 InstallFinalize 之后执行，条件为 Installed AND REMOVE="ALL" AND NOT UPGRADINGPRODUCTCODE。`tools/windows-installer/Package.wxs:39`
- OperitRegisterShellEntries 在 OperitFinishRemoval 之后执行，条件为 NOT REMOVE~="ALL"。`tools/windows-installer/Package.wxs:40`

### 清理范围：六处位置

- 清理范围包括 %APPDATA%\Operit2，包括固定启动配置、默认数据和工作区。`tools/windows-installer/README-Windows.txt:19`
- 清理范围包括启动配置中记录的自定义 runtimeRoot、workspaceRoot 目录及其全部内容。`tools/windows-installer/README-Windows.txt:20`
- 清理范围包括 %LOCALAPPDATA%\app.operit\Operit2，即托管运行环境。`tools/windows-installer/README-Windows.txt:21`
- 清理范围包括 %LOCALAPPDATA%\Operit2，即崩溃报告。`tools/windows-installer/README-Windows.txt:22`
- 清理范围包括 %LOCALAPPDATA%\webview_all_windows\operit2，即浏览器缓存、Cookie 等。`tools/windows-installer/README-Windows.txt:23`
- 清理范围包括 Windows 凭据管理器中以 Operit2: 开头的应用凭据。`tools/windows-installer/README-Windows.txt:24`
- 清理会覆盖本机所有身份。`tools/windows-installer/README-Windows.txt:25`
- Describe 说明安装版与压缩包版共用这些数据，其他副本也会失去这些本机数据。`tools/windows-installer/shared/UserDataCleanup.cs:25`
- Describe 说明清理包含所有本机身份的聊天、设置、插件、工作区、浏览器数据和运行环境。`tools/windows-installer/shared/UserDataCleanup.cs:25`
- CreatePlan 从 roaming 下 Operit2 目录中 client\link\local_runtime_storage.json 读取启动配置。`tools/windows-installer/shared/UserDataCleanup.cs:72`
- 启动配置 confirmed 为 true 时加入 ConfiguredRoot 读取的 runtimeRoot。`tools/windows-installer/shared/UserDataCleanup.cs:83`
- 启动配置 confirmed 为 true 时加入 ConfiguredRoot 读取的 workspaceRoot。`tools/windows-installer/shared/UserDataCleanup.cs:84`
- 启动配置缺失 confirmed 布尔值时抛 InvalidDataException。`tools/windows-installer/shared/UserDataCleanup.cs:79`
- 把 roaming 下的 Operit2 目录 appRoot 加入清理根目录。`tools/windows-installer/shared/UserDataCleanup.cs:87`
- 把 local 下的 app.operit\Operit2 目录加入清理根目录。`tools/windows-installer/shared/UserDataCleanup.cs:88`
- 把 local 下的 Operit2 目录加入清理根目录。`tools/windows-installer/shared/UserDataCleanup.cs:89`
- 把 local 下的 webview_all_windows\operit2 目录加入清理根目录。`tools/windows-installer/shared/UserDataCleanup.cs:90`
- 清理根目录用 Distinct 按 OrdinalIgnoreCase 去重。`tools/windows-installer/shared/UserDataCleanup.cs:91`
- 用 IsWithin 去掉被其他根包含的嵌套根，含 bootstrap 的根排在最后。`tools/windows-installer/shared/UserDataCleanup.cs:95`
- 凭据删除只针对 Type 为 1 且 TargetName 以 Operit2: 开头的凭据，调用 CredDelete 按目标名与类型删除。`tools/windows-installer/shared/UserDataCleanup.cs:263`
- DeleteCredentials 用 CredEnumerate 按过滤器 Operit2:* 枚举当前用户的凭据。`tools/windows-installer/shared/UserDataCleanup.cs:251`
- CredEnumerate 枚举不到凭据、错误为 1168 时直接返回，不抛异常。`tools/windows-installer/shared/UserDataCleanup.cs:254`
- 清理不会向其他设备或云端发送删除指令。`tools/windows-installer/README-Windows.txt:27`

### 为什么清理不可回滚

- 文件删除无法回滚；中途失败会说明未全部完成，请按提示处理后重新打开工具。`tools/windows-installer/README-Windows.txt:29`
- DeleteData 先调用 ValidatePlan，再调用 clearCredentials，然后对每个存在的根目录调用 DeleteTree。`tools/windows-installer/shared/UserDataCleanup.cs:119`
- 删除不跟随链接目录递归，删除文件前清除文件的 ReadOnly 属性。`tools/windows-installer/shared/UserDataCleanup.cs:213`
- DeleteData 删除前弹出确认框，文案为永久删除列出的所有本机数据，此操作无法撤销。`tools/windows-installer/cleanup/Program.cs:81`
- 清理失败时界面显示清理未全部完成，已删除的数据无法恢复，并再次列出计划范围。`tools/windows-installer/cleanup/Program.cs:97`
- 生成清理计划后调用 ValidatePlan，再用 Describe 弹出确认框确认永久删除本机用户数据。`tools/windows-installer/ui/SetupWindow.xaml.cs:73`
- 数据目录配置已改变时抛 InvalidOperationException，要求重新打开清理界面并确认。`tools/windows-installer/shared/UserDataCleanup.cs:106`
- 确认复选框文案为已备份需要的数据，并理解这会影响本机所有 Operit2 副本。`tools/windows-installer/cleanup/Program.cs:49`
- ConsentChanged 仅在清理计划存在、确认复选框勾选且未运行时启用删除按钮。`tools/windows-installer/cleanup/Program.cs:76`

### Operit2DataCleanup.exe 为什么不依赖 Flutter、Rust DLL 或 MSI

- Operit2DataCleanup.exe 不依赖 Flutter、Rust DLL 或 MSI，但需要 Windows 自带的 .NET Framework 4.7.2 或更新版本。`tools/windows-installer/README-Windows.txt:16`
- Program.Main 的注释说明独立清理工具不需要 Flutter 或已安装的 MSI。`tools/windows-installer/cleanup/Program.cs:10`
- Program.Main 以 STAThread 启动 WPF Application 并运行 CleanupWindow。`tools/windows-installer/cleanup/Program.cs:13`
- Program.cs 只引用 System、System.IO、System.Threading.Tasks、System.Windows 与 System.Windows.Controls。`tools/windows-installer/cleanup/Program.cs:3`
- UserDataCleanup.cs 只引用 System 系列命名空间与 Microsoft.Win32。`tools/windows-installer/shared/UserDataCleanup.cs:5`
- DeleteCredentials 用 CredEnumerate 按过滤器 Operit2:* 枚举当前用户的凭据。`tools/windows-installer/shared/UserDataCleanup.cs:251`
- 打包流程用 dotnet 构建 cleanup/Operit2DataCleanup.csproj，配置为 Release。`tools/build_scripts/build_windows_msi.py:109`
- 打包流程把构建产物 Operit2DataCleanup.exe 从 build/cleanup/bin/Release/net472 复制到发布目录。`tools/build_scripts/build_windows_msi.py:111`
- REQUIRED_FILES 包含 Operit2DataCleanup.exe 与 README-Windows.txt。`tools/build_scripts/build_windows_msi.py:27`

### MSI 契约：MsiContractTests 覆盖哪些契约

- Verify 检查已编译 MSI 的条件与顺序，不安装也不执行自定义操作。`tools/windows-installer/tests/MsiContractTests.cs:7`
- Verify 用 MsiOpenPackageEx 打开 MSI 包做检查。`tools/windows-installer/tests/MsiContractTests.cs:10`
- ReadAction 读取 OperitPrepareRemoval 的执行条件与序号。`tools/windows-installer/tests/MsiContractTests.cs:16`
- ReadAction 同时读取 OperitFinishRemoval、OperitInstallCompleted、InstallInitialize 与 InstallFinalize。`tools/windows-installer/tests/MsiContractTests.cs:18`
- 契约要求 prepare.Sequence 小于 initialize.Sequence，finish.Sequence 大于 finalize.Sequence，complete.Sequence 大于 finish.Sequence。`tools/windows-installer/tests/MsiContractTests.cs:21`
- Evaluate 把 installed、remove、upgrading 依次设为 Installed、REMOVE、UPGRADINGPRODUCTCODE 会话属性，再用 MsiEvaluateCondition 求值。`tools/windows-installer/tests/MsiContractTests.cs:70`
- 条件求值场景 Evaluate(session, condition, "1", "ALL", "") 的期望结果为 true。`tools/windows-installer/tests/MsiContractTests.cs:24`
- 条件求值场景 Evaluate(session, condition, "1", "ALL", "{old-product}") 的期望结果为 false。`tools/windows-installer/tests/MsiContractTests.cs:25`
- 条件求值场景 Evaluate(session, condition, "1", "", "") 的期望结果为 false。`tools/windows-installer/tests/MsiContractTests.cs:26`
- 条件求值场景 Evaluate(session, condition, "", "", "") 的期望结果为 false。`tools/windows-installer/tests/MsiContractTests.cs:27`
- 条件求值场景 Evaluate(session, condition, "", "ALL", "") 的期望结果为 false。`tools/windows-installer/tests/MsiContractTests.cs:28`
- 注释说明显式命令行清理 opt-in 不得绕过升级保护。`tools/windows-installer/tests/MsiContractTests.cs:29`
- 设置 OPERIT_DELETE_USER_DATA 为 1 后，条件求值场景 Evaluate(session, condition, "1", "ALL", "{old-product}") 的期望结果仍为 false。`tools/windows-installer/tests/MsiContractTests.cs:30`
- 测试通过时输出 PASS compiled MSI uninstall, upgrade, repair, and post-commit conditions。`tools/windows-installer/tests/MsiContractTests.cs:33`

### 打包流程：build_windows_msi.py

- build_windows_msi.py 的作用是将完整的 Flutter Windows 发布目录打包为品牌 MSI。`tools/build_scripts/build_windows_msi.py:2`
- 默认发布目录为 FLUTTER_APP_DIR 下的 build/windows/x64/runner/Release。`tools/build_scripts/build_windows_msi.py:19`
- REQUIRED_FILES 包含 operit2.exe、flutter_windows.dll、operit_flutter_bridge.dll。`tools/build_scripts/build_windows_msi.py:24`
- REQUIRED_FILES 包含 operit_local_llm.dll、msvcp140.dll、vcruntime140.dll。`tools/build_scripts/build_windows_msi.py:25`
- REQUIRED_FILES 包含 data/icudtl.dat、data/app.so、data/flutter_assets/AssetManifest.bin。`tools/build_scripts/build_windows_msi.py:26`
- write_payload 要求 REQUIRED_FILES 全部存在于发布目录，否则抛 RuntimeError。`tools/build_scripts/build_windows_msi.py:59`
- 载荷中出现符号链接时抛 RuntimeError。`tools/build_scripts/build_windows_msi.py:69`
- 载荷路径大小写不敏感重复时抛 RuntimeError。`tools/build_scripts/build_windows_msi.py:72`
- 组件 Guid 由路径小写形式的 uuid5 生成。`tools/build_scripts/build_windows_msi.py:87`
- AppDirectoryCleanup 组件在 HKCU 下 Software\Operit\Operit2\Installer 写 Directories 注册表值，并为每个目录加 RemoveFolder，On 为 uninstall。`tools/build_scripts/build_windows_msi.py:99`
- msi_version 把 SemVer 映射为 MSI 版本。`tools/build_scripts/build_windows_msi.py:32`
- 稳定版 revision 为 999。`tools/build_scripts/build_windows_msi.py:38`
- 预发布通道 dev、preview、rc 的 revision 基数分别为 0、200、400。`tools/build_scripts/build_windows_msi.py:41`
- 预发布计数器大于 199 时抛 ValueError。`tools/build_scripts/build_windows_msi.py:40`
- build 等于 patch 乘 1000 加 revision，major 或 minor 大于 255 或 build 大于 65535 时抛 ValueError。`tools/build_scripts/build_windows_msi.py:45`
- 打包流程把 README-Windows.txt 复制到发布目录。`tools/build_scripts/build_windows_msi.py:112`
- 打包流程还构建 ui/OperitInstaller.csproj 与 actions/OperitCleanupActions.csproj。`tools/build_scripts/build_windows_msi.py:117`
- WiX 构建以 Package.wxs 与生成的 Payload.wxs 为输入，架构为 x64。`tools/build_scripts/build_windows_msi.py:123`
- WiX 构建指定 -pdbtype none，不生成 pdb。`tools/build_scripts/build_windows_msi.py:130`
- 默认 MSI 输出路径为 DIST_DIR 下按 release_asset_name("app", "windows", "x86_64", "msi") 命名的文件。`tools/build_scripts/build_windows_msi.py:146`

### 清理前的安全检查链

- CreatePlan 先对启动配置文件调用 EnsureNoLinkedAncestor 检查链接祖先。`tools/windows-installer/shared/UserDataCleanup.cs:73`
- 每个去重后的清理根目录调用 ValidateRoot。`tools/windows-installer/shared/UserDataCleanup.cs:92`
- ValidateRoot 拒绝磁盘根目录、受保护路径包含的目录与 Windows 目录。`tools/windows-installer/shared/UserDataCleanup.cs:149`
- 清理根目录逐个调用 EnsureNoLinkedAncestor 检查。`tools/windows-installer/shared/UserDataCleanup.cs:152`
- EnsureNoLinkedAncestor 沿路径的祖先目录逐级向上检查。`tools/windows-installer/shared/UserDataCleanup.cs:181`
- 祖先目录带 ReparsePoint 属性时抛 IOException，提示数据路径经过链接。`tools/windows-installer/shared/UserDataCleanup.cs:190`
- ValidatePlan 重新调用 CreatePlan，并比对 Directories 顺序、BootstrapContent 与 BootstrapPath。`tools/windows-installer/shared/UserDataCleanup.cs:104`
- 校验调用 ensureStopped 要求 Operit 进程退出。`tools/windows-installer/shared/UserDataCleanup.cs:107`
- EnsureOperitStopped 按进程名 operit2 查找进程。`tools/windows-installer/shared/UserDataCleanup.cs:128`
- 发现 operit2 进程仍在运行时抛 InvalidOperationException，要求先退出所有 Operit2 窗口、后台进程及命令行。`tools/windows-installer/shared/UserDataCleanup.cs:133`
- 对每个已存在的清理根目录调用 CheckTree 检查。`tools/windows-installer/shared/UserDataCleanup.cs:111`
- CheckTree 跳过带 ReparsePoint 属性的条目，对普通文件以 FileShare.None 打开检查文件锁。`tools/windows-installer/shared/UserDataCleanup.cs:199`
- 清理根目录不存在但被文件占用时抛 IOException。`tools/windows-installer/shared/UserDataCleanup.cs:112`
- 目录经过链接、指向受保护位置、配置损坏或文件被占用时会明确报错。`tools/windows-installer/README-Windows.txt:28`
- PreventClosingWhileRunning 在清理运行时取消关闭。`tools/windows-installer/cleanup/Program.cs:106`
- BeginFinalization 把 finalizing 置真并禁用取消按钮与关闭按钮。`tools/windows-installer/ui/SetupWindow.xaml.cs:138`

### 程序入口与快捷方式：只删属于本副本的入口

- MSI 普通卸载会清除属于当前安装副本的桌面、开始菜单和 operit2:// 协议入口。`tools/windows-installer/README-Windows.txt:32`
- RemoveShellEntries 针对 operit2 协议注册表键 Software\Classes\operit2 操作。`tools/windows-installer/shared/UserDataCleanup.cs:274`
- operit2 协议键只在注册的打开命令等于本副本 operit2.exe "%1" 时才删除。`tools/windows-installer/shared/UserDataCleanup.cs:286`
- 开始菜单创建 Operit2、Operit2 Data Rescue、Operit2 Data Cleanup、Operit2 Uninstall 快捷方式与桌面上的 Operit2.lnk。`tools/windows-installer/shared/UserDataCleanup.cs:334`
- Operit2 Data Rescue 快捷方式以 --data-rescue 参数启动 operit2.exe。`tools/windows-installer/shared/UserDataCleanup.cs:334`
- Operit2 Uninstall 快捷方式以 msiexec.exe 加 UninstallArguments(productCode) 参数启动。`tools/windows-installer/shared/UserDataCleanup.cs:336`
- UninstallArguments 生成 /x "{ProductCode}" /qf 形式的参数，ProductCode 按大写 B 格式格式化。`tools/windows-installer/shared/UserDataCleanup.cs:346`
- 开始菜单 Operit2 目录下检查 Operit2.lnk、Operit2 Data Rescue.lnk、Operit2 Data Cleanup.lnk、Operit2 Uninstall.lnk 与桌面上的 Operit2.lnk。`tools/windows-installer/shared/UserDataCleanup.cs:295`
- 快捷方式只在目标为本副本 operit2.exe、Operit2DataCleanup.exe，或目标为 msiexec.exe 且参数等于 UninstallArguments(productCode) 时才删除。`tools/windows-installer/shared/UserDataCleanup.cs:306`
- 快捷方式删除后，若 menu 目录为空则调用 Directory.Delete 删除该目录。`tools/windows-installer/shared/UserDataCleanup.cs:315`
- 快捷方式的图标位置取自安装目录下 operit2.exe 的第 0 个图标。`tools/windows-installer/shared/UserDataCleanup.cs:359`

## 关键符号

- `CleanupPlan` — 清理计划，包含 Directories、BootstrapPath、BootstrapContent 三个属性。`tools/windows-installer/shared/UserDataCleanup.cs:16`
- CleanupPlan 的 `Describe` — 列出将永久删除的目录及其全部内容，并说明同时删除 Windows 凭据管理器中的 Operit2: 凭据。`tools/windows-installer/shared/UserDataCleanup.cs:23`
- `UserDataCleanup` — 解析启动配置、生成并校验清理计划、执行删除与凭据清理的类。`tools/windows-installer/shared/UserDataCleanup.cs:30`
- UserDataCleanup 的 `CreatePlan` — 从启动配置读取自定义根目录并生成清理计划。`tools/windows-installer/shared/UserDataCleanup.cs:69`
- UserDataCleanup 的 `ValidatePlan` — 重新生成计划并比对，检查进程、链接与文件锁。`tools/windows-installer/shared/UserDataCleanup.cs:101`
- UserDataCleanup 的 `DeleteData` — 先校验计划，再清除凭据，然后删除各根目录。`tools/windows-installer/shared/UserDataCleanup.cs:117`
- UserDataCleanup 的 `EnsureOperitStopped` — 按进程名 operit2 查找进程，仍在运行时抛错。`tools/windows-installer/shared/UserDataCleanup.cs:126`
- UserDataCleanup 的 `DeleteCredentials` — 用 CredEnumerate 按 Operit2:* 枚举并删除凭据。`tools/windows-installer/shared/UserDataCleanup.cs:249`
- UserDataCleanup 的 `RemoveShellEntries` — 只删除属于本副本的协议键与快捷方式。`tools/windows-installer/shared/UserDataCleanup.cs:272`
- UserDataCleanup 的 `RegisterShellEntries` — 创建开始菜单与桌面的快捷方式。`tools/windows-installer/shared/UserDataCleanup.cs:319`
- UserDataCleanup 的 `UninstallArguments` — 生成 /x "{ProductCode}" /qf 形式的卸载参数。`tools/windows-installer/shared/UserDataCleanup.cs:345`
- UserDataCleanup 的 `Normalize` — 要求完整 Windows 路径，拒绝以 \\?\ 与 \\.\ 为前缀的路径。`tools/windows-installer/shared/UserDataCleanup.cs:156`
- UserDataCleanup 的 `IsWithin` — 按目录边界比较路径是否位于根目录内。`tools/windows-installer/shared/UserDataCleanup.cs:169`
- UserDataCleanup 的 `EnsureNoLinkedAncestor` — 沿路径的祖先目录逐级向上检查链接。`tools/windows-installer/shared/UserDataCleanup.cs:181`
- UserDataCleanup 的 `CheckTree` — 跳过链接条目，对普通文件以 FileShare.None 打开检查文件锁。`tools/windows-installer/shared/UserDataCleanup.cs:195`
- UserDataCleanup 的 `DeleteTree` — 不跟随链接目录递归删除。`tools/windows-installer/shared/UserDataCleanup.cs:206`
- `Program.Main` — 以 STAThread 启动 WPF Application 并运行 CleanupWindow。`tools/windows-installer/cleanup/Program.cs:13`
- `CleanupWindow` — 独立清理工具窗口。`tools/windows-installer/cleanup/Program.cs:20`
- CleanupWindow 的 `DeleteData` — 删除前弹出确认框，在后台任务中调用 cleanup.DeleteData(plan)。`tools/windows-installer/cleanup/Program.cs:79`
- `SetupWindow` — MSI 内嵌安装、修复与卸载界面。`tools/windows-installer/ui/SetupWindow.xaml.cs:13`
- `SetupOperation` — 枚举包含 Install、Repair、Remove 三个值。`tools/windows-installer/ui/SetupWindow.xaml.cs:11`
- SetupWindow 的 `DeleteData` — 在 Operation 为 Remove 且 DeleteUserData 复选框勾选时为真的属性。`tools/windows-installer/ui/SetupWindow.xaml.cs:24`
- SetupWindow 的 `ShowCleanupDetails` — 用 CreatePlan 与 Describe 显示清理范围，不修改或删除任何数据。`tools/windows-installer/ui/SetupWindow.xaml.cs:119`
- SetupWindow 的 `BeginFinalization` — 把 finalizing 置真并禁用取消按钮与关闭按钮。`tools/windows-installer/ui/SetupWindow.xaml.cs:138`
- SetupWindow 的 `Complete` — 在 MSI 事务结束后显示成功、取消或错误结果。`tools/windows-installer/ui/SetupWindow.xaml.cs:176`
- `MsiContractTests.Verify` — 检查已编译 MSI 的条件与顺序，不安装也不执行自定义操作。`tools/windows-installer/tests/MsiContractTests.cs:8`
- `ReadAction` — 从 InstallExecuteSequence 读取指定动作的 Condition 与 Sequence。`tools/windows-installer/tests/MsiContractTests.cs:50`
- `Evaluate` — 在未执行安装的 Windows Installer 会话中求值生命周期场景的条件。`tools/windows-installer/tests/MsiContractTests.cs:68`
- `OPERIT_DELETE_USER_DATA` — Secure 属性，无人值守清理的显式 opt-in 开关。`tools/windows-installer/Package.wxs:24`
- `OPERIT_CLEANUP_PLAN` — Hidden 属性。`tools/windows-installer/Package.wxs:25`
- `OperitPrepareRemoval` — 自定义操作，入口为 PrepareRemoval，Return 为 check。`tools/windows-installer/Package.wxs:32`
- `OperitFinishRemoval` — 自定义操作，入口为 FinishRemoval，Return 为 check。`tools/windows-installer/Package.wxs:33`
- `OperitRegisterShellEntries` — 自定义操作，入口为 RegisterShellEntries，Return 为 check。`tools/windows-installer/Package.wxs:34`
- `build_windows_msi` — 打包流程的入口函数，接受发布目录与目标路径。`tools/build_scripts/build_windows_msi.py:103`
- `msi_version` — 把 SemVer 映射为 MSI 版本。`tools/build_scripts/build_windows_msi.py:32`
- `write_payload` — 接受发布目录与目标路径，生成载荷描述。`tools/build_scripts/build_windows_msi.py:56`
- `INSTALLFOLDER` — 安装目录，位于 LocalAppDataFolder 下的 Programs\Operit2。`tools/windows-installer/Package.wxs:46`

## 调用链

1. MSI 安装版卸载：用户在完整卸载界面勾选删除用户数据，DeleteData 属性为真。`tools/windows-installer/ui/SetupWindow.xaml.cs:24`
2. MSI 安装版卸载：勾选删除数据时，安装窗口以 InstallFolder 创建 UserDataCleanup 并调用 CreatePlan 生成 DataCleanupPlan。`tools/windows-installer/ui/SetupWindow.xaml.cs:71`
3. MSI 安装版卸载：生成清理计划后调用 ValidatePlan，再用 Describe 弹出确认框确认永久删除本机用户数据。`tools/windows-installer/ui/SetupWindow.xaml.cs:73`
4. MSI 安装版卸载：Package.wxs 把 OperitPrepareRemoval 排在 InstallInitialize 之前。`tools/windows-installer/Package.wxs:37`
5. MSI 安装版卸载：Package.wxs 把 OperitFinishRemoval 排在 InstallFinalize 之后。`tools/windows-installer/Package.wxs:39`
6. MSI 安装版卸载：OperitRegisterShellEntries 在 OperitFinishRemoval 之后执行，条件为 NOT REMOVE~="ALL"。`tools/windows-installer/Package.wxs:40`
7. 压缩包版清理：Program.Main 以 STAThread 启动 WPF Application 并运行 CleanupWindow。`tools/windows-installer/cleanup/Program.cs:13`
8. 压缩包版清理：启动时调用 CreatePlan 生成清理计划，并用 Describe 显示清理范围。`tools/windows-installer/cleanup/Program.cs:61`
9. 压缩包版清理：ConsentChanged 仅在清理计划存在、确认复选框勾选且未运行时启用删除按钮。`tools/windows-installer/cleanup/Program.cs:76`
10. 压缩包版清理：删除前弹出确认框，文案为永久删除列出的所有本机数据，此操作无法撤销。`tools/windows-installer/cleanup/Program.cs:81`
11. 压缩包版清理：删除在后台任务 Task.Run 中调用 cleanup.DeleteData(plan)。`tools/windows-installer/cleanup/Program.cs:88`
12. 压缩包版清理：DeleteData 先调用 ValidatePlan，再调用 clearCredentials，然后对每个存在的根目录调用 DeleteTree。`tools/windows-installer/shared/UserDataCleanup.cs:119`
13. 压缩包版清理：清理成功后界面显示用户数据清理完成，其他设备和云端的数据未被修改。`tools/windows-installer/cleanup/Program.cs:90`
14. 压缩包版清理：清理失败时界面显示清理未全部完成，已删除的数据无法恢复，并再次列出计划范围。`tools/windows-installer/cleanup/Program.cs:97`
15. MSI 打包：打包流程用 dotnet 构建 cleanup/Operit2DataCleanup.csproj，配置为 Release。`tools/build_scripts/build_windows_msi.py:109`
16. MSI 打包：打包流程把构建产物 Operit2DataCleanup.exe 从 build/cleanup/bin/Release/net472 复制到发布目录。`tools/build_scripts/build_windows_msi.py:111`
17. MSI 打包：WiX 构建以 Package.wxs 与生成的 Payload.wxs 为输入，架构为 x64。`tools/build_scripts/build_windows_msi.py:123`
18. MSI 契约检查：Verify 用 MsiOpenPackageEx 打开 MSI 包做检查。`tools/windows-installer/tests/MsiContractTests.cs:10`

## 来源

- tools/windows-installer/README-Windows.txt
- tools/windows-installer/Package.wxs
- tools/windows-installer/cleanup/Program.cs
- tools/windows-installer/shared/UserDataCleanup.cs
- tools/windows-installer/ui/SetupWindow.xaml.cs
- tools/windows-installer/tests/MsiContractTests.cs
- tools/build_scripts/build_windows_msi.py
- 范围限定：SetupWindow.xaml 本体与 tools/windows-installer/actions/ 下的 4 个文件未计入大纲 seed，本页未读，正文不写这些文件的内容。
- Package.wxs 声明 OperitPrepareRemoval 的 DllEntry 为 PrepareRemoval，入口实现不在本页 seed 范围内。`tools/windows-installer/Package.wxs:32`
- “不依赖 Flutter、Rust DLL 或 MSI”是 README-Windows.txt 的声明，核验范围为本页 7 个 seed 文件。`tools/windows-installer/README-Windows.txt:16`
- Program.cs 的 using 块只含 System、System.IO、System.Threading.Tasks、System.Windows 与 System.Windows.Controls。`tools/windows-installer/cleanup/Program.cs:3`
- UserDataCleanup.cs 的 using 块只含 System 系列命名空间与 Microsoft.Win32。`tools/windows-installer/shared/UserDataCleanup.cs:5`
- 基线：AAswordman/Operit2 @ 364d1d594，7 个 seed 文件共 1058 行，2026-11-11 核验。
