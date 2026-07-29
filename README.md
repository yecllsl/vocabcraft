# VocabCraft - 词汇学习与制作一体 MCP 工具

基于 Trae IDE CN / Trae Work CN 的词汇学习与制作一体化解决方案。核心流程：拍照 OCR 识别词汇 → AI 结构化解析 → 本地保存 → 基于遗忘曲线（SM-2 算法）的复习排程 → 到期自动出考题 → 作答评分更新记忆状态。**一份配置同时运行在 TRAEWORK CN 与 TRAEIDE CN 双环境**。

## 核心功能

- 📷 **拍照采集**: 拍照 + OCR 识别 + AI 结构化解析词汇（单词、音标、词性、释义、例句）
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
└── 双环境: Trae IDE CN + Trae Work CN (共用 .trae/mcp.json)
    ↓
Skills 编排层 (.trae/skills/vocabcraft-*: capture / review / quiz / stats / export)
├── subagent 角色定义 (.trae/agents/vocabcraft-*-agent: 采集 / 复习 / 考题 agent)
    ↓
MCP Tools 层 (vocabcraft-mcp)
├── OCR 识别 → 结构化解析 → 存储 → SM-2 排程 → 考题生成 → 评分 → 统计 → 导出
    ↓
Rules 约束层 (.trae/rules/vocabcraft-* 业务规则，与 BMAD 工作流规则共存)
    ↓
数据存储层 (本地 JSON 文件，原子写入)
```

## 技术栈

- **MCP Server**: Python 3.12+ / FastMCP / Pydantic v2
- **复习算法**: SM-2 遗忘曲线（SuperMemo 2）
- **OCR 引擎（可选）**: PaddleOCR（本地部署，无需 API Key；不安装也能用基础功能）
- **数据存储**: JSON 文件（本地存储，原子写入）
- **包管理**: uv（现代高速 Python 包管理器）
- **测试**: pytest + pytest-asyncio + pytest-cov
- **CI/CD**: GitHub Actions（Tests + Release）

## 快速安装

### 前置要求

- Python 3.12+
- [uv 包管理器](https://docs.astral.sh/uv/)（Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`）
- Trae IDE CN 或 Trae Work CN（两者均支持，双环境共用同一份配置）

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

> ⏱️ 首次安装会询问是否安装 OCR 引擎（PaddleOCR + PaddlePaddle 约 1.5 GB）。**仅当需要 `/capture` 拍照录入词汇时才需要**。手动录入、复习、考题等功能无需 OCR。

#### 3. 在 Trae 中配置（双环境操作一致）

1. 用 Trae IDE CN **或** Trae Work CN 打开解压后的文件夹
2. 进入 **设置 → MCP**
3. 打开 **"启用项目级 MCP"** 开关
4. 重启 Trae

> 💡 项目级 MCP 配置已内置于 `.trae/mcp.json`，使用 `${workspaceFolder}` 变量自动适配路径，**两个环境共用同一份配置**，无需手动填写。

#### 4. 开始使用

```
/capture  - 拍照录入词汇
/review   - 查看到期复习清单
/quiz     - 出考题并作答评分
/stats    - 查看词汇统计
/export   - 导出词汇数据
```

### 可选：安装 OCR 引擎

OCR 引擎（PaddleOCR + PaddlePaddle，约 1.5 GB）用于图片词汇识别，**非必需**。仅当使用 `/capture` 拍照录入时才需要安装：

```bash
cd vocabcraft-mcp
uv sync --extra ocr
```

未安装时调用 OCR 会得到友好提示，不影响其他功能。

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
| `/capture` | 拍照录入词汇（OCR 识别 + AI 结构化） |
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
拍照 OCR ──→ AI 结构化解析 ──→ 本地保存
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
├── vocabcraft-mcp/                       # MCP Server 服务层（Python）
│   ├── src/vocabcraft_mcp/
│   │   ├── server.py                      # FastMCP 服务入口（main 函数）
│   │   ├── models.py                      # Pydantic v2 数据模型（词汇/考题/记忆状态）
│   │   ├── storage.py                     # JSON 存储引擎（原子写、部分更新）
│   │   ├── algorithms.py                  # SM-2 遗忘曲线算法
│   │   ├── tools/                         # MCP Tools（OCR / 解析 / CRUD / 排程 / 考题 / 评分 / 统计 / 导出）
│   │   ├── prompts/                       # AI Prompt 模板（词汇解析 / 考题生成 / 评分）
│   │   └── resources/                     # MCP Resources（遗忘曲线 / 语言包 / 考题模板）
│   ├── tests/                             # 测试套件（单元 + 集成）
│   ├── data/                              # 运行时数据（被 .gitignore，保留 .gitkeep）
│   │   ├── vocabs/                        # 词汇记录 JSON
│   │   ├── reviews/                       # 复习排程 JSON
│   │   ├── quizzes/                       # 考题与作答 JSON
│   │   ├── images/                        # OCR 图片
│   │   └── exports/                       # 导出文件
│   ├── pyproject.toml                     # Python 项目配置（入口 vocabcraft-mcp）
│   └── uv.lock                            # 依赖锁定文件
│
├── .trae/                                  # 配置层（subagent 配置 + BMAD 共存）
│   ├── mcp.json                            # 项目级 MCP 配置（双环境共用，${workspaceFolder} 适配）
│   ├── hooks.json                          # Trae 钩子配置
│   ├── skill-config.json                   # Skills 配置
│   ├── 开发流程规范.md                     # 开发流程统一手册
│   ├── agents/                             # subagent 角色定义（vocabcraft-* + BMAD）
│   ├── commands/                           # 命令定义（vocabcraft-* + BMAD）
│   ├── documents/                          # 项目文档（发版计划等）
│   ├── skills/                             # Skills 源文件
│   │   ├── vocabcraft-capture/             # /capture 拍照录入
│   │   ├── vocabcraft-review/              # /review 复习排程
│   │   ├── vocabcraft-quiz/                # /quiz 考题与评分
│   │   ├── vocabcraft-stats/               # /stats 统计
│   │   └── vocabcraft-export/              # /export 导出
│   └── rules/                              # 规则源文件
│       ├── vocabcraft-*.md                 # 词汇业务规则（采集/复习/数据安全/交互等）
│       ├── ponytail.md                     # BMAD: 懒惰高级开发模式
│       ├── project-rules.md                # BMAD: 项目总规则
│       ├── security-rules.md               # BMAD: 安全规则
│       ├── compliance-rules.md             # BMAD: 合规规则
│       ├── quality-rules.md                # BMAD: 质量规则
│       └── process-rules.md                # BMAD: 流程规则
│
├── .github/
│   └── workflows/
│       ├── test.yml                        # CI：单元 + 集成测试（3.12/3.13）
│       └── release.yml                     # Release：push tag → 自动打包 + 上传
│
├── scripts/                                # 开发者工具
│   ├── build-release.ps1                   # Windows 发布包构建（PowerShell）
│   └── build-release.sh                    # Linux/macOS 发布包构建（bash，与 .ps1 逻辑对齐）
├── install.ps1                             # Windows 安装脚本（可选装 OCR）
├── install.sh                              # Linux/macOS 安装脚本（可选装 OCR）
├── QUICKSTART.md                           # 5 分钟快速上手
├── DEPLOY.md                               # 详细部署指南
├── README.md                               # 本文件
└── LICENSE                                 # MIT
```

## 架构设计说明

### 分层分离原则

本项目采用 **"服务层 + 配置层"** 分离架构：

| 层级 | 位置 | 用途 |
|------|------|------|
| **服务层** | `vocabcraft-mcp/` | 纯 Python MCP Server，通用，不绑定任何客户端，可独立发布 |
| **配置层** | `.trae/` | Trae 专用配置，定义 subagent 行为、流程与约束（单一真相源） |

### subagent 配置层定义

`.trae/` 目录是 subagent 配置层，定义了 AI 在 Trae 环境中的行为：

- **`agents/`** — subagent 角色定义（vocabcraft-* 业务 agent）
- **`commands/`** — 命令入口定义（`/capture` `/review` `/quiz` `/stats` `/export`）
- **`skills/`** — 流程编排（每个 skill 对应一个命令的完整执行流程）
- **`rules/`** — 约束规则（业务规则 + 安全/合规/质量/流程规则）
- **`mcp.json`** — MCP Server 连接配置

### BMAD 工作流共存

`.trae/rules/` 目录下同时存在两类规则，互不冲突：

1. **vocabcraft-\* 业务规则** — 词汇学习业务的专属约束（采集规则、复习规则、数据安全、交互规范等）
2. **BMAD 工作流规则** — 通用开发方法论（`ponytail.md` 懒惰开发模式、`project-rules.md` 项目总规则、`security-rules.md` / `compliance-rules.md` / `quality-rules.md` / `process-rules.md`）

两者各司其职：业务规则约束词汇学习流程，BMAD 规则约束代码开发流程。发布包构建时**只打包 vocabcraft-\* 业务文件**，不打包 BMAD 既有文件（详见 `scripts/build-release.sh`）。

### 双环境适配

项目同时支持 **Trae IDE CN** 与 **Trae Work CN** 两个环境，核心机制：

1. **共用 `.trae/mcp.json`** — 使用 `${workspaceFolder}` 变量指向项目根目录，两个环境都会自动替换为实际路径
2. **同一份 Skills/Rules** — 两个环境读取相同的 `.trae/` 配置，行为一致
3. **路径回退方案** — 若 Trae 版本不支持 `${workspaceFolder}` 变量，运行 `.\install.ps1 -FixPath`（Windows）或 `./install.sh --fix-path`（Linux/macOS）自动替换为绝对路径

### 为什么要分离？

1. **职责清晰**: 代码归代码，配置归配置
2. **可复用**: `vocabcraft-mcp/` 可单独在其他 MCP 客户端（如 Cursor）中使用
3. **单一真相源**: Skills/Rules/agents/commands 配置直接在 `.trae/` 下编辑，无需同步步骤
4. **Git 友好**: 项目结构一目了然，`.trae/` 即 Trae 配置根目录
5. **双环境友好**: 一份配置，两个环境同时运行

## 数据安全

- ✅ 所有数据仅存储在本地
- ✅ OCR 本地部署，不调用外部 API
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

1. 确认已在 Trae 中打开 **"启用项目级 MCP"** 开关
2. 确认已重启 Trae
3. 如果 `${workspaceFolder}` 变量不被支持，运行 `.\install.ps1 -FixPath` 自动修复路径

### Q: Trae IDE CN 和 Trae Work CN 能否同时使用？

可以。两个环境共用同一份 `.trae/mcp.json`（使用 `${workspaceFolder}` 自动适配路径），在任一环境打开项目文件夹并启用项目级 MCP 即可。详见 [DEPLOY.md](DEPLOY.md)。

### Q: OCR / PaddleOCR 安装失败

- 确认 Python 版本 >= 3.12
- 确认网络畅通（需下载模型文件）
- OCR 为**可选依赖**，默认 `uv sync` 不会安装。需要时执行：`cd vocabcraft-mcp && uv sync --extra ocr`
- 若仅使用手动录入、复习、考题等基础功能，**无需安装 OCR**

## License

MIT License

## Contributing

欢迎提交 Issue 和 Pull Request！

## 测试与开发

### 本地运行测试

```bash
cd vocabcraft-mcp

# 单元 + 集成测试（不装 paddleocr，最快）
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
