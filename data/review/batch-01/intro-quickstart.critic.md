# Critic：intro-quickstart.md / intro-quickstart.facts.json

核查人：独立 critic（与 writer 无关）。真理源：~/workspace/Operit2，基线 364d1d594，只读，未做 git 操作、未联网。
核查方法：65 条 fact 逐条核对 ref 文件存在性与行号范围，并读 ref 行 ±5 行核对语义；正文断言逐项对照 facts；全文 grep 禁用词（可能/大概/似乎/应该/也许）；关键主张（README 旧命令、代理脚本）在 apps/cli 与 tools/ 中 grep 复核。

## 逐条结论（65 条）

1. Preview 阶段仍会 breaking 变更 — README.md:14 — 支撑（行 14 原文一致）
2. CoreNode 经本地 Host 用文件/终端/浏览器等能力 — README.md:18 — 支撑（行 18 原文一致）
3. Space 组织协作与持久化同步，Binding 记录下一节点 — README.md:18 — 支撑（同行原文一致）
4. Space 内节点平等，加入不自动授予他设备系统权限 — README.md:20 — 支撑（行 20 原文一致）
5. 交接以工具结果已持久化、下一轮模型请求未开始为界，不搬运进行中请求/终端/浏览器会话 — README.md:22 — 支撑（行 22 原文一致）
6. CLI 提供配对/发现/连接/会话/传输/Space 管理入口，Link Access 建认证连接，PeerLink 承载请求与同步流量 — README.md:43 — 支撑（行 43 原文一致）
7. 命令参数以 operit2 --help 与 operit2 cli 实际输出为准，不得用默认开发 token 在公网监听 — README.md:53 — 支撑（行 53 原文一致）
8. Web Access 让浏览器访问运行中的 CoreNode，打开页面不自动成为 Space 独立节点 — README.md:72 — 支撑（行 72 原文一致）
9. CLI 提供 identity、storage paths、快照导出与恢复、备份检查与 Operit v1 快照检查入口 — README.md:80 — 支撑（行 80-86 列表一致）
10. 快照/配置/身份范围由命令帮助与格式版本决定，活动进程与实时会话留在原节点 — README.md:90 — 支撑（行 90 原文一致）
11. Rust CLI/TUI 的当前 CLI Host 主要覆盖 Windows、Linux 与 macOS — README.md:97 — 支撑（行 97 表格原文一致）
12. Web Access 不是自动加入 Space 的浏览器节点，也不是集中式 Agent Server — README.md:99 — 支撑（行 99 表格原文一致）
13. 仓库当前不包含可直接发布的完整 Server 产品 — README.md:103 — 支撑（行 103 表格原文一致）
14. API 密钥、设备私钥、配对密钥、会话与本地平台权限默认归属本地节点，加入 Space 不自动复制 — README.md:128 — 支撑（行 128 原文一致）
15. Full 只放宽 AI 能力限制，不提升 Host 权限，不创造 OS 没有的能力 — README.md:129 — 支撑（行 129 原文一致）
16. 开发入口要求 Rust stable 与 rustup、Flutter SDK 与 FVM、Node.js、Python 3 — README.md:156 — 支撑（行 156-159 四项列表，±5 行内齐全）
17. 不带参数运行 operit2 默认进入 TUI — README.md:175 — 支撑（行 175 原文一致）
18. Flutter App 从 apps/flutter/app 运行，fvm flutter run -d windows 中的 windows 只是示例设备名 — README.md:191 — 支撑（行 191 命令 + 行 192 说明，±5 行内齐全）
19. README 双终端步骤引用 node tools/dev_web_access_proxy.mjs，代理监听 4836 端口 — README.md:205 — 支撑（行 205 原文一致；附注：该脚本文件在基线树中不存在，见末尾第 4 项）
20. 双终端步骤要求 Flutter 上游端口与代理 --upstream-port 保持相同 — README.md:208 — 支撑（行 208 原文一致；附注同第 19 条）
21. link 子命令清单 13 项（discover、qr、pair、unpair、peers、prompts、listen、session、space、doctor、control、stream-probe、edge-call） — apps/cli/src/cli/link.rs:1299 — 支撑（行 1299 usage JSON 与行 1303-1318 打印清单一致；grep 复核 run_link_command 分发行 36-50 无 serve/connect）
22. link listen 接受 http/ws/tcp/serial/bluetooth，支持 --automatic-port、--fixed-port 与 --bind — apps/cli/src/cli/link.rs:1309 — 支撑（行 1309 用法 + 行 260-275 参数解析与传输映射一致）
23. link discover 接受 --timeout-ms — apps/cli/src/cli/link.rs:1304 — 支撑（行 1304 用法 + 行 682-686 解析一致）
24. link discover 默认超时 2000 毫秒 — apps/cli/src/cli/link.rs:679 — 支撑（行 679 `timeout_ms = 2000_u64`）
25. link space show 显示 Space 名称与成员数量 — apps/cli/src/cli/link.rs:729 — 支撑（行 733-734 打印 spaceName 与 members.len()）
26. link space join 接受设备名或编号作为选择器 — apps/cli/src/cli/link.rs:1310 — 支撑（行 1310 用法 `join [device-name|number]` + select_link_choice 按名或序号解析）
27. link qr 接受 http/ws/tcp，支持 --bind 与 --no-discovery — apps/cli/src/cli/link.rs:1305 — 支撑（行 1305 用法 + 行 252-270 参数解析一致）
28. identity list 列出本地身份与当前活动身份 — apps/cli/src/cli/mod.rs:205 — 支撑（行 205-212 list 分支取 identities 与 activeIdentityId）
29. storage paths 由 storage 命令的 paths 子命令实现 — core/crates/command/core/src/commands/storage.rs:16 — 支撑（行 16-22 paths 分支）
30. export snapshot <path> 导出快照 — apps/cli/src/cli/transfer.rs:53 — 支撑（行 53-56 snapshot 分支调 export_snapshot）
31. backup create 等价于导出快照 — apps/cli/src/cli/transfer.rs:121 — 支撑（行 121 `"create" => export_snapshot`）
32. backup restore 导入快照 — apps/cli/src/cli/transfer.rs:122 — 支撑（行 122 `"restore" => import_snapshot`）
33. backup inspect 检查快照并打印格式版本、创建时间与文件清单 — apps/cli/src/cli/transfer.rs:123 — 支撑（行 123-143 打印 formatVersion、createdAt、includes）
34. backup inspect-operit1-snapshot 检查 Operit v1 快照 — apps/cli/src/cli/transfer.rs:146 — 支撑（行 146-150 分支存在）
35. 不带参数运行 operit2 进入 TUI — apps/cli/src/main.rs:57 — 支撑（行 62-64 args 为空进 run_tui_command，±5 行内齐全）
36. operit2 cli version 显示 CLI、Core 与 Link 版本 — apps/cli/src/cli/mod.rs:129 — 支撑（行 132-134 version 分支调 print_local_version；该函数打印 CLI/Core/Link 三个版本）
37. web open 只打开 https://web.operit.app/，不启动本地服务器，不把凭证放进 URL — apps/cli/src/cli/web.rs:6 — 支撑（行 4 常量 URL + 行 6-16 仅 open 分支并打开该 URL）
38. 发现查询 _operit-link._tcp.local.，不枚举 IP 地址 — docs/device-space-lan-discovery.md:5 — 支撑（行 5 原文一致）
39. 仅在监听器运行且 discoveryEnabled 开启时广播，默认 HTTP 与 WebSocket、OS 分配端口、绑定 0.0.0.0 — docs/device-space-lan-discovery.md:7 — 支撑（行 6-8 原文一致）
40. TXT 必须含 nodeId、displayName、transports，不完整广播被拒绝并给出诊断 — docs/device-space-lan-discovery.md:9 — 支撑（行 9-10 原文一致）
41. 添加设备对话框 5 秒主动扫描，刷新重启共享查询并保留订阅句柄 — docs/device-space-lan-discovery.md:11 — 支撑（行 11-13 原文一致）
42. 本地与已配对设备有意从添加设备结果中排除，包括当前离线的已配对设备 — docs/device-space-lan-discovery.md:14 — 支撑（行 14-16 原文一致）
43. 离线已配对网络设备按已发现地址排序重连，已保存地址作后备，每备选地址连接与认证尝试有界 — docs/device-space-lan-discovery.md:19 — 支撑（行 17-20 原文一致）
44. 已发现 nodeId 只是拨号提示，握手验证预期节点并证明持有配对密钥后，成功地址与传输方式持久化到出站配对记录 — docs/device-space-lan-discovery.md:21 — 支撑（行 21-24 原文一致）
45. 认证失败不改变已保存端点，并发解除配对或凭证替换不被进行中连接撤销 — docs/device-space-lan-discovery.md:25 — 支撑（行 25-27 原文一致）
46. Windows、Linux、Android 与 OHOS 用共享原生 mDNS 提供方，守护进程与浏览器工作线程归 Host 所有 — docs/device-space-lan-discovery.md:32 — 支撑（行 32-34 原文一致）
47. iOS 与 macOS 用系统 Bonjour DNS-SD 守护进程，不用应用自有 UDP 组播套接字，macOS CLI 安装同样 Apple 发现 Host — docs/device-space-lan-discovery.md:37 — 支撑（行 37-41 原文一致）
48. 两端须放行本地组播 DNS（UDP 5353 到 224.0.0.251 / ff02::fb）与到已广播监听器端口的入站连接 — docs/device-space-lan-discovery.md:55 — 支撑（行 55-57 原文一致）
49. v2 连接码携带节点 ID、显示名、实时网络地址与 5 分钟有效的随机邀请密钥 — docs/device-space-lan-discovery.md:108 — 支撑（行 107-109 原文一致）
50. 扫码确认通过已有 SPAKE2 配对交换认证并提交 Space 加入请求，该路径不显示手动配对码对话框 — docs/device-space-lan-discovery.md:110 — 支撑（行 110-112 原文一致）
51. 相机扫码在 Android、iOS、macOS 与 web 可用，其他 Host 导入图片或粘贴连接码 — docs/device-space-lan-discovery.md:103 — 支撑（行 103-105 原文一致）
52. qr http --no-discovery 在无守护进程或 TUI 属主运行时启动 HTTP 监听器并保持到 Ctrl-C — docs/device-space-lan-discovery.md:130 — 支撑（文档行 132-134 + 代码 run_link_qr 行 149-189：无属主时新建 Core 应用、启动监听器、循环等 Ctrl-C）
53. link qr 的 --json 以无终端转义序列的形式输出连接信息 — docs/device-space-lan-discovery.md:135 — 支撑（行 135-136 原文一致）
54. 交互式 link session 中 qr 显示同一连接码，pair <connection-code> 完成 QR 配对，space 命令提交或检查加入请求 — docs/device-space-lan-discovery.md:138 — 支撑（行 137-139 原文一致）
55. 部署服务器须为每个应用资产发 COOP same-origin、COEP require-corp、CORP same-origin，线程化 Sherpa ONNX WASM 才能跑本地 STT/TTS — apps/flutter/app/web/README.md:9 — 支撑（行 5-12 三头 + 目的句，±5 行内齐全）
56. CLI 暴露的 Link Access 服务器不提供 Web 前端 — apps/flutter/app/web/README.md:14 — 支撑（行 14 原文一致）
57. FVM 固定 Flutter SDK 从应用根目录读 web_dev_config.yaml，内置开发服务器在 http://127.0.0.1:4835 并发三头，不需单独 Node 进程或代理端口 — apps/flutter/app/web/README.md:20 — 支撑（行 18-22 原文一致）
58. Web 开发用 fvm flutter run -d edge，Chrome 用 -d chrome，手动浏览器用 -d web-server 并访问 127.0.0.1:4835 — apps/flutter/app/web/README.md:26 — 支撑（行 26-30 原文一致，±5 行内齐全）
59. VS Code 选 Operit2: Web (isolated) 后按 F5 启动 Edge，无需预启动代理任务 — apps/flutter/app/web/README.md:34 — 支撑（行 33-35 原文一致）
60. 跨域隔离头启用跨域隔离，不代表对远程 API 无限制 CORS 访问，远程 API 仍须自身 CORS 策略授权开发源 — apps/flutter/app/web/README.md:37 — 支撑（行 37-39 原文一致）
61. runtime/src 放 TS 源码，runtime/generated 放生成 JS/WASM 产物与 v86 客户机运行时，runtime/vendor 放 MessagePack 等第三方静态文件 — apps/flutter/app/web/README.md:47 — 支撑（行 47-50 原文一致）
62. 原生应用与 CLI 不打包也不提供 web 目录，设置入口与 web open 打开 https://web.operit.app/，不启动本地服务器，不把凭证放进 URL — apps/flutter/app/web/README.md:52 — 支撑（行 52-54 原文一致）
63. 连接另一台设备是独立的节点监听与配对操作，不是 Web Access 服务器生命周期 — apps/flutter/app/web/README.md:55 — 支撑（行 55-56 原文一致）
64. ServiceDiscovery 日志记录选定原生浏览接口、解析到的地址与端口、守护进程错误、广播与扫描总数 — docs/device-space-lan-discovery.md:46 — 支撑（行 46-48 原文一致）
65. RuntimePeerService 记录原始广播总数与本地、已配对、无效、可添加四类过滤总数 — docs/device-space-lan-discovery.md:51 — 支撑（行 51-53 原文一致）

## 关键主张复核（grep 实证）

- `link serve`：run_link_command 分发（link.rs:36-50）与用法清单（link.rs:1299-1318）均无 serve；README.md:46 的 serve 示例与代码不符，正文“以代码为准”的处理正确。
- `link connect`：同上，分发与用法清单均无 connect；README.md:48 的 connect 示例与代码不符，正文处理正确。
- `link space join <session-name>`：README.md:49 确为该写法；代码用法为 `join [device-name|number]`（link.rs:1310），选择器按设备名或序号解析（select_link_choice），正文“不是会话名”的纠正正确。
- `node tools/dev_web_access_proxy.mjs`：README.md:205 确有该引用；但该文件在基线树中不存在（`ls tools/dev_web_access_proxy.mjs` 失败）。README 的双终端步骤因此在当前树上不可执行，正文只写了“两份文档说法不同”，未点明脚本本身缺失（见末尾第 4 项）。

## 正文一致性与禁查

- 正文断言均与 facts 一致，未发现超出 facts 支撑范围的发挥；“数据流向”一段为各 facts 的串联，未引入新事实。
- 禁用词：全文 grep 可能/大概/似乎/应该/也许，零命中。
- 单平台写成全平台：未发现。平台差异均有注明（CLI Host 覆盖 Win/Linux/macOS、相机扫码四平台、mDNS 提供方分平台、fvm run -d windows 标示例设备名）。

## 需修改（4 项，均为正文小修，facts.json 不用动）

1. 行号引用：正文“CLI 从仓库根目录运行：cargo check …，cargo run … --help 查看帮助（README.md:169）”——`--help` 命令在 README.md:170，不在 169。改为引用 README.md:169-170。
2. 行号引用：正文四条 fvm 命令只引 README.md:188——四条命令跨行 188-191。改为引用 README.md:188-191。
3. 缺引用：正文“Flutter App 的 Host 能力在 Android、Windows、Linux、macOS、iOS、OpenHarmony 与浏览器模式下各不相同。”无引用。补 README.md:96（平台表 Flutter App 行）。
4. 缺关键事实：正文记录了 README 与 web README 在开发代理上的说法冲突，但未说明 `tools/dev_web_access_proxy.mjs` 在基线树中根本不存在——按 README 步骤执行会在第二步就失败。建议在该段补一句：“另注意：该脚本在当前仓库树中不存在，README 的双终端步骤目前不可直接执行。”（经 `ls` 核实缺失；若后续补回文件，本句须随之删除。）

## 总结论

**需修改**——65 条事实全部支撑，0 条不支撑，0 条存疑；正文无禁用词、无平台泛化、无超范围发挥。仅正文有 4 处小修（2 处行号引用、1 处补引用、1 处补“代理脚本文件缺失”说明），修完即可通过，无需打回重写。
