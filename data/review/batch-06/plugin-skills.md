---
title: Skills 机制
module: plugins
platforms: [all]
sources: [core/crates/tool/services/src/tools/skill/SkillManager.rs, core/crates/tool/services/src/tools/skill/SkillPackage.rs, core/crates/tool/services/src/tools/skill/mod.rs, core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs, core/crates/tool/services/src/tools/skill_runtime/mod.rs]
date: 2026-11-11
---

## 概述

Skill 是以目录为单位的扩展包，一个 Skill 目录以 `SKILL.md` 为入口文件（`core/crates/tool/services/src/tools/skill/SkillManager.rs:156`）。
Skill 的载体是 `SKILL.md` 目录，`SkillPackage` 只记录 `name`、`description`、`directory`、`skillFile` 四个字段（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
Skill 是独立的扩展类型，不是 ToolPkg 插件的同义词（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
本页同时覆盖 Agent 回路的 Skills 主题，不再单立 agent-skills 页。
`SkillManager` 持有 `RuntimeStorePaths` 与 `FileSystemHost`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:17`）。
`SkillRepository` 是管理已安装与导入 Skill 的门面（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:13`）。

## AI 速览

- 核心符号：`SkillPackage` — 一个已安装 Skill 的记录，含名、描述、目录与 `SKILL.md` 路径（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
- 核心符号：`SkillManager` — 扫描、安装、删除 Skill 并生成激活提示的管理器（`core/crates/tool/services/src/tools/skill/SkillManager.rs:17`）。
- 核心符号：`SkillRepository` — 对外暴露 Skill 管理操作的仓库门面（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:13`）。
- 核心符号：`refreshAvailableSkills` — 扫描 device 与 space 两个位置并返回有效 Skill 与错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:52`）。
- 核心符号：`getSkillSystemPrompt` — 生成 Skill 激活时用的系统提示片段（`core/crates/tool/services/src/tools/skill/SkillManager.rs:397`）。
- 核心符号：`importBundledExternalSkill` — 安装一个随包外部 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:298`）。
- 核心符号：`importSkillFromGitHubRepo` — 从 GitHub 仓库下载 zip 导入 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:159`）。
- 核心符号：`importSkillFromDirectInput` — 用文本内容直接创建一个 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:199`）。
- 核心符号：`getAiVisibleSkillPackages` — 只返回对 AI 包激活可见的 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:86`）。
- 主入口函数：`SkillRepository` 的 `getInstance`（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:31`）。
- 数据流向一句话：Skill 目录经扫描成为 `SkillPackage`，激活时 `SKILL.md` 全文拼进系统提示片段交给 Agent 运行时（`core/crates/tool/services/src/tools/skill/SkillManager.rs:425`）。

## 核心机制

### Skill 的形态与元数据

Skill 目录的入口文件也可以是小写 `skill.md`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:157`）。
`SkillPackage` 的 `name` 字段保存 Skill 名（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:7`）。
`SkillPackage` 的 `description` 字段保存 Skill 描述（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:8`）。
`SkillPackage` 的 `directory` 字段保存 Skill 所在的目录路径（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:9`）。
`SkillPackage` 的 `skillFile` 字段保存 `SKILL.md` 文件路径（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:10`）。
内容首行是 `---` 时按行调用 `parseMetadataLine` 解析 frontmatter（`core/crates/tool/services/src/tools/skill/SkillManager.rs:614`）。
frontmatter 缺 `name` 或 `description` 时 `parseSkillMetadataContent` 回退扫描前 40 行（`core/crates/tool/services/src/tools/skill/SkillManager.rs:622`）。
`parseMetadataLine` 解析一行元数据并写入 `name` 或 `description`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:631`）。

### 扫描与安装位置

`SkillManager` 的 `getSkillsDirectoryPath` 返回用户已安装 Skill 的存放目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:45`）。
`SkillManager` 的 `getSkillsRootDir` 返回 `RuntimeStorePaths` 的 `skills_dir`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:587`）。
`SkillManager` 的 `refreshAvailableSkills` 扫描 `device` 与 `space` 两个位置（`core/crates/tool/services/src/tools/skill/SkillManager.rs:60`）。
`space` 位置的扫描按 `sharedSources` 过滤，未登记的目录被跳过（`core/crates/tool/services/src/tools/skill/SkillManager.rs:154`）。
扫描只处理 `isDirectory` 为真的子项（`core/crates/tool/services/src/tools/skill/SkillManager.rs:150`）。
缺少 `SKILL.md` 的目录记入 `Missing SKILL.md` 加载错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:181`）。
`SKILL.md` 元数据的 `name` 为空时 Skill 名回退为目录名（`core/crates/tool/services/src/tools/skill/SkillManager.rs:188`）。
同一位置内出现重名 Skill 时记入 `Duplicate scanned skill name` 加载错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:204`）。
同名 Skill 同时存在于 `device` 与 `space` 时 `refreshAvailableSkills` 报 `Skill ownership conflict` 且该 Skill 不可用（`core/crates/tool/services/src/tools/skill/SkillManager.rs:70`）。
`device` 位置的 Skill 扫描后调用 `ExtensionStore` 的 `registerDevice` 登记（`core/crates/tool/services/src/tools/skill/SkillManager.rs:81`）。
扫描后用 `ExtensionStore` 的 `record` 校验 Skill 记录的位置与来源名（`core/crates/tool/services/src/tools/skill/SkillManager.rs:88`）。
`SkillManager` 的 `getAvailableSkills` 返回当前已安装的全部有效 Skill 包（`core/crates/tool/services/src/tools/skill/SkillManager.rs:232`）。
`SkillManager` 的 `getAvailableSkillsSnapshot` 同时返回有效 Skill 包与加载错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:238`）。
`SkillManager` 的 `getSkillLoadErrors` 返回扫描 Skill 目录的加载错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:246`）。

### 打包、安装与按需导入

`SkillManager` 的 `getBundledExternalSkillCandidates` 列出尚未安装的随包外部 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:252`）。
随包 Skill 候选的描述取自其 `SKILL.md` 的元数据（`core/crates/tool/services/src/tools/skill/SkillManager.rs:279`）。
`importBundledExternalSkill` 在同名 Skill 已安装时拒绝导入（`core/crates/tool/services/src/tools/skill/SkillManager.rs:305`）。
`importBundledExternalSkill` 写入随包资产前调用 `clearBundledSkillFiles` 清空目标目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:339`）。
`importBundledExternalSkill` 用 `writeFileBytes` 把随包资产写入 Skill 目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:344`）。
`normalizeAssetRelativePath` 拒绝含非普通路径段的随包资产路径（`core/crates/tool/services/src/tools/skill/SkillManager.rs:660`）。
`importBundledExternalSkill` 导入后重新扫描，Skill 未加载则报错（`core/crates/tool/services/src/tools/skill/SkillManager.rs:363`）。
`importSkillArchiveBytes` 把 zip 字节解到以 `.import_tmp_` 开头的临时目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:457`）。
`importSkillArchiveBytes` 在导入完成后删除临时目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:473`）。
`importSkillArchiveBytesInner` 调用 `unzipBytesToDirectory` 解压 zip（`core/crates/tool/services/src/tools/skill/SkillManager.rs:486`）。
`unzipBytesToDirectory` 用 `enclosed_name` 校验 zip 条目，指向目标目录外的条目被拒绝（`core/crates/tool/services/src/tools/skill/SkillManager.rs:749`）。
zip 只有唯一子目录时 `singleChildDirectory` 返回该子目录作为解压根目录（`core/crates/tool/services/src/tools/skill/SkillManager.rs:495`）。
导入时调用 `findSkillFiles` 在包内递归查找 `SKILL.md`，最多找 10 个候选（`core/crates/tool/services/src/tools/skill/SkillManager.rs:514`）。
zip 内找不到 `SKILL.md` 时导入返回 `No SKILL.md found in the imported zip`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:520`）。
`importSkillArchiveBytesInner` 调用 `parseSkillMetadata` 解析导入 Skill 的元数据（`core/crates/tool/services/src/tools/skill/SkillManager.rs:530`）。
导入的 Skill 名优先取 `SKILL.md` 元数据的 `name`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:535`）。
元数据无 `name` 且解压根目录就是临时目录时导入的 Skill 名取 zip 文件名主干（`core/crates/tool/services/src/tools/skill/SkillManager.rs:538`）。
同名 Skill 已安装时 zip 导入返回 `Skill already exists in an installation location`（`core/crates/tool/services/src/tools/skill/SkillManager.rs:560`）。
zip 导入对非 `.zip` 文件返回 `Only .zip files are supported`（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:152`）。
`importSkillFromGitHubRepo` 从 GitHub 仓库下载 zip 导入 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:159`）。
`importSkillFromGitHubRepo` 未指定分支时调用 `getGithubDefaultBranch` 查询默认分支（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:166`）。
`importSkillFromGitHubRepo` 从 `codeload.github.com` 下载仓库 zip（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:178`）。
`parseGitHubSkillTarget` 解析 GitHub Skill 目标地址（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:388`）。
`parseGitHubSkillTarget` 接受 `raw.githubusercontent.com` 地址（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:447`）。
`importSkillFromDirectInput` 要求 Skill id 非空（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:211`）。
`isValidSkillId` 只接受字母、数字、点、下划线与连字符组成的 Skill id（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:336`）。
`importSkillFromDirectInput` 通过 `buildDirectSkillMarkdown` 生成带 `name` 与 `description` frontmatter 的 `SKILL.md`（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:315`）。
`importSkillFromDirectInput` 把附件复制到 Skill 目录下的 `assets` 子目录（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:288`）。
`importSkillFromDirectInput` 写入失败时删除已创建的 Skill 目录（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:259`）。
`SkillManager` 的 `deleteSkill` 调用 `ExtensionStore` 的 `delete` 注销 Skill 并返回布尔结果（`core/crates/tool/services/src/tools/skill/SkillManager.rs:433`）。

### PackageBuilder 随包 Skill

`PackageBuilder` 是随包 Skill 的名称（`core/crates/tool/services/src/tools/skill/SkillManager.rs:14`）。
`ensureQuickPluginCreatorBundledSkill` 在 `QUICK_PLUGIN_CREATOR_SKILL_NAME` 已安装时直接返回已安装的 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:372`）。
`ensureQuickPluginCreatorBundledSkill` 在该 Skill 未安装时调用 `importBundledExternalSkill` 导入（`core/crates/tool/services/src/tools/skill/SkillManager.rs:380`）。
`ensureQuickPluginCreatorSkillVisible` 在安装快速插件创建 Skill 后调用 `setSkillVisibleToAi` 将其设为可见（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:120`）。

### 与 Agent 运行时的交互

`SkillManager` 的 `readSkillContent` 读取一个已安装 Skill 的 `SKILL.md` 内容（`core/crates/tool/services/src/tools/skill/SkillManager.rs:387`）。
`SkillManager` 的 `getSkillSystemPrompt` 生成 Skill 激活时用的系统提示片段（`core/crates/tool/services/src/tools/skill/SkillManager.rs:397`）。
`getSkillSystemPrompt` 的提示以 `Using package (Skill):` 加 Skill 名开头（`core/crates/tool/services/src/tools/skill/SkillManager.rs:405`）。
`getSkillSystemPrompt` 的执行策略要求优先使用 Skill 提供的指令与随包脚本并用终端相关工具完成任务（`core/crates/tool/services/src/tools/skill/SkillManager.rs:408`）。
`getSkillSystemPrompt` 的提示包含 `SKILL.md` 路径（`core/crates/tool/services/src/tools/skill/SkillManager.rs:413`）。
`getSkillSystemPrompt` 的提示包含 Skill 目录结构文本（`core/crates/tool/services/src/tools/skill/SkillManager.rs:421`）。
`getSkillSystemPrompt` 的提示末尾附上 `SKILL.md` 全文（`core/crates/tool/services/src/tools/skill/SkillManager.rs:425`）。
`SkillRepository` 的 `getAiVisibleSkillPackages` 只返回对 AI 包激活可见的 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:86`）。
`SkillRepository` 的 `isSkillVisibleToAi` 查询一个 Skill 是否对 AI 包激活可见（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:108`）。
`SkillRepository` 的 `setSkillVisibleToAi` 设置一个 Skill 对 AI 包激活的可见性（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:114`）。
`SkillRepository` 的 `getInstance` 要求 `HostManager` 提供 `FileSystemHost`（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:31`）。

## 关键符号

- `SkillPackage` — 一个已安装 Skill 的记录（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
- `SkillManager` — 扫描、安装、删除 Skill 并生成激活提示的管理器（`core/crates/tool/services/src/tools/skill/SkillManager.rs:17`）。
- `SkillRepository` — 对外暴露 Skill 管理操作的仓库门面（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:13`）。
- `SkillManager` 的 `fromDefaultPaths` — 用默认运行时存储路径创建管理器（`core/crates/tool/services/src/tools/skill/SkillManager.rs:31`）。
- `SkillManager` 的 `refreshAvailableSkills` — 扫描 `device` 与 `space` 两个位置并返回有效 Skill 与错误（`core/crates/tool/services/src/tools/skill/SkillManager.rs:52`）。
- `SkillManager` 的 `getAvailableSkills` — 返回当前已安装的全部有效 Skill 包（`core/crates/tool/services/src/tools/skill/SkillManager.rs:232`）。
- `SkillManager` 的 `getSkillSystemPrompt` — 生成 Skill 激活时用的系统提示片段（`core/crates/tool/services/src/tools/skill/SkillManager.rs:397`）。
- `SkillManager` 的 `importBundledExternalSkill` — 安装一个随包外部 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:298`）。
- `SkillManager` 的 `importSkillArchiveBytes` — 从 zip 字节导入 Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:445`）。
- `SkillManager` 的 `ensureQuickPluginCreatorBundledSkill` — 安装随包的 `PackageBuilder` Skill（`core/crates/tool/services/src/tools/skill/SkillManager.rs:372`）。
- `SkillRepository` 的 `getAiVisibleSkillPackages` — 只返回对 AI 包激活可见的 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:86`）。
- `SkillRepository` 的 `importSkillFromGitHubRepo` — 从 GitHub 仓库下载 zip 导入 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:159`）。
- `SkillRepository` 的 `importSkillFromDirectInput` — 用文本内容直接创建一个 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:199`）。
- `QUICK_PLUGIN_CREATOR_SKILL_NAME` — 值为 `PackageBuilder` 的随包 Skill 名常量（`core/crates/tool/services/src/tools/skill/SkillManager.rs:14`）。

## 调用链

1. `SkillRepository` 的 `getInstance` 用 `HostManager` 的 `FileSystemHost` 创建 `SkillManager`（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:31`）。
2. `SkillManager` 的 `refreshAvailableSkills` 扫描 `device` 与 `space` 两个位置（`core/crates/tool/services/src/tools/skill/SkillManager.rs:60`）。
3. `scanSkillsDirectory` 在每个子目录里找 `SKILL.md` 并调用 `parseSkillMetadata` 解析元数据（`core/crates/tool/services/src/tools/skill/SkillManager.rs:186`）。
4. 解析出的 `name` 与 `description` 连同目录与 `SKILL.md` 路径装进 `SkillPackage`（`core/crates/tool/services/src/tools/skill/SkillPackage.rs:6`）。
5. 随包安装时 `importBundledExternalSkill` 把资产写入 Skill 目录后重新扫描确认加载（`core/crates/tool/services/src/tools/skill/SkillManager.rs:363`）。
6. zip 导入时 `importSkillArchiveBytesInner` 调用 `findSkillFiles` 在包内递归查找 `SKILL.md`，最多找 10 个候选（`core/crates/tool/services/src/tools/skill/SkillManager.rs:514`）。
7. GitHub 导入时 `importSkillFromGitHubRepo` 从 `codeload.github.com` 下载仓库 zip 再走 zip 导入（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:178`）。
8. 激活时 `getSkillSystemPrompt` 把 `SKILL.md` 全文、目录结构与执行策略拼进系统提示片段（`core/crates/tool/services/src/tools/skill/SkillManager.rs:425`）。
9. `getAiVisibleSkillPackages` 按 `isSkillVisibleToAi` 过滤出对 AI 包激活可见的 Skill（`core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs:86`）。

## 来源

- core/crates/tool/services/src/tools/skill/SkillManager.rs
- core/crates/tool/services/src/tools/skill/SkillPackage.rs
- core/crates/tool/services/src/tools/skill/mod.rs
- core/crates/tool/services/src/tools/skill_runtime/SkillRepository.rs
- core/crates/tool/services/src/tools/skill_runtime/mod.rs
