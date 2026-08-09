# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.5.4] - 2026-08-09

### AAIF Migration
- 配置真相源由 `.trae/` 迁移到 AAIF 标准目录 `.agents/`（含 `runtime/`、`skills/`、`AGENTS.md`、`tools.json`、`triggers.json`、`workflows.json`）。
- `scripts/sync-agent-configs` 改为以 `.agents/` 为唯一来源，单向同步到 `.trae/` / `.opencode/` / `.workbuddy/` / `.hermes/` 四平台目录（含 `AGENTS.md`、Skills、runtime 配置）。
- `scripts/generate-platform-configs.js` 重写为 Python `scripts/generate-platform-configs.py`（与项目 Python 技术栈统一）；`package.json` 的 `generate-configs` / `sync-configs` 同步更新。
- `scripts/pre-commit` 机械防线扩展为拦截 `.trae/` / `.opencode/` / `.workbuddy/` / `.hermes/` 全部生成目录的直接编辑，要求改动先落在 `.agents/`。
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