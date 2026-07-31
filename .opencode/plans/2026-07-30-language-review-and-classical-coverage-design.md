# Design: 按语种分别复习 + 文言文例句全覆盖

日期: 2026-07-30
状态: 已批准

## 背景

两个用户体验问题：
1. Web 复习功能将所有语种混在一起，用户无法按语种分组复习
2. 文言文释义题每次只考一个例句（Web 端硬编码 `examples[0]`），无法确保每个例句都被覆盖

## Feature 1: 按语种分别复习

### 目标

Review 页面支持按语种过滤，用户点击语种标签查看该语种的到期词汇，批量复习也只复习选中语种。

### 交互设计

Review 页面顶部「今日待复习」下方增加语种标签栏：

```
[全部] [英语(3)] [中文(5)] [文言文(2)] [德语(1)]
```

- 括号内数字为该语种到期词汇数量
- 点击标签通过 HTMX 查询参数 `?language=xx` 刷新列表
- 当前选中标签高亮
- 「开始今日复习」按钮只复习当前选中语种的到期词汇
- 无到期词汇的语种标签不显示（或显示为灰色）

### 改动点

#### 1. `tools/review.py` — `schedule_review()` 增加 language 参数

```python
def schedule_review(language: str = "") -> dict:
    # 在遍历 vocab 时增加过滤：
    if language and v.structured.language != language:
        continue
```

#### 2. `web/services.py` — `get_upcoming_reviews()` 增加 language 参数

```python
def get_upcoming_reviews(language: str = "") -> list[dict]:
    # 现有逻辑不变
    # 在返回前增加过滤：
    if language:
        upcoming = [x for x in upcoming if x["language"] == language]
```

#### 3. `web/services.py` — `start_batch_review()` 增加 language 参数

```python
def start_batch_review(language: str = "") -> Optional[dict]:
    schedule = schedule_review(language=language)
    # 其余逻辑不变
```

#### 4. `web/routes/review.py` — 路由接受 language 参数

```python
@router.get("/partials/review")
async def review_page(language: str = ""):
    upcoming = services.get_upcoming_reviews(language=language)
    # 传递 language 到模板用于标签高亮

@router.post("/api/review/batch/start")
async def batch_start(language: str = ""):
    result = services.start_batch_review(language=language)
```

#### 5. `web/templates/partials/review.html` — 增加标签栏

在「今日待复习」标题和按钮之间增加语种标签，使用 HTMX 查询参数切换：

```html
<div class="language-tabs">
    <a class="tab {{ 'active' if not language }}" href="#" hx-get="/partials/review" hx-target="#content">全部 ({{ total_count }})</a>
    {% for lang_code, lang_name in supported_languages %}
    {% if lang_counts[lang_code] > 0 %}
    <a class="tab {{ 'active' if language == lang_code }}" href="#" hx-get="/partials/review?language={{ lang_code }}" hx-target="#content">{{ lang_name }} ({{ lang_counts[lang_code] }})</a>
    {% endif %}
    {% endfor %}
</div>
```

「开始今日复习」按钮携带当前 language 参数：

```html
<button hx-post="/api/review/batch/start?language={{ language }}" ...>
```

### 数据流

```
用户点击语种标签
  → HTMX GET /partials/review?language=xx
  → services.get_upcoming_reviews(language=xx)
  → 过滤该语种到期词汇
  → 渲染标签栏 + 过滤后的列表

用户点击「开始今日复习」
  → HTMX POST /api/review/batch/start?language=xx
  → services.start_batch_review(language=xx)
  → schedule_review(language=xx) 只返回该语种到期词
  → 为每个到期词生成 quiz
  → 进入批量复习流程
```

---

## Feature 2: 文言文例句全覆盖

### 目标

zh_classical 释义题在一次复习中，选中一个义项后，遍历该义项所有例句，每例句生成一道独立 quiz。确保每个例句都被考察。

边界情况：若选中义项的 `examples` 为空列表，降级为 1 道「请写出词性与释义」题（与现有行为一致）。

### 改动点

#### 1. `models.py` — Quiz 和 ReviewRecord 增加 example_index

```python
class Quiz(BaseModel):
    # ...existing fields...
    example_index: Optional[int] = Field(
        default=None,
        description="考查的例句索引（definitions[i].examples 列表下标）"
    )

class ReviewRecord(BaseModel):
    # ...existing fields...
    example_index: Optional[int] = Field(
        default=None,
        description="本次复习考查的例句索引，透传自 Quiz"
    )
```

向后兼容：`example_index` 默认 None，不影响现有数据。

#### 2. `tools/quiz.py` — `generate_quiz` 返回多道 quiz

zh_classical 释义题生成逻辑改为：

```python
def generate_quiz(vocab_id, quiz_type=""):
    # ...existing definition selection (不变)...
    
    if qtype == "释义" and v.structured.language == "zh_classical":
        quizzes = []
        if selected.examples:
            for ex_idx, example in enumerate(selected.examples):
                # 每个例句生成独立 prompt（只含当前例句）
                defs_block = f"1. {selected.text}\n   - {example}"
                prompt = CLASSICAL_GENERATE_PROMPT.format(...)
                quiz = Quiz(..., definition_index=definition_index, example_index=ex_idx)
                storage.save_quiz(quiz)
                quizzes.append({"quiz_id": quiz.id, ...})
        else:
            # 无例句降级为「请写出词性与释义」
            prompt = f"请写出「{word}」的词性与释义"
            quiz = Quiz(..., definition_index=definition_index, example_index=None)
            storage.save_quiz(quiz)
            quizzes.append({"quiz_id": quiz.id, ...})
        
        return {"quizzes": quizzes}
    
    # 非 zh_classical 保持现有单 quiz 返回格式
    return {"quiz_id": quiz.id, "quiz": quiz.model_dump(), "generate_prompt": prompt}
```

#### 3. `web/services.py` — `generate_web_quiz` 支持例句展开

```python
def generate_web_quiz(vocab_id, quiz_type=""):
    # ...existing logic...
    
    if qtype == "释义" and vocab.structured.language == "zh_classical":
        # 遍历义项的所有例句
        saved_quiz_ids = []
        for ex_idx, example in enumerate(selected_def.examples):
            sentence = example
            highlighted = sentence.replace(word, f"<mark>{word}</mark>")
            prompt = highlighted
            
            # 答案（与现有逻辑相同）
            pos = selected_def.part_of_speech or vocab.structured.part_of_speech.strip()
            pos = _zh_to_en_pos(pos) if pos else "?"
            answer = f"{pos}|{selected_def.text}"
            
            quiz = Quiz(
                id=_generate_quiz_id(storage),
                vocab_id=vocab_id,
                quiz_type="释义",
                question=prompt,
                answer=answer,
                generated_at=_now_utc(),
                graded=False,
                definition_index=definition_index,
                example_index=ex_idx,
            )
            storage.save_quiz(quiz)
            saved_quiz_ids.append(quiz.id)
        
        return {"quiz_ids": saved_quiz_ids}  # 多个 quiz_id
    
    # 其他情况保持现有逻辑，返回 {"quiz_id": ...}
```

#### 4. `web/services.py` — `start_batch_review` 处理多 quiz 返回

```python
def start_batch_review(language=""):
    # ...existing logic...
    for item in due_words:
        result = generate_web_quiz(item["vocab_id"], "")
        if result:
            if "quiz_ids" in result:  # zh_classical 展开为多道
                quiz_ids.extend(result["quiz_ids"])
            elif "quiz_id" in result:  # 其他语种单道
                quiz_ids.append(result["quiz_id"])
    # ...
```

#### 5. `tools/quiz.py` — `grade_quiz` 透传 example_index

```python
def grade_quiz(quiz_id, response):
    # ...existing logic...
    # 在写入 ReviewRecord 时增加 example_index：
    record = ReviewRecord(
        ...,
        definition_index=quiz.definition_index,
        example_index=quiz.example_index,
    )
```

#### 6. `tools/quiz.py` — `_least_reviewed_definition_index` 升级

```python
def _least_reviewed_definition_index(vocab_id, defs, storage):
    """返回复习次数最少的义项下标。

    统计粒度为 (definition_index, example_index) 对，
    优先选择有未覆盖例句的义项。
    """
    # 构建 (def_idx, ex_idx) -> count 的映射
    counts = {}
    for i, d in enumerate(defs):
        for j in range(len(d.examples)):
            counts[(i, j)] = 0
    if not counts:
        return 0
    
    for r in storage.list_all_review_records():
        if r.vocab_id == vocab_id and r.definition_index is not None:
            key = (r.definition_index, r.example_index or 0)
            if key in counts:
                counts[key] += 1
    
    # 按义项聚合：义项的总复习次数 = 该义项所有例句的复习次数之和
    def_counts = {}
    for (di, ei), c in counts.items():
        def_counts[di] = def_counts.get(di, 0) + c
    
    return min(def_counts, key=lambda i: (def_counts[i], i))
```

### 数据流

```
批量复习开始
  → start_batch_review(language="zh_classical")
  → schedule_review() 返回到期的文言文词汇
  → 对每个词汇调用 generate_web_quiz()
    → 选中一个义项（_least_reviewed_definition_index）
    → 遍历该义项 N 个例句
    → 每例句生成 1 道 quiz，definition_index + example_index 记录
    → 返回 N 个 quiz_id
  → batch session 包含所有 quiz_id（连续排列）

用户逐题作答
  → grade_quiz() 评分
  → ReviewRecord 记录 definition_index + example_index
  → SM-2 更新 review_state
  → 下次轮询时 _least_reviewed_definition_index 统计 (def, ex) 覆盖情况
```

### 向后兼容

- `example_index` 默认 None，不影响现有 Quiz/ReviewRecord 数据
- 非 zh_classical 语种不使用例句展开，行为不变
- MCP 工具端（/quiz 命令）和 Web 端采用相同逻辑

---

## 影响范围

### 文件改动清单

| 文件 | 改动 |
|------|------|
| `models.py` | Quiz + ReviewRecord 增加 `example_index` 字段 |
| `tools/quiz.py` | `generate_quiz` zh_classical 返回多 quiz；`grade_quiz` 透传 example_index；`_least_reviewed_definition_index` 升级 |
| `tools/review.py` | `schedule_review` 增加 language 参数 |
| `web/services.py` | `get_upcoming_reviews` / `start_batch_review` / `generate_web_quiz` 增加 language + 例句展开 |
| `web/routes/review.py` | 路由增加 language 参数 |
| `web/templates/partials/review.html` | 增加语种标签栏 |

### 测试要求

- `test_tools_quiz.py`: zh_classical 多例句生成 + example_index 透传 + 轮询策略
- `test_web_services.py`: 语种过滤 + zh_classical 批量复习展开
- `test_tools_review.py`: schedule_review language 参数
