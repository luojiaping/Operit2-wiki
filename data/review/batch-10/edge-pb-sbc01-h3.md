---
title: PB_SBC01_H3 机器人
module: edge
platforms: [linux]
sources: 7
date: 2026-11-11
---

## 概述

- `operit-pb-sbc01-h3` 是 PB_SBC01_H3 的 full Core 控制器。`edge/boards/pb_sbc01_h3/README.md:12`
- `operit-pb-sbc01-h3-face` 是机器人脸部状态文件的本地控制台渲染器。`edge/boards/pb_sbc01_h3/README.md:13`
- 该入口在 PB_SBC01_H3 上启动完整 Core 树。`edge/boards/pb_sbc01_h3/README.md:5`
- 板级机器人脸部能力通过 Host API 接入。`edge/boards/pb_sbc01_h3/README.md:6`
- 该入口为手机、桌面与 Web Access 客户端提供已认证的 Link 端点。`edge/boards/pb_sbc01_h3/README.md:7`
- 控制器只在 Linux 上启动，非 Linux 目标打印 operit-pb-sbc01-h3 requires Linux 并以退出码 1 退出。`edge/boards/pb_sbc01_h3/src/main.rs:27`

## AI 速览

- `run` — 启动带 PB_SBC01_H3 板级服务接入的完整 Operit Core。`edge/boards/pb_sbc01_h3/src/app.rs:17`
- `PbSbc01H3Config` — 控制器命令行配置。`edge/boards/pb_sbc01_h3/src/config.rs:9`
- `PbSbc01H3Board` — 板级 profile，持有机器人脸部宿主。`edge/boards/pb_sbc01_h3/board/src/lib.rs:49`
- `PbSbc01H3RobotFaceHost` — 把经校验的表情写入板级脸部状态文件。`edge/boards/pb_sbc01_h3/board/src/lib.rs:105`
- `PbSbc01H3FaceStateFile` — 脸部状态文件格式。`edge/boards/pb_sbc01_h3/board/src/lib.rs:159`
- `createPbSbc01H3HostManager` — 创建带板级能力接入的 Linux HostManager。`edge/boards/pb_sbc01_h3/src/app.rs:64`
- `createBoardProxy` — 创建类型化板级代理。`edge/boards/pb_sbc01_h3/src/app.rs:74`
- `faceGlyph` — 为表情选控制台字形。`edge/boards/pb_sbc01_h3/src/face_console.rs:92`
- 主入口函数为 Linux 上的 `main`，调用 `app::run`。`edge/boards/pb_sbc01_h3/src/main.rs:14`
- 数据流向一句话：控制器经 `setExpression` 把表情写入状态文件（`edge/boards/pb_sbc01_h3/board/src/lib.rs:139`），脸部渲染器循环读文件并渲染到终端（`edge/boards/pb_sbc01_h3/src/face_console.rs:27`）。

## 核心机制

### 两个二进制

- `operit-pb-sbc01-h3` 是 PB_SBC01_H3 的 full Core 控制器。`edge/boards/pb_sbc01_h3/README.md:12`
- `operit-pb-sbc01-h3-face` 是机器人脸部状态文件的本地控制台渲染器。`edge/boards/pb_sbc01_h3/README.md:13`
- Linux 上的 `main` 以 `tokio::main` 运行，调用 `app::run`，失败时打印错误并返回 `ExitCode::FAILURE`。`edge/boards/pb_sbc01_h3/src/main.rs:14`
- 脸部渲染器的 `run` 循环读状态、渲染、休眠 `POLL_INTERVAL_MS`。`edge/boards/pb_sbc01_h3/src/face_console.rs:27`
- `POLL_INTERVAL_MS` 为 250。`edge/boards/pb_sbc01_h3/src/face_console.rs:11`
- `readState` 从状态文件读文本并解码为 `PbSbc01H3FaceStateFile`。`edge/boards/pb_sbc01_h3/src/face_console.rs:69`
- `readState` 读文件失败时返回 read robot face state failed 错误。`edge/boards/pb_sbc01_h3/src/face_console.rs:71`
- `renderState` 把机器人脸部状态渲染到活动终端显示。`edge/boards/pb_sbc01_h3/src/face_console.rs:77`
- `renderState` 先清屏再打印眼睛与嘴巴的 ASCII 框。`edge/boards/pb_sbc01_h3/src/face_console.rs:79`
- `renderState` 打印 PB_SBC01_H3 与当前 expression。`edge/boards/pb_sbc01_h3/src/face_console.rs:82`
- `faceGlyph` 为 neutral、booting、online、listening、thinking 各选一个 `FaceGlyph`。`edge/boards/pb_sbc01_h3/src/face_console.rs:94`
- `faceGlyph` 为 speaking、happy、sleeping、error 各选一个 `FaceGlyph`。`edge/boards/pb_sbc01_h3/src/face_console.rs:97`
- 不支持的表情返回 unsupported robot face expression 错误。`edge/boards/pb_sbc01_h3/src/face_console.rs:103`
- `FaceGlyph` 只有 eyes 与 mouth 两个字段。`edge/boards/pb_sbc01_h3/src/face_console.rs:109`
- `faceUsage` 给出 `operit-pb-sbc01-h3-face --state-file <path>` 用法。`edge/boards/pb_sbc01_h3/src/face_console.rs:122`

### 板级目录、hosts/linux、sdk/node、sdk/proxy 四处边界如何分工

- `edge/boards/pb_sbc01_h3` 拥有完整 Core 启动与 PB_SBC01_H3 进程编排。`edge/boards/pb_sbc01_h3/README.md:37`
- `hosts/linux` 拥有 Linux 平台 Host API 实现。`edge/boards/pb_sbc01_h3/README.md:38`
- `edge/boards/pb_sbc01_h3/board` 拥有 PB_SBC01_H3 板级 Host API 表面。`edge/boards/pb_sbc01_h3/README.md:39`
- `edge/sdk/node` 拥有类型化板级服务分发边界，见 [[edge-sdk-node|Edge 节点 crate]]。`edge/boards/pb_sbc01_h3/README.md:40`
- `edge/sdk/proxy` 拥有来自 PB_SBC01_H3 代码的类型化板级服务调用，见 [[edge-sdk-proxy|Edge 代理 crate]]。`edge/boards/pb_sbc01_h3/README.md:41`
- 板级 crate 不拥有 Operit Core 启动、Access 配对、Link 包或应用命令路由。`edge/boards/pb_sbc01_h3/board/README.md:9`
- 首个已实现表面是 `RobotFaceHost`，写入经校验的表情状态供本地脸部渲染进程使用。`edge/boards/pb_sbc01_h3/board/README.md:6`
- `installIntoHostManager` 把板级能力加入 Linux `HostManager`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:66`
- `installIntoHostManager` 经 `withRobotFaceHost` 注册机器人脸部宿主。`edge/boards/pb_sbc01_h3/board/src/lib.rs:68`
- `installIntoHostManager` 经 `withHostEnvironment` 注册 `pbSbc01H3HostEnvironment`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:69`
- `createBoardProxy` 以 `createDeviceIoService` 创建 `EdgeNode` 并挂 `withRobotFaceService`。`edge/boards/pb_sbc01_h3/src/app.rs:75`
- `createBoardProxy` 返回 `EdgeProxy::new(node)`。`edge/boards/pb_sbc01_h3/src/app.rs:77`
- `createPbSbc01H3HostManager` 以 `config.runtimeRoot`、`config.workspaceRoot` 与 `LinuxWebVisitHost` 调用 `createRuntimeHostManager`。`edge/boards/pb_sbc01_h3/src/app.rs:65`
- `createPbSbc01H3HostManager` 经 `board.installIntoHostManager` 把板级能力装入 `HostManager`。`edge/boards/pb_sbc01_h3/src/app.rs:69`

### 机器人脸部状态文件写在哪里

- 默认路径为 `$HOME/.local/share/operit2/pb_sbc01_h3/state/robot_face_state.json`。`edge/boards/pb_sbc01_h3/README.md:25`
- `defaultDataRoot` 返回当前 Linux 用户 HOME 下的 .local/share/operit2/pb_sbc01_h3。`edge/boards/pb_sbc01_h3/src/config.rs:69`
- 默认 `runtimeRoot`、`workspaceRoot`、`stateRoot` 分别为 dataRoot 下的 runtime、workspace、state 子目录。`edge/boards/pb_sbc01_h3/src/config.rs:24`
- `PB_SBC01_H3_FACE_STATE_FILE` 为 robot_face_state.json。`edge/boards/pb_sbc01_h3/board/src/lib.rs:18`
- `PbSbc01H3RobotFaceHost` 的 `new` 创建状态目录。`edge/boards/pb_sbc01_h3/board/src/lib.rs:114`
- `PbSbc01H3RobotFaceHost` 的 `new` 把状态路径定为状态目录下的 `PB_SBC01_H3_FACE_STATE_FILE`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:115`
- `PbSbc01H3RobotFaceHost` 的 `new` 以 `INITIAL_EXPRESSION` 写入初始状态文件。`edge/boards/pb_sbc01_h3/board/src/lib.rs:115`
- `INITIAL_EXPRESSION` 为 neutral。`edge/boards/pb_sbc01_h3/board/src/lib.rs:20`
- `setExpression` 先校验表情再写状态文件。`edge/boards/pb_sbc01_h3/board/src/lib.rs:134`
- `setExpression` 写文件后更新内存中的当前状态。`edge/boards/pb_sbc01_h3/board/src/lib.rs:139`
- `getExpression` 返回板级宿主已提交的当前表情。`edge/boards/pb_sbc01_h3/board/src/lib.rs:149`
- `PbSbc01H3FaceStateFile` 有 `boardId`、`expression`、`updatedAtUnixMillis` 三个字段。`edge/boards/pb_sbc01_h3/board/src/lib.rs:160`
- `writeFaceState` 把 `boardId` 写为 `PB_SBC01_H3_BOARD_ID`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:168`
- `writeFaceState` 的 `updatedAtUnixMillis` 来自 `currentUnixMillis`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:170`
- `writeFaceState` 以 `serde_json::to_vec_pretty` 序列化状态文件。`edge/boards/pb_sbc01_h3/board/src/lib.rs:171`
- `currentUnixMillis` 返回当前 Unix 时间戳毫秒数。`edge/boards/pb_sbc01_h3/board/src/lib.rs:178`
- `validateExpression` 拒绝 `SUPPORTED_EXPRESSIONS` 之外的表情。`edge/boards/pb_sbc01_h3/board/src/lib.rs:187`
- `SUPPORTED_EXPRESSIONS` 包含 neutral、booting、online、listening、thinking。`edge/boards/pb_sbc01_h3/board/src/lib.rs:22`
- `SUPPORTED_EXPRESSIONS` 包含 speaking、happy、sleeping、error。`edge/boards/pb_sbc01_h3/board/src/lib.rs:26`
- 启动后打印 `board.robotFaceStatePath()` 给出的脸部状态文件路径。`edge/boards/pb_sbc01_h3/src/app.rs:56`
- `robotFaceStatePath` 返回供显示渲染器消费的机器人脸部状态文件路径。`edge/boards/pb_sbc01_h3/board/src/lib.rs:73`
- 脸部渲染器以 `--state-file` 参数接收状态文件路径。`edge/boards/pb_sbc01_h3/README.md:32`
- `parseStateFile` 解析脸部渲染器的 --state-file 参数。`edge/boards/pb_sbc01_h3/src/face_console.rs:40`
- `--state-file` 缺失时返回 --state-file is required 错误。`edge/boards/pb_sbc01_h3/src/face_console.rs:55`

### 启动顺序与配置

- `run` 先以 `PbSbc01H3Config::parse` 解析命令行参数。`edge/boards/pb_sbc01_h3/src/app.rs:18`
- `run` 以 `PbSbc01H3BoardConfig` 包装 `config.stateRoot` 创建 `PbSbc01H3Board`。`edge/boards/pb_sbc01_h3/src/app.rs:19`
- `run` 以 `createPbSbc01H3HostManager` 创建带板级能力接入的 Linux `HostManager`。`edge/boards/pb_sbc01_h3/src/app.rs:21`
- `run` 以 `createBoardProxy` 创建供 PB_SBC01_H3 本地服务使用的类型化板级代理。`edge/boards/pb_sbc01_h3/src/app.rs:22`
- Core 启动前 `boardProxy` 的 `setExpression` 把表情设为 booting。`edge/boards/pb_sbc01_h3/src/app.rs:25`
- run 以 `CoreApplication::start` 启动 Core。`edge/boards/pb_sbc01_h3/src/app.rs:29`
- `LinkDeviceInfo` 的 platform 为 pb_sbc01_h3。`edge/boards/pb_sbc01_h3/src/app.rs:32`
- `LinkDeviceInfo` 的 model 为 `PB_SBC01_H3_BOARD_ID`。`edge/boards/pb_sbc01_h3/src/app.rs:33`
- `run` 以 `core.nodeRuntime().runtimeStorageHost()` 创建 `PeerStateStore`。`edge/boards/pb_sbc01_h3/src/app.rs:40`
- 监听配置缺失时 `run` 返回 Node listener preferences are not initialized 错误。`edge/boards/pb_sbc01_h3/src/app.rs:41`
- 给出 --bind 时 `listenerConfig.bindAddress` 被命令行值覆盖。`edge/boards/pb_sbc01_h3/src/app.rs:43`
- 给出 --bind 时，解析覆盖后的 `bindAddress` 端口，端口为 0 时 `portMode` 为 Automatic，否则为 Fixed。`edge/boards/pb_sbc01_h3/src/app.rs:46`
- 覆盖后的监听配置经 `store.saveHostConfig` 保存。`edge/boards/pb_sbc01_h3/src/app.rs:50`
- `run` 以 `PeerTransport::Http` 调用 `core.accessServices().startListening` 启动监听。`edge/boards/pb_sbc01_h3/src/app.rs:52`
- 监听启动后 `boardProxy` 的 `setExpression` 把表情设为 online。`edge/boards/pb_sbc01_h3/src/app.rs:54`
- 启动后打印监听地址与 `core.deviceInfo().displayName()`。`edge/boards/pb_sbc01_h3/src/app.rs:55`
- run 等待 Ctrl-C 后调用 `core.shutdown()`。`edge/boards/pb_sbc01_h3/src/app.rs:57`
- `PbSbc01H3Config` 携带 `bindAddress`、`runtimeRoot`、`workspaceRoot`、`stateRoot` 四个字段。`edge/boards/pb_sbc01_h3/src/config.rs:10`
- `PbSbc01H3Config` 的 `parse` 从命令行参数解析控制器设置。`edge/boards/pb_sbc01_h3/src/config.rs:18`
- `--bind` 设置 `bindAddress`。`edge/boards/pb_sbc01_h3/src/config.rs:31`
- `--runtime-root` 设置 `runtimeRoot`。`edge/boards/pb_sbc01_h3/src/config.rs:32`
- `--workspace-root` 设置 `workspaceRoot`。`edge/boards/pb_sbc01_h3/src/config.rs:35`
- `--state-root` 设置 `stateRoot`。`edge/boards/pb_sbc01_h3/src/config.rs:38`
- `--help` 或 `-h` 返回 `usage()` 错误。`edge/boards/pb_sbc01_h3/src/config.rs:41`
- 未知参数返回 unknown PB_SBC01_H3 argument 错误。`edge/boards/pb_sbc01_h3/src/config.rs:42`
- HOME 缺失时 `defaultDataRoot` 返回 HOME is required for PB_SBC01_H3 data directories 错误。`edge/boards/pb_sbc01_h3/src/config.rs:68`
- `usage` 给出 operit-pb-sbc01-h3 的命令行用法。`edge/boards/pb_sbc01_h3/src/config.rs:79`

### 环境描述符与入门要求

- `pbSbc01H3HostEnvironment` 以 `HostEnvironmentDescriptor::linux()` 构建描述符。`edge/boards/pb_sbc01_h3/board/src/lib.rs:80`
- 环境描述符 id 为 pb_sbc01_h3。`edge/boards/pb_sbc01_h3/board/src/lib.rs:81`
- 环境描述符 displayName 为 `PB_SBC01_H3_BOARD_DISPLAY_NAME`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:82`
- 环境描述符 capabilities 包含 robot.face。`edge/boards/pb_sbc01_h3/board/src/lib.rs:83`
- robot.face 结构化能力的 scope 为 Device，operations 为 Read 与 Write。`edge/boards/pb_sbc01_h3/board/src/lib.rs:87`
- 入门要求 id 为 board.pb_sbc01_h3.face，isRequired 为 true。`edge/boards/pb_sbc01_h3/board/src/lib.rs:93`
- 入门要求 status 为 Missing，action 为 HostManaged。`edge/boards/pb_sbc01_h3/board/src/lib.rs:98`

## 关键符号

- `PB_SBC01_H3_BOARD_ID` — 板级标识，值为 PB_SBC01_H3。`edge/boards/pb_sbc01_h3/board/src/lib.rs:16`
- `PB_SBC01_H3_BOARD_DISPLAY_NAME` — 板级显示名，值为 PB_SBC01_H3。`edge/boards/pb_sbc01_h3/board/src/lib.rs:17`
- `PB_SBC01_H3_FACE_STATE_FILE` — 脸部状态文件名 robot_face_state.json。`edge/boards/pb_sbc01_h3/board/src/lib.rs:18`
- `INITIAL_EXPRESSION` — 初始表情 neutral。`edge/boards/pb_sbc01_h3/board/src/lib.rs:20`
- `SUPPORTED_EXPRESSIONS` — 9 种受支持表情的列表。`edge/boards/pb_sbc01_h3/board/src/lib.rs:21`
- `PbSbc01H3BoardConfig` — 板级配置，只含 `stateDirectory`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:35`
- `PbSbc01H3Board` — 板级 profile，持有 `Arc<PbSbc01H3RobotFaceHost>` 类型的 `robotFaceHost`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:49`
- `PbSbc01H3RobotFaceHost` — 板级机器人脸部宿主，持有 `statePath` 与 `Mutex<RobotFaceState>` 类型的 `state`。`edge/boards/pb_sbc01_h3/board/src/lib.rs:105`
- `PbSbc01H3FaceStateFile` — 脸部状态文件格式。`edge/boards/pb_sbc01_h3/board/src/lib.rs:159`
- `FaceGlyph` — 一个 ASCII 机器人脸部字形，只有 `eyes` 与 `mouth`。`edge/boards/pb_sbc01_h3/src/face_console.rs:108`
- `POLL_INTERVAL_MS` — 脸部渲染器轮询间隔，250 毫秒。`edge/boards/pb_sbc01_h3/src/face_console.rs:11`
- `run` — app.rs 中的控制器主流程。`edge/boards/pb_sbc01_h3/src/app.rs:17`
- `PbSbc01H3Config` — 控制器命令行配置。`edge/boards/pb_sbc01_h3/src/config.rs:9`
- `CoreApplication` — 以 `CoreApplication::start` 启动完整 Core。`edge/boards/pb_sbc01_h3/src/app.rs:29`
- `LinkDeviceInfo` — 设备信息，platform 为 pb_sbc01_h3。`edge/boards/pb_sbc01_h3/src/app.rs:31`
- `PeerStateStore` — 监听配置存储。`edge/boards/pb_sbc01_h3/src/app.rs:40`
- `EdgeProxy<EdgeNode>` — 类型化板级代理。`edge/boards/pb_sbc01_h3/src/app.rs:74`
- `pbSbc01H3HostEnvironment` — 板级 Linux 环境描述符。`edge/boards/pb_sbc01_h3/board/src/lib.rs:79`
- `RobotFaceHost` — 板级实现的 Host API 表面。`edge/boards/pb_sbc01_h3/board/src/lib.rs:132`

## 调用链

1. Linux 上的 `main` 调用 `app::run`。`edge/boards/pb_sbc01_h3/src/main.rs:15`
2. `run` 以 `PbSbc01H3Config::parse` 解析命令行参数。`edge/boards/pb_sbc01_h3/src/app.rs:18`
3. `run` 以 `PbSbc01H3BoardConfig` 创建 `PbSbc01H3Board`。`edge/boards/pb_sbc01_h3/src/app.rs:19`
4. `PbSbc01H3Board` 的 `new` 初始化 `PbSbc01H3RobotFaceHost`，后者创建状态目录并写入初始 neutral 状态文件。`edge/boards/pb_sbc01_h3/board/src/lib.rs:56`
5. `createPbSbc01H3HostManager` 创建 Linux `HostManager` 并装入板级能力。`edge/boards/pb_sbc01_h3/src/app.rs:21`
6. `createBoardProxy` 创建类型化板级代理。`edge/boards/pb_sbc01_h3/src/app.rs:22`
7. `boardProxy` 的 `setExpression` 把表情设为 booting。`edge/boards/pb_sbc01_h3/src/app.rs:25`
8. `CoreApplication::start` 启动完整 Core。`edge/boards/pb_sbc01_h3/src/app.rs:29`
9. `run` 以 `core.nodeRuntime().runtimeStorageHost()` 创建 `PeerStateStore`。`edge/boards/pb_sbc01_h3/src/app.rs:40`
10. 给出 --bind 时监听地址被覆盖，同一 --bind 值的端口为 0 时 `portMode` 为 Automatic。`edge/boards/pb_sbc01_h3/src/app.rs:43`
11. 覆盖后的监听配置经 `store.saveHostConfig` 保存。`edge/boards/pb_sbc01_h3/src/app.rs:50`
12. `core.accessServices().startListening` 以 `PeerTransport::Http` 启动监听。`edge/boards/pb_sbc01_h3/src/app.rs:52`
13. `boardProxy` 的 `setExpression` 把表情设为 online。`edge/boards/pb_sbc01_h3/src/app.rs:54`
14. 控制器打印监听地址与设备显示名。`edge/boards/pb_sbc01_h3/src/app.rs:55`
15. 控制器打印脸部状态文件路径。`edge/boards/pb_sbc01_h3/src/app.rs:56`
16. run 等待 Ctrl-C 后调用 `core.shutdown()`。`edge/boards/pb_sbc01_h3/src/app.rs:57`
17. 脸部渲染器循环读状态文件并渲染到终端。`edge/boards/pb_sbc01_h3/src/face_console.rs:27`

## 来源

- `edge/boards/pb_sbc01_h3/README.md`：产品说明、二进制与边界分工，全文 41 行。
- `edge/boards/pb_sbc01_h3/board/README.md`：板级 crate 说明，全文 10 行。
- `edge/boards/pb_sbc01_h3/src/main.rs`：控制器入口，Linux 与非 Linux 分支，全文 29 行。
- `edge/boards/pb_sbc01_h3/src/app.rs`：控制器主流程、HostManager 与板级代理创建，全文 78 行。
- `edge/boards/pb_sbc01_h3/src/config.rs`：控制器命令行配置，全文 83 行。
- `edge/boards/pb_sbc01_h3/src/face_console.rs`：脸部控制台渲染器，全文 123 行。
- `edge/boards/pb_sbc01_h3/board/src/lib.rs`：板级 profile、机器人脸部宿主与状态文件格式，全文 246 行。

否定性核验方法：2026-11-12 对基线 AAswordman/Operit2 @ 364d1d594 的本地 checkout 执行 `grep -rn "setExpression" edge/boards/pb_sbc01_h3/README.md edge/boards/pb_sbc01_h3/board/README.md edge/boards/pb_sbc01_h3/src/main.rs edge/boards/pb_sbc01_h3/src/app.rs edge/boards/pb_sbc01_h3/src/config.rs edge/boards/pb_sbc01_h3/src/face_console.rs edge/boards/pb_sbc01_h3/board/src/lib.rs`，命中 5 处：`src/app.rs:25`（booting）、`src/app.rs:54`（online）、`board/src/lib.rs:134`（定义）、`board/src/lib.rs:216` 与 `:237`（测试）；因此本页只写控制器在启动前设 booting、监听启动后设 online，不写其他表情切换点。

否定性核验方法（续）：同日同基线执行 `grep -rn "withRobotFaceHost\|withHostEnvironment" edge/boards/pb_sbc01_h3/board/src/lib.rs`，唯一命中为 `board/src/lib.rs:68` 与 `:69`；`installIntoHostManager` 除机器人脸部宿主外只注册环境描述符，不注册第二个板级能力。

范围说明：控制器只在 Linux 上启动；脸部渲染器本身无平台门控，但其状态文件由 Linux 控制器写出。`edge/boards/pb_sbc01_h3/src/main.rs:27`

未读文件：本页只读 7 个 seed 文件；`edge/boards/pb_sbc01_h3/Cargo.toml` 与引用的共享 crate（`operit_link`、`operit_node_runtime`、`operit_core_application`、`operit_host_api`、`operit_host_linux_native`、`operit_node_edge`、`operit_proxy_edge`）未读未引。
