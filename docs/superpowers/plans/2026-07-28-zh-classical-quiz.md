# 文言文词汇出题方式实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `language=zh_classical` 的词汇改造默认「释义」题，使其在 Web 与 Skill 场景下都能以「例句 + 选择词性 + 填写释义」的形式客观评分，并分题轮询覆盖所有义项。

**Architecture:** 复用现有 `Quiz` 模型与 `quiz_type="释义"`，不新增题型枚举。在 `tools/quiz.py` 中增加分题轮询与客观评分分支；在 `web/services.py` 与模板层增加 Web 专用的词性单选 + 释义输入；Skill 层更新 prompt 与文档说明作答格式。

**Tech Stack:** Python 3.12+, FastAPI, Jinja2, Pydantic, pytest

## Global Constraints

- 不修改核心数据模型（`VocabRecord`、`Quiz`、`ReviewRecord`、`Definition`）。
- 不新增 `quiz_type` 枚举值，继续使用「释义」。
- 评分客观精确，Web 端无 LLM 参与。
- 释义答案严格一致，词性大小写不敏感。
- 连续出题不超过 2 次相同题型。
- 所有数据仅本地存储。

---

## File Structure

| 文件 | 职责 |
|------|------|
| `vocabcraft-mcp/src/vocabcraft_mcp/tools/quiz.py` | 分题轮询选义项、文言释义题客观评分 |
| `vocabcraft-mcp/src/vocabcraft_mcp/prompts/quiz_generate_prompt.py` | 新增 `CLASSICAL_GENERATE_PROMPT` 供 Skill/LLM 场景使用 |
| `vocabcraft-mcp/src/vocabcraft_mcp/web/services.py` | 生成 Web 可用的文言释义题（题干/选项/答案） |
| `vocabcraft-mcp/src/vocabcraft_mcp/web/routes/quiz.py` | 解析 `pos` + `definition` 表单并拼接为评分字符串 |
| `vocabcraft-mcp/src/vocabcraft_mcp/web/routes/review.py` | 批量复习路由同样解析 `pos` + `definition` 表单 |
| `vocabcraft-mcp/src/vocabcraft_mcp/web/templates/partials/quiz.html` | 渲染词性单选 + 释义输入框 |
| `vocabcraft-mcp/src/vocabcraft_mcp/web/templates/partials/batch_review_item.html` | 批量复习渲染词性单选 + 释义输入框 |
| `.trae/skills/vocabcraft-quiz/skill.md` | 更新题型对照与作答格式说明 |
| `vocabcraft-mcp/tests/test_tools_quiz.py` | 出题与评分单元测试 |
| `vocabcraft-mcp/tests/test_web_services.py` | Web 服务层生成逻辑测试 |
| `vocabcraft-mcp/tests/test_web_routes.py` | Web 路由评分测试 |

---

### Task 1: 分题轮询选义项

**Files:**
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/tools/quiz.py:42-107`

**Interfaces:**
- Consumes: `Storage.list_all_review_records()` → `list[ReviewRecord]`
- Produces: `generate_quiz()` 在 `zh_classical` 释义场景下按复习次数选择 `definition_index`

- [ ] **Step 1: 编写测试**

```python
# tests/test_tools_quiz.py
from vocabcraft_mcp.tools.quiz import generate_quiz, grade_quiz
from vocabcraft_mcp.tools.crud import save_vocab, get_storage


def test_generate_classical_quiz_uses_round_robin_definition(isolated_storage):
    """多次生成 zh_classical 释义题应轮询不同义项"""
    save_vocab({
        "id": "vocab_test_001",
        "structured": {
            "word": "兵",
            "phonetic": "",
            "part_of_speech": "n.",
            "language": "zh_classical",
            "definitions": [
                {"text": "兵器", "examples": ["收天下之兵"]},
                {"text": "士兵，军队", "examples": ["赵兵果败"]},
            ],
        },
    })

    # 第一次：无复习记录，应选 definition_index=0
    r1 = generate_quiz("vocab_test_001", "释义")
    assert r1["quiz"]["definition_index"] == 0

    # 模拟 definition_index=0 已复习一次
    from datetime import datetime, timezone
    from vocabcraft_mcp.models import ReviewRecord
    rec = ReviewRecord(
        record_id="rec_test_001",
        vocab_id="vocab_test_001",
        review_time=datetime.now(timezone.utc),
        grade=5,
        prev_ease=2.5,
        new_ease=2.6,
        definition_index=0,
    )
    get_storage().save_review_record(rec)

    # 第二次：应选复习次数更少的 definition_index=1
    r2 = generate_quiz("vocab_test_001", "释义")
    assert r2["quiz"]["definition_index"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd vocabcraft-mcp && pytest tests/test_tools_quiz.py::test_generate_classical_quiz_uses_round_robin_definition -v`
Expected: FAIL

- [ ] **Step 3: 实现分题轮询逻辑**

在 `vocabcraft-mcp/src/vocabcraft_mcp/tools/quiz.py` 中，`_generate_quiz_id` 之后新增辅助函数：

```python
_CLASSICAL_POS_POOL = ["n.", "v.", "adj.", "adv.", "pron.", "num.", "量", "连", "介", "助", "叹"]


def _least_reviewed_definition_index(vocab_id: str, defs: list, storage) -> int:
    """返回复习次数最少的义项下标；次数相同按下标升序取第一个"""
    counts = {i: 0 for i in range(len(defs))}
    for r in storage.list_all_review_records():
        if r.vocab_id == vocab_id and r.definition_index is not None:
            counts[r.definition_index] = counts.get(r.definition_index, 0) + 1
    return min(counts, key=lambda i: (counts[i], i))
```

修改 `generate_quiz`：

1. 定义选择段落改为：

```python
    defs = v.structured.definitions
    if defs:
        if qtype == "释义" and v.structured.language == "zh_classical":
            definition_index = _least_reviewed_definition_index(vocab_id, defs, storage)
        elif len(defs) > 1:
            definition_index = random.randrange(len(defs))
        else:
            definition_index = 0
        selected = defs[definition_index]
        defs_block = f"1. {selected.text}" + "".join(f"\n   - {e}" for e in selected.examples)
    else:
        definition_index = None
        defs_block = "（无）"
```

2. 占位 answer 编码改为：

```python
    if qtype == "拼写":
        answer = v.structured.word
    elif qtype == "释义" and v.structured.language == "zh_classical":
        answer = f"{v.structured.part_of_speech.strip()}|{defs[definition_index].text.strip()}" if defs else ""
    else:
        answer = defs[definition_index].text if defs else ""
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd vocabcraft-mcp && pytest tests/test_tools_quiz.py::test_generate_classical_quiz_uses_round_robin_definition -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd vocabcraft-mcp
git add src/vocabcraft_mcp/tools/quiz.py tests/test_tools_quiz.py
git commit -m "feat(quiz): round-robin definition selection for zh_classical"
```

---

### Task 2: 文言释义题客观评分

**Files:**
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/tools/quiz.py:110-193`

**Interfaces:**
- Consumes: `Quiz.answer` 编码为 `"词性|释义"`
- Produces: `grade_quiz()` 对 `zh_classical` 释义题返回 `correct: bool`

- [ ] **Step 1: 编写测试**

```python
# tests/test_tools_quiz.py
from datetime import datetime, timezone
from vocabcraft_mcp.models import Quiz
from vocabcraft_mcp.tools.crud import save_vocab, get_storage


def _save_classical_quiz(vocab_id: str, quiz_id: str, answer: str, definition_index: int = 0):
    """测试辅助：保存一个 zh_classical 释义 Quiz"""
    quiz = Quiz(
        id=quiz_id,
        vocab_id=vocab_id,
        quiz_type="释义",
        question="题干",
        answer=answer,
        generated_at=datetime.now(timezone.utc),
        definition_index=definition_index,
    )
    get_storage().save_quiz(quiz)


def test_grade_classical_quiz_exact_match(isolated_storage):
    save_vocab({
        "id": "vocab_test_002",
        "structured": {
            "word": "兵",
            "part_of_speech": "n.",
            "language": "zh_classical",
            "definitions": [{"text": "兵器", "examples": ["收天下之兵"]}],
        },
    })
    _save_classical_quiz("vocab_test_002", "quiz_test_002", "n.|兵器")

    assert grade_quiz("quiz_test_002", "n.|兵器")["correct"] is True
    assert grade_quiz("quiz_test_002", "v.|兵器")["correct"] is False
    assert grade_quiz("quiz_test_002", "n.|武器")["correct"] is False


def test_grade_classical_quiz_normalizes_pos_case(isolated_storage):
    save_vocab({
        "id": "vocab_test_003",
        "structured": {
            "word": "兵",
            "part_of_speech": "N.",
            "language": "zh_classical",
            "definitions": [{"text": "兵器", "examples": ["收天下之兵"]}],
        },
    })
    _save_classical_quiz("vocab_test_003", "quiz_test_003", "N.|兵器")

    assert grade_quiz("quiz_test_003", "n.|兵器")["correct"] is True
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd vocabcraft-mcp && pytest tests/test_tools_quiz.py::test_grade_classical_quiz_exact_match tests/test_tools_quiz.py::test_grade_classical_quiz_normalizes_pos_case -v`
Expected: FAIL

- [ ] **Step 3: 实现评分逻辑**

在 `vocabcraft-mcp/src/vocabcraft_mcp/tools/quiz.py` 中，`_OBJECTIVE_TYPES` 下方新增：

```python
def _grade_classical_definition(response: str, answer: str) -> tuple[int, bool]:
    """文言释义题客观评分：词性大小写不敏感，释义严格一致"""
    if "|" not in response or "|" not in answer:
        return 0, False
    resp_pos, _, resp_def = response.partition("|")
    ans_pos, _, ans_def = answer.partition("|")
    correct = (
        resp_pos.strip().lower() == ans_pos.strip().lower()
        and resp_def.strip() == ans_def.strip()
    )
    return (5, True) if correct else (0, False)
```

修改 `grade_quiz` 中评分分支（约第 142-155 行）为：

```python
    # 评分：客观题精确匹配；文言释义题客观匹配；其他释义题交 LLM
    if quiz.quiz_type in _OBJECTIVE_TYPES:
        correct = response.strip().lower() == quiz.answer.strip().lower()
        grade = 5 if correct else 0
        result["correct"] = correct
    elif quiz.quiz_type == "释义" and vocab.structured.language == "zh_classical":
        grade, correct = _grade_classical_definition(response, quiz.answer)
        result["correct"] = correct
    else:
        # 释义题主观题：渲染 grade_prompt 交宿主 LLM，骨架阶段用 grade=3 推进
        result["grade_prompt"] = GRADE_PROMPT.format(
            question=quiz.question,
            reference_answer=quiz.answer,
            user_answer=response,
        )
        result["correct"] = None
        grade = 3
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd vocabcraft-mcp && pytest tests/test_tools_quiz.py::test_grade_classical_quiz_exact_match tests/test_tools_quiz.py::test_grade_classical_quiz_normalizes_pos_case -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd vocabcraft-mcp
git add src/vocabcraft_mcp/tools/quiz.py tests/test_tools_quiz.py
git commit -m "feat(quiz): objective grading for zh_classical definition quizzes"
```

---

### Task 3: 新增文言文 Prompt

**Files:**
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/prompts/quiz_generate_prompt.py`

**Interfaces:**
- Produces: `CLASSICAL_GENERATE_PROMPT` 字符串，供 `tools/quiz.py` 在 `zh_classical` 释义时引用

- [ ] **Step 1: 编写测试**

```python
# tests/test_tools_quiz.py
from vocabcraft_mcp.prompts.quiz_generate_prompt import CLASSICAL_GENERATE_PROMPT


def test_classical_generate_prompt_exists():
    assert "词性" in CLASSICAL_GENERATE_PROMPT
    assert "释义" in CLASSICAL_GENERATE_PROMPT
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd vocabcraft-mcp && pytest tests/test_tools_quiz.py::test_classical_generate_prompt_exists -v`
Expected: FAIL

- [ ] **Step 3: 实现 Prompt 并接入 generate_quiz**

在 `vocabcraft-mcp/src/vocabcraft_mcp/prompts/quiz_generate_prompt.py` 文件末尾新增：

```python
CLASSICAL_GENERATE_PROMPT = """你是一位文言文教师。请根据以下词汇信息，为「释义」题生成一道适合 Web/命令行使用的题目。

词汇：{word}
词性：{part_of_speech}
考查义项：
{definitions_block}

要求：
1. 题干给出一条例句，并将目标词用 <mark>{word}</mark> 高亮。
2. 若义项无例句，则题干为：请写出「{word}」在义项「释义文本」中的词性与释义。
3. 提供 4 个词性选项，格式为 JSON 数组。
4. 正确答案格式必须为：词性|释义文本（例如 n.|兵器）。

请只输出 JSON：
{{
  "question": "...",
  "options": ["n.", "v.", "adj.", "adv."],
  "answer": "n.|释义文本"
}}
"""
```

（如 `quiz_generate_prompt.py` 当前有 `__all__` 等导出控制，请同步添加 `CLASSICAL_GENERATE_PROMPT`。）

然后在 `vocabcraft-mcp/src/vocabcraft_mcp/tools/quiz.py` 中：

1. 导入改为：

```python
from vocabcraft_mcp.prompts.quiz_generate_prompt import GENERATE_PROMPT, CLASSICAL_GENERATE_PROMPT
```

2. 将原来的 `prompt = GENERATE_PROMPT.format(...)` 块替换为：

```python
    if qtype == "释义" and v.structured.language == "zh_classical":
        prompt = CLASSICAL_GENERATE_PROMPT.format(
            word=v.structured.word,
            part_of_speech=v.structured.part_of_speech,
            definitions_block=defs_block,
        )
    else:
        prompt = GENERATE_PROMPT.format(
            word=v.structured.word,
            phonetic=v.structured.phonetic,
            definitions_block=defs_block,
            quiz_type=qtype,
            language=v.structured.language,
        )
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd vocabcraft-mcp && pytest tests/test_tools_quiz.py::test_classical_generate_prompt_exists -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd vocabcraft-mcp
git add src/vocabcraft_mcp/prompts/quiz_generate_prompt.py src/vocabcraft_mcp/tools/quiz.py tests/test_tools_quiz.py
git commit -m "feat(prompts): add classical chinese generate prompt"
```

---

### Task 4: Web 层生成文言释义题

**Files:**
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/web/services.py:271-336`

**Interfaces:**
- Consumes: `Quiz.definition_index`, `vocab.structured.part_of_speech`, `vocab.structured.language`
- Produces: `generate_web_quiz()` 返回的 `quiz` dict 包含 `options`、`answer="词性|释义"`、`language`

- [ ] **Step 1: 编写测试**

```python
# tests/test_web_services.py
from vocabcraft_mcp.web.services import generate_web_quiz
from vocabcraft_mcp.tools.crud import save_vocab


def test_generate_web_classical_quiz_has_pos_options_and_definition_answer(temp_storage):
    save_vocab({
        "id": "vocab_web_001",
        "structured": {
            "word": "兵",
            "part_of_speech": "n.",
            "language": "zh_classical",
            "definitions": [{"text": "兵器", "examples": ["收天下之兵"]}],
        },
    })

    result = generate_web_quiz("vocab_web_001", "释义")
    quiz = result["quiz"]
    assert quiz["language"] == "zh_classical"
    assert quiz["options"] is not None
    assert len(quiz["options"]) == 4
    assert "n." in quiz["options"]
    assert quiz["answer"] == "n.|兵器"


def test_generate_web_classical_quiz_question_highlights_word(temp_storage):
    save_vocab({
        "id": "vocab_web_002",
        "structured": {
            "word": "兵",
            "part_of_speech": "n.",
            "language": "zh_classical",
            "definitions": [{"text": "兵器", "examples": ["收天下之兵"]}],
        },
    })

    result = generate_web_quiz("vocab_web_002", "释义")
    assert "<mark>兵</mark>" in result["quiz"]["question"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd vocabcraft-mcp && pytest tests/test_web_services.py::test_generate_web_classical_quiz_has_pos_options_and_definition_answer tests/test_web_services.py::test_generate_web_classical_quiz_question_highlights_word -v`
Expected: FAIL

- [ ] **Step 3: 实现 Web 出题逻辑**

在 `vocabcraft-mcp/src/vocabcraft_mcp/web/services.py` 中，`_pick_distractors` 之后新增：

```python
_CLASSICAL_POS_POOL = ["n.", "v.", "adj.", "adv.", "pron.", "num.", "量", "连", "介", "助", "叹"]


def _classical_pos_options(part_of_speech: str) -> list[str]:
    """生成文言释义题词性选项：1 个正确 + 3 个干扰项，顺序随机打乱"""
    from random import shuffle
    correct = part_of_speech.strip()
    if not correct:
        options = [""] + sample(_CLASSICAL_POS_POOL, 3)
    else:
        distractors = [p for p in _CLASSICAL_POS_POOL if p.lower() != correct.lower()]
        options = [correct] + sample(distractors, 3)
    shuffle(options)
    return options
```

修改 `generate_web_quiz` 中「释义」分支（约第 324-327 行）为：

```python
    else:  # 释义
        if vocab.structured.language == "zh_classical":
            definition_index = quiz.definition_index if quiz.definition_index is not None else 0
            definition = defs[definition_index] if defs else None
            if definition and definition.examples:
                sentence = definition.examples[0]
                prompt = sentence.replace(word, f"<mark>{word}</mark>")
                prompt += "<br><small>请选择词性并填写释义</small>"
            elif definition:
                prompt = f"请写出「{word}」在义项「{definition.text}」中的词性与释义"
            else:
                prompt = f"请写出「{word}」的词性与释义"
            answer = f"{vocab.structured.part_of_speech.strip()}|{definition.text.strip() if definition else word}"
            options = _classical_pos_options(vocab.structured.part_of_speech)
        else:
            prompt = f"请写出单词「{word}」的释义"
            answer = first_def_text if defs else word
            options = None
```

并在函数返回前注入 `language`：

```python
    quiz_dict = updated_quiz.model_dump()
    quiz_dict["language"] = vocab.structured.language
    return {"quiz_id": quiz_id, "quiz": quiz_dict}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd vocabcraft-mcp && pytest tests/test_web_services.py::test_generate_web_classical_quiz_has_pos_options_and_definition_answer tests/test_web_services.py::test_generate_web_classical_quiz_question_highlights_word -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd vocabcraft-mcp
git add src/vocabcraft_mcp/web/services.py tests/test_web_services.py
git commit -m "feat(web): generate zh_classical definition quiz with pos options"
```

---

### Task 5: Web 出题路由解析词性 + 释义

**Files:**
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/web/routes/quiz.py:42-63`

**Interfaces:**
- Consumes: 表单字段 `pos` 与 `definition`
- Produces: 拼接为 `"pos|definition"` 后调用 `services.grade_web_quiz`

- [ ] **Step 1: 编写测试**

```python
# tests/test_web_routes.py
from datetime import datetime, timezone
from vocabcraft_mcp.models import Quiz


def test_grade_classical_quiz_via_pos_and_definition(client):
    test_client, storage = client
    storage.save_vocab(_make_vocab("兵", "vocab_route_001", language="zh_classical"))
    quiz = Quiz(
        id="quiz_route_001",
        vocab_id="vocab_route_001",
        quiz_type="释义",
        question="题干",
        answer="n.|兵 def",  # _make_vocab 默认释义文本
        generated_at=datetime.now(timezone.utc),
        definition_index=0,
    )
    storage.save_quiz(quiz)

    response = test_client.post("/api/quiz/quiz_route_001/grade", data={"pos": "n.", "definition": "兵 def"})
    assert response.status_code == 200
    assert "✅" in response.text

    response_wrong = test_client.post("/api/quiz/quiz_route_001/grade", data={"pos": "v.", "definition": "兵 def"})
    assert "❌" in response_wrong.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd vocabcraft-mcp && pytest tests/test_web_routes.py::test_grade_classical_quiz_via_pos_and_definition -v`
Expected: FAIL

- [ ] **Step 3: 实现路由解析**

修改 `vocabcraft-mcp/src/vocabcraft_mcp/web/routes/quiz.py` 中 `grade_quiz_partial`：

```python
    form = await request.form()
    pos = form.get("pos")
    definition = form.get("definition")
    if pos is not None and definition is not None:
        response = f"{pos}|{definition}"
    else:
        response = form.get("response", "")
        if not response:
            response = request.query_params.get("response", "")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd vocabcraft-mcp && pytest tests/test_web_routes.py::test_grade_classical_quiz_via_pos_and_definition -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd vocabcraft-mcp
git add src/vocabcraft_mcp/web/routes/quiz.py tests/test_web_routes.py
git commit -m "feat(web/quiz): parse pos and definition form fields"
```

---

### Task 6: 批量复习路由解析词性 + 释义

**Files:**
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/web/routes/review.py:90-119`

**Interfaces:**
- Consumes: 表单字段 `pos` 与 `definition`
- Produces: 拼接为 `"pos|definition"` 后调用 `services.grade_batch_review_item`

- [ ] **Step 1: 编写测试**

```python
# tests/test_web_routes.py
from vocabcraft_mcp.web import services


def test_grade_batch_classical_quiz_via_pos_and_definition(client):
    test_client, storage = client
    storage.save_vocab(_make_vocab("兵", "vocab_batch_001", language="zh_classical", next_review="2020-01-01"))

    batch = services.start_batch_review()
    assert batch is not None

    response = test_client.post(
        f"/api/review/batch/{batch['batch_id']}/item/0/grade",
        data={"pos": "n.", "definition": "兵 def"},
    )
    assert response.status_code == 200
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd vocabcraft-mcp && pytest tests/test_web_routes.py::test_grade_batch_classical_quiz_via_pos_and_definition -v`
Expected: FAIL

- [ ] **Step 3: 实现路由解析**

修改 `vocabcraft-mcp/src/vocabcraft_mcp/web/routes/review.py` 中 `grade_batch_review_item_partial`：

```python
    form = await request.form()
    pos = form.get("pos")
    definition = form.get("definition")
    if pos is not None and definition is not None:
        response = f"{pos}|{definition}"
    else:
        response = form.get("response", "")
        if not response:
            response = request.query_params.get("response", "")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd vocabcraft-mcp && pytest tests/test_web_routes.py::test_grade_batch_classical_quiz_via_pos_and_definition -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
cd vocabcraft-mcp
git add src/vocabcraft_mcp/web/routes/review.py tests/test_web_routes.py
git commit -m "feat(web/review): parse pos and definition in batch review"
```

---

### Task 7: 注入 language 到模板上下文

**Files:**
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/web/routes/quiz.py:28-39`
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/web/services.py:397-413`

**Interfaces:**
- Produces: 模板中 `quiz.language` 或 `item.quiz.language` 可用

- [ ] **Step 1: 修改 quiz_partial 路由**

在 `vocabcraft-mcp/src/vocabcraft_mcp/web/routes/quiz.py` 中：

```python
@router.get("/partials/quiz/{quiz_id}", response_class=HTMLResponse)
async def quiz_partial(request: Request, quiz_id: str):
    """返回指定考题的展示片段"""
    storage = services._get_storage()
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="考题不存在")
    vocab = storage.load_vocab(quiz.vocab_id)
    quiz_dict = quiz.model_dump()
    if vocab is not None:
        quiz_dict["language"] = vocab.structured.language
    return templates.TemplateResponse(
        request,
        "partials/quiz.html",
        {"quiz": quiz_dict, "result": None},
    )
```

- [ ] **Step 2: 修改 get_batch_review_item**

在 `vocabcraft-mcp/src/vocabcraft_mcp/web/services.py` 中：

```python
    storage = _get_storage()
    quiz = storage.load_quiz(session.quiz_ids[index])
    if quiz is None:
        return None

    vocab = storage.load_vocab(quiz.vocab_id)
    quiz_dict = quiz.model_dump()
    if vocab is not None:
        quiz_dict["language"] = vocab.structured.language

    return {
        "batch_id": batch_id,
        "index": index,
        "total": len(session.quiz_ids),
        "quiz": quiz_dict,
    }
```

- [ ] **Step 3: 运行相关 Web 测试**

Run: `cd vocabcraft-mcp && pytest tests/test_web_routes.py tests/test_web_services.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
cd vocabcraft-mcp
git add src/vocabcraft_mcp/web/routes/quiz.py src/vocabcraft_mcp/web/services.py
git commit -m "feat(web): inject language into quiz template context"
```

---

### Task 8: 模板渲染词性单选 + 释义输入

**Files:**
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/web/templates/partials/quiz.html`
- Modify: `vocabcraft-mcp/src/vocabcraft_mcp/web/templates/partials/batch_review_item.html`

**Interfaces:**
- Consumes: `quiz.language == "zh_classical"` 且 `quiz.options` 存在

- [ ] **Step 1: 修改 quiz.html**

替换原有 `{% if quiz.options %}` 块为：

```html
        {% if quiz.options and quiz.language == "zh_classical" %}
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
        {% elif quiz.options %}
        <div class="quiz-options">
            {% for option in quiz.options %}
            <label class="quiz-option">
                <input type="radio" name="response" value="{{ option }}" required>
                <span>{{ option }}</span>
            </label>
            {% endfor %}
        </div>
        {% else %}
        <div class="form-group">
            <input type="text" name="response" class="quiz-input" placeholder="请输入答案" required autocomplete="off">
        </div>
        {% endif %}
```

- [ ] **Step 2: 修改 batch_review_item.html**

替换原有 `{% if item.quiz.options %}` 块为：

```html
        {% if item.quiz.options and item.quiz.language == "zh_classical" %}
        <div class="quiz-options">
            {% for option in item.quiz.options %}
            <label class="quiz-option">
                <input type="radio" name="pos" value="{{ option }}" required>
                <span>{{ option }}</span>
            </label>
            {% endfor %}
        </div>
        <input type="text" name="definition" class="quiz-input" placeholder="请填写释义" required autofocus autocomplete="off">
        {% elif item.quiz.options %}
        <div class="quiz-options">
            {% for option in item.quiz.options %}
            <label class="quiz-option">
                <input type="radio" name="response" value="{{ option }}" required>
                <span>{{ option }}</span>
            </label>
            {% endfor %}
        </div>
        {% else %}
        <input type="text" name="response" class="quiz-input" placeholder="请输入答案" required autofocus autocomplete="off">
        {% endif %}
```

- [ ] **Step 3: 运行 Web 测试**

Run: `cd vocabcraft-mcp && pytest tests/test_web_routes.py tests/test_web_services.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
cd vocabcraft-mcp
git add src/vocabcraft_mcp/web/templates/partials/quiz.html src/vocabcraft_mcp/web/templates/partials/batch_review_item.html
git commit -m "feat(web/templates): render pos radio and definition input for zh_classical"
```

---

### Task 9: 更新 Skill 文档

**Files:**
- Modify: `.trae/skills/vocabcraft-quiz/skill.md`

**Interfaces:**
- Produces: Skill 使用者了解 `zh_classical` 释义题形式与作答格式

- [ ] **Step 1: 更新题型对照表**

将：

```markdown
| 释义题 | `definition` | 给词形写释义 | 核心义素匹配即对 |
```

改为：

```markdown
| 释义题 | `definition` | 给词形写释义（de/en/zh 等） | 核心义素匹配即对 |
| 释义题 | `definition` | 给例句，选择词性并填写释义（zh_classical） | 词性、释义均正确得 5 分，否则 0 分 |
```

- [ ] **Step 2: 更新 Common Mistakes**

在「评分后未更新记忆状态」之前新增：

```markdown
- **文言文作答格式错误**：`zh_classical` 释义题作答必须为 `"词性|释义"`（如 `n.|兵器`），否则判 0 分
```

- [ ] **Step 3: 提交**

```bash
cd vocabcraft-mcp
git add ../.trae/skills/vocabcraft-quiz/skill.md
git commit -m "docs(skill): update quiz skill for zh_classical definition format"
```

---

### Task 10: 全量回归测试

**Files:**
- None（仅运行测试）

- [ ] **Step 1: 运行完整测试套件**

Run: `cd vocabcraft-mcp && pytest -q`
Expected: 全部通过

- [ ] **Step 2: 启动 Web 服务手动验证（可选）**

Run: `cd vocabcraft-mcp && uv run python -m vocabcraft_mcp.web.app`
然后访问 `/partials/quiz/{vocab_id}/generate?quiz_type=释义` 对 `zh_classical` 词汇进行验证。

- [ ] **Step 3: 提交最终变更（如有）**

若测试或手动验证中修复了问题，单独提交修复 commit。

---

## Self-Review

**1. Spec coverage:**

- 分题轮询覆盖多义项 → Task 1
- 例句题干 + 高亮目标词 → Task 4
- 词性选项生成 → Task 4
- 客观精确评分 → Task 2
- Web 表单解析 → Task 5 / Task 6
- 模板渲染 → Task 8
- Skill 文档更新 → Task 9
- 边界与降级（无词性、无例句）→ Task 4 / Task 2

无遗漏。

**2. Placeholder scan:**

- 无 TBD/TODO。
- 所有步骤包含具体代码或命令。
- 测试代码包含可运行断言。

**3. Type consistency:**

- `Quiz.answer` 始终编码为 `"词性|释义"`。
- `grade_quiz` 接收 `response: str` 不变。
- Web 路由将 `pos` + `definition` 拼接后传入，签名不变。
- 模板条件统一使用 `quiz.language == "zh_classical"`。

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-28-zh-classical-quiz.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints for review

**Which approach?**
