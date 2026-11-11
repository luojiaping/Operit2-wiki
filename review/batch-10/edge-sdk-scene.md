---
title: Scene 服务与资源格式
module: edge
platforms: [all]
sources: 4
date: 2026-11-11
---

## 概述

- 原生 `edge.scene` 服务管四件事：有界索引资源、持久显示配置、条带绘制与本地触摸命中测试，没有 JS 运行时。`edge/sdk/scene/README.md:3`
- 在设备空间中的定位见 [[edge-architecture|Edge 在设备空间中的职责与边界]]。`edge/sdk/scene/README.md:3`
- 设备应用构造 `SceneService`，挂接带原子写入的 `RuntimeStorageHost`，路由原生调用，本地处理返回的触摸目标。`edge/sdk/scene/README.md:5`
- 线路与资产格式见 `plugins/docs/edge-scene.md`。`edge/sdk/scene/README.md:13`

## AI 速览

- `SERVICE_TARGET` — 服务目标，值为 "edge.scene"。`edge/sdk/scene/src/protocol.rs:2`
- `VERSION` — 协议版本 1。`edge/sdk/scene/src/protocol.rs:3`
- `ACTIONS` — 10 个动作：capabilities、config.read、config.apply、config.clear、state、pack.begin、pack.chunk、pack.commit、pack.abort、pack.remove。`edge/sdk/scene/src/protocol.rs:4`
- `MAX_REQUEST` — 请求上限 1024 字节。`edge/sdk/scene/src/protocol.rs:8`
- `MAX_REPLY` — 响应上限 4096 字节。`edge/sdk/scene/src/protocol.rs:9`
- `MAX_PACK` — 单包上限 4096 字节。`edge/sdk/scene/src/protocol.rs:10`
- `MAX_CACHE` — 缓存上限 8192 字节。`edge/sdk/scene/src/protocol.rs:11`
- `MAX_PACKS` — 最多 2 包。`edge/sdk/scene/src/protocol.rs:12`
- `MAX_ASSETS` — 每包最多 4 素材。`edge/sdk/scene/src/protocol.rs:13`
- `MAX_LAYERS` — 最多 4 图层。`edge/sdk/scene/src/protocol.rs:14`
- `MAX_CHUNK` — 上传块 256 字节。`edge/sdk/scene/src/protocol.rs:15`
- `SceneService` — 设备原生显示服务，含 state、storage、clock、width、height、reserved_top、touch 七个字段。`edge/sdk/scene/src/lib.rs:150`
- SceneService 的 `new` — 构造服务，要求 width 大于 0 且 height 大于 reserved_top。`edge/sdk/scene/src/lib.rs:158`
- `with_storage` — 挂接存储并从快照恢复配置与资源。`edge/sdk/scene/src/lib.rs:168`
- `call` — 原生调用主入口，接收 edge.scene 调用并经 `dispatch` 分发。`edge/sdk/scene/src/lib.rs:436`
- `dispatch` — 按动作分发并校验参数与容量。`edge/sdk/scene/src/lib.rs:274`
- `persist` — 把配置与引用资源写成一次原子快照。`edge/sdk/scene/src/lib.rs:190`
- `system_exit` — 停止当前显示，不动保存的配置。`edge/sdk/scene/src/lib.rs:219`
- `touch` — 本地触摸命中测试。`edge/sdk/scene/src/lib.rs:224`
- `advance_target_frame` — 推进指定 `target` 的图层帧。`edge/sdk/scene/src/lib.rs:240`
- `paint_strip` — 按条带绘制一帧。`edge/sdk/scene/src/lib.rs:251`
- `render_state` — 返回 active 与 revision。`edge/sdk/scene/src/lib.rs:203`
- `summary` — 返回 active、revision、taps 的 JSON。`edge/sdk/scene/src/lib.rs:207`
- `visual_snapshot` — 本地编辑器镜像，含图层与各包经 `STANDARD` 编码的数据。`edge/sdk/scene/src/lib.rs:212`
- `SceneConfiguration` — 显示配置，含 enabled、background、layers 三个字段。`edge/sdk/scene/src/lib.rs:89`
- `Layer` — 单图层，含 asset、x、y、scale 字段。`edge/sdk/scene/src/lib.rs:36`
- 单图层另含 `anchor`、`frame`、`play`、`loop`、`target` 字段。`edge/sdk/scene/src/lib.rs:47`
- `Rect` — 显示区域，含 x、y、w、h 四个 u16 字段。`edge/sdk/scene/src/lib.rs:28`
- `StoredConfiguration` — 快照记录，含 v、config、packs 三个字段。`edge/sdk/scene/src/lib.rs:99`
- `CONFIG_PATH` — 快照文件路径 runtime/device/display_scene.json。`edge/sdk/scene/src/lib.rs:84`
- `parse_pack` — 校验 ESP1 包并解析出 ESI1 素材。`edge/sdk/scene/src/lib.rs:449`
- `sample` — 按锚点与帧取图层像素。`edge/sdk/scene/src/lib.rs:520`
- `blend` — 用 `mix` 闭包混合各通道。`edge/sdk/scene/src/lib.rs:548`
- `ESP1` — 资源包格式，魔数 ESP1。`plugins/docs/edge-scene.md:64`
- `ESI1` — 索引色素材格式，魔数 ESI1。`plugins/docs/edge-scene.md:76`
- 主入口函数是 `call`：接收原生 edge.scene 调用，转 JSON 后由 `dispatch` 按动作分发。`edge/sdk/scene/src/lib.rs:436`
- 数据流向一句话：原生调用 → `call` 转 JSON → `dispatch` 按动作分发 → 返回含 v/ok 的回复。`edge/sdk/scene/src/lib.rs:436`

## 核心机制

### 服务职责与协议

- 服务目标 `SERVICE_TARGET` 为 "edge.scene"，协议版本 `VERSION` 为 1。`edge/sdk/scene/src/protocol.rs:2`
- 10 个动作由 `ACTIONS` 列出：capabilities、config.read、config.apply、config.clear、state、pack.begin、pack.chunk、pack.commit、pack.abort、pack.remove。`edge/sdk/scene/src/protocol.rs:4`
- 容量上限：单包 `MAX_PACK` 4096 字节，缓存 `MAX_CACHE` 8192 字节，最多 `MAX_PACKS` 2 包，每包 `MAX_ASSETS` 4 素材，`MAX_LAYERS` 4 图层，`MAX_CHUNK` 256 字节上传块。`edge/sdk/scene/src/protocol.rs:12`
- 请求序列化后超过 `MAX_REQUEST`（1024 字节）时拒绝。`edge/sdk/scene/src/lib.rs:275`
- 回复序列化后超过 `MAX_REPLY`（4096 字节）时返回错误。`edge/sdk/scene/src/lib.rs:442`
- 请求参数 `v` 必须等于 `VERSION`，否则返回 `SCENE_VERSION`。`edge/sdk/scene/src/lib.rs:276`
- 按动作限定允许字段，多余字段返回 `invalid` 错误。`edge/sdk/scene/src/lib.rs:286`
- 未知动作返回 `invalid` 错误。`edge/sdk/scene/src/lib.rs:284`
- invalid() 返回的错误码为 `SCENE_ARGS`。`edge/sdk/scene/src/lib.rs:18`
- 经 `Tools.device(nodeId).Edge.execute` 调用 `edge.scene`，参数带 v:1，失败时抛错（文档说法）。`plugins/docs/edge-scene.md:10`
- `capabilities` 返回屏幕、区域、输入、格式、容量、缓存和持久化能力（文档说法）。`plugins/docs/edge-scene.md:20`
- `config.read` 返回 enabled、background、layers（文档说法）。`plugins/docs/edge-scene.md:21`
- `config.apply` 返回 configured、persistent、revision（文档说法）。`plugins/docs/edge-scene.md:22`
- `config.clear` 保存默认关闭配置并恢复系统 UI（文档说法）。`plugins/docs/edge-scene.md:23`
- `state` 返回本地 active、taps、revision 诊断状态（文档说法）。`plugins/docs/edge-scene.md:24`
- `capabilities` 返回屏幕尺寸与格式 RGB565_LE、本地输入、保留区、持久化与动画能力、格式与容量上限。`edge/sdk/scene/src/lib.rs:290`
- `config.read` 返回当前 `SceneConfiguration`。`edge/sdk/scene/src/lib.rs:298`
- `state` 返回 active、taps、revision。`edge/sdk/scene/src/lib.rs:299`

### 配置与原子快照

- `SceneConfiguration` 含 enabled、background、layers 三个字段。`edge/sdk/scene/src/lib.rs:89`
- `SceneConfiguration` 默认关闭、背景 0、空图层。`edge/sdk/scene/src/lib.rs:95`
- 快照文件路径 `CONFIG_PATH` 为 runtime/device/display_scene.json。`edge/sdk/scene/src/lib.rs:84`
- 快照字节上限 `MAX_STORED_BYTES` 等于 ((MAX_CACHE + 2) / 3) * 4 + MAX_REQUEST + 1024。`edge/sdk/scene/src/lib.rs:85`
- 快照记录 `StoredConfiguration` 含 v、config、packs 三个字段。`edge/sdk/scene/src/lib.rs:99`
- `persist` 只保存配置图层引用的包，未被引用的包不进快照。`edge/sdk/scene/src/lib.rs:192`
- `persist` 经 `writeBytesAtomically` 写快照，失败返回 `SCENE_STORAGE`。`edge/sdk/scene/src/lib.rs:198`
- `persist` 在未挂接存储时直接返回成功，不做持久化。`edge/sdk/scene/src/lib.rs:191`
- `config.apply` 先 validate 再 persist，成功后才 apply 并返回 configured、persistent、revision。`edge/sdk/scene/src/lib.rs:305`
- `config.clear` 用默认配置走同一保存路径。`edge/sdk/scene/src/lib.rs:301`
- 显示配置和引用的原始资源作为单个快照原子保存（文档说法）。`plugins/docs/edge-scene.md:31`
- 保存失败不改变当前配置（文档说法）。`plugins/docs/edge-scene.md:31`
- 设备重启恢复配置及资源（文档说法）。`plugins/docs/edge-scene.md:31`
- 动画帧和点击计数属于本次设备运行（文档说法）。`plugins/docs/edge-scene.md:31`
- 配置包在保存完成后可以关闭或卸载（文档说法）。`plugins/docs/edge-scene.md:31`
- 系统退出只停止当前显示，保存配置仍保留（文档说法）。`plugins/docs/edge-scene.md:31`
- `config.clear` 清除保存配置（文档说法；实际是保存一份默认关闭配置，快照文件仍存在，'清除'指配置内容恢复默认而非删除文件）。`plugins/docs/edge-scene.md:31`
- 设备的可用持久化空间不足时保存失败返回 `SCENE_STORAGE`（文档说法）。`plugins/docs/edge-scene.md:33`
- 禁用宿主编辑器对设备运行没有影响（README 说法）。`edge/sdk/scene/README.md:9`
- `with_storage` 在快照文件存在时读回并校验版本等于 `VERSION` 且包数不超过 `MAX_PACKS`。`edge/sdk/scene/src/lib.rs:173`
- 恢复时对每包做 `STANDARD` 解码，单包超过 `MAX_PACK` 或总量超过 `MAX_CACHE` 时拒绝，并用 `parse_pack` 解析。`edge/sdk/scene/src/lib.rs:179`
- 恢复后经 `validate` 校验配置并经 `apply` 应用。`edge/sdk/scene/src/lib.rs:184`
- 测试断言保存失败时返回 `SCENE_STORAGE` 且存储内容与当前配置不变。`edge/sdk/scene/src/lib.rs:641`

### 资源上传

- `pack.begin` 在已有未完成上传时返回 `SCENE_BUSY`。`edge/sdk/scene/src/lib.rs:312`
- `pack.begin` 校验 packId 符合 id 规则。`edge/sdk/scene/src/lib.rs:314`
- 要求 `sha256` 为 64 位小写十六进制字符串。`edge/sdk/scene/src/lib.rs:320`
- 要求包大小在 5..=`MAX_PACK` 字节，否则返回 `SCENE_LIMIT`。`edge/sdk/scene/src/lib.rs:325`
- 拒绝已被应用配置引用的包（即使当前未启用显示），返回 `SCENE_IN_USE`。`edge/sdk/scene/src/lib.rs:328`
- 在缓存空间不足或包数已满时返回 `SCENE_LIMIT`。`edge/sdk/scene/src/lib.rs:337`
- 上传句柄由 `Uuid::new_v4` 生成。`edge/sdk/scene/src/lib.rs:345`
- 返回上传句柄 `upload` 与 `chunkBytes` `MAX_CHUNK`。`edge/sdk/scene/src/lib.rs:353`
- `pack.chunk`、`pack.commit`、`pack.abort` 共用入口，先校验存在未完成上传且句柄匹配。`edge/sdk/scene/src/lib.rs:359`
- `pack.abort` 放弃未完成上传并返回空对象。`edge/sdk/scene/src/lib.rs:363`
- 要求 `data` 经 `STANDARD` 解码后为 1..256 字节，文本超过 344 字符时拒绝。`edge/sdk/scene/src/lib.rs:369`
- 要求 `offset` 等于已收字节数，否则返回 `SCENE_OFFSET`。`edge/sdk/scene/src/lib.rs:387`
- 对已收过的相同数据返回当前 `offset`，不重复写入。`edge/sdk/scene/src/lib.rs:379`
- 在已收长度不等于声明长度时返回 `SCENE_OFFSET`。`edge/sdk/scene/src/lib.rs:393`
- 比对 SHA-256，不符返回 `SCENE_HASH`。`edge/sdk/scene/src/lib.rs:403`
- 用 `parse_pack` 校验格式后把包发布进缓存。`edge/sdk/scene/src/lib.rs:409`
- 成功后把 `revision` 加一。`edge/sdk/scene/src/lib.rs:419`
- `pack.remove` 拒绝删除正被保存配置引用的包，返回 `SCENE_IN_USE`。`edge/sdk/scene/src/lib.rs:424`
- `pack.remove` 删除不存在的包时返回 `SCENE_RESOURCE`。`edge/sdk/scene/src/lib.rs:427`
- `pack.begin` 返回 upload、chunkBytes（文档说法）。`plugins/docs/edge-scene.md:25`
- `pack.chunk` 返回当前 offset，data 为标准 base64（文档说法）。`plugins/docs/edge-scene.md:26`
- `pack.commit` 校验长度、SHA-256 和格式后发布缓存资源（文档说法）。`plugins/docs/edge-scene.md:27`
- `pack.abort` 放弃未完成上传（文档说法）。`plugins/docs/edge-scene.md:28`
- `pack.remove` 删除未被保存配置引用的资源（文档说法）。`plugins/docs/edge-scene.md:29`
- 测试断言错误的 SHA-256 返回 `SCENE_HASH`。`edge/sdk/scene/src/lib.rs:654`

### 坐标、锚点、叠加与动画

- `rect` 使用屏幕绝对逻辑坐标，原点左上，x 向右、y 向下，宽高为像素数（文档说法）。`plugins/docs/edge-scene.md:37`
- `rect` 必须完整位于屏幕内，y>=24 且宽高非零（文档说法）。`plugins/docs/edge-scene.md:38`
- 每层 x、y 是区域局部坐标、有符号 16 位整数，可部分位于区域外，显示时裁剪（文档说法）。`plugins/docs/edge-scene.md:39`
- `anchor` 默认 tl，center 为中心锚点，bc 为底边中心锚点（文档说法）。`plugins/docs/edge-scene.md:40`
- `anchor` 换算：tl 左上为 (x,y)，center 左上为 (x-floor(W/2),y-floor(H/2))，bc 左上为 (x-floor(W/2),y-H)（文档说法）。`plugins/docs/edge-scene.md:42`
- `scale` 默认 1，最近邻整数缩放，asset 为 packId:assetId（文档说法）。`plugins/docs/edge-scene.md:45`
- `background` 是 0–65535 的 RGB565 整数，默认黑色，填满租赁区域（文档说法）。`plugins/docs/edge-scene.md:46`
- 图片背景放在 layers 首层，后续宠物、道具按数组顺序从后到前叠加（文档说法）。`plugins/docs/edge-scene.md:47`
- alpha 为 straight alpha，0 完全透明、255 不透明（文档说法）。`plugins/docs/edge-scene.md:48`
- 各 RGB565 通道按 floor((foreground*alpha + background*(255-alpha) + 127)/255) 混合（文档说法）。`plugins/docs/edge-scene.md:49`
- `frame` 默认 0 且须为素材内有效帧，`play` 默认 false，`loop` 默认 true（文档说法）。`plugins/docs/edge-scene.md:50`
- 播放从 `frame` 开始，按素材 `frameMs` 推进，循环时取模，不循环时停在最后一帧（文档说法）。`plugins/docs/edge-scene.md:51`
- 每次 `config.apply` 从保存配置重新开始当前动画（文档说法）。`plugins/docs/edge-scene.md:52`
- 绘制条带在整帧开始冻结时间戳，避免同一帧不同条带使用不同动画帧（文档说法）。`plugins/docs/edge-scene.md:53`
- 本地动画不依赖 Core 每帧 RPC（文档说法）。`plugins/docs/edge-scene.md:54`
- 图层变更不一定等到正在绘制的帧结束才生效（文档说法）。`plugins/docs/edge-scene.md:54`
- `validate` 要求 scale 在 1..=8、anchor 为 tl、center、bc 之一、frame 小于素材帧数、target 符合 id 规则。`edge/sdk/scene/src/lib.rs:128`
- `apply` 把 active 置为 config.enabled，并同步 layers、background、config 与 started。`edge/sdk/scene/src/lib.rs:135`
- `taps` 清零，`revision` 加一。`edge/sdk/scene/src/lib.rs:141`
- `sample` 按 anchor 计算图层左上角：center 减半宽高的一半，bc 减半宽、高全减，默认取 x、y。`edge/sdk/scene/src/lib.rs:523`
- 在播放时按 `elapsed` 除以 `a.ms` 推进帧，循环取模，不循环停在最后一帧。`edge/sdk/scene/src/lib.rs:535`
- 按最近邻取像素：坐标除以 `scale` 后查调色板。`edge/sdk/scene/src/lib.rs:542`
- `blend` 用 `mix` 闭包按 (f*a + b*(255-a) + 127)/255 混合各通道。`edge/sdk/scene/src/lib.rs:548`

### 二进制素材格式

- 包里没有 ZIP、外部图片解码器、路径、脚本、下载 URL 或可执行代码（文档说法）。`plugins/docs/edge-scene.md:58`
- 包里只存索引色素材，多字节整数均小端，禁止尾随垃圾／截断（文档说法）。`plugins/docs/edge-scene.md:59`
- `ESP1` 包以魔数 ESP1 开头，assetCount 为 1..4（文档说法）。`plugins/docs/edge-scene.md:64`
- `ESP1` 包每素材含 idLength 1..24、ASCII assetId、u16 LE assetLength 与精确长度的 ESI1 素材（文档说法）。`plugins/docs/edge-scene.md:67`
- `ESP1` 包内 assetId 不能重名（文档说法）。`plugins/docs/edge-scene.md:68`
- `ESI1` 素材以魔数 ESI1 开头，宽高 1..96、帧数 1..8、调色板数 1..16、frameMs 50..2000（文档说法）。`plugins/docs/edge-scene.md:76`
- `ESI1` 调色板每项为 u16 LE RGB565 颜色加 u8 straight alpha，像素为 frameCount*width*height 个 u8 调色板索引（文档说法）。`plugins/docs/edge-scene.md:81`
- 每帧按行存放，先上后下、先左后右，每个索引必须小于 paletteCount（文档说法）。`plugins/docs/edge-scene.md:88`
- 所有帧共用同一调色板、尺寸和帧间隔（文档说法）。`plugins/docs/edge-scene.md:89`
- SHA-256 覆盖整个 `ESP1` 包，包括头与 ID（文档说法）。`plugins/docs/edge-scene.md:89`
- 要求包以 `ESP1` 魔数开头。`edge/sdk/scene/src/lib.rs:458`
- 要求素材数在 1..=`MAX_ASSETS`。`edge/sdk/scene/src/lib.rs:461`
- 要求包内素材 ID 符合 `id` 规则且不重名。`edge/sdk/scene/src/lib.rs:470`
- 要求素材以 `ESI1` 魔数开头且长度至少 10 字节。`edge/sdk/scene/src/lib.rs:477`
- 要求素材宽高在 1..96、帧数在 1..8、调色板数在 1..16、帧间隔 `ms` 在 50..2000。`edge/sdk/scene/src/lib.rs:486`
- 要求素材长度精确等于头加调色板加像素数，且每个像素索引小于调色板总数 `p`。`edge/sdk/scene/src/lib.rs:496`
- 在解析结束位置不等于包长时拒绝尾随垃圾。`edge/sdk/scene/src/lib.rs:515`

### 本地输入与集成

- 有 target 的图层按从前到后进行命中测试，透明像素不响应（文档说法）。`plugins/docs/edge-scene.md:93`
- `SceneService.touch` 返回本地 target，系统退出拥有本地优先级（文档说法）。`plugins/docs/edge-scene.md:93`
- 设备应用使用 `SceneService::new(width, height, reserved_top, touch).with_storage(storage)`，把原生 `edge.scene` Call 接到 `SceneService.call`，把显示条带接到 `paint_strip`（文档说法）。`plugins/docs/edge-scene.md:95`
- 当前 ESP32 和模拟器使用 320×240 屏幕与 24 像素系统栏（文档说法）。`plugins/docs/edge-scene.md:95`
- 其他设备可以采用自己的显示协议（文档说法）。`plugins/docs/edge-scene.md:95`
- `com.operit.edge_pixel_pet` 提供 inspect、apply_configuration、clear_configuration，用于配置这个原生服务（文档说法）。`plugins/docs/edge-scene.md:97`
- `touch` 在未启用触摸时返回 None。`edge/sdk/scene/src/lib.rs:225`
- `touch` 只在场景激活且坐标落在 rect 内才做命中测试。`edge/sdk/scene/src/lib.rs:229`
- 命中测试按 `layers` 从前到后进行，`alpha` 为 0 的像素不响应。`edge/sdk/scene/src/lib.rs:231`
- 命中目标时 `taps` 加一。`edge/sdk/scene/src/lib.rs:237`
- `advance_target_frame` 在未激活时直接返回。`edge/sdk/scene/src/lib.rs:242`
- 把指定 `target` 的图层 `frame` 加一对帧数取模，并把 `play` 置 false。`edge/sdk/scene/src/lib.rs:246`
- `paint_strip` 在未激活或缓冲区长度不符时直接返回。`edge/sdk/scene/src/lib.rs:253`
- 按行绘制，像素从 `background` 起步再按图层顺序经 `blend` 叠加。`edge/sdk/scene/src/lib.rs:260`
- 像素以 `to_le_bytes` 小端写入缓冲区。`edge/sdk/scene/src/lib.rs:269`
- `system_exit` 把 active 置 false 并把 revision 加一。`edge/sdk/scene/src/lib.rs:219`
- 测试断言恢复后 touch(4,6) 返回 pet。`edge/sdk/scene/src/lib.rs:626`
- 测试断言 system_exit 后 active 为 false 且 revision 加一。`edge/sdk/scene/src/lib.rs:629`

## 关键符号

- `SERVICE_TARGET`：服务目标 "edge.scene"。`edge/sdk/scene/src/protocol.rs:2`
- `VERSION`：协议版本 1。`edge/sdk/scene/src/protocol.rs:3`
- `ACTIONS`：10 个动作的常量数组。`edge/sdk/scene/src/protocol.rs:4`
- `MAX_REQUEST`：请求上限 1024 字节。`edge/sdk/scene/src/protocol.rs:8`
- `MAX_REPLY`：响应上限 4096 字节。`edge/sdk/scene/src/protocol.rs:9`
- `MAX_PACK`：单包上限 4096 字节。`edge/sdk/scene/src/protocol.rs:10`
- `MAX_CACHE`：缓存上限 8192 字节。`edge/sdk/scene/src/protocol.rs:11`
- `MAX_PACKS`：最多 2 包。`edge/sdk/scene/src/protocol.rs:12`
- `MAX_ASSETS`：每包最多 4 素材。`edge/sdk/scene/src/protocol.rs:13`
- `MAX_LAYERS`：最多 4 图层。`edge/sdk/scene/src/protocol.rs:14`
- `MAX_CHUNK`：上传块 256 字节。`edge/sdk/scene/src/protocol.rs:15`
- `Rect`：显示区域，x、y、w、h 四个 u16 字段。`edge/sdk/scene/src/lib.rs:28`
- `Layer`：单图层，含 asset、x、y、scale 字段。`edge/sdk/scene/src/lib.rs:36`
- 单图层另含 `anchor`、`frame`、`play`、`loop`、`target` 字段。`edge/sdk/scene/src/lib.rs:47`
- `SceneConfiguration`：显示配置，含 enabled、background、layers 三个字段。`edge/sdk/scene/src/lib.rs:89`
- `StoredConfiguration`：快照记录，含 v、config、packs 三个字段。`edge/sdk/scene/src/lib.rs:99`
- `CONFIG_PATH`：快照文件路径 runtime/device/display_scene.json。`edge/sdk/scene/src/lib.rs:84`
- `MAX_STORED_BYTES`：快照字节上限。`edge/sdk/scene/src/lib.rs:85`
- `SceneService`：设备原生显示服务。`edge/sdk/scene/src/lib.rs:150`
- SceneService 的 `new`：构造服务，要求 width 大于 0 且 height 大于 reserved_top。`edge/sdk/scene/src/lib.rs:158`
- `with_storage`：挂接存储并从快照恢复配置与资源。`edge/sdk/scene/src/lib.rs:168`
- `persist`：把配置与引用资源写成一次原子快照。`edge/sdk/scene/src/lib.rs:190`
- `validate`：校验图层数、scale、anchor、frame 与 target。`edge/sdk/scene/src/lib.rs:124`
- `render_state`：返回 active 与 revision。`edge/sdk/scene/src/lib.rs:203`
- `summary`：返回 active、revision、taps 的 JSON。`edge/sdk/scene/src/lib.rs:207`
- `visual_snapshot`：本地编辑器镜像。`edge/sdk/scene/src/lib.rs:212`
- `system_exit`：停止当前显示，不动保存的配置。`edge/sdk/scene/src/lib.rs:219`
- `touch`：本地触摸命中测试。`edge/sdk/scene/src/lib.rs:224`
- `advance_target_frame`：推进指定 `target` 的图层帧。`edge/sdk/scene/src/lib.rs:240`
- `paint_strip`：按条带绘制一帧。`edge/sdk/scene/src/lib.rs:251`
- `tick`：返回 `now()` 的毫秒值（截断为 `u32`），供 paint_strip 的 `tick` 参数使用。`edge/sdk/scene/src/lib.rs:273`
- `dispatch`：按动作分发并校验参数与容量。`edge/sdk/scene/src/lib.rs:274`
- `call`：原生调用主入口。`edge/sdk/scene/src/lib.rs:436`
- `parse_pack`：校验 ESP1 包并解析出 ESI1 素材。`edge/sdk/scene/src/lib.rs:449`
- `sample`：按锚点与帧取图层像素。`edge/sdk/scene/src/lib.rs:520`
- `blend`：按 straight alpha 混合 RGB565 各通道。`edge/sdk/scene/src/lib.rs:548`
- `ESP1`：资源包格式。`plugins/docs/edge-scene.md:64`
- `ESI1`：索引色素材格式。`plugins/docs/edge-scene.md:76`
- `com.operit.edge_pixel_pet`：配置该原生服务的包，提供 inspect、apply_configuration、clear_configuration（文档说法）。`plugins/docs/edge-scene.md:97`

## 调用链

1. 设备应用用 SceneService 的 `new`(width, height, reserved_top, touch) 构造服务。`edge/sdk/scene/src/lib.rs:158`
2. `with_storage` 挂接 `RuntimeStorageHost`，快照文件存在时读回并校验版本与包数，恢复配置与资源。`edge/sdk/scene/src/lib.rs:168`
3. `call` 把 CoreValue 转 JSON 后经 `dispatch` 按动作分发。`edge/sdk/scene/src/lib.rs:436`
4. `capabilities` 返回屏幕、格式、容量与缓存能力。`edge/sdk/scene/src/lib.rs:290`
5. `config.read` 返回当前 `SceneConfiguration`。`edge/sdk/scene/src/lib.rs:298`
6. pack.begin 返回上传句柄 `upload` 与 `chunkBytes` `MAX_CHUNK`。`edge/sdk/scene/src/lib.rs:353`
7. pack.chunk 要求 `offset` 等于已收字节数，分块上传数据。`edge/sdk/scene/src/lib.rs:387`
8. 比对 SHA-256，不符返回 `SCENE_HASH`。`edge/sdk/scene/src/lib.rs:403`
9. 用 `parse_pack` 校验格式后把包发布进缓存。`edge/sdk/scene/src/lib.rs:409`
10. `config.apply` 先 validate 再 persist，成功后才 apply 并返回 configured、persistent、revision。`edge/sdk/scene/src/lib.rs:305`
11. 按行绘制，像素从 `background` 起步再按图层顺序经 `blend` 叠加。`edge/sdk/scene/src/lib.rs:260`
12. 像素以 `to_le_bytes` 小端写入缓冲区。`edge/sdk/scene/src/lib.rs:269`
13. 命中测试按 `layers` 从前到后进行，`alpha` 为 0 的像素不响应。`edge/sdk/scene/src/lib.rs:231`
14. 命中目标时 `taps` 加一。`edge/sdk/scene/src/lib.rs:237`
15. 把指定 `target` 的图层 `frame` 加一对帧数取模，并把 `play` 置 false。`edge/sdk/scene/src/lib.rs:246`
16. `system_exit` 把 active 置 false 并把 revision 加一。`edge/sdk/scene/src/lib.rs:219`
17. `config.clear` 用默认配置走同一保存路径。`edge/sdk/scene/src/lib.rs:301`
18. 设备重启后 `with_storage` 再次读回快照，恢复配置与资源。`edge/sdk/scene/src/lib.rs:168`

## 来源

- `edge/sdk/scene/README.md`
- `edge/sdk/scene/src/lib.rs`
- `edge/sdk/scene/src/protocol.rs`
- `plugins/docs/edge-scene.md`
- 四份 seed 文件合计 792 行（README 17 行、lib.rs 663 行、protocol.rs 15 行、文档 97 行），与大纲 est_lines: 792 一致；源码基线为 AAswordman/Operit2 @ 364d1d594（2026-11-11，本地 checkout 已核验 git rev-parse HEAD）。
- 单元测试命令为 `cargo test --manifest-path edge/sdk/scene/Cargo.toml --lib`。`edge/sdk/scene/README.md:16`
- 否定性结论核验方法（2026-11-12，基线 364d1d594）：对四份 seed 文件执行 `grep -rni "http"`，零命中，四份 seed 文件中无 HTTP 引用、无下载地址；文档称包里没有下载 URL。`plugins/docs/edge-scene.md:58`
- `com.operit.edge_pixel_pet` 只出现在文档中：对两份代码文件与 README 执行 `grep -rn "com.operit.edge_pixel_pet"` 零命中，仅文档命中。`plugins/docs/edge-scene.md:97`
- 本页 4 份 seed 文件已全部读完，无未读文件。
- 文档提到的调用示例只按文档说法写入，未在代码 seed 中验证。`plugins/docs/edge-scene.md:10`
- `com.operit.edge_pixel_pet` 只按文档说法写入，未在代码 seed 中验证。`plugins/docs/edge-scene.md:97`
- 320×240 屏幕与 24 像素系统栏的表述只针对当前 ESP32 和模拟器，其他设备可以采用自己的显示协议；服务本身为设备侧原生 Rust 实现，不区分 Host，故 platforms 标 [all]。`plugins/docs/edge-scene.md:95`
- 正文中标（文档说法）的断言只来自文档或 README，本页代码 seed 未验证对应实现；标（README 说法）的断言只来自 README。`edge/sdk/scene/README.md:9`
