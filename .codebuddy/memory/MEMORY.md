# VocabCraft 长期记忆

## 配置策略决策（2026-08-13，2026-08-17 更新）
- `vocabcraft.plugin/` 下的 `tools.json` / `triggers.json` / `workflows.json` 是 **AAIF 标准声明文件**（原 `.agents/` 已重命名为 `vocabcraft.plugin/`），由 `scripts/generate-aaif-declarations.py` 从真实源生成（tools←MCP server 自省，triggers/workflows←Skills），**勿手工编辑**。
- 生成依赖 uv 环境（sync 脚本：`uv run --no-sync --directory vocabcraft.plugin/vocabcraft-mcp python scripts/generate-aaif-declarations.py`）。
- 它们由 AAIF 工具链 `agents publish vocabcraft.plugin` 消费，是 AAIF 包格式合规要求，非运行时直接读取。
- 用户已确认走 AAIF 合规路线（保留而非删除这三个文件）。

## Harness 两层支持策略（2026-09-27/28 落地，随 v0.8.0 发布）
- **Tier 1 = Agent Plugins 1.0**（`vocabcraft.plugin/`：`plugin.json` + `mcp.json` + `skills/`）。规范 v1.0.0（2026-08-06），首发采纳方 **Vercel + AWS + Anysphere(Cursor) + GitHub + Microsoft + OpenAI**。代表客户端 **VS Code / Copilot**。该规范**不携带 AGENTS.md/rules**。
- **Tier 2 = 原生目录 + install 脚本**：**Trae / CodeBuddy / OpenCode**；CodeBuddy 另有本地插件市场（根 `.codebuddy-plugin/marketplace.json`，CodeBuddy 自有格式）。
- **不支持**：WorkBuddy、Hermes（用户级）、**Goose（已移除）**。
- **已实测交付**：Tier 1 用 VS Code **Agents Window → 插件 → Install from Source**（指向 `vocabcraft.plugin/`，识别为 5 skills + 1 MCP server）；Tier 2 用 CodeBuddy **插件管理 → 插件市场 → 添加本地市场**（市场 `vocabcraft-local-market`，插件 `vocabcraft`）。步骤见 `DEPLOY.md`「手动 E2E 验收（Tier 1 / Tier 2）」。
- **OpenCode 澄清**：有 JS/TS **hook 插件**机制（`.opencode/plugin/` 或 npm 包）——那是运行时**行为扩展**，非 Agent Plugins 1.0 打包；**OpenCode 未采纳 Agent Plugins 1.0**。其 MCP 走 `opencode.json` 的 `mcp` 字段、skills 走 `.opencode/skills/`（本项目由 `sync-agent-configs` 同步）。→ OpenCode 不能「以插件方式」装 MCP+skills，只能走原生目录（Tier 2）。**已核实（opencode.ai/docs/skills，2026-09-26 更新）**：目录确为复数 `skills`，`SKILL.md` 需 YAML frontmatter（`name` 必填且须与目录名一致、匹配 `^[a-z0-9]+(-[a-z0-9]+)*$`；`description` 必填）——本项目 5 个 skill 均合规。
- **Trae 澄清**：**未采纳 Agent Plugins 1.0**；其「插件市场」是 IDE 扩展市场，与 agent plugin 无关。Trae 装 MCP+skills 走原生机制（MCP 市场 / `.trae/mcp.json`、`.trae/skills/`，本项目已同步）→ 即 Tier 2。
