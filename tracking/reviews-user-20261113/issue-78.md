# Issue 78 用户评审意见

- 作者：luojiaping
- 时间：2026-11-13T13:30:55Z
- 链接：https://github.com/luojiaping/Operit2-wiki/issues/78#issuecomment-6854387684


本轮复核正文与117条facts，仍需修改第81行的预算保证。MAX_VALIDATOR_MEMORY_BYTES=512MiB只是一处常量定义，基线364d1d594及最新09249fb9中没有执行消费者；最新worker的initialize()未提供受限Memory，build_preview.py:73-85也未设置Wasm max-memory。输入字节、像素和图片解码器192MiB限制不等于整个校验器512MiB内存上限。请写成已声明但未接入执行约束的预算，不宣称硬保证；15秒应限定为theme_contract_client.js的Worker任务计时，不能泛化到原生同步校验。另核了PNG/JPEG格式、解码尺寸、确定性Stored ZIP与返回前完整自检，未见问题。Wiki固定f9c90d7，未执行构建或测试。

源码定位：
- [core/crates/plugin/theme/src/lib.rs:62](https://github.com/AAswordman/Operit2/blob/09249fb9ff3b660731b88f3846ebc26915ea89f7/core/crates/plugin/theme/src/lib.rs#L62)
