---
title: Operit2-wiki 大纲 v1
module: meta
sources: [outline/outline-v1.yaml]
date: 2026-11-11
---

# Operit2-wiki 大纲 v1

> 状态：已批准（Issue #1，用户主聊 2026-11-11 13:59 通过）。P0 首批 10 页已于同日写完，评审 Issue #2–#11。
>
> 生成依据：2026-11-11 六路子代理并行只读清点（Core / apps+hosts / plugins / edge+tools / docs / 定位与 Agent 回路），逐目录 git ls-files 计数 + 文件头抽查 + 关键文件 ls 核实；未全文读文件。
>
> 源码基线：AAswordman/Operit2 @ 364d1d594（2026-11-11）。全库 6335 个 tracked 文件；Rust 1236、Dart 1455、TypeScript 516。
>
> 规模：11 章、115 页，seed 文件 est_lines 合计约 580,324 行（含跨页重复引用的 seed，去重后更少；含空行注释）。

## 章节与页面

### 定位与入门（4 页）

1. **Operit2 是什么** —— 一句话定位；源于什么项目；单节点 Agent 已包含哪些能力
2. **Operit2 不是什么** —— 为什么不是“任务流转 + 手机审批”；Space 中没有固定主节点
3. **预览版与破坏性变更** —— Preview 阶段哪些东西可能 breaking；版本号规则；现有 release notes 覆盖到哪个版本
4. **第一次运行** —— 配对、发现、加入 Space 的 CLI 入口；为什么不要用默认开发 token 对公网监听

### 架构总览（6 页）

5. **整体架构** —— Core、Host、Space 各自负责什么；持久化同步与实时传输是两条什么路径
6. **CoreNode** —— 由哪三部分组成；为什么一个 CoreNode 只有一个 OperitApplication 和一个 HostManager
7. **Space** —— 只负责哪三件事；配对完成后会不会自动加入 Space
8. **Binding** —— Binding 的 key 是什么；generation 单调递增起什么作用
9. **持久化同步（总览）** —— 哪些数据进入同步、哪些永远留在本地；机制细节见第 7 章
10. **路由与转发** —— RoutedLink 外层携带什么；第一跳的硬性要求

### Core（23 页）

11. **Core 总览与 crate 边界** —— 11 个领域分组与 29 个真 crate 的关系；依赖方向；trait 注入机制
12. **基础层——共享契约与数据模型** —— HostManager 的能力边界；operit-model 的跨 crate 数据结构；Link 协议层
13. **基础层——通用工具库** —— util 的子能力；哪些带 feature 门
14. **持久化——store 聚合 crate** —— 身份/绑定/Space/偏好/插件/扩展仓库；Repository 归属规则
15. **持久化——同步存储** —— 操作日志与 Blob；冲突合并规则；工作区文件同步与运行时文件同步的存储差异
16. **持久化——数据救援** —— 离线便携救援；输入输出格式
17. **Provider——服务聚合** —— AIService 与各家适配器的关系；对话编排；STT/TTS 与 market 挂在哪里
18. **Provider——本地模型** —— 清单与注册表；模型下载走谁；LocalModelRuntimeSupport 暴露了什么（同时覆盖“本地模型”主题）
19. **工具系统——执行与注册** —— 模型输出到执行再到结果回填的完整链路；权限系统；Hook 位置
20. **工具系统——包、技能与 MCP** —— 技能包加载；MCP 接入；JS 工具运行时与 plugin JS 桥的关系
21. **插件——Plugin SDK** —— ToolPkg 包模型与加载流程；Hook 挂载点；Compose DSL；JsExecutionHost 分工
22. **插件——JS 桥** —— QuickJS 引擎；JS 如何调用宿主操作
23. **插件——主题 v1 契约** —— schema 约束了什么；为什么不做 I/O、不做主题应用（纯契约 crate）
24. **插件——SDK 代码生成与 IPC** —— 声明与客户端代码如何生成；sdk-ipc 分工；sdk-ipc-bridge 是什么
25. **Runtime 总览与 OperitApplication** —— 如何组装各子 crate 的服务；启动与生命周期；CORE_VERSION 的作用
26. **Runtime——业务服务** —— ChatServiceCore；Provider/Tool 运行时支持；终端、浏览器、STT/TTS 服务
27. **Runtime——数据与插件宿主** —— Operit1 快照导入；偏好分层；插件注册表与 ToolPkg 宿主
28. **节点——节点运行时** —— CoreNodeRouter 如何决定本地还是跨节点；SpaceRuntime 与同步服务分工
29. **节点——PeerLink 传输与路由宏** —— 传输引擎与载体；配对节流；路由元数据
30. **代理生成** —— 扫描、发射器、本地代理运行时
31. **RsLink** —— Rust 值与 Link 值互转；codegen 的 IR
32. **应用组装——CoreApplication 门面** —— 如何把 runtime、proxy、node 组装成一棵 Core 树
33. **命令层——CLI 命令编排** —— 覆盖哪些命令组；与门面的关系

### Agent 回路（8 页）

34. **Agent 回路总览** —— 一轮模型请求到工具循环再到回填的完整链路；工具调用在哪个边界切换 CoreNode
35. **会话与分支** —— 会话、消息、变体、分支如何存储；分支聊天；整段删除的特殊语义
36. **上下文压缩与摘要** —— 手动入口；自动压缩存在吗；摘要 hook 的内容；与 CoreNode 切换的时序（待重核）
37. **Subagent 并行** —— 哪几个工具；并发上限与调度；完成会不会唤醒父会话；重启后状态（待重核）
38. **记忆** —— 记忆位于哪里；scheduler/analysis/embeddings 各负责什么；如何进入 Space 同步
39. **角色卡** —— 与聊天的绑定；生命周期；提示词组装；与主题配置的关系
40. **Hooks** —— hook 类型；聊天运行时如何桥接到 ToolPkg；超时如何处理
41. **Slash 命令** —— TUI 内置命令；/resume；用户自定义加载机制存在吗（清单须以 commands.rs 实测为准）

### 应用与 Host（14 页）

42. **Android 模块应用** —— 与普通 Flutter APK 的关系；Root 执行环境；构建与发布产物
43. **命令行应用 operit2** —— 是完整 CoreNode 还是瘦客户端；link 子命令；daemon/mdns/rescue；TUI 与 Flutter UI 的能力边界
44. **Flutter 应用（主客户端）** —— 一个 Flutter 应用如何覆盖 7 个平台；Dart 与 Rust Core 如何桥接；为什么用 flutter-ohos 分支（v1 只做总览，v2 再拆）
45. **服务端应用（占位）** —— 空目录占位，无任何代码；只写一段 stub，或推迟到代码落地后再写
46. **Android Host** —— 提供的能力；终端特权边界；与 android-module 的关系
47. **Apple Host** —— macOS 与 iOS 如何复用；沙盒限制；macOS 注册了哪些 Host（macos 并入本页）
48. **iOS Host 与 ARM64 Linux 运行时** —— iOS 终端；Host 目录 bind mount；串口现状
49. **iOS 内嵌 ARM64 Linux 运行时（vendored）** —— completeness.md 如何区分实现、接线、验证；各模块分工；验收状态
50. **Linux Host** —— tools 与其他平台的异同；系统包管理；daemon 能力
51. **Windows Host** —— 终端、进程管理、daemon 与 Unix 平台的差异；应用更新；MCI；Plugin SDK IPC 走 pipe
52. **Web/WASM Host** —— 如何实现全部 host trait；插件 JS 执行为什么用浏览器原生引擎；64 KiB 共享缓冲区的同步调用机制
53. **OpenHarmony Host** —— 提供的能力；托管运行时；本地推理与 TTS 分工；应用存储根目录为什么必须显式传入
54. **Host 共享实现** —— 8 个 crate 各提供什么；共享与平台实现的界线；数据救援与 CLI rescue 的关系
55. **能力 × 平台矩阵** —— 能力全集从哪来；每个格子的判定标准；已知的“不支持”；矩阵脚本如何取数（由脚本生成，不手写）

### 插件系统（11 页）

56. **ToolPkg 2.0.0 总览** —— 是什么；与 1.0.0/1.0.1 的关系；三个版本号各指什么；三类包的打包区别
57. **清单 manifest 与安装作用域** —— 字段；device 与 space 作用域的区别；环境变量与配置归属；1.x 包在 2.0 上的兼容性
58. **JS/TS 与 Wasm 运行时** —— JS 引擎；Wasm 加载调用；注册流程；脚本超时与取消规则
59. **Compose DSL 界面** —— 如何声明界面；useEffect 订阅与清理；页面资源快照；XML 渲染桥的修订号
60. **MCP 集成** —— 是什么扩展类型；服务器配置安装启用；MCP 工具如何变成 Agent 可调用的工具；配置如何在 Space 内共享
61. **Skills 机制** —— 是什么；打包安装按需导入；与 Agent 运行时的交互（同时覆盖 Agent 回路的 Skills 主题）
62. **PackageBuilder** —— 随软件携带的插件开发 Skill；标准开发流程；2.0 新建包的 manifest 声明；1.x 迁移检查项
63. **QuickPluginCreator** —— App 内入口实际做什么；与 PackageBuilder、operit_editor 的关系（不自动生成源码）
64. **内置插件目录** —— 16 个插件各解决什么问题；哪些默认启用；单文件包与目录包的区别；character_cards 为什么这么大
65. **外置（官方可选）插件目录** —— 30 个插件；与内置的打包加载启用差异；subagents；哪些是演示性质
66. **主题即插件** —— themes 数组如何声明模板；模板与 ThemeConfig 的关系；安装、作用域、同步、更新、卸载；moss_atelier 的两套模板

### 多设备同步（8 页）

67. **同步总览** —— 哪些节点参与；数据路径；四类校验如何分工；SpacePersistenceSyncService 各管什么
68. **事务模型与同步契约** —— 记号体系；两端事务合并顺序；三种迁移的区别；最终一致如何保证
69. **工作区文件同步** —— 哪些目录参与双向复制；.operit/sync.json 默认策略；为什么跳过外部挂载与软链接
70. **VFS 挂载与文件访问边界** —— 根入口各挂到哪里；业务代码为什么不许直接拿调用方路径调 FileSystemHost；原生访问边界由什么强制执行
71. **局域网发现、配对与加入 Space** —— 发现协议；Link 的 Call/Watch/Push；配对只授予什么授权；space_join 的 refresh 流程
72. **大同步进度与联调记录** —— 首次加入与离线增量是否同链路；进度向界面发布的阈值；接收成功为什么不等于业务应用成功；2026-11-11 联调记录（模拟器，须标注边界）
73. **协议版本与构建指纹** —— 三个版本为何独立；指纹覆盖范围；新协议实现文件为什么必须加入 sources
74. **设备间路由与实时分发** —— 路由决策与承载层选路的关系；代价最小的活跃路由；一条边只发一次、再分发

### UI 与主题（4 页）

75. **Theme Studio 预览协议 v1** —— 信任边界；5 步握手；预览核校验位置；SHA-256 的作用
76. **主题渲染与媒体校验** —— L4 图片/SVG/字体/九宫格检查；校验通过前为什么不允许 Flutter 解码；如何导出为二进制
77. **主题的安装、作用域与同步** —— 作用域如何决定；偏好 owner 声明与物化协调；schema 迁移在哪里执行（须先定位实现）
78. **工具展示语义与 WebView 渲染** —— 展示信息由谁声明；声明与 tool_display_labels.json 的配合；WebView 应用缩放与页面缩放为何独立

### 模型与 Provider（3 页）

79. **模型目录与模型识别** —— 价格、上下文、能力、思考档位来自哪里；缓存过期；本地模型为什么不依赖此目录；无模型列表接口的服务商如何处理
80. **模型调用与聊天发送契约** —— SDK 对外暴露的发送方法恰好是哪三个；Rust 权威实现与 TS 导出各在哪里；发送、取消、流式输出的执行控制
81. **TTS 供应商目录** —— 七家供应商的默认模型、音频格式、音色来源；在线音色查询每页取多少条；合成与查询走哪条 HTTP 通道

### Edge 与厂商接入（16 页）

82. **Edge 总览与产品形态** —— edge/ 收纳哪三类东西；产品形态由谁决定；统一验收入口
83. **operit-edge-sdk 入口与功能开关** —— 稳定厂商入口是哪个 crate；四个功能各提供什么；两种装配方式；依赖审计脚本检查什么
84. **Edge 契约 crate** —— 只包含什么、不实现什么；为什么 Node 与 Proxy 都能依赖它
85. **Edge 节点 crate** —— 路由器接受哪些路由；原生服务如何注册；配对与空间加入为什么是两个独立步骤
86. **Edge 代理 crate** —— 如何封装 Link 请求构造与响应解码；调用方为什么不直接构造请求
87. **Scene 服务与资源格式** —— 管哪四件事；配置与资源如何以一次原子快照保存与恢复
88. **厂商接入指南** —— 三种需求各启用哪些功能；最小装配六步；配对、加入空间、授权三者为什么不能互相代替
89. **Edge 在设备空间中的职责与边界** —— 与完整 CoreNode 的区别；内置 edge 角色的权限边界；五种操作各影响什么
90. **受限设备的空间与展示链路** —— 控制状态如何发布与校验；聊天展示投影包含什么、排除什么；为什么不能代替授权
91. **ESP32 固件** —— 如何配对；Wi-Fi 如何配置；独立聊天与远端 Core 聊天的上下文规则差异；device preference 的上限与合并规则
92. **ESP32 聊天实现** —— 独立聊天如何直连模型服务；远端 Core 模式下 Edge 只保存什么；迟到结果为什么不能进入新会话
93. **ESP32 编辑器与调试工具** —— 四项能力；模拟器如何复用固件模块并通过真实 TCP 连桌面 Core
94. **ESP32 资源预算与内存实测** —— 固定堆与栈预算；峰值 252,208 字节中占比最大的三项；为什么模拟器数据不能直接当作真机整板 RAM
95. **Edge 验收记录与 V1 收尾** —— 统一验收入口覆盖哪些场景；SDK 全功能测试与 8 种功能组合依赖审计的结果；固件容量阻塞如何修复；哪些“通过”不代表真机通过
96. **无屏传感器产品** —— 暴露哪两个服务；控制台配对与加入的命令顺序；如何把演示后端换成真实 HAL 或 HttpBackend
97. **PB_SBC01_H3 机器人** —— 两个二进制各负责什么；四处边界如何分工；脸部状态文件写在哪里（跑完整 Core 只是该产品选择、不是 SDK 要求）

### 开发与工具（18 页）

98. **tools 总览** —— 收纳哪几类工具；本地构建与 CI 为什么共用同一批入口；构建产物与私密凭据各放在哪个被忽略的目录
99. **构建脚本入口** —— 按什么命名；三类构建各有哪些入口脚本；发布包文件名规则
100. **Windows MSI 安装器与卸载数据清理** —— 安装版与压缩包版卸载数据的差异；清理覆盖哪六处位置，为什么不可回滚；MsiContractTests 覆盖哪些契约
101. **发布流程** —— 版本、tag、更新通道与包资产规则由哪份文档定义；build_release.py 必须遵循什么
102. **各平台运行时工具包** —— 四个工具包各准备什么；iOS 终端后端为什么是独立的 AArch64 Linux runtime
103. **主题工具与 Web Studio** —— 主题包格式为什么是 ToolPkg；预览内核如何构建；Studio 与校验器之间走什么协议
104. **跨边界测试集** —— 152 个文件按什么维度组织；哪几类测试覆盖 Android 运行时、内置工具目录与 Compose DSL
105. **Figma 界面桥接工具** —— 当前只能做到什么，明确做不到什么；两个入口各生成什么（README 自述“尚未达到目标”，须原样保留）
106. **性能场景与基准** —— Link 性能场景为什么必须针对 CoreNodeRouter → PeerLink → CoreNode 写；性能报告必须记录哪四项
107. **协议版本检查脚本** —— 检查什么；与构建时 SHA-256 校验的关系；违反时如何防止旧哈希被替换而不升级版本
108. **白皮书 PDF 构建** —— 可编辑原稿是哪个文件；排版规范；构建依赖与字体嵌入
109. **构建指南** —— 仓库布局；各平台构建的前置要求；哪些构建输入是钉死的；Windows GNU 工具链常见问题
110. **贡献指南** —— 改动范围限制；提交前必须跑哪些本地检查；分支与提交命名；PR 流程与许可
111. **版本与发布** —— 版本号规则；release notes 覆盖到哪个版本；10 月“没有更新日志”的结论还成立吗（已过期，只有两份）
112. **排障·移动端** —— Android root shell 的能力边界与风险；iOS 性能问题如何定位；TestFlight 反馈的典型问题
113. **排障·桌面端** —— Flutter Impeller 渲染目标失败；WebView 渲染的已知问题；Windows GNU 工具链问题
114. **排障·Web 与 Web Access** —— 如何部署与访问；浏览器 Host 与 WASM 运行时的能力边界；Web 与桌面渲染差异如何排查
115. **从 Operit1 迁移** —— 快照如何检查与导入；哪些数据能带过来、哪些不能；数据救援流程；详细 FAQ 在 Operit-wiki（本页只引用，不重写）

## 评审问题（请用户在 Issue #1 回复）

1. 章节切分与页数是否合适；app-flutter 一页 223,607 行，v1 只做总览、v2 再拆，是否接受。
2. app-server 只有 .gitkeep 的空占位：保留一段 stub 说明，还是推迟到代码落地后再写。
3. Agent Plugins 1.0 可移植子集（plugin.json + skills/SKILL.md + mcp.json）：全仓 grep 无对应实现，拟写为对照说明、不单独立页，是否同意。
4. 合并处理：agent-skills 并入 plugin-skills；model-local 并入 core-provider-local-model；theme-contract 并入 plugin-theme。
5. 待重核项（写页前必须重核，不可沿用旧结论）：自动压缩是否已存在、subagents 并发上限与唤醒行为、主题 schema 3→4 迁移、slash 命令清单。

## 已知缺口与注意事项（写页前处理）

- Core 章纠正：11 个是领域分组，真 crate 是 29 个（core/Cargo.toml workspace 成员清单）。
- Agent Plugins 1.0：代码里无对应实现；Operit2 的可移植载体是 ToolPkg 2.0.0 本身。
- release notes 只有两份（preview.22 / preview.27），体例不一、序列不连续，滞后于当前版本（测试记录已称 Core preview.31）。
- 三份文档在 HEAD 上不存在，不得引用：docs/toolpkg-pre-hook-timeout.md、docs/openharmony-flutter-adaptation-checklist.md、docs/windows-webview-composition.md；docs/mcp-remote-smoke.md 也不存在；docs/edge-architecture.md 被 sync-architecture.md 引用但全仓无此文件。
- hosts/README.md 已过时（写 hosts/boards、hosts/server，均已不存在）；全库不存在统一的 Host 能力清单数据文件，矩阵必须由脚本从 host-api trait 与各平台注册生成。
- 两份白皮书 PDF 只核存在与大小，正文一行未读，定位页不得引白皮书正文。
- 旧结论待重核：自动压缩（HEAD 上有反证）、subagents（2026-10-25 走查针对合入时版本）、slash 命令数（不得沿用“18 个”）、主题 schema 3→4 迁移（本次未在代码中核实）。
- 各 README 的“目标拆分”是计划不是现状（persistence / provider / runtime / tool / plugin），写页时须以现状为准、计划只作备注。
