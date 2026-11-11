第 2 轮复核结论：**仍需修改**。

本轮 wiki：`77e3b7ca`；核对源码：上游 main `053c6686`。复核范围是本次修订、对应原子事实及相邻调用链。

上一轮语义问题已经修复：正文及 fact 第 **43** 条正确区分执行器安装与实际调用时的调度器检查；fact 第 **53** 条明确旧 fileSystemHost 与当前 filesystem/VFS 的版本关系；Dart 模型收录规则也已合并额外类型来源。

**[P2] 请保留泛型的代码标记，当前网页会丢掉类型参数。** [正文第 124 行](https://github.com/luojiaping/Operit2-wiki/blob/77e3b7cae17eef5176f85a09f5dd2a7ab82d0eb2/review/batch-03/core-proxy.md#L124)本轮把 `Option<T>` 改为普通文本；第 **151** 行新增的 `Arc<VisualFileSystem>` 也未包反引号。

用仓库同版本 marked 渲染后，`<T>`、`<VisualFileSystem>` 原样进入 HTML，站点插入 innerHTML 时会把它们当成标签。因此读者实际看到的是“把 Option 映射为 T?”和“filesystem() -> Arc”，公开类型信息不完整。渲染入口见 [site/entry.html:117](https://github.com/luojiaping/Operit2-wiki/blob/77e3b7cae17eef5176f85a09f5dd2a7ab82d0eb2/site/entry.html#L117)及 [site/wiki.html:249](https://github.com/luojiaping/Operit2-wiki/blob/77e3b7cae17eef5176f85a09f5dd2a7ab82d0eb2/site/wiki.html#L249)。

请把这两处完整类型表达式恢复为内联代码。当前源码实际分别是 Option 到可空类型的映射、以及 [lib.rs:283](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/proxy/local/src/lib.rs#L283)的 VFS 返回类型。facts 的版本说明本身无需撤销。

本轮为静态差异与源码核对；涉及显示问题时使用了站点同版本 Markdown 渲染器检查。未运行项目编译、构建或测试。

