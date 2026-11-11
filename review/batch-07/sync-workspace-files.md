---
title: 工作区文件同步与 .operit/sync.json
module: sync
platforms: [all]
sources: [4]
date: 2026-11-11
---

## 概述

- 同一 Space 内，应用管理的工作区、无工作区时的对话产出目录与兼容旧版的附件目录按各自的 `.operit/sync.json` 自动双向复制普通文件，同步完成后副本可离线使用。`docs/workspace-file-sync.md:3`
- 只有配对、尚未加入同一 Space 时不共享文件。`docs/workspace-file-sync.md:3`
- 同步复用 `runtime_file` 域、SHA-256 Blob、原有向量时钟、成员校验与传输，不增加第二套同步协议。`docs/workspace-file-sync.md:40`
- 同步复制文件字节，不是 Git 或文本协同编辑。`docs/workspace-file-sync.md:52`
- 同时修改同一文件时按现有同步操作的确定性顺序（时间、设备 ID、序号）决定最终版本，不做逐行合并。`docs/workspace-file-sync.md:52`
- VFS 的 `/virtual` 入口挂到平台文件系统及授权资源后端，挂载与访问边界见 [[sync-vfs|VFS 挂载与文件访问边界]]。`docs/vfs-mounts.md:5`

## AI 速览

- `WorkspaceFileSyncStore` — 受管工作区文件的扫描、发布与接收。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:42`
- `FileSyncPolicy` — 一份 `.operit/sync.json` 策略，含 `version`、`ignoreFiles`、`exclude`、`maxFileBytes` 与 `maxTotalBytes` 五个字段。`core/crates/persistence/store/src/FileSyncPolicy.rs:20` `core/crates/persistence/store/src/FileSyncPolicy.rs:11`
- `FileReference` — 超限原件的定位文件，含 `nodeId`、`path`、`fileName`、`fileSize` 与可选的 `modifiedAt`。`core/crates/persistence/store/src/FileSyncPolicy.rs:240`
- `MANAGED_ROOTS` — 三个受管根：`workspaces`、产出目录与旧附件目录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:20`
- `POLICY_PATH` — 策略文件相对路径 `.operit/sync.json`。`core/crates/persistence/store/src/FileSyncPolicy.rs:11`
- 主入口函数：WorkspaceFileSyncStore 的 `scan`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:93`
- 主入口函数：WorkspaceFileSyncStore 的 `trackPaths`，在应用修改前后各扫描一次。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:120`
- 数据流向一句话：受管目录文件经扫描比对修改时间与大小，变化生成 `upsert` 或 `delete`。`docs/workspace-file-sync.md:45`
- 数据流向一句话：接收端按本地策略接受或推迟入站文件，推迟的文件进入 `deferred`，策略放宽后重新变得可传输。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:410`

## 核心机制

- 工作区 VFS 入口 `/operitapp/workspaces/<目录>` 对应存储位置 `workspaces/<目录>`。`docs/workspace-file-sync.md:7`
- 产出目录 VFS 入口 `/operitapp/outputs/<父对话创建时间>` 对应存储位置 `runtime/data/chat_outputs/<父对话创建时间>`。`docs/workspace-file-sync.md:8`
- 旧附件 VFS 入口 `/operitapp/data/data/chat_attachments/<chatId>` 对应存储位置 `runtime/data/chat_attachments/<chatId>`。`docs/workspace-file-sync.md:9`
- `MANAGED_ROOTS` 由 `workspaces`、`RUNTIME_CHAT_OUTPUTS_DIR_PATH` 与 `LEGACY_CHAT_ATTACHMENTS_DIR_PATH` 三个受管根组成。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:20`
- WorkspaceFileSyncStore 的 `manages` 在路径以受管根加斜杠开头时返回真。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:81`
- WorkspaceFileSyncStore 的 `affectedBy` 覆盖受管路径与其祖先路径。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:87`
- WorkspaceFileSyncStore 的 `owns` 在操作域为 `RUNTIME_FILE_SYNC_DOMAIN` 且 `manages` 覆盖 `entityId` 时判定归属。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:76`
- scanUnlocked 对每个受管根下的目录条目调用 FileSyncPolicy 的 `loadForScan` 加载该目录的策略。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:184`
- `managedDirectory` 取受管根下第一段作为拥有该文件的受管目录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:563`
- `managedVfsPath` 把 `workspaces/` 前缀映射为 `/operitapp/workspaces/`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:573`
- `managedVfsPath` 把 chat_outputs 前缀映射为 `/operitapp/outputs/`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:574`
- `managedVfsPath` 把其余 `runtime/` 前缀映射为 `/operitapp/data/`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:575`
- `validatePath` 要求路径属于受管路径且所有权为 `Space`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:579`
- `validateFilePath` 要求受管文件属于某个受管目录，不接受目录本身作为文件路径。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:584`
- FileSyncPolicy 的默认 `version` 为 1。`core/crates/persistence/store/src/FileSyncPolicy.rs:27`
- FileSyncPolicy 的默认 `ignoreFiles` 为 [`.gitignore`]。`core/crates/persistence/store/src/FileSyncPolicy.rs:28`
- FileSyncPolicy 的默认 `exclude` 含 `.git/`、`node_modules/`、`target/` 与 `build/`。`core/crates/persistence/store/src/FileSyncPolicy.rs:30`
- FileSyncPolicy 的默认 `exclude` 含 `dist/`、`.dart_tool/`、`.gradle/` 与 `__pycache__/`。`core/crates/persistence/store/src/FileSyncPolicy.rs:34`
- FileSyncPolicy 的默认 `maxFileBytes` 为 `DEFAULT_AUTO_SYNC_FILE_BYTES`。`core/crates/persistence/store/src/FileSyncPolicy.rs:42`
- FileSyncPolicy 的默认 `maxTotalBytes` 为 `DEFAULT_AUTO_SYNC_TOTAL_BYTES`。`core/crates/persistence/store/src/FileSyncPolicy.rs:43`
- 默认策略的 `maxFileBytes` 为 16777216，`maxTotalBytes` 为 268435456。`docs/workspace-file-sync.md:27`
- 默认单文件 16 MiB，每个受管理目录自动同步总量 256 MiB。`docs/workspace-file-sync.md:32`
- `maxFileBytes` 与 `maxTotalBytes` 只控制自动复制，不限制本地原件大小，也不是设备总磁盘配额。`docs/workspace-file-sync.md:32`
- `.operit/sync.json` 本身始终参与同步。`docs/workspace-file-sync.md:32`
- FileSyncPolicy 的 `ensure` 只在策略文件不存在时写入默认策略，已有配置保留。`core/crates/persistence/store/src/FileSyncPolicy.rs:71`
- 策略文件缺失时 `loadForScan` 返回默认策略。`core/crates/persistence/store/src/FileSyncPolicy.rs:57`
- 策略 `version` 不为 1 时 loadForScan 报错 `Unsupported sync policy version`。`core/crates/persistence/store/src/FileSyncPolicy.rs:63`
- `MAX_POLICY_BYTES` 为 256 * 1024，限制策略文件与忽略文件的读取长度。`core/crates/persistence/store/src/FileSyncPolicy.rs:13`
- 读取超出限额时 readLimitedForScan 报错 `exceeds the allowed`。`core/crates/persistence/store/src/FileSyncPolicy.rs:175`
- `validateRelative` 拒绝空串、斜杠开头、含反斜杠、冒号或 NUL，以及含空段、`.` 段或 `..` 段的 ignoreFiles 条目。`core/crates/persistence/store/src/FileSyncPolicy.rs:186`
- `rulesForScan` 把 `exclude` 的每条规则加入 `GitignoreBuilder`。`core/crates/persistence/store/src/FileSyncPolicy.rs:97`
- rulesForScan 再读取 `ignoreFiles` 指定的忽略文件并追加规则。`core/crates/persistence/store/src/FileSyncPolicy.rs:106`
- `includesForScan` 对控制路径直接返回真，即控制路径始终计入同步。`core/crates/persistence/store/src/FileSyncPolicy.rs:129`
- `ignoreFiles` 含 `.gitignore` 时，includesForScan 沿路径的各级父目录读取 `.gitignore` 并追加规则。`core/crates/persistence/store/src/FileSyncPolicy.rs:135`
- `ignored` 按规则顺序求值，后出现的白名单反选推翻前面的忽略。`core/crates/persistence/store/src/FileSyncPolicy.rs:220`
- `isControl` 判定路径等于受管目录下的 .operit/sync.json 或 `.operit` 目录本身。`core/crates/persistence/store/src/FileSyncPolicy.rs:229`
- scanUnlocked 中控制路径与定位文件不计入单文件限额与总量预算，直接进入待同步清单。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:196`
- 被排除的目录在遍历前剪枝，不复制内容，也不逐文件生成定位索引。`docs/workspace-file-sync.md:77`
- 不得整体排除存放附件和定位文件的 `.operit/`。`docs/workspace-file-sync.md:77`
- 外部挂载目录 `/virtual/...` 与 `/data/...` 不会被扫描。`docs/workspace-file-sync.md:13`
- WorkspaceFileSyncStore 的 `scan` 只扫描受管根，不查挂载的 VFS 目录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:93`
- 软链接、链接目录、失效链接、在 Windows 上的 junction/reparse point 以及非普通文件跳过，不跟随目标。`docs/workspace-file-sync.md:13`
- 接收端也不通过已有链接读写文件。`docs/workspace-file-sync.md:13`
- 目标路径上某组件已存在但不在目录列表中时，接收端报错 `Workspace synchronization will not follow a link`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:536`
- `checkDestination` 在目标路径出现文件与目录类型冲突时报错 `Workspace file/directory conflict`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:530`
- 排除文件继续保留在原设备，已有副本不会因为策略收紧而自动删除。`docs/workspace-file-sync.md:54`
- 新增忽略规则、文件变大或超过总量预算只会停止自动复制，不会作为删除广播，也不清理其他设备已有副本。`docs/workspace-file-sync.md:36`
- 取消忽略或放宽限额后，保留的远端最新状态可重新应用。`docs/workspace-file-sync.md:36`
- 无效 JSON、超大的规则文件或非法规则会报告错误并停止该次扫描，不发布一批错误删除。`docs/workspace-file-sync.md:36`
- 超限原件保留在本机，分享 `<原文件名>.operit-ref.json` 定位文件。`docs/workspace-file-sync.md:34`
- FileReference 的 `format` 为 `operit_file_reference`，`version` 为 1。`core/crates/persistence/store/src/FileSyncPolicy.rs:257`
- FileReference 的 `validate` 要求 `path` 以 `/app/`、`/operitapp/`、`/mnt/`、`/virtual/` 之一开头。`core/crates/persistence/store/src/FileSyncPolicy.rs:271`
- `wantsBlob` 在申请 Blob 之前检查本地策略，避免先下载大文件再排除。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:404`
- 被策略推迟的文件进入 `deferred`，策略放宽后 `deferredBlobs` 重新变得可传输。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:410`
- `acceptsForScan` 对待接收文件用本地策略的 `maxFileBytes` 核对单文件上限。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:440`
- acceptsForScan 把待接收文件大小与同目录下已收文件大小相加后与 `maxTotalBytes` 比较。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:453`
- `captureReference` 在定位文件路径已被占用且内容与新定位不符时报错 `Reference path is occupied`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:281`
- `removeLocalReference` 只删除本节点自己生成的定位文件。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:299`
- 文件只按修改时间和大小判同，没有创建时间或定期内容哈希检查。`docs/workspace-file-sync.md:43`
- 未变化的文件不读内容，文件有变化时只读取一次。`docs/workspace-file-sync.md:43`
- `upsert` 携带源文件修改时间（Unix 微秒），接收端写入字节后恢复该时间。`docs/workspace-file-sync.md:44`
- `writePending` 写入字节后按快照的 `modifiedAt` 调用 `setModifiedAt` 恢复修改时间。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:492`
- 文件内容改变生成 `upsert`，消失生成 `delete`，重命名表示旧路径删除、新路径写入。`docs/workspace-file-sync.md:45`
- 删除优先于新增，以支持文件与目录之间切换。`docs/workspace-file-sync.md:45`
- 扫描时先为被替换路径记 `tombstone` 再发布 `upsert`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:238`
- 收到文件后更新清单，不把远端内容当成新本地修改再次广播。`docs/workspace-file-sync.md:47`
- 接收前先持久化待应用内容，异常退出后重放待应用写入。`docs/workspace-file-sync.md:48`
- 扫描失败不发布缺失文件删除。`docs/workspace-file-sync.md:48`
- 受管根不可用且清单中仍有该根下文件时，scanUnlocked 报错拒绝批量删除。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:177`
- `scanRead` 对 `NotFound` 与 `PermissionDenied` 跳过该路径并保留先前清单。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:264`
- 首次加入 Space 后重新登记设备已有的本体文件，避免旧操作日志不再导出而使本地文件无法分享。`docs/workspace-file-sync.md:49`
- `trackPaths` 在应用修改前后各扫描一次，即时捕获应用内写入。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:120`
- 定时扫描稳定空闲时以指数退避拉长轮询间隔，2 秒起，上限 60 秒，发现变更立即回到 2 秒。`docs/workspace-file-sync.md:42`
- 关闭 Core 后不后台运行，重新启动时补扫。`docs/workspace-file-sync.md:42`
- 停止 Space 同步服务时停止定时扫描。`docs/workspace-file-sync.md:50`
- 本地清单保存在 `runtime/sync/workspace_inventory.json`，记录已观察到的文件修改时间和大小，不同步给其他设备。`docs/workspace-file-sync.md:41`
- 目录随文件创建。`docs/workspace-file-sync.md:53`
- 删除后清理空的子目录，保留工作区根目录。`docs/workspace-file-sync.md:53`
- 独立空目录、文件权限和执行位不作为同步对象。`docs/workspace-file-sync.md:53`
- 同一文件的一组待处理状态只落盘最终胜者。`docs/workspace-file-sync.md:46`
- 每个接收批次只扫一次工作区，应用整批操作后才推进同步时钟。`docs/workspace-file-sync.md:47`
- 产出目录绑定保存在 `runtime/data/chat_output_bindings/<chatId>.json`，随 Space 同步。`docs/workspace-file-sync.md:11`
- 产出目录名采用首次父对话创建时间 `YYYY-MM-DD_HH-mm-ss-SSS`，绑定保存后不按当天重算。`docs/workspace-file-sync.md:11`
- 子孙对话和消息分支继承已保存的产出目录绑定。`docs/workspace-file-sync.md:11`
- 提升子对话、删除父对话、切换工作区不会改变已有产出目录。`docs/workspace-file-sync.md:11`
- 创建时间相同允许共用同一产出目录。`docs/workspace-file-sync.md:11`
- 产出区域不会被当作用户绑定的工作区。`docs/workspace-file-sync.md:11`
- 聊天文件变更快照保存在对应工作区的 `.operit/backups/<聊天作用域>/`，`state.json` 记录最近编辑轮次的文件变更，`objects/` 保存按内容哈希寻址的文件字节。`docs/workspace-file-sync.md:82`
- 每个聊天只保留最近一次涉及文件修改的轮次。`docs/workspace-file-sync.md:74`
- `.operit` 被快照捕获规则排除，避免备份把自身再次备份。`docs/workspace-file-sync.md:78`
- 工作区本体中的备份文件按普通文件同步规则处理，外部挂载内的备份仍遵循外部挂载不参与同步的边界。`docs/workspace-file-sync.md:79`

## 关键符号

- `WorkspaceFileSyncStore` — 受管工作区文件的扫描、发布与接收。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:42`
- `MANAGED_ROOTS` — 三个受管根：`workspaces`、产出目录与旧附件目录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:20`
- WorkspaceFileSyncStore 的 `manages` — 判断路径是否属于受管根。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:81`
- WorkspaceFileSyncStore 的 `affectedBy` — 覆盖受管路径与其祖先路径。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:87`
- WorkspaceFileSyncStore 的 `owns` — 操作域为 `RUNTIME_FILE_SYNC_DOMAIN` 且 `manages` 覆盖 `entityId` 时判定归属。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:76`
- WorkspaceFileSyncStore 的 `scan` — 只扫描受管根，不查挂载的 VFS 目录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:93`
- WorkspaceFileSyncStore 的 `scanUnlocked` — 执行一次完整扫描并返回变化数。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:152`
- WorkspaceFileSyncStore 的 `collect` — 遍历每个受管子目录并按策略收集文件。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:309`
- WorkspaceFileSyncStore 的 `trackPaths` — 在应用修改前后各扫描一次，即时捕获应用内写入。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:120`
- WorkspaceFileSyncStore 的 `applyOperation` — 落盘操作并追加操作记录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:333`
- WorkspaceFileSyncStore 的 `materializeOperations` — 按批应用操作。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:345`
- WorkspaceFileSyncStore 的 `applyUnlocked` — 按 `upsert` 或 `delete` 落盘待应用状态。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:381`
- WorkspaceFileSyncStore 的 `wantsBlob` — 在申请 Blob 之前检查本地策略。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:404`
- WorkspaceFileSyncStore 的 `deferredBlobs` — 被策略推迟的文件在策略放宽后重新变得可传输。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:410`
- WorkspaceFileSyncStore 的 `acceptsForScan` — 对待接收文件核对单文件上限与总量上限。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:440`
- WorkspaceFileSyncStore 的 `finishPending` — 完成待应用写入并提交清单。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:466`
- WorkspaceFileSyncStore 的 `writePending` — 写入字节后按快照的 `modifiedAt` 恢复修改时间。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:492`
- WorkspaceFileSyncStore 的 `removeEmptyParents` — 删除后清理空的父目录，保留工作区根目录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:510`
- WorkspaceFileSyncStore 的 `checkDestination` — 在目标路径出现文件与目录类型冲突时报错。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:530`
- WorkspaceFileSyncStore 的 `captureReference` — 在定位文件路径被占用且内容不符时报错。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:281`
- WorkspaceFileSyncStore 的 `removeLocalReference` — 只删除本节点自己生成的定位文件。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:299`
- `managedDirectory` — 取受管根下第一段作为拥有该文件的受管目录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:563`
- `managedVfsPath` — 把受管存储路径映射为 VFS 路径。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:573`
- `validatePath` — 要求路径属于受管路径且所有权为 `Space`。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:579`
- `validateFilePath` — 要求受管文件属于某个受管目录，不接受目录本身作为文件路径。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:584`
- `FileSyncPolicy` — 一份 `.operit/sync.json` 策略，含 `version`、`ignoreFiles`、`exclude`、`maxFileBytes` 与 `maxTotalBytes` 五个字段。`core/crates/persistence/store/src/FileSyncPolicy.rs:20` `core/crates/persistence/store/src/FileSyncPolicy.rs:11`
- FileSyncPolicy 的 `ensure` — 只在策略文件不存在时写入默认策略。`core/crates/persistence/store/src/FileSyncPolicy.rs:71`
- FileSyncPolicy 的 `loadForScan` — 策略文件缺失时返回默认策略。`core/crates/persistence/store/src/FileSyncPolicy.rs:57`
- FileSyncPolicy 的 loadForScan — 策略 `version` 不为 1 时报错。`core/crates/persistence/store/src/FileSyncPolicy.rs:63`
- FileSyncPolicy 的 `rulesForScan` — 把 `exclude` 的每条规则加入 `GitignoreBuilder`。`core/crates/persistence/store/src/FileSyncPolicy.rs:97`
- FileSyncPolicy 的 rulesForScan — 再读取 `ignoreFiles` 指定的忽略文件并追加规则。`core/crates/persistence/store/src/FileSyncPolicy.rs:106`
- FileSyncPolicy 的 `includesForScan` — 对控制路径直接返回真，即控制路径始终计入同步。`core/crates/persistence/store/src/FileSyncPolicy.rs:129`
- FileSyncPolicy 的 includesForScan — 含 `.gitignore` 时沿路径的各级父目录读取 `.gitignore` 并追加规则。`core/crates/persistence/store/src/FileSyncPolicy.rs:135`
- `POLICY_PATH` — 策略文件相对路径 `.operit/sync.json`。`core/crates/persistence/store/src/FileSyncPolicy.rs:11`
- `REFERENCE_SUFFIX` — 定位文件后缀 `.operit-ref.json`。`core/crates/persistence/store/src/FileSyncPolicy.rs:12`
- `MAX_POLICY_BYTES` — 策略文件与忽略文件的读取上限 256 * 1024。`core/crates/persistence/store/src/FileSyncPolicy.rs:13`
- `ignored` — 按规则顺序求值，后出现的白名单反选推翻前面的忽略。`core/crates/persistence/store/src/FileSyncPolicy.rs:220`
- `isControl` — 判定路径等于受管目录下的 .operit/sync.json 或 `.operit` 目录本身。`core/crates/persistence/store/src/FileSyncPolicy.rs:229`
- `validateRelative` — 拒绝非法 ignoreFiles 条目。`core/crates/persistence/store/src/FileSyncPolicy.rs:186`
- readLimitedForScan — 读取超出限额时报错 `exceeds the allowed`。`core/crates/persistence/store/src/FileSyncPolicy.rs:175`
- `FileReference` — 超限原件的定位文件，含 `nodeId`、`path`、`fileName`、`fileSize` 与可选的 `modifiedAt`。`core/crates/persistence/store/src/FileSyncPolicy.rs:240`
- FileReference 的 `validate` — 要求 `path` 以 `/app/`、`/operitapp/`、`/mnt/`、`/virtual/` 之一开头。`core/crates/persistence/store/src/FileSyncPolicy.rs:271`

## 调用链

1. 应用内写入：WorkspaceFileSyncStore 的 `trackPaths` 在修改前扫描一次，写入后立即再扫描一次。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:120`
2. 定时扫描：Core 运行时定时扫描覆盖终端、外部编辑器和其它绕过应用入口的写入，稳定空闲时从 2 秒起指数退避、上限 60 秒，发现变更立即回到 2 秒。`docs/workspace-file-sync.md:42`
3. 扫描执行：WorkspaceFileSyncStore 的 `scanUnlocked` 执行一次完整扫描并返回变化数。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:152`
4. 策略加载：scanUnlocked 对每个受管根下的目录条目调用 FileSyncPolicy 的 `loadForScan` 加载该目录的策略。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:184`
5. 收集文件：WorkspaceFileSyncStore 的 `collect` 遍历每个受管子目录并按策略收集文件。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:309`
6. 预算判定：控制路径与定位文件直接进入待同步清单，其余文件按单文件限额与总量预算分流。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:196`
7. 发布变化：文件内容改变生成 `upsert`，消失生成 `delete`，重命名表示旧路径删除、新路径写入。`docs/workspace-file-sync.md:45`
8. 接收检查：`wantsBlob` 在申请 Blob 之前检查本地策略，避免先下载大文件再排除。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:404`
9. 接收落盘：WorkspaceFileSyncStore 的 `applyOperation` 落盘操作并追加操作记录。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:333`
10. 写入恢复：`writePending` 写入字节后按快照的 `modifiedAt` 调用 `setModifiedAt` 恢复修改时间。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:492`
11. 清单提交：`finishPending` 完成待应用写入并提交清单。`core/crates/persistence/store/src/WorkspaceFileSyncStore.rs:466`
12. 首次加入：首次加入 Space 后重新登记设备已有的本体文件，避免旧操作日志不再导出而使本地文件无法分享。`docs/workspace-file-sync.md:49`

## 来源

- `core/crates/persistence/store/src/FileSyncPolicy.rs`
- `core/crates/persistence/store/src/WorkspaceFileSyncStore.rs`
- `docs/vfs-mounts.md`
- `docs/workspace-file-sync.md`
