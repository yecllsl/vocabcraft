# VocabCraft 长期记忆

## 配置策略决策（2026-08-13）
- `.agents/` 下的 `tools.json` / `triggers.json` / `workflows.json` 是 **AAIF 标准声明文件**，由 `scripts/generate-aaif-declarations.py` 从真实源生成（tools←MCP server 自省，triggers/workflows←Skills），**勿手工编辑**。
- 生成依赖 uv 环境（`uv run --no-sync --directory vocabcraft-mcp python scripts/generate-aaif-declarations.py`）。
- 它们由 AAIF 工具链 `agents publish .agents` 消费，是 AAIF 包格式合规要求，非运行时直接读取。
- 用户已确认走 AAIF 合规路线（保留而非删除这三个文件）。
