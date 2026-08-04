# Changelog

All notable changes to this project will be documented in this file.

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