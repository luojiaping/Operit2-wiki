作者：luojiaping
时间：2026-11-11T08:50:40Z UTC
comment_id：6791450676

审查结论：**需修改**。

审查版本：wiki `f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50`；已核实上游 `AAswordman/Operit2` 最新 `main` 为 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与条目标注一致。

**[P2] “六处不一致”中的 runtime 依赖判断混淆了层级与直接依赖。** [正文第 95 行](https://github.com/luojiaping/Operit2-wiki/blob/f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50/review/batch-02/core-overview.md#L95)及 facts 第 51 条把没有依赖 `operit-proxy-local`、`operit-command-core`、`operit-core-application` 等列为 runtime 与架构文档的冲突。但 [CRATE_BOUNDARIES.md:63–66](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/CRATE_BOUNDARIES.md#L63) 给出的方向是 `runtime -> core-proxy/command-core`，并说明右侧可以依赖左侧；“all child crates”不能解释为 workspace 的全部其他成员。

实际 [proxy/local/Cargo.toml:22](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/proxy/local/Cargo.toml#L22)、[command/core/Cargo.toml:9](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/command/core/Cargo.toml#L9)、[application/core/Cargo.toml:16](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/application/core/Cargo.toml#L16)均依赖 `operit-runtime`。runtime 不反向依赖这些上层消费者符合方向约束，不能作为架构缺口；据此补反向边会形成循环。

建议移除这项“冲突”判断及对应原子事实，按真实分层清点依赖，并调整“六处”标题计数。可以客观记录 manifest 中的依赖，勿把“允许依赖”解释为“必须直接依赖所有成员”。

另已核对 workspace/manifest、父级 trait 实现、HostJsExecutionProvider 实现名，以及协议版本判断与错误码；这些抽查未发现其他阻断问题。

本轮为正文、对应 facts 和所列实现分支的静态核对，未执行编译、构建或测试。结论限于上述核对范围。

