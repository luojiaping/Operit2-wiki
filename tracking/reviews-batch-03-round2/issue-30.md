第 2 轮复核结论：**本轮已列问题均已修复，未发现新的阻断问题**。

本轮 wiki：`77e3b7ca`；核对源码：上游 main `053c6686`。复核范围是本次修订、对应原子事实及相邻调用链。

正文第 **102–105** 行及 fact 第 **52** 条，已明确 512 是配置常量，拒绝路径不清理，只有成功消费令牌后调用 prune；不再承诺无条件来源桶硬上限。与 [pairing_throttle.rs:91](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/node/runtime/src/peer/pairing_throttle.rs#L91)及第 **96–101、112–120** 行一致。

正文第 **152、153** 行及 facts 第 **96、97** 条，也分别标出了旧基线的 version 15／7 个根与当前源码的 version 19／8 个根，见 [peer-protocol.json:116](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/peer-protocol.json#L116)。正文和事实均未再将旧快照值作为当前版本值。

本轮为静态差异与源码核对；涉及显示问题时使用了站点同版本 Markdown 渲染器检查。未运行项目编译、构建或测试。

