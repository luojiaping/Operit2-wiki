## luojiaping @ 2026-11-11T07:39:49Z (https://github.com/luojiaping/Operit2-wiki/issues/2#issuecomment-6790085164)

复审结论：**仍需修改**。

复审版本：wiki `a851929c6f2c58d35f93231d65d65deaa1c60d48`；已核实上游 `AAswordman/Operit2` 最新 `main` 仍为 `364d1d594a0b7610e68fd804fc86fa342f18e14d`。

首轮的旧 Web 开发流程和板卡入口已修复：[正文:208–213](https://github.com/luojiaping/Operit2-wiki/blob/a851929c6f2c58d35f93231d65d65deaa1c60d48/review/batch-01/intro-overview.md#L208)及 facts 第 59、60 条已改为 Flutter 原生服务器与 4835；facts 第 61 条已改为 `edge/boards/pb_sbc01_h3`。这些与 [Web README:18–30](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/apps/flutter/app/web/README.md#L18)、真实板卡入口一致。新增 Provider 同步实现证据也核对成立。

**[P1] 旧的“不复制”原子事实尚未替换，机器事实仍互相冲突。** [正文第 150 行](https://github.com/luojiaping/Operit2-wiki/blob/a851929c6f2c58d35f93231d65d65deaa1c60d48/review/batch-01/intro-overview.md#L150)和 [facts 数组第 48 条（文件第 1 行）](https://github.com/luojiaping/Operit2-wiki/blob/a851929c6f2c58d35f93231d65d65deaa1c60d48/review/batch-01/intro-overview.facts.json#L1)仍无条件写“API key……不会因为加入 Space 自动复制”；新正文第 151–160 行及 facts 第 66–72 条又说明完整 Provider 配置进入同步存储。对单独检索第 48 条的 AI 而言，后文追加说明不能修正这条可独立取出的安全保证。

实现证据仍是 [ModelConfigManager.rs:112](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L112) 使用同步 store、[同文件:1333](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/runtime/application/src/data/preferences/ModelConfigManager.rs#L1333)完整序列化 Provider，以及 [ModelConfigData.rs:606–608](https://github.com/AAswordman/Operit2/blob/364d1d594a0b7610e68fd804fc86fa342f18e14d/core/crates/foundation/model/src/ModelConfigData.rs#L606) 的凭证字段。

建议参照本批 `intro-not-what` 的修订，将旧正文和 facts 第 48 条一起改成“README 声明的原则”，显式注明与当前实现冲突；也可直接替换成区分设计原则和实现的完整事实。无需为此增加同步实验。

本轮限于首轮问题、关联正文修订及新增/改写 facts 的静态复核，未运行编译、构建或测试，未做真实双设备实验。


