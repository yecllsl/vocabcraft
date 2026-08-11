# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### 新增个人级 Harness：WorkBuddy / Hermes
- WorkBuddy 与 Hermes 属于**仅支持个人级配置**的 Agent Runtime，无法通过项目级 `.agents/` 统一配置体系（单向同步到 `.trae/` / `.opencode/` / `.codebuddy/` / `.goose/`）管理，因此不纳入同步生成，亦不在 `scripts/pre-commit` 拦截名单中。
- 项目根目录新增 `.workbuddy/` 与 `.hermes/` 目录，各自仅含一份 `README.md`，说明如何为个人级 harness 加载配置：配置文件存放路径、MCP stdio 格式要求、符号链接加载机制，以及与现有配置体系的兼容性。
- `install.*` 增加 `workbuddy` / `hermes` 运行时选项：检测对应可执行文件 → 解析个人配置目录（`~/.workbuddy` / `~/.hermes`，Windows 为 `%USERPROFILE%\.workbuddy` 等）→ 写入绝对路径 `mcp.json` → 为 `AGENTS.md` 与 `skills/` 建立符号链接（失败降级复制）→ 提示验证。
- `build-release.*` 打包清单新增 `.workbuddy/README.md` 与 `.hermes/README.md`，便于发布包内用户查阅个人级配置说明。

### Runtime 重命名：WorkBuddy → CodeBuddy
- 项目面向的是腾讯 **CodeBuddy**（AI 代码编辑器），因此将生成目录由 `.workbuddy/` 改为 `.codebuddy/`，与 CodeBuddy 的配置目录约定一致。
- `.agents/runtime/workbuddy.json` → `codebuddy.json`；`scripts/sync-agent-configs.*`、`generate-platform-configs.py`、`install.*`、`.git/hooks/pre-commit` 的目标运行时由 workbuddy 改为 codebuddy。
- 修正先前对 OpenCode 的误判：`.opencode/opencode.json` 是 OpenCode 官方支持的（且优先级更高）的项目配置位置，配置本身有效。

### 新增 Agent Runtime：Goose (AAIF)
- 根目录新增 `.goose/` 目录，由 AAIF 配置层单向同步生成（Goose 为 Block 开源 Agent 运行时）。
- 新增 `.agents/runtime/goose.json`（Goose 原生 `extensions`/`stdio` schema）；新增 `scripts/generate-goose-config.py` 将其转换为 `.goose/config.yaml`，并把 `uv --directory` 解析为绝对项目路径（无需 `${workspaceFolder}`）。
- `scripts/sync-agent-configs.*` 增加 `--skip-goose` / `-SkipGoose`，同步 Skills 与 `AGENTS.md` 到 `.goose/`。
- `scripts/pre-commit` 生成目录拦截名单新增 `.goose/*`。
- `install.*` 增加 `goose` 运行时选项；`README.md` / `QUICKSTART.md` / `DEPLOY.md` 增加 Goose 配置说明与运行时计数更新。

### 文档清理：移除遗留 WorkBuddy 引用
- 清理 `.workbuddy/` / `WorkBuddy` 过时引用（`WorkBuddy` 此前已重命名为 `CodeBuddy`，项目实际仅生成 `.codebuddy/`）：同步修正 `.agents/AGENTS.md`、`AGENTS.md`、`README.md`、`DEPLOY.md`、`scripts/pre-commit`、`install.*` 中的生成目录列表、pre-commit 拦截名单与安装提示文案。

## [0.5.4] - 2026-08-09

### AAIF Migration
- 配置真相源由 `.trae/` 迁移到 AAIF 标准目录 `.agents/`（含 `runtime/`、`skills/`、`AGENTS.md`、`tools.json`、`triggers.json`、`workflows.json`）。
- `scripts/sync-agent-configs` 改为以 `.agents/` 为唯一来源，单向同步到 `.trae/` / `.opencode/` / `.workbuddy/` 三平台目录（含 `AGENTS.md`、Skills、runtime 配置）。
- `scripts/generate-platform-configs.js` 重写为 Python `scripts/generate-platform-configs.py`（与项目 Python 技术栈统一）；`package.json` 的 `generate-configs` / `sync-configs` 同步更新。
- `scripts/pre-commit` 机械防线扩展为拦截 `.trae/` / `.opencode/` / `.workbuddy/` 全部生成目录的直接编辑，要求改动先落在 `.agents/`。
- `install.*` 的 FixPath 路径修复改以 `.agents/runtime/` 为对象并重新同步；`build-release.*` 打包源改为 `.agents/skills/` 与 `.agents/AGENTS.md`。
- `.agents/tools.json` 工具名对齐真实 MCP 工具（`grade_quiz` / `export_data`），并补全 `update_vocab` / `delete_vocab` / `import_xlsx_vocab`。
- 版本号统一至 0.5.4（package.json / install.* / README.md / DEPLOY.md / QUICKSTART.md / CHANGELOG）。

## [0.5.2] - 2026-08-07

### Quality / Compliance
- 引入 ruff 严格集（E,F,W,I,N,UP,B,SIM）并清零；`scripts/` 下 `import_xlsx.py` 一并修复（F401/E501/E741/W292/B905）。
- 接入 mypy 类型检查（项目源码零错误）。
- 接入 bandit 安全扫描：B704（Markup 已逐片段 escape）、B110（导入失败仅上报不放大）、B311（random 仅出题/抽样）经审查后集中豁免；B104（绑定 0.0.0.0）保留为本地工具预期行为，地址可由 `VOCABCRAFT_WEB_HOST` 覆盖。
- CI（`test.yml`）新增 `quality-gates` job 运行 ruff / mypy / bandit；单元测试增加 `--cov-fail-under=80` 覆盖率门槛。
- `ruff` / `mypy` / `bandit` 加入 `dev` 可选依赖。

### Behavior
- 评分改为四级制 **4/3/2/1**（4 完全记住 / 3 勉强记住 / 2 部分错 / 1 几乎忘），替代原 5/3/2/0 与 5/0 混合尺度；客观题答对=4、答错=1，zh_classical 释义题按词性+释义维度评 4/3/2/1，主观释义题 LLM 评分范围同步改为 1-4。grade<3 仍视为失败并重置复习周期（与 SM-2 边界一致）。
- `/stats` 维度文档对齐实现（`language`/`mastery`/`date`/`quiz_type`），移除未实现的 `overview`/`review`。
- 五个 Skill 的约束规则去重，仅保留 Prompt 防御红线，其余引用 `AGENTS.md` 为唯一真相源。

## [0.5.1] - 2026-08-04

- Fix null handling in multi-language part-of-speech import
- Optimize filtering logic for word example sentences
- Fix empty result issue in Classical Chinese question generation
- Documentation updates: Added 0.5.1 update content

## [0.5.0] - 2026-08-02

### Documentation / Baseline Alignment
- Remove deprecated PaddleOCR optional dependency notice - image collection now uses host LLM's multimodal parsing, no OCR engine installation required. Install scripts and documentation references to `uv sync --extra ocr` have been cleaned up.
- Deployment and project structure documentation aligned with actual `.trae/` directory (only `skills/`, `mcp.json`, `skill-config.json`). Removed non-existent `rules/`, `agents/`, `commands/`, `documents/`, `hooks.json`, `BMAD` descriptions.
- Install scripts remove `-InstallOcr` / `--install-ocr` parameters and OCR installation prompts.
- `README.md` / `DEPLOY.md` / `QUICKSTART.md` version references updated to `0.5.1`.