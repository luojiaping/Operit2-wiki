## luojiaping @ 2026-11-11T07:40:53Z (https://github.com/luojiaping/Operit2-wiki/issues/11#issuecomment-6790113322)

复审结论：**仍需修改**。

复审版本：wiki `a851929c6f2c58d35f93231d65d65deaa1c60d48`；已核实上游 `AAswordman/Operit2` 最新 `main` 仍为 `364d1d594a0b7610e68fd804fc86fa342f18e14d`。

首轮四类问题已实质修复：不可达 Binding 的当前行为与设计要求已分开；实际交接链路已补充；屏障和代际去重已标为设计约束；四字段概念图与实际六字段协议类型已区分；主要机制和调用链补上了源码引用。

**[P2] 新增的配置身份校验断言漏了适用条件。** [正文第 169 行](https://github.com/luojiaping/Operit2-wiki/blob/a851929c6f2c58d35f93231d65d65deaa1c60d48/review/batch-01/arch-routing.md#L169)及 [facts 数组第 44 条](https://github.com/luojiaping/Operit2-wiki/blob/a851929c6f2c58d35f93231d65d65deaa1c60d48/review/batch-01/arch-routing.facts.json#L1)写成“目标节点续接前校验 extensionOwner 与 participantId，不一致时返回错误”，但 [MessageCoordinationDelegate.rs:495–501](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/services/core/MessageCoordinationDelegate.rs#L495)实际为：

```rust
if configuration.extensionOwner != MODEL_CONFIGURATION_OWNER
    && (configuration.extensionOwner != context.extensionOwner
        || configuration.profile.id != context.participantId)
```

该常量在 [ProviderRuntimeSupportService.rs:37](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/services/ProviderRuntimeSupportService.rs#L37)定义为 `"host.chat.model"`。这项与交接快照身份的额外一致性比较，仅在配置 `extensionOwner` 不是 `host.chat.model` 时执行，当前文案把有条件分支写成了所有续接配置的统一保证。

建议正文和 facts 一起改为：“对 extensionOwner 不是 host.chat.model 的配置，要求 extensionOwner 及 profile.id 与交接上下文身份一致，否则返回错误。”此项无需改代码，只需准确保留源码条件。

本轮限于首轮问题、关联正文修订及新增/改写 facts 的静态复核，未运行编译、构建或测试，未做真实双设备实验。


