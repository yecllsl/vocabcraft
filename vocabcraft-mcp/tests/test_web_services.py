# tests/test_web_services.py
"""测试 Web 服务层 — 编排 storage/statistics/review/quiz"""
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from vocabcraft_mcp.models import Definition, ReviewState, StructuredVocab, VocabRecord
from vocabcraft_mcp.storage import Storage
from vocabcraft_mcp.web import services


@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    """创建临时 storage 并注入 services 模块"""
    storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: storage)
    # 同时隔离底层 crud 的默认目录，避免 quiz 工具读到真实数据
    monkeypatch.setattr("vocabcraft_mcp.tools.crud._DEFAULT_DATA_DIR", tmp_path)
    return storage


def _make_vocab(word, vid, language="en", repetitions=0, next_review=""):
    """构造完整测试词汇（definitions 内嵌 examples 新格式）"""
    return VocabRecord(
        id=vid,
        structured=StructuredVocab(
            word=word,
            phonetic="/test/",
            part_of_speech="n.",
            definitions=[Definition(text=f"{word} 的释义", examples=[f"This is {word}."])],
            language=language,
        ),
        review_state=ReviewState(
            repetitions=repetitions,
            next_review=next_review,
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ──────────────────────────────────────────
# Dashboard summary 测试
# ──────────────────────────────────────────

def test_dashboard_summary_empty(temp_storage):
    """无数据时应返回零值"""
    summary = services.get_dashboard_summary()
    assert summary["total"] == 0
    assert summary["today_pending"] == 0
    assert summary["week_new"] == 0
    assert summary["mastered"] == 0
    assert summary["language_distribution"] == []
    assert summary["mastery_distribution"] == [
        {"name": "新词", "value": 0},
        {"name": "生疏", "value": 0},
        {"name": "熟悉", "value": 0},
        {"name": "掌握", "value": 0},
    ]
    assert len(summary["trends"]) == 30
    assert all(v == 0 for v in summary["trends"].values())


def test_dashboard_summary_with_data(temp_storage):
    """有数据时应正确统计"""
    today = datetime.now(timezone.utc).date().isoformat()
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", language="en", next_review=today))
    temp_storage.save_vocab(_make_vocab("世界", "vocab_002", language="zh", repetitions=6))

    summary = services.get_dashboard_summary()
    assert summary["total"] == 2
    assert summary["today_pending"] == 1
    assert summary["mastered"] == 1

    languages = {item["name"] for item in summary["language_distribution"]}
    assert "en" in languages
    assert "zh" in languages


# ──────────────────────────────────────────
# Multi-dim stats 测试
# ──────────────────────────────────────────

def test_multi_dim_stats(temp_storage):
    """多维统计应返回分布与趋势数据"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))
    temp_storage.save_vocab(_make_vocab("world", "vocab_002", language="en"))

    multi = services.get_multi_dim_stats()
    assert "language_distribution" in multi
    assert "mastery_distribution" in multi
    assert "quiz_type_distribution" in multi
    assert "trend_data" in multi
    assert len(multi["trend_data"]) == 30


# ──────────────────────────────────────────
# 待复习列表测试
# ──────────────────────────────────────────

def test_upcoming_reviews(temp_storage):
    """应返回已到期的词汇"""
    today = datetime.now(timezone.utc).date().isoformat()
    temp_storage.save_vocab(_make_vocab("due", "vocab_001", next_review=today))
    temp_storage.save_vocab(_make_vocab("future", "vocab_002", next_review="2099-01-01"))

    upcoming = services.get_upcoming_reviews()
    assert len(upcoming) == 1
    assert upcoming[0]["vocab_id"] == "vocab_001"


# ──────────────────────────────────────────
# 复习日历测试
# ──────────────────────────────────────────

def test_review_calendar(temp_storage):
    """日历应包含当月每一天"""
    today = datetime.now(timezone.utc)
    temp_storage.save_vocab(_make_vocab("due", "vocab_001", next_review=today.date().isoformat()))

    calendar = services.get_review_calendar()
    assert "calendar_days" in calendar
    assert len(calendar["calendar_days"]) >= 28
    assert any(day["is_today"] for day in calendar["calendar_days"])


# ──────────────────────────────────────────
# 出题与评分测试
# ──────────────────────────────────────────

def test_generate_web_quiz(temp_storage):
    """应能生成 Web 考题并填充题干"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001"))
    result = services.generate_web_quiz("vocab_001", "拼写")
    assert result is not None
    assert result["quiz"]["quiz_type"] == "拼写"
    assert "释义" in result["quiz"]["question"] or "拼写" in result["quiz"]["question"]


def test_generate_web_quiz_unknown_vocab(temp_storage):
    """词汇不存在返回 None"""
    assert services.generate_web_quiz("vocab_missing", "拼写") is None


def test_grade_web_quiz(temp_storage):
    """评分后应更新记忆状态"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001"))
    quiz_result = services.generate_web_quiz("vocab_001", "拼写")
    quiz_id = quiz_result["quiz_id"]

    result = services.grade_web_quiz(quiz_id, "hello")
    assert result["grade"] == 5
    assert result["correct"] is True
    assert "updated_review_state" in result


# ──────────────────────────────────────────
# 词汇管理测试
# ──────────────────────────────────────────

def test_list_vocabs_for_web(temp_storage):
    """词汇列表应支持按语言/关键词过滤"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))
    temp_storage.save_vocab(_make_vocab("世界", "vocab_002", language="zh"))

    all_vocabs = services.list_vocabs_for_web()
    assert len(all_vocabs) == 2

    en_vocabs = services.list_vocabs_for_web(language="en")
    assert len(en_vocabs) == 1
    assert en_vocabs[0]["word"] == "hello"

    filtered = services.list_vocabs_for_web(keyword="世界")
    assert len(filtered) == 1
    assert filtered[0]["word"] == "世界"


def test_get_vocab_detail(temp_storage):
    """词汇详情应包含结构化字段与时间戳"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))
    detail = services.get_vocab_detail("vocab_001")
    assert detail is not None
    assert detail["word"] == "hello"
    assert detail["language"] == "en"
    assert "created_at" in detail
    assert "updated_at" in detail


def test_update_vocab_from_web(temp_storage):
    """Web 表单更新应修改词汇结构化信息并保留 source_image

    表单 definitions textarea 每行格式：`释义文本|例句1;例句2`
    """
    vocab = _make_vocab("hello", "vocab_001", language="en")
    vocab.structured.source_image = "images/test.png"
    temp_storage.save_vocab(vocab)

    updated = services.update_vocab_from_web("vocab_001", {
        "word": "hi",
        "phonetic": "/haɪ/",
        "part_of_speech": "int.",
        "language": "de",
        # 新格式：两行释义，第一行带例句
        "definitions": "你好|Hi, there.;Hi!\n您好",
    })
    assert updated is not None
    assert updated["word"] == "hi"
    assert updated["language"] == "de"
    # definitions 返回 list[dict]（每项 {text, examples}）
    assert len(updated["definitions"]) == 2
    assert updated["definitions"][0]["text"] == "你好"
    assert updated["definitions"][0]["examples"] == ["Hi, there.", "Hi!"]
    assert updated["definitions"][1]["text"] == "您好"
    assert updated["definitions"][1]["examples"] == []

    # source_image 应保留
    reloaded = temp_storage.load_vocab("vocab_001")
    assert reloaded.structured.source_image == "images/test.png"


def test_delete_vocab(temp_storage):
    """删除词汇应成功"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001"))
    assert services.delete_vocab("vocab_001") is True
    assert temp_storage.load_vocab("vocab_001") is None


# ──────────────────────────────────────────
# 批量复习测试
# ──────────────────────────────────────────

def _today_iso():
    """当前 UTC 日期字符串"""
    return datetime.now(timezone.utc).date().isoformat()


def test_start_batch_review_with_due_words(temp_storage):
    """有到期词汇时应创建批量复习会话"""
    today = _today_iso()
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", next_review=today))
    temp_storage.save_vocab(_make_vocab("world", "vocab_002", next_review=today))
    temp_storage.save_vocab(_make_vocab("future", "vocab_003", next_review="2099-01-01"))

    batch = services.start_batch_review()
    assert batch is not None
    assert batch["total"] == 2

    # 第 0 题应存在
    item = services.get_batch_review_item(batch["batch_id"], 0)
    assert item is not None
    assert item["index"] == 0
    assert item["total"] == 2


def test_start_batch_review_no_due_words(temp_storage):
    """无到期词汇时返回 None"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", next_review="2099-01-01"))
    assert services.start_batch_review() is None


def test_grade_batch_review_item(temp_storage):
    """批量评分应推进到下一题并更新记忆状态"""
    today = _today_iso()
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", next_review=today))
    temp_storage.save_vocab(_make_vocab("world", "vocab_002", next_review=today))

    batch = services.start_batch_review()
    batch_id = batch["batch_id"]

    # 第一题答错
    graded = services.grade_batch_review_item(batch_id, 0, "wrong")
    assert graded is not None
    assert graded["is_last"] is False
    assert graded["next_index"] == 1

    # 第二题答对
    graded = services.grade_batch_review_item(batch_id, 1, "world")
    assert graded is not None
    assert graded["is_last"] is True
    assert graded["next_index"] is None


def test_get_batch_review_summary(temp_storage):
    """汇总应包含题数、均分、薄弱词、下次复习分布"""
    today = _today_iso()
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", next_review=today))
    temp_storage.save_vocab(_make_vocab("world", "vocab_002", next_review=today))

    batch = services.start_batch_review()
    batch_id = batch["batch_id"]
    services.grade_batch_review_item(batch_id, 0, "wrong")
    services.grade_batch_review_item(batch_id, 1, "world")

    summary = services.get_batch_review_summary(batch_id)
    assert summary is not None
    assert summary["total"] == 2
    assert summary["graded_count"] == 2
    assert summary["avg_grade"] == 2.5
    assert len(summary["weak_words"]) == 1
    assert summary["weak_words"][0]["word"] == "hello"
    assert summary["next_review_distribution"] != {}
