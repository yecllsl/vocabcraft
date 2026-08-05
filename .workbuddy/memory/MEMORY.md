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
- **采集合并约定（用户明确）**：同词多例句时，语义相同的释义只存**一条** `Definition`，其全部例句聚合进该条 `examples` 列表；不要因为"例句多"就把同义项拆成多条 definition。用户对"不要合并精简"的指令本意是保留同义多条释义（如"回头"与"回头看"可并存），而非把每个例句拆成独立释义项。2026-08-05 顾/观/归/国/过 5 词即按此合并（过由 14 义项合并为 9）。

## 调度算法实际实现（2026-07-30 核查）
- 真正驱动排程的是 `src/vocabcraft_mcp/algorithms.py` 的改良版 SM-2（`compute_next_review`：EF 初始 2.5/下限 1.3；通过走 1→6→×EF；失败 reps 归零、间隔=1 天）。
- ⚠️ **三套不一致的间隔定义**：①`INITIAL_INTERVALS_DAYS=[1,2,4,7,15]`（真正用于新词初始排程）；②`resources/forgetting_curve.json` 的 20min/1h/9h/1d/2d/6d/31d（**完全未被任何代码读取的死配置**，既不被算法用、也不被 Web 用；注释还引用了不存在的 `algorithms.ebbinghaus_schedule`）；③标准 SM-2 的 1天/6天/×EF。
- AGENTS.md 写"遗忘曲线参数取自 forgetting_curve.json"不准确，该 json 只是展示用。
- `algorithms.py` docstring 第 8 行称"grade 3 同 0-2 视为失败"，但代码 `if grade < 3` 实际把 3 当通过（标准 SM-2 中 3=勉强记住=通过，代码正确、注释错误）。
- 对比 Anki：现行默认是 FSRS（机器学习、个性化、可设目标保留率），老版/早期默认是 SM-2 变体。结论：SM-2 够用省心；FSRS 数据越多越强、长期效率更优。VocabCraft 走本地极简路线，SM-2 契合 ponytail 原则。

## 备注
- `uv` 已安装（0.11.31）。`vocabcraft-mcp/.venv` 已存在，import 正常。
- README 对 `web/` 模块描述不足，实际项目比文档更丰富。
- `vocabcraft-stats` skill 文档已修正（移除服务端不支持的 overview/review 维度，改为 date/language/mastery/quiz_type）。
