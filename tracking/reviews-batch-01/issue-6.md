## luojiaping @ 2026-11-11T07:09:37Z (https://github.com/luojiaping/Operit2-wiki/issues/6#issuecomment-6789507121)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，上游 `AAswordman/Operit2` 最新 `main` 已确认是 `364d1d594a0b7610e68fd804fc86fa342f18e14d`，与 wiki 标注一致。以下是静态源码审查意见。

1. [正文第 151 行](https://github.com/luojiaping/Operit2-wiki/blob/b75bcad9d63959f0108f81193119e372eca38f4a/review/batch-01/arch-overview.md#L151)及 facts 第 23 条的凭证边界需修正。**[P1] 区分 Provider 凭证同步与节点身份/配对密钥的本地边界。** README:128 确实声明了“API key 默认节点本地、不随加入 Space 复制”的原则，但实现中 [ModelConfigManager.rs:108–112](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L108) 使用 Space 同步的 `PreferencesDataStore::newWithStorage`；[同文件:1332–1339](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L1332) 将完整 `ProviderProfile` 写入 `provider_<id>`，其 [ModelConfigData.rs:600–608](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/model/src/ModelConfigData.rs#L600) 包含 `apiKey`、`apiKeyPool`；[PreferencesDataStore.rs:2924–2966](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/PreferencesDataStore.rs#L2924) 为此创建同步日志和 descriptor。建议明确列出 README 原则与实现的冲突，说明 Provider 凭证存在随配置同步的路径，勿将其与设备身份、配对密钥及 OS 权限统称为“不复制”。这是**源码直引、wiki 未覆盖**；应同步修正正文、facts 和来源记录，未进行真实双设备同步实验。

2. **[P2] 第 85 行“每个同步周期对每个可达成员先发送一次探针”缺少条件。** [SpacePersistenceSyncService.rs:716–734](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/node/runtime/src/SpacePersistenceSyncService.rs#L716) 先处理退避、待处理工作和失败重试；未获存储复制授权的成员走 `authority_only` 分支，直接继续控制交换，只有正常存储复制门控分支才调用摘要探针。建议限定为“具备存储复制授权、处于正常变更门控状态的可达成员使用 `syncClockDigest` 判断是否需要完整交换”。这是**源码直引、wiki 未覆盖**。 请同步修正 facts 第 43 条。

另已抽查项目定位（README:3）、crate 依赖方向（core/CRATE_BOUNDARIES.md:63）、PeerLink crate 名（core/crates/node/peer-link/Cargo.toml:2），这些项目与引用一致。frontmatter 和六个固定小节齐全；本页 100 条 facts 引用路径均存在且行号未越界。未执行编译、构建或测试。


