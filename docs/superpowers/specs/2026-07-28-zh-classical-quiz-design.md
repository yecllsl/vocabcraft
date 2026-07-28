# 文言文词汇出题方式设计文档

## 1. 背景与目标

项目当前默认的出题方式更适合德语等拼音文字：给出单词，让用户拼写或写出现代汉语释义。对于文言文（`language=zh_classical`）实词，用户需要的是「给出例句，判断词性并写出释义」的考查方式，且每个实词的多个义项必须被逐一覆盖。

本设计在不变更核心数据模型的前提下，将 `zh_classical` 词汇的默认「释义」题改造为适合文言实词的出题形态，并同时覆盖主动出题（`/quiz`）与到期复习（`/review`）两条路径。

## 2. 设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 题型 | 复用现有 `quiz_type="释义"` | 用户明确选择「替换 zh_classical 默认释义题」，不引入新枚举，改动面最小 |
| 多义项覆盖 | 分题轮询 | 每次出题只考查一个义项，依据复习记录选择最少被考的义项 |
| 作答方式 | Web 单选词性 + 填写释义 | Web 端无 LLM，必须客观评分 |
| 评分方式 | 客观精确匹配 | 词性大小写不敏感，释义严格一致 |
| 例句呈现 | 原句高亮目标词 | 符合用户「给出例句」的字面需求，不挖空 |
| 词性选项 | 正确词性 + 固定池干扰项 | 从词汇自身 `part_of_speech` 出发，混入固定文言词性池中的干扰项 |

## 3. 数据模型与题型约定

沿用现有 `Quiz` 模型，不新增字段、不新增枚举值。通过以下约定识别文言释义题：

- 触发条件：`vocab.structured.language == "zh_classical"` 且 `quiz.quiz_type == "释义"`。
- `Quiz.definition_index`：指向本次考查的义项下标（已有字段）。
- `Quiz.options`：在文言释义题中存储词性候选列表（如 `["n.", "v.", "adj.", "adv."]`），用于 Web 单选。
- `Quiz.answer`：编码为 `"词性|释义文本"`，例如 `"n.|兵器"`。

词汇模型无需改动。`StructuredVocab.part_of_speech` 继续作为该词汇的主词性；不同义项不单独记录词性（用户选择保持现状）。

## 4. 出题逻辑

### 4.1 定义选择（分题轮询）

`tools/quiz.generate_quiz(vocab_id, quiz_type)` 中，当检测到 `zh_classical` 释义题时：

1. 读取该词汇所有 `ReviewRecord`，按 `definition_index` 分组统计每个义项的复习次数。
2. 选择复习次数最少的义项作为本次考查目标；次数相同时按下标升序取第一个。
3. 记录该义项下标到 `Quiz.definition_index`。

### 4.2 题干生成

针对选中的义项 `definition = definitions[definition_index]`：

- 若该义项有例句，取第一条例句作为题干，并将目标词用 `<mark>` 标签高亮。
- 若该义项无例句，题干退化为：`请写出「{word}」在义项「{definition.text}」中的词性与释义`。
- 题干末尾追加提示：`请选择词性并填写释义`。

### 4.3 词性选项生成

固定文言词性池：

```text
{"n.", "v.", "adj.", "adv.", "pron.", "num.", "量", "连", "介", "助", "叹"}
```

生成规则：

1. 正确选项 = 词汇顶层 `part_of_speech`（去空白）。
2. 从词性池中排除正确项后，随机抽取 3 个干扰项。
3. 最终 `options` 共 4 项，顺序随机打乱。

### 4.4 答案编码

`Quiz.answer` 设置为：

```python
f"{vocab.structured.part_of_speech.strip()}|{definition.text.strip()}"
```

## 5. 评分逻辑

`tools/quiz.grade_quiz(quiz_id, response)` 中，当检测到文言释义题时：

1. 使用 `response.partition("|")` 拆分为 `pos` 与 `definition` 两部分（只认第一个 `|`，释义中即使含 `|` 也能正常解析）；若无 `|`，直接判错。
2. 按同样规则从 `Quiz.answer` 解析出正确 `expected_pos` 与 `expected_definition`。
3. 同时满足以下两条视为正确：
   - `pos.strip().lower() == expected_pos.strip().lower()`（词性大小写不敏感）
   - `definition.strip() == expected_definition.strip()`（释义严格一致，仅去首尾空白）
4. 正确则 `grade=5`，否则 `grade=0`。
5. 仍按现有流程调用 `compute_next_review` 更新记忆状态，并写入 `ReviewRecord`（透传 `definition_index`）。

> Web 层提交前需将表单中的 `pos` 与 `definition` 拼接为 `"pos|definition"` 字符串，再调用 `grade_quiz`。

## 6. Web 界面

### 6.1 服务层：`web/services.py`

`generate_web_quiz(vocab_id, quiz_type)` 中新增 `zh_classical` 释义分支：

- `question`：例句高亮 + 提示文本。
- `options`：4 个词性选项。
- `answer`：`"词性|释义"`。
- 返回的 `quiz` 字典中额外注入 `language` 字段（取词汇语言），供模板判断渲染模式。

### 6.2 路由层：`web/routes/quiz.py`

`/api/quiz/{quiz_id}/grade`：

- 读取表单字段 `pos` 与 `definition`。
- 若存在，拼接为 `"pos|definition"` 作为 `response`。
- 若不存在，回退到原有的单字段 `response`。

批量复习路由 `/api/review/batch/.../grade` 同样处理 `pos` + `definition` 表单字段。

### 6.3 模板：`partials/quiz.html` 与 `partials/batch_review_item.html`

当 `quiz.options` 存在且 `quiz.language == "zh_classical"` 时（Web 服务层已注入 `language`），渲染：

```html
<div class="quiz-question">{{ quiz.question }}</div>

<div class="quiz-options">
  {% for option in quiz.options %}
  <label class="quiz-option">
    <input type="radio" name="pos" value="{{ option }}" required>
    <span>{{ option }}</span>
  </label>
  {% endfor %}
</div>

<div class="form-group">
  <input type="text" name="definition" class="quiz-input" placeholder="请填写释义" required autocomplete="off">
</div>
```

现有样式复用 `.tag-quiz-释义` 与 `.quiz-options`，不新增大量 CSS。

## 7. Skill 与 MCP 交互

### 7.1 Skill 文档更新

`.trae/skills/vocabcraft-quiz/skill.md`：

- 在「题型对照」表中补充：

| 题型 | 适用语言 | 题目形式 | 评分 |
|------|----------|----------|------|
| 释义 | zh_classical | 例句 + 选择词性 + 填写释义 | 词性、释义均正确得 5 分，否则 0 分 |

- 在「Common Mistakes」中补充：
  - 作答格式必须为 `"词性|释义"`（如 `n.|兵器`）。
  - 连续出题仍遵循「不超过 2 次相同题型」规则；zh_classical 默认释义题视为释义题型。

### 7.2 Prompt 更新

`prompts/quiz_generate_prompt.py` 中新增一个专用 prompt（如 `CLASSICAL_GENERATE_PROMPT`），用于 `language=zh_classical` 且题型为释义时替换默认 prompt。该 prompt 要求 LLM 输出包含：例句题干、4 个词性选项、正确答案（词性|释义）。此 prompt 仅服务于 Skill/LLM 场景；Web 层直接使用本地生成逻辑，不走 LLM。

## 8. 测试策略

### 8.1 单元测试

**`tests/test_tools_quiz.py`**

- `test_generate_classical_quiz_uses_round_robin_definition`：对同一 `zh_classical` 词汇多次生成释义题，验证 `definition_index` 按复习记录轮询。
- `test_grade_classical_quiz_exact_match`：验证 `"n.|兵器"` 得 5 分；`"v.|兵器"` 与 `"n.|武器"` 得 0 分。
- `test_grade_classical_quiz_normalizes_pos_case`：验证 `"N.|兵器"` 与 `"n.|兵器"` 均判对。
- `test_generate_classical_quiz_options_include_correct_pos`：验证选项包含正确词性且共 4 项。

**`tests/test_web_services.py`**

- `test_generate_web_classical_quiz_has_pos_options_and_definition_answer`：验证 Web 层生成的文言题包含 4 个词性选项，且 `answer` 格式为 `"词性|释义"`。
- `test_generate_web_classical_quiz_question_highlights_word`：验证题干中包含 `<mark>` 高亮标签。

**`tests/test_web_routes.py`**

- 验证 `/api/quiz/{quiz_id}/grade` 能正确接收 `pos` + `definition` 表单并返回正确/错误结果。
- 验证批量复习评分路由同样支持 `pos` + `definition` 表单。

### 8.2 E2E 测试（可选，用户偏好 Playwright）

- 访问 Web，对 `zh_classical` 词汇生成释义题。
- 选择正确词性、填写释义，提交后看到成功反馈。
- 选择错误词性，提交后看到失败反馈。

## 9. 边界与降级

| 场景 | 处理 |
|------|------|
| 词汇无 `part_of_speech` | 正确词性视为空字符串，选项中包含一个空字符串占位项；另从固定词性池随机取 3 个干扰项，共 4 项；用户选择空字符串占位项即可通过词性校验 |
| 义项无例句 | 题干退化为释义文本提示，不强制要求例句 |
| 词汇无释义 | 按现有规则返回错误，不生成题目 |
| 作答格式非法 | 直接判 0 分，并在结果中提示正确格式 |
| Web 表单只提交单字段 | 回退到原有释义题评分逻辑（非 zh_classical 不受影响） |

## 10. 非目标

- 不修改 `Definition` 模型添加按义项词性（用户明确选择保持现状）。
- 不新增独立题型枚举（继续使用「释义」）。
- 不放宽释义匹配的严格性（不同写法需作为独立义项录入）。
- 不改变非 `zh_classical` 语言（de/en/zh）的现有出题与评分行为。
