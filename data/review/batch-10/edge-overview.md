---
title: Edge 总览与产品形态
module: edge
platforms: [all]
sources: 1
date: 2026-11-11
---

## 概述

- `edge/` 收纳厂商 SDK、接入文档和完整产品三类东西。`edge/README.md:3`
- 产品形态由厂商决定。`edge/README.md:3`
- 设备空间、配对、加密连接和权限使用 Operit 的共享协议。`edge/README.md:3`
- 厂商接入从 `docs/manufacturer-guide.md` 开始。`edge/README.md:20`
- PB_SBC01_H3 选择运行完整 Core，这是该产品的选择，不是 SDK 的要求。`edge/README.md:20`

## AI 速览

- `sdk` — 手写 Rust SDK，独立 Cargo workspace。`edge/README.md:7`
- `src` — 厂商入口、本地 agent、可选 HTTP 模型适配。`edge/README.md:8`
- `contract` — 设备服务和聊天展示协议。`edge/README.md:9`
- `node` — 设备服务分发和共享 Peer runtime 适配。`edge/README.md:10`
- `proxy` — 手写设备服务客户端。`edge/README.md:11`
- `scene` — 可选的有界场景渲染。`edge/README.md:12`
- `docs` — 接入、架构和验收说明。`edge/README.md:13`
- `esp32` — ESP32 固件、硬件适配、UI、编辑器与真实 Rust 模拟器。`edge/README.md:15`
- `headless_sensor` — 无屏产品：本地 agent、传感器服务、配对与空间加入。`edge/README.md:16`
- `pb_sbc01_h3` — Linux 机器人产品，运行完整 Core。`edge/README.md:17`
- `space` — 提供设备空间接入。`edge/README.md:22`
- `http-agent` — 提供模型工具调用。`edge/README.md:22`
- `scene` — 提供可选显示能力。`edge/README.md:22`
- 主入口：ESP32 完整模拟器验收入口命令是 `EMSDK=/path/to/emsdk npm run test:device-budget --prefix edge/boards/esp32/editor`，从仓库根目录运行。`edge/README.md:37`
- 数据流向：厂商决定产品形态，设备空间、配对、加密连接和权限走 Operit 共享协议。`edge/README.md:3`

## 核心机制

- SDK 默认没有第三方依赖。`edge/README.md:22`
- `space`、`http-agent`、`scene` 分别提供设备空间接入、模型工具调用和可选显示能力。`edge/README.md:22`
- SDK 不要求 SQL、JavaScript、工具包执行器或本地模型引擎。`edge/README.md:22`
- 需要屏幕、独立聊天和设备调试的产品参考 `boards/esp32/README.md`。`edge/README.md:20`
- 无屏网关或传感器参考 `boards/headless_sensor/README.md`。`edge/README.md:20`
- 选择 SDK 功能并创建厂商产品，文档入口是 `docs/manufacturer-guide.md`。`edge/README.md:28`
- 查看 crate 配置和 SDK 检查命令，文档入口是 edge/sdk/README.md，SDK 入口与功能开关见 [[edge-sdk-entry|operit-edge-sdk 入口与功能开关]]。`edge/README.md:29`
- 理解 Edge、Core、Host 和权限的边界，文档入口是 `docs/architecture.md`。`edge/README.md:30`
- 启动 ESP32 预览、模拟器或真机调试，文档入口是 `boards/esp32/editor/README.md`。`edge/README.md:31`
- 查看既有验收的基线、场景和资源测量，文档入口是 `docs/acceptance.md`。`edge/README.md:32`
- Emscripten 与桌面构建环境见 `boards/esp32/editor/README.md`。`edge/README.md:55`
- 验收范围与测量方法见 `docs/acceptance.md`。`edge/README.md:55`
- V1 收尾状态、当前回归结果和真机交付检查见 `docs/v1-closeout.md`。`edge/README.md:57`

## 关键符号

- `esp32` — ESP32 固件、硬件适配、UI、编辑器与真实 Rust 模拟器。`edge/README.md:15`
- `headless_sensor` — 无屏产品：本地 agent、传感器服务、配对与空间加入。`edge/README.md:16`
- `pb_sbc01_h3` — Linux 机器人产品，运行完整 Core。`edge/README.md:17`
- `space` — 提供设备空间接入。`edge/README.md:22`
- `http-agent` — 提供模型工具调用。`edge/README.md:22`
- `scene` — 提供可选显示能力。`edge/README.md:22`
- `EMSDK` — 指向本机 Emscripten SDK 目录的环境变量，运行完整模拟器验收前设置。`edge/README.md:34`

## 调用链

1. 从仓库根目录设置 `EMSDK` 指向本机 Emscripten SDK 目录。`edge/README.md:34`
2. 运行 `EMSDK=/path/to/emsdk npm run test:device-budget --prefix edge/boards/esp32/editor`。`edge/README.md:37`
3. 该入口重建 C/Wasm、Rust 模拟器和本机 CLI，再检查固定堆/栈预算、独立聊天、空间加入、双向消息和重启。`edge/README.md:55`
4. 需要同时检查 ESP32 固件编译、链接和镜像导出时，先设置 `EMSDK` 环境变量并准备好 ESP-IDF 与 Xtensa 工具链，再运行 `npm run test:device-budget --prefix edge/boards/esp32/editor -- --firmware`。`edge/README.md:50`
5. 固件验收还需检查应用分区及 `.flash.text` 映射区余量。`edge/README.md:53`
6. 该命令不执行烧录。`edge/README.md:53`
7. 实际音频、网络与持续运行需要另做真机验收。`edge/README.md:53`
8. Windows PowerShell 下先设置 `$env:EMSDK = 'D:\tools\emsdk'` 再运行同一命令。`edge/README.md:44`

## 来源

- 本页 seed 文件：`edge/README.md`（57 行，基线 AAswordman/Operit2 @ 364d1d594，2026-11-11 全文读完）。
- 本页断言均来自该 README 文档的说法，未逐项在代码层验证；SDK 内部实现细节见 [[edge-sdk-entry|operit-edge-sdk 入口与功能开关]]。
- 本页无全仓零命中类断言，无需写核验方法。
