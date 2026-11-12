---
title: Edge 验收记录与 V1 收尾
module: edge
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

本页记录 Edge 验收与 V1 收尾，验收范围限于实际运行的 CLI、受资源约束的产品模拟器与 SDK 及共享模块回归。`edge/docs/acceptance.md:81`
验收记录的验收基线是 `upstream/main` 的 3c5fcc81653999613328209bd0beafb415949c82。`edge/docs/acceptance.md:3`
V1 收尾记录的首次验收基线是 3d6238a4（main），本轮在 Windows 上收尾 SDK 接入和验收入口。`edge/docs/v1-closeout.md:3`
V1 收尾的 PR 已 rebase 到 06784b03，旧基线结果仅作历史记录。`edge/docs/v1-closeout.md:4`
最新基线的固件容量阻塞已修复，Edge 软件验收通过；真机交付尚未完成。`edge/docs/v1-closeout.md:8`
历史结果不能替代本轮结果，也不能代表当前固件已经烧录。`edge/docs/v1-closeout.md:7`
上述验收基线与大纲基线 364d1d594 不同，本页引用的验收数据以验收记录自身的基线号为准。`edge/docs/acceptance.md:3`

## AI 速览

- ESP32 完整模拟器验收入口命令是 `EMSDK=/path/to/emsdk npm run test:device-budget --prefix edge/boards/esp32/editor`，在仓库根目录执行。`edge/docs/acceptance.md:11`
- 该入口重建预览、模拟器、插件资产和当前 CLI，清理环境变量，避免压力场景被跳过。`edge/docs/acceptance.md:15`
- 该入口任意阶段失败都会终止并返回非零退出码。`edge/docs/acceptance.md:15`
- 验收记录的验收基线是 3c5fcc81653999613328209bd0beafb415949c82。`edge/docs/acceptance.md:3`
- V1 收尾首次基线是 3d6238a4，最新基线复验的 PR 已 rebase 到 06784b03。`edge/docs/v1-closeout.md:4`
- 资源预算：模拟器固定 262,144 字节 Rust 堆，主线程、异步任务与阻塞任务栈分别为 16/24/20 KiB，带保护页。`edge/docs/acceptance.md:32`
- SDK 全功能测试 23 项通过，全部 8 种功能组合依赖审计通过。`edge/docs/v1-closeout.md:48`
- 依赖审计：默认本地 agent 依赖 0 包。`edge/docs/acceptance.md:56`
- 依赖审计：`space` 108 包。`edge/docs/acceptance.md:57`
- 依赖审计：`http-agent` 25 包。`edge/docs/acceptance.md:58`
- 依赖审计：`scene` 41 包。`edge/docs/acceptance.md:59`
- 固件容量阻塞是 `.flash.text` 超限 3,226 字节。`edge/docs/v1-closeout.md:42`
- 三个小型映射改成逐项插入后，代码段减少 8,524 字节。`edge/docs/v1-closeout.md:45`
- 容量余量（最新基线）：factory 应用分区余量 38,384 字节。`edge/docs/v1-closeout.md:75`
- 容量余量（最新基线）：`.flash.text` 映射区余量 5,298 字节。`edge/docs/v1-closeout.md:76`
- CLI 修复：`space sync` 同步 future 独立装箱，修复 Windows 调试版主线程栈溢出。`edge/docs/v1-closeout.md:33`
- 通过范围是实际运行的 macOS CLI 与受资源约束的产品模拟器，以及 SDK 和共享模块回归。`edge/docs/acceptance.md:81`
- 最新基线复验本轮未连接交付板，未执行烧录或真机验收。`edge/docs/v1-closeout.md:92`
- 主入口：ESP32 完整模拟器验收入口 `npm run test:device-budget`，固件构建可并入验收（加 `-- --firmware`）。`edge/docs/v1-closeout.md:91`
- 固件验收加 `-- --firmware` 并检查应用分区及 `.flash.text` 映射区余量；该命令不执行烧录，真机音频、网络与持续运行另行验收。`edge/README.md:53`
- 数据流向：ESP32 完整模拟器验收入口重建 CLI 与模拟器 → 执行配对、聊天、语音、插件场景 → 采样 Rust 堆峰值与分配失败 → 固件链接检查 .flash.text 容量。`edge/docs/acceptance.md:15`

## 核心机制

### ESP32 完整模拟器验收入口覆盖的场景与结果

ESP32 完整模拟器验收入口命令是 `EMSDK=/path/to/emsdk npm run test:device-budget --prefix edge/boards/esp32/editor`，在仓库根目录执行。`edge/docs/acceptance.md:11`
该入口重建预览、模拟器、插件资产和当前 CLI，清理环境变量，避免压力场景被跳过。`edge/docs/acceptance.md:15`
该入口任意阶段失败都会终止并返回非零退出码。`edge/docs/acceptance.md:15`
C/Wasm 预览构建与 TypeScript 检查通过。`edge/docs/acceptance.md:21`
产品共用 Rust 模块 62 项通过。`edge/docs/acceptance.md:22`
编辑器与实际堆/栈边界探针 116 项通过。`edge/docs/acceptance.md:23`
配对、加入空间、持久化与重启通过。`edge/docs/acceptance.md:24`
CLI 退出后的独立流式聊天、连续额外 12 轮、设备重启后聊天通过。`edge/docs/acceptance.md:25`
空间聊天与两边消息互通、完整 UI 操作与恢复通过。`edge/docs/acceptance.md:26`
完整互通场景验证聊天列表、创建和切换会话、历史分页、长 UTF-8 消息跨帧传输、取消、离线取消、退出与重新加入、审批期间存储失败后的恢复，以及重启后的状态恢复。`edge/docs/acceptance.md:29`
语音场景验证 PCM/WAV、较长识别结果、多段 TTS、背压、断开重连；插件场景经过真实 Core JS 处理器和设备服务路由。`edge/docs/acceptance.md:30`
统一验收命令可加 `-- --firmware`，把固件构建并入该次验收。`edge/docs/v1-closeout.md:160`

### 实际资源约束与堆峰值

模拟器启用固定 262,144 字节 Rust 堆，主线程、异步任务与阻塞任务分别使用 16/24/20 KiB 可用栈，并使用保护页检测越界。`edge/docs/acceptance.md:32`
配对、空间接入与重启场景的跨重启最大 Rust 堆峰值是 175,584 / 262,144 字节，采样状态中的分配失败为 0。`edge/docs/acceptance.md:36`
独立聊天、12 轮压力与重启场景的跨重启最大 Rust 堆峰值是 231,224 / 262,144 字节，采样状态中的分配失败为 0。`edge/docs/acceptance.md:37`
双向互通、语音与恢复场景的跨重启最大 Rust 堆峰值是 226,952 / 262,144 字节，采样状态中的分配失败为 0。`edge/docs/acceptance.md:38`
最新基线最后一轮统一验收的 arena 高水位：配对、审批、重启恢复峰值 168,952 / 262,144 字节。`edge/docs/v1-closeout.md:66`
最新基线最后一轮统一验收的 arena 高水位：独立聊天、额外 12 轮、Core 退出、设备重启峰值 225,824 / 262,144 字节。`edge/docs/v1-closeout.md:67`
最新基线最后一轮统一验收的 arena 高水位：远端聊天、存储故障、二进制语音恢复与双向审批峰值 215,608 / 262,144 字节。`edge/docs/v1-closeout.md:68`
单独复验独立聊天时最高采样为 234,920 字节；带代理且回环直连的复验为 226,104 字节。`edge/docs/v1-closeout.md:70`
最新基线所有场景的采样分配失败均为 0；任务栈继续按 16/24/20 KiB 受保护预算验收。`edge/docs/v1-closeout.md:71`
模拟器 Rust arena 不包含 ESP-IDF、Wi-Fi、TLS、C UI 和原生驱动，不能作为整板内存结论。`edge/docs/v1-closeout.md:203`

### SDK 全功能测试与 8 种功能组合依赖审计

SDK workspace 的 23 项测试通过，覆盖设备协议、服务路由、场景渲染、本地 agent 工具闭环、未知工具拒绝、上下文与步数预算，以及 HTTP 模型响应上限和工具结果回传。`edge/docs/acceptance.md:50`
最新基线复验中 SDK 全功能 23 项测试及全部 8 种功能组合依赖审计通过。`edge/docs/v1-closeout.md:48`
首次基线验证中 SDK 依赖边界默认及 `space` / `http-agent` / `scene` 全部 8 种组合通过。`edge/docs/v1-closeout.md:120`
依赖审计中默认本地 agent 的依赖包数是 0。`edge/docs/acceptance.md:56`
依赖审计中 `space` 功能的依赖包数是 108。`edge/docs/acceptance.md:57`
依赖审计中 `http-agent` 功能的依赖包数是 25。`edge/docs/acceptance.md:58`
依赖审计中 `scene` 功能的依赖包数是 41。`edge/docs/acceptance.md:59`
各功能分别检查，组合启用时依赖包数不能直接相加；审计拒绝引入完整 Core 应用运行时、SQL、JavaScript、本地模型引擎和 reqwest。`edge/docs/acceptance.md:61`
无屏产品通过 `--once` 本地工具调用，以及普通启动的真实监听端口、持久身份、状态查询、本地 agent 与正常退出检查；它仅选择 SDK 的 `space`，不引入 ESP32 UI 或 `scene`。`edge/docs/acceptance.md:63`
无屏产品的温度读数是明确标记的桌面演示值，厂商可用自己的 HAL 替换工具。`edge/docs/acceptance.md:63`

### 共享实现回归

共享实现回归中节点运行时与 Peer Link 共 323 项通过。`edge/docs/acceptance.md:75`
共享实现回归中 `node-state` 存储 181 项通过、1 项忽略。`edge/docs/acceptance.md:75`
共享实现回归中调度器普通模式 25 项、ESP32 兼容模式 26 项通过。`edge/docs/acceptance.md:75`
共享实现回归中跨设备类型的协议与空间接入 42 项通过。`edge/docs/acceptance.md:75`
最新基线复验中存储 `node-state` 单元测试 192 项通过，1 项原有压力测试忽略；包含历史审批格式升级回归。`edge/docs/v1-closeout.md:49`
首次基线验证中存储单元测试 `node-state` 190 通过、0 失败；原有 ultra compaction 压力测试 1 项忽略。`edge/docs/v1-closeout.md:121`
最新基线复验中 Preferences 布局与升级 19 项测试通过。`edge/docs/v1-closeout.md:52`
最新基线复验中 Core `device_space` 108 项及同步进度 9 项测试通过。`edge/docs/v1-closeout.md:52`
首次基线验证中 Core `device_space` 行为测试 107 项通过，单线程执行。`edge/docs/v1-closeout.md:129`
最新基线复验中 ESP32 release 编译、链接、Tokio/ring 最终 ELF Xtensa ABI 检查与 4 MB 镜像导出通过。`edge/docs/v1-closeout.md:50`
最新基线复验中模拟器固件模块 62 项测试和 TypeScript 检查通过。`edge/docs/v1-closeout.md:51`
最新基线复验中编辑器和实际内存/受保护栈边界探针 116 项通过。`edge/docs/v1-closeout.md:53`
最新基线复验中带固件的统一验收完整通过：当前 CLI 和 release 模拟器重建后，配对审批与重启恢复、独立聊天额外 12 轮及 Core/设备退出重启、远端聊天与存储故障及二进制语音恢复均通过。`edge/docs/v1-closeout.md:54`

### V1 收尾时固件容量阻塞的修复

历史 rebase 后复验（1ced7f40）中 ESP32 固件在链接时失败：`.flash.text` 超出原有映射区 3,226 字节；不能沿用首次基线“固件构建通过”的结论。`edge/docs/v1-closeout.md:104`
历史 rebase 后复验中带固件的统一验收在构建阶段停止，未完成后续端到端场景。`edge/docs/v1-closeout.md:106`
未修改前在最新 main 上复现 `.flash.text` 超限 3,226 字节。`edge/docs/v1-closeout.md:42`
固件容量修复把三个小型映射改成逐项插入：旧版 `nodeIds` 的默认身份映射、四个内置角色和审批路由 BFS 的起始距离。`edge/docs/v1-closeout.md:43`
固件容量修复避免为这些构造保留批量收集器的临时排序缓冲和独立排序代码，最终代码段减少 8,524 字节；映射内容、节点顺序、权限和协议保持一致。`edge/docs/v1-closeout.md:45`
最新基线固件 factory 应用分区占用 3,959,312 / 3,997,696 字节，余量 38,384 字节。`edge/docs/v1-closeout.md:75`
最新基线固件 `.flash.text` 映射区占用 3,337,006 / 3,342,304 字节，余量 5,298 字节。`edge/docs/v1-closeout.md:76`
首次基线固件 factory 应用分区占用 3,961,680 / 3,997,696 字节，余量 36,016 字节（约 35.2 KiB）。`edge/docs/v1-closeout.md:178`
首次基线固件 `.flash.text` 映射区占用 3,339,390 / 3,342,304 字节，余量 2,914 字节（约 2.85 KiB）。`edge/docs/v1-closeout.md:179`
V1 收尾记录指出代码段余量仍然有限，后续更新必须重新构建并检查两种容量限制。`edge/docs/v1-closeout.md:79`
最新基线验收产物 ELF `operit-esp32` 的 SHA-256 是 3ec09572bac486a2cf17a171361f7380d6106f7b11c2b83b87684bcc0bdd92da。`edge/docs/v1-closeout.md:83`
最新基线验收产物应用 `operit-esp32.bin` 的 SHA-256 是 456fa22357e3d4138db79159e252cc7dc57ccdb3b080906e9c8236b25417a049。`edge/docs/v1-closeout.md:84`
最新基线验收产物合并镜像 `operit-esp32-4mb-full.bin` 的 SHA-256 是 1c14d8e31172969f7cad9d4459141bde2afa5cc1acfa7194872170003e1daa46。`edge/docs/v1-closeout.md:85`

### CLI 同步栈溢出修复与代理复验

CLI `space sync` 独立装箱同步 future，避免复制进命令和会话的异步执行帧，修复 Windows 调试版主线程栈溢出。`edge/docs/v1-closeout.md:33`
Windows 调试版 CLI `space sync` 在未继承代理时也复现过主线程栈溢出；将同步 future 独立装箱后，上述场景全部通过。`edge/docs/v1-closeout.md:56`
另行保留 `HTTP_PROXY` / `HTTPS_PROXY=http://127.0.0.1:7890`，设置 `NO_PROXY=127.0.0.1,localhost,::1`，独立聊天 12 轮与重启场景通过。`edge/docs/v1-closeout.md:58`
带代理的复验验证了配置代理且回环地址直连的本地链路，不代表外部代理服务或远端模型已验收。`edge/docs/v1-closeout.md:60`

### 哪些“通过”明确不代表真机通过

模型和 STT/TTS 服务使用本地确定性提供方；本次没有调用外部付费模型，也不据此评价外部模型质量。`edge/docs/acceptance.md:79`
首次基线中 65 秒 PCM 指字节量，语音和模型提供者使用本地确定性 fixture，不代表真实服务识别质量或实际麦克风/扬声器已经验收。`edge/docs/v1-closeout.md:143`
本机只发现蓝牙串口，没有检测到 USB ESP32，因此没有执行烧录或真机操作。`edge/docs/v1-closeout.md:192`
最新基线复验本轮未连接交付板，未执行烧录或真机验收。`edge/docs/v1-closeout.md:92`
首次基线验证中真机烧录、音频与持续运行未执行；无 USB 交付板。`edge/docs/v1-closeout.md:130`
当前版本已通过上述新基线软件复验；仍须通过真机检查，才能标记“ESP32 Edge V1 硬件交付完成”。`edge/docs/v1-closeout.md:206`

## 关键符号

- `npm run test:device-budget` —— ESP32 完整模拟器验收入口，执行全部场景。`edge/docs/acceptance.md:11`
- `EMSDK` —— ESP32 完整模拟器验收入口所需的 Emscripten 环境变量。`edge/docs/acceptance.md:11`
- `operit-edge-sdk` —— 厂商接入 Edge V1 的 SDK。`edge/docs/v1-closeout.md:15`
- `space` —— SDK 功能，依赖包数 108。`edge/docs/acceptance.md:57`
- `http-agent` —— SDK 功能，依赖包数 25。`edge/docs/acceptance.md:58`
- `scene` —— SDK 功能，依赖包数 41。`edge/docs/acceptance.md:59`
- `node-state` —— 存储功能，最新基线单元测试 192 项通过。`edge/docs/v1-closeout.md:49`
- `device_space` —— Core 行为测试对象，最新基线 108 项通过。`edge/docs/v1-closeout.md:52`
- `space sync` —— CLI 同步命令，独立装箱同步 future 后修复主线程栈溢出。`edge/docs/v1-closeout.md:33`
- `.flash.text` —— ESP32 代码段映射区，最新基线占用 3,337,006 / 3,342,304 字节。`edge/docs/v1-closeout.md:76`
- `nodeIds` —— 旧版默认身份映射，固件容量修复中改成逐项插入。`edge/docs/v1-closeout.md:43`
- `operit-esp32` —— 最新基线验收产物 ELF，SHA-256 见正文。`edge/docs/v1-closeout.md:83`
- `operit-esp32.bin` —— 最新基线验收产物应用镜像，SHA-256 见正文。`edge/docs/v1-closeout.md:84`
- `operit-esp32-4mb-full.bin` —— 最新基线验收产物合并镜像，SHA-256 见正文。`edge/docs/v1-closeout.md:85`
- `HTTP_PROXY` —— 代理复验保留的环境变量，取值为 http://127.0.0.1:7890。`edge/docs/v1-closeout.md:58`

## 调用链

1. 执行 ESP32 完整模拟器验收入口 `npm run test:device-budget`，重建预览、模拟器、插件资产和当前 CLI。`edge/docs/acceptance.md:15`
2. 执行 C/Wasm 预览构建与 TypeScript 检查。`edge/docs/acceptance.md:21`
3. 执行产品共用 Rust 模块测试，62 项通过。`edge/docs/acceptance.md:22`
4. 执行编辑器与实际堆/栈边界探针，116 项通过。`edge/docs/acceptance.md:23`
5. 执行配对、加入空间、持久化与重启。`edge/docs/acceptance.md:24`
6. 执行 CLI 退出后的独立流式聊天、连续额外 12 轮与设备重启后聊天。`edge/docs/acceptance.md:25`
7. 执行空间聊天与两边消息互通、完整 UI 操作与恢复。`edge/docs/acceptance.md:26`
8. 执行语音场景与插件场景，语音场景验证 PCM/WAV、多段 TTS、背压、断开重连，插件场景经过真实 Core JS 处理器和设备服务路由。`edge/docs/acceptance.md:30`
9. 采样各场景的 Rust 堆峰值与分配失败，核对 262,144 字节固定堆预算与 16/24/20 KiB 任务栈预算。`edge/docs/acceptance.md:32`
10. 执行 SDK workspace 全功能测试与 8 种功能组合依赖审计。`edge/docs/v1-closeout.md:48`
11. 执行共享实现回归：节点运行时与 Peer Link、`node-state` 存储、调度器、跨设备协议与空间接入。`edge/docs/acceptance.md:75`
12. 构建 ESP32 release 固件，完成编译、链接、最终 ELF Xtensa ABI 检查与 4 MB 镜像导出。`edge/docs/v1-closeout.md:50`
13. 核对 factory 应用分区占用 3,959,312 / 3,997,696 字节，余量 38,384 字节。`edge/docs/v1-closeout.md:75`
14. 核对 `.flash.text` 映射区占用 3,337,006 / 3,342,304 字节，余量 5,298 字节。`edge/docs/v1-closeout.md:76`
15. 容量超限时把三个小型映射改成逐项插入，代码段减少 8,524 字节后重验。`edge/docs/v1-closeout.md:45`
16. 真机交付检查仍待在交付板上执行：本轮未连接交付板，未执行烧录或真机验收。`edge/docs/v1-closeout.md:92`

## 来源

- `edge/docs/acceptance.md`：Edge 验收记录（2026-10-29），验收基线 3c5fcc81653999613328209bd0beafb415949c82，macOS 上实际运行的 CLI 与 ESP32 产品模拟器验收。
- `edge/docs/v1-closeout.md`：Edge V1 收尾记录（更新于 2026-10-30），首次验收基线 3d6238a4，PR rebase 到 06784b03，Windows 上收尾 SDK 接入和验收入口。
- `edge/README.md`：Edge 总览，完整模拟器验收的入口说明与固件验收限定（加 `-- --firmware`、检查应用分区及 `.flash.text` 映射区余量、不执行烧录、真机音频/网络/持续运行另行验收）。
- 本页引用的验收基线号（3c5fcc81653999613328209bd0beafb415949c82、3d6238a4、06784b03、1ced7f40、ec9702ae）均取自上述两份验收记录，与大纲基线 364d1d594 不同，不得把验收基线写成大纲基线。
- 否定性结论核验方法：本页“未执行”类断言（未执行 ESP-IDF 目标固件构建、真实 ESP32 烧录、整板 Wi-Fi/TLS/C 内存和闪存测量、未调用外部付费模型、未连接交付板、未执行烧录或真机验收、真机烧录/音频/持续运行未执行）均直接取自两份验收记录的原文表述；2026-11-12 在基线 364d1d594 的本地 checkout 上用 grep -n "没有执行|未执行|未连接|没有调用" edge/docs/acceptance.md edge/docs/v1-closeout.md 核对，上述否定表述在两份记录中均有原文对应，无额外推断。
