# intro-overview 评审（critic）

- 核查对象：`review/batch-01/intro-overview.md` + `intro-overview.facts.json`（65 条）
- 真理源：`~/workspace/Operit2` @ 364d1d594，只读；README.md（262 行）与 README-zh.md（262 行）均已全文读过核对
- 判定口径：ref 行 ±5 行内的原文是否真实支撑断言；行号在范围内；正文引用与 facts 是否一致；禁用词（可能/大概/似乎/应该/也许）；单平台结论是否被写成全平台

## 逐条结论

- #1 一句话定位 "An Agent core that connects your device space" | README.md:3 | 支撑
- #2 面向个人用户的开源跨设备 Agent 项目，设备各展所长、对话任务上下文延续 | README.md:10 | 支撑
- #3 处于 Preview Release 阶段 | README.md:4 | 支撑
- #4 预览期底层结构/数据格式/插件契约/跨设备流程未冻结，破坏性更新在明确声明的预期内 | README.md:14 | 支撑
- #5 源于 Operit 的 Android Agent 实践，当前打磨多端同步/跨设备执行/恢复体验 | README.md:12 | 支撑
- #6 每个运行 Core 的实例称 CoreNode，经本机 Host 用文件/终端/浏览器等能力 | README.md:18 | 支撑
- #7 Space 组织节点间协作与持久化同步 | README.md:18 | 支撑
- #8 Binding 记录任务下一步由哪个节点继续 | README.md:18 | 支撑
- #9 Space 节点地位对等；Linux 云端设备可因长期在线/合适能力承担更多任务，但不成固定主节点 | README.md:20 | 支撑
- #10 加入 Space 不自动授予其他设备的系统权限 | README.md:20 | 支撑
- #11 任务交接以工具结果已持久化、下一轮模型请求尚未开始为边界；目标节点取得同步记录后再继续 | README.md:22 | 支撑
- #12 接续依赖保存的上下文和任务事实，不搬迁在运行的模型请求/终端进程/浏览器会话 | README.md:22 | 支撑
- #13 每个 CoreNode 可独立运行自己的 Agent 工作流，能力取决于平台 Host/模型 Provider/本地配置 | README.md:30 | 支撑
- #14 已含对话/会话分支/消息管理/附件/角色卡/角色群组/提示词配置 | README.md:32 | 支撑
- #15 已含 Provider 配置/模型参数/工具调用/请求队列/可下载本地聊天模型（嵌入 llama.cpp 与 MNN CPU 推理） | README.md:33 | 支撑
- #16 已含工作区/文件操作/项目模板/命令/备份/导入导出 | README.md:34 | 支撑
- #17 已含终端会话、PTY 输入和输出流 | README.md:35 | 支撑
- #18 已含网页访问/浏览器自动化/工作区浏览器/运行时 WebView 会话投影 | README.md:36 | 支撑
- #19 已含记忆/摘要/语音识别/语音合成及其他内置工具 | README.md:37 | 支撑
- #20 能力并非所有平台相同；能否执行取决于目标节点 Host 描述/系统权限/已安装服务/当前用户批准 | README.md:39 | 支撑
- #21 CLI 已提供配对/发现/连接/session/传输方式/Space 成员管理入口；Link Access 建认证连接，PeerLink 承载请求与同步流量，适合本地或受控局域网试验 | README.md:43 | 支撑
- #22 Link 入口命令 serve/discover/connect/space join/space show 五条 | README.md:46 | 支撑（建议：五条命令分占 46–50 行，ref 改为 :46-50 更精确；按 ±5 行规则现 ref 仍算支撑）
- #23 参数以 operit2 --help 与 operit2 cli 实际输出为准；勿用默认开发 token 对公网监听 | README.md:53 | 支撑
- #24 用 JavaScript/TypeScript 写 Package 和 ToolPkg | README.md:59 | 支撑
- #25 用 JS bridge/Wasm runtime/Compose DSL 构建工具与界面 | README.md:60 | 支撑
- #26 Skill 提供可导入、可见性可控的工作流和知识资源 | README.md:61 | 支撑
- #27 连接 MCP server，管理 MCP 配置/工具/本地 MCP 进程 | README.md:62 | 支撑
- #28 插件市场与包管理命令用于安装/启用/停用/查看/执行扩展 | README.md:63 | 支撑
- #29 Rust SDK/TS 声明/codegen 是插件开发入口，接口仍在演进 | README.md:64 | 支撑
- #30 插件及依赖须按目标平台验证，跨设备可移植性仍是重点建设方向 | README.md:66 | 支撑
- #31 Web Access 让浏览器访问已运行的 CoreNode；打开页面不自动使浏览器成为 Space 独立节点 | README.md:72 | 支撑
- #32 浏览器 Host 与 WebAssembly 运行时是另一条工程路径，能力与部署方式分别看待 | README.md:72 | 支撑
- #33 CLI 已提供身份/存储路径/快照导出恢复/备份检查/Operit 一代快照检查入口 | README.md:80 | 支撑
- #34 备份命令 identity list/storage paths/export snapshot/backup inspect/backup restore 五条 | README.md:83 | 支撑（建议：五条命令分占 83–87 行，ref 改为 :83-87 更精确；按 ±5 行规则现 ref 仍算支撑）
- #35 活动中进程与实时会话仍属原节点；有备份不等于已完成所有运行时无缝迁移 | README.md:90 | 支撑
- #36 Flutter App 是移动端与桌面端主要图形访问面，也可承载 CoreNode；各平台 Host/构建条件不同 | README.md:96 | 支撑
- #37 Rust CLI/TUI 是本地 CoreNode 与运维/开发入口；当前 CLI Host 主要覆盖 Windows/Linux/macOS | README.md:97 | 支撑
- #38 PB_SBC01_H3 是运行完整 Core 的 Linux 硬件主控入口，应用入口在 edge/boards/pb_sbc01_h3 | README.md:98 | 支撑
- #39 Web Access 不是自动加入 Space 的浏览器节点，也不是中心化 Agent Server | README.md:99 | 支撑
- #40 WebAssembly/browser Host 是浏览器运行时本地能力边界，与 Web Access 访问面分开，能力取决于浏览器与当前 Web 构建模式 | README.md:100 | 支撑
- #41 Linux 云端设备是 Space 中的普通 CoreNode，长期在线可承担更多任务，但不因此拥有中心身份 | README.md:101 | 支撑
- #42 ESP32 Edge Node 是设备原生业务与 Edge Service 能力节点，拥有本地配置与有界运行，参与 Space 控制并可消费 Core 服务，无完整业务副本 | README.md:102 | 支撑
- #43 Server 是未来部署形态与 Host 方向；当前仓库还没有可直接发布的完整 Server 产品 | README.md:103 | 支撑
- #44 仓库含多平台 Host 适配路径，但“能够构建”不等于“已经完成跨设备互操作验证” | README.md:105 | 支撑
- #45 能力模型外层两层是 App Runtime Sandbox 与 Host Authorization | README.md:112 | 支撑（建议：两层分占 112 与 115 行，ref 改为 :112-115 或 :109-116 更精确；按 ±5 行规则现 ref 仍算支撑）
- #46 能力模型内层两层是 AI Capability Limit（三档 ReadOnly/WorkspaceWrite/Full）与 User Tool Approval（允许/询问/禁止） | README.md:118 | 支撑（建议：两层分占 118–119 与 121–122 行，ref 改为 :118-122 更精确；按 ±5 行规则现 ref 仍算支撑）
- #47 Space 成员资格不授予其他节点读本机文件/用本机终端/获管理员或 root 能力 | README.md:127 | 支撑
- #48 API key/设备私钥/配对密钥/session/本地平台权限默认属节点本地，不因加入 Space 自动复制 | README.md:128 | 支撑
- #49 Full 只表示 AI 能力限制放宽，不表示 Host 提权，也不能创造操作系统没有的能力 | README.md:129 | 支撑
- #50 应用内部 sandbox 字段与 UI 不能冒充真实操作系统级隔离边界 | README.md:130 | 支撑
- #51 对外监听 Link 或 Web Access 前，应使用强 token/受限监听地址/TLS 与防火墙/脱敏日志 | README.md:131 | 支撑
- #52 用户始终拥有是否同步敏感数据/是否批准具体动作/是否让节点参与协作的决定权 | README.md:132 | 支撑
- #53 当前优先修复问题、打磨稳定性，尤其关注跨设备执行的取消/重连/资源释放/失败恢复 | README.md:138 | 支撑
- #54 仍在设计/完善/验证的方向包括结合 Health/长期执行记录/用户偏好选设备，及备用节点/受控并行/子任务拆分 | README.md:142 | 支撑（fact 用“包括”未穷举原文 142–146 行的五条方向，未失实）
- #55 以个人设备空间为主要场景，未验证数千节点调度，不以企业组织治理为目标；Rust 本身不构成无资源泄漏的保证 | README.md:148 | 支撑
- #56 CLI 入口用 cargo run --manifest-path apps/cli/Cargo.toml --bin operit2 -- --help 查看 | README.md:170 | 支撑
- #57 无参数时 operit2 默认进入 TUI | README.md:175 | 支撑
- #58 Flutter App 从 apps/flutter/app 目录运行，fvm flutter run -d windows 中的 windows 只是示例设备名，各平台模式需各自平台工具链，且 Host 能力并不相同 | README.md:191 | 支撑
- #59 Web Access 本地开发用两个终端：Flutter Web 在 4835 端口，代理监听 4836 端口 | README.md:202 | 支撑
- #60 打开 http://127.0.0.1:4836；端口被占用时可同时改 Flutter 上游端口与代理 --upstream-port，但须保持两者一致 | README.md:208 | 支撑
- #61 仓库结构 apps/ 下有 cli、pb_sbc01_h3、flutter/app、flutter/app/web，server/ 是 Server 形态预留目录 | README.md:213 | 支撑（建议：apps 树分占 213–218 行，ref 改为 :213-218 更精确；按 ±5 行规则现 ref 仍算支撑）
- #62 仓库结构 core/ 下有 crates、CRATE_BOUNDARIES.md、examples；hosts/ 是各平台 Host 实现；plugins/ 是 ToolPkg、Skill、SDK 类型与插件开发工具；tools/ 是构建/发布/Web/开发辅助脚本；docs/ 是架构/权限/Link/迁移/版本文档 | README.md:225 | 支撑（建议：该段分占 220–228 行，ref 改为 :220-228 更精确；按 ±5 行规则现 ref 仍算支撑）
- #63 架构文档中标注为“目标”“计划”或“演进方向”的内容不代表所有平台已实现；判断当前实际行为以源码/命令帮助输出/构建结果/目标平台运行结果为准 | README.md:246 | 支撑
- #64 修改跨设备能力时须守住三条边界：本地 Host 权限不因 Space 成员关系自动继承；同步范围与数据归属必须能被用户理解；功能可演进，但不能静默丢失任务连续性与可恢复记录 | README.md:254 | 支撑
- #65 仓库根 LICENSE 当前为 GNU Affero General Public License v3.0（AGPL-3.0）；具体组件可能附带自己的许可证或元数据 | README.md:262 | 支撑

## 正文核查（.md 与 facts 的一致性）

- 正文全部断言均能在 facts 中找到对应支撑，未发现超出 facts 支撑范围的发挥。
- 禁用词：正文全文 grep 可能/大概/似乎/应该/也许，零命中。
- 单平台问题：正文明确写了“这些能力并不在所有平台完全相同”及“能否执行……要看目标节点的 Host 描述、系统权限、已安装服务和当前用户批准”，并以表格分平台写边界；未发现把单平台实现写成全平台结论之处。frontmatter `platforms: [all]` 与正文的分平台表述一致（本页是通用定位页，平台差异已在页内注明）。
- 来源声称：README.md（262 行，全文已读）与 README-zh.md（262 行，全文已读）——实测两文件确为 262 行；白皮书 PDF 未被引用，与声称一致。注意：正文全部引用均指向 README.md，README-zh.md 仅列在 frontmatter sources 中，未在正文引用；不构成错误，但若中文版与英文版有出入，正文无法从引用上体现核对过哪一版。
- 沙盒能力模型代码块与 README.md:111-123 原文逐字一致；平台表格 8 行与 README.md:96-103 逐行一致；两组 CLI 命令块与 README.md:46-50、83-87 逐行一致。

## 发现的唯一问题（正文引用不精确，需修改）

- 位置：正文“AI 速览”节，`主入口：operit2（无参数默认进入 TUI），命令参数以 operit2 --help 的实际输出为准（README.md:170）`。
- 问题：该句把两个断言压在同一个 ref :170 下，但 :170 只是 `cargo run ... -- --help` 这一行命令。
  - “无参数默认进入 TUI”的准确出处是 README.md:175（:170 距其 5 行，勉强落在 ±5 行窗口内，但 ref 应直接指向 175）。
  - “命令参数以 operit2 --help 的实际输出为准”的准确出处是 README.md:53，距 :170 有 117 行，完全不在 ±5 行窗口内——该半句的引用不成立。
- 修正建议：拆成两处引用——`operit2（无参数默认进入 TUI，README.md:175），命令参数以 operit2 --help 的实际输出为准（README.md:53）`。facts.json 本身无需改动（#23 与 #57 的 ref 各自正确）。

## 总结论：需修改

- 65 条 facts：支撑 65，不支撑 0，存疑 0。
- 需修改项（1 项，均在正文，不在 facts.json）：AI 速览“主入口”句的引用拆分（见上节）。
- 可选优化（不影响通过与否）：#22、#34、#45、#46、#61、#62 六条的 ref 建议改为范围引用（:46-50、:83-87、:112-115、:118-122、:213-218、:220-228），使单行 ref 与多行原文的对应更精确；按 ±5 行规则现 ref 已算支撑，改不改由 writer 定。
