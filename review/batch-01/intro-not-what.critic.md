# Critic：intro-not-what（独立核查）

- 核查对象：`review/batch-01/intro-not-what.md` 与 `intro-not-what.facts.json`（53 条）
- 真理源：`~/workspace/Operit2`，基线 364d1d594，只读；未做 git 操作、未联网
- 方法：每条 fact 的 ref 文件存在性 + 行号范围 + ref 行 ±5 行语义对照；正文引用逐一核对；禁用词与平台泛化扫描
- 结论口径：支撑 / 不支撑 / 存疑

## 逐条结论（53 条）

1. Operit2 定位是连接用户设备空间的 Agent 核心 | README.md:3 | 支撑（原文 "An Agent core that connects your device space"）
2. 预览阶段底层结构、数据格式、插件契约和跨设备流程仍可能发生破坏性变更 | README.md:14 | 支撑（原文 "may still undergo breaking changes"；"可能"二字是原文 may 的直译，非推测性措辞）
3. 每个运行 Core 的实例称为 CoreNode | README.md:18 | 支撑
4. Space 组织节点协作与持久化同步，Binding 记录任务下一步由哪个节点继续 | README.md:18 | 支撑
5. Space 中的节点地位对等 | README.md:20 | 支撑（原文 "equal standing"）
6. Linux 云端设备承担更多任务也不会因此成为固定主节点 | README.md:20 | 支撑
7. 加入 Space 不会自动授予节点其他设备的系统权限 | README.md:20 | 支撑
8. 任务交接以工具结果已持久化、下一轮模型请求尚未开始为边界 | README.md:22 | 支撑
9. 任务接续依赖保存的上下文和任务事实，不搬迁运行中的模型请求、终端进程或浏览器会话 | README.md:22 | 支撑
10. 主对话保留发起设备的交互归属，子任务在执行节点推进，其他设备通过异步同步了解进展 | README.md:24 | 支撑
11. 手机发起、合适设备执行、桌面查看或批准、回手机接收结果的完整体验仍在完善中 | README.md:24 | 支撑（"The complete experience is still being developed"）
12. 单节点 Agent 的能力取决于平台 Host、模型 Provider 和本地配置 | README.md:30 | 支撑
13. 单节点 Agent 的能力并不在所有平台完全相同 | README.md:39 | 支撑
14. 打开 Web Access 页面不会自动让浏览器成为 Space 中的独立节点 | README.md:72 | 支撑
15. 活动中的进程和实时会话仍然属于原节点，备份不等于所有运行时状态已经能够无缝迁移 | README.md:90 | 支撑
16. Web Access 不是自动加入 Space 的浏览器节点，也不是中心化 Agent Server | README.md:99 | 支撑（平台表行原文）
17. Linux 云端设备是 Space 中的普通 CoreNode，不因此拥有中心身份 | README.md:101 | 支撑（平台表行原文）
18. ESP32 Edge Node 不保存完整业务副本 | README.md:102 | 支撑（原文 "no full business replica"）
19. 当前仓库还没有可以直接发布的完整 Server 产品 | README.md:103 | 支撑
20. Space 成员资格不会授予其他节点读取本机文件、使用本机终端或获得管理员/root 能力 | README.md:127 | 支撑
21. API key、设备私钥、配对密钥、session 和本地平台权限默认属于节点本地，不会因为加入 Space 自动复制 | README.md:128 | 支撑
22. Full 只表示 AI 能力限制放宽，不表示 Host 提权，也不能创造操作系统没有的能力 | README.md:129 | 支撑
23. 当前以个人设备空间为主要场景，尚未验证数千节点调度，也不以企业组织治理为产品目标 | README.md:148 | 支撑
24. Rust 本身不构成无资源泄漏的保证 | README.md:148 | 支撑（原文 "Rust itself does not guarantee the absence of resource leaks"；注：与本页主题关联弱，但引用准确，不扣分）
25. 架构文档中标注为目标、计划或演进方向的内容不代表所有平台已经实现，判断当前实际行为以源码、命令帮助输出、构建结果和目标平台运行结果为准 | README.md:246 | 支撑
26. 用户身份不进入设备空间同步，也不通过 Link 传播 | docs/core-node-space-binding-architecture.md:17 | 存疑——ref 行原文主语是"身份"（L16"每个身份独立拥有……"，L17"身份不进入设备空间同步"），fact 加了"用户"二字；"用户身份"与文档"身份"是否为同一术语未在文中定名。建议：fact 改为"身份不进入设备空间同步，也不通过 Link 传播"，或在术语表中确认"用户身份"即文档"身份"。核心断言本身有原文支撑。
27. 执行模型只包含 CoreNode 和 Binding 两个概念 | docs/core-node-space-binding-architecture.md:24 | 支撑（L21"执行模型只包含两个概念" + L24-25 代码块）
28. Space 是节点成员、路由和持久化同步的范围，不是执行容器，不拥有 Agent、聊天或运行时 | docs/core-node-space-binding-architecture.md:28 | 支撑（L28-29 原文）
29. 架构中不引入 Chat Core、Agent Core、Env、Placement、Lease、Circuit、Capability 或远程数据放置 Ownership 模型 | docs/core-node-space-binding-architecture.md:34 | 支撑（L34-35 原文）
30. 每个 CoreNode 只有一套 OperitApplication + LocalCoreProxy + HostManager | docs/core-node-space-binding-architecture.md:51 | 支撑
31. CoreNode 不持有环境注册表，需要另一台设备或另一套 Host 能力时 Agent 切换到另一个 CoreNode | docs/core-node-space-binding-architecture.md:54 | 支撑（L54-55 原文）
32. 服务监听方、连接发起方和请求执行方只是一次连接或调用中的角色，不形成主节点和从节点 | docs/core-node-space-binding-architecture.md:58 | 支撑（L57-58 原文）
33. Space 只负责三件事：确定协作范围、确定可承载 Space 流量的已配对连接、确定持久化数据同步范围 | docs/core-node-space-binding-architecture.md:69 | 支撑（L69-74 原文）
34. Space 不表达执行位置，也不表达数据归属 | docs/core-node-space-binding-architecture.md:77 | 支撑
35. 配对完成后不会自动加入设备空间 | docs/core-node-space-binding-architecture.md:93 | 支撑
36. 退出设备空间只重写本机成员记录，保留完整业务数据和直接配对记录，并创建新的单设备空间 | docs/core-node-space-binding-architecture.md:111 | 支撑（L111-112 原文）
37. Binding 只表达一句话：这个 key 对应的下一次路由执行由哪个 CoreNode 完成 | docs/core-node-space-binding-architecture.md:141 | 支撑（L141-143 原文）
38. Binding 不表示业务数据位于目标节点 | docs/core-node-space-binding-architecture.md:146 | 支撑（L146-147 原文）
39. 同一个 Agent 的不同聊天可以绑定不同 CoreNode，切换 Binding 不会移动 Agent，也不会移动其对话 | docs/core-node-space-binding-architecture.md:150 | 支撑（L150-151 原文）
40. 业务副本同步只在双方都具备 storage.provide 且实际提供 Core 存储服务时运行 | docs/core-node-space-binding-architecture.md:187 | 支撑
41. CoreNode 身份私钥、两两配对密钥和 session、HostManager 平台状态、本机监听地址、应用界面缩放、本机平台能力和临时交互句柄保持节点本地，不进入 Space 持久化同步 | docs/core-node-space-binding-architecture.md:258 | 支撑（L255-263 列表逐项对应）
42. 实时传输不负责复制持久化业务数据 | docs/core-node-space-binding-architecture.md:280 | 支撑
43. 实时 continuation 的同步时钟只是交接屏障，不表示数据迁移 | docs/core-node-space-binding-architecture.md:281 | 支撑（L280-281 原文）
44. RoutedLink 外层不携带 chatId、Binding、envId、文件路径或 Host 配置 | docs/core-node-space-binding-architecture.md:297 | 支撑（L297-298 原文）
45. 聊天历史读取、配置编辑和其他持久化数据操作在本地 Core 执行，由持续同步传播，只有模型执行、工具循环、取消当前执行和实时执行状态进入 Binding 路由 | docs/core-node-space-binding-architecture.md:363 | 支撑（L362-363 原文）
46. 整段会话删除属于本地持久化操作，不要求存在 Binding，也不要求执行节点在线 | docs/core-node-space-binding-architecture.md:365 | 支撑
47. 切换 CoreNode 不触发会话总结或上下文压缩，上下文压缩仍由独立的自动阈值或用户手动操作触发 | docs/core-node-space-binding-architecture.md:379 | 支撑（L379 原文逐字对应；注：该句引的是架构文档原文。"自动阈值"在代码中是否真实存在属文档与代码一致性问题，超出本页 fact 核查范围——若后续代码核实推翻文档，应同步修正本条）
48. 设备身份、配对 secret 和 Host 授权保持节点本地，Space 成员资格不授予其他节点直接读取本机文件或终端的能力 | docs/core-node-space-binding-architecture.md:472 | 支撑（L472-474 原文）
49. Binding 只决定 chat 的下一步执行节点 | docs/core-node-space-binding-architecture.md:481 | 支撑
50. Binding 改变不移动数据 | docs/core-node-space-binding-architecture.md:482 | 支撑
51. 一个 chat 的同一执行轮次只有一个 CoreNode 可以推进 | docs/core-node-space-binding-architecture.md:484 | 支撑
52. 两两配对仍是所有直接网络信任的基础 | docs/core-node-space-binding-architecture.md:486 | 支撑
53. Binding 目标不可达时由发起设备原子接管，显式设备调用仍返回明确错误 | docs/core-node-space-binding-architecture.md:488 | 支撑

统计：支撑 52 条，不支撑 0 条，存疑 1 条（第 26 条）。

## 正文核查（.md 引用与断言）

- 正文 53 条 facts 的引用与 facts.json 一致，未发现正文断言超出 facts 支撑范围的发挥；概述句"仍未冻结"是对 README.md:14 "may still undergo breaking changes" 的合理转述。
- 正文引用了 facts.json 之外的行号，均已逐一核对原文，全部支撑：README.md:49（`operit2 cli link space join <session-name>` 命令原文）、arch:146（chatId 作 key）、arch:159（list_core_nodes）、arch:164（switch_core）、arch:171（generation 单调递增）、arch:289（RoutedLink 结构）、arch:386（切换边界代码块，±5 行内含完整三行边界）、arch:395–404（调用链 10 步与文档编号逐行对应）、arch:407（requiredClock）。
- 存疑 1 处（正文）：AI 速览"主入口：`operit2 cli link space join <session-name>`，加入 Space 前先完成配对与连接，见 `README.md:49`"——README.md:49 只有命令本身，±5 行（L43-51）只列出入口命令，未明说"先完成配对与连接"这一前置关系；该前置关系实际由架构文档 L86-89 的流程（发现 → 配对握手 → 用户明确选择加入）支撑。建议：该句 ref 改为 `docs/core-node-space-binding-architecture.md:88`，或在 facts.json 中补一条以 arch:88 为 ref 的 fact。
- 禁用词扫描：正文 .md 无"可能/大概/似乎/应该/也许"；facts.json 仅第 2 条含"可能"，系 README.md:14 原文 "may" 的直译，非推测性措辞，不违规。
- 平台泛化扫描：未发现把单平台实现写成全平台结论。frontmatter `platforms: [all]` 与内容相符——各断言均为 README 与架构文档的通用边界陈述；唯一单平台断言（ESP32 Edge Node）已明确限定平台；"单节点 Agent 的能力并不在所有平台完全相同"一节本身就是反泛化声明。
- frontmatter `sources` 列出 README-zh.md，但正文未引用其中文行——仅为来源清单，不构成错误。

## 总结论：需修改

需改 2 处（均为轻微措辞/引用问题，无事实性错误，不必打回重写）：

1. 第 26 条 fact：把"用户身份"改为"身份"，与架构文档 L16-17 原文主语一致；或在术语表中定名"用户身份"即文档"身份"。修正后即为支撑。
2. 正文 AI 速览"主入口"句：ref 由 `README.md:49` 改为 `docs/core-node-space-binding-architecture.md:88`（配对握手 → 用户选择加入的流程原文），或在 facts.json 补一条 arch:88 的 fact 再引用。

其余 52 条 fact 与正文其余引用全部支撑通过；无禁用词违规，无平台泛化问题。
