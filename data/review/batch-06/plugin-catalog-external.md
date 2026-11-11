---
title: 外置（官方可选）插件目录
module: plugins
platforms: [all]
sources: [plugins/README.md, plugins/packages/external/subagents/manifest.json, plugins/packages/external/moss_atelier/manifest.json, plugins/packages/external/worldbook/manifest.json, plugins/packages/external/wechat/manifest.json, plugins/packages/external/subagents/README.md, plugins/packages/external/subagents/src/tools.ts, plugins/packages/external/waifu/manifest.json, plugins/packages/external/qqbot/manifest.json, plugins/packages/external/image_workbench/manifest.json, plugins/packages/external/custom_ai_provider/manifest.json, plugins/packages/external/desktop_widget_demo/manifest.json, plugins/packages/external/dino_runner/manifest.json, plugins/packages/external/floating_window_demo/manifest.json, plugins/packages/external/sidebar_bing_action/manifest.json, plugins/packages/external/template_try/manifest.json, plugins/packages/external/context_limiter/manifest.json, plugins/packages/external/debug_msg_dump/manifest.json, plugins/packages/external/deepseek_dafeiyu/manifest.json, plugins/packages/external/edge_pixel_pet/manifest.json, plugins/packages/external/message_insert/manifest.json, plugins/packages/external/openui/manifest.json, plugins/packages/external/sidebar_model_sites/manifest.json, plugins/packages/external/baidu_map.ts, plugins/packages/external/beeimg_image_uploader.ts, plugins/packages/external/douyin_download.ts, plugins/packages/external/duckduckgo.ts, plugins/packages/external/extended_chat.ts, plugins/packages/external/extended_http_tools.ts, plugins/packages/external/google_search.ts, plugins/packages/external/network_test.ts, plugins/packages/external/tavily.ts, plugins/packages/external/zhipu_search.ts, plugins/packages/external/tsconfig.json, core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs]
date: 2026-11-11
---

## 概述

外置插件是随应用打包、由用户从 more plugins 加载的官方捆绑 ToolPkg（`plugins/README.md:9`）。
buildin、external 与 examples 使用相同的源码布局，区别是打包方式，字段定义见 [[plugin-manifest|插件 manifest 格式]] 与 [[plugin-toolpkg-overview|ToolPkg 总览]]（`plugins/README.md:17`）。

## AI 速览

- 核心符号：`spawn_agent` — 创建并立即返回 agent ID，后台执行（`plugins/packages/external/subagents/README.md:21`）。
- 核心符号：`wait_agent` — 等待任一所选当前轮次结束，默认 30000 毫秒（`plugins/packages/external/subagents/README.md:22`）。
- 核心符号：`send_input` — 发送新轮次，运行中需显式打断（`plugins/packages/external/subagents/README.md:23`）。
- 核心符号：`close_agent` — 等待实际停止，关闭任务及后代，保留历史（`plugins/packages/external/subagents/README.md:24`）。
- 核心符号：`list_agents` — 读取当前聊天子任务与最终结果（`plugins/packages/external/subagents/README.md:25`）。
- 主入口：`main` 指向 dist/main.js（`plugins/packages/external/subagents/manifest.json:6`）。
- 数据流向：导入后 sourceType 为 EXTERNAL，并发现全部五个工具（`plugins/packages/external/subagents/README.md:72`）。

## 核心机制

### 外置与内置的打包差异

packages/buildin/ 是打包为内置插件的 ToolPkg 源码（`plugins/README.md:8`）。
packages/external/ 是随应用打包、由用户从 more plugins 加载的官方捆绑 ToolPkg 源码（`plugins/README.md:9`）。
packages/buildin/、packages/external/ 与 packages/examples/ 使用相同的源码布局，区别是打包方式（`plugins/README.md:17`）。
subagents 的打包产物是 dist/subagents.toolpkg，归档包含 manifest、README 与全部运行时 JS（`plugins/packages/external/subagents/README.md:55`）。
subagents 通过安装并启用 dist/subagents.toolpkg 来使用（`plugins/packages/external/subagents/README.md:5`）。
subagents 的 enabled_by_default 为 false，installation_scope 为 space（`plugins/packages/external/subagents/manifest.json:12`）。
moss_atelier 的 enabled_by_default 为 false（`plugins/packages/external/moss_atelier/manifest.json:17`）。
worldbook 的 enabled_by_default 为 false（`plugins/packages/external/worldbook/manifest.json:21`）。
wechat 的 enabled_by_default 为 false，installation_scope 为 device（`plugins/packages/external/wechat/manifest.json:12`）。
message_insert 的 enabled_by_default 为 true（`plugins/packages/external/message_insert/manifest.json:15`）；显式声明为 true 的仅 message_insert，另有 debug_msg_dump 因省略该字段而缺省为 true。
debug_msg_dump 的 manifest 省略 enabled_by_default，按宿主缺省规则实际默认启用（`plugins/packages/external/debug_msg_dump/manifest.json:1`；`core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs:668`）。
context_limiter 的 ctx_limiter 子包 enabled_by_default 为 true（`plugins/packages/external/context_limiter/manifest.json:14`）。
edge_pixel_pet 的 edge_pixel_pet 子包 enabled_by_default 为 true（`plugins/packages/external/edge_pixel_pet/manifest.json:14`）。
subagents 工具子包的默认启用声明位于 src/tools.ts 的 METADATA 中，容器本身仍默认关闭（`plugins/packages/external/subagents/README.md:57`）。

### 目录清单（20 个目录插件）

| 目录 | toolpkg_id | 版本 | 引用 |
| --- | --- | --- | --- |
| context_limiter | com.operit.context_limiter | 1.0.0 | `plugins/packages/external/context_limiter/manifest.json:4` |
| custom_ai_provider | com.operit.custom_ai_provider_example | 0.1.0 | `plugins/packages/external/custom_ai_provider/manifest.json:3` |
| debug_msg_dump | com.operit.debug_msg_dump | 1.0.0 | `plugins/packages/external/debug_msg_dump/manifest.json:3` |
| deepseek_dafeiyu | com.operit.deepseek_dafeiyu | 0.2.0 | `plugins/packages/external/deepseek_dafeiyu/manifest.json:3` |
| desktop_widget_demo | com.operit.desktop_widget_demo | 0.1.0 | `plugins/packages/external/desktop_widget_demo/manifest.json:3` |
| dino_runner | com.operit.dino_runner | 0.1.0 | `plugins/packages/external/dino_runner/manifest.json:4` |
| edge_pixel_pet | com.operit.edge_pixel_pet | 0.1.0 | `plugins/packages/external/edge_pixel_pet/manifest.json:3` |
| floating_window_demo | com.operit.floating_window_demo | 0.1.0 | `plugins/packages/external/floating_window_demo/manifest.json:3` |
| image_workbench | com.operit.image_workbench | 1.0.0 | `plugins/packages/external/image_workbench/manifest.json:3` |
| message_insert | com.operit.message_insert_bundle | 0.4.0 | `plugins/packages/external/message_insert/manifest.json:3` |
| moss_atelier | com.operit.moss_atelier | 0.1.0 | `plugins/packages/external/moss_atelier/manifest.json:3` |
| openui | com.operit.openui | 0.1.0 | `plugins/packages/external/openui/manifest.json:3` |
| qqbot | com.operit.qqbot_bundle | 1.1.2 | `plugins/packages/external/qqbot/manifest.json:3` |
| sidebar_bing_action | com.operit.sidebar_bing_action | 0.1.0 | `plugins/packages/external/sidebar_bing_action/manifest.json:3` |
| sidebar_model_sites | com.operit.sidebar_model_sites | 0.1.0 | `plugins/packages/external/sidebar_model_sites/manifest.json:3` |
| subagents | com.operit.subagents | 0.1.0 | `plugins/packages/external/subagents/manifest.json:3` |
| template_try | com.operit.template_try_bundle | 0.1.0 | `plugins/packages/external/template_try/manifest.json:3` |
| waifu | com.operit.waifu | 1.1.0 | `plugins/packages/external/waifu/manifest.json:3` |
| wechat | com.operit.wechat_bot | 1.0.0 | `plugins/packages/external/wechat/manifest.json:3` |
| worldbook | com.operit.worldbook | 1.2.0 | `plugins/packages/external/worldbook/manifest.json:3` |

### 松散单文件插件（10 个）

| 文件 | METADATA 名称 | 引用 |
| --- | --- | --- |
| baidu_map.ts | `baidu_map` | `plugins/packages/external/baidu_map.ts:4` |
| beeimg_image_uploader.ts | `beeimg_image_uploader_v2` | `plugins/packages/external/beeimg_image_uploader.ts:3` |
| douyin_download.ts | `douyin_download` | `plugins/packages/external/douyin_download.ts:4` |
| duckduckgo.ts | `duckduckgo` | `plugins/packages/external/duckduckgo.ts:4` |
| extended_chat.ts | `extended_chat` | `plugins/packages/external/extended_chat.ts:3` |
| extended_http_tools.ts | `extended_http_tools` | `plugins/packages/external/extended_http_tools.ts:3` |
| google_search.ts | `google_search` | `plugins/packages/external/google_search.ts:3` |
| network_test.ts | `network_test` | `plugins/packages/external/network_test.ts:4` |
| tavily.ts | `tavily` | `plugins/packages/external/tavily.ts:3` |
| zhipu_search.ts | `zhipu_search` | `plugins/packages/external/zhipu_search.ts:3` |

tsconfig.json 是 external 目录的 TypeScript 编译配置，把输出写到 ../../.out/external（`plugins/packages/external/tsconfig.json:8`）。
tsconfig.json 的 include 覆盖 *.ts，松散 .ts 文件随 external 一起编译（`plugins/packages/external/tsconfig.json:30`）。

### 演示性质的插件（manifest 称演示或示例）

custom_ai_provider 演示如何通过 ToolPkg.registerAiProvider 注册自定义 AI 供应商（`plugins/packages/external/custom_ai_provider/manifest.json:12`）。
desktop_widget_demo 演示如何通过 ToolPkg 注册可配置的桌面小组件，并点击打开对应的 compose_dsl 页面（`plugins/packages/external/desktop_widget_demo/manifest.json:13`）。
dino_runner 是以 Chrome 小恐龙为主题的 WebView 示例，页面本体是全屏小游戏（`plugins/packages/external/dino_runner/manifest.json:13`）。
floating_window_demo 演示透明实时悬浮窗、桌宠交互、移动和显示生命周期（`plugins/packages/external/floating_window_demo/manifest.json:8`）。
sidebar_bing_action 演示 ToolPkg 侧边栏插件项通过 action 函数直接执行逻辑，而不是跳转路由（`plugins/packages/external/sidebar_bing_action/manifest.json:12`）。
template_try 用于演示 ToolPkg 工作流模板与工作区模板在宿主中的注册、展示与导入（`plugins/packages/external/template_try/manifest.json:18`）。

### 大插件边界

#### image_workbench

image_workbench 在一个工作台中使用 OpenAI、通义千问、智谱、xAI、MiniMax 和 Nano Banana（`plugins/packages/external/image_workbench/manifest.json:12`）。
image_workbench 支持配置密钥、文生图、参考图生图和查看生成结果（`plugins/packages/external/image_workbench/manifest.json:12`）。
image_workbench 拥有统一的生图工具与六个内部供应商适配器（`plugins/README.md:15`）。
image_workbench 声明 id 为 image_workbench 的子包，入口为 dist/tools.js（`plugins/packages/external/image_workbench/manifest.json:20`）。
packages/external/image_workbench/ 提供可选的官方 Image Workbench，从 more plugins 提供，默认禁用（`plugins/README.md:15`）。

#### waifu

waifu 提供普通聊天中的分句气泡、打字节奏、角色绑定、情绪表情和自拍提示（`plugins/packages/external/waifu/manifest.json:13`）。
waifu 声明 public_api 为 src/api.ts，向依赖插件公开 API（`plugins/packages/external/waifu/manifest.json:7`）。
waifu 依赖 com.operit.character_cards，最低版本 0.1.0（`plugins/packages/external/waifu/manifest.json:292`）。
waifu 的 resources 包含 resources/emoji/ 下的情绪表情图片（`plugins/packages/external/waifu/manifest.json:26`）。
waifu 声明 id 为 waifu 的子包，入口为 dist/tools.js（`plugins/packages/external/waifu/manifest.json:20`）。

#### wechat

wechat 扫码连接微信，支持消息与媒体收发、独立聊天记录、角色卡和 Waifu 自动回复（`plugins/packages/external/wechat/manifest.json:9`）。
wechat 依赖 com.operit.waifu 1.0.0 与 com.operit.character_cards 0.1.0（`plugins/packages/external/wechat/manifest.json:17`）。

#### qqbot

qqbot 通过宿主原生网络连接腾讯 QQ Bot，提供 C2C/群消息收发、事件队列和 AI 自动回复（`plugins/packages/external/qqbot/manifest.json:12`）。
qqbot 的 installation_scope 为 device（`plugins/packages/external/qqbot/manifest.json:16`）。
qqbot 依赖 com.operit.waifu 1.0.0 与 com.operit.character_cards 0.1.0（`plugins/packages/external/qqbot/manifest.json:26`）。

### subagents 的启用与限制

子代理由 AI 通过 spawn_agent 工具创建，面板不提供用户手动创建入口（`plugins/packages/external/subagents/README.md:9`）。
最多同时运行 8 个子代理，新建和后续轮次共享这个限制（`plugins/packages/external/subagents/README.md:27`）。
wait_agent 的 timeout_ms 取值 1..30000，默认 30000（`plugins/packages/external/subagents/src/tools.ts:24`）。
send_input 的 interrupt 默认 false（`plugins/packages/external/subagents/src/tools.ts:33`）。
插件主运行时重启会丢失正在执行轮次的观察句柄，这类记录标记为 interrupted，不伪造完成回执（`plugins/packages/external/subagents/README.md:41`）。
插件不会在结果完成后自动恢复主模型生成，主聊天通过 wait_agent 工具获取结果并继续自己的轮次（`plugins/packages/external/subagents/README.md:43`）。

### moss_atelier 与 worldbook

moss_atelier 提供苔绿与暖砂两套外观模板，配有完整明暗配色、柔和背景与悬浮输入框（`plugins/packages/external/moss_atelier/manifest.json:11`）。
moss_atelier 的 manifest 未声明 main 入口，仅声明 themes，是无入口的主题包（`plugins/packages/external/moss_atelier/manifest.json:1`）。
moss_atelier 的 themes 包含 id 为 moss 的主题，主题机制见 [[plugin-theme|主题即插件]]（`plugins/packages/external/moss_atelier/manifest.json:28`）。
manifest 声明 id 为 dune 的主题（`plugins/packages/external/moss_atelier/manifest.json:47`）。
moss_atelier 的 logo 资源 key 为 package_logo，路径为 resources/logo.svg（`plugins/packages/external/moss_atelier/manifest.json:18`）。
worldbook 支持创建、编辑、启用/禁用世界书条目，并通过关键词或常驻激活自动注入到系统提示词或用户消息中（`plugins/packages/external/worldbook/manifest.json:17`）。
worldbook 声明 id 为 worldbook_tools 的子包，入口为 dist/packages/worldbook_tools.js（`plugins/packages/external/worldbook/manifest.json:24`）。
worldbook 的 worldbook_tools 子包 enabled_by_default 为 false（`plugins/packages/external/worldbook/manifest.json:26`）。
worldbook 依赖 com.operit.character_cards，最低版本 0.1.0（`plugins/packages/external/worldbook/manifest.json:39`）。

## 关键符号

- `spawn_agent` — 创建并立即返回 agent ID，后台执行（`plugins/packages/external/subagents/README.md:21`）。
- `wait_agent` — 等待任一所选当前轮次结束（`plugins/packages/external/subagents/README.md:22`）。
- `send_input` — 发送新轮次，运行中需显式打断（`plugins/packages/external/subagents/README.md:23`）。
- `close_agent` — 等待实际停止，关闭任务及后代，保留历史（`plugins/packages/external/subagents/README.md:24`）。
- `list_agents` — 读取当前聊天子任务与最终结果（`plugins/packages/external/subagents/README.md:25`）。
- `toolpkg_id` — 插件包 ID，如 com.operit.subagents（`plugins/packages/external/subagents/manifest.json:3`）。
- `main` — 插件入口，如 dist/main.js（`plugins/packages/external/subagents/manifest.json:6`）。
- `enabled_by_default` — 是否默认启用，subagents 为 false（`plugins/packages/external/subagents/manifest.json:12`）。
- `installation_scope` — 安装作用域，subagents 为 space（`plugins/packages/external/subagents/manifest.json:13`）。
- `subpackages` — 子包声明，subagents 子包入口为 dist/tools.js（`plugins/packages/external/subagents/manifest.json:15`）。
- `requires` — 依赖声明，worldbook 依赖 character_cards（`plugins/packages/external/worldbook/manifest.json:39`）。
- `themes` — 主题声明，moss_atelier 用它提供 moss 主题（`plugins/packages/external/moss_atelier/manifest.json:28`）。
- `public_api` — 对外公开的 API 入口，waifu 为 src/api.ts（`plugins/packages/external/waifu/manifest.json:7`）。
- `sourceType` — 导入来源类型，subagents 导入后为 EXTERNAL（`plugins/packages/external/subagents/README.md:72`）。
- `METADATA` — 松散 .ts 插件的文件头声明，如 baidu_map（`plugins/packages/external/baidu_map.ts:4`）。

## 调用链

1. 用户安装并启用 dist/subagents.toolpkg（`plugins/packages/external/subagents/README.md:5`）。
2. 导入后 sourceType 为 EXTERNAL，并发现全部五个工具（`plugins/packages/external/subagents/README.md:72`）。
3. AI 调用 spawn_agent 创建子代理，立即得到 agent ID（`plugins/packages/external/subagents/README.md:21`）。
4. 主聊天调用 wait_agent 等待子代理当前轮次结束（`plugins/packages/external/subagents/README.md:22`）。
5. 继续对话调用 send_input 发送新指令（`plugins/packages/external/subagents/README.md:23`）。
6. 结束调用 close_agent，等待实际停止并保留历史（`plugins/packages/external/subagents/README.md:24`）。
7. 打包只发出插件 JavaScript 并创建 dist/subagents.toolpkg（`plugins/packages/external/subagents/README.md:55`）。

## 来源

- `plugins/README.md`
- `plugins/packages/external/subagents/manifest.json`
- `plugins/packages/external/moss_atelier/manifest.json`
- `plugins/packages/external/worldbook/manifest.json`
- `plugins/packages/external/wechat/manifest.json`
- `plugins/packages/external/subagents/README.md`
- `plugins/packages/external/subagents/src/tools.ts`
- `plugins/packages/external/waifu/manifest.json`
- `plugins/packages/external/qqbot/manifest.json`
- `plugins/packages/external/image_workbench/manifest.json`
- `plugins/packages/external/custom_ai_provider/manifest.json`
- `plugins/packages/external/desktop_widget_demo/manifest.json`
- `plugins/packages/external/dino_runner/manifest.json`
- `plugins/packages/external/floating_window_demo/manifest.json`
- `plugins/packages/external/sidebar_bing_action/manifest.json`
- `plugins/packages/external/template_try/manifest.json`
- `plugins/packages/external/context_limiter/manifest.json`
- `plugins/packages/external/debug_msg_dump/manifest.json`
- `plugins/packages/external/deepseek_dafeiyu/manifest.json`
- `plugins/packages/external/edge_pixel_pet/manifest.json`
- `plugins/packages/external/message_insert/manifest.json`
- `plugins/packages/external/openui/manifest.json`
- `plugins/packages/external/sidebar_model_sites/manifest.json`
- `plugins/packages/external/baidu_map.ts`
- `plugins/packages/external/beeimg_image_uploader.ts`
- `plugins/packages/external/douyin_download.ts`
- `plugins/packages/external/duckduckgo.ts`
- `plugins/packages/external/extended_chat.ts`
- `plugins/packages/external/extended_http_tools.ts`
- `plugins/packages/external/google_search.ts`
- `plugins/packages/external/network_test.ts`
- `plugins/packages/external/tavily.ts`
- `plugins/packages/external/zhipu_search.ts`
- `plugins/packages/external/tsconfig.json`
- `core/crates/plugin/sdk/src/toolpkg/ToolPkgParser.rs`
