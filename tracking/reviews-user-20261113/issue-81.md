# Issue 81 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:31:13Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/81#issuecomment-6854394729


本轮全量重审结论：需修改。审查 Wiki `f9c90d7ad06c8ec51cbfb6c67a2e252d2160b432`，区分条目声明基线 `364d1d594a0b7610e68fd804fc86fa342f18e14d` 与最新上游 `09249fb9ff3b660731b88f3846ebc26915ea89f7`。

[P2] 正文第14行和第157行仍把无服务商模型列表接口推导为“不走下载路径”。该推论在原基线就不成立：`ModelConfigManager.rs:389–394` 先执行 `requireCatalog()` 和过期刷新，随后才为 `OPENAI_CODEX` 跳过服务商列表抓取；`ModelSpecResolver.rs:95–109` 也对所有非 `LOCAL_MODEL` 服务商先要求完整目录，再设置固定模型列表。请改成“Codex 不请求服务商模型列表接口，模型行来自固定表；原基线的能力解析仍要求 models.dev 目录就绪”。fact 52 只说固定列表，本身正确，可保留。

另复核了首次下载共享、失败冷却与 stamp 最后写入顺序。本轮仅静态审查，未运行测试、构建、CI、模型请求或设备实验。

源码定位：
- [core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:389](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L389)
- [core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs:394](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L394)
- [core/crates/runtime/application/src/data/preferences/ModelSpecResolver.rs:95](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelSpecResolver.rs#L95)
