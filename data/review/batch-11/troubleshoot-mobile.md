---
title: 排障·移动端（Android / iOS）
module: dev
platforms: [android, ios]
sources: 3
date: 2026-11-11
---

## 概述

- 本页只覆盖 Android root shell、iOS 性能定位、TestFlight 反馈排查三份 seed 文档记载的内容，seed 文件是 `docs/android-root-shell.md`、docs/performance-ios-2026-10-27.md、docs/testflight-feedback-investigation-2026-11-09.md。`docs/android-root-shell.md:1`
- 本页的断言全部来自文档记载，文档说法与实现事实分开表述，文档中标注“未关闭”“未宣称”的结论在本页同样保留为未关闭、未宣称。`docs/testflight-feedback-investigation-2026-11-09.md:5`
- Android 侧的细节见 [[host-android|Android Host]]，iOS 侧的细节见 [[host-ios|iOS Host 与 ARM64 Linux 运行时]]，桌面端排障见 [[troubleshoot-desktop|排障·桌面端（Windows / macOS / Linux）]]。`docs/android-root-shell.md:1`

## AI 速览

- `AndroidRootCommandRouter` — 自动/强制模式、自定义 su argv、设备 Root 迹象与实际授权区分、身份探测、执行路由。`docs/android-root-shell.md:5`
- `AndroidRootShell` — 管理私有 libsu Shell，启用 mount-master，初始化上限 10 秒，每条 libsu 命令有独立 deadline。`docs/android-root-shell.md:7`
- `AndroidCommandProcessRunner` — 直接 exec 和 Shizuku 共用的 stdout/stderr 并发读取、超时、关闭 stdin、清理进程和输出流。`docs/android-root-shell.md:9`
- `AndroidPrivilegeAuthorization` — 显式用户同意加当前 UID 验证，不把持久化 `true` 当作永久授权。`docs/android-root-shell.md:12`
- `RootAuto` — Android 授权检查和截图默认使用的自动模式，遵循同一套设置。`docs/android-root-shell.md:15`
- `hostOnboardingRequestPermission` — 对 `android.root` 新增两个可选字段的 MethodChannel。`docs/android-root-shell.md:26`
- `execute_privileged_command` — Owner 特权命令入口，支持 `root` / `root_auto`，同时保留 `root_libsu` / `root_exec` / `shizuku`。`docs/android-root-shell.md:44`
- `hosts/android/src/terminal.rs` — Super Admin 非 Linux/proot 终端的 Rust 路由点，按 Root → Shizuku → 普通 sh 选择身份。`docs/android-root-shell.md:53`
- `notify_waiters` — iOS 工具链中出现在日期工具压力测试 12.55%、设备状态工具压力测试 17.56% 原生运行样本中的广播通知。`docs/performance-ios-2026-10-27.md:45`
- `PipelineOwner.flushLayout` — 流式阶段 Dart 样本占比 28.40% 的布局入口。`docs/performance-ios-2026-10-27.md:75`
- `ChatArea` — 流式高度变化、逐帧底部跟随的界面组件，`_beginBottomFollowCompletion → _tickBottomFollow → jumpTo` 路径允许回复完成后继续逐帧追赶底部。`docs/performance-ios-2026-10-27.md:97`
- `installMarketArtifact` — 市场认证安装链路的入口，文件入口及字节入口均走该链路。`docs/testflight-feedback-investigation-2026-11-09.md:102`
- `themePrivateFontMaxBytes` — 私有字体上限，256 MiB，同时用于本地导入和保存后重新加载。`docs/testflight-feedback-investigation-2026-11-09.md:84`
- `RuntimeStorageRepository.writeBytesStream` — 至多 1 MiB 二进制块的分块写入入口。`docs/testflight-feedback-investigation-2026-11-09.md:85`
- 主入口：Android 特权命令走 `execute_privileged_command`。`docs/android-root-shell.md:44`
- 数据流向：Android 上用户命令 → 身份探测 → Root / Shizuku / 普通 sh 传输执行。`docs/android-root-shell.md:53`
- 数据流向：iOS 上工具调用 → `watch` 广播调度 → 界面布局排版渲染。`docs/performance-ios-2026-10-27.md:40`

## 核心机制

### Android root shell：能力边界

- 文档记载，`AndroidRootCommandRouter` 负责自动/强制模式、自定义 su argv、设备 Root 迹象与实际授权区分、身份探测、执行路由。`docs/android-root-shell.md:5`
- 文档记载，`AndroidRootShell` 管理私有 libsu Shell，启用 mount-master，初始化上限 10 秒。`docs/android-root-shell.md:7`
- 文档记载，`AndroidRootShell` 的每条 libsu 命令有独立 deadline，失败/超时后关闭失效 Shell，非 Root Shell 不缓存。`docs/android-root-shell.md:7`
- 文档记载，`AndroidCommandProcessRunner` 为直接 exec 和 Shizuku 共用 stdout/stderr 并发读取、超时、关闭 stdin、清理进程和输出流。`docs/android-root-shell.md:9`
- 文档记载，直接 exec / Shizuku 保留原始字节输出，libsu 使用按行文本收集 API。`docs/android-root-shell.md:10`
- 文档记载，Android 的授权检查和截图默认使用 `RootAuto`，遵循同一套设置。`docs/android-root-shell.md:15`
- 文档记载，自动选择优先复查最近成功的传输，首次探测遇到 KernelSU / APatch 的版本标识优先直接 exec，否则优先 libsu。`docs/android-root-shell.md:16`
- 文档记载，失败时只在身份探测阶段尝试另一种执行方式。`docs/android-root-shell.md:17`
- 文档记载，`MethodChannel` 的 `hostOnboardingRequestPermission` 对 `android.root` 新增两个可选字段。`docs/android-root-shell.md:26`
- 文档记载，现有 Flutter 调用不传字段时沿用已保存设置，首次默认为自动模式。`docs/android-root-shell.md:27`
- 文档记载，`rootExecutionMode` 取值 auto / libsu / exec，`suCommand` 接受自定义 su 命令。`docs/android-root-shell.md:33`
- 文档记载，强制模式不会自动切换到另一种执行方式。`docs/android-root-shell.md:41`
- 文档记载，默认 `su` 在 PATH 不可执行时还会尝试存在的常见 su 绝对路径。`docs/android-root-shell.md:42`
- 文档记载，Owner `execute_privileged_command` 支持 `root` / `root_auto`，同时保留 `root_libsu` / `root_exec` / `shizuku`。`docs/android-root-shell.md:44`
- 文档记载，显式的 `root_libsu` 和 `root_exec` 保持指定传输，不会自动切换。`docs/android-root-shell.md:45`
- 文档记载，`RootAuto` 单条命令的传输探测与实际执行共用调用者传入的超时预算。`docs/android-root-shell.md:49`

### Android root shell：风险与防护

- 文档记载，版本输出、su 文件存在仅是 Root 迹象，实际授权必须满足 `id -u` 退出码为 0，且输出恰好为 `0`。`docs/android-root-shell.md:18`
- 文档记载，`AndroidPrivilegeAuthorization` 要求显式用户同意加当前 UID 验证，不把持久化 `true` 当作永久授权。`docs/android-root-shell.md:12`
- 文档记载，未同意时状态查询不调用 `su`，以免打开界面就触发授权弹窗。`docs/android-root-shell.md:13`
- 文档记载，授权成功或拒绝不会永久缓存，撤销权限后下次状态查询重新验证，拒绝后能重试。`docs/android-root-shell.md:20`
- 文档记载，直接 exec 的用户命令在同一 su 进程内再次检查 UID，不允许降级成普通用户执行。`docs/android-root-shell.md:21`
- 文档记载，用户命令启动后不会换传输重试，避免有副作用的命令执行两次。`docs/android-root-shell.md:22`
- 文档记载，自定义 su 按参数列表解析，支持带空格的路径、引号、转义，不会作为 shell 表达式执行。`docs/android-root-shell.md:39`
- 文档记载，修改模式或命令会清除旧的用户同意标志，必须通过本次授权探测确认新配置。`docs/android-root-shell.md:40`
- 文档记载，授权请求总预算为 30 秒，已同意后的状态复查总预算为 10 秒，并放到后台线程。`docs/android-root-shell.md:48`
- 文档记载，终端创建不会主动发起新的授权申请，身份在会话创建时确定，后续命令不重新路由。`docs/android-root-shell.md:64`
- 文档记载，Flutter 模式选择/自定义命令的设置界面尚未新增，原生配置入口已提供。`docs/android-root-shell.md:38`

### Android 系统终端：三身份路由

- 文档记载，Super Admin 的非 Linux/proot 终端走 `hosts/android/src/terminal.rs`，在创建系统 shell 会话时由 Rust 按 Root → Shizuku → 普通 sh 选择身份。`docs/android-root-shell.md:53`
- 文档记载，Root 身份在已有用户同意后重新用 `id -u` 验证直接 su argv，再通过该 argv 启动持久 PTY。`docs/android-root-shell.md:57`
- 文档记载，Shizuku 身份在 Root 当前不可用且已有 Shizuku 授权时绑定专用 UserService。`docs/android-root-shell.md:60`
- 文档记载，普通 sh 身份在两项授权均不可用时以应用自身 UID 启动 `/system/bin/sh`。`docs/android-root-shell.md:62`
- 文档记载，Shizuku 的默认工作目录从应用私有目录调整为 `/sdcard`，不携带应用私有动态库路径。`docs/android-root-shell.md:67`
- 文档记载，没有 Kotlin 编译器时 Python 测试显式报告 skipped，不将其视为行为验证通过。`docs/android-root-shell.md:91`
- 文档记载，Magisk / KernelSU / APatch 真机验证仍需进行，JVM 测试不能替代设备级兼容性验证。`docs/android-root-shell.md:95`

### iOS 性能定位：采样方法与实测数

- 文档记载，iOS 性能采样对象是 iPhone 18 Pro Max / iOS 27 模拟器，进程 PID 31239，沿用 `lib/main.dart` 与 `deepseek-flash` 配置。`docs/performance-ios-2026-10-27.md:5`
- 文档记载，iOS 性能采样通过 Flutter VM 的 WebSocket 调试接口触发业务，同步使用 Instruments Time Profiler 抓取原生线程。`docs/performance-ios-2026-10-27.md:5`
- 文档记载，日期工具连续 200 次平均 CPU 为 150.9%，100 毫秒峰值为 198.0%。`docs/performance-ios-2026-10-27.md:20`
- 文档记载，设备状态工具连续 200 次平均 CPU 为 196.1%，100 毫秒峰值为 245.5%。`docs/performance-ios-2026-10-27.md:21`
- 文档记载，实际消息流式接收、渲染平均 CPU 为 46.8%，100 毫秒峰值为 235.1%。`docs/performance-ios-2026-10-27.md:22`
- 文档记载，回复完成后的 3 秒平均 CPU 为 39.9%，100 毫秒峰值为 146.8%。`docs/performance-ios-2026-10-27.md:23`
- 文档声明，连续 200 次是明确标注的压力测试，不等于用户点一次工具的持续负载。`docs/performance-ios-2026-10-27.md:25`
- 文档声明，当前是 Apple M5 上的 iOS 模拟器、Flutter debug 模式并附加采样，没有读取到物理 iPhone 的温度、瓦数或降频记录，不能据此给出手机温度或声称真机发热已解决。`docs/performance-ios-2026-10-27.md:105`

### iOS 性能定位：两类真实 CPU 工作

- 文档记载，iOS 工具调用原生栈包含 `JsEngine::scriptRequestStepTask`、`NativeHostJavaScriptRuntime::callHostJavaScriptFunction`、V8 `host_callback`。`docs/performance-ios-2026-10-27.md:35`
- 文档记载，该调用链经 `NativeHostRuntimeTaskSchedulerHost::scheduleHostRuntimeBlockingAsyncTask` 与 `RuntimeTaskQueue::sendMany` 到达 `tokio::sync::watch` / `BigNotify::notify_waiters`。`docs/performance-ios-2026-10-27.md:40`
- 文档记载，`notify_waiters` 出现在日期工具压力测试 12.55%、设备状态工具压力测试 17.56% 的原生运行样本中，该比例包含通知子调用，不等于函数本体的 self CPU。`docs/performance-ios-2026-10-27.md:45`
- 文档记载，共享任务队列采用 `watch` 广播，入队、任务开始 poll、结束 poll、销毁及分派后都会发送变化，普通 runtime 池有 16 个 worker。`docs/performance-ios-2026-10-27.md:47`
- 文档指出，优先优化目标是按可运行任务和接收者定向通知、取消空队列状态广播。`docs/performance-ios-2026-10-27.md:47`
- 文档记载，不能简单替换为 `notify_one`，现有队列会选择特定的低负载 worker，替换时需要同时处理接收者选择、队列交接和关闭语义。`docs/performance-ios-2026-10-27.md:49`
- 文档记载，`ToolPackage` 克隆也是成本之一，日期阶段带克隆函数的样本占 21.18%，设备状态阶段为 11.94%。`docs/performance-ios-2026-10-27.md:51`
- 文档记载，流式阶段原生采样中主线程占 52.6%，raster 线程占 10.1%。`docs/performance-ios-2026-10-27.md:57`
- 文档记载，Dart 侧流式调用链经 `SchedulerBinding.handleDrawFrame`、`PipelineOwner.flushLayout`、`RenderChatMessageSliverList.performLayout`，直至 `TextPainter.layout` 与 `_NativeParagraph.layout`。`docs/performance-ios-2026-10-27.md:66`
- 文档记载，`PipelineOwner.flushLayout` 占流式阶段 Dart 样本的 28.40%。`docs/performance-ios-2026-10-27.md:75`
- 文档记载，`RenderChatMessageSliverList.performLayout` 占流式阶段 Dart 样本的 24.46%，`RenderChatMessageExtentBox.performLayout` 占 23.65%。`docs/performance-ios-2026-10-27.md:76`
- 文档声明，Dart 样本占比的分母是 Dart 采样集合，与原生线程占比、进程 CPU 百分比不同，表中父子调用高度重叠，不能相加。`docs/performance-ios-2026-10-27.md:85`
- 文档记载，回复完成后 3 秒 Dart 样本中 `flushSemantics` 占 38.52%，`flushLayout` 占 8.15%。`docs/performance-ios-2026-10-27.md:95`
- 文档记载，`ChatArea` 的 `_beginBottomFollowCompletion → _tickBottomFollow → jumpTo` 路径允许回复完成后继续逐帧追赶底部，误差修正系数是 0.8/秒，停止阈值是 1 像素。`docs/performance-ios-2026-10-27.md:97`
- 文档声明，没有做关闭自动跟随的对照试验，因此不把全部完成后 CPU 归因于该 ticker，也不宣称发生永久空转。`docs/performance-ios-2026-10-27.md:99`
- 文档记载，iOS 性能复现产物由 `tools/benchmarks/ios_cpu_flamegraph.py` 生成，只依赖 Python 标准库。`docs/performance-ios-2026-10-27.md:112`

### TestFlight 反馈：验收口径与规模

- 文档记载，TestFlight 验收口径是用户明确要求“测试通过的我们也不管了”，已修复且对应场景测试通过的项目按本地验证结果收尾，本地通过不表述为实际真机运行通过，也不代表已发布。`docs/testflight-feedback-investigation-2026-11-09.md:5`
- 文档记载，审计覆盖全部 162 条普通反馈的 ID、平台、build、原文、截图数量及原清单关联。`docs/testflight-feedback-investigation-2026-11-09.md:28`
- 文档记载，App Store Connect 缓存中有 145 条 iOS 崩溃记录、160 条 iOS 和 2 条 macOS 普通反馈，原 22 类清单只关联了 66 条普通反馈。`docs/testflight-feedback-investigation-2026-11-09.md:51`
- 文档记载，原始反馈含个人信息，保存在忽略目录 `tools/release/work/testflight-feedback-unresolved-20261109/`，不提交。`docs/testflight-feedback-investigation-2026-11-09.md:51`
- 文档声明，不存在“build 34/35 的所有反馈更新即可解决”的证据。`docs/testflight-feedback-investigation-2026-11-09.md:119`

### TestFlight 反馈：已复现并修复的典型问题

- 文档记载，重新生成内容串用已复现并修复，历史刷新仅按时间戳保留流，会把旧回复正文覆盖到新保存/新选中的版本。`docs/testflight-feedback-investigation-2026-11-09.md:17`
- 文档记载，聊天 400 / `messages[].name` 已修复，移除工具结果顶层 name，保留 function name 和 tool_call_id，完整请求回归与 provider 套件通过，216 项通过前可复现。`docs/testflight-feedback-investigation-2026-11-09.md:57`
- 文档记载，记忆重建的 `WebAssembly is not defined` 引擎缺失问题按当前口径已收尾，两次独立模拟器进程、每次两个引擎实例均通过，每实例 462 个断言，没有连接到 iOS 真机，因此不宣称真机运行通过。`docs/testflight-feedback-investigation-2026-11-09.md:7`
- 文档记载，iOS WASM 引擎修复在 iOS 27.0 ARM64 模拟器执行 462 个断言，两次独立进程、每次两次创建/销毁引擎实例均通过。`docs/testflight-feedback-investigation-2026-11-09.md:96`
- 文档记载，V8 DrumBrake 打开 WebAssembly，保留关闭 JIT 编译器、指针压缩、sandbox 和 cppgc cage，显式检查每次内存访问边界。`docs/testflight-feedback-investigation-2026-11-09.md:95`
- 文档记载，大字体缺陷已修复，本地字体由 32 MiB 扩至 256 MiB。`docs/testflight-feedback-investigation-2026-11-09.md:61`
- 文档记载，`themePrivateFontMaxBytes` 为 256 MiB，同时用于本地导入和保存后重新加载。`docs/testflight-feedback-investigation-2026-11-09.md:84`
- 文档记载，`RuntimeStorageRepository.writeBytesStream` 接收至多 1 MiB 的二进制块，`readBase64Chunk` 每次读取至多 1 MiB，分块传输避开桌面本地传输的 64 MiB 单帧限制。`docs/testflight-feedback-investigation-2026-11-09.md:85`
- 文档记载，`installMarketArtifact` 的文件入口及字节入口均使用市场认证安装链路，修正首次下载被存成 EXTERNAL、后续按名称冲突拒绝的问题。`docs/testflight-feedback-investigation-2026-11-09.md:102`
- 文档记载，电量信息注入已修复插件空实现，接入真实设备信息，iOS/macOS 电量来源与未知电量处理已修改，Linux/Windows/Web 未知值统一为 unavailable。`docs/testflight-feedback-investigation-2026-11-09.md:78`

### TestFlight 反馈：未关闭的典型问题

- 文档记载，同一反馈里的“AI 漏字、逻辑不通”未关闭，正文串用能解释版本显示错乱，不能据此确认所有漏字原因。`docs/testflight-feedback-investigation-2026-11-09.md:18`
- 文档记载，思考内容外露未关闭，需要核对原图及当时返回格式。`docs/testflight-feedback-investigation-2026-11-09.md:19`
- 文档记载，重新生成后删不了第一个的 Core 删除与重新编号回归通过，原反馈设备上的按钮操作尚未验收。`docs/testflight-feedback-investigation-2026-11-09.md:20`
- 文档记载，工具慢、搜索中断、发热已回归工具截止时间及结构化流，供应商延迟与设备发热缺少可重复测量，未关闭。`docs/testflight-feedback-investigation-2026-11-09.md:62`
- 文档记载，本轮执行聊天界面/流中断 53 项通过，头像、附件、外观预览、聊天滚动四个测试文件 84 项通过、2 项失败。`docs/testflight-feedback-investigation-2026-11-09.md:22`
- 文档记载，84 项中的 2 项失败是实时聊天切换后的帧回调未结束、最终工具块未显示，保留失败，不能宣称聊天整套回归通过。`docs/testflight-feedback-investigation-2026-11-09.md:22`
- 文档记载，Edge 显示投影测试 3 通过、2 失败，失败断言要求未闭合工具标记必须报错，而当前共享解析器明确支持中断时补全。`docs/testflight-feedback-investigation-2026-11-09.md:24`
- 文档记载，未关联旧清单的文字反馈中仍需单独跟进的问题包括 macOS 首次启动 Plugin SDK IPC EPERM、切换模型 Provider logo OTHER 报错、群组回复身份错误。`docs/testflight-feedback-investigation-2026-11-09.md:35`
- 文档记载，截至本次刷新最新收到的是 11 月 9 日北京时间 21:26 的 build 34 崩溃（iPhone X / iOS 16.7.14），最新四份崩溃的 crashLog 接口均返回 404，没有可用于定位的新堆栈。`docs/testflight-feedback-investigation-2026-11-09.md:111`

### 移动端 Host 能力与桌面端的区别

- 文档记载，Android 的 Super Admin 系统终端由 Rust 按 Root → Shizuku → 普通 sh 选择身份。`docs/android-root-shell.md:53`
- 文档记载，iOS 的 WebAssembly 走 V8 DrumBrake，保留关闭 JIT 编译器、指针压缩、sandbox 和 cppgc cage，显式检查每次内存访问边界。`docs/testflight-feedback-investigation-2026-11-09.md:95`
- 文档记载，电量信息注入在 iOS/macOS 有真实电量来源，Linux/Windows/Web 未知值统一为 unavailable，电量能力按平台区分。`docs/testflight-feedback-investigation-2026-11-09.md:78`
- 文档记载，分块传输避开的是桌面本地传输的 64 MiB 单帧限制，该限制在文档中按桌面本地传输表述。`docs/testflight-feedback-investigation-2026-11-09.md:85`
- 完整的移动端与桌面端能力对照见 [[app-host-capability-matrix|能力 × 平台矩阵]]，本页只写三份 seed 中出现的平台差异点。`docs/testflight-feedback-investigation-2026-11-09.md:85`

## 关键符号

- `AndroidRootCommandRouter` — 自动/强制模式、自定义 su argv、设备 Root 迹象与实际授权区分、身份探测、执行路由。`docs/android-root-shell.md:5`
- `AndroidRootShell` — 管理私有 libsu Shell，启用 mount-master，初始化上限 10 秒，每条 libsu 命令有独立 deadline。`docs/android-root-shell.md:7`
- `AndroidCommandProcessRunner` — 直接 exec 和 Shizuku 共用的 stdout/stderr 并发读取、超时、关闭 stdin、清理进程和输出流。`docs/android-root-shell.md:9`
- `AndroidPrivilegeAuthorization` — 显式用户同意加当前 UID 验证，不把持久化 `true` 当作永久授权。`docs/android-root-shell.md:12`
- `RootAuto` — Android 授权检查和截图默认使用的自动模式。`docs/android-root-shell.md:15`
- `hostOnboardingRequestPermission` — 对 `android.root` 新增两个可选字段的 MethodChannel。`docs/android-root-shell.md:26`
- `rootExecutionMode` — 取值 auto / libsu / exec 的 Root 执行模式字段。`docs/android-root-shell.md:33`
- `suCommand` — 接受自定义 su 命令的字段。`docs/android-root-shell.md:33`
- `execute_privileged_command` — Owner 特权命令入口，支持 `root` / `root_auto`，同时保留 `root_libsu` / `root_exec` / `shizuku`。`docs/android-root-shell.md:44`
- `hosts/android/src/terminal.rs` — Super Admin 非 Linux/proot 终端的 Rust 路由点。`docs/android-root-shell.md:53`
- `id -u` — 实际授权的验证命令，退出码为 0 且输出恰好为 `0` 才算授权。`docs/android-root-shell.md:18`
- `notify_waiters` — 工具链调度广播的通知点，出现在日期工具压力测试 12.55%、设备状态工具压力测试 17.56% 的原生运行样本中。`docs/performance-ios-2026-10-27.md:45`
- `RuntimeTaskQueue::sendMany` — 工具调用链中向 `watch` 广播发送任务的环节。`docs/performance-ios-2026-10-27.md:40`
- `PipelineOwner.flushLayout` — 流式阶段 Dart 样本占比 28.40% 的布局入口。`docs/performance-ios-2026-10-27.md:75`
- `RenderChatMessageSliverList.performLayout` — 流式阶段 Dart 样本占比 24.46% 的消息列表布局。`docs/performance-ios-2026-10-27.md:76`
- `ChatArea` — 流式高度变化、逐帧底部跟随的界面组件。`docs/performance-ios-2026-10-27.md:97`
- `FfiCoreTransport.dart` — 消息桥接接收，当前采样占比低于布局链。`docs/performance-ios-2026-10-27.md:91`
- `installMarketArtifact` — 市场认证安装链路的入口。`docs/testflight-feedback-investigation-2026-11-09.md:102`
- `themePrivateFontMaxBytes` — 私有字体上限 256 MiB。`docs/testflight-feedback-investigation-2026-11-09.md:84`
- `RuntimeStorageRepository.writeBytesStream` — 至多 1 MiB 二进制块的分块写入入口。`docs/testflight-feedback-investigation-2026-11-09.md:85`
- `ThemeFontRegistry.registerBytes` — 私有字体读取成功后曾被 32 MiB 公共主题包预算拒绝的注册点。`docs/testflight-feedback-investigation-2026-11-09.md:82`
- `NativeHostJavaScriptRuntimeHost` — iOS WASM 验收中使用的真实 JS 运行时 Host。`docs/testflight-feedback-investigation-2026-11-09.md:96`
- `ToolPkgWasmApi.js` — iOS WASM 验收中使用的 ToolPkg WASM API。`docs/testflight-feedback-investigation-2026-11-09.md:96`
- `usearch.wasm` — iOS WASM 验收中使用的真实 USearch WASM 产物。`docs/testflight-feedback-investigation-2026-11-09.md:96`
- `VectorIndex` — iOS WASM 验收中使用的生产向量索引适配器。`docs/testflight-feedback-investigation-2026-11-09.md:96`

## 调用链

### Android 特权命令：授权与执行

1. Flutter 经 `hostOnboardingRequestPermission` 传入可选字段，不传字段时沿用已保存设置。`docs/android-root-shell.md:26`
2. `rootExecutionMode` 取值 auto / libsu / exec，`suCommand` 接受自定义 su 命令。`docs/android-root-shell.md:33`
3. `AndroidPrivilegeAuthorization` 要求显式用户同意加当前 UID 验证，未同意时状态查询不调用 `su`。`docs/android-root-shell.md:12`
4. 实际授权验证用 `id -u`，退出码为 0 且输出恰好为 `0` 才算授权。`docs/android-root-shell.md:18`
5. 自动选择优先复查最近成功的传输，首次探测遇到 KernelSU / APatch 的版本标识优先直接 exec，否则优先 libsu。`docs/android-root-shell.md:16`
6. Owner 经 `execute_privileged_command` 以 `root` / `root_auto` / `root_libsu` / `root_exec` / `shizuku` 指定传输执行。`docs/android-root-shell.md:44`
7. 用户命令启动后不会换传输重试，避免有副作用的命令执行两次。`docs/android-root-shell.md:22`

### Android 系统终端：身份选择

1. Super Admin 的非 Linux/proot 终端走 `hosts/android/src/terminal.rs`，创建系统 shell 会话时由 Rust 选择身份。`docs/android-root-shell.md:53`
2. 已有用户同意时重新用 `id -u` 验证直接 su argv，再通过该 argv 启动持久 PTY，走 Root 身份。`docs/android-root-shell.md:57`
3. Root 当前不可用且已有 Shizuku 授权时绑定专用 UserService，走 Shizuku 身份。`docs/android-root-shell.md:60`
4. 两项授权均不可用时以应用自身 UID 启动 `/system/bin/sh`，走普通 sh 身份。`docs/android-root-shell.md:62`
5. 身份在会话创建时确定，后续命令不重新路由，授权变化后需新建会话。`docs/android-root-shell.md:64`

### iOS 工具调用：调度广播链

1. `JsEngine::scriptRequestStepTask` 经 `NativeHostJavaScriptRuntime::callHostJavaScriptFunction` 进入 V8 `host_callback`。`docs/performance-ios-2026-10-27.md:35`
2. 调用经 `NativeHostRuntimeTaskSchedulerHost::scheduleHostRuntimeBlockingAsyncTask` 与 `RuntimeTaskQueue::sendMany` 到达 `tokio::sync::watch` / `BigNotify::notify_waiters`。`docs/performance-ios-2026-10-27.md:40`
3. 共享任务队列采用 `watch` 广播，入队、任务开始 poll、结束 poll、销毁及分派后都会发送变化。`docs/performance-ios-2026-10-27.md:47`
4. 文档指出，优先优化目标是按可运行任务和接收者定向通知、取消空队列状态广播。`docs/performance-ios-2026-10-27.md:47`

### iOS 消息接收：帧工作链

1. `SchedulerBinding.handleDrawFrame` 经 `PipelineOwner.flushLayout` 进入消息列表布局。`docs/performance-ios-2026-10-27.md:66`
2. `RenderChatMessageSliverList.performLayout` 与 `RenderChatMessageExtentBox.performLayout` 之后经 `RenderParagraph.performLayout` 到 `TextPainter.layout` 与 `_NativeParagraph.layout`。`docs/performance-ios-2026-10-27.md:66`
3. 回复完成后，`ChatArea` 的 `_beginBottomFollowCompletion → _tickBottomFollow → jumpTo` 路径允许继续逐帧追赶底部。`docs/performance-ios-2026-10-27.md:97`
4. 文档声明，没有做关闭自动跟随的对照试验，因此不把全部完成后 CPU 归因于该 ticker。`docs/performance-ios-2026-10-27.md:99`

### TestFlight 反馈：排查链

1. 按原始反馈文字逐条核对，优先复现用户操作。`docs/testflight-feedback-investigation-2026-11-09.md:13`
2. 可复现的缺陷按实际调用链确认后修复，信息不足的不等于用户操作错误。`docs/testflight-feedback-investigation-2026-11-09.md:49`
3. 已修复且对应场景测试通过的项目按本地验证结果收尾，本地通过不表述为实际真机运行通过。`docs/testflight-feedback-investigation-2026-11-09.md:5`
4. 未测试的独立症状和失败项目继续排查，缺少新堆栈的崩溃不依据相似旧堆栈关闭。`docs/testflight-feedback-investigation-2026-11-09.md:53`

## 来源

- `docs/android-root-shell.md` — Android Root / su 封装：组件职责、模式与自定义 su、Rust Android 系统终端、维护检查。`docs/android-root-shell.md:1`
- `docs/performance-ios-2026-10-27.md` — iOS 工具调用与消息接收 CPU 堆栈分析：实测 CPU、工具调用链、消息接收帧工作、回复完成后帧工作、发热结论边界。`docs/performance-ios-2026-10-27.md:1`
- `docs/testflight-feedback-investigation-2026-11-09.md` — TestFlight 反馈逐项排查（2026-11-09）：验收口径、原始反馈回归、原清单遗漏、排查边界、22 项清单、大字体修复、iOS WASM 引擎修复、市场更新修复、验证限制。`docs/testflight-feedback-investigation-2026-11-09.md:1`
- 核验方法：2026-11-11 对基线 AAswordman/Operit2 @ 364d1d594 的三份 seed 文件全文 grep“桌面”“对照表”“能力对照”，“桌面”仅在 `docs/testflight-feedback-investigation-2026-11-09.md:85` 命中一次（64 MiB 帧上限按桌面本地传输表述），“对照表”“能力对照”零命中；三份 seed 未提供完整的移动端/桌面端能力对照表，本页的平台差异点只取自 seed 中出现的平台区分表述。`docs/testflight-feedback-investigation-2026-11-09.md:85`
- 本页 seed 之外未读其他文件，未引用 seed 之外的实现细节。`docs/android-root-shell.md:1`
