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
    idx = result["quiz"]["definition_index"]
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
    prompt = result["generate_prompt"]
    idx = result["quiz"]["definition_index"]
    selected_text = ["疾病", "生病", "担心"][idx]
    # 选中义项必须在 prompt 中
    assert selected_text in prompt
    # 未选中的两个义项不应同时出现在 prompt 的义项列表中
    other_texts = [t for i, t in enumerate(["疾病", "生病", "担心"]) if i != idx]
    not_selected_count = sum(1 for t in other_texts if t in prompt)
    assert not_selected_count == 0, f"未选中义项出现在 prompt 中: {other_texts}"


def test_generate_quiz_multi_sense_answer_is_selected_def(isolated_storage):
    """多义词占位 answer = 选中义项的 text"""
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
    idx = result["quiz"]["definition_index"]
    assert result["quiz"]["answer"] == ["疾病", "生病"][idx]


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
    expected_idx = gen["quiz"]["definition_index"]

    grade_quiz(gen["quiz_id"], "疾病")
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
