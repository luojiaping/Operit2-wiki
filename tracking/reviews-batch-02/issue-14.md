作者：luojiaping
时间：2026-11-11T08:50:51Z UTC
comment_id：6791454362

审查结论：**需修改**。

审查版本：wiki `f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50`；已核实上游 `AAswordman/Operit2` 最新 `main` 为 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与条目标注一致。

**[P2] 日志返回值需要区分立即写入和批处理排队。** [正文第 118 行](https://github.com/luojiaping/Operit2-wiki/blob/f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50/review/batch-02/core-foundation-util.md#L118)、[第 130 行](https://github.com/luojiaping/Operit2-wiki/blob/f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50/review/batch-02/core-foundation-util.md#L130)及 facts 第 77、93 条将返回值解释为写入成功/失败及任一文件 sink 失败的结果，但批处理会延后实际 I/O。

[AppLogger.rs:571–592](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/util/src/AppLogger.rs#L571) 中，批处理深度大于 0 时 `append_line` 仅加入线程本地队列，立即返回 `Ok(())`；此时 `v_with_level` 可以返回 0，文件尚未实际写入。[LogFileWriteBatch::drop:119–135](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/util/src/AppLogger.rs#L119) 在最外层作用域退出时才刷入，并以 `let _ = append_line_with_rotation_cap(...)` 丢弃结果。刷入失败会报告 I/O 错误，无法回传给此前已结束的日志调用。

触发情形是已启用文件 sink、处于批处理作用域，随后刷入发生 I/O 错误。调用方不能据此前返回 0 判断已落盘，也不能依赖该返回值获知所有后续写入错误。

建议正文和 facts 同步说明：立即写入分支返回本次写入结果；批处理分支只先排队，退出最外层作用域时刷入，刷入错误不回传给先前调用。无需改动代码。

另已核对 sink 配置失败、轮转、内存历史淘汰、文本判定阈值、feature 门控和 Stream/VecStream/FnStream 行为，未发现其他阻断问题。

本轮为正文、对应 facts 和所列实现分支的静态核对，未执行编译、构建或测试。结论限于上述核对范围。

