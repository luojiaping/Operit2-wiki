---
title: ESP32 编辑器与调试工具
module: edge
platforms: [all]
sources: 4
date: 2026-11-11
---

## 概述

- edge/boards/esp32/editor/ 目录提供四项能力：共享 C/Wasm UI 预览、Rust Edge 模拟器、固件构建和真机调试。`edge/boards/esp32/editor/README.md:3`
- 运行需要支持 `--experimental-strip-types` 的 Node.js 22.6+（推荐 24）和桌面 Rust/Cargo。`edge/boards/esp32/editor/README.md:10`
- 预览构建还需要 Emscripten，完整固件构建需要 ESP Rust / ESP-IDF 工具链。`edge/boards/esp32/editor/README.md:11`
- 本地服务默认地址是 `http://127.0.0.1:8766`，首次启动前需要先构建，构建产物放在被 Git 忽略的 `generated/` 下。`edge/boards/esp32/editor/README.md:19`
- 设备系统 UI 和浏览器预览共同编译同一份 C 实现，逻辑屏幕为 320×240。`edge/boards/esp32/editor/FRONTEND.md:3`
- 本页是 Edge 产品线的开发工具页，Edge 整体定位见 [[edge-overview|Edge 总览与产品形态]]。

## AI 速览

- `operit_mini_ui.c` — 设备系统 UI 的 C 实现，浏览器预览与真机共用。`edge/boards/esp32/editor/FRONTEND.md:3`
- `operit_ui_*` — C ABI，更新状态、接收触摸并输出 RGB565 像素。`edge/boards/esp32/editor/FRONTEND.md:4`
- `server.mts` — 本地 HTTP 服务与静态路由。`edge/boards/esp32/editor/FRONTEND.md:23`
- simulator — Rust Edge 模拟器，默认 TCP 监听 `0.0.0.0:18765`。`edge/boards/esp32/editor/simulator/src/main.rs:156`
- `device_space_ui` — 固件设备空间控制器模块，模拟器直接编译。`edge/boards/esp32/editor/simulator/src/main.rs:6`
- `standalone_chat` — 固件独立聊天模块，模拟器直接编译。`edge/boards/esp32/editor/simulator/src/main.rs:26`
- `PeerRuntimeLimits` — 模拟器与真机共用的运行限制，消息帧上限 8 KiB。`edge/boards/esp32/editor/README.md:176`
- `OPERIT_SIM_BIND` — 指定模拟器监听地址。`edge/boards/esp32/editor/README.md:45`
- `OPERIT_SIM_DISCOVERY` — 设为 `false` 可隔离 mDNS 发现测试。`edge/boards/esp32/editor/README.md:44`
- `device-debug.py` — 真机 USB 调试脚本。`edge/boards/esp32/editor/AGENT_API.md:62`
- 主入口（预览）：`npm start --prefix edge/boards/esp32/editor` 启动本地服务。`edge/boards/esp32/editor/README.md:16`
- 主入口（真机）：`npm run dev` 构建固件、烧录并输出串口日志。`edge/boards/esp32/editor/README.md:119`
- 数据流向：浏览器 C/Wasm 界面轮询 `/api/simulator/state`，操作后主动刷新。`edge/boards/esp32/editor/README.md:49`
- 数据流向：Rust 模拟器是真实 Edge 进程，默认 TCP 监听 `0.0.0.0:18765`，共享 Peer runtime 完成验证码配对、加密连接和空间审批。`edge/boards/esp32/editor/README.md:41`

## 核心机制

- 共享 C/Wasm UI 预览：设备系统 UI 和浏览器预览共同编译 `edge/boards/esp32/ui_port/operit_mini_ui.c`，通过 `operit_ui_*` C ABI 更新状态、接收触摸并输出 RGB565 像素。`edge/boards/esp32/editor/FRONTEND.md:3`
- 逻辑屏幕为 320×240，页面、控件位置、文字和动作由 C 实现，状态与设备命令由 Rust 适配。`edge/boards/esp32/editor/FRONTEND.md:5`
- Rust Edge 模拟器：网页启动真实 Rust Edge 进程，默认 TCP 监听 `0.0.0.0:18765`。`edge/boards/esp32/editor/README.md:36`
- 模拟器复用固件的设备空间控制器、独立聊天、远端聊天和原生服务模块。`edge/boards/esp32/editor/README.md:40`
- 模拟器使用共享 Peer runtime 完成验证码配对、加密连接和空间审批。`edge/boards/esp32/editor/README.md:41`
- 配对可从 Core 发起并在设备上批准加入，也可使用设备「设置 → 设备空间」从设备发起。`edge/boards/esp32/editor/README.md:42`
- 模拟器源码用 #[path] 直接引用固件模块编译，例如 `device_space_ui`。`edge/boards/esp32/editor/simulator/src/main.rs:6`
- 模拟器源码用 #[path] 直接引用固件的 `standalone_chat` 模块参与编译。`edge/boards/esp32/editor/simulator/src/main.rs:26`
- 固件构建：`npm run dev` 一条命令完成构建固件/预览、烧录、串口日志；`npm run flash` 只更新已有固件，不重新构建。`edge/boards/esp32/editor/README.md:119`
- 真机调试：USB 读屏使用 `npm run device:screen`、`device:tree`、`device:tap`，不需要常驻 HTTP server。`edge/boards/esp32/editor/AGENT_API.md:59`
- 读屏返回的 `source: "device-uart"` 表示内容来自物理设备当前 C 渲染器。`edge/boards/esp32/editor/AGENT_API.md:69`
- Web TypeScript / CSS 修改后刷新网页生效。`edge/boards/esp32/editor/README.md:26`
- 共享 C UI / 表情 SVG 修改后执行 `npm run build` 再刷新网页；真机另需构建和更新固件。`edge/boards/esp32/editor/README.md:27`
- Rust 模拟器 / 共享固件模块修改后，停止并启动模拟设备，Cargo 重新检查并编译。`edge/boards/esp32/editor/README.md:28`
- 设备配置和场景素材使用设备原生接口保存，无需修改固件。`edge/boards/esp32/editor/README.md:29`
- 刷新网页不等于重启 Rust 进程。`edge/boards/esp32/editor/README.md:31`
- 系统页面直接修改 `edge/boards/esp32/ui_port/operit_mini_ui.c`，状态与动作使用固件 Rust 模块；不要另写一套 Web 页面来模拟设备控件。`edge/boards/esp32/editor/README.md:31`
- 仅网页或预览修改可使用预览构建；系统页面和设备原生能力变更需要固件构建。`edge/boards/esp32/editor/AGENT_API.md:50`
- 网页 CSS 只改变调试台外观；Canvas 显示 C/Wasm 的输出，不能通过网页样式改变设备控件。`edge/boards/esp32/editor/FRONTEND.md:29`
- 保持 320×240 逻辑坐标；网页缩放只改变显示尺寸。`edge/boards/esp32/editor/FRONTEND.md:67`
- 新增前端模块时同步注册 `src/server.mts` 的静态路由。`edge/boards/esp32/editor/FRONTEND.md:30`
- 软件可在加载 app.js 前注入 `window.operitHost` 请求桥接。`edge/boards/esp32/editor/FRONTEND.md:38`
- `web/transport.ts` 使用这个桥接入口处理 `/api/board`、`/api/build` 等 JSON 请求；模拟器面板和图片发送还使用直接 fetch。`edge/boards/esp32/editor/FRONTEND.md:47`
- WebView 需要能加载前端文件、`generated/manifest.json`、`generated/ui.mjs` 和 `generated/ui.wasm`；Wasm 的 MIME 类型为 `application/wasm`。`edge/boards/esp32/editor/FRONTEND.md:50`
- `GET` `/api/board` 查询预览板型、尺寸与系统 UI 能力。`edge/boards/esp32/editor/AGENT_API.md:19`
- `GET` `/api/build` 查询构建状态、清单与源码是否变化；`POST` `/api/build` 构建浏览器预览和固件，不烧录。`edge/boards/esp32/editor/AGENT_API.md:20`
- `POST` `/api/simulator/start` 启动 Rust 模拟设备；`POST` `/api/simulator/stop` 停止。`edge/boards/esp32/editor/AGENT_API.md:23`
- `GET` `/api/simulator/memory` 查询模拟设备的资源限制。`edge/boards/esp32/editor/AGENT_API.md:25`
- `GET` `/api/simulator/debug/snapshot` 读取浏览器中当前 C/Wasm UI 的结构化屏幕状态。`edge/boards/esp32/editor/AGENT_API.md:27`
- `POST` `/api/simulator/send` 使用 `{text}` 向模拟设备的当前对话发送文字。`edge/boards/esp32/editor/AGENT_API.md:30`
- `/api/simulator/debug/*` 需要浏览器预览页面保持打开，命令由实际 C/Wasm 实例执行；不读取物理设备，也不由 Rust 模拟器构造另一套 UI 树。`edge/boards/esp32/editor/AGENT_API.md:35`
- `GET /api/deploy/ports` 查询串口；`POST /api/deploy/flash` 使用 `{port}` 安装已构建固件，不启动编译。`edge/boards/esp32/editor/FRONTEND.md:74`
- Core 上的 JS/TS 插件使用 `Tools.device(nodeId).Edge` 调用设备能力。`edge/boards/esp32/editor/AGENT_API.md:8`
- 可选 `edge.scene` 服务支持像素素材、本地动画和事件。`edge/boards/esp32/editor/AGENT_API.md:9`
- 模拟器不执行 ESP32 指令集，不模拟无线电、SPI 时序或整板 RAM。`edge/boards/esp32/editor/README.md:55`
- 模拟器屏幕来自实际 C 渲染器，资源限制来自应用注入，实际堆和 NVS 必须读取真机遥测。`edge/boards/esp32/editor/README.md:56`
- 每次 Rust 启动有独立 `sessionId`，发送回执通过本地 `sendId` 去重；这些 ID 不进入公共 Link 协议。`edge/boards/esp32/editor/README.md:52`
- 网页与 Rust 是两个运行时：C/Wasm 拥有导航、绘制、滚动和输入草稿，Rust 拥有设备会话和数据状态。`edge/boards/esp32/editor/README.md:48`
- IPC 只服务本机调试，不替代节点间 Link。`edge/boards/esp32/editor/README.md:50`
- mDNS 使用共享 Host 服务；隔离测试可设置 `OPERIT_SIM_DISCOVERY=false`。`edge/boards/esp32/editor/README.md:44`
- `OPERIT_SIM_BIND` 指定监听地址，`OPERIT_SIM_ADVERTISE` 指定对外展示的 IP。`edge/boards/esp32/editor/README.md:45`
- 仅绑定 `127.0.0.1` 时只能进行本机直连测试。`edge/boards/esp32/editor/README.md:46`
- 模拟器与真机都使用 `PeerRuntimeLimits::constrained()`：消息帧上限 8 KiB，入站会话/待配对各 2 个、并发探测 1 个。`edge/boards/esp32/editor/README.md:176`
- Rust 使用固定的 256 KiB arena；主任务 16 KiB、异步 worker 24 KiB、阻塞 worker 20 KiB。`edge/boards/esp32/editor/README.md:178`
- 模拟器复用固件的 7,000 字节快照限制、压缩记录和双 bank 提交流程。`edge/boards/esp32/editor/README.md:194`
- `/api/simulator/memory` 报告 `enforced-budgets`，包括 Rust 实际使用量、空闲量、峰值和分配失败次数。`edge/boards/esp32/editor/README.md:184`
- 浏览器完整草稿最多 16384 UTF-8 字节，C 渲染器只保留最多 511 字节预览。`edge/boards/esp32/editor/README.md:236`
- 远端消息超过 2048 字节时，Edge 通过现有 Link Push / ReverseStream 向 Core 的 `sendUserMessageStream` 逐块传送，单块最多 2048 UTF-8 字节。`edge/boards/esp32/editor/README.md:238`
- 模拟器注册应用自有的 `operit.device.speech` Watch / Push 示例协议，可连接语音处理插件。`edge/boards/esp32/editor/README.md:219`
- 读屏 `result` 包含页面、节点 ID、文本、坐标、可点击与可用状态，以及配对码和 UI 静态内存。`edge/boards/esp32/editor/AGENT_API.md:70`
- 读屏返回的是结构化屏幕内容，不是像素截图或整板 RAM 测量。`edge/boards/esp32/editor/AGENT_API.md:71`
- 点击通过真实触摸/事件入口执行。`edge/boards/esp32/editor/AGENT_API.md:73`
- 调试命令与 Link 复用 `UART0`，在 UI 主线程执行；队列单飞，帧有长度限制和 CRC。`edge/boards/esp32/editor/AGENT_API.md:74`
- USB 调试不代替配对或空间审批。`edge/boards/esp32/editor/AGENT_API.md:75`
- 串口一次只能由一个程序占用：先结束 monitor 或 CLI 常驻串口 session 再读屏。`edge/boards/esp32/editor/AGENT_API.md:77`
- 读屏和点击不主动复位设备；点击超时后先读屏确认状态，避免重复执行动作。`edge/boards/esp32/editor/AGENT_API.md:79`

## 关键符号

- `operit_mini_ui.c` — 设备系统 UI 的 C 实现，浏览器预览与真机共用。`edge/boards/esp32/editor/FRONTEND.md:3`
- `operit_ui_*` — C ABI，更新状态、接收触摸并输出 RGB565 像素。`edge/boards/esp32/editor/FRONTEND.md:4`
- `device_space_ui` — 固件设备空间控制器模块，模拟器直接编译。`edge/boards/esp32/editor/simulator/src/main.rs:6`
- `standalone_chat` — 固件独立聊天模块，模拟器直接编译。`edge/boards/esp32/editor/simulator/src/main.rs:26`
- `edge_chat` — 固件远端聊天模块，模拟器直接编译。`edge/boards/esp32/editor/simulator/src/main.rs:13`
- `PeerRuntimeLimits` — 模拟器与真机共用的运行限制，消息帧上限 8 KiB。`edge/boards/esp32/editor/README.md:176`
- `OPERIT_SIM_BIND` — 指定模拟器监听地址。`edge/boards/esp32/editor/README.md:45`
- `OPERIT_SIM_DISCOVERY` — 设为 `false` 可隔离 mDNS 发现测试。`edge/boards/esp32/editor/README.md:44`
- `window.operitHost` — 软件宿主注入的请求桥接入口。`edge/boards/esp32/editor/FRONTEND.md:38`
- `device-debug.py` — 真机 USB 调试脚本。`edge/boards/esp32/editor/AGENT_API.md:62`
- `device.local.json` — 本机配置，只包含 SDK 路径和可选串口，不保存令牌。`edge/boards/esp32/editor/README.md:139`

## 调用链

1. 执行 `npm install --prefix edge/boards/esp32/editor` 安装依赖。`edge/boards/esp32/editor/README.md:14`
2. 执行 `npm run build --prefix edge/boards/esp32/editor` 构建预览。`edge/boards/esp32/editor/README.md:15`
3. 执行 `npm start --prefix edge/boards/esp32/editor` 启动本地服务。`edge/boards/esp32/editor/README.md:16`
4. 打开 `http://127.0.0.1:8766` 进入调试台。`edge/boards/esp32/editor/README.md:19`
5. 在网页启动 Rust 模拟设备，模拟器默认 TCP 监听 `0.0.0.0:18765`。`edge/boards/esp32/editor/README.md:36`
6. 网页轮询 `/api/simulator/state` 获取模拟设备状态、TCP 地址与日志。`edge/boards/esp32/editor/AGENT_API.md:22`
7. 配对码由共享 C/Wasm 屏幕显示。`edge/boards/esp32/editor/README.md:38`
8. 从 Core 发起配对并在设备上批准加入，或使用设备「设置 → 设备空间」从设备发起。`edge/boards/esp32/editor/README.md:42`
9. 读取 `/api/simulator/debug/tree` 获取当前 C/Wasm UI 的节点树。`edge/boards/esp32/editor/AGENT_API.md:26`
10. 使用 `/api/simulator/debug/tap` 与 `{id}` 点击当前可用控件。`edge/boards/esp32/editor/AGENT_API.md:28`
11. 点击前先读取当前节点 ID；隐藏、禁用或不存在的节点会返回错误。`edge/boards/esp32/editor/AGENT_API.md:37`
12. 真机烧录：`npm run flash` 先擦除完整 `factory` 程序分区再写入，保留 NVS 和 UI 布局。`edge/boards/esp32/editor/README.md:145`
13. 需要清空设备时用 `npm run flash:fresh`，交互终端要求输入 `ERASE`。`edge/boards/esp32/editor/README.md:147`
14. `npm run flash -- --dry-run` 只校验现有产物并输出烧录计划，不连接或修改设备。`edge/boards/esp32/editor/README.md:151`

## 来源

- 本页 seed 文件：`edge/boards/esp32/editor/README.md`（240 行）、`edge/boards/esp32/editor/FRONTEND.md`（77 行）、`edge/boards/esp32/editor/AGENT_API.md`（82 行），基线 AAswordman/Operit2 @ 364d1d594，2026-11-11 全文读完。
- 另核对了模拟器源码 `edge/boards/esp32/editor/simulator/src/main.rs`（848 行）与 C 实现 `edge/boards/esp32/ui_port/operit_mini_ui.c`，确认模拟器直接编译固件模块、屏幕为 320×240 RGB565。
- 本页断言均来自上述文档与源码的说法；未逐项在真机上验证。
- 本页无全仓零命中类断言，无需写核验方法。
