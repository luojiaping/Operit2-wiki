作者：luojiaping
时间：2026-11-11T08:51:15Z UTC
comment_id：6791461830

审查结论：**需修改**。

审查版本：wiki `f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50`；已核实上游 `AAswordman/Operit2` 最新 `main` 为 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与条目标注一致。

**[P2] validate_source_files 的“只验路径合法与重复”遗漏了实际拒绝条件。** [正文第 90 行](https://github.com/luojiaping/Operit2-wiki/blob/f8bc7166f67cbaf74b88a8c86a4906fdd0c24a50/review/batch-02/core-persistence-rescue.md#L90)及 facts 第 71 条使用了排他表述，但 [rescue/lib.rs:340–347](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/rescue/src/lib.rs#L340) 还检查 `MAX_FILES` 文件数量上限，并调用 `validate_ancestors` 拒绝父子路径重叠。

例如同时提供 `a` 与 `a/b`，每条路径单独合法且没有重复，该函数仍会拒绝；超过文件数上限也在此处直接报错。建议正文和 facts 一起列明“文件数量上限、路径合法性、重复路径、祖先重叠”四类检查，并保留它与后续 payload 长度/哈希验证的职责区别。

另已核对归档校验、layout 限制、payload 验证以及暂存后提交的流程，未发现其他阻断问题。

本轮为正文、对应 facts 和所列实现分支的静态核对，未执行编译、构建或测试。结论限于上述核对范围。

