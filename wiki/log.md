# Operit2-wiki 合并日志

> 追加记录，不删改。每次合并一批条目记一条。

## 2026-11-11 · batch-01（P0 首批 10 页，第 1、2 章）

- 来源：AAswordman/Operit2 @ 364d1d594；大纲 v1（outline-v1.yaml，11 章 115 页）已于 2026-11-11 获用户批准。
- 页：intro-overview、intro-not-what、intro-preview、intro-quickstart、arch-overview、arch-corenode、arch-space、arch-binding、arch-sync、arch-routing。
- 事实：761 条原子事实（facts.json），引用全部落在源文件行号范围内，坏引用 0。
- Lint：`lint.py --dir review/batch-01` 硬失败 0、警告 0。
- Critic：首批 5 页全审（intro-overview、intro-not-what、intro-preview、intro-quickstart、arch-overview），结论均为「需修改」小修，已按 critic.md 逐项修正并复验 lint 0/0；其余 5 页 facts 引用机械核验 0 坏引用。
- 质量走查（.quality.json）：4 页有记录——intro-quickstart（README 旧命令与代码不符、代理脚本缺失）、arch-overview（edge-architecture.md 断链、§8 旧名）、arch-corenode（两处断链）、arch-sync（edge-architecture.md 断链）。
- 阅读登记：16 个源文件 complete，见 tracking/read-status.json。
- 评审 Issue：#2–#11，状态均为 review-pending。

## 2026-11-11 · batch-01 修订版（用户首轮评审后打回重写）

- 用户于 2026-11-11 在 Issue #2–#11 各留一条审查意见，结论均为需修改（静态源码核对，基线 364d1d594 未变）；修订意见原文已拉取存档于 tracking/reviews-batch-01/issue-2.md～issue-11.md。
- 三个跨页问题：Provider 凭证同步与 README:128 原则冲突（4 页）、“目标不可达时原子接管”不符合实现（3 页）、交接的屏障/代际去重是设计约束而非已实现调用链（2 页）；另有各页 P2 项（Web 开发脚本缺失、list_core_nodes 返回字段、update check 参数、配对三种操作、syncClockDigest 探针条件、快照校正条件、诊断日志字段、RoutedLink 字段、速览引用补齐等）。
- 修订：10 页并行修订，facts 761 → 876 条（+115），引用机械核验 0 坏引用；Lint 硬失败 0、警告 0；各页 .status.json 保持 review-pending，watcher 水位线已前移到各条审查留言的 comment id。
- 本版重新部署后请用户复审，Issue #2–#11 不变。

## 2026-11-11 · batch-01 复审修订 + 全部上线（已批准）

- 用户复审修订版 a851929（2026-11-11 15:39–15:40）：8 页“本轮未发现阻断问题”（#3–#10），2 页“仍需修改”（#2 intro-overview、#11 arch-routing），另 #9 arch-binding 有一处非阻断措辞建议。复审意见原文存 tracking/reviews-batch-01/r2-issue-2.md～r2-issue-11.md。
- 本轮 3 处修订：#2 旧正文 150 行与 facts 第 48 条的无条件“不复制”保证改成“README 声明的原则”（与 intro-not-what 同口径）；#11 配置身份校验补上适用条件（只在 extensionOwner 不是 MODEL_CONFIGURATION_OWNER 即 host.chat.model 时执行）并补常量事实 1 条；#9 删去第 70 行与第 64 行重复的 generation 递增句。
- 修订后 facts 876 → 877 条，lint 硬失败 0、警告 0。用户主聊 2026-11-11 15:50 指示“评审完了这一轮改完直接上线”，10 页状态同日翻为 approved（approved_at 2026-11-11 07:52 UTC），不再走下一轮评审。
- 首页统计随部署更新为 11 页已发布、877 条原子事实。

## 2026-11-11 · batch-02（第 3 章 Core 前 10 页，待评审）

- 来源：AAswordman/Operit2 @ 364d1d594；大纲 v1（11 章 115 页）第 3 章前 10 页。
- 页：core-overview、core-foundation、core-foundation-util、core-persistence-store、core-persistence-sync、core-persistence-rescue、core-provider-services、core-provider-local-model、core-tool-execution、core-tool-packages-mcp。
- 事实：1489 条原子事实（facts.json），引用全部落在源文件行号范围内，坏引用 0；critic 修正后 1482 → 1489 条（+7：core-overview +1、core-foundation +2、core-foundation-util +2、core-persistence-store +1、core-persistence-sync +1）。
- Lint：`lint.py --dir review/batch-02` 硬失败 0、警告 0。
- Critic：首 5 页全审（core-overview、core-foundation、core-foundation-util、core-persistence-store、core-persistence-sync），结论均为「需修改」小修，已按 critic.md 逐项修正并复验 lint 0/0；其余 5 页 facts 引用机械核验 0 坏引用。
- 质量走查（.quality.json）：8 页有记录——core-overview（CRATE_BOUNDARIES.md 文档声称与 Cargo.toml 实现 6 处不一致）、core-foundation（HostManager 默认宿主取回不一致、hostCapabilities 未定义 id 直接 panic、setDefault* 丢弃 OnceLock 结果）、core-foundation-util（ArchiveUtil 空 struct 零功能）、core-persistence-store（mergedProjection 合并成员未去重）、core-provider-services（EnhancedAIService 运行时配置失败直接 panic，5 处）、core-provider-local-model（STT segments 恒为空、verifiedAtMs 无人写入真实值）、core-tool-execution（refreshPermissionRequestState 只有 false 一行零调用）、core-tool-packages-mcp（包工具声明 READ、MCP 调用声明 WRITE 的权限不对称）。
- 阅读登记：60 个源文件 complete（本批），见 tracking/read-status.json。
- 评审 Issue：#12–#21，状态均为 review-pending。首页统计随部署更新为 21 页知识页面、11 页已发布、2366 条原子事实、3 个编译批次。

## 2026-11-11 · batch-02 修订版（用户首轮评审后）

- 用户于 2026-11-11 在 Issue #12–#21 各留一条审查意见：5 页需修改（#12、#14、#16、#17、#21），5 页本轮未发现阻断问题（#13、#15、#18、#19、#20）；审查意见原文存 tracking/reviews-batch-02/issue-12.md～issue-21.md。
- 5 页并行修订：#12 删 runtime 依赖“冲突”判断（方向链读反了）并改标题六处→五处；#14 日志返回值区分立即写入与批处理排队；#16 操作日志位置由已退休 JSONL 改为当前 SQLite Journal（transactions.sqlite），扫描/隔离 API 明确为遗留 JSONL；#17 validate_source_files 补全四类检查（数量上限、合法、重复、祖先重叠）；#21 依赖调用 main 限制角色纠正 + 技能激活不走冒号命名。facts 1489 → 1498 条（+9），引用机械核验 0 坏引用；Lint 硬失败 0、警告 0；各页 .status.json 保持 review-pending，watcher 水位线已前移到各条审查留言的 comment id。
- 本版重新部署后请用户复审，Issue #12–#21 不变。
- 首页统计随部署更新为 21 页知识页面、11 页已发布、2375 条原子事实。

## 2026-11-11 · batch-02 复审修订 + 全部上线（已批准）

- 用户复审修订版 0d80949（2026-11-11 17:18–17:19）：5 个修订页“本轮已列问题均已修复，未发现新的阻断问题”（#12、#14、#16、#17、#21），另 #16 有一处非阻断措辞建议；其余 5 页首轮即无阻断问题，无新意见。复审意见原文存 tracking/reviews-batch-02/r2-issue-12.md、r2-issue-14.md、r2-issue-16.md、r2-issue-17.md、r2-issue-21.md。
- 本轮 1 处小修：#16 第 39 行及 facts 第 165 条“唯一读取已退休文件式 ledger 的入口”收窄为“当前 Journal 的一次性迁移入口”（scanOperationLog 仍可读取遗留 JSONL 做诊断）。facts 总数不变，仍为 1498 条，lint 硬失败 0、警告 0。
- 用户主聊 2026-11-11 17:20 指示“复审意见已经发布。改完这轮直接发布”，10 页状态同日翻为 approved（approved_by=luojiaping，approved_at 2026-11-11 09:21 UTC，水位线保留），不再走下一轮评审。
- 首页统计随部署更新为 21 页知识页面、21 页已发布、2375 条原子事实。

## 2026-11-11 · batch-03（第 3 章 Core 后 13 页，待评审）

- 来源：AAswordman/Operit2 @ 364d1d594；大纲 v1（11 章 115 页）第 3 章后 13 页。
- 页：core-plugin-sdk、core-plugin-js-bridge、core-plugin-theme、core-plugin-codegen、core-runtime、core-runtime-services、core-runtime-data、core-node-runtime、core-node-peer-link、core-proxy、core-rslink、core-application、core-command。
- 事实：1979 条原子事实（facts.json），引用全部落在源文件行号范围内，坏引用 0；初版 1964 条，critic 修订 +15（core-runtime +2、core-plugin-codegen +1、core-node-runtime +12）；机械核验抓出 50 条符号越窗（core-command 19、core-node-peer-link 11、core-plugin-js-bridge 20）已全部修完。
- Lint：`lint.py --dir review/batch-03` 硬失败 0、警告 0。
- Critic：抽查 5 页（core-plugin-codegen、core-runtime-services、core-node-runtime、core-runtime、core-plugin-sdk），结论均为「需修改」小修，已按 critic 意见逐项修正并复验 lint 0/0；其中 core-node-runtime 抓出 1 条凭空捏造的字段名（changeGate/pendingStage）与 1 处函数归属错误，core-runtime-services 抓出 4 处事实错误，均已修正；其余 8 页 facts 引用机械核验 0 坏引用。
- 质量走查（.quality.json）：9 页有记录，共 18 条——core-plugin-sdk（validateProtectedEntryPolicy 空壳、README Target Split 称新增 runtime crate 但磁盘无此目录）、core-plugin-js-bridge（文本回调非文本值 panic、AES 走 ECB 无 IV、Java 桥桩与三处未实现静态操作）、core-plugin-theme（两个校验器常量定义后全 crate 未使用）、core-runtime（newWithContext 多处 expect panic、onCreate 静默回退默认 Host）、core-runtime-data（暂存删除失败掩盖原始错误、互斥锁中毒三处 expect panic）、core-node-runtime（README 的 runtime/src/remote 目录不存在，文档滞后）、core-node-peer-link（订阅失败与解码失败 panic）、core-application（Drop 不调 clearCoreRouteRuntime 而 shutdownNow 会调）、core-command（用法文本承诺不存在的 codex-login 子命令、--runtime 被静默忽略、chat new 用法漏列 --workspace）。
- 阅读登记：76 个源文件 complete（本批，66 个 seed + 补充阅读），见 tracking/read-status.json。
- 评审 Issue：#22–#34，状态均为 review-pending。首页统计随部署更新为 34 页知识页面、21 页已发布、4354 条原子事实、4 个编译批次。

## 2026-11-11 · batch-04（第 4 章 Agent 回路 8 页，待评审）

- 来源：AAswordman/Operit2 @ 364d1d594；大纲 v1（11 章 115 页）第 4 章 8 页。35 个 seed 开工时逐个核实全部存在。
- 页：agent-loop-overview、agent-chat-branch、agent-compaction、agent-subagents、agent-memory、agent-character-cards、agent-hooks、agent-slash。
- 事实：850 条原子事实（facts.json），引用全部落在源文件行号范围内，坏引用 0；初版 849 条，critic 修订 +1（agent-memory fact [103] 拆成两条）；机械核验抓出 23 条符号越窗（全在 agent-compaction，`Type::method` 全限定名形式问题）已全部修完，0 删事实；正文引用同口径复核另修 79 处越窗（agent-compaction）+ 20 处（agent-loop-overview）+ 16 处（agent-slash），均已清零。
- Lint：`lint.py --dir review/batch-04` 硬失败 0、警告 0（注：lint 的引用正则不含 `.rs` 后缀，正文 Rust 引用的 ±5 检查由父级自写脚本另行复核）。
- Critic：抽查 5 页（agent-loop-overview、agent-chat-branch、agent-compaction、agent-subagents、agent-memory），结论均为「需修改」小修，已按 critic 意见逐项修正并复验 lint 0/0；其中 agent-compaction 抓出 1 处锚点不能支撑断言（:786 只是日志行，重锚 :521）与 1 处丢 gating 条件，agent-memory 抓出 1 处事实错误（authorMissing 标记条件写错），agent-loop-overview 抓出 1 处事实错误（对话回顾超限保留前 30 + 后 70 条）与 4 处丢条件，agent-chat-branch 抓出 displayOrder 取值与透传变体分类两处错误，agent-subagents 抓出 1 处丢条件（spawn 拒绝只在父会话本身是子代理时触发）；其余 3 页 facts 引用机械核验 0 坏引用。
- 重核结论：自动压缩存在且默认启用（阈值 0.85），推翻 2026-10-13 差距调查的 P0「自动 compaction 缺失」结论；上下文用量显示同样存在；subagents 旧结论（并发上限 8、无唤醒、重启标 interrupted）逐项复核全部成立；slash 命令实测 81 条、用户自定义 slash 加载机制不存在。
- 质量走查（.quality.json）：7 页有记录，共 15 条——agent-loop-overview（runtimeToolHandler 与 createAndGetDefaultWorkspace 未初始化 expect panic、switch_core 成功结果先于实际移动、translate_text 空壳）、agent-chat-branch（导入 skipped 计数恒为 0、缺基础 parts 时整批加载失败）、agent-hooks（两座桥取互斥锁用 expect，锁中毒分别导致状态通知 panic、摘要流程中断）、agent-subagents（enabled_by_default 两处声明值相反、spawn 保存失败留无记录子会话、一条坏记录致全部操作永久失败）、agent-memory（待处理候选少于 5 条时自动提取饥饿）、agent-slash（updatedAt 解析 expect panic、print_shell_usage 漏列 /current）、agent-compaction（检查点提示词取用函数全仓无调用方）。agent-character-cards 无 quality 记录（读到的严格行为均为有意设计约束）。
- 阅读登记：56 个源文件 complete（本批，35 个 seed + 补充阅读），见 tracking/read-status.json。
- 评审 Issue：#35–#42，状态均为 review-pending。首页统计随部署更新为 42 页知识页面、21 页已发布、5204 条原子事实、5 个编译批次。

## 2026-11-11 · batch-03/04 首轮评审后部分发布（10 页已批准）

- 用户于 2026-11-11 21:02–21:11（CST）在 Issue #22–#42 各留一条静态审查意见（审查对象 wiki cd042091/66baaf0，对照上游最新 main 053c6686；审查意见原文存 tracking/reviews-batch-03/issue-22.md～issue-34.md、tracking/reviews-batch-04/issue-35.md～issue-42.md），评审把「原有事实偏差」与「上游后续变化」分开说明。
- 结论：batch-03 需修改 8 页（#22、#24、#26、#27、#28、#30、#31、#32），本轮未发现阻断问题 5 页（#23、#25、#29、#33、#34）；batch-04 需修改 3 页（#36、#40、#41），本轮未发现阻断问题 5 页（#35、#37、#38、#39、#42）。
- 用户主聊 2026-11-11 21:21 指示「10 页没阻断问题的先发布，11 页改完再审」，10 页状态同日翻为 approved（approved_by=luojiaping，approved_at 2026-11-11 13:21 UTC，水位线保留）：batch-03 的 core-plugin-js-bridge、core-plugin-codegen、core-node-runtime、core-application、core-command；batch-04 的 agent-loop-overview、agent-compaction、agent-subagents、agent-memory、agent-slash。11 页修订中，基线是否前移至 053c6686 待定。
- 首页统计随部署更新为 42 页知识页面、31 页已发布、5204 条原子事实、5 个编译批次。

## 2026-11-11 · batch-03/04 用户首轮评审修订（11 页，待复审）

- 修订对象：用户 2026-11-11 21:02–21:11 在 Issue #22–#42 留下的静态审查意见（原文存 tracking/reviews-batch-03/issue-22.md～issue-34.md、tracking/reviews-batch-04/issue-35.md～issue-42.md）。协调员逐项核实：评审实质内容全部属实，无一条判错；其中原有事实偏差 8 项、上游后续变化 8 项（VFS 迁移 FileSystemHost → VisualFileSystem 横跨 #22/#26/#27/#31 四页）、非阻断精确化 2 项。
- 修订 11 页：batch-03 的 core-plugin-sdk（#22，3 处加时效标注）、core-plugin-theme（#24，保留名检查改为任意路径组件主干命中即拒，补 con.png/nul.ttf 例子）、core-runtime（#26，6 条 facts + 6 行正文加时效标注）、core-runtime-services（#27，fact #163 dataDir 按评审删除——该事实在基线 364d1d594 下为真，上游 053c6686 已删；另 fact #255 加时效标注）、core-runtime-data（#28，structured_preferences 阶段限定为语音配置迁移，角色/记忆移到 chats 阶段 :717）、core-node-peer-link（#30，512 是常量非硬上限；修订 15→19、schemaRoots 7→8 加时效标注）、core-proxy（#31，执行时才要求调度器；fact #92/#94 合并）、core-rslink（#32，删除正文 :63 执行断言与 fact #46）；batch-04 的 agent-chat-branch（#36，deleteMessage 同一事务删本地数据并记同步操作；「返回条数」→「读取上限」）、agent-character-cards（#40，Core 扩展只存不透明引用；补公开 API 步骤）、agent-hooks（#41，收窄为 14 个 hook 注册结构）。上游变化只加时效标注，不改 .status.json 的 source_commit（仍 364d1d594）；基线是否整体前移至 053c6686 待用户拍板。修订 brief 落 tracking/revision-briefs/。
- 事实数：batch-03 1979 → 1985（评审修订 −3：#27 −1、#31 −1、#32 −1；theme 断言拆分 +11：91 → 102；core-plugin-codegen 删 2 条重复事实：259 → 257）；batch-04 850 不变；全站 5204 → 5210。
- 正文引用同口径复核另清零 392 处：第一轮 176 处（core-plugin-sdk 55、core-runtime-services 78、core-plugin-theme 37、agent-compaction 4、agent-loop-overview 2，含 theme 拆分时纠正一处锚点错误 :1054 → :1018）；第二轮 216 处（core-plugin-codegen 126、core-node-runtime 46、core-runtime-data 23、core-application 8、core-plugin-js-bridge 6、core-command 5、core-node-peer-link 2，均为修订前已存在的残留）。修法：方法名在窗口内的改写为「Type 的 `method`」，其余去反引号改 plain 文本。
- 核验：父级自写脚本（facts 与正文逐处查「反引号符号须在同行任一引用 ±5 行内」）全批 facts 2835 条、bad 0；lint.py 两批各硬失败 0、警告 0。
- 状态：11 页仍为 review-pending，待用户复审；首页统计随部署更新为 42 页知识页面、31 页已发布、5210 条原子事实、5 个编译批次。

## 2026-11-11 · batch-03/04 第 2 轮复核（11 页）

- 另一审核 agent 于 2026-11-11 22:06–22:07（CST）在 11 个 Issue 各留一条第 2 轮复核意见（核对对象 wiki 77e3b7ca，对照上游 main 053c6686；原文存 tracking/reviews-batch-03-round2/issue-22.md～issue-32.md、tracking/reviews-batch-04-round2/issue-36.md～issue-41.md）。
- 结论：9 页「本轮已列问题均已修复，未发现新的阻断问题」（#24、#26、#27、#28、#30、#32、#36、#40、#41）；2 页「仍需修改」，均为 P2 展示问题——正文时效标注里的泛型类型写成普通文本，站点 innerHTML 渲染会把尖括号部分当 HTML 标签丢掉：#22（core-plugin-sdk 正文 :12、:220 的 filesystem: Arc<VisualFileSystem>、Arc<VisualFileSystem>、Arc<dyn FileSystemHost>）、#31（core-proxy 正文 :124 的 Option<T>、:151 的 Arc<VisualFileSystem>）。
- P2 修复：两页 8 处泛型全部恢复内联代码标记；逐项核验——Arc<VisualFileSystem> 在上游 PackageManager.rs:37 逐字存在，proxy 上游 lib.rs:283 返回 Arc<operit_vfs::VisualFileSystem::VisualFileSystem>（简写形式按复核意见原文），Option<T> → T? 映射在基线 dart-codegen lib.rs:1516 核实（single_generic_arg 取 Option 内层、可空加 ?）。事实数不变（全站 5210），lint 0/0；父级脚本余 6 处均为上述已逐项核验的上游符号，不按基线窗口判坏。提交 b3ffe1c＋生成数据同步 e7911ba，部署 gh-pages cf39b39；#22、#31 各留交付留言（comment id 6798144728、6798145257）。
- 注意：复核意见以 luojiaping 账号发出，但正文不含批准词，watcher 不会翻状态；翻 approved 仍须用户主聊明确指示。9 页是否先发布，待用户拍板。

## 2026-11-11 · 第 2 轮复核后发布 9 页（已发布 31 → 40）

- 用户主聊 2026-11-11 22:15 指示「9 页没问题的先发布」。9 页翻为 approved（approved_by=luojiaping，approved_at 2026-11-11 14:16 UTC，水位线保留）：batch-03 的 core-plugin-theme（#24）、core-runtime（#26）、core-runtime-services（#27）、core-runtime-data（#28）、core-node-peer-link（#30）、core-rslink（#32）；batch-04 的 agent-chat-branch（#36）、agent-character-cards（#40）、agent-hooks（#41）。提交 aef98da＋生成数据同步 f6f9cac，部署 gh-pages aca2df2；首页 42/40/5210/5，队列 42 条 40 已批准＋2 待评审（#22、#31 待第 3 轮复核）。
- 覆盖：大纲 115 页，已发布 40 页，待评审 2 页，未写 74 页。
