---
title: VFS 挂载与文件访问边界
module: sync
platforms: [all]
sources: [4]
date: 2026-11-11
---

## 概述

- 业务文件操作走 `VisualFileSystem`，不直接拿调用方路径调 `FileSystemHost`。`docs/filesystem-access-boundary.md:3`
- `VisualFileSystem` 持有 `host: Arc<dyn FileSystemHost>` 与 `mapper: PathMapper`，把宿主文件接口表现为规范化虚拟文件系统路径。`core/crates/tool/services/src/files/VisualFileSystem.rs:13`
- 基线里 `FileSystemHost` 与 `VisualFileSystem` 并存：`FileSystemHost` 仍是公开提供者契约，因为平台 crate 实现它；`VisualFileSystem` 是包在它外面的 VFS 层。`docs/filesystem-access-boundary.md:9`
- `/app` 与 `/operitapp` 同时挂到应用数据及工作区后端，`/mnt` 与 `/virtual` 同时挂到平台文件系统及授权资源后端，两组入口访问同一份数据。`docs/vfs-mounts.md:5`
- 本页讲挂载与访问边界；文件选择器返回的临时文件不参与同步，同步策略见 [[sync-workspace-files|工作区文件同步与 .operit/sync.json]]。`docs/vfs-mounts.md:13`

## AI 速览

- `VisualFileSystem` — 业务代码的文件入口，把 VFS 路径映射后委托给 `FileSystemHost`。`core/crates/tool/services/src/files/VisualFileSystem.rs:12`
- `PathMapper` — 规范化 VFS 路径并映射到宿主可见存储根。`core/crates/tool/services/src/files/PathMapper.rs:77`
- `FileSystemHost` — 公开提供者契约，由平台 crate 实现。`docs/filesystem-access-boundary.md:9`
- `ResolvedVfsPath` — 公开 VFS 路径到宿主定位符的解析结果，含 `vfsPath` 与 `physicalPath`。`core/crates/tool/services/src/files/PathMapper.rs:49`
- `VFS_ROOTS` — 六个 VFS 根入口及其隐藏标志。`core/crates/tool/services/src/files/PathMapper.rs:26`
- 主入口函数：`VisualFileSystem` 的 `fromContext`。`core/crates/tool/services/src/files/VisualFileSystem.rs:20`
- 文件输入解析入口：`PathMapper` 的 `resolveFileResourcePath`。`docs/filesystem-access-boundary.md:7`
- 数据流向一句话：调用方 VFS 路径经 resolvePath 映射为物理路径后交给 FileSystemHost 执行，搜索与元数据结果由 `mapPhysicalChildToVfs` 映回 VFS 路径。`core/crates/tool/services/src/files/VisualFileSystem.rs:195`

## 核心机制

- `/app`、`/mnt`、`/sdcard`、`/data` 为隐藏入口，不出现在 `list /` 的结果中，直接指定路径仍可访问，列出其子目录也不受影响。`docs/vfs-mounts.md:5`
- VFS 根目录展示 `/operitapp`，存在可用平台挂载时再展示 `/virtual`。`docs/vfs-mounts.md:5`
- `VFS_ROOTS` 中 `ROOT_APP`、`ROOT_MNT`、`ROOT_SDCARD`、`ROOT_DATA` 的 `hidden` 为 `true`，`ROOT_OPERITAPP` 与 `ROOT_VIRTUAL` 的 `hidden` 为 `false`。`core/crates/tool/services/src/files/PathMapper.rs:26`
- VFS 根目录 `/` 的条目只含 `hidden` 为 false 的 `VFS_ROOTS`，`ROOT_VIRTUAL` 仅在存在平台挂载时出现。`core/crates/tool/services/src/files/PathMapper.rs:330`
- /app 与 /operitapp 的虚拟条目为 data、workspaces、outputs。`core/crates/tool/services/src/files/PathMapper.rs:336`
- /mnt 与 /virtual 的条目来自 `mntMountEntries`，即已挂载的平台入口。`core/crates/tool/services/src/files/PathMapper.rs:337`
- /mnt 与 /virtual 的平台入口只列出已挂载者：`windows`、`android`、`linux`、`macos`。`core/crates/tool/services/src/files/PathMapper.rs:726`
- VFS 直接解析两组根入口，不在插件、工具参数、返回值或持久化记录中把一个根名替换成另一个。`docs/vfs-mounts.md:7`
- 文件结果保留调用者使用的 VFS 根目录。`docs/vfs-mounts.md:7`
- 应用新生成的地址使用 `/operitapp` 与 `/virtual`，已有地址继续有效。`docs/vfs-mounts.md:7`
- 根入口映射仅存在于应用内，不移动物理文件，也不修改终端中的实际挂载点。`docs/vfs-mounts.md:7`
- 测试断言经 `/app` 写入的文件可经 `/operitapp` 读出同一内容。`core/crates/tool/services/src/files/VisualFileSystem.rs:396`
- 测试断言 `fileInfo` 回显调用者使用的 VFS 根路径。`core/crates/tool/services/src/files/VisualFileSystem.rs:399`
- 测试断言根目录列表含 `operitapp`，不含 `app`、`mnt`、`sdcard`、`data`。`core/crates/tool/services/src/files/VisualFileSystem.rs:405`
- 用 `VisualFileSystem` 的 `fromContext` 构造 VFS，或向服务构造器注入必需的 `VisualFileSystem`。`docs/filesystem-access-boundary.md:5`
- VFS 使用所属运行时的存储根与已注册挂载。`docs/filesystem-access-boundary.md:5`
- 不得把 mapper 设为可选，也不得在 VFS 初始化失败时回退到原生 I/O。`docs/filesystem-access-boundary.md:5`
- `fromContext` 缺少 `RuntimeStorageHost` 时返回错误。`core/crates/tool/services/src/files/VisualFileSystem.rs:21`
- `fromContext` 要求 `runtimeRootDir` 与 `workspaceRootDir` 均可用。`core/crates/tool/services/src/files/VisualFileSystem.rs:22`
- `fromContext` 缺少 `FileSystemHost` 时返回错误。`core/crates/tool/services/src/files/VisualFileSystem.rs:24`
- `PathMapper` 的 `new` 要求传入 `RuntimeStorageHost`。`core/crates/tool/services/src/files/PathMapper.rs:99`
- 省略 Host 构造 `PathMapper` 是编译错误。`core/crates/tool/services/src/files/PathMapper.rs:89`
- PathMapper 的 `builtinOnly` 明确排除持久挂载，只做内置路径映射，需要已注册挂载的运行时消费者必须用带 Host 的 `new`。`core/crates/tool/services/src/files/PathMapper.rs:113`
- 上传、网页结果、归档导入与包校验不得把调用方提供的路径直接交给 `FileSystemHost`。`docs/filesystem-access-boundary.md:3`
- Rust 无法把公开 trait 方法仅对选定的外部 crate 设为私有。`docs/filesystem-access-boundary.md:9`
- 仓库在 `operit-tools` 构建期间强制执行模块级原生访问边界。`docs/filesystem-access-boundary.md:9`
- `build_support/native_filesystem.rs` 解析生产 Rust 源码，拒绝 admitted 模块之外对 `FileSystemHost` 的引用或经 `fileSystemHost` 的访问。`docs/filesystem-access-boundary.md:9`
- 测试夹具与字符串不授予生产访问权。`docs/filesystem-access-boundary.md:9`
- 该边界检查覆盖 Core、Flutter 原生桥与 CLI，`hosts/` 中的平台提供者实现保留其原生角色。`docs/filesystem-access-boundary.md:9`
- 原生访问保留给映射后 VFS 分发、宿主组装、已安装包/技能/MCP 存储、原生流式/暂存，以及原生录制、截图或语音 API 返回的文件。`docs/filesystem-access-boundary.md:11`
- 被 admitted 并不意味着直接读任意调用方路径是恰当的。`docs/filesystem-access-boundary.md:11`
- 新的原生使用者需要明确的模块条目与理由，业务服务应依赖 VFS。`docs/filesystem-access-boundary.md:11`
- 需要原生归档的包加载器收到经 VFS 解析的路径。`docs/filesystem-access-boundary.md:13`
- 资源挂载暂存进运行时拥有的存储，导入完成后移除，导入流水线其余部分只见到解析出的原生文件。`docs/filesystem-access-boundary.md:13`
- 边界与工具测试用 `cd core` 后 `cargo test -p operit-tools --lib --test native_filesystem_boundary` 运行。`docs/filesystem-access-boundary.md:19`
- PathMapper 的 `resolve` 先查注册挂载，`mountRelativePath` 命中时按挂载解析。`core/crates/tool/services/src/files/PathMapper.rs:364`
- `native` 后端挂载把 `mount.root` 与相对路径拼接为物理路径。`core/crates/tool/services/src/files/PathMapper.rs:371`
- 非 `native` 后端挂载把挂载编码为 `FileSystemResource` 定位符。`core/crates/tool/services/src/files/PathMapper.rs:374`
- /app 或 /operitapp 下的 data 解析到 `runtimeStoreRoot`。`core/crates/tool/services/src/files/PathMapper.rs:384`
- /app 或 /operitapp 下的 `outputs` 解析到 `runtimeStoreRoot` 下的 `data/chat_outputs`。`core/crates/tool/services/src/files/PathMapper.rs:389`
- /app 或 /operitapp 下的 workspaces 解析到 `workspaceCollectionRoot`。`core/crates/tool/services/src/files/PathMapper.rs:393`
- PathMapper 的 `workspaceCollectionPath` 返回 `/operitapp/workspaces`。`core/crates/tool/services/src/files/PathMapper.rs:133`
- VFS 根 `/` 与裸挂载根是虚拟目录，resolve 返回错误。`core/crates/tool/services/src/files/PathMapper.rs:382`
- 未知 VFS 根返回 `Unknown VFS root` 错误。`core/crates/tool/services/src/files/PathMapper.rs:458`
- VFS 路径必须以 `/` 开头，否则返回错误。`core/crates/tool/services/src/files/PathMapper.rs:497`
- VFS 路径段 `.` 与 `..` 被拒绝。`core/crates/tool/services/src/files/PathMapper.rs:551`
- `physicalPath` 保留旧名，资源后端目标是不透明定位符，需要真实操作系统路径时调用 `nativePath` 或 `terminalDirectory`。`core/crates/tool/services/src/files/PathMapper.rs:42`
- ResolvedVfsPath 的 `nativePath` 对文档/资源挂载返回错误，对原生后端返回 `physicalPath`。`core/crates/tool/services/src/files/PathMapper.rs:64`
- `ResolvedVfsPath` 的 `terminalDirectory` 让终端宿主翻译受支持的文档后端目录。`core/crates/tool/services/src/files/PathMapper.rs:57`
- `resolveFileResourcePath` 保留 VFS 定位符，相对路径按当前文件目录解析，原生绝对兼容路径映射进已挂载的 VFS。`docs/filesystem-access-boundary.md:7`
- 工具调用的 `directory` 取自 `ToolExecutionManager` 的 `currentToolRuntimeContext` 与 `context` 的 `fileDirectory`。`docs/filesystem-access-boundary.md:7`
- 无文件目录的相对路径仍是明确错误。`docs/filesystem-access-boundary.md:7`
- `/` VFS 目录对目录操作仍有效。`docs/filesystem-access-boundary.md:7`
- PathMapper 的 `resolveFileToolPath` 在相对路径且无当前文件目录时返回错误。`core/crates/tool/services/src/files/PathMapper.rs:222`
- 相对路径的 `..` 越出 VFS 根时返回错误。`core/crates/tool/services/src/files/PathMapper.rs:226`
- 原生兼容路径在任何宿主访问前先进入已挂载的 VFS。`core/crates/tool/services/src/files/PathMapper.rs:243`
- resolveFileResourcePath 对 VFS 根路径调用 `canonicalizeVfsPath`，对其他绝对路径调用 `normalizeAbsoluteHostWorkspacePath`。`core/crates/tool/services/src/files/PathMapper.rs:255`
- PathMapper 的 `canonicalizeVfsPath` 把 /sdcard 与 /storage/emulated/0 开头的旧共享存储别名转为身份拥有的插件存储路径（Android）。`core/crates/tool/services/src/files/PathMapper.rs:168`
- Windows 盘符经 `normalizeDriveLetter` 规范化，未挂载的盘符返回错误（Windows）。`core/crates/tool/services/src/files/PathMapper.rs:398`
- `normalizeDriveLetter` 要求单个 ASCII 字母盘符并转为小写。`core/crates/tool/services/src/files/PathMapper.rs:701`
- Windows 上 `windowsDriveRootExists` 检查 `盘符:/` 是否存在（Windows）。`core/crates/tool/services/src/files/PathMapper.rs:758`
- 非 Windows 上 `windowsDriveRootExists` 恒为 `false`。`core/crates/tool/services/src/files/PathMapper.rs:764`
- `windowsMounted` 在存在任一盘符根时为 true（Windows）。`core/crates/tool/services/src/files/PathMapper.rs:738`
- `/virtual/android/sdcard` 解析到 `/sdcard`，未挂载时返回错误（Android）。`core/crates/tool/services/src/files/PathMapper.rs:418`
- `/virtual/android/root` 解析到 `/`，未挂载时返回错误（Android）。`core/crates/tool/services/src/files/PathMapper.rs:425`
- `/virtual/linux` 解析到 `/`，未挂载时返回错误（Linux）。`core/crates/tool/services/src/files/PathMapper.rs:432`
- `/virtual/macos` 解析到 `/`，未挂载时返回错误（macOS）。`core/crates/tool/services/src/files/PathMapper.rs:441`
- `/data` 解析到 `/data`，未挂载时返回错误（Android）。`core/crates/tool/services/src/files/PathMapper.rs:450`
- Android 上 `androidPathMounted` 检查该路径是否存在（Android）。`core/crates/tool/services/src/files/PathMapper.rs:784`
- 非 Android 上 `androidPathMounted` 恒为 `false`。`core/crates/tool/services/src/files/PathMapper.rs:790`
- Linux 上 `linuxRootMounted` 检查 `/` 是否存在（Linux）。`core/crates/tool/services/src/files/PathMapper.rs:796`
- 非 Linux 上 `linuxRootMounted` 恒为 `false`。`core/crates/tool/services/src/files/PathMapper.rs:802`
- macOS 上 `macosRootMounted` 检查 `/` 是否存在（macOS）。`core/crates/tool/services/src/files/PathMapper.rs:808`
- 非 macOS 上 `macosRootMounted` 恒为 `false`。`core/crates/tool/services/src/files/PathMapper.rs:814`
- Windows 盘符路径 D:/... 映射为 /virtual/windows/d/...（Windows）。`core/crates/tool/services/src/files/PathMapper.rs:622`
- 非 VFS 的绝对宿主路径按编译目标平台映射：macOS 进 /virtual/macos，Android 进 /virtual/android/root，其余进 /virtual/linux。`core/crates/tool/services/src/files/PathMapper.rs:644`
- `mapPhysicalChildToVfs` 对资源搜索结果校验 `backend` 与 `root` 与基路径一致，否则返回错误。`core/crates/tool/services/src/files/PathMapper.rs:468`
- 宿主返回的原生子路径不在解析基路径之下时返回错误。`core/crates/tool/services/src/files/PathMapper.rs:482`
- Compose DSL 文件选择器返回的 `path` 与 `uri` 是同一个规范 VFS 路径，可直接交给统一文件接口使用。`docs/vfs-mounts.md:11`
- 原生物理路径、文档提供者 URI 与浏览器对象 URL 由 host 内部持有。`docs/vfs-mounts.md:11`
- 选中的文件经 Flutter `XFile` 分块读取、经运行时 `RuntimeStorageWriteHost` 写入私有暂存文件，字节数验证通过并提交后才返回 `/operitapp/data/temp/clean_on_exit/file_picker/<id>/<name>`。`docs/vfs-mounts.md:13`
- 选中的文件保留原始名称，属于退出时清理的临时数据，不参与同步。`docs/vfs-mounts.md:13`
- 读取或存储失败会终止选择请求并清理本次产生的文件。`docs/vfs-mounts.md:13`
- `maxContentBytes` 只控制可选的内联 Base64 内容，未请求内联内容时同样返回可读取的 VFS 文件。`docs/vfs-mounts.md:13`
- 选中的目录保留平台适配器提供的授权后端，通过挂载目录注册为 `/virtual/<namespace>/<kind>/<id>`。`docs/vfs-mounts.md:15`
- Rust host 出口验证每个返回资源的 VFS 可访问性、类型与文件大小。`docs/vfs-mounts.md:15`
- 聊天工作区中使用「选择本机文件夹」时，Android 打开系统 SAF 文档树选择器（Android）。`docs/vfs-mounts.md:19`
- Android 文档树挂载形如 `/virtual/android/documents/<mount-id>/`，其下文件如 `/virtual/android/documents/<mount-id>/src/main.py`（Android）。`docs/vfs-mounts.md:23`
- 不把 `content://` URI 强行转换为物理路径，也不依赖提供者的 authority 或文档 ID 格式（Android）。`docs/vfs-mounts.md:26`
- 挂载记录按当前运行时身份保存在 `config/vfs_mounts.json` 中，重启后仍需提供者存在且授权有效（Android）。`docs/vfs-mounts.md:26`
- 授权撤销、只读树及提供者错误会作为文件操作错误返回（Android）。`docs/vfs-mounts.md:26`
- Android 文档树支持列目录、元数据、文本/二进制读写、创建目录、删除、复制/移动、查找、内容搜索及 ZIP 压缩/解压（Android）。`docs/vfs-mounts.md:28`
- Android 文档树的实际写入能力取决于提供者权限（Android）。`docs/vfs-mounts.md:28`
- Android 文档树的移动通过复制后删除完成，不保证原子性，删除挂载根目录被禁止（Android）。`docs/vfs-mounts.md:28`
- `/virtual/android/root/` 映射到 `/`，`/virtual/android/root/data/` 映射到 `/data/`（Android）。`docs/vfs-mounts.md:33`
- `/virtual/android/root` 是路径映射，不是提权或内核挂载（Android）。`docs/vfs-mounts.md:37`
- 经 `/virtual/android/root` 的访问仍受 Android 的 UID、SELinux 与已有权限限制（Android）。`docs/vfs-mounts.md:37`
- 访问 Termux 私有目录应使用其授权的 SAF 文档树，不能靠 `/virtual/android/root` 绕过权限（Android）。`docs/vfs-mounts.md:37`
- SAF 是应用级文件访问能力，不是终端的物理工作目录，不能直接作为 shell cwd。`docs/vfs-mounts.md:55`
- 终端、OCR 等仅支持原生文件路径的调用会明确拒绝文档资源定位符。`docs/vfs-mounts.md:55`
- Linux 测试断言经 `/virtual/linux` 挂载根写入的文件，其 fileInfo 回显同一 VFS 路径（Linux）。`core/crates/tool/services/src/files/VisualFileSystem.rs:482`
- 通用挂载目录记录 `namespace`、`backend`、`root`、`name` 与稳定 ID。`docs/vfs-mounts.md:41`
- 原生目录使用 `native` 后端，平台文档资源使用专属后端。`docs/vfs-mounts.md:41`
- 新增非原生后端还需要实现对应宿主文件操作，注册名称本身不会产生访问能力。`docs/vfs-mounts.md:41`
- `storage mounts list` 列出挂载。`docs/vfs-mounts.md:46`
- `storage mounts add /virtual/local/folders native /absolute/project Project` 添加原生目录挂载。`docs/vfs-mounts.md:47`
- `storage mounts remove /virtual/local/folders/<mount-id>` 移除挂载。`docs/vfs-mounts.md:48`
- 桌面工作区文件夹选择也通过该注册接口建立原生目录挂载，保留既有 macOS 安全作用域选择流程。`docs/vfs-mounts.md:51`
- Android 启动/设置中的应用存储根目录仍要求原生路径，不使用 SAF 工作区选择器（Android）。`docs/vfs-mounts.md:51`
- 文档记录已有 Rust、Flutter 及 Kotlin 本地回归测试，完整 APK 构建、真机 Termux 提供者访问与跨重启授权恢复仍需设备验证。`docs/vfs-mounts.md:57`

## 关键符号

- `VisualFileSystem` — 业务代码的文件入口，把 VFS 路径映射后委托给 `FileSystemHost`。`core/crates/tool/services/src/files/VisualFileSystem.rs:12`
- `VisualFileSystem` 的 `fromContext` — 用 `HostManager` 上下文构造 VFS。`core/crates/tool/services/src/files/VisualFileSystem.rs:20`
- VisualFileSystem 的 `new` — 用宿主文件系统与 `PathMapper` 构造 VFS 包装。`core/crates/tool/services/src/files/VisualFileSystem.rs:29`
- VisualFileSystem 的 `mapper` — 返回所用的 `PathMapper`。`core/crates/tool/services/src/files/VisualFileSystem.rs:34`
- VisualFileSystem 的 `resolvePath` — 经 `mapper.resolve` 把虚拟路径解析为映射宿主路径与 VFS 元数据。`core/crates/tool/services/src/files/VisualFileSystem.rs:40`
- VisualFileSystem 的 `runtimePath` — 经 `PathMapper` 的 `runtimeDataPath` 返回声明运行时存储条目的 VFS 地址。`core/crates/tool/services/src/files/VisualFileSystem.rs:47`
- VisualFileSystem 的 `downloadFile` — 先解析 VFS 目标路径，再用 `http.downloadToFile` 下载到解析出的 `physicalPath`。`core/crates/tool/services/src/files/VisualFileSystem.rs:54`
- VisualFileSystem 的 `listFiles` — 在 mapper 提供虚拟目录条目时返回这些条目，否则解析路径后委托宿主 `listFiles`。`core/crates/tool/services/src/files/VisualFileSystem.rs:61`
- VisualFileSystem 的 `readFile` — 解析路径后读宿主 `physicalPath` 的文本。`core/crates/tool/services/src/files/VisualFileSystem.rs:87`
- VisualFileSystem 的 `readFileWithLimit` — 解析路径后按 `maxBytes` 上限读宿主文本。`core/crates/tool/services/src/files/VisualFileSystem.rs:96`
- VisualFileSystem 的 `readFileBytes` — 解析路径后读宿主 `physicalPath` 的原始字节。`core/crates/tool/services/src/files/VisualFileSystem.rs:105`
- VisualFileSystem 的 `writeFile` — 解析路径后写文本，`append` 控制追加。`core/crates/tool/services/src/files/VisualFileSystem.rs:114`
- VisualFileSystem 的 `writeFileBytes` — 解析路径后写原始字节。`core/crates/tool/services/src/files/VisualFileSystem.rs:123`
- VisualFileSystem 的 `deleteFile` — 解析路径后删除映射的宿主文件或目录，`recursive` 控制递归。`core/crates/tool/services/src/files/VisualFileSystem.rs:132`
- VisualFileSystem 的 `fileExists` — 对虚拟目录直接返回存在、目录、大小 0，其余路径解析后委托宿主 `fileExists`。`core/crates/tool/services/src/files/VisualFileSystem.rs:141`
- VisualFileSystem 的 `moveFile` — 解析源与目标后委托宿主 `moveFile`。`core/crates/tool/services/src/files/VisualFileSystem.rs:157`
- VisualFileSystem 的 `copyFile` — 解析源与目标后委托宿主 `copyFile`，`recursive` 控制递归。`core/crates/tool/services/src/files/VisualFileSystem.rs:167`
- VisualFileSystem 的 `makeDirectory` — 解析路径后委托宿主 `makeDirectory`，`createParents` 控制建父目录。`core/crates/tool/services/src/files/VisualFileSystem.rs:177`
- VisualFileSystem 的 `findFiles` — 把请求路径解析为物理路径后调用宿主 `findFiles`，结果经 mapPhysicalChildToVfs 映回 VFS 路径。`core/crates/tool/services/src/files/VisualFileSystem.rs:186`
- VisualFileSystem 的 `fileInfo` — 对虚拟目录返回 `virtualDirectoryInfo` 生成的元数据，否则把宿主元数据的 `path` 改写为解析出的 vfsPath。`core/crates/tool/services/src/files/VisualFileSystem.rs:203`
- VisualFileSystem 的 `grepCode` — 把请求路径解析为物理路径后调用宿主 `grepCode`，每个匹配文件路径经 mapPhysicalChildToVfs 改写为 VFS 路径。`core/crates/tool/services/src/files/VisualFileSystem.rs:219`
- VisualFileSystem 的 `zipFiles` — 解析源与目标后委托宿主 `zipFiles`。`core/crates/tool/services/src/files/VisualFileSystem.rs:244`
- VisualFileSystem 的 `unzipFiles` — 解析源与目标后委托宿主 `unzipFiles`。`core/crates/tool/services/src/files/VisualFileSystem.rs:254`
- VisualFileSystem 的 `openFile` — 解析路径后用平台文件打开器打开映射的宿主文件。`core/crates/tool/services/src/files/VisualFileSystem.rs:264`
- VisualFileSystem 的 `shareFile` — 解析路径后经宿主分享映射的文件，`title` 为分享标题。`core/crates/tool/services/src/files/VisualFileSystem.rs:273`
- `hostErrorMessage` — 把 `HostError` 转为桥接侧消息字符串，取 `error.message`。`core/crates/tool/services/src/files/VisualFileSystem.rs:280`
- `virtualDirectoryInfo` — 生成合成虚拟目录元数据：存在、类型 `directory`、大小 0、权限 `rwx`。`core/crates/tool/services/src/files/VisualFileSystem.rs:290`
- `PathMapper` — 规范化 VFS 路径并映射到宿主可见存储根。`core/crates/tool/services/src/files/PathMapper.rs:77`
- PathMapper 的 `workspaceCollectionPath` — 返回 `/operitapp/workspaces`。`core/crates/tool/services/src/files/PathMapper.rs:133`
- PathMapper 的 `workspacePath` — 在工作区集合根下为工作区 id 构建 VFS 路径。`core/crates/tool/services/src/files/PathMapper.rs:140`
- PathMapper 的 `normalizeVfsPath` — 规范化绝对 VFS 路径。`core/crates/tool/services/src/files/PathMapper.rs:150`
- PathMapper 的 `runtimeDataPath` — 要求存储路径以 `runtime/` 开头，并把它接在 `/operitapp/data` 之下。`core/crates/tool/services/src/files/PathMapper.rs:156`
- PathMapper 的 `canonicalizeVfsPath` — 把 /sdcard 与 /storage/emulated/0 开头的旧共享存储别名转为身份拥有的插件存储路径。`core/crates/tool/services/src/files/PathMapper.rs:168`
- PathMapper 的 `normalizeWorkspaceBindingPath` — 接受绝对 VFS 路径或绝对宿主路径。`core/crates/tool/services/src/files/PathMapper.rs:183`
- PathMapper 的 `resolveFileToolPath` — 在相对路径且无当前文件目录时返回错误。`core/crates/tool/services/src/files/PathMapper.rs:222`
- PathMapper 的 `resolveFileResourcePath` — 接受 VFS 路径、原生绝对路径与相对于文件目录的路径。`core/crates/tool/services/src/files/PathMapper.rs:242`
- PathMapper 的 `joinVfsPath` — 连接规范化 VFS 基路径与相对路径。`core/crates/tool/services/src/files/PathMapper.rs:265`
- PathMapper 的 `relativePath` — 在首段把 `ROOT_APP` 与 `ROOT_OPERITAPP`、ROOT_MNT 与 ROOT_VIRTUAL 视为同一挂载身份。`core/crates/tool/services/src/files/PathMapper.rs:284`
- PathMapper 的 `relativeFileToolPath` — 按同一挂载身份比较根别名，表达当前文件目录的稳定 VFS 定位符。`core/crates/tool/services/src/files/PathMapper.rs:306`
- PathMapper 的 `virtualDirectoryEntries` — 返回不由宿主目录支撑的 VFS 目录的合成条目。`core/crates/tool/services/src/files/PathMapper.rs:320`
- PathMapper 的 `resolve` — 把规范化 VFS 路径解析为宿主物理路径或资源定位符。`core/crates/tool/services/src/files/PathMapper.rs:362`
- PathMapper 的 `mapPhysicalChildToVfs` — 把宿主搜索/列举结果映回解析基路径下的 VFS 树。`core/crates/tool/services/src/files/PathMapper.rs:464`
- `ResolvedVfsPath` — 公开 VFS 路径到宿主定位符的解析结果，含 `vfsPath` 与 `physicalPath`。`core/crates/tool/services/src/files/PathMapper.rs:49`
- ResolvedVfsPath 的 `nativePath` — 对文档/资源挂载返回错误，对原生后端返回 `physicalPath`。`core/crates/tool/services/src/files/PathMapper.rs:64`
- `ResolvedVfsPath` 的 `terminalDirectory` — 让终端宿主翻译受支持的文档后端目录。`core/crates/tool/services/src/files/PathMapper.rs:57`
- `FileSystemHost` — 公开提供者契约，由平台 crate 实现。`docs/filesystem-access-boundary.md:9`

## 调用链

1. 构造 VFS：`VisualFileSystem` 的 `fromContext` 用 `HostManager` 上下文构造 VFS。`core/crates/tool/services/src/files/VisualFileSystem.rs:20`
2. 解析文件输入：用 `PathMapper` 的 `resolveFileResourcePath` 解析文件输入。`docs/filesystem-access-boundary.md:7`
3. 工具调用的 `directory` 取自 `ToolExecutionManager` 的 `currentToolRuntimeContext` 与 `context` 的 `fileDirectory`。`docs/filesystem-access-boundary.md:7`
4. 解析 VFS 路径：VisualFileSystem 的 `resolvePath` 经 `mapper.resolve` 把虚拟路径解析为映射宿主路径与 VFS 元数据。`core/crates/tool/services/src/files/VisualFileSystem.rs:40`
5. 注册挂载优先：PathMapper 的 `resolve` 先查注册挂载，`mountRelativePath` 命中时按挂载解析。`core/crates/tool/services/src/files/PathMapper.rs:364`
6. 执行文件操作：VisualFileSystem 的 `readFile` 解析路径后读宿主 `physicalPath` 的文本。`core/crates/tool/services/src/files/VisualFileSystem.rs:87`
7. 结果回映：搜索结果经 `mapPhysicalChildToVfs` 映回 VFS 路径。`core/crates/tool/services/src/files/VisualFileSystem.rs:195`
8. 元数据回映：VisualFileSystem 的 `fileInfo` 把宿主返回元数据的 `path` 改写为解析出的 `vfsPath`。`core/crates/tool/services/src/files/VisualFileSystem.rs:212`
9. Host 文件选择：选中的文件经 Flutter `XFile` 分块读取、经运行时 `RuntimeStorageWriteHost` 写入私有暂存文件，字节数验证通过并提交后才返回 `/operitapp/data/temp/clean_on_exit/file_picker/<id>/<name>`。`docs/vfs-mounts.md:13`
10. 目录选择：选中的目录保留平台适配器提供的授权后端，通过挂载目录注册为 `/virtual/<namespace>/<kind>/<id>`。`docs/vfs-mounts.md:15`
11. Android 文档树：聊天工作区中使用「选择本机文件夹」时，Android 打开系统 SAF 文档树选择器。`docs/vfs-mounts.md:19`
12. Android 文档树挂载形如 `/virtual/android/documents/<mount-id>/`，其下文件如 `/virtual/android/documents/<mount-id>/src/main.py`。`docs/vfs-mounts.md:23`
13. 通用挂载：`storage mounts add /virtual/local/folders native /absolute/project Project` 添加原生目录挂载。`docs/vfs-mounts.md:47`

## 来源

本页事实全部取自以下 4 个 seed 文件，基线为 AAswordman/Operit2 @ 364d1d594。

- `docs/vfs-mounts.md`
- `docs/filesystem-access-boundary.md`
- `core/crates/tool/services/src/files/VisualFileSystem.rs`
- `core/crates/tool/services/src/files/PathMapper.rs`
