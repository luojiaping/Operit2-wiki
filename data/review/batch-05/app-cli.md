---
title: 命令行应用 operit2
module: apps
platforms: [windows, linux, macos]
sources: [apps/cli/Cargo.toml, apps/cli/src/main.rs, apps/cli/src/bootstrap.rs, apps/cli/src/cli/mod.rs, apps/cli/src/cli/link.rs, apps/cli/src/cli/host_ops.rs, apps/cli/src/cli/network_control_ui.rs, apps/cli/src/cli/transfer.rs, apps/cli/src/cli/web.rs, apps/cli/src/daemon.rs, apps/cli/src/mdns.rs, apps/cli/src/rescue.rs, apps/cli/src/chat_runtime.rs, apps/cli/src/core_proxy.rs, apps/cli/src/tui/mod.rs]
date: 2026-11-11
---

## 概述

operit2 是 Operit2 的命令行应用，包名 `operit-cli`，版本是 2.0.0-preview.31（`apps/cli/Cargo.toml:3`）。
CLI 可执行文件名为 `operit2`（`apps/cli/Cargo.toml:12`）。
无参数启动 operit2 进入 TUI（`apps/cli/src/main.rs:57`）。
operit2 rescue 把参数交给 `rescue` 的 `run`（`apps/cli/src/main.rs:61`）。
operit2 cli 把参数交给 `cli` 的 `run_cli_root`（`apps/cli/src/main.rs:66`）。
operit2 daemon 把参数交给 `daemon` 的 `run`（`apps/cli/src/main.rs:67`）。
operit2 tui 把参数交给 `tui` 的 `run_tui_command`（`apps/cli/src/main.rs:68`）。
operit2 install 与 operit2 uninstall 把参数交给 `cli` 的 `run_cli_root`（`apps/cli/src/main.rs:69`）。
CLI host 只在 Windows、Linux、macOS 上实现（`apps/cli/src/bootstrap.rs:62`）。
CLI 不是瘦客户端：无 owner 时启动进程内短命 Core；有 owner 时复用 owner 的 Core（`apps/cli/src/cli/mod.rs:155`）（`apps/cli/src/core_proxy.rs:51`）。
短命 CLI Core 在 owner 运行时关闭 Space 同步（`apps/cli/src/bootstrap.rs:248`）。

## AI 速览

- 核心符号：`local_cli_core` — 创建进程内本地 CLI Core（`apps/cli/src/core_proxy.rs:51`）。
- 核心符号：`create_cli_core_application` — 启动 CLI 的 CoreApplication（`apps/cli/src/bootstrap.rs:238`）。
- 核心符号：`run_cli_root_inner` — 按首个参数分发 CLI 命令（`apps/cli/src/cli/mod.rs:116`）。
- 核心符号：`run_link_command` — 分发 link 的子命令（`apps/cli/src/cli/link.rs:33`）。
- 核心符号：`OwnerGuard` 的 `acquire` — 为一个身份抢占排他 Core 所有权锁（`apps/cli/src/daemon.rs:135`）。
- 核心符号：`try_run_cli_command` — 有 owner 时把 CLI 命令路由给 owner（`apps/cli/src/daemon.rs:491`）。
- 核心符号：`run_tui_command` — TUI 入口（`apps/cli/src/tui/mod.rs:92`）。
- 核心符号：`discover_devices` — 浏览 mDNS 服务发现设备（`apps/cli/src/mdns.rs:51`）。
- 主入口函数：main 按首个参数分发到 TUI、CLI、daemon、rescue、安装（`apps/cli/src/main.rs:57`）。
- 数据流向：用户输入 → run_cli_root_inner 分发 → 有 owner 时走控制通道复用 owner 的 Core，无 owner 时启动短命进程内 Core → 本地路径：Core 命令经 `GeneratedCoreProxy`（`apps/cli/src/core_proxy.rs:56`）发往 Core，由 `run_core_command_and_print` 执行并打印结果（`apps/cli/src/cli/mod.rs:1442`）；owner 路径：命令经控制通道 `run` 操作在 owner 的 Core 上执行（`apps/cli/src/daemon.rs:491`）（`apps/cli/src/daemon.rs:457`）。

## 核心机制

### 完整 CoreNode，而不是瘦客户端

`local_cli_core` 创建进程内本地 CLI Core（`apps/cli/src/core_proxy.rs:51`）。
`CliCore` 的 proxy 是包着 `SharedLocalCore` 的 `GeneratedCoreProxy`（`apps/cli/src/core_proxy.rs:56`）。
`SharedLocalCore` 持有 `Arc<LocalCoreProxy>`（`apps/cli/src/core_proxy.rs:14`）。
`create_cli_host_manager` 构造 CLI 的 `HostManager`（`apps/cli/src/bootstrap.rs:65`）。
`create_cli_core_application` 启动 CLI 的 `CoreApplication`（`apps/cli/src/bootstrap.rs:238`）。
CLI 设备身份用 `LinkDeviceInfo` 的 `nativeCliOnHost` 构造（`apps/cli/src/bootstrap.rs:78`）。
短命 CLI Core 在 owner 运行时关闭 Space 同步（`apps/cli/src/bootstrap.rs:248`）。
带节点服务的 CLI Core 创建入口固定关闭 Space 同步（`apps/cli/src/bootstrap.rs:267`）。
run_cli_root_inner 在启动自有 Core 之前先调用 `try_run_cli_command`（`apps/cli/src/cli/mod.rs:155`）。
有 owner 时 CLI 命令经 `try_run_cli_command` 走 owner 的控制通道（`apps/cli/src/daemon.rs:491`）。
`route_supported` 把交互与本地命令排除在 owner 路由之外（`apps/cli/src/daemon.rs:528`）。
model codex-login 不走 owner 路由（`apps/cli/src/daemon.rs:533`）。
`OPERIT_CLI_CONFIG_DIR` 环境变量覆盖 CLI 配置目录（`apps/cli/src/bootstrap.rs:630`）。
显式 CLI 配置下插件 SDK IPC 实例按身份隔离（`apps/cli/src/bootstrap.rs:108`）。

### 命令清单：31 个固有命令族加插件命令

`run_cli_root_inner` 按首个参数分发 CLI 命令（`apps/cli/src/cli/mod.rs:116`）。
`CLI_COMMANDS` 表定义固有 CLI 命令族（`apps/cli/src/cli/mod.rs:1794`）。
单元测试断言 `CLI_COMMANDS` 覆盖 31 个固有 CLI 命令族（`apps/cli/src/cli/mod.rs:2316`）。
`read_cli_plugin_commands` 通过 plugin commands --json 读取插件命令目录（`apps/cli/src/cli/mod.rs:1848`）。
插件命令与固有 CLI 命令同名时报错（`apps/cli/src/cli/mod.rs:1855`）。
插件命令来自已启用插件的 Core 命令目录（`apps/cli/src/cli/mod.rs:1843`）。
`run_cli_root` 剥离 `--json` 后分发命令（`apps/cli/src/cli/mod.rs:102`）。
`cli_json_mode` 表示本次调用是否要求 JSON 输出（`apps/cli/src/cli/mod.rs:80`）。
`cli_usage_lines`（`apps/cli/src/cli/mod.rs:1862`）的用法文本列出 `--link <session>` 全局选项（`apps/cli/src/cli/mod.rs:1868`）。
除 chat shell 外，`chat` 子命令转发给 Core 命令（`apps/cli/src/cli/mod.rs:176`）。
`run_identity_command` 处理 identity 本地管理命令（`apps/cli/src/cli/mod.rs:203`）。
`identity` 子命令包含 `list`、`current`、`create`、`use`、`rename`（`apps/cli/src/cli/mod.rs:1942`）。
model codex-login 只接受 `browser` 或 `device` 两种方式（`apps/cli/src/cli/mod.rs:1470`）。
market auth login 走 GitHub OAuth 回调完成登录（`apps/cli/src/cli/mod.rs:1647`）。
`run_update_cli_command` 处理 update 的发现、下载与安装（`apps/cli/src/cli/mod.rs:510`）。
`cli_update_target` 用产品 `cli` 与当前系统、架构构造更新目标（`apps/cli/src/cli/host_ops.rs:21`）。
`install_current_cli` 从当前可执行文件安装 CLI（`apps/cli/src/cli/mod.rs:842`）。
install_cli_from_source 把同一二进制复制为 `operit` 与 `operit2` 两个命令（`apps/cli/src/cli/mod.rs:901`）。
非 Windows 的 CLI 安装目录是 ~/.local/bin（`apps/cli/src/cli/mod.rs:1096`）。
Windows CLI 运行时库包含 `operit_local_llm.dll`（`apps/cli/src/cli/host_ops.rs:29`）。

### link：配对、空间与网络控制

`run_link_command` 分发 link 的子命令（`apps/cli/src/cli/link.rs:33`）。
run_link_command 把 `session` 交给 `run_link_session`（`apps/cli/src/cli/link.rs:40`）。
`link` 包含 `stream-probe` 与 `edge-call` 子命令（`apps/cli/src/cli/link.rs:45`）。
`print_link_usage` 列出 link 的全部子命令用法（`apps/cli/src/cli/link.rs:1296`）。
link pair 配对时在接收设备上读六位确认码（`apps/cli/src/cli/link.rs:127`）。
连接二维码有效期为 5 分钟（`apps/cli/src/cli/link.rs:210`）。
link listen 接受 `http`、`ws`、`tcp`、`serial`、`bluetooth` 五种传输（`apps/cli/src/cli/link.rs:273`）。
link discover 默认超时 2000 毫秒（`apps/cli/src/cli/link.rs:679`）。
link discover 通过 `discoverPeers` 发现对端（`apps/cli/src/cli/link.rs:700`）。
`link doctor` 默认只读，`--repair` 才隔离损坏的日记行（`apps/cli/src/cli/link.rs:610`）。
`run_link_space_command` 处理设备空间的查看与成员管理（`apps/cli/src/cli/link.rs:711`）。
link space join 在只有一个已配对设备时不需要参数（`apps/cli/tests/network_control_session.py:152`）。
`run_link_control_command` 处理空间网络控制策略命令（`apps/cli/src/cli/link.rs:889`）。
`network_capabilities` 把 `all`、`audit`、`relay`、`storage`、`execute`、`view` 等短名映射为协议能力（`apps/cli/src/cli/network_control_ui.rs:155`）。
`network_device_label` 用设备名、用户名、平台、型号拼接设备标签（`apps/cli/src/cli/network_control_ui.rs:10`）。
`run_link_stream_probe_command` 用路由探测验证 StateFlow 与嵌入流（`apps/cli/src/cli/link.rs:1115`）。
`run_link_edge_call_command` 向指定设备发起 edge 调用（`apps/cli/src/cli/link.rs:498`）。

### daemon：无头 Core owner 与控制通道

`daemon` 子命令包含 `run`、`start`、`status`、`stop`（`apps/cli/src/daemon.rs:701`）。
`OwnerGuard` 的 `acquire` 为一个身份抢占排他 Core 所有权锁（`apps/cli/src/daemon.rs:135`）。
OwnerGuard 的 `mark_ready` 把 owner 状态发布为 `ready`（`apps/cli/src/daemon.rs:214`）。
`ControlServer` 的 `bind` 在宿主控制端点上监听（`apps/cli/src/daemon.rs:308`）。
控制通道的 `run` 操作在 owner 的 Core 上执行命令（`apps/cli/src/daemon.rs:457`）。
控制通道拒绝关闭 TUI 拥有的身份（`apps/cli/src/daemon.rs:443`）。
控制通道读超时为 3600 秒（`apps/cli/src/daemon.rs:35`）。
单条控制请求上限 16 MiB（`apps/cli/src/daemon.rs:29`）。
`DAEMON_READY_TIMEOUT` 是 60 秒（`apps/cli/src/daemon.rs:37`）。
daemon start 用 `DAEMON_READY_TIMEOUT` 限时等待就绪（`apps/cli/src/daemon.rs:915`）。

### mdns 发现

mDNS 服务类型是 `_operit._tcp.local.`（`apps/cli/src/mdns.rs:7`）。
`MdnsRegistration` 的 `register` 注册 mDNS 服务（`apps/cli/src/mdns.rs:16`）。
`discover_devices` 浏览 mDNS 服务发现设备（`apps/cli/src/mdns.rs:51`）。
mDNS 发现要求服务带 `deviceId` 属性（`apps/cli/src/mdns.rs:84`）。
mDNS 发现只保留 IPv4 地址（`apps/cli/src/mdns.rs:72`）。
mDNS 地址排序把私网地址排在最前（`apps/cli/src/mdns.rs:150`）。
link discover 通过 `discoverPeers` 发现对端（`apps/cli/src/cli/link.rs:700`）。

### rescue：离线数据抢救，不启动 Core

`rescue` 入口不启动 Core、不打开 SQLite（`apps/cli/src/rescue.rs:1`）。
`rescue` 子命令包含 `describe`、`export`、`inspect`、`import`、`resume`（`apps/cli/src/rescue.rs:85`）。
rescue import 替换在线数据时要求 `--confirm`（`apps/cli/src/rescue.rs:150`）。
rescue resume 要求 `--confirm`（`apps/cli/src/rescue.rs:157`）。
`rescue` 默认运行时根取自 `NativeRuntimeStorageHost` 的默认根（`apps/cli/src/bootstrap.rs:758`）。

### 聊天 shell 与 TUI

聊天 shell 经 `CliCore` 代理运行（`apps/cli/src/chat_runtime.rs:8`）。
shell 启动参数包含 `--chat`、`--resume`、`--source`、`--input`、`--update-current-version`（`apps/cli/src/chat_runtime.rs:322`）。
交互 shell 支持 `/help`、`/exit`、`/switch`、`/resume` 等命令（`apps/cli/src/chat_runtime.rs:694`）。
交互 shell 支持 `/attach`、`/send` 等命令（`apps/cli/src/chat_runtime.rs:700`）。
shell 发送消息复用 chat send Core 命令并取回执（`apps/cli/src/chat_runtime.rs:718`）。
`run_tui_command` 是 TUI 入口（`apps/cli/src/tui/mod.rs:92`）。
TUI 启动时以 `tui` 模式抢占身份 owner 锁（`apps/cli/src/tui/mod.rs:99`）。
TUI 绑定与 daemon 相同的控制服务器（`apps/cli/src/tui/mod.rs:181`）。
`tui` 启动参数包含 `--link-listen`、`--no-listen`、`--link-join`、`--chat`、`--resume`（`apps/cli/src/tui/mod.rs:266`）。
TUI 启动时按保存的监听配置启动入站监听（`apps/cli/src/tui/mod.rs:313`）。
TUI 启动时加入已配对的节点空间（`apps/cli/src/tui/mod.rs:369`）。
TUI 工具审批请求等待 60 秒（`apps/cli/src/tui/mod.rs:456`）。
TUI 渲染依赖 `ratatui` 0.28（`apps/cli/Cargo.toml:44`）。
终端控制依赖 `crossterm` 0.28（`apps/cli/Cargo.toml:21`）。
TUI 包含 `diff` 子模块（`apps/cli/src/tui/mod.rs:10`）。
TUI 包含 `render`、`theme`、`transcript` 等子模块（`apps/cli/src/tui/mod.rs:37`）。
TUI 与 Flutter UI 的能力边界：Flutter 应用见 [[app-flutter|Flutter 应用（主客户端）]]，本页不复述 Flutter 侧能力。

### 导入导出与 web 入口

export memory 导出记忆（`apps/cli/src/cli/transfer.rs:20`）。
export chat 导出聊天记录 JSON（`apps/cli/src/cli/transfer.rs:36`）。
export snapshot 导出快照（`apps/cli/src/cli/transfer.rs:53`）。
`import` 支持 `operit1-snapshot` 迁移一代快照（`apps/cli/src/cli/transfer.rs:106`）。
`backup` 子命令包含 `create`、`restore`、`inspect`（`apps/cli/src/cli/transfer.rs:120`）。
快照导入按 64 KiB 分块上传（`apps/cli/src/cli/transfer.rs:11`）。
`stageArchiveUpload` 以流式分块暂存待导入的归档（`apps/cli/src/cli/transfer.rs:293`）。
`web` 入口指向 `https://web.operit.app/`（`apps/cli/src/cli/web.rs:3`）。
`web` 子命令只接受 `open`（`apps/cli/src/cli/web.rs:6`）。

### 测试验收口径

空间压力测试启动六个真实 CLI 进程（`apps/cli/tests/space-stress.md:3`）。
网络控制会话测试以 link session 启动真实 CLI 进程（`apps/cli/tests/network_control_session.py:40`）。
mcp_http_streaming.rs 包含流式响应与超时测试 `streamed_responses_and_deadlines`（`apps/cli/tests/mcp_http_streaming.rs:22`）。

## 关键符号

- `operit2` — CLI 可执行文件名（`apps/cli/Cargo.toml:12`）。
- `local_cli_core` — 创建进程内本地 CLI Core（`apps/cli/src/core_proxy.rs:51`）。
- `SharedLocalCore` — 持有 `Arc<LocalCoreProxy>` 的共享本地 Core 包装（`apps/cli/src/core_proxy.rs:14`）。
- `create_cli_core_application` — 启动 CLI 的 CoreApplication（`apps/cli/src/bootstrap.rs:238`）。
- `create_cli_host_manager` — 构造 CLI 的 HostManager（`apps/cli/src/bootstrap.rs:65`）。
- `run_cli_root_inner` — 按首个参数分发 CLI 命令（`apps/cli/src/cli/mod.rs:116`）。
- `CLI_COMMANDS` — 固有 CLI 命令族表，31 个（`apps/cli/src/cli/mod.rs:1794`）。
- `read_cli_plugin_commands` — 通过 plugin commands --json 读取插件命令目录（`apps/cli/src/cli/mod.rs:1848`）。
- `run_link_command` — 分发 link 的子命令（`apps/cli/src/cli/link.rs:33`）。
- `run_link_session` — 运行交互式 link 会话（`apps/cli/src/cli/link.rs:40`）。
- `run_link_space_command` — 处理设备空间的查看与成员管理（`apps/cli/src/cli/link.rs:711`）。
- `run_link_control_command` — 处理空间网络控制策略命令（`apps/cli/src/cli/link.rs:889`）。
- `run_link_doctor_command` — 运行共享空间诊断，默认只读（`apps/cli/src/cli/link.rs:610`）。
- `run_link_stream_probe_command` — 用路由探测验证 StateFlow 与嵌入流（`apps/cli/src/cli/link.rs:1115`）。
- `run_link_edge_call_command` — 向指定设备发起 edge 调用（`apps/cli/src/cli/link.rs:498`）。
- `OwnerGuard` 的 `acquire` — 为一个身份抢占排他 Core 所有权锁（`apps/cli/src/daemon.rs:135`）。
- `ControlServer` 的 `bind` — 在宿主控制端点上监听（`apps/cli/src/daemon.rs:308`）。
- `try_run_cli_command` — 有 owner 时把 CLI 命令路由给 owner（`apps/cli/src/daemon.rs:491`）。
- `MdnsRegistration` 的 `register` — 注册 mDNS 服务（`apps/cli/src/mdns.rs:16`）。
- `discover_devices` — 浏览 mDNS 服务发现设备（`apps/cli/src/mdns.rs:51`）。
- `run_tui_command` — TUI 入口（`apps/cli/src/tui/mod.rs:92`）。
- `parse_shell_args` — 解析 shell 启动参数（`apps/cli/src/chat_runtime.rs:322`）。
- `stageArchiveUpload` — 以流式分块暂存待导入的归档（`apps/cli/src/cli/transfer.rs:293`）。
- `WEB_APP_URL` — web 入口地址 `https://web.operit.app/`（`apps/cli/src/cli/web.rs:3`）。

## 调用链

1. 用户执行 operit2 cli 命令，`run_cli_root` 剥离 `--json` 后分发命令（`apps/cli/src/cli/mod.rs:102`）。
2. run_cli_root_inner 在启动自有 Core 之前先调用 `try_run_cli_command`（`apps/cli/src/cli/mod.rs:155`）。
3. 有 owner 时 CLI 命令经 `try_run_cli_command` 走 owner 的控制通道（`apps/cli/src/daemon.rs:491`）。
4. 无 owner 时 `local_cli_core` 创建进程内本地 CLI Core（`apps/cli/src/core_proxy.rs:51`）。
5. `CliCore` 的 proxy 是包着 `SharedLocalCore` 的 `GeneratedCoreProxy`，命令经它发往 Core（`apps/cli/src/core_proxy.rs:56`）。
6. link pair 配对时在接收设备上读六位确认码（`apps/cli/src/cli/link.rs:127`），完成配对后再用 `link space join` 申请加入空间（`apps/cli/src/cli/link.rs:135`）。
7. daemon start 拉起分离的 owner 进程（`apps/cli/src/daemon.rs:906`），daemon start 用 `DAEMON_READY_TIMEOUT` 限时等待就绪（`apps/cli/src/daemon.rs:915`）。
8. rescue import 替换在线数据时要求 `--confirm`，全程不启动 Core（`apps/cli/src/rescue.rs:150`）。

## 来源

- apps/cli/Cargo.toml
- apps/cli/src/main.rs
- apps/cli/src/bootstrap.rs
- apps/cli/src/cli/mod.rs
- apps/cli/src/cli/link.rs
- apps/cli/src/cli/host_ops.rs
- apps/cli/src/cli/network_control_ui.rs
- apps/cli/src/cli/transfer.rs
- apps/cli/src/cli/web.rs
- apps/cli/src/daemon.rs
- apps/cli/src/mdns.rs
- apps/cli/src/rescue.rs
- apps/cli/src/chat_runtime.rs
- apps/cli/src/core_proxy.rs
- apps/cli/src/tui/mod.rs
- apps/cli/tests/space-stress.md
- apps/cli/tests/network_control_session.py
- apps/cli/tests/mcp_http_streaming.rs
