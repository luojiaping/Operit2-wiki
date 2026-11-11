# arch-overview critic（独立核查）

- 核查对象：`review/batch-01/arch-overview.md` 与 `arch-overview.facts.json`（99 条）
- 真理源：`~/workspace/Operit2`，基线 364d1d594，只读；未做 git 操作、未联网
- 核查方法：逐条核对 ref 文件存在性、行号范围、ref 行 ±5 行内的语义支撑；核对正文引用与 facts 的一致性；grep 禁用词；逐个核实 §8 对照表的 Cargo.toml name 字段；核实 quality.json 断链主张
- 结论速览：99 条 facts 中 98 条支撑、1 条存疑、0 条不支撑；正文另有 3 处引用行号问题（1 处错误、2 处不精确）

## 逐条结论（facts.json）

- [1] 一句话定位 An Agent core that connects your device space — README.md:3 — 支撑（第 3 行为副标题原文）
- [2] Preview 阶段仍可能 breaking changes — README.md:14 — 支撑（原文 may still undergo breaking changes；“可能”是对原文 may 的直译，不是 hedge）
- [3] 每个运行 Core 的实例称 CoreNode，经本地 Host 用文件/终端/浏览器能力 — README.md:18 — 支撑
- [4] Space 组织协作与持久化同步，Binding 记录哪个节点继续执行 — README.md:18 — 支撑
- [5] Space 内节点地位对等，Linux 云设备多干活也不成固定主节点 — README.md:20 — 支撑
- [6] 加入 Space 不自动授予其他设备系统权限 — README.md:20 — 支撑
- [7] 任务交接边界：工具结果已持久化且下一轮模型请求尚未开始 — README.md:22 — 支撑
- [8] 交接不移动进行中的模型请求、终端进程或浏览器会话 — README.md:22 — 支撑
- [9] 单节点 Agent 能力各平台不完全相同，取决于 Host 描述/系统权限/已装服务/用户批准 — README.md:39 — 支撑
- [10] CLI 提供配对/发现/连接/会话/传输方式/Space 成员管理入口，含 serve/discover/connect/space join/space show — README.md:47 — 支撑（命令与 README.md:46-50 逐一对应）
- [11] 不用默认开发 token 对公网监听，不把 token/私钥/真实业务数据放进公开日志或截图 — README.md:53 — 支撑
- [12] Web Access 让浏览器访问运行中的 CoreNode，打开页面不会自动成 Space 内独立节点 — README.md:72 — 支撑
- [13] Flutter App 是移动与桌面主图形入口，也能托管 CoreNode；Host 与构建条件在 7 平台上不同 — README.md:96 — 支撑
- [14] 当前 CLI Host 主要覆盖 Windows、Linux、macOS — README.md:97 — 支撑
- [15] PB_SBC01_H3 是运行完整 Core 的 Linux 硬件控制入口，应用入口 edge/boards/pb_sbc01_h3 — README.md:98 — 支撑
- [16] WebAssembly/browser Host 是浏览器运行时本地能力边界，与 Web Access 是两条不同工程路径 — README.md:100 — 支撑
- [17] Linux 云设备是 Space 内普通 CoreNode，始终在线可多干活，但不因此获得中心身份 — README.md:101 — 支撑
- [18] ESP32 Edge Node 拥有本地配置与有界操作，参与 Space 控制并可消费 Core 服务，无完整业务副本 — README.md:102 — 支撑
- [19] 当前仓库没有可直接发布的完整 Server 产品 — README.md:103 — 支撑
- [20] 能力模型外层两层是 App Runtime Sandbox 与 Host Authorization — README.md:115 — 支撑（第 0 层在 112 行，在 ref±5 内）
- [21] 能力模型内层两层是 AI Capability Limit（ReadOnly、WorkspaceWrite、Full）与 User Tool Approval — README.md:118 — 支撑（第 3 层在 121 行，在 ref±5 内）
- [22] Space 成员资格不授予其他节点读本机文件/用本机终端/获管理员/root 能力 — README.md:127 — 支撑
- [23] API 密钥/设备私钥/配对密钥/会话与本地平台权限默认属节点本地，加入 Space 不自动复制 — README.md:128 — 支撑
- [24] Full 只表示放宽 AI 能力限制，不提升 Host 特权，也不创造操作系统没有的能力 — README.md:129 — 支撑
- [25] 标记为 target/plan/direction of evolution 的架构文档不表示各平台已实现；当前实际行为以源码/命令帮助输出/构建结果/目标平台运行时结果为准 — README.md:246 — 支撑（246 行原文逐句对应）
- [26] 执行模型只包含 CoreNode 与 Binding 两个概念 — docs/core-node-space-binding-architecture.md:24 — 支撑（21-26 行）
- [27] Space 是节点成员、路由与持久化同步的范围，不是执行容器，不拥有 Agent、聊天或运行时 — docs/core-node-space-binding-architecture.md:28 — 支撑
- [28] 架构中不引入 Chat Core、Agent Core、Env、Placement、Lease、Circuit、Capability 或远程数据放置 Ownership 模型 — docs/core-node-space-binding-architecture.md:34 — 支撑
- [29] CoreNode 由 nodeId、OperitApplication、LocalCoreProxy、HostManager 组成 — docs/core-node-space-binding-architecture.md:44 — 支撑（结构体 42-47 行）
- [30] 每个 CoreNode 只有一个 OperitApplication 和一个 HostManager — docs/core-node-space-binding-architecture.md:479 — 支撑（§10 约束原文）
- [31] CoreNode 之间地位对等，监听方/发起方/执行方只是一次连接或调用中的角色 — docs/core-node-space-binding-architecture.md:57 — 支撑
- [32] Space 由 spaceId 与 members（Set<nodeId>）组成 — docs/core-node-space-binding-architecture.md:64 — 支撑（结构体 63-66 行）
- [33] Space 只负责三件事：确定协作范围、确定哪些已配对连接可承载 Space 流量、确定持久化数据在哪些 CoreNode 间持续同步 — docs/core-node-space-binding-architecture.md:69 — 支撑（69-74 行）
- [34] Space 不表达执行位置，也不表达数据归属 — docs/core-node-space-binding-architecture.md:77 — 支撑
- [35] 配对完成后不会自动加入设备空间 — docs/core-node-space-binding-architecture.md:93 — 支撑
- [36] Binding 由 key、nodeId、generation 组成，只表达 key 对应的下一次路由执行由哪个 CoreNode 完成 — docs/core-node-space-binding-architecture.md:141 — 支撑（结构体 133-138 行 + 141-143 行）
- [37] 聊天路由直接使用现有 chatId 作为 key；Binding 不表示业务数据位于目标节点 — docs/core-node-space-binding-architecture.md:146 — 支撑
- [38] 每次比较写入成功后 generation 单调递增，同时标识目标节点即将执行的 continuation — docs/core-node-space-binding-architecture.md:171 — 支撑
- [39] list_core_nodes 只读取本机已经同步的 Space 成员视图 — docs/core-node-space-binding-architecture.md:159 — 支撑
- [40] switch_core 调用时按同一份路由视图校验目标，目标不是 Space 成员或当前不可达时工具直接返回失败 — docs/core-node-space-binding-architecture.md:164 — 支撑
- [41] 内置 admin、user、relay 角色均具有 storage.provide；业务副本同步只在双方具备 storage.provide 且实际提供 Core 存储服务时运行 — docs/core-node-space-binding-architecture.md:185 — 支撑（185-188 行）
- [42] SpacePersistenceSyncService 是 CoreNode 启动后长期运行的服务，经认证路由与可达成员持续交换本地操作日志和向量时钟 — docs/core-node-space-binding-architecture.md:202 — 支撑
- [43] 每个同步周期对每个可达成员先发送一次常量大小的 syncClockDigest 探针 — docs/core-node-space-binding-architecture.md:218 — 支撑（217-219 行）
- [44] 同步页单侧一页最多 DEFAULT_SYNC_PAGE_BYTES（4 MiB） — docs/core-node-space-binding-architecture.md:233 — 支撑
- [45] 身份私钥、两两配对密钥和 session、HostManager 平台状态、本机监听地址、本机平台能力与临时交互句柄保持节点本地，不进入 Space 持久化同步 — docs/core-node-space-binding-architecture.md:258 — 支撑（258-263 行完整列表；fact 未列“应用界面缩放”一项，属省略而非错述）
- [46] 实时传输承载 Core call、Core watch、Core push、stream event、Agent turn continuation、Host interaction response、Space 路由控制消息 — docs/core-node-space-binding-architecture.md:274 — 支撑（271-277 行列表）
- [47] 实时传输不负责复制持久化业务数据；实时 continuation 要求的同步时钟只是交接屏障，不表示数据迁移 — docs/core-node-space-binding-architecture.md:280 — 支撑
- [48] RoutedLink 由 spaceId、targetNodeId、ttl、payload 组成；外层不携带 chatId、Binding、envId、文件路径或 Host 配置 — docs/core-node-space-binding-architecture.md:294 — 支撑（结构体 289-294 行 + 297-298 行）
- [49] 每个 CoreNode 保存 Space 拓扑，第一跳必须是当前活跃且获准承载该 Space 流量的直接 Peer Link — docs/core-node-space-binding-architecture.md:312 — 支撑
- [50] ttl 每转发一次减一；无有效路径、TTL 用尽或目标不属于 Space 时属于路由失败 — docs/core-node-space-binding-architecture.md:321 — 支撑
- [51] 本地 App 始终首先进入本机 CoreNodeRouter — docs/core-node-space-binding-architecture.md:348 — 支撑
- [52] 只有模型执行、工具循环、取消当前执行与实时执行状态进入 Binding 路由；聊天历史读取、配置编辑等持久化数据操作在本地 Core 执行 — docs/core-node-space-binding-architecture.md:362 — 支撑
- [53] 请求类型由真实 Core 方法上的 #[operit_core_route(...)] 声明，经 typed Core codegen 生成；未标注的方法始终留在本地 Core — docs/core-node-space-binding-architecture.md:371 — 支撑
- [54] 切换 CoreNode 的边界是工具调用已完成、工具结果已持久化、下一轮模型请求尚未发起 — docs/core-node-space-binding-architecture.md:385 — 支撑（385-387 行）
- [55] requiredClock 是持久化同步屏障；execution generation 来自 Binding 比较写入 — docs/core-node-space-binding-architecture.md:407 — 支撑
- [56] 每轮模型请求开始前，CoreNode 必须确认 Binding(chatId) 指向自己；只有当前执行节点能够提交 Agent 发起的切换 — docs/core-node-space-binding-architecture.md:416 — 支撑
- [57] 每一跳只接受已配对 Peer 的签名流量；收到 RoutedLink 后验证当前节点/上一跳/targetNodeId 属于 spaceId、payload 类型允许转发 — docs/core-node-space-binding-architecture.md:460 — 存疑（前三项校验在 463-465 行，ref±5 内；第 4 项“payload 类型允许在该 Peer Link 上转发”在 466 行，超出 ref±5 一行。修正：ref 改为 :463，即可覆盖整张校验清单 462-466 行）
- [58] Space 把多个已配对 CoreNode 组成同一个持续同步网络；Binding 决定一个聊天的下一步在哪个 CoreNode 执行；实时转发层把现有 Link 调用和 Agent continuation 送到该节点 — docs/core-node-space-binding-architecture.md:493 — 支撑
- [59] operit-store 负责操作日志、收据、Binding 与各存储 owner 的提交，以及拓扑记录与确定性路由计算 — docs/core-node-space-binding-architecture.md:442 — 支撑（§8 表格原文）
- [60] operit-link 负责 Call、Watch、Push、事件、错误和流的协议契约 — docs/core-node-space-binding-architecture.md:443 — 支撑
- [61] §8 表格中的 node/peer-link 负责认证连接承载、心跳、请求关联和连接生命周期 — docs/core-node-space-binding-architecture.md:444 — 支撑
- [62] §8 表格中的 node/runtime 负责配对与成员策略、CoreNodeRouter、逐跳转发、共享 Watch 与同步调度 — docs/core-node-space-binding-architecture.md:445 — 支撑
- [63] operit-proxy-local 负责本机类型化代理与业务分发 — docs/core-node-space-binding-architecture.md:446 — 支撑
- [64] §8 表格中的 runtime/application 负责单节点业务运行时、模型工具循环与 handoff — docs/core-node-space-binding-architecture.md:447 — 支撑
- [65] §8 表格中的 application/core 负责组装 Core、Proxy、Node 与 Host 的应用树 — docs/core-node-space-binding-architecture.md:448 — 支撑
- [66] §8 的 node/peer-link 对应当前 crate operit-peer-link — core/crates/node/peer-link/Cargo.toml:2 — 支撑（name = "operit-peer-link"；且为 core/Cargo.toml workspace 成员）
- [67] §8 的 node/runtime 对应当前 crate operit-node-runtime — core/crates/node/runtime/Cargo.toml:2 — 支撑（name = "operit-node-runtime"；workspace 成员）
- [68] §8 的 runtime/application 对应当前 crate operit-runtime — core/crates/runtime/application/Cargo.toml:2 — 支撑（name = "operit-runtime"；workspace 成员）
- [69] §8 的 application/core 对应当前 crate operit-core-application — core/crates/application/core/Cargo.toml:2 — 支撑（name = "operit-core-application"；workspace 成员）
- [70] operit-host-api 提供 host 能力 trait 与 HostManager；平台 host 实现该边界，core crate 通过 trait 消费 host 行为 — core/CRATE_BOUNDARIES.md:9 — 支撑
- [71] operit-util 提供共享工具代码、流 helper、日志 helper、序列化、路径布局常量与媒体/文档 helper — core/CRATE_BOUNDARIES.md:11 — 支撑
- [72] operit-model 提供 runtime、store、tools、providers、proxy 生成与 host-facing DTO 共用的数据结构 — core/CRATE_BOUNDARIES.md:13 — 支撑
- [73] operit-store 是持久化层，含 DAO/repository 代码、偏好存储、SQLite/ObjectBox 风格 helper、同步存储与存储 host 注册 — core/CRATE_BOUNDARIES.md:15 — 支撑
- [74] operit-plugin-sdk 提供可发布的插件契约、独立 JS 包解析与管理、固定 JS 工具 API、Compose DSL、ToolPkg 归档解析/加载、完整包查询、hook 分发与 JS 执行契约 — core/CRATE_BOUNDARIES.md:17 — 支撑
- [75] operit-plugin-theme 只含运行时无关的 theme v1 schema；只依赖公共生态 crate；不做 I/O、Host 调用、运行时启动、插件执行、持久化或主题应用 — core/CRATE_BOUNDARIES.md:20 — 支撑（20-25 行）
- [76] operit-tools 是工具系统，含内置工具、ToolPkg、MCP、skill 包、权限感知工具注册、包生命周期管理、工具执行元数据与工具侧运行时支持 trait — core/CRATE_BOUNDARIES.md:27 — 支撑
- [77] operit-local-models 提供本地模型清单、已装模型注册表契约、存储路径 helper 与本地 STT/TTS/聊天会话接口；运行时侧操作经 LocalModelRuntimeSupport 暴露 — core/CRATE_BOUNDARIES.md:31 — 支撑
- [78] operit-providers 提供 provider 契约与内置实现，含 AIService、provider 请求/结果/流类型、ProviderRuntimeSupport、LLM 适配器、对话编排、TTS/STT/market 服务 — core/CRATE_BOUNDARIES.md:34 — 支撑
- [79] operit-js-bridge 提供 JavaScript 引擎集成与 JS 侧 ToolPkg 执行面，实现 operit-plugin-sdk 暴露的 JS 执行 trait — core/CRATE_BOUNDARIES.md:38 — 支撑
- [80] operit-runtime 是父编排 crate，拥有应用启动、服务装配、插件资产、偏好、工作区服务、聊天服务生命周期、provider 支持实现与 tool 支持实现 — core/CRATE_BOUNDARIES.md:41 — 支撑
- [81] operit-proxy-local 是构建时代理生成与本地分发，扫描选定公共面并生成 Rust 与 Dart 代理代码 — core/CRATE_BOUNDARIES.md:44 — 支撑
- [82] operit-link 提供传输协议与 client/server 原语 — core/CRATE_BOUNDARIES.md:48 — 支撑
- [83] operit-edge-contract 只含共享 Edge Service 地址与属性名，不含 Host 实现或 Link 分发 — core/CRATE_BOUNDARIES.md:49 — 支撑
- [84] operit-node-edge 是轻量设备侧 Edge Core 节点，是设备能力节点，不是 Space 架构定义的完整 CoreNode 组合 — core/CRATE_BOUNDARIES.md:51 — 支撑
- [85] operit-command-core 是面向 CLI 的命令层，构建于 runtime 与拆分后的 core crate 之上 — core/CRATE_BOUNDARIES.md:56 — 支撑
- [86] 依赖方向是 plugin-sdk/host-api → util → model → store → tools/local-models/providers/js-bridge → runtime → core-proxy/command-core — core/CRATE_BOUNDARIES.md:63 — 支撑（原文用 `->`，语义一致）
- [87] runtime 可依赖全部子 crate；子 crate 不得依赖 operit-runtime — core/CRATE_BOUNDARIES.md:66 — 支撑
- [88] operit-plugin-sdk 只依赖公共生态 crate — core/CRATE_BOUNDARIES.md:74 — 支撑
- [89] operit-plugin-theme 只依赖公共生态 crate；runtime 与未来浏览器/审计适配器可消费它，绝不反向 — core/CRATE_BOUNDARIES.md:75 — 支撑
- [90] ToolRuntimeSupport 由 operit-runtime 在 services/ToolRuntimeSupportService.rs 实现 — core/CRATE_BOUNDARIES.md:104 — 支撑（104-108 行）
- [91] ProviderRuntimeSupport 由 operit-runtime 在 services/ProviderRuntimeSupportService.rs 实现 — core/CRATE_BOUNDARIES.md:109 — 支撑（109-112 行）
- [92] LocalModelRuntimeSupport 定义本地模型侧请求；operit-runtime 拥有具体实现 — core/CRATE_BOUNDARIES.md:113 — 支撑（113-116 行）
- [93] JsExecutionHost 定义完整的 JavaScript 到应用的执行边界；operit-tools 以真实工具、包、资源与 IPC 逻辑实现它 — core/CRATE_BOUNDARIES.md:123 — 支撑
- [94] JsExecutionProvider 定义引擎 provider 边界；operit-js-bridge 以 QuickJsExecutionProvider 实现，operit-runtime 把 provider 注入 operit-tools — core/CRATE_BOUNDARIES.md:126 — 支撑
- [95] Host 集成位于 operit-host-api 之后；HostManager 拥有活跃 host 能力集与生命周期侧 host 句柄 — core/CRATE_BOUNDARIES.md:140 — 支撑
- [96] 仓库与持久化数据结构属于 operit-store；可复用值模型属于 operit-model；runtime 服务可组合仓库，但仓库所有权留在 store — core/CRATE_BOUNDARIES.md:150 — 支撑
- [97] operit-proxy-local 是桌面投影层，扫描选定公共面并生成面向传输的 Rust 与 Dart 代理代码 — core/CRATE_BOUNDARIES.md:181 — 支撑
- [98] operit-proxy-edge 是 Edge Service 的类型化投影；operit-edge-contract 只含稳定 Edge 地址，远端载体无需导入本地 Edge Node 即可使用同一契约 — core/CRATE_BOUNDARIES.md:184 — 支撑
- [99] 两个 proxy crate 都不拥有运行时行为、host 实现、provider 逻辑、工具逻辑或存储 — core/CRATE_BOUNDARIES.md:187 — 支撑

## 正文 .md 核查（超出 facts.json 的断言与引用）

正文其余断言均有 facts 支撑；以下 3 处引用行号有问题，均不在 facts.json 内（facts.json 没有覆盖这三句）：

- [M1] 概述第二段：跨设备定位句引 `README.md:12` — 不支撑（行号错误）。`README.md:12` 是“The project grew out of Operit's Android Agent practice…”，与断言无关；断言原文在 `README.md:10`（“Operit2 is an open-source, cross-device Agent project…so conversations, tasks, and context can continue across a personal device space”）。修正：正文引用改为 `README.md:10`，并建议在 facts.json 补一条 fact（ref README.md:10）。
- [M2] AI 速览 `Space` 条引用 `docs/core-node-space-binding-architecture.md:64` — 存疑（行号不精确）。64 行是结构体成员 `spaceId`，支撑的是组合定义（即 fact [32]）；gloss“节点成员、路由与持久化同步的范围”出自 28 行（即 fact [27]）。修正：引用改为 `:28`，或把 gloss 改写为组合定义。
- [M3] AI 速览 `Binding` 条引用 `docs/core-node-space-binding-architecture.md:134` — 存疑（行号不精确）。134 行是结构体成员 `key`；gloss“key 对应的下一次路由执行由哪个 CoreNode 完成”出自 141-143 行（即 fact [36]）。修正：引用改为 `:141`。

其余正文引用逐一核过，均与 facts 一致：

- 调用链第 2 步引 `:354`：354 行起的代码块确为 ordinary request → LocalCoreProxy、annotated Binding request → Binding(key) → target CoreNode，支撑。
- 调用链第 3 步引 `:395`：390-396 行的 switch_core 流程（验证可达成员、同一事务持久化、Router 比较写入 Binding、Binding record 与 operation 进 Link route context）与正文复述一致，支撑。
- 调用链第 4 步引 `:407`：402-408 行（等待 requiredClock、加载已同步 assistant 消息、用 switch_core 工具结果发起下一轮）支撑。
- 调用链第 5 步引 `:432`：431-434 行（响应流属于一次用户发起的 execution、最初接受请求的 CoreNodeRouter 保持上游流）支撑。
- “子 crate 需要父级行为时定义 trait 并消费 trait 对象，由父级 runtime 实现并安装”引 `core/CRATE_BOUNDARIES.md:99`：98-100 行原文支撑。
- AI 速览其余条目：`CoreNode` :42（结构体首行）、`OperitApplication` :44 / `LocalCoreProxy` :45（结构体成员，gloss 为合理转述）、`HostManager` :140、`CoreNodeRouter` :348、`SpacePersistenceSyncService` :202、`RoutedLink` :289（结构体首行）、`operit-runtime` :41、`operit-host-api` :9——均支撑。
- 正文中 `[[sync-overview]]`、`[[core-overview]]` 内部链接指向大纲内尚未撰写的页面，属正常前向引用，非缺陷。
- 禁用词：正文全文 grep 可能/大概/似乎/应该/也许——0 命中。facts.json 唯一一处“可能”在 [2]，系 README 原文 may 的直译，非 hedge。
- 单平台写成全平台：未发现。平台断言均已限定：CLI Host 主要覆盖 Windows/Linux/macOS（fact [14]）；Flutter Host 与构建条件分平台不同（fact [13]）；ESP32、PB_SBC01_H3、Linux 云设备、Server 缺位均按平台/形态单独表述。

## §8 旧名改写对照表核查（逐个核实 Cargo.toml name 字段）

| 架构文档 §8 写法 | 本页改写 | 核实结果 |
| --- | --- | --- |
| node/peer-link | operit-peer-link | 支撑：`core/crates/node/peer-link/Cargo.toml:2` name = "operit-peer-link"，且为 core workspace 成员 |
| node/runtime | operit-node-runtime | 支撑：`core/crates/node/runtime/Cargo.toml:2` name = "operit-node-runtime"，且为 core workspace 成员 |
| runtime/application | operit-runtime | 支撑：`core/crates/runtime/application/Cargo.toml:2` name = "operit-runtime"，且为 core workspace 成员 |
| application/core | operit-core-application | 支撑：`core/crates/application/core/Cargo.toml:2` name = "operit-core-application"，且为 core workspace 成员 |
| operit-store | operit-store（不变） | 支撑：与 §8 表格原文一致，无改写 |
| operit-link | operit-link（不变） | 支撑：与 §8 表格原文一致，无改写 |
| operit-proxy-local | operit-proxy-local（不变） | 支撑：与 §8 表格原文一致，无改写 |

对照表 7 行职责描述与 arch 文档 §8 表格 442-448 行逐字对应。quality.json 第二条 finding（§8 使用目录式旧名）属实，改写正确。

## quality.json 断链主张核查

- `arch-overview.quality.json` 第一条：架构文档第 79 行以相对链接引用 `[Edge 架构](edge-architecture.md)`，但全仓库不存在 `docs/edge-architecture.md` — 属实。`ls docs/edge-architecture.md` 无此文件；同一缺失路径共 5 处引用：`docs/core-node-space-binding-architecture.md:79`、`docs/README.md:12`、`docs/cli-network-control.md:108`、`docs/link-access-architecture.md:47`、`docs/sync-architecture.md:3`。正文本身未引用该文件，页面文字不受影响。
- 附带核实（不在本页 quality.json 内，供参考）：`arch-corenode.quality.json` 第二条称 `docs/edge-core-entry-protocol.md` 不存在——同样属实，`ls` 无此文件，实际文件是 `edge/docs/core-entry-protocol.md`。

## 总结论：需修改

需修改的条目（共 4 项，均为引用行号修正，不涉及事实改写，无需重读代码）：

1. [M1] 正文概述第二段引用 `README.md:12` 改为 `README.md:10`；建议 facts.json 补一条 ref 为 README.md:10 的 fact。
2. [M2] 正文 AI 速览 `Space` 条引用 `:64` 改为 `:28`（或改写 gloss 为组合定义）。
3. [M3] 正文 AI 速览 `Binding` 条引用 `:134` 改为 `:141`。
4. [57] facts.json ref `docs/core-node-space-binding-architecture.md:460` 改为 `:463`，以覆盖完整四项校验清单（462-466 行）。

其余 98 条 facts 全部支撑；§8 对照表改写全部正确；quality.json 断链主张属实；无禁用词，无单平台泛化。正文事实质量过关，改完上述 4 处行号即可通过。
