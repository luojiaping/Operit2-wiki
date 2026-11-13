---
title: 大同步进度与联调记录
module: sync
platforms: [all]
sources: [3]
date: 2026-11-11
---

## 概述

- 首次加入、离线后积累的大批增量、路由切换和失败恢复走同一条同步链路；展示条件不依赖是否首次加入。`docs/device-space-large-sync-progress.md:14`
- 加入完成只唤醒原有后台调度，不等待业务数据全部同步后才向界面返回。`docs/device-space-large-sync-progress.md:16`
- 接收成功不等于业务应用成功；`receipt` 中的 `pending`、`errors` 和缺失文件留给后续轮次。`docs/device-space-large-sync-progress.md:9`
- 一个 `CoreNode` 共享一个同步服务状态；后台同步、加入后的唤醒及路由切换前的同步使用相同 gate，同一对端串行执行。`docs/device-space-large-sync-progress.md:15`
- 同步进度用 `SpaceSyncProgress` 记录本地执行进度，与成员关系和同步 receipt 独立。`core/crates/node/runtime/src/SpaceSyncProgress.rs:23`
- 状态流独立于拓扑流，避免进度更新触发拓扑和权限重新加载。`docs/device-space-large-sync-progress.md:17`
- 业务同步要求两端都有存储权限，完整同步机制见 [[sync-overview|同步总览：Space 持久化同步]]。`docs/device-space-large-sync-progress.md:7`
- 加入流程从 `space_join::refresh` 开始，校验审批结果并导入成员、身份和拓扑，发布 `Joined`；配对与加入的完整机制见 [[sync-discovery-join|局域网发现、配对与加入 Space]]。`docs/device-space-large-sync-progress.md:5`

## AI 速览

- `SpaceSyncProgress` — 一次同步任务的本地执行进度，与成员关系和同步 receipt 独立。`core/crates/node/runtime/src/SpaceSyncProgress.rs:23`
- `SpaceSyncStatus` — `Syncing` / `Waiting` / `Completed`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:8`
- `SpaceSyncStage` — `Checking` / `Records` / `Files`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:15`
- `SyncProgressTracker` — 会话表与可见性门禁。`core/crates/node/runtime/src/SpaceSyncProgress.rs:66`
- `SyncProgressSession` — 一次会话的进度、可见标志与待处理/错误账本。`core/crates/node/runtime/src/SpaceSyncProgress.rs:58`
- `LARGE_SYNC_DELAY_MS` / `LARGE_SYNC_RECORDS` / `LARGE_SYNC_BYTES` — 3 秒 / 256 条 / 1 MiB 门槛。`core/crates/node/runtime/src/SpaceSyncProgress.rs:44`
- `RuntimeActivityOverlay` — 根部统一订阅大同步状态的全局任务浮层。`docs/device-space-large-sync-progress.md:66`
- 主入口函数：`begin`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:137`
- 数据流向一句话：同步执行直接产生进度状态，经可见性门禁后由 `flow` 向界面发布，隐藏会话不越过代理。`core/crates/node/runtime/src/SpaceSyncProgress.rs:86`

## 核心机制

### 同一条链路：首次加入与离线增量

- 此链路同时覆盖首次加入、离线后积累的大批增量、路由切换和失败恢复；展示条件不依赖是否首次加入。`docs/device-space-large-sync-progress.md:14`
- 离线成员继续通过原有可达性检查跳过，失败遵循原有指数退避。`docs/device-space-large-sync-progress.md:14`
- 一个 `CoreNode` 共享一个同步服务状态；后台同步、加入后的唤醒及路由切换前的同步使用相同 gate，同一对端串行执行。`docs/device-space-large-sync-progress.md:15`
- 加入完成只唤醒原有后台调度，不等待业务数据全部同步后才向界面返回。`docs/device-space-large-sync-progress.md:16`
- 修复前，Full Core 的 `RuntimeRemoteLinkService::afterJoined` 直接等待 `synchronizeReachablePeer`，失败只写日志。`docs/device-space-large-sync-progress.md:6`
- 常驻同步服务由持久化变更、连接变化、每两秒的文件扫描唤醒。`docs/device-space-large-sync-progress.md:6`
- 常驻服务 `synchronizeOnce` 先交换空间投影，再通过 change gate 对可达成员执行权限交换、设备偏好交换、版本检查和业务同步。`docs/device-space-large-sync-progress.md:7`
- 业务同步要求两端都有存储权限。`docs/device-space-large-sync-progress.md:7`
- `synchronizeDomains` 比较 `receipt`，合并双向差异，按操作数和传输字节分页；先补齐引用文件，再向两端提交操作。`docs/device-space-large-sync-progress.md:8`
- 文件按 64 KiB 分块，关闭传输后再次检查文件是否落盘。`docs/device-space-large-sync-progress.md:8`
- 每轮最多 64 页。`docs/device-space-large-sync-progress.md:9`
- UI 的 `deviceSpaceSnapshotFlow` 只有成员和拓扑，没有同步执行信息。`docs/device-space-large-sync-progress.md:10`
- 修复前，独立创建的 facade 会创建独立的同步状态，首次同步与常驻同步没有共用 gate。`docs/device-space-large-sync-progress.md:10`
- 同步过程直接产生状态：检查差异、交换记录、传输文件、等待重试、完成。`docs/device-space-large-sync-progress.md:17`
- 状态流独立于拓扑流，避免进度更新触发拓扑和权限重新加载。`docs/device-space-large-sync-progress.md:17`
- 隐藏任务只保留本地计数；等待同步结果的同时竞争一个延时，快任务完成即取消延时，不为每次小同步留下独立定时任务。`docs/device-space-large-sync-progress.md:17`
- 一次任务跨多个分页轮次及失败重试；到达页数上限、重复页、业务 `pending` 或错误均不能标记完成。`docs/device-space-large-sync-progress.md:18`

### 进度何时向界面发布

- 服务仅在任务持续 3 秒，且达到 256 条交换记录、总量 256 条、1 MiB 实际传输量或当前文件大小后发布可见进度。`docs/device-space-large-sync-progress.md:20`
- 可见进度门槛常量为 `LARGE_SYNC_DELAY_MS` 3000 毫秒、`LARGE_SYNC_RECORDS` 256 条、`LARGE_SYNC_BYTES` 1024×1024 字节。`core/crates/node/runtime/src/SpaceSyncProgress.rs:44`
- `hasSubstantialWork` 在 `exchangedRecords` 达到 256 条、`totalRecords` 达到 256 条、`transferredBytes` 达到 1 MiB 或 `fileSize` 达到 1 MiB 时返回真。`core/crates/node/runtime/src/SpaceSyncProgress.rs:49`
- 仅在会话已有实质工作量（`hasSubstantialWork`）时把会话置为可见。`core/crates/node/runtime/src/SpaceSyncProgress.rs:205`
- `reveal` 仅在会话已有实质工作量时把会话置为可见。`core/crates/node/runtime/src/SpaceSyncProgress.rs:199`
- 进度更新后，会话在已有实质工作量（`hasSubstantialWork`）且已满 3 秒、或出现 `error` 时变为可见。`core/crates/node/runtime/src/SpaceSyncProgress.rs:224`
- `revealDelayMs` 返回某对端隐藏会话的剩余揭示延迟毫秒数。`core/crates/node/runtime/src/SpaceSyncProgress.rs:184`
- 剩余延迟等于 `LARGE_SYNC_DELAY_MS` 减去自 `startedAt` 经过的时间，夹在 0 到 3000 之间。`core/crates/node/runtime/src/SpaceSyncProgress.rs:194`
- `flow` 只返回 `visible` 为真的会话进度，隐藏会话不越过代理、不重建界面。`core/crates/node/runtime/src/SpaceSyncProgress.rs:86`
- `peer` 只返回已可见的会话进度，不把隐藏会话或已完成旧会话暴露给调用方。`core/crates/node/runtime/src/SpaceSyncProgress.rs:80`
- 小同步的开始、批次和完成均不产生界面事件，也不额外统计全部待同步数据。`docs/device-space-large-sync-progress.md:20`
- 进度显示后跨轮次保留，完成后保留 3 秒；界面由根部 `RuntimeActivityOverlay` 统一订阅，页面切换不影响任务展示；仅完成收起使用定时器。`docs/device-space-large-sync-progress.md:20`
- 权限撤销、成员退出或空间切换时清除不再适用的进度。`docs/device-space-large-sync-progress.md:21`
- 结束时，在 `pending` 为真、有 `error` 或 `pendingRecords` 大于 0 时状态置为 `Waiting`，否则置为 `Completed`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:314`
- 结束时状态为 `Completed` 的会话清除 `error`，并把 `totalRecords` 置为 `completedRecords`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:321`
- 快速成功的不可见已完成会话在结束后从会话列表中移除，不产生可观察的生命周期。`core/crates/node/runtime/src/SpaceSyncProgress.rs:329`
- 测试：连续 20 次小同步只收到 1 次初始空快照事件，`flow` 为空。`core/crates/node/runtime/src/SpaceSyncProgress.rs:398`
- 测试：慢小同步在延迟届满后调用 `reveal` 仍不产生可见进度，`flow` 为空。`core/crates/node/runtime/src/SpaceSyncProgress.rs:413`
- 测试：大库存同步在延迟届满前不揭示，延迟届满后 `reveal` 才让进度可见，`flow` 长度为 1。`core/crates/node/runtime/src/SpaceSyncProgress.rs:431`
- 测试：延迟届满后，记录数、当前文件大小或累计传输量任一跨过门槛，`flow` 长度变为 1。`core/crates/node/runtime/src/SpaceSyncProgress.rs:464`
- 测试：待处理轮次与重试共用同一会话，`startedAt` 不变，`exchangedRecords` 跨轮次累加到 522。`core/crates/node/runtime/src/SpaceSyncProgress.rs:482`

### 接收成功为什么不等于业务应用成功

- 接收成功不等于业务应用成功；`receipt` 中的 `pending`、`errors` 和缺失文件留给后续轮次。`docs/device-space-large-sync-progress.md:9`
- `synchronizeDomains` 比较 `receipt`，合并双向差异，按操作数和传输字节分页；先补齐引用文件，再向两端提交操作。`docs/device-space-large-sync-progress.md:8`
- 一次任务跨多个分页轮次及失败重试；到达页数上限、重复页、业务 `pending` 或错误均不能标记完成。`docs/device-space-large-sync-progress.md:18`
- `report` 按端（`side`）记录未应用标识与错误。`core/crates/node/runtime/src/SpaceSyncProgress.rs:240`
- `pendingRecords` 取各端待处理标识集合的并集大小；错误非空时会话置为可见。`core/crates/node/runtime/src/SpaceSyncProgress.rs:247`
- `confirmRecords` 只在两端都不再把某条原始记录报为未应用后才计入 `completedRecords`，每条原始记录只计一次。`core/crates/node/runtime/src/SpaceSyncProgress.rs:261`
- 计入已完成记录后，`totalRecords` 取原值与已见原始记录数（`workIds` 长度）的较大值。`core/crates/node/runtime/src/SpaceSyncProgress.rs:263`
- `backlog` 从实际导出清单刷新总量：`totalRecords` 等于 `completedRecords` 加剩余数再加共享待处理数。`core/crates/node/runtime/src/SpaceSyncProgress.rs:231`
- 测试：同一失败在两端各报一次只计 1 条 `pendingRecords`；512 条原始记录中有 1 条失败时 `completedRecords` 为 511、`totalRecords` 为 10000、`pendingRecords` 为 1。`core/crates/node/runtime/src/SpaceSyncProgress.rs:355`
- 测试：结束时 `pending` 为真则状态为 `Waiting`，并保留应用错误。`core/crates/node/runtime/src/SpaceSyncProgress.rs:358`
- 测试：缺失清单时 `totalRecords` 为 `None`，不凭页面大小编造总量；小错误仍可见，结束时状态为 `Waiting`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:378`
- 测试：失败的原始记录在后续轮次重新上报为空后，`completedRecords` 升到 512，`pendingRecords` 归零。`core/crates/node/runtime/src/SpaceSyncProgress.rs:367`
- 验证范围要求 Rust 检查共享服务、任务跨轮次与重试、真实批次和文件统计、分页退出的 `pending` 语义。`docs/device-space-large-sync-progress.md:25`

### 文件传输与字节统计

- 双向文件传输共用一段分块循环，保留逐块权限检查和落盘校验。`docs/device-space-large-sync-progress.md:19`
- 统计已确认交换的记录与实际发送的文件字节；当前文件有真实大小才能显示比例，没有总量时不构造总体百分比。`docs/device-space-large-sync-progress.md:19`
- 字节统计表示传输量，重传也计入。`docs/device-space-large-sync-progress.md:19`
- `records` 把阶段切到 `Records`，`exchangedRecords` 累加传入条数，并把 `fileBytes` 与 `fileSize` 清零。`core/crates/node/runtime/src/SpaceSyncProgress.rs:270`
- `beginFile` 把阶段切到 `Files`，`fileBytes` 清零，`fileSize` 记为传入大小。`core/crates/node/runtime/src/SpaceSyncProgress.rs:280`
- `fileOffset` 每秒最多发布 5 次文件偏移更新（200 毫秒节流），但始终发布最终偏移。`core/crates/node/runtime/src/SpaceSyncProgress.rs:291`
- `fileOffset` 把偏移夹在 `fileBytes` 与 `fileSize` 之间，`transferredBytes` 累加偏移增量，重传计入传输量。`core/crates/node/runtime/src/SpaceSyncProgress.rs:294`
- 测试：两个 1024 字节文件传完后 `fileSize` 为 1024、`fileBytes` 为 1024、`transferredBytes` 为 2048，重传计入传输量。`core/crates/node/runtime/src/SpaceSyncProgress.rs:517`
- 测试：收到一条新记录后，`fileSize` 被清零。`core/crates/node/runtime/src/SpaceSyncProgress.rs:519`

### 全局任务浮层与代理复用

- `OperitTheme` 根部保留一个 `RuntimeActivityOverlay`，直接消费现有包加载状态与大同步状态，不新增通用任务框架。`docs/device-space-large-sync-progress.md:66`
- 原 `PluginLoadingOverlay` 与设置页的 `SpaceSyncProgressCard`、同步订阅一起移除。`docs/device-space-large-sync-progress.md:67`
- 折叠态为 232 × 64 的圆角卡片，含任务图标、两行摘要、底部细进度条；多任务增加数量提示。`docs/device-space-large-sync-progress.md:70`
- 点击展开后在同一个可滚动面板中查看各设备同步、包启动详情和原有日志；卡片支持拖动并约束在安全区域内；跳过包加载只调用原有包加载接口，不中断同步。`docs/device-space-large-sync-progress.md:70`
- 生成代理每次调用都会重建 facade；原 `localApplicationSharedClient()` 每次创建新的 `Arc`，导致同步服务注册表无法把后台 worker 与进度订阅识别为同一应用。`docs/device-space-large-sync-progress.md:76`
- `LocalCoreProxy` 现在通过共享 `Weak` 缓存复用仍存活的应用客户端，避免强引用环，同时保留不同应用实例的隔离；原生双端测试实际经过这条代理链路。`docs/device-space-large-sync-progress.md:78`
- `mirror` 把协调方的实际进度镜像到本端会话，并保留原 `startedAt`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:124`
- 镜像后的会话置为可见（`visible` 为 `true`）。`core/crates/node/runtime/src/SpaceSyncProgress.rs:132`
- 测试：镜像到不同空间的会话不进入 `flow`，`flow` 为空。`core/crates/node/runtime/src/SpaceSyncProgress.rs:534`
- 测试：`retain` 以空成员列表清理后，`flow` 为空。`core/crates/node/runtime/src/SpaceSyncProgress.rs:548`
- `retain` 只保留属于指定 `spaceId` 且对端在给定成员列表中的会话。`core/crates/node/runtime/src/SpaceSyncProgress.rs:107`
- 测试协调器仅负责阶段屏障与系统截图，不提供业务响应或注入同步进度。`docs/device-space-large-sync-progress.md:42`
- 包加载预览单独使用示例包状态，文件名以 `package-*-preview` 标注；同步进度与拓扑订阅始终使用原生 Core。`docs/device-space-large-sync-progress.md:43`
- Flutter 检查小同步静默、慢同步显示、文件进度、完成收起、重试、空间切换及与包加载共用的展开/折叠界面；客户端契约通过真实代理生成工具更新。`docs/device-space-large-sync-progress.md:25`

### 2026-10-25 验证记录

- 2026-10-25 验证：`cargo check -p operit-proxy-local` 通过，使用原有生成器生成代理契约。`docs/device-space-large-sync-progress.md:29`
- 2026-10-25 验证：先前设置页方案通过 50 项 Flutter 测试；当前已替换为全局任务浮层，下方记录最终全局方案的验证结果。`docs/device-space-large-sync-progress.md:30`
- 2026-10-25 验证：Rust 进度状态 4 项、原同步服务 8 项测试全部通过；连续 20 次小同步只收到初始空快照，没有进度事件。`docs/device-space-large-sync-progress.md:31`
- 2026-10-25 验证：设备空间行为回归 97 项中 95 项通过、2 项失败；最终全局方案已改为即使超过三秒仍保持静默，重建 facade 复用同一个 gate。`docs/device-space-large-sync-progress.md:32`
- 2026-10-25 验证：两项失败为 `doctor_detects_quarantines_and_selfchecks_damaged_lines` 和 `target_space_change_does_not_block_withdrawal_of_an_old_request`。`docs/device-space-large-sync-progress.md:33`
- 2026-10-25 验证：在隔离的 `6c1fa579` 源码副本上复用相同依赖、单独编译并运行，两项失败均在原断言失败，确认不由本次同步修改引入。`docs/device-space-large-sync-progress.md:33`
- 2026-10-25 验证：当前 macOS 测试链接需要显式补充本地模型依赖的 Accelerate，命令为 `cargo rustc -p operit-node-runtime --lib --profile test -- -l framework=Accelerate`，随后运行生成的测试程序；没有修改项目链接配置。`docs/device-space-large-sync-progress.md:34`
- 2026-10-25 验证：原有 `check_structure.py` 因 `coverage.json` 与测试清单不一致而失败；本次未新增或重命名该目录的测试用例，也未修改原有清单。`docs/device-space-large-sync-progress.md:35`
- 2026-10-25 最终全局方案验证：macOS 与 iOS 27.0 / iPhone 18 Pro Max 模拟器完整原生集成测试均通过。`docs/device-space-large-sync-progress.md:83`
- 2026-10-25 最终全局方案验证：首次加入传输 96 MiB 文件、断开监听并积压 96 MiB 文件后恢复增量，均落盘并核对 SHA-256。`docs/device-space-large-sync-progress.md:84`
- 2026-10-25 最终全局方案验证：6 字节小文本两端实际同步成功，无新增可见进度事件，截图中无同步浮层。`docs/device-space-large-sync-progress.md:85`
- 2026-10-25 最终全局方案验证：切换到工作空间页面后仍显示同一个全局同步浮层；完成后正常收起。`docs/device-space-large-sync-progress.md:86`
- 2026-10-25 最终全局方案验证：原生联测发现“仅三秒门槛”误展示慢的小同步，因此增加实际工作量门槛；不额外遍历待同步数据。`docs/device-space-large-sync-progress.md:87`
- 2026-10-25 最终全局方案验证：Flutter 全局浮层、设备设置、加入弹窗共 50 项通过；相关界面与集成测试静态分析无问题。`docs/device-space-large-sync-progress.md:88`
- 2026-10-25 最终全局方案验证：Rust 进度状态 5 项、同步分页与错误处理 8 项、原调度 gate 4 项通过；新增慢小同步静默、延时后才跨越记录门槛的状态测试。`docs/device-space-large-sync-progress.md:89`
- 2026-10-25 最终全局方案验证：两端原始截图及 `verification.json`、`native-events.json` 见 `docs/assets/sync-progress-2026-10-25/`。`docs/device-space-large-sync-progress.md:90`
- 2026-10-25 最终全局方案验证：`compact-preview.png` 仅裁切并拼排原始系统截图；包加载截图为示例包状态的原生界面预览，同步截图来自真实网络传输。`docs/device-space-large-sync-progress.md:91`
- 联调场景包括首次加入传输 96 MiB 工作区文件、暂停后台同步后积压 96 MiB 增量再恢复、最后同步一个小文本；大文件核对完整 SHA-256。`docs/device-space-large-sync-progress.md:60`
- 原生集成测试 `integration_test/device_space_sync_native_test.dart` 在两端分别创建独立存储目录，通过真实 HTTP Peer Link 配对、申请加入、审批并启动原有后台同步。`docs/device-space-large-sync-progress.md:41`
- 协调器启动命令为 `python3 apps/flutter/app/integration_test/device_space_sync_coordinator.py` `--output docs/assets/sync-progress-2026-10-25`。`docs/device-space-large-sync-progress.md:49`
- 两端分别运行 `fvm flutter test integration_test/device_space_sync_native_test.dart -d macos --reporter expanded` 与同一命令的 -d iOS 模拟器 UDID 变体。`docs/device-space-large-sync-progress.md:56`

### 2026-11-11 iOS/macOS 联调记录

- 范围说明：本节联调针对代码版本 `dc4079ab9`、Core `2.0.0-preview.31`、协议 v13（v14 反向联调为协议 v14），与 wiki 基线 364d1d594 不是同一版本；结论只适用于该次联调。`docs/device-space-native-testing.md:4`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）的测试时间为 00:07–00:20（Asia/Shanghai）。`docs/device-space-native-testing.md:3`
- 2026-11-11 iOS/macOS 模拟器联调的代码版本为 `dc4079ab9`，Core 为 `2.0.0-preview.31`，两端协议版本均为 13。`docs/device-space-native-testing.md:4`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：macOS 端为当前工作区构建的原生 Operit2 桌面应用，正常 `lib/main.dart` 入口。`docs/device-space-native-testing.md:8`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：iOS 端为 Device Hub 中的 iPhone 18 Pro / iOS 27.0 模拟器，正常应用入口。`docs/device-space-native-testing.md:9`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：两端均通过应用里的用户档案创建独立本地身份，然后切换并重启；Mac 测试身份显示为 `iOS-Mac`，iOS 测试身份为新建的未命名身份。`docs/device-space-native-testing.md:10`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：本次为模拟器与同一台 Mac 的实际界面操作，不是真机测试。`docs/device-space-native-testing.md:14`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：iOS 引导选择“加入已有设备空间”，点击“添加设备”后通过附近发现列表看到 macos-arm64，点击该设备；Mac 自动弹出六位配对码。`docs/device-space-native-testing.md:18`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：在 iOS 屏幕数字键盘输入配对码，点击“完成连接”；iOS 显示“申请加入空间 / 等待批准”，Mac 随后弹出“空间加入申请”，在 Mac 点击“批准”。`docs/device-space-native-testing.md:22`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：Mac 显示“共 2 台设备 / 2 在线”；iOS 设备条目为“普通用户 / 在线 · 直连 · 空间成员 · 已直连”。`docs/device-space-native-testing.md:24`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：iOS 完成引导后进入设置中的设备空间，显示“2 台设备 / 2 在线”；Mac 设备条目为“管理员 / 在线 · 直连 · 空间成员 · 已直连”。`docs/device-space-native-testing.md:26`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：通过 simctl 终止并重新启动 iOS 应用后，Mac 再次显示 iOS 在线、直连、空间成员；后续恢复界面检查中，iOS 设备空间同样显示两台设备在线、直连、空间成员。`docs/device-space-native-testing.md:28`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：只读核对的本地记录中，Mac 节点为 core-1794327047074-0e5a84557ee14bbaba4b26683ac3a213，iOS 节点为 core-1794327022645-6f9378d30b55488eabf8ced2fc867d9e。`docs/device-space-native-testing.md:38`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：加入请求为 c170fd78-1962-4a64-926d-79dd3b538ab9，Mac 入站记录 status 为 approved，iOS 出站记录 status 为 joined，加入目标空间为 space-df7fba0d90064f3b95573e40443e6f7a。`docs/device-space-native-testing.md:40`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：新建身份下，iOS 发起、Mac 配对并批准的完整界面流程成功；iOS 重启后，Mac 观察到连接恢复；未修改配对或加入的业务代码。`docs/device-space-native-testing.md:47`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：原 Mac 身份加入的是已有 Windows 管理员的空间，Mac 自身为普通用户，Windows 管理员在测试开始时离线；此状态与新建空间不同，审批影响尚未确认，原身份失败尚未复现，不能认定它就是根因，也不能宣布原问题修复。`docs/device-space-native-testing.md:50`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：未验收范围包括 Mac 发起的全新配对、二维码、真机网络和本地网络授权、旧配对数据迁移、原身份加入失败、完整文件同步。`docs/device-space-native-testing.md:54`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：此前服务驱动的原生集成测试有配对与加入成功记录，但完整同步测试未通过；新编写的双向传输矩阵未完成执行，已移除未验收的临时测试脚本；这些结果均不替代上述实际界面验证。`docs/device-space-native-testing.md:57`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：用户报告两端均为最新版，发现设备后不出配对码，二维码能解析但确认后无动作，切换 TCP / HTTP / WebSocket 无效。`docs/device-space-native-testing.md:64`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：按用户回忆的英文，该故障与源码中的 `PEER_PROTOCOL_UPGRADE_REQUIRED` 的对应关系尚无错误原文确认；该分支检查消息中的 `protocol` 是否缺失，与 `PEER_PROTOCOL_MISMATCH`（明确收到不同版本号）不同。`docs/device-space-native-testing.md:66`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：不能仅凭该错误断定用户没有升级，用户另一环境的这次故障也尚未复现。`docs/device-space-native-testing.md:68`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：源码中 outbound `Hello`、inbound `HelloReply` 的 transcript 都主动写入当前协议。`docs/device-space-native-testing.md:70`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：新增生产握手的二进制 `Link` 编码回归测试中，双向平台信息都能完成 `hello`/`authorize`，接收端生成配对码；缺少身份字段时按请求、回复分别拒绝并保留具体错误阶段。`docs/device-space-native-testing.md:71`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：上述回归测试证明当前本地编码路径正常，不证明发布安装包或用户实际运行环境一定正常。`docs/device-space-native-testing.md:73`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：缺少身份字段的文案不再直接归因为“请升级固件”；保留严格的协议校验，在错误文案和 `details` 里补上收到请求、收到回复、空间协商阶段及本机协议版本。`docs/device-space-native-testing.md:77`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：网络配对原来没有等待上限，现为探测与建连各 10 秒、单次未加密握手交换 5 秒、整段握手或确认 20 秒；串口原有重试保留。`docs/device-space-native-testing.md:79`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：对不返回的连接，确保有错误返回、关闭已建立的 carrier，且不发布配对凭据。`docs/device-space-native-testing.md:81`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：添加设备窗口在等待时显示“正在连接”，失败时恢复操作，并记录发起方式与错误；被配对码或加入弹窗覆盖时停止背景连接动画。`docs/device-space-native-testing.md:82`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：当时按仓库构建要求追加开发中的协议修订 v14，既有 v1–v13 保持不变；当时构建互测两端一起使用 v14。`docs/device-space-native-testing.md:84`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：原生 pairing 相关 36 项通过（包含实际 TCP / HTTP / WebSocket、二维码、新增 4 项等待上限和 2 项二进制握手测试），协议校验与构建保护 6 项通过。`docs/device-space-native-testing.md:87`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：Flutter 的设备操作、二维码、空间加入共 57 项通过；改动 Dart 文件静态检查通过；macOS debug 与 iOS simulator debug 原生构建均成功；这些自动化测试不替代实际 iOS / Mac 界面测试。`docs/device-space-native-testing.md:89`
- 2026-11-11 v14 实际界面反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）时间为 01:25–01:29（Asia/Shanghai），两端均重新构建并启动，构建生成的 `peer_protocol_identity.rs` 均为 `VERSION = 14`。`docs/device-space-native-testing.md:96`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：Mac 新建并切换身份 Mac-to-iOS-v14，iOS 新建并切换第三个未命名身份。`docs/device-space-native-testing.md:99`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：本次都使用正常应用入口，没有用服务调用替代点击。`docs/device-space-native-testing.md:101`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：Mac 引导选择加入已有空间，在“添加设备”发现 iOS，点击设备；iOS 实际弹出配对码，Mac 出现输入窗口；通过 Mac 窗口输入后点击“完成连接”。`docs/device-space-native-testing.md:102`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：Mac 显示等待批准，iOS 实际弹出“空间加入申请”；点击批准后两端设备空间均显示 2 台设备、2 在线，互相显示在线、直连、空间成员。`docs/device-space-native-testing.md:104`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：只读记录核对为 Mac 出站 joined、iOS 入站 approved，请求 ID 为 6c177a76-eeb4-4f3e-a7c4-c342bbc41322，目标空间为 space-b4c39a05938c4ab8b144cc0fd9fd3d54。`docs/device-space-native-testing.md:107`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：Mac 节点为 core-1794331075185-76d189401d534d7d96995c932c3d98a8，iOS 节点为 core-1794331251116-c83a47baffeb4a6992e195ce55ab7199。`docs/device-space-native-testing.md:110`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：本次没有实际相机扫码验证；二维码路径有原生和 Flutter 自动化验证；v14 新增界面验证是 Mac 发起方向，前述 iOS 发起的界面验证使用 v13。`docs/device-space-native-testing.md:119`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：用户报告的另一处最新版双向缺少协议身份错误仍未复现，不能认定已修复；后续需要发生错误那一轮的完整错误或诊断日志，才能进一步核对实际接收阶段。`docs/device-space-native-testing.md:121`
- 用户提供的 Android 诊断日志（导出于 2026-11-11 01:49:02）写明：日志共 7393 行，客户端运行时路径为 /data/user/0/app.operit/files/runtime，并记录 Android 前台服务及 CPU 锁，因此这份导出来自 Android；不能用前述 iOS 模拟器与 Mac 测试替代这个实际环境。`docs/device-space-native-testing.md:127`
- 用户提供的 Android 诊断日志（导出于 2026-11-11 01:49:02）写明：日志没有给出另一端平台、应用构建号或当前原生协议版本。`docs/device-space-native-testing.md:130`
- 用户提供的 Android 诊断日志（导出于 2026-11-11 01:49:02）写明：与 Peer 有关的日志只有 7 行，包括 23:28:58.911 监听绑定到 0.0.0.0:39267，以及三次发现完成记录（7 条广播记录、1 个最终候选；5 条广播记录、0 个最终候选；8 条广播记录、1 个最终候选），三次均为 0 个已配对节点。`docs/device-space-native-testing.md:132`
- 用户提供的 Android 诊断日志（导出于 2026-11-11 01:49:02）写明：全文没有 `PEER_PROTOCOL`、`protocol identity`、`startPairing`、`finishPairing` 或握手错误原文；发现日志不能证明点击后的握手成功，也不能证明用户未点击。`docs/device-space-native-testing.md:139`
- 用户提供的 Android 诊断日志（导出于 2026-11-11 01:49:02）写明：公告请求超时、模型 401、宠物插件窗口异常没有足够证据与配对故障建立因果关系；此前关于打包或运行实例错配的方向仍为假设，当前未发现打包跳过 Rust 编译的证据。`docs/device-space-native-testing.md:141`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：已确认的日志缺口是配对 UI catch 只显示错误；原生 serve 对校验拒绝调用 sendError，成功发送拒绝后返回 Ok，因此监听循环只记录 serve 返回 Err 的机制不会写出拒绝。`docs/device-space-native-testing.md:144`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：在前述修改基础上进一步加入不含配对码、二维码密钥、公钥或会话密钥的原生诊断：启动时记录平台、节点和编译协议版本；配对开始记录目标与传输类型；接收 hello / reply 时记录实际声明的协议；hello 调用失败、协议拒绝、确认失败都记录具体阶段。`docs/device-space-native-testing.md:147`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：缺字段回归测试改为从二进制消息前的 map 中真正移除字段，验证 serde 默认处理路径；新增日志代码的 pairing 回归 36 项与协议回归 6 项通过。`docs/device-space-native-testing.md:150`
- 2026-11-11 联调记录（代码版本 dc4079ab9）写明：新增日志尚未部署到用户提供日志的 Android 设备；前述 v14 界面测试构建早于此日志补丁。`docs/device-space-native-testing.md:152`
- 2026-11-11 联调记录写明：提交前主分支已推进至 `6b7771c48`，其中已记录协议 v14；为保留已提交的协议记录，本批修改追加 v15，并通过 `tools/check_peer_protocol.py --base HEAD` 校验。`docs/device-space-native-testing.md:157`
- 2026-11-11 联调记录写明：上面的 v13 / v14 界面联调记录对应各自当时的开发构建，不代表当前 v15 已完成两端界面验收；额外原生诊断代码也尚未完成两端界面验收。`docs/device-space-native-testing.md:159`
- 2026-11-11 联调记录写明：本次提交范围为配对等待超时处理、连接中提示、协议错误阶段与诊断日志，以及对应回归测试；用户现场缺少协议身份的根因仍未确认。`docs/device-space-native-testing.md:162`
- 2026-11-11 联调记录（当前 v15 工作区）写明：重新验证中配对回归 36 项、协议回归 6 项、握手响应回归 2 项全部通过；Flutter 设备操作、二维码、空间加入 57 项通过，两个改动 Dart 文件静态检查无问题，`git diff --check` 通过。`docs/device-space-native-testing.md:165`
- 2026-11-11 联调记录（当前 v15 工作区）写明：Rust 首次编译因本地缺少新增内置插件归档而中止，运行仓库 `plugins/tools/sync_plugin_packages.py --source runtime` `--no-hot-reload` 生成忽略的构建资源后，以上 Rust 检查均通过。`docs/device-space-native-testing.md:167`

### 范围边界：未验收项

- 真机上的大文件、弱网、移动端后台恢复还需实际验收；本次自动化结果不等于这些场景已经通过。`docs/device-space-large-sync-progress.md:37`
- 实机、弱网与系统长时间后台挂起未在本轮验收范围内；这里的双端结果为 macOS 与 iOS 模拟器前台联测。`docs/device-space-large-sync-progress.md:93`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：未验收范围包括 Mac 发起的全新配对、二维码、真机网络和本地网络授权、旧配对数据迁移、原身份加入失败、完整文件同步。`docs/device-space-native-testing.md:54`
- 2026-11-11 iOS/macOS 模拟器联调（dc4079ab9、Core 2.0.0-preview.31、协议 v13）写明：此前服务驱动的原生集成测试有配对与加入成功记录，但完整同步测试未通过；新编写的双向传输矩阵未完成执行，已移除未验收的临时测试脚本；这些结果均不替代上述实际界面验证。`docs/device-space-native-testing.md:57`
- 2026-11-11 v14 反向联调（Mac 发起 → iOS 接收，iOS 27.0 模拟器）写明：用户报告的另一处最新版双向缺少协议身份错误仍未复现，不能认定已修复；后续需要发生错误那一轮的完整错误或诊断日志，才能进一步核对实际接收阶段。`docs/device-space-native-testing.md:121`
- 2026-11-11 联调记录写明：上面的 v13 / v14 界面联调记录对应各自当时的开发构建，不代表当前 v15 已完成两端界面验收；额外原生诊断代码也尚未完成两端界面验收。`docs/device-space-native-testing.md:159`
- 2026-11-11 联调记录写明：本次提交范围为配对等待超时处理、连接中提示、协议错误阶段与诊断日志，以及对应回归测试；用户现场缺少协议身份的根因仍未确认。`docs/device-space-native-testing.md:162`

## 关键符号

- `SpaceSyncStatus` — `Syncing`、`Waiting`、`Completed` 三种状态。`core/crates/node/runtime/src/SpaceSyncProgress.rs:8`
- `SpaceSyncStage` — `Checking`、`Records`、`Files` 三个阶段。`core/crates/node/runtime/src/SpaceSyncProgress.rs:15`
- `SpaceSyncProgress` — 一次同步任务的本地执行进度。`core/crates/node/runtime/src/SpaceSyncProgress.rs:26`
- 进度结构另含 `transferredBytes`、`fileBytes`、`fileSize`、`retryAt`、`error` 字段。`core/crates/node/runtime/src/SpaceSyncProgress.rs:38`
- `LARGE_SYNC_DELAY_MS` / `LARGE_SYNC_RECORDS` / `LARGE_SYNC_BYTES` — 3000 毫秒 / 256 条 / 1024×1024 字节。`core/crates/node/runtime/src/SpaceSyncProgress.rs:44`
- `hasSubstantialWork` — 判断会话是否已有实质工作量。`core/crates/node/runtime/src/SpaceSyncProgress.rs:49`
- `SyncProgressSession` — 一次会话的进度、可见标志与待处理/错误账本。`core/crates/node/runtime/src/SpaceSyncProgress.rs:58`
- `SyncProgressTracker` — 以 `StateFlow` 持有会话列表。`core/crates/node/runtime/src/SpaceSyncProgress.rs:66`
- SyncProgressTracker 的 `peer` — 只返回已可见的会话进度。`core/crates/node/runtime/src/SpaceSyncProgress.rs:80`
- SyncProgressTracker 的 `flow` — 只返回可见会话进度。`core/crates/node/runtime/src/SpaceSyncProgress.rs:86`
- SyncProgressTracker 的 `retain` — 只保留指定空间与成员的会话。`core/crates/node/runtime/src/SpaceSyncProgress.rs:107`
- SyncProgressTracker 的 `mirror` — 镜像协调方进度，保留原 `startedAt`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:124`
- SyncProgressTracker 的 `begin` — 新建或复用会话。`core/crates/node/runtime/src/SpaceSyncProgress.rs:137`
- SyncProgressTracker 的 `revealDelayMs` — 返回隐藏会话的剩余揭示延迟毫秒数。`core/crates/node/runtime/src/SpaceSyncProgress.rs:184`
- SyncProgressTracker 的 `reveal` — 仅在已有实质工作量时把会话置为可见。`core/crates/node/runtime/src/SpaceSyncProgress.rs:199`
- SyncProgressTracker 的 `backlog` — 从实际导出清单刷新总量。`core/crates/node/runtime/src/SpaceSyncProgress.rs:231`
- SyncProgressTracker 的 `report` — 按端记录未应用标识与错误。`core/crates/node/runtime/src/SpaceSyncProgress.rs:240`
- SyncProgressTracker 的 `confirmRecords` — 只在两端都不再报未应用后才计入已完成。`core/crates/node/runtime/src/SpaceSyncProgress.rs:261`
- SyncProgressTracker 的 `records` — 阶段切到 `Records` 并累加交换记录。`core/crates/node/runtime/src/SpaceSyncProgress.rs:270`
- SyncProgressTracker 的 `beginFile` — 阶段切到 `Files` 并记录当前文件大小。`core/crates/node/runtime/src/SpaceSyncProgress.rs:280`
- SyncProgressTracker 的 `fileOffset` — 节流发布文件偏移并累加传输字节。`core/crates/node/runtime/src/SpaceSyncProgress.rs:291`
- 结束时按 `pending`、`error`、`pendingRecords` 决定 `Waiting` 或 `Completed`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:314`
- `space_join::refresh` — 校验审批结果并导入成员、身份和拓扑，发布 `Joined`。`docs/device-space-large-sync-progress.md:5`
- RuntimeRemoteLinkService 的 `afterJoined` — 只调度后台同步（`scheduleSynchronization("space_joined")`），不等待业务同步。`core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1389`
- `synchronizeOnce` — 先交换空间投影，再通过 change gate 做权限交换、设备偏好交换、版本检查和业务同步。`docs/device-space-large-sync-progress.md:7`
- `synchronizeDomains` — 比较 `receipt`，合并双向差异，按操作数和传输字节分页。`docs/device-space-large-sync-progress.md:8`
- `deviceSpaceSnapshotFlow` — 只有成员和拓扑，没有同步执行信息。`docs/device-space-large-sync-progress.md:10`
- `RuntimeActivityOverlay` — 根部统一订阅大同步状态。`docs/device-space-large-sync-progress.md:66`
- `OperitTheme` — 根部保留一个 `RuntimeActivityOverlay`。`docs/device-space-large-sync-progress.md:66`
- `PluginLoadingOverlay` — 与设置页同步卡片、同步订阅一起移除。`docs/device-space-large-sync-progress.md:67`
- `SpaceSyncProgressCard` — 设置页的同步卡片，与 `PluginLoadingOverlay` 一起移除。`docs/device-space-large-sync-progress.md:67`
- `LocalCoreProxy` — 通过共享 `Weak` 缓存复用仍存活的应用客户端。`docs/device-space-large-sync-progress.md:78`
- `localApplicationSharedClient()` — 每次创建新的 `Arc`，导致同步服务注册表无法把后台 worker 与进度订阅识别为同一应用。`docs/device-space-large-sync-progress.md:76`

## 调用链

1. 加入：`space_join::refresh` 校验审批结果并导入成员、身份和拓扑，发布 `Joined`。`docs/device-space-large-sync-progress.md:5`
2. 加入后：RuntimeRemoteLinkService 的 `afterJoined` 只调度后台同步（`scheduleSynchronization("space_joined")`），不等待业务数据同步。`core/crates/node/runtime/src/RuntimeRemoteLinkService.rs:1389`
3. 加入完成只唤醒原有后台调度，不等待业务数据全部同步后才向界面返回。`docs/device-space-large-sync-progress.md:16`
4. 常驻同步由持久化变更、连接变化、每两秒的文件扫描唤醒。`docs/device-space-large-sync-progress.md:6`
5. 常驻服务 `synchronizeOnce` 先交换空间投影，再通过 change gate 对可达成员执行权限交换、设备偏好交换、版本检查和业务同步；业务同步要求两端都有存储权限。`docs/device-space-large-sync-progress.md:7`
6. `synchronizeDomains` 比较 `receipt`，合并双向差异，按操作数和传输字节分页；先补齐引用文件，再向两端提交操作。`docs/device-space-large-sync-progress.md:8`
7. 文件按 64 KiB 分块，关闭传输后再次检查文件是否落盘。`docs/device-space-large-sync-progress.md:8`
8. 每轮最多 64 页；接收成功不等于业务应用成功，`receipt` 中的 `pending`、`errors` 和缺失文件留给后续轮次。`docs/device-space-large-sync-progress.md:9`
9. 进度产生：新建会话时 `visible` 为 `false`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:159`
10. 新建会话的状态为 `Syncing`、阶段为 `Checking`，`exchangedRecords`、`completedRecords`、`pendingRecords` 归零，`totalRecords` 为 `None`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:168`
11. `records` 把阶段切到 `Records`，`exchangedRecords` 累加传入条数。`core/crates/node/runtime/src/SpaceSyncProgress.rs:270`
12. `beginFile` 把阶段切到 `Files`，`fileBytes` 清零，`fileSize` 记为传入大小。`core/crates/node/runtime/src/SpaceSyncProgress.rs:280`
13. `fileOffset` 每秒最多发布 5 次文件偏移更新（200 毫秒节流），但始终发布最终偏移。`core/crates/node/runtime/src/SpaceSyncProgress.rs:291`
14. `fileOffset` 把偏移夹在 `fileBytes` 与 `fileSize` 之间，`transferredBytes` 累加偏移增量，重传计入传输量。`core/crates/node/runtime/src/SpaceSyncProgress.rs:294`
15. `report` 按端（`side`）记录未应用标识与错误。`core/crates/node/runtime/src/SpaceSyncProgress.rs:240`
16. `pendingRecords` 取各端待处理标识集合的并集大小；错误非空时会话置为可见。`core/crates/node/runtime/src/SpaceSyncProgress.rs:247`
17. `confirmRecords` 只在两端都不再把某条原始记录报为未应用后才计入 `completedRecords`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:261`
18. `backlog` 从实际导出清单刷新总量。`core/crates/node/runtime/src/SpaceSyncProgress.rs:231`
19. 可见性门禁：仅在会话已有实质工作量（`hasSubstantialWork`）且已满 3 秒、或出现 `error` 时，会话变为可见。`core/crates/node/runtime/src/SpaceSyncProgress.rs:224`
20. 结束时，在 `pending` 为真、有 `error` 或 `pendingRecords` 大于 0 时状态置为 `Waiting`，否则置为 `Completed`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:314`
21. 结束时状态为 `Completed` 的会话清除 `error`，并把 `totalRecords` 置为 `completedRecords`。`core/crates/node/runtime/src/SpaceSyncProgress.rs:321`
22. 快速成功的不可见已完成会话在结束后从会话列表中移除，不产生可观察的生命周期。`core/crates/node/runtime/src/SpaceSyncProgress.rs:329`
23. 界面：根部 `RuntimeActivityOverlay` 统一订阅，页面切换不影响任务展示；进度显示后跨轮次保留，完成后保留 3 秒收起。`docs/device-space-large-sync-progress.md:20`
24. 联调验证：协调器启动命令为 `python3 apps/flutter/app/integration_test/device_space_sync_coordinator.py` `--output docs/assets/sync-progress-2026-10-25`。`docs/device-space-large-sync-progress.md:49`
25. 联调验证：两端分别运行 `fvm flutter test integration_test/device_space_sync_native_test.dart -d macos --reporter expanded` 与同一命令的 -d iOS 模拟器 UDID 变体。`docs/device-space-large-sync-progress.md:56`

## 来源

- `core/crates/node/runtime/src/SpaceSyncProgress.rs`
- `docs/device-space-large-sync-progress.md`
- `docs/device-space-native-testing.md`
- 本页的否定性表述均为 seed 文档自身的记录转述：docs/device-space-native-testing.md（2026-11-11 联调记录）与 docs/device-space-large-sync-progress.md（2026-10-25 验证记录），基线均为 364d1d594。
- Android 诊断日志全文无 `PEER_PROTOCOL`、`protocol identity`、`startPairing`、`finishPairing` 或握手错误原文。`docs/device-space-native-testing.md:139`
- 此前服务驱动的原生集成测试有配对与加入成功记录，但完整同步测试未通过。`docs/device-space-native-testing.md:57`
- 用户报告的另一处最新版双向缺少协议身份错误仍未复现，不能认定已修复。`docs/device-space-native-testing.md:121`
- 用户现场缺少协议身份的根因仍未确认。`docs/device-space-native-testing.md:162`
- 2026-10-25 验证：设备空间行为回归 97 项中 95 项通过、2 项失败。`docs/device-space-large-sync-progress.md:32`
- 两项失败在隔离的 `6c1fa579` 源码副本上复现，确认不由本次同步修改引入。`docs/device-space-large-sync-progress.md:33`
- 本次写作未对 seed 全仓做 grep 复核；如补做，须写明命令与范围，例如 `grep -rn "PEER_PROTOCOL" --include=*.rs core/`。
- 用户提供的 Android 诊断日志原文不在 seed 仓库内，无法在基线 364d1d594 上复核。
- 范围说明：联调记录文件本身在 wiki 基线内，但其记录的联调针对代码版本 `dc4079ab9`、Core `2.0.0-preview.31`、协议 v13/v14，与 wiki 基线 364d1d594 不是同一版本。`docs/device-space-native-testing.md:4`
