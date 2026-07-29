# VocabCraft 项目长期记忆

## 项目定位
本地优先的词汇学习与记忆管理系统。`vocabcraft-mcp/` 是核心 Python 包（FastMCP stdio 服务 + FastAPI/HTMX Web UI），SM-2 遗忘曲线调度，数据全存本地 `data/`（JSON），无云端依赖。

## 双 IDE 扩展配置（重要）
本项目用 `.trae/` 文件夹承载 Trae 的扩展（agents/commands/skills/rules/mcp.json）。
WorkBuddy 不读 `.trae/`，需等价移植：

- **MCP**：已注册到 `~/.workbuddy/mcp.json`（server 名 `vocabcraft-mcp`），用绝对路径 `C:\Users\yecll\.local\bin\uv.exe run --directory D:/yecll/Documents/LocalCode/vocabcraft/vocabcraft-mcp vocabcraft-mcp` 启动。**需用户在连接器管理页面对其点击「Trust」才会激活。**
- **Skills**：5 个 `vocabcraft-*` skill 已从 `.trae/skills/` 复制到 `.workbuddy/skills/`（项目级），格式兼容（name+description 前置元信息）。`.trae/skills` 仍视为单一真相源，改动后需重新复制。
- **Commands（5）/ Agents（3）**：Trae 专属，无 1:1 机制；功能上已由 5 个 vocabcraft skill 覆盖（按任务描述触发）。
- **Rules（10 个 .md）**：Trae 会自动注入；WorkBuddy 无"始终自动注入项目规则"机制。关键约束已内联在各 SKILL.md 的「约束规则」段。真正全局性的约定见下。

## 始终生效的工程约定（来自 .trae/rules）
- **ponytail（最小可行）原则**：先交付骨架（如 parse 仅返回 prompt），后续迭代补全，不要一次堆全。
- **数据安全**：图片仅存本地 `data/images/`，禁止外传；OCR 失败降级为手动输入而非报错。
- **vocab_id 格式**：`vocab_YYYYMMDD_NNN`（NNN 当日递增）；quiz 以 `quiz_` 开头。
- **结构化 vs 记忆状态分离**：`StructuredVocab` 与 `ReviewState` 分离；`grade_quiz` 只 patch `review_state`，不触动用户确认的 `structured`。

## 备注
- `uv` 已安装（0.11.31）。`vocabcraft-mcp/.venv` 已存在，import 正常。
- README 对 `web/` 模块描述不足，实际项目比文档更丰富。
