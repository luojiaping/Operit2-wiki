---
title: 持久化——数据救援
module: core
platforms: [all]
sources: [core/crates/persistence/rescue/src/lib.rs, docs/data-rescue.md]
date: 2026-11-11
---

# 持久化——数据救援

## 概述

- `DataRescue` 是离线便携式数据救援：不启动 Core 或数据库，直接操作 Host 拥有的存储（core/crates/persistence/rescue/src/lib.rs:1）
- 输入是 Host 选定的常规文件，输出是 ZIP 归档，清单以 `manifest.json` 条目写入归档（core/crates/persistence/rescue/src/lib.rs:224）
- 归档清单的 `format` 为 `operit.data-rescue`，`version` 为 1（core/crates/persistence/rescue/src/lib.rs:216）
- 恢复前对每个 payload 逐条调用 verify_payload 验证（core/crates/persistence/rescue/src/lib.rs:271）
- 恢复先暂存全部文件，再由 `commit_restore` 一次发布（core/crates/persistence/rescue/src/lib.rs:293）
- 本 crate 不区分平台：布局由 Host 的 `layout()` 提供（core/crates/persistence/rescue/src/lib.rs:69）
- 上游文档称原生布局为 `operit.files.v1`、浏览器布局为 `operit.browser.v1`（docs/data-rescue.md:20）

## AI 速览

- `DataRescue` — 离线救援执行器，持 `host` 与 `archives`（core/crates/persistence/rescue/src/lib.rs:93）
- `RescueHost` — Host 存储契约：离线存储、独占访问与发布（core/crates/persistence/rescue/src/lib.rs:65）
- `RescueManifest` — 归档清单：`format`、`version`、`layout`、`files`、`metadata`（core/crates/persistence/rescue/src/lib.rs:56）
- `RescueFile` — 单个常规文件：`path`、`byte_length`、`sha256`（core/crates/persistence/rescue/src/lib.rs:47）
- `RescueProgress` — 维护阶段的已完成工作计数器（core/crates/persistence/rescue/src/lib.rs:21）
- `ArchiveIo` — Host 暂存到 ZIP 可寻址 I/O 的适配器（core/crates/persistence/rescue/src/lib.rs:398）
- `execute` — 按 `operation` 分发救援操作的主入口（core/crates/persistence/rescue/src/lib.rs:100）
- `export` — 流式导出 payload 与完整性清单（core/crates/persistence/rescue/src/lib.rs:135）
- `inspect` — 验证归档全部条目并返回清单（core/crates/persistence/rescue/src/lib.rs:236）
- `restore` — 验证归档、暂存全部文件、一次发布（core/crates/persistence/rescue/src/lib.rs:278）
- `verify_storage_manifest` — 按 Host 重验已暂存 payload（core/crates/persistence/rescue/src/lib.rs:149）
- `validate_path` — 路径边界校验（core/crates/persistence/rescue/src/lib.rs:316）
- `verify_payload` — payload 流式校验（core/crates/persistence/rescue/src/lib.rs:364）
- `CHUNK_BYTES` — 64 KiB 分块单位（core/crates/persistence/rescue/src/lib.rs:14）
- `MAX_FILES` — 归档文件数上限 500_000（core/crates/persistence/rescue/src/lib.rs:16）
- `MAX_METADATA_BYTES` — manifest 上限 16 MiB（core/crates/persistence/rescue/src/lib.rs:15）
- 主入口：`DataRescue::execute`（core/crates/persistence/rescue/src/lib.rs:100）
- 数据流向：Host 选定文件 → ZIP 归档（`manifest.json` + `payload/`）→ 验后暂存 → Host 发布（core/crates/persistence/rescue/src/lib.rs:232）

## 核心机制

### 离线分发

- `describe` 与 `export` 分别委托给 Host 与 `export()`（core/crates/persistence/rescue/src/lib.rs:102）
- `beginUpload` 生成新 UUID 作 `archiveId`，`byteLength` 必填，长度为 0 拒绝（core/crates/persistence/rescue/src/lib.rs:105）
- `uploadChunk` 对 `bytes` 做 STANDARD 解码，超过 64 KiB 的块拒绝（core/crates/persistence/rescue/src/lib.rs:112）
- `sealUpload` 封存归档后返回 `byteLength`（core/crates/persistence/rescue/src/lib.rs:117）
- `inspect` 检查归档并返回其清单，`restore` 按请求中的归档标识恢复归档（core/crates/persistence/rescue/src/lib.rs:118）
- `resumeRestore` 委托给 `host.resume_restore()`，`verifyFiles` 先解析 manifest 再校验（core/crates/persistence/rescue/src/lib.rs:120）
- `discardArchive` 删除指定归档；未知 `operation` 报错（core/crates/persistence/rescue/src/lib.rs:127）

### 导出

- `export` 先创建导出归档，失败时删除归档（core/crates/persistence/rescue/src/lib.rs:137)
- 导出先上报 `scan` 阶段，再列出文件并按 `path` 排序（core/crates/persistence/rescue/src/lib.rs:176）
- 导出 ZIP 条目用 Deflate 压缩（core/crates/persistence/rescue/src/lib.rs:184）
- 导出文件写入 `payload/<path>` 条目（core/crates/persistence/rescue/src/lib.rs:189）
- 有明文偏好时用明文替代源内容，并按明文重算 `byte_length` 与 `sha256`（core/crates/persistence/rescue/src/lib.rs:190）
- 导出分块读到短读时报错：源已变或被截断（core/crates/persistence/rescue/src/lib.rs:202）
- 导出后源文件多出 1 字节时报错：源在导出期间增长（core/crates/persistence/rescue/src/lib.rs:209）
- 导出 manifest 的 `format` 为 `operit.data-rescue`，`version` 为 1，`layout` 取 `host.layout()`，`metadata` 取 `host.describe()`（core/crates/persistence/rescue/src/lib.rs:216）
- manifest 序列化后超 16 MiB 拒绝导出（core/crates/persistence/rescue/src/lib.rs:222）
- `export` 返回 `archiveId`、`byteLength`、`fileReference`、`fileCount`（core/crates/persistence/rescue/src/lib.rs:232）
- `finalizeExport` 阶段共 3 个计项（core/crates/persistence/rescue/src/lib.rs:213）

### 检查

- `inspect` 先封存归档；条目数为 0 或超 `MAX_FILES + 1` 拒绝（core/crates/persistence/rescue/src/lib.rs:239）
- `inspect` 拒绝加密条目、重复条目、目录与符号链接条目（core/crates/persistence/rescue/src/lib.rs:246）
- `manifest.json` 超 16 MiB 时拒绝（core/crates/persistence/rescue/src/lib.rs:254）
- `inspect` 要求 `format` 为 `operit.data-rescue` 且 `version` 为 1（core/crates/persistence/rescue/src/lib.rs:260）
- `inspect` 要求 `layout` 与 `host.layout()` 一致（core/crates/persistence/rescue/src/lib.rs:263）
- 归档条目集合与 manifest 精确一致：`manifest.json` 加全部 `payload/<path>`（core/crates/persistence/rescue/src/lib.rs:266）
- 对每个 payload 逐条调用 `verify_payload` 验证（core/crates/persistence/rescue/src/lib.rs:271）

### 恢复

- `restore` 先 `inspect`，再建新 UUID 作 `restore_id`；`begin_restore` 失败时丢弃暂存（core/crates/persistence/rescue/src/lib.rs:281）
- `restore` 暂存失败时丢弃暂存，清理失败时把两段错误拼进返回（core/crates/persistence/rescue/src/lib.rs:290）
- `restore` 暂存全部文件后调用 `commit_restore` 发布（core/crates/persistence/rescue/src/lib.rs:293）
- `stage_restore` 每文件先验证 payload，再边验边写，写完调 `finish_restore_file`（core/crates/persistence/rescue/src/lib.rs:305）
- 中断的发布只由显式恢复推进：`resume_restore` 从 Host 维护日志恢复（core/crates/persistence/rescue/src/lib.rs:87）

### 校验与边界

- `validate_path` 拒绝空路径、超 4096 字节、含反斜杠、冒号或空字节、含空段、`.` 或 `..` 的路径（core/crates/persistence/rescue/src/lib.rs:317）
- `validate_files` 要求 `sha256` 为 64 位十六进制，拒绝重复路径与祖先重叠（core/crates/persistence/rescue/src/lib.rs:330）
- `validate_source_files` 只验路径合法与重复（core/crates/persistence/rescue/src/lib.rs:343）
- `validate_ancestors` 按 `/` 切分逐段查，祖先与子路径共存时拒绝（core/crates/persistence/rescue/src/lib.rs:354）
- `verify_payload` 用 `CHUNK_BYTES` 大小的缓冲流式读，累计用 `checked_add` 防溢出（core/crates/persistence/rescue/src/lib.rs:367）
- 累计超声明 `byte_length` 时拒绝；结束时总长与 `sha256` 一致（core/crates/persistence/rescue/src/lib.rs:372）
- `verify_storage_manifest` 要求 format、version、layout 三者一致，否则拒绝（core/crates/persistence/rescue/src/lib.rs:150）
- 校验暂存 payload 时短读报错：暂存 payload 被截断（core/crates/persistence/rescue/src/lib.rs:162）
- 校验时在文件末尾多读 1 字节，非空或哈希不符时报完整性失败（core/crates/persistence/rescue/src/lib.rs:167）
- `archiveId` 只接受能解析为 UUID 的标识（core/crates/persistence/rescue/src/lib.rs:389）
- 请求缺失字符串字段时报错（core/crates/persistence/rescue/src/lib.rs:384）

### 进度

- `RescueProgress` 只在对应工作成功后推进，并向 Host 上报（core/crates/persistence/rescue/src/lib.rs:33）
- `scan` 阶段上报文件枚举，`total` 未知，单位 `files`（core/crates/persistence/rescue/src/lib.rs:176）
- `export` 阶段按源字节计量（core/crates/persistence/rescue/src/lib.rs:185）
- `finalizeExport` 阶段共 3 个计项（core/crates/persistence/rescue/src/lib.rs:213）
- `readManifest` 阶段按归档条目数计量（core/crates/persistence/rescue/src/lib.rs:240）
- `verifyArchive` 阶段按 payload 总字节计量（core/crates/persistence/rescue/src/lib.rs:268）
- `verifyRestored` 阶段按 payload 总字节计量（core/crates/persistence/rescue/src/lib.rs:154）
- `restore` 阶段按 payload 总字节计量（core/crates/persistence/rescue/src/lib.rs:300）

### 归档 I/O

- `ArchiveIo` 把 Host 暂存适配为标准 ZIP 可寻址 I/O（core/crates/persistence/rescue/src/lib.rs:398）
- `ArchiveIo` 读按 `CHUNK_BYTES` 封顶，短读报暂存归档截断（core/crates/persistence/rescue/src/lib.rs:409）
- `ArchiveIo` 写按 `CHUNK_BYTES` 分块提交给 Host（core/crates/persistence/rescue/src/lib.rs:421）
- `ArchiveIo` 的 `flush` 是空操作，持久化交给归档封存（core/crates/persistence/rescue/src/lib.rs:429）
- `ArchiveIo` 的 `seek` 拒绝溢出与负向定位（core/crates/persistence/rescue/src/lib.rs:435）

### 测试

- 内置测试覆盖路径边界拒绝（core/crates/persistence/rescue/src/lib.rs:449）
- 内置测试覆盖无效 sha256 摘要拒绝（core/crates/persistence/rescue/src/lib.rs:462）
- 内置测试覆盖路径前缀碰撞拒绝（core/crates/persistence/rescue/src/lib.rs:468）

## 关键符号

- `DataRescue` — 离线救援执行器（core/crates/persistence/rescue/src/lib.rs:93）
- `RescueHost` — Host 存储契约（core/crates/persistence/rescue/src/lib.rs:65）
- `RescueManifest` — 归档清单（core/crates/persistence/rescue/src/lib.rs:56）
- `RescueFile` — 单个常规文件（core/crates/persistence/rescue/src/lib.rs:47）
- `RescueProgress` — 阶段进度计数器（core/crates/persistence/rescue/src/lib.rs:21）
- `ArchiveIo` — Host 暂存到 ZIP I/O 的适配器（core/crates/persistence/rescue/src/lib.rs:398）
- `CHUNK_BYTES` — 64 KiB 分块单位（core/crates/persistence/rescue/src/lib.rs:14）
- `MAX_METADATA_BYTES` — manifest 上限 16 MiB（core/crates/persistence/rescue/src/lib.rs:15）
- `MAX_FILES` — 归档文件数上限 500_000（core/crates/persistence/rescue/src/lib.rs:16）
- `payload_bytes` — `checked_add` 累加 payload 总字节（core/crates/persistence/rescue/src/lib.rs:40）
- `validate_path` — 路径边界校验（core/crates/persistence/rescue/src/lib.rs:316）
- `validate_files` — manifest 记录校验（core/crates/persistence/rescue/src/lib.rs:325）
- `validate_ancestors` — 祖先路径重叠校验（core/crates/persistence/rescue/src/lib.rs:352）
- `verify_payload` — payload 流式校验（core/crates/persistence/rescue/src/lib.rs:364）
- `archive_id` — 只接受 UUID 标识（core/crates/persistence/rescue/src/lib.rs:388）

## 调用链

### 导出

1. `execute` 收到 `operation` 为 `export` 的请求（core/crates/persistence/rescue/src/lib.rs:103）
2. `export` 生成新 UUID 并创建导出归档（core/crates/persistence/rescue/src/lib.rs:137）
3. `write_export` 上报 `scan`，列出文件并按 `path` 排序（core/crates/persistence/rescue/src/lib.rs:176）
4. 逐文件写入 `payload/<path>`，有明文偏好时用明文替代（core/crates/persistence/rescue/src/lib.rs:190）
5. 写 `manifest.json`，超 16 MiB 拒绝（core/crates/persistence/rescue/src/lib.rs:222）
6. 封存归档并返回 `archiveId`、`byteLength`、`fileReference`、`fileCount`（core/crates/persistence/rescue/src/lib.rs:232）

### 检查

1. `inspect` 先封存归档（core/crates/persistence/rescue/src/lib.rs:237）
2. 条目数为 0 或超 `MAX_FILES + 1` 时拒绝（core/crates/persistence/rescue/src/lib.rs:239）
3. 逐条目检查加密、重复、目录与符号链接（core/crates/persistence/rescue/src/lib.rs:246）
4. 读 `manifest.json` 并验 format、version、layout（core/crates/persistence/rescue/src/lib.rs:260）
5. 核对条目集合与 manifest 精确一致（core/crates/persistence/rescue/src/lib.rs:266）
6. 对每个 payload 逐条调用 `verify_payload` 验证（core/crates/persistence/rescue/src/lib.rs:271）

### 恢复

1. `execute` 收到 `restore`，先 `inspect` 归档（core/crates/persistence/rescue/src/lib.rs:119）
2. 建新 UUID 作 `restore_id` 并调 `begin_restore`（core/crates/persistence/rescue/src/lib.rs:281）
3. `stage_restore` 逐文件验证并写入隔离目的地（core/crates/persistence/rescue/src/lib.rs:305）
4. `commit_restore` 发布暂存导入（core/crates/persistence/rescue/src/lib.rs:293）

### 上传

1. `beginUpload` 生成 `archiveId` 并创建归档（core/crates/persistence/rescue/src/lib.rs:105）
2. `uploadChunk` 按 base64 块追加，每块不超 64 KiB（core/crates/persistence/rescue/src/lib.rs:112）
3. `sealUpload` 封存后返回 `byteLength`（core/crates/persistence/rescue/src/lib.rs:117）
4. `inspect` 或 `restore` 接手已封存归档（core/crates/persistence/rescue/src/lib.rs:118）

## 来源

- `core/crates/persistence/rescue/src/lib.rs` — 本页唯一 seed，470 行，已全读；全部事实引用均出自该文件。
- `docs/data-rescue.md` — 交叉引用：上游文档描述各平台入口与布局；本页事实以 lib.rs 为准，文档中的布局名与入口不在本 crate 内定义。
