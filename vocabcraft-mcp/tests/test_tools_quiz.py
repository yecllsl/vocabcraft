# tests/test_tools_quiz.py
"""考题 Tool 单元测试

验证 generate_quiz / grade_quiz 真实行为:
    - generate_quiz: 默认题型"拼写"、占位题持久化、渲染 generate_prompt
    - grade_quiz 客观题: 精确匹配答对 grade=5/答错 grade=0
    - grade_quiz 释义题: 返回 grade_prompt，默认 grade=3
    - 评分后 SM-2 状态更新（repetitions/ease_factor/next_review 演进）
"""

import pytest

from vocabcraft_mcp.tools.quiz import generate_quiz, grade_quiz
from vocabcraft_mcp.tools.crud import save_vocab, get_storage
from vocabcraft_mcp.prompts.quiz_generate_prompt import CLASSICAL_GENERATE_PROMPT


def test_quiz_importable():
    """模块可正常 import"""
    assert callable(generate_quiz)
    assert callable(grade_quiz)


def test_generate_quiz_default_type(isolated_storage, make_vocab_data):
    """未指定 quiz_type 默认'拼写'"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    result = generate_quiz("vocab_001")
    assert result["quiz_id"].startswith("quiz_")
    assert result["quiz"]["quiz_type"] == "拼写"
    assert "generate_prompt" in result
    # 拼写题 answer = 词形
    assert result["quiz"]["answer"] == "hello"


def test_generate_quiz_specified_type(isolated_storage, make_vocab_data):
    """指定 quiz_type='选择' 生成的考题为选择题"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    result = generate_quiz("vocab_001", "选择")
    assert result["quiz"]["quiz_type"] == "选择"


def test_generate_quiz_nonexistent_returns_error(isolated_storage):
    """词汇不存在返回 error"""
    result = generate_quiz("vocab_999")
    assert "error" in result


def test_grade_quiz_correct_objective(isolated_storage, make_vocab_data):
    """客观题答对：grade=5, correct=True"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    gen = generate_quiz("vocab_001")  # 拼写题，answer="hello"

    result = grade_quiz(gen["quiz_id"], "hello")
    assert result["grade"] == 5
    assert result["correct"] is True


def test_grade_quiz_wrong_objective(isolated_storage, make_vocab_data):
    """客观题答错：grade=0, correct=False"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    gen = generate_quiz("vocab_001")

    result = grade_quiz(gen["quiz_id"], "wrong")
    assert result["grade"] == 0
    assert result["correct"] is False


def test_grade_quiz_case_insensitive(isolated_storage, make_vocab_data):
    """客观题精确匹配忽略大小写与空白"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    gen = generate_quiz("vocab_001")

    result = grade_quiz(gen["quiz_id"], "  HELLO  ")
    assert result["grade"] == 5
    assert result["correct"] is True


def test_grade_quiz_updates_sm2_state(isolated_storage, make_vocab_data):
    """评分后 SM-2 状态更新：答对 rep 0→1, EF 2.5→2.6"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    gen = generate_quiz("vocab_001")

    grade_quiz(gen["quiz_id"], "hello")
    v = get_storage().load_vocab("vocab_001")
    assert v.review_state.repetitions == 1
    assert v.review_state.ease_factor == pytest.approx(2.6, abs=1e-3)
    assert v.review_state.interval == 1
    assert v.review_state.next_review  # 非空


def test_grade_quiz_wrong_resets_repetitions(isolated_storage, make_vocab_data):
    """答错 repetitions 归零"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    gen = generate_quiz("vocab_001")

    grade_quiz(gen["quiz_id"], "wrong")
    v = get_storage().load_vocab("vocab_001")
    assert v.review_state.repetitions == 0
    assert v.review_state.interval == 1  # 答错 interval=1（明天重背）


def test_grade_quiz_subjective_returns_prompt(isolated_storage, make_vocab_data):
    """释义题返回 grade_prompt，correct=None，默认 grade=3"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    gen = generate_quiz("vocab_001", "释义")

    result = grade_quiz(gen["quiz_id"], "你好")
    assert "grade_prompt" in result
    assert result["correct"] is None
    assert result["grade"] == 3  # 骨架默认值


def test_grade_quiz_writes_review_record(isolated_storage, make_vocab_data):
    """评分后写入复习记录"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    gen = generate_quiz("vocab_001")

    result = grade_quiz(gen["quiz_id"], "hello")
    assert "review_record_id" in result
    records = get_storage().list_all_review_records()
    assert len(records) == 1
    assert records[0].grade == 5


def test_grade_quiz_marks_graded(isolated_storage, make_vocab_data):
    """评分后考题标记 graded=True"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    gen = generate_quiz("vocab_001")

    grade_quiz(gen["quiz_id"], "hello")
    quiz = get_storage().load_quiz(gen["quiz_id"])
    assert quiz.graded is True


def test_grade_quiz_nonexistent_returns_error(isolated_storage):
    """考题不存在返回 error"""
    result = grade_quiz("quiz_999", "hello")
    assert "error" in result


def test_generate_quiz_single_sense_definition_index_zero(isolated_storage, make_vocab_data):
    """单词义词的 definition_index = 0"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    result = generate_quiz("vocab_001", "释义")
    assert result["quiz"]["definition_index"] == 0


def test_generate_quiz_multi_sense_definition_index_in_range(isolated_storage):
    """多义词的 definition_index 在 [0, len(defs)) 范围内"""
    from vocabcraft_mcp.tools.crud import save_vocab
    data = {
        "id": "vocab_001",
        "structured": {
            "word": "病",
            "phonetic": "",
            "part_of_speech": "n.",
            "definitions": [
                {"text": "疾病", "examples": []},
                {"text": "生病", "examples": []},
                {"text": "担心", "examples": []},
            ],
            "language": "zh_classical",
        },
    }
    save_vocab(data)
    result = generate_quiz("vocab_001", "释义")
    quizzes = result["quizzes"]
    assert len(quizzes) == 1
    idx = quizzes[0]["quiz"]["definition_index"]
    assert idx in (0, 1, 2)


def test_generate_quiz_multi_sense_prompt_only_contains_selected_def(isolated_storage):
    """多义词的 generate_prompt 只含选中义项，不含其他义项"""
    from vocabcraft_mcp.tools.crud import save_vocab
    data = {
        "id": "vocab_001",
        "structured": {
            "word": "病",
            "phonetic": "",
            "part_of_speech": "n.",
            "definitions": [
                {"text": "疾病", "examples": []},
                {"text": "生病", "examples": []},
                {"text": "担心", "examples": []},
            ],
            "language": "zh_classical",
        },
    }
    save_vocab(data)
    result = generate_quiz("vocab_001", "释义")
    quizzes = result["quizzes"]
    assert len(quizzes) == 1
    prompt = quizzes[0]["generate_prompt"]
    idx = quizzes[0]["quiz"]["definition_index"]
    selected_text = ["疾病", "生病", "担心"][idx]
    # 选中义项必须在 prompt 中
    assert selected_text in prompt
    # 未选中的两个义项不应同时出现在 prompt 的义项列表中
    other_texts = [t for i, t in enumerate(["疾病", "生病", "担心"]) if i != idx]
    not_selected_count = sum(1 for t in other_texts if t in prompt)
    assert not_selected_count == 0, f"未选中义项出现在 prompt 中: {other_texts}"


def test_generate_quiz_multi_sense_answer_is_selected_def(isolated_storage):
    """多义词占位 answer：zh_classical 编码为 '词性|释义'，其他语言为选中义项 text"""
    from vocabcraft_mcp.tools.crud import save_vocab
    data = {
        "id": "vocab_001",
        "structured": {
            "word": "病",
            "phonetic": "",
            "part_of_speech": "n.",
            "definitions": [
                {"text": "疾病", "examples": []},
                {"text": "生病", "examples": []},
            ],
            "language": "zh_classical",
        },
    }
    save_vocab(data)
    result = generate_quiz("vocab_001", "释义")
    quizzes = result["quizzes"]
    assert len(quizzes) == 1
    idx = quizzes[0]["quiz"]["definition_index"]
    assert quizzes[0]["quiz"]["answer"] == f"n.|{['疾病', '生病'][idx]}"


def test_generate_quiz_non_classical_multi_sense_answer_is_plain_text(isolated_storage):
    """非 zh_classical 多义词的释义题 answer 仍为纯释义文本"""
    from vocabcraft_mcp.tools.crud import save_vocab
    data = {
        "id": "vocab_001",
        "structured": {
            "word": "run",
            "phonetic": "/rʌn/",
            "part_of_speech": "v.",
            "definitions": [
                {"text": "跑", "examples": ["I run every morning."]},
                {"text": "经营", "examples": ["She runs a company."]},
            ],
            "language": "en",
        },
    }
    save_vocab(data)
    result = generate_quiz("vocab_001", "释义")
    idx = result["quiz"]["definition_index"]
    assert result["quiz"]["answer"] == ["跑", "经营"][idx]
    assert "|" not in result["quiz"]["answer"]


def test_generate_quiz_classical_empty_pos_uses_placeholder(isolated_storage):
    """zh_classical 释义题词性为空时，answer 用 '?' 占位"""
    from vocabcraft_mcp.tools.crud import save_vocab
    data = {
        "id": "vocab_001",
        "structured": {
            "word": "兵",
            "phonetic": "",
            "part_of_speech": "",
            "definitions": [
                {"text": "兵器", "examples": []},
                {"text": "士兵", "examples": []},
            ],
            "language": "zh_classical",
        },
    }
    save_vocab(data)
    result = generate_quiz("vocab_001", "释义")
    quizzes = result["quizzes"]
    assert len(quizzes) == 1
    idx = quizzes[0]["quiz"]["definition_index"]
    assert quizzes[0]["quiz"]["answer"] == f"?|{['兵器', '士兵'][idx]}"


def test_grade_quiz_propagates_definition_index(isolated_storage):
    """评分后 ReviewRecord.definition_index 透传自 Quiz"""
    from vocabcraft_mcp.tools.crud import save_vocab
    data = {
        "id": "vocab_001",
        "structured": {
            "word": "病",
            "phonetic": "",
            "part_of_speech": "n.",
            "definitions": [
                {"text": "疾病", "examples": []},
                {"text": "生病", "examples": []},
            ],
            "language": "zh_classical",
        },
    }
    save_vocab(data)
    gen = generate_quiz("vocab_001", "释义")
    quizzes = gen["quizzes"]
    assert len(quizzes) == 1
    expected_idx = quizzes[0]["quiz"]["definition_index"]

    grade_quiz(quizzes[0]["quiz_id"], "疾病")
    records = get_storage().list_all_review_records()
    assert len(records) == 1
    assert records[0].definition_index == expected_idx


def test_grade_quiz_definition_index_none_for_legacy_quiz(isolated_storage, make_vocab_data):
    """旧 Quiz（definition_index=None）评分后 ReviewRecord.definition_index=None"""
    from datetime import datetime
    from vocabcraft_mcp.models import Quiz
    from vocabcraft_mcp.tools.crud import save_vocab, get_storage

    save_vocab(make_vocab_data("hello", "vocab_001"))
    # 手动构造一个无 definition_index 的旧式 Quiz
    storage = get_storage()
    legacy_quiz = Quiz(
        id="quiz_20260725_001",
        vocab_id="vocab_001",
        quiz_type="拼写",
        question="题干",
        answer="hello",
        generated_at=datetime.now(),
    )
    storage.save_quiz(legacy_quiz)

    grade_quiz("quiz_20260725_001", "hello")
    records = get_storage().list_all_review_records()
    assert len(records) == 1
    assert records[0].definition_index is None


def _make_classical_vocab(vocab_id: str = "vocab_001", pos: str = "n."):
    """构造 zh_classical 测试词汇数据"""
    return {
        "id": vocab_id,
        "structured": {
            "word": "兵",
            "phonetic": "",
            "part_of_speech": pos,
            "definitions": [
                {"text": "兵器", "examples": ["收天下之兵"]},
                {"text": "士兵，军队", "examples": ["赵兵果败"]},
            ],
            "language": "zh_classical",
        },
    }


def test_grade_quiz_classical_definition_correct(isolated_storage):
    """zh_classical 释义题答对：grade=5, correct=True"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab(_make_classical_vocab())
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]

    result = grade_quiz(q["quiz_id"], q["quiz"]["answer"])
    assert result["grade"] == 5
    assert result["correct"] is True
    assert "grade_prompt" not in result


def test_grade_quiz_classical_definition_wrong(isolated_storage):
    """zh_classical 释义题答错：grade=0, correct=False"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab(_make_classical_vocab())
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]

    result = grade_quiz(q["quiz_id"], "兵器")
    assert result["grade"] == 0
    assert result["correct"] is False


def test_grade_quiz_classical_definition_case_insensitive_pos(isolated_storage):
    """zh_classical 释义题词性大小写不敏感"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab(_make_classical_vocab(pos="N."))
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]
    # answer 编码为 "N.|兵器"，用户小写输入仍应判对
    result = grade_quiz(q["quiz_id"], "n.|兵器")
    assert result["grade"] == 5
    assert result["correct"] is True


def test_grade_quiz_classical_definition_strict_meaning(isolated_storage):
    """zh_classical 释义题释义严格一致"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab(_make_classical_vocab())
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]

    # 释义不同则判错
    result = grade_quiz(q["quiz_id"], "n.|武器")
    assert result["grade"] == 0
    assert result["correct"] is False


def test_grade_quiz_classical_definition_empty_pos_placeholder(isolated_storage):
    """zh_classical 释义题词性为空时，按 '?|释义' 格式评分"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab(_make_classical_vocab(pos=""))
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]
    assert q["quiz"]["answer"].startswith("?|")

    result = grade_quiz(q["quiz_id"], q["quiz"]["answer"])
    assert result["grade"] == 5
    assert result["correct"] is True


def test_grade_quiz_classical_definition_pipe_in_meaning(isolated_storage):
    """zh_classical 释义题释义中可含 '|'"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab({
        "id": "vocab_001",
        "structured": {
            "word": "test",
            "phonetic": "",
            "part_of_speech": "n.",
            "definitions": [
                {"text": "a|b|c", "examples": []},
            ],
            "language": "zh_classical",
        },
    })
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]
    assert q["quiz"]["answer"] == "n.|a|b|c"

    result = grade_quiz(q["quiz_id"], "n.|a|b|c")
    assert result["grade"] == 5
    assert result["correct"] is True


def test_grade_quiz_classical_definition_quote_mismatch(isolated_storage):
    """释义中中文单双引号不一致时应判错"""
    from vocabcraft_mcp.tools.crud import save_vocab

    # 标准答案使用中文双引号
    save_vocab({
        "id": "vocab_001",
        "structured": {
            "word": "长",
            "phonetic": "",
            "part_of_speech": "adj.",
            "definitions": [
                {"text": "与\"短\"相对", "examples": [], "part_of_speech": "形容词"},
            ],
            "language": "zh_classical",
        },
    })
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]
    assert q["quiz"]["answer"] == "adj.|与\"短\"相对"

    # 用户输入中文单引号，应判错
    result = grade_quiz(q["quiz_id"], "adj.|与'短'相对")
    assert result["grade"] == 0
    assert result["correct"] is False


def test_grade_quiz_classical_definition_updates_sm2(isolated_storage):
    """zh_classical 释义题评分后仍更新 SM-2 状态与复习记录"""
    from vocabcraft_mcp.tools.crud import save_vocab, get_storage

    save_vocab(_make_classical_vocab())
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]

    result = grade_quiz(q["quiz_id"], q["quiz"]["answer"])
    assert result["grade"] == 5

    v = get_storage().load_vocab("vocab_001")
    assert v.review_state.repetitions == 1
    assert v.review_state.ease_factor == pytest.approx(2.6, abs=1e-3)

    records = get_storage().list_all_review_records()
    assert len(records) == 1
    assert records[0].definition_index == q["quiz"]["definition_index"]


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
    assert r1["quizzes"][0]["quiz"]["definition_index"] == 0

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
    assert r2["quizzes"][0]["quiz"]["definition_index"] == 1


def test_classical_generate_prompt_exists():
    """文言文专用生成 prompt 存在且包含关键要求"""
    assert "词性" in CLASSICAL_GENERATE_PROMPT
    assert "释义" in CLASSICAL_GENERATE_PROMPT
    assert "<mark>{word}</mark>" in CLASSICAL_GENERATE_PROMPT
    assert "词性|释义文本" in CLASSICAL_GENERATE_PROMPT


def test_generate_classical_quiz_uses_classical_prompt(isolated_storage):
    """zh_classical 释义题返回 CLASSICAL_GENERATE_PROMPT"""
    save_vocab({
        "id": "vocab_prompt_001",
        "structured": {
            "word": "兵",
            "phonetic": "",
            "part_of_speech": "n.",
            "language": "zh_classical",
            "definitions": [
                {"text": "兵器", "examples": ["收天下之兵"]},
            ],
        },
    })

    result = generate_quiz("vocab_prompt_001", "释义")
    quizzes = result["quizzes"]
    assert len(quizzes) == 1
    prompt = quizzes[0]["generate_prompt"]
    # 专用 prompt 的占位符应已被渲染
    assert "词汇：兵" in prompt
    assert "词性：n." in prompt
    assert "兵器" in prompt
    assert "收天下之兵" in prompt
    # 不应包含默认 prompt 的「音标」字段
    assert "音标：" not in prompt


def test_generate_non_classical_definition_uses_default_prompt(isolated_storage, make_vocab_data):
    """非 zh_classical 释义题仍使用默认 GENERATE_PROMPT"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    result = generate_quiz("vocab_001", "释义")
    prompt = result["generate_prompt"]
    # 默认 prompt 包含音标与题型说明
    assert "音标：" in prompt
    assert "题型：释义" in prompt


def test_grade_quiz_transfers_example_index(isolated_storage):
    """grade_quiz 应将 Quiz.example_index 透传到 ReviewRecord"""
    from vocabcraft_mcp.tools.crud import save_vocab
    data = {
        "id": "vocab_exgrad_001",
        "structured": {
            "word": "兵",
            "phonetic": "",
            "part_of_speech": "n.",
            "language": "zh_classical",
            "definitions": [
                {"text": "兵器", "examples": ["收天下之兵", "兵者国之大事"]},
            ],
        },
    }
    save_vocab(data)

    result = generate_quiz("vocab_exgrad_001", "释义")
    quizzes = result["quizzes"]
    assert len(quizzes) == 2

    # 评分第一道（example_index=0）
    grade_result = grade_quiz(quizzes[0]["quiz_id"], "n.|兵器")
    assert grade_result["grade"] == 5

    # 检查 ReviewRecord 包含 example_index
    records = get_storage().list_all_review_records()
    ex_indices = [r.example_index for r in records if r.vocab_id == "vocab_exgrad_001"]
    assert 0 in ex_indices


def test_least_reviewed_definition_index_by_example(isolated_storage):
    """_least_reviewed_definition_index 应统计 (def_idx, ex_idx) 覆盖"""
    from vocabcraft_mcp.tools.quiz import _least_reviewed_definition_index
    from vocabcraft_mcp.models import Definition, ReviewRecord
    from datetime import datetime, timezone

    defs = [
        Definition(text="兵器", examples=["收天下之兵", "兵者国之大事"], part_of_speech="n."),
        Definition(text="士兵", examples=["赵兵果败"], part_of_speech="n."),
    ]

    # 模拟：义项0例句0已复习1次，其余为0
    rec = ReviewRecord(
        record_id="rec_ex_001",
        vocab_id="vocab_ex_001",
        review_time=datetime.now(timezone.utc),
        grade=5, prev_ease=2.5, new_ease=2.6,
        definition_index=0, example_index=0,
    )
    get_storage().save_review_record(rec)

    result = _least_reviewed_definition_index("vocab_ex_001", defs, get_storage())
    # 义项0有1次复习，义项1有0次 → 应返回义项1
    assert result == 1





def test_grade_quiz_classical_definition_with_pos_prefix(isolated_storage):
    """用户释义带词性前缀时仍能判对"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab(_make_classical_vocab())
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]

    result = grade_quiz(q["quiz_id"], "n.|兵器")
    assert result["grade"] == 5
    assert result["correct"] is True


def test_grade_quiz_classical_definition_with_zh_pos_prefix(isolated_storage):
    """用户释义带中文词性前缀时仍能判对"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab(_make_classical_vocab(pos="名词"))
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]

    result = grade_quiz(q["quiz_id"], "名词|兵器")
    assert result["grade"] == 5
    assert result["correct"] is True


def test_grade_quiz_classical_definition_mixed_pos_style(isolated_storage):
    """期望英文词性、用户回答中文词性（或相反）时仍能判对"""
    from vocabcraft_mcp.tools.crud import save_vocab

    save_vocab(_make_classical_vocab(pos="n."))
    gen = generate_quiz("vocab_001", "释义")
    q = gen["quizzes"][0]

    # 期望 n.|兵器，用户用中文词性回答
    result = grade_quiz(q["quiz_id"], "名词|兵器")
    assert result["grade"] == 5
    assert result["correct"] is True


def test_generate_classical_quiz_expands_examples(isolated_storage):
    """zh_classical 释义题应为每个例句生成独立 quiz"""
    save_vocab({
        "id": "vocab_multi_001",
        "structured": {
            "word": "兵",
            "phonetic": "",
            "part_of_speech": "n.",
            "language": "zh_classical",
            "definitions": [
                {"text": "兵器", "examples": ["收天下之兵", "兵者国之大事"]},
                {"text": "士兵", "examples": ["赵兵果败"]},
            ],
        },
    })

    result = generate_quiz("vocab_multi_001", "释义")
    # 应返回 quizzes 列表（非 quiz_id）
    assert "quizzes" in result
    quizzes = result["quizzes"]
    # 义项0有2个例句 → 2道题
    assert len(quizzes) == 2
    # 每道题有独立的 quiz_id 和 generate_prompt
    for q in quizzes:
        assert "quiz_id" in q
        assert "generate_prompt" in q
        assert "quiz" in q
    # definition_index 一致（同一义项）
    assert quizzes[0]["quiz"]["definition_index"] == quizzes[1]["quiz"]["definition_index"]
    # example_index 分别为 0 和 1
    assert quizzes[0]["quiz"]["example_index"] == 0
    assert quizzes[1]["quiz"]["example_index"] == 1


def test_generate_classical_quiz_no_examples_fallback(isolated_storage):
    """zh_classical 义项无例句时降级为单道题"""
    save_vocab({
        "id": "vocab_noex_001",
        "structured": {
            "word": "兵",
            "phonetic": "",
            "part_of_speech": "n.",
            "language": "zh_classical",
            "definitions": [
                {"text": "兵器", "examples": []},
            ],
        },
    })

    result = generate_quiz("vocab_noex_001", "释义")
    assert "quizzes" in result
    assert len(result["quizzes"]) == 1
    assert result["quizzes"][0]["quiz"]["example_index"] is None
