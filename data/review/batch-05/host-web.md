---
title: Web/WASM Host
module: hosts
platforms: [web]
sources: [hosts/web/README.md, hosts/web/Cargo.toml, hosts/web/src/lib.rs, hosts/web/src/common.rs, hosts/web/src/javascript_runtime.rs, hosts/web/src/javascript_promises.js, hosts/web/src/tools/fs/mod.rs, hosts/web/src/tools/browser/mod.rs, hosts/web/src/tools/browser_session/mod.rs, hosts/web/src/tools/runtime/mod.rs, hosts/web/src/tools/storage/mod.rs, hosts/web/src/tools/system/mod.rs, hosts/web/src/tools/terminal/mod.rs, hosts/web/src/tools/archive/mod.rs, hosts/web/src/tools/websocket.rs]
date: 2026-11-11
---

## 概述

`operit-host-web` 为 `operit-host-api` 的每个 host trait 提供 Web/WASM 实现（`hosts/web/README.md:3`）。
Web 平台的 Rust 代码调用与原生构建相同的 host trait（`hosts/web/README.md:4`）。
浏览器侧在构造 Web host 结构体之前安装 `globalThis.__operitHost`（`hosts/web/README.md:4`）。
Web Host 的 crate 名为 `operit-host-web`（`hosts/web/Cargo.toml:2`）。
`operit-host-web` 声明 `publish = false`，不对外发布（`hosts/web/Cargo.toml:6`）。
`operit-host-web` 的 crate 类型为 `cdylib` 与 `rlib`（`hosts/web/Cargo.toml:6`）。
`createRuntimeHostManager` 创建浏览器侧 host bundle，不构造第二棵 Core 树（`hosts/web/src/lib.rs:35`）。
hosts/web 不是浏览器控件或 WebView：它是 `operit-host-api` 的 host trait 实现层，Android 平台的实现见 [[host-android|Android Host]]（`hosts/web/README.md:3`）。
`WebBrowserSessionHost` 模拟浏览器会话（`hosts/web/src/tools/browser_session/mod.rs:24`）。
浏览器会话保存在线程局部 `BROWSER_SESSIONS` 映射里（`hosts/web/src/tools/browser_session/mod.rs:20`）。
导航只更新已存会话的当前 URL 与标题，并把 `canGoBack` 置为 true、进度置为 100（`hosts/web/src/tools/browser_session/mod.rs:200`）。
脚本求值用 `js_sys::eval` 在当前浏览器全局作用域执行脚本（`hosts/web/src/tools/browser_session/mod.rs:222`）。
Web Host 的浏览器会话是模拟状态，不是应用内嵌的浏览器控件（`hosts/web/src/tools/browser_session/mod.rs:24`）。
`visitWeb` 是一次性访问：转发到桥接 `visitWeb` 方法并返回内容（`hosts/web/src/tools/browser/mod.rs:24`）。

## AI 速览

- `createRuntimeHostManager` — 组装浏览器侧 `HostManager`（`hosts/web/src/lib.rs:36`）
- `WebFileSystemHost` — Web 文件系统 Host（`hosts/web/src/tools/fs/mod.rs:49`）
- `WebWebVisitHost` — Web 网页访问 Host（`hosts/web/src/tools/browser/mod.rs:22`）
- `WebManagedRuntimeHost` — 托管运行时 Host（`hosts/web/src/tools/runtime/mod.rs:25`）
- `WebRuntimeStorageHost` — 提供 `defaultRuntimeRoot` 的运行时存储 Host（`hosts/web/src/tools/storage/mod.rs:25`）
- `WebSystemOperationHost` — 由 `createRuntimeHostManager` 创建的系统操作 Host（`hosts/web/src/lib.rs:41`）
- `WebTerminalHost` — 实现 `TerminalHost` 的终端 Host（`hosts/web/src/tools/terminal/mod.rs:48`）
- `WebArchiveStagingHost` — 实现 `ArchiveStagingHost` 的归档暂存 Host（`hosts/web/src/tools/archive/mod.rs:21`）
- `WebWebSocketHost` — 实现 `WebSocketHost` 的 WebSocket Host（`hosts/web/src/tools/websocket.rs:35`）
- `WebBrowserSessionHost` — 模拟浏览器会话 Host（`hosts/web/src/tools/browser_session/mod.rs:24`）
- `WebHostJavaScriptRuntimeHost` — 实现 `HostJavaScriptRuntimeHost` 的 JS 运行时 Host（`hosts/web/src/javascript_runtime.rs:451`）
- `withToastHost` 与 `withClipboardHost` 都以系统操作 Host 注册（`hosts/web/src/lib.rs:51`）
- 数据流向：Rust host trait 调用 → `bridge_module` 取 globalThis 的 `__operitHost` 同名模块 → 桥接方法执行 → 读回字段（`hosts/web/src/common.rs:106`）

## 核心机制

### 共享 JS 桥接

`bridge_module` 从 `js_sys::global` 读取 `__operitHost`（`hosts/web/src/common.rs:106`）。
`__operitHost` 未安装时返回 web host bridge `__operitHost` is not installed 错误（`hosts/web/src/common.rs:109`）。
桥接模块缺失时返回 web host bridge module is not installed 错误（`hosts/web/src/common.rs:115`）。
`call_function` 要求桥接方法能转成 `Function`，否则返回 web host bridge method is not a function 错误（`hosts/web/src/common.rs:124`）。
桥接方法返回 `Promise` 时返回异步 `Promise` 错误，不等待它完成（`hosts/web/src/common.rs:137`）。
桥接值使用与 `operit-host-api` 相同的字段名，二进制数据以 `Uint8Array` 传递（`hosts/web/README.md:74`）。
SQLite 整数以字符串形式跨 JS 传递，以保留 64 位值（`hosts/web/README.md:75`）。
`sqlite_value_to_js` 把 `SqliteValue::Integer` 转成字符串（`hosts/web/src/common.rs:565`）。
`js_i64` 先尝试把字符串解析为 `i64`，再接受 JS 数字（`hosts/web/src/common.rs:838`）。
`OperitWebHost` 桥接类型列出 `fileSystem`、`webVisit`、`managedRuntime`、`managedRuntimeProcess`、`runtimeStorage`、`sqlite`、`terminal`、`systemOperation`、`localInference`（`hosts/web/README.md:60`）。

### Host 组装：`createRuntimeHostManager` 注册全部 host trait

`createRuntimeHostManager` 返回 `HostManager`（`hosts/web/src/lib.rs:36`）。
`runtimeSqliteHost` 是 `runtimeStorageHost` 的克隆（`hosts/web/src/lib.rs:38`）。
`hostSecretStore` 是 `runtimeStorageHost` 的克隆（`hosts/web/src/lib.rs:39`）。
`withFileSystemWebVisitSystemOperationAndManagedRuntimeHosts` 装配 `WebFileSystemHost`、`WebWebVisitHost`、`WebHttpHost`、`WebManagedRuntimeHost` 与系统操作 Host（`hosts/web/src/lib.rs:43`）。
系统操作 Host 同时注册为 toast Host 与 clipboard Host（`hosts/web/src/lib.rs:51`）。
运行时存储写 Host 通过 `withRuntimeStorageWriteHost` 注册（`hosts/web/src/lib.rs:54`）。
归档暂存 Host 通过 `withArchiveStagingHost` 注册（`hosts/web/src/lib.rs:55`）。
浏览器会话 Host 通过 `withBrowserSessionHost` 注册 `WebBrowserSessionHost`（`hosts/web/src/lib.rs:57`）。
WebSocket Host 通过 `withWebSocketHost` 注册 `WebWebSocketHost`（`hosts/web/src/lib.rs:58`）。
终端 Host 通过 `withTerminalHost` 注册 `WebTerminalHost`（`hosts/web/src/lib.rs:59`）。
音频播放 Host 通过 `withAudioPlaybackHost` 注册 `WebAudioPlaybackHost`（`hosts/web/src/lib.rs:60`）。
蓝牙 Host 通过 `withBluetoothHost` 注册 `WebBluetoothHost`（`hosts/web/src/lib.rs:61`）。
本地推理 Host 通过 `withLocalInferenceHost` 注册 `WebLocalInferenceHost`（`hosts/web/src/lib.rs:62`）。
TTS 播放 Host 通过 `withTtsPlaybackHost` 注册 `WebTtsPlaybackHost`（`hosts/web/src/lib.rs:63`）。
运行时事件调度 Host 通过 `withHostRuntimeEventSchedulerHost` 注册（`hosts/web/src/lib.rs:66`）。
运行时任务调度 Host 通过 `withHostRuntimeTaskSchedulerHost` 注册（`hosts/web/src/lib.rs:67`）。
JS 运行时 Host 通过 `withHostJavaScriptRuntimeHost` 注册 `WebHostJavaScriptRuntimeHost`（`hosts/web/src/lib.rs:68`）。
运行时事件 Host 通过 `withHostRuntimeEventHost` 注册 `WebHostRuntimeEventHost`（`hosts/web/src/lib.rs:69`）。
`call_data_rescue` 调用桥接 `dataRescue` 模块（`hosts/web/src/common.rs:46`）。

### 插件 JS 执行：浏览器原生引擎

Web JS Host 用浏览器原生引擎执行插件代码（`hosts/web/README.md:20`）。
每个 JS 运行时各拥有一个带独立全局变量的专用模块 Worker（`hosts/web/README.md:20`）。
Web 构建不需要 QuickJS/WASM 引擎或 WASI libc（`hosts/web/README.md:22`）。
Web 平台上 Core 继续使用 `HostJavaScriptRuntime`（`hosts/web/README.md:21`）。
JS Worker 经已有的主页面 host 通道创建，模块就绪先确认，Core 再开始同步等待（`hosts/web/README.md:24`）。
浏览器在确认命令前先排空 Promise 微任务（`hosts/web/README.md:31`）。
Core 经同一个有作用域的 Promise 注册表交付异步 host 完成通知（`hosts/web/README.md:31`）。
等待期间轮询 host 中断谓词，中断会终止整个执行 Worker（`hosts/web/README.md:32`）。
中断后的后续命令报告运行时已被销毁，释放 Rust 运行时也会终止其 Worker（`hosts/web/README.md:33`）。
同机引擎对比用 Chrome 155 与编译为 WASM 的 QuickJS-NG 0.16.2（-O3），预热后测七个样本并核对校验和（`hosts/web/README.md:40`）。
编译 521,155 字节的角色卡入口：QuickJS/WASM 中位 26.2 毫秒，浏览器引擎中位 8.0 毫秒（`hosts/web/README.md:45`）。
一百万次整数迭代：QuickJS/WASM 中位 44.7 毫秒，浏览器引擎中位 3.7 毫秒（`hosts/web/README.md:46`）。
一万条记录的 JSON 过滤映射排序：QuickJS/WASM 中位 254.5 毫秒，浏览器引擎中位 27.5 毫秒（`hosts/web/README.md:47`）。
遍历两万个对象节点：QuickJS/WASM 中位 170.0 毫秒，浏览器引擎中位 6.3 毫秒（`hosts/web/README.md:48`）。
引擎对比测的是引擎工作量，不是整应用提速，也不是新 Worker 传输开销（`hosts/web/README.md:50`）。

### 同步调用：结构化克隆 + MessagePack 64 KiB 共享缓冲区

命令输入用结构化克隆（`hosts/web/README.md:25`）。
结果与同步 host 调用用 MessagePack 帧，放在 64 KiB 共享缓冲区里（`hosts/web/README.md:26`）。
每帧复用前先确认，因此消息长度超过缓冲区大小（`hosts/web/README.md:27`）。
Rust 保留结构化桥接的深度与节点上限以及安全整数表示（`hosts/web/README.md:27`）。
插件 host 操作继续在 Core 执行器上以当前执行上下文执行（`hosts/web/README.md:28`）。
`structuredResult` 限制结构化桥接深度 128、节点数 1,000,000（`hosts/web/src/javascript_runtime.rs:338`）。
JS 桥接把深度上限设为 128、节点上限设为 1000000（`hosts/web/src/javascript_promises.js:20`）。
JS 桥接的待处理 Promise 注册表上限为 4096（`hosts/web/src/javascript_promises.js:19`）。
安全整数范围内的小数部分为零的数字保留为 `i64` 或 `u64`（`hosts/web/src/javascript_runtime.rs:402`）。
Host 数据不支持 `BigInt`（`hosts/web/src/javascript_promises.js:33`）。
Host 参数含循环引用时抛 `TypeError`（`hosts/web/src/javascript_promises.js:37`）。
`ByteArray` 参数经 `transferValue` 转移底层的 buffer（`hosts/web/src/javascript_promises.js:85`）。
异步绑定要求作用域为字符串（`hosts/web/src/javascript_promises.js:98`）。
Promise 请求标识在 9007199254740991 处耗尽（`hosts/web/src/javascript_promises.js:110`）。
`settle` 在调用完成处理前先从待处理表删除请求（`hosts/web/src/javascript_promises.js:134`）。
`cancel` 以 JavaScript execution was cancelled 拒绝该作用域的待处理 Promise（`hosts/web/src/javascript_promises.js:144`）。
`__operitHostPromiseRegistry` 冻结后提供 `binding`、`syncBinding`、`snapshotResult`、`settle`、`cancel`（`hosts/web/src/javascript_promises.js:155`）。
`snapshotResult` 对非 JSON 兼容的生命周期返回值抛 `TypeError`（`hosts/web/src/javascript_promises.js:71`）。
中断信号是 16 字节 `SharedArrayBuffer` 上的 `Int32Array`（`hosts/web/src/javascript_runtime.rs:70`）。
`cancel` 把信号字 1 置为 1 并经 `Atomics` 通知等待方（`hosts/web/src/javascript_runtime.rs:93`）。
替换中断令牌时取最早期限，经 `Atomics` 把信号字 1 清零，再把期限写入信号字 2 与字 3（`hosts/web/src/javascript_runtime.rs:113`）。
`createHostJavaScriptRuntime` 读取全局 `__operitCreateJavaScriptRuntime` 工厂（`hosts/web/src/javascript_runtime.rs:457`）。
新建 JS 运行时以 `initialize` 操作装入 `javascript_promises.js` 源码（`hosts/web/src/javascript_runtime.rs:469`）。
释放 `WebHostJavaScriptRuntime` 时调用浏览器侧 `dispose`（`hosts/web/src/javascript_runtime.rs:206`）。
`registerHostJavaScriptFunction` 用 `syncBinding` 工厂注册同步绑定（`hosts/web/src/javascript_runtime.rs:316`）。
`registerHostJavaScriptAsyncJsonFunction` 用 `binding` 工厂注册异步绑定（`hosts/web/src/javascript_runtime.rs:285`）。
`settleHostJavaScriptPromise` 以 `settle` 操作发送标识、值与拒绝标志（`hosts/web/src/javascript_runtime.rs:299`）。
`executePendingHostJavaScriptJobs` 以 `jobs` 操作让浏览器排空待处理 JS 任务（`hosts/web/src/javascript_runtime.rs:261`）。
求值字符串用 `as_string` 取浏览器引擎的字符串转换，非字符串结果报错（`hosts/web/src/javascript_runtime.rs:254`）。
`createHostJavaScriptRuntimeState` 创建浏览器亲和的 JS 状态并分配数字句柄（`hosts/web/src/javascript_runtime.rs:477`）。
`destroyHostJavaScriptRuntimeState` 把状态标为已销毁并移除状态与锁（`hosts/web/src/javascript_runtime.rs:606`）。
JS 运行时测试命令为从仓库根运行 `node --test tools/tests/web_javascript_runtime.test.mjs`（`hosts/web/README.md:35`）。

### 文件系统、存储与 SQLite（Web 平台）

`src/tools/fs/mod.rs` 实现 `FileSystemHost`（`hosts/web/README.md:10`）。
文件系统 Host 的 `envLabel` 返回 `web`（`hosts/web/src/tools/fs/mod.rs:68`）。
`environmentDescriptor` 返回 `HostEnvironmentDescriptor` 的 web 描述（`hosts/web/src/tools/fs/mod.rs:72`）。
`openAppendFile` 拒绝目录路径，不存在时先写空文件，初始长度取 `fileExists` 的 size，负数报错（`hosts/web/src/tools/fs/mod.rs:56`）。
追加句柄的 `append` 在本地累加 `length`，不重读文件（`hosts/web/src/tools/fs/mod.rs:42`）。
`validatePath` 转发到桥接 `validatePath` 方法（`hosts/web/src/tools/fs/mod.rs:76`）。
`listFiles` 的条目含 `name`、`isDirectory`、`size`、`permissions`、`lastModified`（`hosts/web/src/tools/fs/mod.rs:90`）。
`readFileBytesRange` 把偏移与长度转发到桥接（`hosts/web/src/tools/fs/mod.rs:123`）。
`grepCode` 把请求转成 JS 对象后调用桥接 `grepCode`（`hosts/web/src/tools/fs/mod.rs:228`）。
`GrepCodeResult` 含 `totalMatches` 与 `filesSearched`（`hosts/web/src/tools/fs/mod.rs:254`）。
`defaultRuntimeRoot` 返回 `runtime` 路径（`hosts/web/src/tools/storage/mod.rs:25`）。
`defaultWorkspaceRoot` 返回 `workspaces` 路径（`hosts/web/src/tools/storage/mod.rs:31`）。
`readBytesRange` 从 Worker 拥有的 OPFS 运行时存储读一段有界字节范围（`hosts/web/src/tools/storage/mod.rs:63`）。
`writeBytesAtomically` 直接调用 `writeBytes`（`hosts/web/src/tools/storage/mod.rs:100`）。
`createWriteSession` 返回会话标识字符串（`hosts/web/src/tools/storage/mod.rs:183`）。
`commit` 调用桥接 `commitWriteSession`（`hosts/web/src/tools/storage/mod.rs:169`）。
`discard` 调用桥接 `discardWriteSession`（`hosts/web/src/tools/storage/mod.rs:175`）。
桥接值为空或未定义时 `readSecret` 返回 `None`（`hosts/web/src/tools/storage/mod.rs:193`）。
`openSqliteDatabase` 调用桥接 `open` 并持有返回的连接标识字符串（`hosts/web/src/tools/storage/mod.rs:216`）。
`readColumnRange` 把读取长度限制在 64 KiB 以内（`hosts/web/src/tools/storage/mod.rs:241`）。
`columnSize` 用 `length` 加 `CAST` 到 `BLOB` 的 SQL 查询列字节数（`hosts/web/src/tools/storage/mod.rs:237`）。
运行时自有文件由专用运行时 Worker 存入 OPFS，host 桥接不把完整运行时树加载到主线程映射里（`hosts/web/README.md:78`）。
存储 Worker 在 OPFS 句柄整个生命周期持有身份专属的排他 Web Lock 与共享维护访问（`hosts/web/README.md:80`）。
旧 Worker 仍拥有存储时，新页面打不开同一存储（`hosts/web/README.md:82`）。
服务源站提供 COOP 与 COEP 响应头，因为运行时 Worker 的 host RPC 使用 `SharedArrayBuffer`（`hosts/web/README.md:84`）。

### 网页访问与浏览器会话：与 WebView 的区别

`visitWeb` 转发到桥接 `visitWeb` 方法（`hosts/web/src/tools/browser/mod.rs:24`）。
`WebVisitResult` 含 `url`、`title`、`content`、`metadata`、`links`（`hosts/web/src/tools/browser/mod.rs:29`）。
网页访问结果含 `imageLinks` 字符串数组（`hosts/web/src/tools/browser/mod.rs:37`）。
`WebBrowserSessionHost` 模拟浏览器会话（`hosts/web/src/tools/browser_session/mod.rs:24`）。
浏览器会话保存在线程局部 `BROWSER_SESSIONS` 映射里（`hosts/web/src/tools/browser_session/mod.rs:20`）。
浏览器会话标识按 `web-browser-{value}` 分配（`hosts/web/src/tools/browser_session/mod.rs:245`）。
新建浏览器会话把标题置为初始 URL，进度置为 100，`canGoBack` 置为 false（`hosts/web/src/tools/browser_session/mod.rs:58`）。
导航只更新已存会话的当前 URL 与标题，并把 `canGoBack` 置为 true、进度置为 100（`hosts/web/src/tools/browser_session/mod.rs:200`）。
脚本求值用 `js_sys::eval` 在当前浏览器全局作用域执行脚本（`hosts/web/src/tools/browser_session/mod.rs:222`）。
`jsValueJson` 用 `JSON::stringify` 序列化脚本求值结果（`hosts/web/src/tools/browser_session/mod.rs:296`）。
不支持的浏览器动作返回 browser simulator does not support action 错误（`hosts/web/src/tools/browser_session/mod.rs:165`）。
Web Host 的浏览器会话是模拟状态，不是应用内嵌的浏览器控件（`hosts/web/src/tools/browser_session/mod.rs:24`）。
`localInference` 执行已安装的 Sherpa ONNX Web STT 与 TTS 包（`hosts/web/README.md:77`）。

### 终端：浏览器内 v86 Linux 虚拟机

终端桥接经 v86 启动浏览器本地 Buildroot Linux 客户机，方法交换原始虚拟串口字节（`hosts/web/README.md:68`）。
Linux 客户机资产由 Flutter Web 构建钩子生成，服务前按固定 SHA-256 摘要核对（`hosts/web/README.md:71`）。
Web 终端的平台为 `web-linux-vm`，终端为 `v86`，终端类型为 `shell`（`hosts/web/src/tools/terminal/mod.rs:20`）。
终端信息把 Web 终端描述为带 `BusyBox`、`Node` 与 `Python` 的浏览器本地 Buildroot 虚拟机（`hosts/web/src/tools/terminal/mod.rs:80`）。
工作目录解析把宿主目录映射到 `/mnt/operit-host/` 之下（`hosts/web/src/tools/terminal/mod.rs:59`）。
启动 PTY 会话在 `rows` 或 `cols` 为零时报错（`hosts/web/src/tools/terminal/mod.rs:100`）。
启动 PTY 会话调用桥接 `startPty` 并传入会话标识、行数与列数（`hosts/web/src/tools/terminal/mod.rs:105`）。
终端会话标识按 `linux-vm-terminal-{value}` 分配（`hosts/web/src/tools/terminal/mod.rs:433`）。
桥接值为空或未定义时 `pollPtyExitCode` 返回 `None`（`hosts/web/src/tools/terminal/mod.rs:170`）。
会话列表只列出未退出的会话，条目 `sessionKind` 为 `linux-vm`（`hosts/web/src/tools/terminal/mod.rs:199`）。
按名创建或复用类型化会话时，遇到同名会话直接复用，`isNewSession` 为 false（`hosts/web/src/tools/terminal/mod.rs:232`）。
新建终端会话从根目录 `/` 启动，默认 24 行 80 列（`hosts/web/src/tools/terminal/mod.rs:244`）。
会话内流式调度拒绝非零 `timeoutMs`，要求会话自有执行（`hosts/web/src/tools/terminal/mod.rs:308`）。
`executeHiddenCommand` 报错，浏览器本地 Linux 虚拟机终端不提供隐藏命令执行（`hosts/web/src/tools/terminal/mod.rs:343`）。
会话屏幕用 `vt100::Parser` 渲染保留的串口屏幕内容（`hosts/web/src/tools/terminal/mod.rs:380`）。
会话内执行命令返回 `output`、`exitCode`、`timedOut`、`workingDir`（`hosts/web/src/tools/terminal/mod.rs:271`）。

### 归档、WebSocket 与系统操作

`createArchive` 把声明的字节长度转成 `i64` 再传给桥接（`hosts/web/src/tools/archive/mod.rs:24`）。
`sealArchive` 返回 `u64` 长度，负数报错（`hosts/web/src/tools/archive/mod.rs:78`）。
`readArchive` 按偏移与长度读一段有界范围（`hosts/web/src/tools/archive/mod.rs:88`）。
`archiveFileReference` 返回存储支持的浏览器文件 URL，不是归档字节数据（`hosts/web/src/tools/archive/mod.rs:59`）。
归档暂存同样是 Worker 拥有的 OPFS：`createArchive` 预留声明字节范围，`appendArchive` 写有序分块，`sealArchive` 核对精确长度，`readArchive` 提供有界的 ZIP 读取范围（`hosts/web/README.md:87`）。
浏览器文件选择留在 UI 线程，选中的 `Blob` 按有界 `openRead()` 分块读取并经 Core Link 推送（`hosts/web/README.md:90`）。
打开 WebSocket 时 `streamId` 已打开则报错（`hosts/web/src/tools/websocket.rs:45`）。
WebSocket 的二进制类型设为 `Arraybuffer`（`hosts/web/src/tools/websocket.rs:55`）。
WebSocket 关闭码 1000 或 1005 视为正常关闭，其余关闭码视为错误（`hosts/web/src/tools/websocket.rs:71`）。
发送 WebSocket 二进制消息用 `send_with_u8_array` 发送字节（`hosts/web/src/tools/websocket.rs:111`）。
`closeWebSocket` 关闭浏览器 WebSocket（`hosts/web/src/tools/websocket.rs:133`）。
`toast` 把消息转发到桥接 `toast` 方法（`hosts/web/src/tools/system/mod.rs:31`）。
`setClipboardText` 返回桥接存下的文本（`hosts/web/src/tools/system/mod.rs:40`）。
`installApp` 先调用 `timing.requireImmediate`，要求立即安装时机（`hosts/web/src/tools/system/mod.rs:95`）。
桥接返回空图片字节时截图报错（`hosts/web/src/tools/system/mod.rs:255`）。
截图保存时创建父目录后经 `WebFileSystemHost` 写下截图字节并返回路径（`hosts/web/src/tools/system/mod.rs:260`）。
`recognizeText` 先经 `WebFileSystemHost` 读图片字节，再调用桥接 `recognizeText`（`hosts/web/src/tools/system/mod.rs:274`）。
`getDeviceInfo` 读取 `deviceId`、`model`、`manufacturer`、`androidVersion`、`sdkVersion`（`hosts/web/src/tools/system/mod.rs:228`）。
`WebManagedRuntimeProcess` 持有桥接返回的标识字符串（`hosts/web/src/tools/runtime/mod.rs:54`）。
运行命令返回 `exitCode`、`stdout`、`stderr`（`hosts/web/src/tools/runtime/mod.rs:70`）。
`readStdoutLine` 接受 `timeoutMs` 参数（`hosts/web/src/tools/runtime/mod.rs:102`）。
`program_to_js` 把 `ManagedRuntimeProgram` 的 Node、Python、Uv、Pnpm、Command 映射为字符串（`hosts/web/src/common.rs:527`）。

## 关键符号

- `createRuntimeHostManager` — 组装浏览器侧 `HostManager`（`hosts/web/src/lib.rs:36`）
- `WebFileSystemHost` — 实现 `FileSystemHost`（`hosts/web/src/tools/fs/mod.rs:49`）
- `WebWebVisitHost` — 实现 `WebVisitHost`（`hosts/web/src/tools/browser/mod.rs:22`）
- `WebManagedRuntimeHost` — 实现 `ManagedRuntimeHost`（`hosts/web/src/tools/runtime/mod.rs:25`）
- `WebRuntimeStorageHost` — 提供 `defaultRuntimeRoot` 的运行时存储 Host（`hosts/web/src/tools/storage/mod.rs:25`）
- `WebSystemOperationHost` — 由 `createRuntimeHostManager` 创建的系统操作 Host（`hosts/web/src/lib.rs:41`）
- `WebTerminalHost` — 实现 `TerminalHost`（`hosts/web/src/tools/terminal/mod.rs:48`）
- `WebArchiveStagingHost` — 实现 `ArchiveStagingHost`（`hosts/web/src/tools/archive/mod.rs:21`）
- `WebWebSocketHost` — 实现 `WebSocketHost`（`hosts/web/src/tools/websocket.rs:35`）
- `WebBrowserSessionHost` — 模拟浏览器会话 Host（`hosts/web/src/tools/browser_session/mod.rs:24`）
- `WebHostJavaScriptRuntimeHost` — 实现 `HostJavaScriptRuntimeHost`（`hosts/web/src/javascript_runtime.rs:451`）
- `WebHostJavaScriptRuntime` — 释放时调用浏览器侧 `dispose` 的 JS 运行时（`hosts/web/src/javascript_runtime.rs:206`）
- `bridge_module` — 取 globalThis 的 `__operitHost` 同名桥接模块（`hosts/web/src/common.rs:106`）
- `call_function` — 调用桥接方法（`hosts/web/src/common.rs:124`）
- `__operitHostPromiseRegistry` — 冻结的 Promise 注册表（`hosts/web/src/javascript_promises.js:155`）
- `WebFileAppendHandle`（`hosts/web/src/tools/fs/mod.rs:27`）的 `append` 在本地累加 `length`（`hosts/web/src/tools/fs/mod.rs:42`）

## 调用链

1. 浏览器侧安装 `globalThis.__operitHost`（`hosts/web/README.md:4`）。
2. `createRuntimeHostManager` 组装 `HostManager`（`hosts/web/src/lib.rs:36`）。
3. Rust 调用 host trait 方法（`hosts/web/README.md:4`）。
4. 共享桥接经 `bridge_module` 取同名模块（`hosts/web/src/common.rs:106`）。
5. `call_function` 调用桥接方法（`hosts/web/src/common.rs:124`）。
6. 桥接方法返回 `Promise` 时返回异步 `Promise` 错误，不等待它完成（`hosts/web/src/common.rs:137`）。
7. 插件 JS 调用：命令输入用结构化克隆，结果与同步调用走 MessagePack 帧（`hosts/web/README.md:26`）。
8. 等待期间轮询 host 中断谓词，中断终止整个执行 Worker（`hosts/web/README.md:32`）。
9. 异步完成经同一个有作用域的 Promise 注册表交付（`hosts/web/README.md:31`）。

## 来源

- hosts/web/README.md
- hosts/web/Cargo.toml
- hosts/web/src/lib.rs
- hosts/web/src/common.rs
- hosts/web/src/javascript_runtime.rs
- hosts/web/src/javascript_promises.js
- hosts/web/src/tools/fs/mod.rs
- hosts/web/src/tools/browser/mod.rs
- hosts/web/src/tools/browser_session/mod.rs
- hosts/web/src/tools/runtime/mod.rs
- hosts/web/src/tools/storage/mod.rs
- hosts/web/src/tools/system/mod.rs
- hosts/web/src/tools/terminal/mod.rs
- hosts/web/src/tools/archive/mod.rs
- hosts/web/src/tools/websocket.rs
