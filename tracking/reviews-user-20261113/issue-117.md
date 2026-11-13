# Issue 117 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:33:34Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/117#issuecomment-6854448052


本轮全量重审结论：需修改。Wiki `f9c90d7`；按声明基线 `364d1d594` 逐项核对，并对照最新上游 `09249fb9`。

1. [P2] 第89行、fact 18 称 rescue 的 export、inspect、import 都接受 `--confirm`，但 `apps/cli/src/rescue.rs:35-36` 在实际选项遍历中明确拒绝 export/inspect 的该标志，报 `--confirm is only valid for import and resume`。第22行只是候选选项表，不能跳过后续条件理解。应写公共根目录选项与仅 import/resume 的确认开关，和本页第88行保持一致。

2. [P2] 第34、35、118、119行的完整 CLI 命令没有放进代码格式，`<snapshot-zip-path>` 被站点自己的 `marked` 解析成 HTML 标签。已使用此 Wiki 快照的 `site/vendor/marked.min.js` 直接复现，输出确实是裸 `<snapshot-zip-path>` 而不是可见的转义文字；`site/entry.html:117` 将其插入 innerHTML，读者会看不到必填路径占位符。请将完整命令用反引号或 fenced code 包住。

3. [P3] 第39行、fact 9 把 `Detected domains` 解释成源快照检测到的“域名”，实际是数据域/类别。`core/crates/runtime/application/src/data/backup/operit1/Operit1ModelMigration.rs:154-191` 收集的是 `model_configs`、`chat_history`、各 DataStore 名及 `memory`/`user_files`，没有提取网络域名。请同步更正文和 fact 9。

另核对了归档格式/大小限制、预检先于导入、thinking 全局设置不采纳及一代导出来源。上述问题在声明基线即成立，非要求追逐版本号。仅静态核查及现有Markdown解析器复现，未执行导入、数据救援、测试或构建。

源码定位：
- [core/crates/runtime/application/src/data/backup/operit1/Operit1ModelMigration.rs:154](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/backup/operit1/Operit1ModelMigration.rs#L154)
- [apps/cli/src/rescue.rs:35](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/cli/src/rescue.rs#L35)
- [site/entry.html:117](https://github.com/luojiaping/Operit2-wiki/blob/f9c90d7ad06c8ec51cbfb6c67a2e252d2160b432/site/entry.html#L117)
