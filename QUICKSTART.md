# VocabCraft 快速入门

## 3 步开始使用

### 第 1 步：下载并解压

从 [GitHub Releases](https://github.com/yecllsl/vocabcraft/releases) 下载最新版本，按需选择格式：

- **Windows**：`VocabCraft-vX.Y.Z.zip`（用资源管理器/7-Zip 解压）
- **现代 Linux/macOS**：`VocabCraft-vX.Y.Z.tar.zst`（`tar --zstd -xf` 或 `zstd -d` + `tar -xf`）
- **兼容老旧系统**：`VocabCraft-vX.Y.Z.tar.gz`（`tar -xzf`）

解压到任意目录（如 `D:\vocabcraft\` 或 `~/vocabcraft/`）。

### 第 2 步：安装依赖

```powershell
# Windows: 右键 install.ps1 → "使用 PowerShell 运行"
.\install.ps1
```

```bash
# Linux/macOS:
chmod +x install.sh && ./install.sh
```

> 📷 图片词汇采集由**宿主 LLM 多模态直接解析**（对话上传图片优先、本地路径次之、文本兜底），无需安装任何 OCR 引擎。手动录入、复习、考题、统计、导出均不依赖额外模型。

### 第 3 步：配置 Agent 运行时

VocabCraft 支持多个 Agent 运行时，选择你使用的环境进行配置：

#### Trae IDE CN / Trae Work CN

1. 用 **Trae IDE CN** 或 **Trae Work CN** 打开项目文件夹
2. 进入 **设置 → MCP**
3. 打开 **"启用项目级 MCP"** 开关
4. 重启 Trae

> 💡 两个环境读取同一份由 `.agents/runtime/trae.json` 同步生成的 `.trae/mcp.json`，无需单独配置。

#### OpenCode

1. 运行安装脚本：
   ```powershell
   .\install.ps1 -AgentRuntime opencode  # Windows
   bash install.sh --agent-runtime opencode  # Linux/macOS
   ```

2. 在项目目录运行 `opencode`

#### Goose

1. 运行安装脚本：
   ```powershell
   .\install.ps1 -AgentRuntime goose  # Windows
   bash install.sh --agent-runtime goose  # Linux/macOS
   ```

2. 用 Goose 打开项目文件夹，会自动读取 `.goose/config.yaml` 加载 vocabcraft-mcp

### 第 4 步：开始使用

输入 `/capture`、`/review`、`/quiz`、`/stats` 或 `/export` 即可！

---

## 5 分钟快速体验

### 1. 采集第一个词汇

**命令方式:**
```
/capture
```

**自然语言方式:**
```
帮我录入这页单词（附上图片路径）
```

**操作流程:**
1. 执行 `/capture` 命令
2. 输入或粘贴词汇图片路径
3. AI 多模态结构化解析（宿主 LLM 直接读图，输出单词、音标、词性、释义、例句）
4. 确认或修改解析结果
5. 保存词汇记录

### 2. 查看到期复习

**命令方式:**
```
/review
```

**自然语言方式:**
```
我该复习什么？
```

**操作流程:**
1. 执行 `/review` 命令
2. AI 按 SM-2 遗忘曲线筛选到期词汇
3. 展示今日复习清单（按记忆强度排序）
4. 展示薄弱词汇排名

### 3. 出考题作答

**命令方式:**
```
/quiz
```

**自然语言方式:**
```
考考我
```

**操作流程:**
1. 执行 `/quiz` 命令
2. AI 为到期词汇生成考题（选择/填空/拼写/释义/文言文释义五种题型）
3. 逐题作答
4. AI 评分并反馈
5. 自动更新 SM-2 记忆参数（易度、间隔、重复次数）
6. 重新排程下次复习时间

**文言文词汇出题（v0.3.0 新增）:**

针对 `language=zh_classical` 的文言文词汇，系统采用特殊出题方式：
- 给出一条例句，高亮目标词
- 提供 4 个词性选项（单选）
- 用户填写释义（格式：`词性|释义`，如 `n.|兵器`）
- 词性大小写不敏感，释义严格匹配
- 多义词按复习历史轮询，确保每个义项都被考查

### 4. 查看词汇统计

**命令方式:**
```
/stats
```

**自然语言方式:**
```
看看我的词汇掌握情况
```

**操作流程:**
1. 执行 `/stats` 命令
2. AI 展示多维度统计：
   - 词汇总量 / 待复习数
   - 掌握度分布
   - 遗忘曲线趋势
3. 可以导出为 JSON 或 CSV

## 常用示例

### 示例 1: 拍照录入词汇

```
/capture
> 请提供词汇图片路径: C:\Users\...\vocab_page.jpg

[AI] OCR 识别完成
原始文本: abandon /əˈbændən/ v. 放弃；抛弃

[AI] 结构化解析:
- 单词: abandon
- 音标: /əˈbændən/
- 词性: v.
- 释义: 放弃；抛弃
- 例句: (待补充)

> 确认解析结果? (y/n): y

[AI] ✅ 词汇已保存
vocab_id: vocab_20260723_001
保存路径: vocabcraft-mcp/data/
下次复习: 1 天后（SM-2 初始排程）
```

### 示例 2: 出考题作答

```
/quiz

[AI] 今日考题（3 道到期词汇）:

Q1. 释义 → 单词
   "放弃；抛弃" 对应的单词是？
> 你的答案: abandon

[AI] ✓ 正确！
   记忆状态更新: 间隔 1天 → 3天，易度 2.5 → 2.6

Q2. 单词 → 释义
   "abundant" 的释义是？
> 你的答案: 丰富的；大量的

[AI] ✓ 正确！
   记忆状态更新: 间隔 1天 → 3天

Q3. 例句填空
   "The government decided to _____ the project."
   （从到期词汇中选择）
> 你的答案: abandon

[AI] ✗ 错误，正确答案: cancel
   记忆状态更新: 间隔 1天 → 1天（重置），易度 2.5 → 2.3

[AI] ✅ 考题完成
本次得分: 2/3 (67%)
下次复习已重新排程
```

### 示例 3: 查看统计

```
/stats

[AI] 词汇统计概览:
┌─────────────────────────────────────┐
│ 📊 总览                             │
│ - 词汇总量: 120                     │
│ - 今日待复习: 8                     │
│ - 本周新增: 15                      │
├─────────────────────────────────────┤
│ 📈 掌握度分布                       │
│ - 已掌握 (间隔>21天): 45 (37.5%)    │
│ - 熟悉中 (间隔 3-21天): 50 (41.7%)  │
│ - 学习中 (间隔 1-3天): 25 (20.8%)   │
├─────────────────────────────────────┤
│ 🔴 薄弱词汇 (Top 5)                 │
│ 1. abandon (易度 1.8)               │
│ 2. abundant (易度 2.0)              │
│ 3. ...                              │
└─────────────────────────────────────┘

> 是否导出? (y/n): n
```

## 小技巧

### 1. 手动录入（无需 OCR）

不安装 OCR 也能用 `/capture`，直接手动输入词汇信息即可。

### 2. 按状态筛选复习

```
/review
> 请选择状态过滤（直接回车跳过）: 学习中
```

只复习记忆强度较低的词汇。

### 3. 数据导出

```
/export
> 请选择导出格式: csv
> 请选择过滤条件（直接回车跳过）:
```

导出全部词汇为 CSV 格式（适合 Excel 查看）。

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| 安装脚本报错 "uv 未安装" | 安装 uv：`irm https://astral.sh/uv/install.ps1 \| iex` |
| MCP Server 不生效 | 确认启用项目级 MCP → 重启 Trae |
| 路径变量不替换 | 运行 `.\install.ps1 -FixPath` 修复路径 |
| 依赖安装失败 / `uv sync` 报错 | 删除 `.venv` 后重试 `uv sync`；确认 Python ≥ 3.12；网络问题检查代理 |
| Skills 不生效 | 重启 Trae → 检查 .agents/skills/vocabcraft-* 目录 |
| 多运行时配置冲突 | 不会冲突，各运行时共用同一份 `.agents/` 配置（经 `scripts/sync-agent-configs` 同步），详见 [DEPLOY.md](DEPLOY.md) |

## 下一步

- 📖 查看 [完整部署指南](DEPLOY.md)（含多运行时详细配置）
- 📚 查看 [项目 README](README.md)
