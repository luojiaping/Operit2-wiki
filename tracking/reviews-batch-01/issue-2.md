## luojiaping @ 2026-11-11T07:08:02Z (https://github.com/luojiaping/Operit2-wiki/issues/2#issuecomment-6789481374)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

1. [正文第 150 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/intro-overview.md#L150)及同名 facts 的凭证边界需修正。**[P1] 区分 Provider 凭证同步与节点身份/配对密钥的本地边界。** README:128 确实声明了“API key 默认节点本地、不随加入 Space 复制”的原则，但实现中 [ModelConfigManager.rs:108–112](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L108) 使用 Space 同步的 `PreferencesDataStore::newWithStorage`；[同文件:1332–1339](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L1332) 将完整 `ProviderProfile` 写入 `provider_<id>`，其 [ModelConfigData.rs:600–608](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/model/src/ModelConfigData.rs#L600) 包含 `apiKey`、`apiKeyPool`；[PreferencesDataStore.rs:2924–2966](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/PreferencesDataStore.rs#L2924) 为此创建同步日志和 descriptor。建议明确列出 README 原则与实现的冲突，说明 Provider 凭证存在随配置同步的路径，勿将其与设备身份、配对密钥及 OS 权限统称为“不复制”。这是**源码直引、wiki 未覆盖**；应同步修正正文、facts 和来源记录，未进行真实双设备同步实验。

2. **[P2] Web 开发步骤调用了基线中不存在的脚本。** [正文第 198 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/intro-overview.md#L198)至第 200 行和 facts 第 59、60 条保留“双终端 + Node 代理 + 4836”的旧流程，但 `tools/dev_web_access_proxy.mjs` 在该提交不存在，用户照做会失败。[Web README:18–30](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/flutter/app/web/README.md#L18) 已说明 Flutter 原生读取 `web_dev_config.yaml`、不需要单独的 Node 代理；[web_dev_config.yaml:3–5](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/flutter/app/web_dev_config.yaml#L3) 配置服务地址 `127.0.0.1:4835`。请改用 `fvm flutter run -d web-server` 后访问 `http://127.0.0.1:4835`，同步修正文案和 facts，并把实现来源加入本页来源记录。

3. **[P2] 修正 facts 中 PB_SBC01_H3 的入口目录。** facts 第 61 条“仓库结构 apps/ 下有 cli、pb_sbc01_h3……”沿用了 README:213 的旧目录树；正文第 120 行已写成 `edge/boards/pb_sbc01_h3`。固定基线实际入口为 [edge/boards/pb_sbc01_h3/Cargo.toml:1](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/edge/boards/pb_sbc01_h3/Cargo.toml#L1)，[README.md:98](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/README.md#L98) 的产品表格也使用新路径。请同步更正原子事实，避免 AI 导航到不存在的 `apps/pb_sbc01_h3`。

已抽查任务交接边界（README:22）、Web Access 与独立节点的区别（README:72）、默认 TUI 入口（README:175），并核对凭证存储、Web 配置与板卡目录。本页 65 条 facts 引用路径均存在且行号未越界；这不等于全部语义已被实现证实。未执行编译、构建或测试。


