第 2 轮复核结论：**仍需修改**。

本轮 wiki：`77e3b7ca`；核对源码：上游 main `053c6686`。复核范围是本次修订、对应原子事实及相邻调用链。

上一轮公开构造接口的版本问题已经修复：正文第 **12、220** 行与 fact 第 **11** 条，都明确区分旧基线的 Host 参数和当前 `Arc<VisualFileSystem>` 参数。该时效说明与 [PackageManager.rs:34](https://github.com/AAswordman/Operit2/blob/053c6686e61c7ede3027f1fe8e2a12018bb1a49e/core/crates/plugin/sdk/src/PackageManager.rs#L34)一致。

**[P2] 新增说明中的泛型类型会在网页上丢失，请恢复内联代码标记。** [正文第 12 行](https://github.com/luojiaping/Operit2-wiki/blob/77e3b7cae17eef5176f85a09f5dd2a7ab82d0eb2/review/batch-03/core-plugin-sdk.md#L12)及第 220 行把 `filesystem: Arc<VisualFileSystem>`、输入列表中的 `Arc<VisualFileSystem>` 和结尾的 `Arc<dyn FileSystemHost>` 写成了普通 Markdown 文本。

站点 [site/entry.html:117](https://github.com/luojiaping/Operit2-wiki/blob/77e3b7cae17eef5176f85a09f5dd2a7ab82d0eb2/site/entry.html#L117)及 [site/wiki.html:249](https://github.com/luojiaping/Operit2-wiki/blob/77e3b7cae17eef5176f85a09f5dd2a7ab82d0eb2/site/wiki.html#L249) 将 marked.parse 的结果设置为 innerHTML；同版本渲染器实际把尖括号部分原样输出为 HTML 标签。因此页面显示的是 `filesystem: Arc`、`Arc`，看不到本轮要澄清的类型参数。请将这两个段落中的完整 Rust 泛型类型包回反引号，使网页完整显示当前签名。facts 第 11 条的修订语义本身已经正确，这次问题集中在正文展示。

本轮为静态差异与源码核对；涉及显示问题时使用了站点同版本 Markdown 渲染器检查。未运行项目编译、构建或测试。

