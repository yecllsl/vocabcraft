# VocabCraft - 词汇学习与制作一体 MCP 工具

基于 Trae IDE CN / Trae Work CN / WorkBuddy / Opencode 的词汇学习与制作一体化解决方案。核心流程：拍照 → **多模态 LLM 直接解析图片（对话上传 > 本地路径）** / OCR 识别（后备）→ 结构化解析 → 本地保存 → 基于遗忘曲线（SM-2 算法）的复习排程 → 到期自动出考题 → 作答评分更新记忆状态。**TRAE配置可通过脚本生成适合 WorkBuddy和Opencode的配置**。

## 系统架构

项目采用 **服务层 + 配置层 + 规则层** 分离架构：

- **服务层** (`vocabcraft-mcp/`)：纯 Python MCP Server，通用，不绑定任何客户端，可独立发布
- **配置层** (`.trae/`)：定义 subagent 行为、流程与约束（单一真相源）
- **规则层**：业务规则约束词汇学习流程，开发规则约束代码开发流程

```
用户交互层
├── 对话式交互 (命令 / 自然语言)
├── 双环境: Trae IDE CN + Trae Work CN (共用 .trae/mcp.json)
    ↓
Skills 编排层 (.trae/skills/vocabcraft-*: capture / review / quiz / stats / export)
├── subagent 角色定义 (vocabcraft-*-agent: 采集 / 复习 / 考题 agent)
    ↓
MCP Tools 层 (vocabcraft-mcp)
├── 多模态 LLM 直接解析图片（首选）→ 结构化解析 → 存储 → SM-2 排程 → 考题生成 → 评分 → 统计 → 导出
    ↓
Rules 约束层 (业务规则 + 安全/合规/质量/流程规则)
    ↓
数据存储层 (本地 JSON 文件，原子写入)
```

## 技术栈

- **MCP Server**: Python 3.12+ / FastMCP / Pydantic v2
- **复习算法**: SM-2 遗忘曲线（SuperMemo 2）
- **多模态 LLM 解析（首选）**: 宿主 LLM 直接读取图片，无需额外依赖
- **OCR 引擎（可选后备）**: PaddleOCR（本地部署，无需 API Key；仅在多模态不可用时使用）
- **数据存储**: JSON 文件（本地存储，原子写入）
- **包管理**: uv（现代高速 Python 包管理器）
- **测试**: pytest + pytest-asyncio + pytest-cov
- **CI/CD**: GitHub Actions（Tests + Release）

## 开发规范

### 代码规范 (ponytail 原则)

You are a lazy senior developer. Lazy means efficient, not careless. The best code is the code never written.

Before writing any code, stop at the first rung that holds:

1. Does this need to be built at all? (YAGNI)
2. Does it already exist in this codebase? Reuse the helper, util, or pattern that's already here, don't re-write it.
3. Does the standard library already do this? Use it.
4. Does a native platform feature cover it? Use it.
5. Does an already-installed dependency solve it? Use it.
6. Can this be one line? Make it one line.
7. Only then: write the minimum code that works.

The ladder runs after you understand the problem, not instead of it: read the task and the code it touches, trace the real flow end to end, then climb.

Bug fix = root cause, not symptom: a report names a symptom. Grep every caller of the function you touch and fix the shared function once — one guard there is a smaller diff than one per caller, and patching only the path the ticket names leaves a sibling caller still broken.

Rules:

- No abstractions that weren't explicitly requested.
- No new dependency if it can be avoided.
- No boilerplate nobody asked for.
- Deletion over addition. Boring over clever. Fewest files possible.
- Shortest working diff wins, but only once you understand the problem. The smallest change in the wrong place isn't lazy, it's a second bug.
- Question complex requests: "Do you actually need X, or does Y cover it?"
- Pick the edge-case-correct option when two stdlib approaches are the same size, lazy means less code, not the flimsier algorithm.
- Mark deliberate simplifications that cut a real corner with a known ceiling (global lock, O(n²) scan, naive heuristic) with a `ponytail:` comment naming the ceiling and upgrade path.

Not lazy about: understanding the problem (read it fully and trace the real flow before picking a rung, a small diff you don't understand is just laziness dressed up as efficiency), input validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs (the platform is never the spec ideal, a clock drifts, a sensor reads off), anything explicitly requested. Lazy code without its check is unfinished: non-trivial logic leaves ONE runnable check behind, the smallest thing that fails if the logic breaks (an assert-based demo/self-check or one small test file; no frameworks, no fixtures). Trivial one-liners need no test.

### 安全规则

#### 输入验证
- 禁止信任未验证的外部数据（配置文件、CLI参数）
- 禁止未校验的文件路径，必须Path.resolve()规范化，拒绝..
- 禁止解析超限文件
- 禁止未捕获的解析异常
- 禁止使用eval()/pickle反序列化不可信数据

#### 敏感数据
- 禁止硬编码API密钥、Token、密码
- 禁止将敏感信息提交到Git
- 禁止config.example.json包含真实密钥
- 禁止将用户数据提交到Git
- 禁止在日志中记录敏感数据
- 安全场景禁止使用MD5/SHA1弱加密

#### 访问控制
- 禁止操作项目目录之外的文件
- 禁止执行不可逆的系统修改命令
- 禁止越权访问其他Agent职责范围
- .gitignore必须排除config.json
- 发现安全问题必须立即停止，修复后再继续

### 合规规则

#### 代码审计
- 必须通过ruff check扫描才能提交
- 必须通过mypy类型检查才能提交
- 必须通过bandit安全扫描才能发布
- 必须通过版本号一致性检查才能发布
- 禁止跳过CI检查直接发布
- 禁止合并未通过测试的代码

#### 许可证检查
- 禁止使用不兼容协议的依赖
- 新增依赖必须指定稳定版本号
- 禁止使用已知有漏洞的依赖版本
- 新增依赖必须先向用户请示

#### 数据隐私
- 禁止使用真实用户数据测试
- 测试必须使用脱敏或合成数据
- 备份文件禁止包含敏感信息
- 禁止在输出中泄露用户隐私数据
- 交付物归档后必须压缩并删除原始目录

### 质量规则

#### 测试覆盖
- core覆盖率必须≥80%
- agents覆盖率必须≥70%
- cli覆盖率必须≥60%
- 禁止交付无单元测试的核心代码
- 禁止Mock内部业务逻辑（保持测试真实性）
- 必须Mock外部API调用（LLM 等）

#### 开发方法论
- 禁止先写实现后补测试，必须TDD顺序（RED→GREEN→REFACTOR）
- 禁止无失败测试就写生产代码
- 禁止未经验证就声称完成，必须运行验证命令拿证据
- 禁止跳过根因分析直接修复Bug，必须先systematic-debugging
- 禁止需求不明确时直接编码，必须先brainstorming澄清

#### 代码规范
- 禁止裸Exception，必须使用自定义异常
- 禁止# type: ignore，必须写正确类型注解
- 禁止Dict[str, Any]，使用TypedDict或dataclass
- 禁止print()调试，使用logging
- 禁止LazyFrame过早collect()
- 禁止直接实例化核心组件，必须get_context()
- 禁止可变默认参数def f(x=[])
- 禁止函数超50行、嵌套超4层

#### 文档完整
- 公共API必须有文档字符串
- 新增功能必须更新CHANGELOG
- 架构变更必须更新架构设计说明书
- 版本发布必须同步更新AGENTS.md

### 流程规则

#### 分支策略（单人模式）
- 禁止在未完成功能时推送Tag
- 禁止跳过CI检查直接发布
- Commit格式必须遵循：`<type>(<scope>): <subject>`
- feature分支可选：小改动可直接在main开发，大功能建议用feature分支

#### 合并策略（GitHub分支保护适配）
- main分支受GitHub保护规则约束，禁止force-push
- main分支保护规则要求：禁止包含merge commit
- 功能分支合并到main必须使用 `git merge --squash` 策略

#### 开发流程（嵌入全局方法论）
- 功能开发必须遵循TDD循环：先写失败测试 → 写实现 → 重构
- Bug根因不明时，必须先执行systematic-debugging定位根因，禁止盲目修改
- 每次commit前必须运行验证命令（lint/test/typecheck），拿证据
- 声称完成必须有验证证据，禁止"应该没问题"式声称
- 需求不明确时，必须先brainstorming澄清，禁止直接编码

#### 发布准入（单人模式）
- 版本号必须保持一致（pyproject.toml/README.md/CHANGELOG.md）
- 版本号更新后必须先推送main，等待CI通过后再创建Tag
- 禁止在CI未通过时创建Tag

#### 变更记录
- 版本发布必须更新CHANGELOG.md
- 版本号必须保持pyproject.toml/README.md/CHANGELOG.md一致

## 业务规则

### 采集规则

1. **对话多模态 LLM 直接解析图片（首选）**：优先使用 `parse_vocab()` 无参数调用，宿主 LLM 直接读取对话上下文中的图片完成结构化解析
2. **本地路径多模态（次选）**：对话上传不可用时，使用 `parse_vocab(image_path=...)` 读取本地图片
3. **OCR 为降级后备**：多模态模式不可用时，降级为 OCR 识别 + 文本解析流程
4. OCR 失败时降级为手动输入，禁止直接报错终止流程
5. 图片文件存储在本地 `data/images/`，禁止上传到任何外部服务
6. vocab_id 格式：`vocab_YYYYMMDD_NNN`，NNN 按当日已有编号递增
7. 解析结果需用户确认后才调用 `save_vocab` 保存
8. **word（词形）和 definitions（释义）为必填字段**，不允许为 null 保存——缺失会导致后续出题与复习不可用
   - `definitions` 为 `list[Definition]`，每项 `{text, examples}` 内嵌该释义的关联例句
9. 若 AI 解析未能完成结构化，必须使用占位值填充并提示用户在确认时修改：word 标记"待确认"、definitions 标记"待确认"
10. 保存词汇时必须同时初始化 SM-2 记忆状态（repetitions=0、easiness=2.5、next_review_date=次日）
11. **多义词必须按义项关联例句**：每条例句挂在对应义项的 `definitions[i].examples` 字段下，禁止所有例句堆在某一条释义下或顶层
12. **Excel 文件批量导入（新增）**：支持从 .xlsx 文件批量导入词汇，使用 `import_xlsx_vocab` 工具
    - 表格格式：word（词汇）、phonetic（音标）、part_of_speech（词性）、definitions（释义）、examples（例句）、language（语言）
    - 多义词处理：每个义项占一行，相同 word 标识同一词汇
    - 必填字段：word 和 definitions 不能为空
    - 错误处理：跳过格式错误的词汇，继续处理其他词汇，最后报告错误详情

### 复习规则

1. 复习排程由 `vocabcraft-mcp/src/vocabcraft_mcp/algorithms.py` 的**改良版 SM-2** 驱动（EF 初始 2.5、下限 1.3；通过走 1→6→×EF；失败 reps 归零、间隔=1 天）。
2. grade 评分标准 0-5：5完全记住/4记住略迟疑/3勉强记住/2部分记错/1几乎全忘/0完全忘记
3. grade<3 时必须重置复习周期（回到短间隔），不得递增间隔
4. 到期词汇（`next_review_date <= 今天`）必须复习，用户跳过时需记录原因且不延后日期
5. 每次评分后必须更新 SM-2 记忆状态：repetitions、easiness、next_review_date
6. 连续出题不得使用相同题型超过 2 次（除非用户指定），保证题型多样性
7. 评分客观，按既定规则给分，禁止因用户情绪或求情调整 grade
8. 选择题干扰项应来自同词性或近义词汇，避免明显错误选项
9. 填空题优先使用词汇自带 examples，无例句时降级为释义题
10. 复习结束必须汇总：题数、均分、grade<3 薄弱词列表、下次复习日期分布

### 交互规则

1. 命令格式：`/capture`、`/review`、`/quiz`、`/stats`、`/export`
2. 自然语言关键词：录词/复习/出题/统计/导出
3. 每次操作结果必须给出明确反馈（成功/失败/降级提示）
4. 错误发生时提供降级方案而非直接报错
5. 多模态 LLM 解析失败时允许降级为 OCR 或手动输入词汇文本
6. AI 解析异常时提供友好提示和重试机制
7. 解析结果、分类、导出操作必须经用户确认后才执行
8. 长流程（如批量复习）应展示进度，避免用户困惑

### 数据安全规则

1. 所有数据仅存储在本地，禁止上传到任何外部服务
2. 图片文件存储在项目目录下 `data/images/`，不外传
3. 导出数据前必须经用户确认，导出文件保存到本地 `data/exports/`
4. 不记录用户姓名等个人身份信息
5. OCR 本地部署，不调用外部 OCR API
6. 导出失败不得损坏原数据（导出为只读原数据操作）
7. 记忆状态（repetitions/easiness/next_review_date）属于用户学习数据，仅本地存储与更新

## 命令参考

### /capture — 词汇采集

- **触发条件**: 命令 `/capture` 或自然语言"录词/录入词汇/添加词汇/拍照录词/采集词汇"
- **调用 Skill**: `vocabcraft-capture`
- **执行流程**: 获取输入(对话上传图片优先 → 本地路径次选) → **多模态 LLM 直接解析图片（首选：`parse_vocab()` 无参数对话模式 / 次选：`parse_vocab(image_path=...)` 本地路径模式）** → 用户确认 → `save_vocab` 保存(生成 `vocab_id`: `vocab_YYYYMMDD_NNN`) → 初始化 SM-2 记忆状态(repetitions=0, easiness=2.5, next_review_date=次日)
- **降级流程**: 对话多模态不可用 → 本地路径多模态 → `ocr_recognize` OCR 识别 → `parse_vocab(ocr_text=...)` 文本解析 → 手动输入
- **关键 MCP Tools**: `parse_vocab`(三模式：无参数对话多模态/`image_path`本地路径多模态/`ocr_text`文本解析)、`ocr_recognize`(OCR 后备)、`save_vocab`(保存并初始化复习)
- **约束**: 对话多模态 LLM 解析为首选，本地路径为次选，OCR 为降级后备；解析结果必须经用户确认后才保存；OCR 失败必须降级手动输入，不报错终止；必填字段 word + definitions 不允许为空
- **新增模式**: Excel 文件批量导入
  - **触发条件**: 用户说"导入Excel文件"、"从表格添加词汇"、"导入词汇表"
  - **调用 Tool**: `import_xlsx_vocab`
  - **执行流程**: 获取.xlsx文件路径 → `import_xlsx_vocab` 解析文件 → 展示解析结果 → 用户确认 → 保存记录
  - **约束**: 表格必须包含 word 和definitions列；多义词每个义项占一行；错误词汇跳过并报告

### /review — 复习排程

- **触发条件**: 命令 `/review` 或自然语言"复习/复习词汇/该复习了/今天复习什么"
- **调用 Skill**: `vocabcraft-review`
- **执行流程**: `schedule_review` 查询到期词汇(next_review_date <= 今天) → 展示复习概览 → 逐词循环(`generate_quiz` 出题 → 用户作答 → `grade_quiz` 评分 grade 0-5 → 即时反馈) → 复习汇总(题数/均分/薄弱词/下次复习日期)
- **关键 MCP Tools**: `schedule_review`(查询到期词汇)、`generate_quiz`(生成考题)、`grade_quiz`(评分并更新记忆状态)
- **约束**: 到期词汇必须全部复习，跳过需记录原因；grade<3 重置复习周期；评分客观，不因用户情绪调整

### /quiz — 考题与评分

- **触发条件**: 命令 `/quiz [vocab_id]` 或自然语言"出题/考我/测试/练一练/考题"
- **调用 Skill**: `vocabcraft-quiz`
- **执行流程**: 确定出题范围(指定 vocab_id 或随机) → 确定题型(用户指定或轮换) → `generate_quiz` 生成考题 → 用户作答 → `grade_quiz` 评分 → 展示反馈 → 询问是否继续
- **关键 MCP Tools**: `generate_quiz`(生成指定题型考题)、`grade_quiz`(评分并更新记忆状态)
- **约束**: 连续出题不得使用相同题型超过 2 次(除非用户指定)；评分客观；干扰项来自同词性或近义词；填空题优先用词汇自带 examples

### /stats — 统计分析

- **触发条件**: 命令 `/stats [dimension]` 或自然语言"统计/词汇量/掌握度/复习进度/学习情况"
- **调用 Skill**: `vocabcraft-stats`
- **执行流程**: 确定统计维度(overview/mastery/date/review，默认概览) → `get_statistics` 按维度聚合 → Markdown 表格展示
- **关键 MCP Tools**: `get_statistics`(按维度聚合统计)
- **约束**: 统计数据只读，不修改任何词汇记录；输出为 Markdown

### /export — 数据导出

- **触发条件**: 命令 `/export [format]` 或自然语言"导出/备份数据/导出词汇/导出 csv"
- **调用 Skill**: `vocabcraft-export`
- **执行流程**: 确定导出格式(json 默认/csv) → 展示导出范围与格式请用户确认 → `export_data` 导出 → 返回文件路径
- **关键 MCP Tools**: `export_data`(导出词汇数据到文件)
- **约束**: 导出前必须经用户确认；导出文件保存到本地 `data/exports/`，不外传；导出失败不得损坏原数据

## MCP Tools 参考

| Tool | 用途 | 关键参数 |
|------|------|----------|
| `parse_vocab` | 结构化解析词汇(词形/音标/释义/例句)，**三模式：对话多模态 > 本地路径多模态 > OCR 文本** | 无参数(对话多模态)/`image_path`(本地路径多模态)/`ocr_text`(文本后备) |
| `ocr_recognize` | OCR 识别图片中的词汇文本（降级后备） | `image_path` |
| `save_vocab` | 保存词汇并初始化记忆状态 | 解析后的结构化数据 |
| `schedule_review` | 查询到期需复习的词汇列表 | 截止日期(默认今天) |
| `generate_quiz` | 为单个词汇生成指定题型的考题 | `vocab_id`、`quiz_type` |
| `grade_quiz` | 评分用户作答并更新记忆状态 | `vocab_id`、用户作答 |
| `get_statistics` | 按维度聚合统计 | `group_by` |
| `export_data` | 导出词汇数据到文件 | `format` |

## Agent 行为约束

主Agent承担工作流协调者（Coordinator）职责，除自身开发能力外，必须遵循以下约束：

### 职责

- 接收用户需求，按决策树判断复杂度级别
- 根据级别选择工作流入口和执行策略
- 委派SubAgent执行具体任务
- 执行质量门控检查
- 处理异常和阶段回退

### 禁止行为

- 跳过brainstorming直接编码（简单任务除外）
- 在未验证的情况下声明完成
- 跳过代码审查直接合并
- 修复循环>3次仍不回退规划阶段
- 无目标探索代码库

### 门控职责

在以下关键节点执行门控检查：

1. **实现前** — 确认规格审批、计划审批、环境隔离
2. **实现中** — 确认TDD循环完成、self-review完成
3. **验证前** — 确认测试套件通过、构建成功
4. **合并前** — 确认验证证据新鲜(<5分钟)、所有审查通过

### 实施层级

| 层级  | 实施位置    | 示例            |
| --- | ------- | ------------- |
| 输入层 | 请求入口    | 过滤恶意输入、权限验证   |
| 执行层 | Agent行为 | 禁止危险命令、限制文件访问 |
| 输出层 | 结果检查    | 敏感信息脱敏、格式验证   |
| 审计层 | 日志记录    | 操作追踪、合规审计     |
