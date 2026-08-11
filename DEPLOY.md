# VocabCraft 部署指南

## 快速开始

### Windows 用户

```powershell
# 1. 从 GitHub Releases 下载 VocabCraft-v0.5.4.zip，解压到任意目录（如 D:\vocabcraft\）
#    或用 7-Zip 解压 .tar.zst / .tar.gz

# 2. 运行安装脚本
.\install.ps1

# 3. 用 Trae IDE CN / Trae Work CN / CodeBuddy / OpenCode / Goose 打开文件夹
# 4. 启用项目级 MCP（各运行时入口不同，见下文）
# 5. 重启运行时
```

### Linux / macOS 用户

```bash
# 1. 从 GitHub Releases 下载并解压
#    tar.zst (推荐):  tar --zstd -xf VocabCraft-v0.5.4.tar.zst
#    tar.gz:          tar -xzf VocabCraft-v0.5.4.tar.gz

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 用对应运行时打开文件夹
# 4. 启用项目级 MCP
# 5. 重启运行时
```

> 💡 安装脚本只装基础依赖（无需 OCR 引擎）。图片词汇采集由**宿主 LLM 多模态直接解析**，手动录入 / 复习 / 出题 / 统计 / 导出等功能均不依赖额外模型。

## 环境要求

| 依赖 | 最低版本 | 安装方式 |
|------|---------|---------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| uv | 最新版 | Windows: `irm https://astral.sh/uv/install.ps1 \| iex` |
| | | Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| 运行时 | 最新版 | Trae IDE CN / Trae Work CN / CodeBuddy / OpenCode / Goose（任选其一或全部） |

> 💡 五个运行时**共用同一份配置与数据**，也可同时安装。

## 多运行时共用配置（核心）

VocabCraft 的设计是**一份配置同时运行在多个 Agent 运行时**。Trae / OpenCode / CodeBuddy 共用 `.agents/runtime/trae.json`（同步生成 `.trae/mcp.json`）与 `.agents/AGENTS.md`（同步到根目录与各平台）；Goose 单独走 `.agents/runtime/goose.json`（同步生成 `.goose/config.yaml`，使用绝对路径，无需 `${workspaceFolder}`）。无需单独配置。

```
┌─────────────────────────┐  ┌─────────────────────────┐  ┌──────────────────┐  ┌──────────────┐
│ Trae IDE CN             │  │ Trae Work CN            │  │ CodeBuddy      │  │ OpenCode     │
│ 设置→MCP→启用            │  │ 设置→MCP→启用           │  │ 信任 mcp        │  │ 运行 opencode│
└────────────┬────────────┘  └────────────┬────────────┘  └────────┬─────────┘  └──────┬───────┘
             │ 读取同一份配置（${workspaceFolder} 各自替换）          │                │
             └────────────────────┬─────────────────────────────────┘                │
                                  ↓                                                  ↓
              ┌───────────────────────┐                                              │
              │  .agents/runtime/trae.json │  ← 同步生成 .trae/mcp.json，各运行时各自替换路径          │
              │  ${workspaceFolder}   │                                              │
              │  /vocabcraft-mcp      │                                              │
              └───────────────────────┘                                              │
                                  ↓                                                  │
              ┌───────────────────────┐                                              │
              │  vocabcraft-mcp/      │  ← 同一份 MCP Server 代码                      │
              │  (uv run 入口)         │                                              │
              └───────────────────────┘                                              │
```

打开**同一个项目文件夹**时，`${workspaceFolder}` 会被各自替换为实际路径，因此解压到任意位置、用任一运行时打开都能正常工作。

### 各运行时配置步骤

**Trae IDE CN / Trae Work CN**
1. 打开项目文件夹
2. **设置 → MCP**，打开 **"启用项目级 MCP"** 开关
3. **设置 → 规则**，开启 **"将 AGENTS.md 包含在上下文中"**
4. 重启 Trae

**CodeBuddy**
1. 运行 `.\install.ps1 -AgentRuntime codebuddy`（或 `bash install.sh --agent-runtime codebuddy`）
2. 用 CodeBuddy 打开项目文件夹
3. 在 MCP 配置中信任 `vocabcraft-mcp`

**OpenCode**
1. 运行 `.\install.ps1 -AgentRuntime opencode`（或 `bash install.sh --agent-runtime opencode`）
2. 在项目目录运行 `opencode`（AGENTS.md 自动加载）

**Goose**
1. 运行 `.\install.ps1 -AgentRuntime goose`（或 `bash install.sh --agent-runtime goose`）
2. 用 Goose 打开项目文件夹，会自动读取 `.goose/config.yaml` 加载 vocabcraft-mcp（绝对路径，无需 `${workspaceFolder}`）

> ✅ 五个运行时操作一致，可同时启用。在哪个环境中使用 `/capture` 等命令，就由哪个环境的 MCP Server 实例响应。

### mcp.json 配置内容

项目级 MCP 配置源在 `.agents/runtime/trae.json`，经 `scripts/sync-agent-configs` 同步生成 `.trae/mcp.json`：

```json
{
  "mcpServers": {
    "vocabcraft-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${workspaceFolder}/vocabcraft-mcp",
        "vocabcraft-mcp"
      ]
    }
  }
}
```

`${workspaceFolder}` 在 MCP Server 启动时自动替换为项目根目录路径，因此解压到任意位置、各运行时均能正常工作。

### 手动配置（回退方案）

若你的运行时版本不支持 `${workspaceFolder}` 变量，可运行路径修复功能：

```powershell
# Windows
.\install.ps1 -FixPath
```

```bash
# Linux/macOS
./install.sh --fix-path
```

这会自动将 `.agents/runtime` 配置中的 `${workspaceFolder}` 替换为实际绝对路径（移动项目后需重新运行修复）。

也可手动在运行时中添加 MCP 服务器：

| 字段 | 值 |
|------|-----|
| 服务器名称 | `vocabcraft-mcp` |
| 命令 | `uv` |
| 参数 | `run --directory 你的项目路径/vocabcraft-mcp vocabcraft-mcp` |

### 验证配置

```powershell
cd vocabcraft-mcp
uv run vocabcraft-mcp
```

若 MCP Server 正常启动，说明配置成功。在运行时中输入 `/capture` 等命令应能触发对应 skill。

## Skills 与规则配置

Skills 位于 `.agents/skills/`（AAIF 真相源），经 `scripts/sync-agent-configs` 同步到 `.trae/` / `.opencode/` / `.codebuddy/` / `.goose/`。修改后重启运行时即可生效。

### Skills 说明（vocabcraft-* 业务编排）

| Skill 名称 | 触发命令 | 功能描述 |
|-----------|---------|---------|
| vocabcraft-capture | `/capture` | 词汇采集流程编排（宿主 LLM 多模态解析 / 文本 / Excel 导入） |
| vocabcraft-review | `/review` | 到期复习清单生成（SM-2 排程） |
| vocabcraft-quiz | `/quiz` | 考题生成与评分（更新记忆状态，支持文言文释义题） |
| vocabcraft-stats | `/stats` | 词汇统计查询 |
| vocabcraft-export | `/export` | 词汇数据导出 |

### 规则来源

业务规则与开发规范统一存放于 **`.agents/AGENTS.md`**（五个运行时共用，单一真相源，同步到根目录与各平台），不再拆分到 `.trae/rules/`。各 skill 的「约束规则」内联在其 `SKILL.md` 中。

## 常见问题

### Q1: 安装脚本报错 "uv 未安装"

```powershell
# 安装 uv (Windows)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# 安装 uv (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Q2: MCP Server 启动失败

1. Python 版本是否 >= 3.12
2. 依赖是否安装成功（`cd vocabcraft-mcp && uv sync`）
3. mcp.json 中的路径是否正确

```powershell
cd vocabcraft-mcp
uv sync
```

### Q3: 运行时无法识别 MCP Server

1. 是否已启用项目级 MCP / 已信任 vocabcraft-mcp
2. `.trae/mcp.json` 文件是否存在（由 `.agents/runtime/trae.json` 同步生成）
3. 是否已重启运行时

→ 运行 `.\install.ps1 -FixPath` 修复路径，或手动添加（见上文）。

### Q4: 五个运行时能否同时使用？

可以，且推荐。各运行时共用同一份 `.agents/` 配置（`trae.json` 同步生成 `.trae/mcp.json`；`goose.json` 同步生成 `.goose/config.yaml`；`.agents/AGENTS.md` 同步到根目录与各平台）：

- **同一台机器**：各运行时打开同一个项目文件夹，各自启用 MCP 即可，`${workspaceFolder}` 会各自替换为当前路径。
- **数据共享**：各运行时 MCP Server 实例读写同一个 `vocabcraft-mcp/data/` 目录，词汇数据互通。
- **配置隔离**：若希望各运行时使用独立数据，可复制整个项目文件夹到不同目录，各自运行 `-FixPath` 修复为独立绝对路径。

### Q5: Skills / Commands 不生效

1. `.agents/skills/vocabcraft-*` 目录和 SKILL.md 是否存在
2. 文件名和格式是否正确
3. 运行时是否重启

→ 重启对应运行时，检查 `.agents` 目录结构是否完整（应有 `skills/` 子目录）。

### Q6: 如何升级到新版本

1. 备份 `vocabcraft-mcp/data/` 目录（含词汇记录与复习状态）
2. 从 GitHub Releases 下载新版并解压到新目录
3. 把旧版 `data/` 复制到新版的 `vocabcraft-mcp/data/` 对应位置
4. 在新目录运行 `install.ps1` / `install.sh`（自动 `uv sync`）
5. 在运行时中重新启用项目级 MCP

## 项目结构说明

```
vocabcraft/
├── vocabcraft-mcp/                       # MCP Server 服务层（Python）
│   ├── src/vocabcraft_mcp/
│   │   ├── server.py                      # FastMCP 服务入口
│   │   ├── models.py                      # Pydantic v2 数据模型
│   │   ├── storage.py                     # JSON 存储引擎（原子写）
│   │   ├── algorithms.py                  # SM-2 遗忘曲线算法
│   │   ├── tools/                         # MCP Tools 实现
│   │   ├── web/                           # FastAPI + ECharts 可视化
│   │   ├── prompts/                       # AI Prompt 模板
│   │   └── resources/                     # MCP Resources
│   ├── tests/                             # 测试套件
│   ├── data/                              # 数据存储目录（运行时，.gitkeep 占位）
│   │   ├── vocabs/ reviews/ quizzes/      # 词汇 / 复习 / 考题 JSON
│   │   ├── images/ exports/ imports/      # 图片 / 导出 / 导入
│   ├── pyproject.toml                     # Python 项目配置
│   └── uv.lock                            # 依赖锁定
│
├── .agents/                                # 配置层（AAIF 唯一真相源，只改这里）
│   ├── runtime/{trae,opencode,codebuddy,goose}.json    # 各平台 MCP 配置源
│   ├── skills/vocabcraft-*                # capture/review/quiz/stats/export（源文件）
│   ├── AGENTS.md                          # 统一规则源
│   └── tools.json / triggers.json / workflows.json           # AAIF 声明
│
├── .trae/  .opencode/  .codebuddy/  .goose/   # 由 scripts/sync-agent-configs 生成
│
├── .github/workflows/                     # test.yml / release.yml
├── scripts/                               # build-release.* / sync-agent-configs.*
├── install.ps1  install.sh                # 安装脚本
├── QUICKSTART.md  DEPLOY.md  README.md  CHANGELOG.md  LICENSE
```

## 开发者工具

### 本地构建发布包

```powershell
# Windows (PowerShell 5.1+)
.\scripts\build-release.ps1 -Version 0.5.4
```

```bash
# Linux / macOS
bash scripts/build-release.sh 0.5.4
```

产物：`dist/VocabCraft-v0.5.4.{zip,tar.zst,tar.gz}`，结构与 GitHub Release 资产一致。

构建脚本采用**白名单复制策略**，只打包必要文件：

- `vocabcraft-mcp/src/`、`vocabcraft-mcp/tests/`、`pyproject.toml`、`uv.lock`
- `.agents/skills/vocabcraft-*`
- `.agents/runtime/trae.json`（注入 `${workspaceFolder}` 变量版本，同步到 `.trae/mcp.json`）
- 顶层文档（README / QUICKSTART / DEPLOY / CHANGELOG / LICENSE）与安装脚本

自动排除：`__pycache__/`、`.pytest_cache/`、`*.pyc`、`.venv/`、`.git/`、`.vscode/`、`data/*.json`（用户数据只放 `.gitkeep`）、`dist/`。

### 本地运行测试

```bash
cd vocabcraft-mcp
uv sync --extra dev
uv run pytest tests/ -m "not e2e"
```

### GitHub Actions

- **`.github/workflows/test.yml`**：PR / push 时跑单元 + 集成测试（矩阵 Python 3.12 / 3.13）
- **`.github/workflows/release.yml`**：push tag `v*.*.*` 时构建 + 上传 release，附 `generate_release_notes` 自动生成 changelog
