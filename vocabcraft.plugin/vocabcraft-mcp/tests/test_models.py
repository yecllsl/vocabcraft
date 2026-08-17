# tests/test_models.py
"""Pydantic 数据模型单元测试

验证核心模型可正常构造、默认值填充与字段校验器工作。
模型层级: StructuredVocab + ReviewState → VocabRecord；Quiz；ReviewRecord；ReviewSchedule
"""

from datetime import UTC, datetime

import pytest

from vocabcraft_mcp.models import (
    Definition,
    Quiz,
    ReviewRecord,
    ReviewSchedule,
    ReviewState,
    StructuredVocab,
    VocabRecord,
)

# ──────────────────────────────────────────
# StructuredVocab
# ──────────────────────────────────────────

def test_structured_vocab_required_word():
    """StructuredVocab 必填 word"""
    v = StructuredVocab(word="hello")
    assert v.word == "hello"


def test_structured_vocab_defaults():
    """StructuredVocab 默认值"""
    v = StructuredVocab(word="hello")
    assert v.phonetic == ""
    assert v.part_of_speech == ""
    assert v.definitions == []
    assert v.language == "en"
    assert v.source_image is None
    # 顶层 examples 字段已删除（迁移到 definitions[i].examples）
    assert not hasattr(v, "examples")


def test_structured_vocab_full():
    """StructuredVocab 完整字段构造（新格式 definitions 内嵌 examples）"""
    v = StructuredVocab(
        word="abandon", phonetic="/əˈbændən/", part_of_speech="v.",
        definitions=[
            Definition(text="放弃", examples=["He abandoned his car."]),
            Definition(text="遗弃", examples=[]),
        ],
        language="en", source_image="/data/images/x.jpg",
    )
    assert v.part_of_speech == "v."
    assert len(v.definitions) == 2
    assert v.definitions[0].text == "放弃"
    assert v.definitions[0].examples == ["He abandoned his car."]
    assert v.definitions[1].text == "遗弃"
    assert v.definitions[1].examples == []
    assert v.source_image == "/data/images/x.jpg"


def test_structured_vocab_definitions_dict_input():
    """StructuredVocab 接受 dict 形式 definitions（不通过 Definition 模型构造）"""
    v = StructuredVocab(
        word="兵",
        definitions=[
            {"text": "兵器", "examples": ["收天下之兵"]},
            {"text": "士兵", "examples": []},
        ],
    )
    assert isinstance(v.definitions[0], Definition)
    assert v.definitions[0].text == "兵器"
    assert v.definitions[0].examples == ["收天下之兵"]


def test_structured_vocab_legacy_format_compat():
    """旧格式（list[str] definitions + 顶层 examples）自动转换为新格式

    旧 JSON 文件加载时由 model_validator(mode="before") 自动归并：
    - list[str] definitions → list[Definition]（examples=[]）
    - 顶层 examples 全部归并到 definitions[0].examples
    """
    v = StructuredVocab(
        word="兵",
        definitions=["兵器", "士兵"],
        examples=["收天下之兵", "项羽兵四十万"],
    )
    assert len(v.definitions) == 2
    assert v.definitions[0].text == "兵器"
    # 旧 examples 全部归并到 definitions[0].examples
    assert v.definitions[0].examples == ["收天下之兵", "项羽兵四十万"]
    assert v.definitions[1].text == "士兵"
    assert v.definitions[1].examples == []
    # 顶层 examples 字段已删除
    assert not hasattr(v, "examples")


def test_structured_vocab_legacy_examples_without_definitions():
    """旧格式边界：有 examples 无 definitions 时，建空释义承载避免数据丢失"""
    v = StructuredVocab(word="x", definitions=[], examples=["例句1"])
    assert len(v.definitions) == 1
    assert v.definitions[0].text == ""
    assert v.definitions[0].examples == ["例句1"]


# ──────────────────────────────────────────
# ReviewState
# ──────────────────────────────────────────

def test_review_state_defaults():
    """ReviewState 默认值：EF=2.5, interval=0, repetitions=0"""
    rs = ReviewState()
    assert rs.ease_factor == 2.5
    assert rs.interval == 0
    assert rs.repetitions == 0
    assert rs.next_review == ""
    assert rs.last_review is None


def test_review_state_full():
    """ReviewState 完整字段构造"""
    rs = ReviewState(
        ease_factor=2.36, interval=6, repetitions=2,
        next_review="2026-07-30", last_review="2026-07-23",
    )
    assert rs.ease_factor == 2.36
    assert rs.next_review == "2026-07-30"


# ──────────────────────────────────────────
# VocabRecord
# ──────────────────────────────────────────

def _make_structured() -> StructuredVocab:
    return StructuredVocab(word="hello", language="en")


def test_vocab_record_required_fields():
    """VocabRecord 必填：id/structured/created_at/updated_at"""
    now = datetime.now(UTC)
    v = VocabRecord(
        id="vocab_001", structured=_make_structured(),
        created_at=now, updated_at=now,
    )
    assert v.id == "vocab_001"
    assert v.structured.word == "hello"
    # review_state 默认注入
    assert v.review_state.ease_factor == 2.5


def test_vocab_record_id_prefix_validation():
    """VocabRecord.id 必须以 vocab_ 开头"""
    now = datetime.now(UTC)
    with pytest.raises(ValueError):
        VocabRecord(
            id="invalid_id", structured=_make_structured(),
            created_at=now, updated_at=now,
        )


# ──────────────────────────────────────────
# Quiz
# ──────────────────────────────────────────

def test_quiz_required_fields():
    """Quiz 必填字段"""
    now = datetime.now(UTC)
    q = Quiz(
        id="quiz_001", vocab_id="vocab_001", quiz_type="拼写",
        question="请拼写 /həˈləʊ/", answer="hello", generated_at=now,
    )
    assert q.id == "quiz_001"
    assert q.options is None  # 默认 None
    assert q.graded is False


def test_quiz_with_options():
    """Quiz 选择题含 options"""
    now = datetime.now(UTC)
    q = Quiz(
        id="quiz_002", vocab_id="vocab_001", quiz_type="选择",
        question="hello 的释义是？",
        options=["你好", "再见", "谢谢", "对不起"],
        answer="你好", generated_at=now,
    )
    assert len(q.options) == 4


def test_quiz_type_validation():
    """quiz_type 必须为 选择/填空/拼写/释义 之一"""
    now = datetime.now(UTC)
    with pytest.raises(ValueError):
        Quiz(
            id="quiz_003", vocab_id="vocab_001", quiz_type="无效题型",
            question="?", answer="?", generated_at=now,
        )


def test_quiz_id_prefix_validation():
    """Quiz.id 必须以 quiz_ 开头"""
    now = datetime.now(UTC)
    with pytest.raises(ValueError):
        Quiz(
            id="invalid_id", vocab_id="vocab_001", quiz_type="选择",
            question="?", answer="?", generated_at=now,
        )


# ──────────────────────────────────────────
# ReviewRecord
# ──────────────────────────────────────────

def test_review_record_required_fields():
    """ReviewRecord 必填字段"""
    now = datetime.now(UTC)
    r = ReviewRecord(
        record_id="rec_001", vocab_id="vocab_001", review_time=now,
        grade=4, prev_ease=2.5, new_ease=2.6,
    )
    assert r.record_id == "rec_001"
    assert r.grade == 4


def test_review_record_grade_validation():
    """grade 必须在 1-4"""
    now = datetime.now(UTC)
    with pytest.raises(ValueError):
        ReviewRecord(
            record_id="rec_002", vocab_id="vocab_001", review_time=now,
            grade=5, prev_ease=2.5, new_ease=2.5,
        )
    with pytest.raises(ValueError):
        ReviewRecord(
            record_id="rec_003", vocab_id="vocab_001", review_time=now,
            grade=0, prev_ease=2.5, new_ease=2.5,
        )


# ──────────────────────────────────────────
# ReviewSchedule
# ──────────────────────────────────────────

def test_review_schedule_defaults():
    """ReviewSchedule 默认 status=待复习"""
    s = ReviewSchedule(vocab_id="vocab_001", due_date="2026-07-24")
    assert s.status == "待复习"
    assert s.quiz_id is None


def test_review_schedule_status_validation():
    """status 必须为 待复习/已完成/已跳过"""
    with pytest.raises(ValueError):
        ReviewSchedule(vocab_id="vocab_001", due_date="2026-07-24", status="无效")


# ──────────────────────────────────────────
# definition_index（N-05 多义词义项追踪）
# ──────────────────────────────────────────

def test_quiz_definition_index_default_none():
    """Quiz 新字段 definition_index 默认 None"""
    from datetime import datetime

    from vocabcraft_mcp.models import Quiz
    q = Quiz(
        id="quiz_20260725_001",
        vocab_id="vocab_20260725_001",
        quiz_type="拼写",
        question="题干",
        answer="hello",
        generated_at=datetime.now(),
    )
    assert q.definition_index is None


def test_review_record_definition_index_default_none():
    """ReviewRecord 新字段 definition_index 默认 None"""
    from datetime import datetime

    from vocabcraft_mcp.models import ReviewRecord
    r = ReviewRecord(
        record_id="rec_20260725_001",
        vocab_id="vocab_20260725_001",
        review_time=datetime.now(),
        grade=4,
        prev_ease=2.5,
        new_ease=2.6,
    )
    assert r.definition_index is None


def test_quiz_legacy_json_without_definition_index():
    """旧 Quiz JSON（无 definition_index）反序列化为 None"""
    import json

    from vocabcraft_mcp.models import Quiz
    legacy = {
        "id": "quiz_20260725_001",
        "vocab_id": "vocab_20260725_001",
        "quiz_type": "拼写",
        "question": "题干",
        "answer": "hello",
        "generated_at": "2026-07-25T00:00:00Z",
        "graded": False,
    }
    q = Quiz.model_validate(json.loads(json.dumps(legacy)))
    assert q.definition_index is None


def test_review_record_legacy_json_without_definition_index():
    """旧 ReviewRecord JSON（无 definition_index）反序列化为 None"""
    import json

    from vocabcraft_mcp.models import ReviewRecord
    legacy = {
        "record_id": "rec_20260725_001",
        "vocab_id": "vocab_20260725_001",
        "review_time": "2026-07-25T00:00:00Z",
        "grade": 4,
        "prev_ease": 2.5,
        "new_ease": 2.6,
    }
    r = ReviewRecord.model_validate(json.loads(json.dumps(legacy)))
    assert r.definition_index is None


# ──────────────────────────────────────────
# Definition.part_of_speech（义项级词性）
# ──────────────────────────────────────────

def test_definition_part_of_speech_default():
    """Definition.part_of_speech 默认空串"""
    d = Definition(text="hello", examples=[])
    assert d.part_of_speech == ""


def test_definition_part_of_speech_explicit():
    """Definition.part_of_speech 可显式传入"""
    d = Definition(text="兵器", examples=["收天下之兵"], part_of_speech="名词")
    assert d.part_of_speech == "名词"


# ──────────────────────────────────────────
# word_type / original_char（虚词、通假字）
# ──────────────────────────────────────────

def test_structured_vocab_word_type_default():
    """StructuredVocab.word_type 默认'实词'"""
    v = StructuredVocab(word="之")
    assert v.word_type == "实词"


def test_structured_vocab_word_type_valid():
    """word_type 接受 实词/虚词/通假字"""
    for wt in ["实词", "虚词", "通假字"]:
        v = StructuredVocab(word="之", word_type=wt)
        assert v.word_type == wt


def test_structured_vocab_word_type_invalid():
    """word_type 非法值拒绝（白名单硬防线）"""
    with pytest.raises(ValueError):
        StructuredVocab(word="之", word_type="名词")


def test_structured_vocab_original_char_default():
    """original_char 默认空串"""
    v = StructuredVocab(word="说")
    assert v.original_char == ""


def test_structured_vocab_original_char_transparent():
    """original_char 透传保存"""
    v = StructuredVocab(word="说", word_type="通假字", original_char="悦")
    assert v.original_char == "悦"


def test_structured_vocab_legacy_json_default_word_type():
    """旧 JSON（无 word_type/original_char）反序列化为默认值，不报错"""
    import json

    legacy = {"word": "兵", "definitions": [{"text": "兵器"}]}
    v = StructuredVocab.model_validate(json.loads(json.dumps(legacy)))
    assert v.word_type == "实词"
    assert v.original_char == ""
