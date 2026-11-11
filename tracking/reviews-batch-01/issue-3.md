## luojiaping @ 2026-11-11T07:08:07Z (https://github.com/luojiaping/Operit2-wiki/issues/3#issuecomment-6789482831)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

1. [正文第 45 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/intro-not-what.md#L45)及同名 facts 的凭证边界需修正。**[P1] 区分 Provider 凭证同步与节点身份/配对密钥的本地边界。** README:128 确实声明了“API key 默认节点本地、不随加入 Space 复制”的原则，但实现中 [ModelConfigManager.rs:108–112](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L108) 使用 Space 同步的 `PreferencesDataStore::newWithStorage`；[同文件:1332–1339](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L1332) 将完整 `ProviderProfile` 写入 `provider_<id>`，其 [ModelConfigData.rs:600–608](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/model/src/ModelConfigData.rs#L600) 包含 `apiKey`、`apiKeyPool`；[PreferencesDataStore.rs:2924–2966](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/PreferencesDataStore.rs#L2924) 为此创建同步日志和 descriptor。建议明确列出 README 原则与实现的冲突，说明 Provider 凭证存在随配置同步的路径，勿将其与设备身份、配对密钥及 OS 权限统称为“不复制”。这是**源码直引、wiki 未覆盖**；应同步修正正文、facts 和来源记录，未进行真实双设备同步实验。

2. **[P1] 将“目标不可达时原子接管”标为设计约束，补充当前实现边界。** [正文第 60 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/intro-not-what.md#L60)及 facts 复述架构文档:488，但 [CoreNodeRouter.rs:451–457](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/CoreNodeRouter.rs#L451) 的 `effectiveBinding` 明确说明 `without mutating ownership`：不可达时仅修改返回副本的 `nodeId`，没有比较写入持久化 Binding，也没有推进 generation。实现能支持“本次选择本地执行”，不能据此承诺“持久化 Binding 已完成原子接管”。建议正文和 facts 明确区分设计目标与该基线行为。此项为**源码直引、wiki 未覆盖**。

已抽查 Space 不是执行容器、Binding 不代表数据位置、切换不移动 Agent、业务同步授权条件及配对与加入 Space 的区别，并核对上述实际实现。本页 54 条 facts 引用路径均存在且行号未越界。未执行编译、构建或测试。


