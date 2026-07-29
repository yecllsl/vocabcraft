# VocabCraft 部署指南

## 快速开始

### Windows 用户

```powershell
# 1. 从 GitHub Releases 下载 VocabCraft-vX.Y.Z.zip，解压到任意目录（如 D:\vocabcraft\）
#    或用 7-Zip 解压 .tar.zst / .tar.gz

# 2. 运行安装脚本
.\install.ps1

# 3. 用 Trae IDE CN 或 Trae Work CN 打开文件夹
# 4. 设置 → MCP → 启用项目级 MCP
# 5. 重启 Trae
```

### Linux / macOS 用户

```bash
# 1. 从 GitHub Releases 下载并解压
#    tar.zst (推荐):  tar --zstd -xf VocabCraft-vX.Y.Z.tar.zst
#    tar.gz:          tar -xzf VocabCraft-vX.Y.Z.tar.gz

# 2. 运行安装脚本
chmod +x install.sh
./install.sh

# 3. 用 Trae IDE CN 或 Trae Work CN 打开文件夹
# 4. 设置 → MCP → 启用项目级 MCP
# 5. 重启 Trae
```

### 安装时的可选步骤

`install.ps1` / `install.sh` 会在基础依赖装完后询问：

> **是否安装 OCR 可选依赖？**
> OCR 用于图片词汇识别，paddleocr + paddlepaddle 约 1.5GB，安装较慢。
> 仅当需要 `/capture` 拍照录入词汇时才需要。

- 选 `N`（默认）：跳过 OCR，手动录入、复习、考题、统计等功能完全可用
- 选 `Y`：安装 PaddleOCR，后续可调用 `uv sync --extra ocr` 重新装

> 💡 跳过后若需要补装：`cd vocabcraft-mcp && uv sync --extra ocr`

## 环境要求

| 依赖 | 最低版本 | 安装方式 |
|------|---------|---------|
| Python | 3.12+ | https://www.python.org/downloads/ |
| uv | 最新版 | Windows: `irm https://astral.sh/uv/install.ps1 \| iex` |
| | | Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Trae IDE CN | 最新版 | https://trae.com.cn |
| Trae Work CN | 最新版 | https://trae.com.cn |

> 💡 Trae IDE CN 与 Trae Work CN **二选一即可**，也可同时安装。VocabCraft 在两个环境下的配置与使用完全一致。

## 双环境配置详解（核心）

VocabCraft 的核心设计是 **一份配置同时运行在 Trae IDE CN 与 Trae Work CN 两个环境**。两个环境共用项目根目录下的 `.trae/mcp.json`，无需为每个环境单独配置。

### 双环境共用原理

```
┌─────────────────────────┐     ┌─────────────────────────┐
│   Trae IDE CN           │     │   Trae Work CN          │
│   (设置→MCP→启用)        │     │   (设置→MCP→启用)        │
└────────────┬────────────┘     └────────────┬────────────┘
             │                                │
             │     读取同一份配置               │
             └────────────┬───────────────────┘
                          ↓
              ┌───────────────────────┐
              │  .trae/mcp.json       │
              │  ${workspaceFolder}   │  ← 两个环境各自替换为当前工作区路径
              │  /vocabcraft-mcp      │
              └───────────────────────┘
                          ↓
              ┌───────────────────────┐
              │  vocabcraft-mcp/      │  ← 同一份 MCP Server 代码
              │  (uv run 入口)         │
              └───────────────────────┘
```

两个环境打开**同一个项目文件夹**时，`${workspaceFolder}` 会被各自替换为实际路径，因此解压到任意位置、用任一环境打开都能正常工作。

### Trae IDE CN 配置步骤

1. 打开 Trae IDE CN
2. **文件 → 打开文件夹** → 选择 VocabCraft 解压目录
3. 进入 **设置**（齿轮图标）→ **MCP**
4. 打开 **"启用项目级 MCP"** 开关
5. 在弹窗中确认信任
6. 重启 Trae IDE CN

### Trae Work CN 配置步骤

1. 打开 Trae Work CN
2. **文件 → 打开文件夹** → 选择**同一个** VocabCraft 解压目录
3. 进入 **设置** → **MCP**
4. 打开 **"启用项目级 MCP"** 开关
5. 在弹窗中确认信任
6. 重启 Trae Work CN

> ✅ 两个环境操作完全一致，可同时启用。在哪个环境中使用 `/capture` 等命令，就由哪个环境的 MCP Server 实例响应。

### mcp.json 配置内容

项目级 MCP 配置已内置于 `.trae/mcp.json`：

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

`${workspaceFolder}` 会在 MCP Server 启动时自动替换为项目根目录路径，因此：
- 解压到任意位置都能正常工作
- Trae IDE CN 与 Trae Work CN 各自替换为当前打开的路径
- 两个环境共用同一个项目文件夹时，行为完全一致

### 手动配置（回退方案）

如果你的 Trae 版本不支持 `${workspaceFolder}` 变量，可以运行安装脚本的路径修复功能：

```powershell
# Windows
.\install.ps1 -FixPath
```

```bash
# Linux/macOS
./install.sh --fix-path
```

这会自动将 mcp.json 中的 `${workspaceFolder}` 替换为实际绝对路径。

> ⚠️ 注意：使用 `-FixPath` 后，mcp.json 中的路径变为绝对路径，项目文件夹移动后需要重新运行修复。推荐优先使用 `${workspaceFolder}` 变量版本。

也可以手动在 Trae 中添加 MCP 服务器：

| 字段 | 值 |
|------|-----|
| 服务器名称 | `vocabcraft-mcp` |
| 命令 | `uv` |
| 参数 | `run --directory 你的项目路径/vocabcraft-mcp vocabcraft-mcp` |

### 验证配置

配置完成后，可以测试 MCP Server 是否正常工作：

```powershell
cd vocabcraft-mcp
uv run vocabcraft-mcp
```

如果 MCP Server 正常启动，说明配置成功。在 Trae 中输入 `/capture` 等命令应能触发对应 skill。

## Skills 和 Rules 配置

Skills 和 Rules 配置位于 `.trae/` 目录下，Trae 会自动读取，修改后重启 Trae 即可生效。

### Skills 说明（vocabcraft-* 业务编排）

| Skill 名称 | 触发命令 | 功能描述 |
|-----------|---------|---------|
| vocabcraft-capture | `/capture` | 拍照录入词汇流程编排（OCR + 结构化解析） |
| vocabcraft-review | `/review` | 到期复习清单生成（SM-2 排程） |
| vocabcraft-quiz | `/quiz` | 考题生成与评分（更新记忆状态，支持文言文释义题） |
| vocabcraft-stats | `/stats` | 词汇统计查询 |
| vocabcraft-export | `/export` | 词汇数据导出 |

### Rules 说明（vocabcraft-* 业务规则 + BMAD 共存）

`.trae/rules/` 下同时存在两类规则：

**vocabcraft-\* 业务规则**（词汇学习业务约束）：

| Rule 名称 | 作用范围 | 功能描述 |
|-----------|---------|---------|
| vocabcraft-* 采集规则 | /capture | OCR 识别、词汇结构化解析约束 |
| vocabcraft-* 复习规则 | /review /quiz | SM-2 排程、考题生成、评分约束 |
| vocabcraft-* 数据安全 | 全局 | 本地存储、不外传、导出确认 |
| vocabcraft-* 交互规则 | 全局 | 命令格式、反馈、降级方案 |

**BMAD 工作流规则**（通用开发方法论，与词汇业务无关）：

| Rule 名称 | 功能描述 |
|-----------|---------|
| ponytail.md | 懒惰高级开发模式（最少可行代码） |
| project-rules.md | 项目总规则、协同黄金法则 |
| security-rules.md | 安全规则（输入验证/敏感数据） |
| compliance-rules.md | 合规规则（代码审计/许可证） |
| quality-rules.md | 质量规则（测试覆盖/代码规范） |
| process-rules.md | 流程规则（开发过程/审批） |

> 💡 两类规则各司其职：业务规则约束词汇学习流程，BMAD 规则约束代码开发流程。发布包构建时只打包 vocabcraft-\* 业务文件（见 [scripts/build-release.sh](scripts/build-release.sh)）。

## 常见问题

### Q1: 安装脚本报错 "uv 未安装"

**解决方案：**
```powershell
# 安装 uv (Windows PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 uv (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Q2: MCP Server 启动失败

**检查项：**
1. Python 版本是否 >= 3.12
2. 依赖是否安装成功（运行 `cd vocabcraft-mcp && uv sync`）
3. mcp.json 中的路径是否正确

**解决方案：**
```powershell
cd vocabcraft-mcp
uv sync
```

### Q3: Trae 无法识别 MCP Server

**检查项：**
1. 是否已启用项目级 MCP
2. `.trae/mcp.json` 文件是否存在
3. 是否已重启 Trae

**解决方案：**
- 运行 `.\install.ps1 -FixPath` 修复路径
- 或手动在 Trae 中添加 MCP 服务器（见上文）

### Q4: Trae IDE CN 和 Trae Work CN 能否同时使用？

可以，且推荐这样做。两个环境共用同一份 `.trae/mcp.json`：

- **同一台机器**：两个环境打开同一个项目文件夹，各自启用项目级 MCP 即可。`${workspaceFolder}` 会各自替换为当前路径。
- **数据共享**：两个环境的 MCP Server 实例读写同一个 `vocabcraft-mcp/data/` 目录，词汇数据互通。
- **配置隔离**：若希望两个环境使用独立数据，可复制整个项目文件夹到不同目录，各自运行 `-FixPath` 修复为独立绝对路径。

### Q5: Skills/Commands 不生效

**检查项：**
1. `.trae/skills/vocabcraft-*` 和 `.trae/rules/vocabcraft-*` 目录/文件是否存在
2. 文件名和格式是否正确
3. Trae 是否重启

**解决方案：**
- 重启 Trae IDE CN / Trae Work CN
- 检查 .trae 目录结构是否完整（应有 agents/commands/skills/rules 子目录）

### Q6: PaddleOCR / OCR 安装失败

**检查项：**
1. Python 版本是否 >= 3.12
2. 网络是否畅通（需下载 paddleocr + paddlepaddle 约 1.5GB）
3. 是否在 `uv sync` 时选择了 `N` 跳过 OCR

**解决方案：**
- OCR 为**可选依赖**，默认 `uv sync` 不会安装
- 如需使用 `/capture` 拍照录入：`cd vocabcraft-mcp && uv sync --extra ocr`
- 如不使用 OCR（手动输入词汇），**无需任何额外操作**

### Q7: 如何升级到新版本

1. 备份你的 `vocabcraft-mcp/data/` 目录（包含所有词汇记录与复习状态）
2. 从 GitHub Releases 下载新版并解压到新目录
3. 把旧版的 `data/` 目录复制到新版 `vocabcraft-mcp/data/` 对应位置
4. 在新目录运行 `install.ps1` / `install.sh`（会自动 `uv sync`）
5. 在 Trae 中重新启用项目级 MCP

## 项目结构说明

```
vocabcraft/
├── vocabcraft-mcp/                       # MCP Server 服务层（Python）
│   ├── src/vocabcraft_mcp/
│   │   ├── server.py                      # 服务入口 (FastMCP)
│   │   ├── models.py                      # Pydantic v2 数据模型
│   │   ├── storage.py                     # JSON 存储引擎（原子写）
│   │   ├── algorithms.py                  # SM-2 遗忘曲线算法
│   │   ├── tools/                         # MCP Tools 实现
│   │   ├── prompts/                       # AI Prompt 模板
│   │   └── resources/                     # MCP Resources
│   ├── tests/                             # 测试套件
│   ├── data/                              # 数据存储目录 (运行时)
│   │   ├── vocabs/ reviews/ quizzes/      # 词汇 / 复习 / 考题 JSON
│   │   ├── images/                        # OCR 图片
│   │   └── exports/                       # 导出文件
│   ├── pyproject.toml                     # Python 项目配置
│   └── uv.lock                            # 依赖锁定
│
├── .trae/                                  # 配置层（subagent 配置 + BMAD 共存）
│   ├── mcp.json                            # 项目级 MCP 配置（双环境共用）
│   ├── hooks.json                          # Trae 钩子配置
│   ├── skill-config.json                   # Skills 配置
│   ├── 开发流程规范.md                     # 开发流程统一手册
│   ├── agents/                             # subagent 角色定义（vocabcraft-* + BMAD）
│   ├── commands/                           # 命令定义（vocabcraft-* + BMAD）
│   ├── documents/                          # 项目文档（发版计划等）
│   ├── skills/                             # vocabcraft-* skills
│   │   ├── vocabcraft-capture/
│   │   ├── vocabcraft-review/
│   │   ├── vocabcraft-quiz/
│   │   ├── vocabcraft-stats/
│   │   └── vocabcraft-export/
│   └── rules/                              # vocabcraft-* 业务规则 + BMAD 既有规则
│
├── .github/workflows/
│   ├── test.yml                            # CI：单元 + 集成测试（3.12/3.13）
│   └── release.yml                         # Release：push tag → 自动打包 + 上传
│
├── scripts/                                # 开发者工具
│   ├── build-release.ps1                   # Windows 发布包构建
│   └── build-release.sh                    # Linux/macOS 发布包构建（与 .ps1 对齐）
├── install.ps1                             # Windows 安装脚本（可选装 OCR）
├── install.sh                              # Linux/macOS 安装脚本（可选装 OCR）
├── QUICKSTART.md                           # 5 分钟快速上手
├── DEPLOY.md                               # 本文件
├── README.md                               # 项目总览
└── LICENSE                                 # MIT
```

## 开发者工具

### 本地构建发布包

```powershell
# Windows (PowerShell 5.1+)
.\scripts\build-release.ps1 -Version 0.3.0
```

```bash
# Linux / macOS
bash scripts/build-release.sh 0.3.0
```

产物：`dist/VocabCraft-v0.3.0.{zip,tar.zst,tar.gz}`，结构与 GitHub Release 资产一致。

构建脚本采用**白名单复制策略**，只打包必要文件：

- `vocabcraft-mcp/src/`、`vocabcraft-mcp/tests/`、`pyproject.toml`、`uv.lock`
- `.trae/skills/vocabcraft-*`、`.trae/rules/vocabcraft-*`、`.trae/agents/vocabcraft-*`、`.trae/commands/vocabcraft-*`（**只打包 vocabcraft-* 业务文件，不打包 BMAD 既有文件**）
- `.trae/mcp.json`（注入 `${workspaceFolder}` 变量版本）、`.trae/hooks.json`
- 顶层文档（README/QUICKSTART/DEPLOY/LICENSE）和安装脚本

自动排除：

- `__pycache__/`、`.pytest_cache/`、`*.pyc`
- `.venv/`、`.git/`、`.vscode/`
- `data/*.json`（用户数据不打包，只放 `.gitkeep` 占位）
- `dist/`（构建产物本身）

### 本地运行测试

```bash
cd vocabcraft-mcp

# 单元 + 集成测试
uv sync --extra dev
uv run pytest tests/ -m "not e2e"
```

### GitHub Actions

- **`.github/workflows/test.yml`**：PR / push 时跑单元 + 集成测试（矩阵 Python 3.12 / 3.13）
- **`.github/workflows/release.yml`**：push tag `v*.*.*` 时构建 + 上传 release，附 `generate_release_notes` 自动生成 changelog
