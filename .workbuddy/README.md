# WorkBuddy 配置说明（个人级）

> 本目录**仅存放这一份说明文档**，不存放由 `sync-agent-configs` 生成的配置。
> WorkBuddy 属于**仅支持个人级配置**的 Agent Runtime，无法通过项目级 `.agents/` 统一配置体系管理。

## 为什么这里只有一个 README

VocabCraft 的统一配置真相源是 `.agents/`，并通过 `scripts/sync-agent-configs` 单向同步到
`.trae/`、`.opencode/`、`.codebuddy/`、`.goose/`（均为**项目级**配置，harness 在打开项目时自动加载）。

WorkBuddy **不支持项目级配置**，不会在项目目录中自动发现或加载 MCP 配置文件。因此它无法被纳入上述同步体系，
必须改用**个人级（user-level）配置**。本目录的 README 说明如何为 WorkBuddy 手动加载 VocabCraft 的全部能力。

## 1. 配置文件存放路径

WorkBuddy 的个人级配置目录按操作系统确定：

| 系统 | 配置目录 |
|------|----------|
| Windows | `%USERPROFILE%\.workbuddy` |
| Linux / macOS | `$HOME/.workbuddy` |

固定文件名约定：

```
~/.workbuddy/
├── mcp.json        # MCP 服务器注册（stdio）
├── AGENTS.md       # → 指向 .agents/AGENTS.md 的符号链接（业务规则）
└── skills/         # → 指向 .agents/skills/ 的符号链接（5 个 vocabcraft-* 技能）
```

## 2. 格式要求

`mcp.json` 采用标准 MCP stdio 配置 schema（与项目内 `.codebuddy/mcp.json` 一致）：

```json
{
  "mcpServers": {
    "vocabcraft-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--no-sync",
        "--directory",
        "C:\\abs\\path\\to\\vocabcraft\\vocabcraft-mcp",
        "vocabcraft-mcp"
      ]
    }
  }
}
```

要点：

- **必须写绝对路径**：个人级配置不支持 `${workspaceFolder}` 变量替换。
- `--no-sync`：复用安装时 `uv sync` 生成的虚拟环境，避免每次启动重新解析依赖。
- `command` 必须为 `uv` 且已加入 `PATH`（安装脚本会检测）。

## 3. 加载机制

WorkBuddy 启动时自动读取个人配置目录下的 `mcp.json` 并注册其中的 MCP 服务器；读取 `AGENTS.md` 作为系统级
业务规则约束；从 `skills/` 目录加载可用技能。

由于项目配置（`.agents/AGENTS.md`、`.agents/skills/`）是持续演进的真相源，本方案**推荐用符号链接**
把个人配置指向项目目录，使规则/技能随项目同步更新：

```bash
# 在项目根目录执行
ln -sfn "$(pwd)/.agents/AGENTS.md" ~/.workbuddy/AGENTS.md
ln -sfn "$(pwd)/.agents/skills"     ~/.workbuddy/skills
```

符号链接创建失败（如 Windows 非提权环境）时，安装脚本会**降级为复制**。复制为静态快照，
项目配置更新后需重新运行安装脚本。

## 4. 与项目现有配置体系的兼容性

- **同一套真相源**：WorkBuddy 加载的 `.agents/AGENTS.md` 与 `.agents/skills/` 和五个项目级运行时完全一致，
  业务规则、5 个 Skill（capture / review / quiz / stats / export）无任何差异。
- **不纳入同步生成**：`.workbuddy/` 不在 `sync-agent-configs` 的生成范围内，也不在 pre-commit 拦截名单中，
  本目录唯一的产物就是这份 README。
- **MCP 行为一致**：通过 `uv run vocabcraft-mcp` 启动同一个 MCP Server，4 个 CRUD + 6 个业务工具、
  `algorithms.py`（SM-2）、本地 JSON 存储全部复用，无二义性。
- **数据隔离**：学习数据仍仅存于项目内 `vocabcraft-mcp/data/`，不写入个人目录。

## 安装

推荐使用项目安装脚本自动完成上述检测与链接：

```powershell
# Windows
pwsh .\install.ps1 -AgentRuntime workbuddy

# Linux / macOS
./install.sh workbuddy
```

脚本会依次：检测 `workbuddy` 可执行文件 → 解析个人配置目录 → 写入 `mcp.json`（绝对路径）→
为 `AGENTS.md` 与 `skills/` 建立符号链接（失败则降级复制）→ 给出验证提示。
