---
title: 贡献指南
module: dev
platforms: [all]
sources: 3
date: 2026-11-11
---

## 概述

- 本页讲向 Operit2 提交改动的规则，seed 文件是 CONTRIBUTING.md。`CONTRIBUTING.md:3`
- Operit2 仓库同时包含 Rust 核心、各平台 host、CLI、Flutter 应用和构建工具。`CONTRIBUTING.md:3`
- 提交改动前须确认改动属于本仓库的维护范围，并保留与现有架构一致的实现方式。`CONTRIBUTING.md:3`
- 开始之前须先阅读 `README.md`，该文件说明项目定位、CLI 用法和常用检查命令。`CONTRIBUTING.md:9`
- 开始之前须先阅读 `BUILDING.md`，该文件说明完整的构建环境和平台工具链要求。`CONTRIBUTING.md:10`
- 项目采用 GNU Affero General Public License v3.0，见 `LICENSE` 文件。`CONTRIBUTING.md:11`
- 提交安全问题时不要公开创建 Issue 或 PR，通过仓库维护者公布的私下渠道联系维护者。`CONTRIBUTING.md:14`
- 构建环境细节见 [[dev-building|构建指南]]。`CONTRIBUTING.md:10`

## AI 速览

- 核心文档：CONTRIBUTING.md — 贡献的改动范围、本地检查、分支提交、PR 流程、许可与行为规范。`CONTRIBUTING.md:1`
- 核心机制：`CLA` — 当前流程不再要求每个提交包含 DCO 的 `Signed-off-by` 行，首次贡献按 CLA.md 在 PR 中发表独立的同意评论。`CONTRIBUTING.md:57` `CONTRIBUTING.md:83`
- 核心符号：`CLA` — 首次贡献的签署方式：在 PR 中发表独立的同意评论，明确协议版本、协议文本提交 SHA 和贡献范围。`CONTRIBUTING.md:57`
- 核心格式：`type(scope): summary` — 提交信息推荐格式，例如 `fix(cli): preserve chat attachments`。`CONTRIBUTING.md:55`
- 核心许可：`CLA` — 贡献者许可协议，贡献者保留版权并授予维护者再许可权利，维护者可按 AGPL-3.0、其他开源许可证或专有商业许可证再许可。`CONTRIBUTING.md:74`
- 核心模板：.github/pull_request_template.md — PR 模板，含改动类型、影响范围、验证与提交者确认。`.github/pull_request_template.md:5`
- 主入口：从最新的默认分支创建主题分支，每个分支聚焦一个问题。`CONTRIBUTING.md:54`
- 数据流向：从最新默认分支创建主题分支开始，完整流程见 ## 调用链。`CONTRIBUTING.md:54`

## 核心机制

### 改动范围

- 保持 host 兼容层和 Rust runtime 的边界，不在 Rust 或 Dart 中添加仅为某个平台服务的分支。`CONTRIBUTING.md:18`
- 复用已有的 host API、运行时抽象和平台适配层，避免在 Flutter 侧重复实现文件系统或 HTTP 能力。`CONTRIBUTING.md:19`
- 修改行为时同步更新相邻文档、测试和用户可见的错误信息。`CONTRIBUTING.md:20`
- 第三方代码、生成文件和资源必须保留其原始许可证与版权声明，并在 PR 中注明来源。`CONTRIBUTING.md:21`
- 不提交 API 密钥、访问令牌、签名文件、个人数据或本地构建产物。`CONTRIBUTING.md:22`

### 本地检查

- 根据改动范围运行相关检查，并在 PR 描述中记录实际运行过的命令及结果。`CONTRIBUTING.md:26`
- Rust CLI 检查命令为 `cargo check --manifest-path apps/cli/Cargo.toml`。`CONTRIBUTING.md:37`
- Rust CLI 检查命令包括 `cargo run --manifest-path apps/cli/Cargo.toml --bin operit2 -- cli version`。`CONTRIBUTING.md:38`
- Flutter 应用检查先进入 `apps/flutter/app`，即 `Set-Location apps/flutter/app`。`CONTRIBUTING.md:44`
- Flutter 应用检查命令包括 `fvm flutter pub get --enforce-lockfile`。`CONTRIBUTING.md:45`
- Flutter 应用检查命令包括 `fvm flutter analyze`。`CONTRIBUTING.md:46`
- Flutter 应用检查命令包括 `fvm flutter test`。`CONTRIBUTING.md:47`
- Rust 或 Flutter bridge 改动也应按照 `BUILDING.md` 中对应平台章节执行检查。`CONTRIBUTING.md:50`
- 涉及构建脚本、发布工具或 Web runtime 的改动，运行对应目录已有的 smoke test 或验证脚本。`CONTRIBUTING.md:50`

### 分支与提交

- 从最新的默认分支创建主题分支，每个分支聚焦一个问题。`CONTRIBUTING.md:54`
- 提交信息使用简短、祈使语气的英文主题，推荐采用 `type(scope): summary` 格式，例如 `fix(cli): preserve chat attachments`。`CONTRIBUTING.md:55`
- 将格式化、重命名和功能改动分开提交，便于审查。`CONTRIBUTING.md:56`
- 当前流程不再要求每个提交包含 DCO 的 `Signed-off-by` 行。`CONTRIBUTING.md:83`
- 首次贡献时，按照 `CLA.md` 的签署步骤，在 PR 中发表独立的同意评论，并明确协议版本、协议文本提交 SHA 和贡献范围。`CONTRIBUTING.md:57`

### PR 流程

- PR 标题应当说明改动结果而不是实现过程。`CONTRIBUTING.md:63`
- PR 应当描述问题、解决方案、影响范围和验证结果。`CONTRIBUTING.md:64`
- PR 应当列出涉及的平台；跨平台能力应说明 host API 和 Flutter/Rust 边界是否变化。`CONTRIBUTING.md:65`
- 为用户可见的行为变化，PR 应当附上截图、日志或复现步骤。`CONTRIBUTING.md:66`
- PR 应当说明迁移、配置、数据库或兼容性影响。`CONTRIBUTING.md:67`
- PR 应当确认每位贡献者均已完成 CLA 签署，在 PR 描述中附上签署评论链接，并完成 PR 模板中的检查项。`CONTRIBUTING.md:68`
- 维护者审查关注正确性、跨平台一致性、数据安全、许可证合规性和测试覆盖。`CONTRIBUTING.md:70`
- 审查意见处理完毕后，维护者会合并或要求继续修改；提交 PR 不代表改动一定会被接受。`CONTRIBUTING.md:70`
- PR 模板的改动类型复选包括 Bug 修复、新功能、重构或性能改进、文档或构建工具、第三方依赖或许可证更新。`.github/pull_request_template.md:7`
- PR 模板的影响范围一节要求列出受影响的平台和模块。`.github/pull_request_template.md:17`
- PR 模板的验证一节要求列出实际运行过的命令及结果，没有运行的检查须明确说明原因。`.github/pull_request_template.md:22`

### 贡献许可与 CLA

- 本项目要求贡献者签署 Operit2 贡献者许可协议（`CLA`）；贡献者保留自己原创贡献的版权，并授予项目维护者协议约定的版权及专利许可，维护者可按 AGPL-3.0、其他开源许可证或专有商业许可证再许可。`CONTRIBUTING.md:74`
- 项目不要求贡献者转让版权。`CONTRIBUTING.md:74`
- 签署时确认提交者有权提交该内容，或已获得必要授权。`CONTRIBUTING.md:78`
- 签署时确认能够授予 CLA 中约定的权利，涉及雇主或组织权利时已取得必要授权。`CONTRIBUTING.md:79`
- 签署时确认理解贡献及签署记录会成为项目公开历史的一部分。`CONTRIBUTING.md:81`
- CLA 的完整文本见仓库根目录 `CLA.md`，包含再许可、商业授权及签署方式。`CONTRIBUTING.md:12`
- 第三方代码仍受其原始许可证约束。`CONTRIBUTING.md:83`
- PR 模板的提交者确认要求确认已阅读 `CONTRIBUTING.md`。`.github/pull_request_template.md:41`
- PR 模板的提交者确认要求已按 `CLA.md` 流程签署协议，或提供了覆盖本次贡献的既有签署记录；所有共同贡献者均有相应签署记录。`.github/pull_request_template.md:42`
- PR 模板的提交者确认要求确认拥有本次提交内容的版权或必要授权。`.github/pull_request_template.md:43`
- PR 模板的提交者确认要求确认已保留第三方代码、资源及其许可证和版权声明。`.github/pull_request_template.md:44`
- PR 模板的提交者确认要求确认没有提交密钥、令牌、个人数据或本地构建产物。`.github/pull_request_template.md:45`
- PR 模板的提交者确认要求确认已更新受影响的文档和测试，或在上文说明了原因。`.github/pull_request_template.md:46`

### 商业化与行为规范

- 项目目前由个人维护。`CONTRIBUTING.md:87`
- 商业化说明列出的收费服务范围包括托管、部署、技术支持、定制开发、咨询、培训、企业集成及其他商业服务。`CONTRIBUTING.md:87`
- 仓库当前公开版本使用 AGPL-3.0，接收者仍须按照其所取得版本的许可证履行义务；发布 CLA 不会撤销已发布副本的 AGPL-3.0 许可，也不会使整个仓库自动具备闭源发行条件。`CONTRIBUTING.md:89`
- 对维护者自行拥有版权或已通过 CLA 等方式取得充分再许可权利的内容，维护者可以另行提供商业许可；涉及第三方或历史贡献时，必须逐项满足其许可要求或取得必要授权。`CONTRIBUTING.md:89`
- 项目未来成立公司或由其他运营主体承接时，维护者可以按 CLA 的约定向项目承接方转让所获权利及相应义务或授予再许可；贡献者的版权仍归贡献者，超出既有授权范围的使用仍需要取得相应权利人的同意。`CONTRIBUTING.md:91`
- 讨论和审查应当聚焦技术事实，尊重不同背景的参与者。`CONTRIBUTING.md:95`
- 行为规范禁止人身攻击、骚扰、歧视性言论、恶意披露个人信息以及故意提交破坏性内容。`CONTRIBUTING.md:95`
- 维护者可以关闭不符合本指南或行为规范的讨论与贡献。`CONTRIBUTING.md:95`

## 关键符号

- CONTRIBUTING.md — 贡献指南全文，95 行，定义改动范围、检查、分支提交、PR、许可与行为规范。`CONTRIBUTING.md:1`
- `CLA` — Operit2 贡献者许可协议；当前流程不再要求每个提交包含 DCO 的 `Signed-off-by` 行。`CONTRIBUTING.md:83`
- `CLA` — 首次贡献的签署方式：在 PR 中发表独立的同意评论，明确协议版本、协议文本提交 SHA 和贡献范围。`CONTRIBUTING.md:57`
- `type(scope): summary` — 提交信息推荐格式，例如 `fix(cli): preserve chat attachments`。`CONTRIBUTING.md:55`
- `AGPL-3.0` — 项目许可证，CONTRIBUTING.md 声明项目采用 GNU Affero General Public License v3.0。`CONTRIBUTING.md:11` `CONTRIBUTING.md:74`
- `cargo check --manifest-path apps/cli/Cargo.toml` — Rust CLI 的本地检查命令。`CONTRIBUTING.md:37`
- `fvm flutter analyze` — Flutter 应用的静态分析检查命令。`CONTRIBUTING.md:46`
- `fvm flutter test` — Flutter 应用的测试检查命令。`CONTRIBUTING.md:47`
- .github/pull_request_template.md — PR 模板，定义改动类型、影响范围、验证与提交者确认检查项。`.github/pull_request_template.md:38`

## 调用链

1. 阅读 `README.md`、`BUILDING.md`、`LICENSE` 三份前置文档。`CONTRIBUTING.md:9`
2. 确认改动属于本仓库的维护范围，并保留与现有架构一致的实现方式。`CONTRIBUTING.md:3`
3. 从最新的默认分支创建主题分支，每个分支聚焦一个问题。`CONTRIBUTING.md:54`
4. 按改动范围运行相关本地检查：Rust CLI 用 `cargo check` 与 cargo run --bin operit2 -- cli version。`CONTRIBUTING.md:37`
5. Flutter 应用检查先进入 `apps/flutter/app`，再运行 `fvm flutter pub get --enforce-lockfile`、`fvm flutter analyze`、`fvm flutter test`。`CONTRIBUTING.md:45`
6. 将格式化、重命名和功能改动分开提交，便于审查。`CONTRIBUTING.md:56`
7. 创建 PR：标题说明改动结果，描述问题、解决方案、影响范围和验证结果，列出涉及的平台，完成 PR 模板中的检查项。`CONTRIBUTING.md:63`
8. 维护者审查正确性、跨平台一致性、数据安全、许可证合规性和测试覆盖，审查意见处理完毕后合并或要求继续修改。`CONTRIBUTING.md:70`

## 来源

- CONTRIBUTING.md（95 行，全文已读）：贡献指南全文，本页全部事实的来源。`CONTRIBUTING.md:1`
- .github/pull_request_template.md（50 行，全文已读）：PR 模板，改动类型、影响范围、验证与提交者确认检查项的来源。`.github/pull_request_template.md:5`
- `LICENSE`（首行已核验）：`LICENSE` 文件首行标明 GNU AFFERO GENERAL PUBLIC LICENSE Version 3，与 CONTRIBUTING.md 的 AGPL-3.0 声明一致。`LICENSE:1`
- 本页事实全部来自上述三个文件在基线 AAswordman/Operit2 @ ff5373fb6 上的内容；`README.md` 与 `BUILDING.md` 仅在 CONTRIBUTING.md 的引用处出现，未展开引用其正文。`CONTRIBUTING.md:9`
