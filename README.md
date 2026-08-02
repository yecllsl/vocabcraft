# VocabCraft - 词汇学习与制作一体 MCP 工具

词汇学习与制作一体化解决方案，同时支持 **Trae IDE CN / Trae Work CN**、**WorkBuddy (CodeBuddy)** 和 **opencode** 三个 Agent Runtime。核心流程：拍照 → AI 结构化解析 → 本地保存 → 基于遗忘曲线（SM-2 算法）的复习排程 → 到期自动出考题 → 作答评分更新记忆状态。

## 核心功能

- 📷 **拍照采集**: 拍照 + AI 结构化解析词汇（单词、音标、词性、释义、例句）
- 🧠 **智能存储**: 词汇记录本地保存，支持释义、例句、标签等多维元数据
- 📅 **复习排程**: SM-2 遗忘曲线算法，按记忆强度自动排程到期复习
- ❓ **考题生成**: 到期词汇自动生成考题（选择/填空/拼写/释义/文言文释义五种题型）
- ✅ **评分反馈**: 作答评分后自动更新 SM-2 记忆参数（易度、间隔、重复次数）
- 📊 **统计分析**: 词汇量、待复习数、掌握度分布、遗忘曲线趋势
- 📤 **数据导出**: JSON / CSV 格式导出词汇本

## 系统架构

```
用户交互层
├── 对话式交互 (命令 / 自然语言)
├── 三运行时: Trae + WorkBuddy + opencode (共用 AGENTS.md)
    ↓
Skills 编排层 (.trae/skills/vocabcraft-*: capture / review / quiz / stats / export)
    ↓
MCP Tools 层 (vocabcraft-mcp)
├── 结构化解析 → 存储 → SM-2 排程 → 考题生成 → 评分 → 统计 → 导出
    ↓
Rules 约束层 (AGENTS.md — 统一规则源，三个运行时共用)
    ↓
数据存储层 (本地 JSON 文件，原子写入)
```

## 技术栈

- **MCP Server**: Python 3.12+ / FastMCP / Pydantic v2
- **复习算法**: SM-2 遗忘曲线（SuperMemo 2）
- **数据存储**: JSON 文件（本地存储，原子写入）
- **包管理**: uv（现代高速 Python 包管理器）
- **测试**: pytest + pytest-asyncio + pytest-cov
- **CI/CD**: GitHub Actions（Tests + Release）

## 快速安装

### 前置要求

- Python 3.12+
- [uv 包管理器](https://docs.astral.sh/uv/)（Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`）
- Trae IDE CN / Trae Work CN、WorkBuddy (CodeBuddy) 或 opencode（三选一或全部）

### 安装步骤

#### 1. 下载并解压

下载 `VocabCraft-v0.3.0.zip`，解压到任意目录（如 `D:\vocabcraft\`）。

#### 2. 运行安装脚本

**Windows:**
```powershell
# 右键 install.ps1 → "使用 PowerShell 运行"
# 或在 PowerShell 中：
.\install.ps1
```

**Linux / macOS:**
```bash
chmod +x install.sh
./install.sh
```

安装脚本会自动检查环境、创建虚拟环境并安装所有依赖。

#### 3. 配置 Agent Runtime

##### Trae

1. 用 Trae IDE CN 或 Trae Work CN 打开项目文件夹
2. 进入 **设置 → MCP**，打开 **"启用项目级 MCP"** 开关
3. 进入 **设置 → 规则**，开启 **"将 AGENTS.md 包含在上下文中"**
4. 重启 Trae

> 💡 项目级 MCP 配置已内置于 `.trae/mcp.json`，使用 `${workspaceFolder}` 变量自动适配路径。

##### WorkBuddy (CodeBuddy)

1. 运行安装脚本：`.\install.ps1 -AgentRuntime workbuddy`（或 `bash install.sh --agent-runtime workbuddy`）
2. 用 WorkBuddy 打开项目文件夹
3. 在 MCP 配置中信任 vocabcraft-mcp

##### opencode

1. 运行安装脚本：`.\install.ps1 -AgentRuntime opencode`（或 `bash install.sh --agent-runtime opencode`）
2. 在项目目录运行 `opencode`

#### 4. 开始使用

```
/capture  - 拍照录入词汇
/review   - 查看到期复习清单
/quiz     - 出考题并作答评分
/stats    - 查看词汇统计
/export   - 导出词汇数据
```

## 下载与发布

每次发版会在 GitHub Release 页面提供三种压缩包，按需选择：

| 格式 | 适用平台 | 特点 |
|------|---------|------|
| `VocabCraft-vX.Y.Z.zip` | Windows | 与 PowerShell `Compress-Archive` 兼容，最通用 |
| `VocabCraft-vX.Y.Z.tar.zst` | 现代 Linux/macOS | 体积最小、速度最快（**推荐**） |
| `VocabCraft-vX.Y.Z.tar.gz` | 所有 Unix | 兼容性最好，老旧系统 fallback |

访问 https://github.com/yecllsl/vocabcraft/releases 下载最新版本。

## 使用方法

### 命令模式

| 命令 | 功能 |
|------|------|
| `/capture` | 拍照录入词汇（AI 结构化） |
| `/review` | 查看到期复习清单（按 SM-2 排程） |
| `/quiz` | 出考题并作答评分（更新记忆状态） |
| `/stats` | 查看词汇统计（词汇量 / 掌握度 / 趋势） |
| `/export` | 导出词汇数据（JSON / CSV） |

### 自然语言模式

- "帮我录入这页单词" → 触发 `/capture`
- "我该复习什么" → 触发 `/review`
- "考考我" / "出题" → 触发 `/quiz`
- "看看我的词汇掌握情况" → 触发 `/stats`
- "导出我的词汇本" → 触发 `/export`

### 核心学习闭环

```
拍照 ──→ AI 结构化解析 ──→ 本地保存
                                      │
                   ┌──────────────────┘
                   ↓
        SM-2 遗忘曲线排程 ──→ 到期词汇 ──→ 出考题
                                                   │
                        作答评分 ←──────────────────┘
                            │
                   更新 SM-2 记忆参数（易度/间隔/重复次数）
                            │
                            └──→ 回到排程（形成学习闭环）
```

### 文言文词汇出题（v0.3.0 新增）

针对 `language=zh_classical` 的文言文词汇，系统采用特殊的出题方式：

**题目形式：**
- 给出一条例句，将目标词用 `<mark>` 高亮
- 提供 4 个词性选项（单选）
- 用户填写释义

**评分规则：**
- 词性大小写不敏感（`n.` = `N.`）
- 释义严格匹配（仅去除首尾空白）
- 词性和释义均正确得 5 分，否则 0 分

**多义词覆盖：**
- 系统按复习历史轮询不同义项，确保每个释义都被考查
- 复习次数最少的义项优先出题

**作答格式：**
```
词性|释义
例如：n.|兵器
```

## 项目结构

```
vocabcraft/
├── AGENTS.md                                 # 统一规则源（三个运行时共用）
├── vocabcraft-mcp/                           # MCP Server 服务层（Python）
│   ├── src/vocabcraft_mcp/
│   │   ├── server.py                         # FastMCP 服务入口（main 函数）
│   │   ├── models.py                         # Pydantic v2 数据模型（词汇/考题/记忆状态）
│   │   ├── storage.py                        # JSON 存储引擎（原子写、部分更新）
│   │   ├── algorithms.py                     # SM-2 遗忘曲线算法
│   │   ├── tools/                            # MCP Tools（解析 / CRUD / 排程 / 考题 / 评分 / 统计 / 导出）
│   │   ├── prompts/                          # AI Prompt 模板（词汇解析 / 考题生成 / 评分）
│   │   └── resources/                        # MCP Resources（遗忘曲线 / 语言包 / 考题模板）
│   ├── tests/                                # 测试套件（单元 + 集成）
│   ├── data/                                 # 运行时数据（被 .gitignore，保留 .gitkeep）
│   │   ├── vocabs/                           # 词汇记录 JSON
│   │   ├── reviews/                          # 复习排程 JSON
│   │   ├── quizzes/                          # 考题与作答 JSON
│   │   ├── images/                           # 图片文件
│   │   └── exports/                          # 导出文件
│   ├── pyproject.toml                        # Python 项目配置（入口 vocabcraft-mcp）
│   └── uv.lock                               # 依赖锁定文件
│
├── .trae/                                    # 配置层（Trae 开发时源文件）
│   ├── mcp.json                              # 项目级 MCP 配置（${workspaceFolder} 适配）
│   ├── skill-config.json                     # Skills 配置
│   ├── skills/                               # Skills 源文件
│   │   ├── vocabcraft-capture/               # /capture 拍照录入
│   │   ├── vocabcraft-review/                # /review 复习排程
│   │   ├── vocabcraft-quiz/                  # /quiz 考题与评分
│   │   ├── vocabcraft-stats/                 # /stats 统计
│   │   └── vocabcraft-export/                # /export 导出
│   └── 开发流程规范.md                        # 开发流程统一手册
│
├── .opencode/                                # opencode 配置（sync-agent-configs 生成）
├── .workbuddy/                               # WorkBuddy 配置（sync-agent-configs 生成）
│
├── .github/
│   └── workflows/
│       ├── test.yml                          # CI：单元 + 集成测试（3.12/3.13）
│       └── release.yml                       # Release：push tag → 自动打包 + 上传
│
├── scripts/                                  # 开发者工具
│   ├── build-release.ps1                     # Windows 发布包构建（PowerShell）
│   ├── build-release.sh                      # Linux/macOS 发布包构建（bash，与 .ps1 逻辑对齐）
│   ├── sync-agent-configs.ps1               # 同步 AGENTS.md 到 opencode/WorkBuddy 配置（PowerShell）
│   └── sync-agent-configs.sh                # 同步 AGENTS.md 到 opencode/WorkBuddy 配置（bash）
├── install.ps1                               # Windows 安装脚本
├── install.sh                                # Linux/macOS 安装脚本
├── QUICKSTART.md                             # 5 分钟快速上手
├── DEPLOY.md                                 # 详细部署指南
├── README.md                                 # 本文件
└── LICENSE                                   # MIT
```

## 架构设计说明

### 分层分离原则

本项目采用 **"服务层 + 配置层"** 分离架构：

| 层级 | 位置 | 用途 |
|------|------|------|
| **服务层** | `vocabcraft-mcp/` | 纯 Python MCP Server，通用，不绑定任何客户端，可独立发布 |
| **配置层** | `.trae/` | Trae 开发时源文件，定义 Skills 流程与约束（单一真相源） |

### AGENTS.md 统一规则源

`AGENTS.md` 是三个运行时共用的统一规则源，包含：

- **业务规则** — 采集规则、复习规则、交互规则、数据安全规则
- **开发规范** — 代码规范、安全规则、合规规则、质量规则、流程规则
- **架构定义** — 系统架构、MCP Tools 参考、Agent 行为约束
- **命令参考** — /capture、/review、/quiz、/stats、/export 的触发条件与约束

三个运行时（Trae / WorkBuddy / opencode）都读取 `AGENTS.md`，保证行为一致。

### 多运行时适配

项目同时支持 **Trae IDE CN / Trae Work CN**、**WorkBuddy (CodeBuddy)** 和 **opencode** 三个 Agent Runtime，核心机制：

1. **统一规则源** — `AGENTS.md` 是唯一的规则与行为定义文件，三个运行时共用
2. **开发时源文件** — `.trae/` 是 Skills 和 MCP 配置的开发时源文件（编辑在这里进行）
3. **同步生成** — 运行 `.\scripts\sync-agent-configs.ps1`（或 `.\scripts\sync-agent-configs.sh`）将 `.trae/skills/` 同步到 `.opencode/` 和 `.workbuddy/` 对应目录
4. **各运行时独立配置目录** — `.trae/`（Trae）、`.opencode/`（opencode）、`.workbuddy/`（WorkBuddy）各自独立，互不干扰

### 为什么要分离？

1. **职责清晰**: 代码归代码，配置归配置
2. **可复用**: `vocabcraft-mcp/` 可单独在任何 MCP 客户端中使用
3. **单一真相源**: `AGENTS.md` 是唯一的规则与行为定义，Skills 配置在 `.trae/` 下编辑，同步到其他运行时
4. **Git 友好**: 项目结构一目了然，`.trae/` 即 Trae 配置根目录
5. **多运行时友好**: 一份 AGENTS.md，三个运行时共用，同步脚本自动生成各运行时配置

## 数据安全

- ✅ 所有数据仅存储在本地
- ✅ 不收集任何个人身份信息
- ✅ 图片文件存储在项目目录下
- ✅ 导出数据前需用户确认

## 常见问题

### Q: 安装脚本报错 "uv 未安装"

```powershell
# 安装 uv (Windows)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装 uv (Linux/macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Q: MCP Server 不生效

1. 确认已打开「启用项目级 MCP」开关（Trae）或已信任 vocabcraft-mcp（WorkBuddy）
2. 确认已重启 IDE / 运行时
3. 如果 `${workspaceFolder}` 变量不被支持，运行 `.\install.ps1 -FixPath` 自动修复路径

### Q: 多个 Agent Runtime 能否同时使用？

可以。三个运行时（Trae IDE CN / Trae Work CN、WorkBuddy、opencode）共用同一份 `AGENTS.md` 规则源，各自有独立的配置目录。首次运行或修改 Skills 后，执行同步脚本确保各运行时配置一致：

```powershell
.\scripts\sync-agent-configs.ps1          # Windows
bash scripts/sync-agent-configs.sh        # Linux/macOS
```

## License

MIT License

## Contributing

欢迎提交 Issue 和 Pull Request！

## 测试与开发

### 本地运行测试

```bash
cd vocabcraft-mcp

# 单元 + 集成测试
uv sync --extra dev
uv run pytest tests/ -m "not e2e"
```

测试矩阵 Python 3.12 / 3.13。

### 本地构建发布包

```powershell
# Windows
pwsh .\scripts\build-release.ps1 -Version 0.3.0
```

```bash
# Linux / macOS
bash scripts/build-release.sh 0.3.0
```

产物：`dist/VocabCraft-v0.3.0.{zip,tar.zst,tar.gz}`。

### CI/CD

- **PR / push** → [`.github/workflows/test.yml`](.github/workflows/test.yml) 跑单元 + 集成测试
- **push tag `v*.*.*`** → [`.github/workflows/release.yml`](.github/workflows/release.yml) 自动构建并发布 GitHub Release（附 `generate_release_notes` 自动 changelog）
