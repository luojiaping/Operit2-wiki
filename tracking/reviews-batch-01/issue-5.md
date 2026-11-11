## luojiaping @ 2026-11-11T07:03:38Z (https://github.com/luojiaping/Operit2-wiki/issues/5#issuecomment-6789408164)

审查结论：**需修改**。

核对基线：wiki `b75bcad9`，源码 `AAswordman/Operit2@364d1d594a0b7610e68fd804fc86fa342f18e14d`。以下是静态源码审查意见。

1. **[P1] 第 143 行的“API 密钥……加入 Space 不会自动复制”不能作为当前实现保证。** 正文与 facts.json 均直接沿用了 README:128，但基线实现将完整 Provider 配置写入 Space 同步偏好：
   - [ModelConfigManager.rs:108–112](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L108-L112) 使用 `PreferencesDataStore::newWithStorage`；
   - [ModelConfigManager.rs:1332–1339](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L1332-L1339) 将整个 `ProviderProfile` 序列化为 `provider_<id>`，其中 [ModelConfigData.rs:600–608](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/model/src/ModelConfigData.rs#L600-L608) 包含 `apiKey` 与 `apiKeyPool`；
   - [PreferencesDataStore.rs:2924–2966](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/persistence/store/src/PreferencesDataStore.rs#L2924-L2966) 明确创建 Space 同步 store。
   
   建议区分节点身份/配对密钥、本地 OS 权限和 Provider 配置，说明 Provider 凭证存在随配置同步的实现路径，并将 README 与实现的冲突显式标出。以上属于**源码直引、wiki 未覆盖**，未进行真实双设备同步实验；请同时修正文案和对应原子事实。

2. **[P2] 第 165 行混淆了显示二维码、手动配对与连接码配对三种操作。** `link qr` 在提供连接码的一端显示二维码；接收连接码的一端运行 `link pair <connection-code>`。源码 [link.rs:121–130](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/cli/src/cli/link.rs#L121-L130) 在 `operit://` 分支完成配对后直接返回，六位码输入只属于设备发现的手动配对分支。建议拆成两条明确的两端操作，避免让连接码用户等待一个不会出现的六位码提示。

3. **[P2] 第 166 行缺少加入申请的审批/状态确认，首次连接流程不能以“提交 join 后 show”直接收尾。** [link.rs:795–801](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/cli/src/cli/link.rs#L795-L801) 中 `space join` 只提交申请并打印回执；[link.rs:803–834](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/cli/src/cli/link.rs#L803-L834) 另有 `requests incoming/outgoing`、`refresh` 与 `approve/reject`。建议写明普通手动配对后的审批步骤及成功判据，并区分 Flutter 的“Confirm join”邀请流程。

已核对：CLI 命令分发及配对分支、Web Access URL 与开发服务器配置、快照导出/恢复入口；本页 65 条 facts 的引用路径均存在且行号未越界。引用可定位不等于语义均已证实。未执行编译、构建或测试。


