# Changelog

本项目版本号遵循语义化版本。AGENTS.md 要求 `pyproject.toml` / `README.md` / `CHANGELOG.md` 版本号保持一致。

## [Unreleased]

### 工程化 / 防护
- 新增 `scripts/pre-commit` git 钩子，作为「配置同步」强约束的机械防线：若提交仅修改生成的 `.opencode/**`、`.workbuddy/**`（`.workbuddy/memory/**` 除外）而无 `.trae/**` 对应改动，则拒绝提交。`install.ps1` / `install.sh` 新增 [6/5] 步骤，自动将该钩子安装到 `.git/hooks/pre-commit`。

## [0.5.0] - 2026-08-02

### 文档 / 基线对齐
- 移除已废弃的 PaddleOCR 可选依赖说明：图片采集现由宿主 LLM 多模态直接解析，无需安装 OCR 引擎。安装脚本与文档中的 `uv sync --extra ocr` 引用一并清除。
- 部署与项目结构说明对齐实际 `.trae/` 目录（仅 `skills/`、`mcp.json`、`skill-config.json`），删除不存在的 `rules/`、`agents/`、`commands/`、`documents/`、`hooks.json`、`开发流程规范.md` 及 `BMAD` 相关描述。
- 安装脚本 `install.ps1` / `install.sh` 移除 `-InstallOcr` / `--install-ocr` 参数及 OCR 安装询问。
- `README.md` / `DEPLOY.md` / `QUICKSTART.md` 中的当前版本引用统一更新为 `0.5.0`。

### Notes
- `0.4.0` 未发布，本次自 `0.3.0` 直接跃迁至 `0.5.0`。
