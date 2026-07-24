# tests/test_tools_review.py
"""复习排程 Tool 单元测试

验证 schedule_review 真实行为:
    - 指定 vocab_id 返回该词复习状态
    - 未指定返回到期词汇列表（next_review <= today）
    - 无到期词返回 due_count=0
    - 不存在词汇返回 error
"""

from datetime import datetime, timezone

import pytest

from vocabcraft_mcp.tools.review import schedule_review
from vocabcraft_mcp.tools.crud import save_vocab


def _save_with_review(word: str, vocab_id: str, next_review: str, make_vocab_data) -> None:
    """保存词汇并指定 next_review（用于构造到期/未到期场景）"""
    data = make_vocab_data(word=word, vocab_id=vocab_id)
    data["review_state"] = {"next_review": next_review}
    save_vocab(data)


def test_review_importable():
    """模块可正常 import"""
    assert callable(schedule_review)


def test_schedule_review_single_vocab(isolated_storage, make_vocab_data):
    """指定 vocab_id 返回复习状态"""
    _save_with_review("hello", "vocab_001", "2026-07-30", make_vocab_data)

    result = schedule_review("vocab_001")
    assert result["vocab_id"] == "vocab_001"
    assert result["word"] == "hello"
    assert result["due_date"] == "2026-07-30"
    assert "review_state" in result
    assert "is_due" in result


def test_schedule_review_aggregate_due(isolated_storage, make_vocab_data):
    """未指定 vocab_id 返回到期词汇列表（next_review <= today）"""
    today = datetime.now(timezone.utc).date().isoformat()
    # 到期词：next_review = 今天
    _save_with_review("hello", "vocab_001", today, make_vocab_data)
    _save_with_review("world", "vocab_002", today, make_vocab_data)
    # 未到期词：next_review = 明天
    _save_with_review("future", "vocab_003", "2099-12-31", make_vocab_data)

    result = schedule_review()
    assert result["due_count"] == 2
    words = [d["word"] for d in result["due_words"]]
    assert set(words) == {"hello", "world"}


def test_schedule_review_no_due(isolated_storage, make_vocab_data):
    """无到期词返回 due_count=0"""
    _save_with_review("future", "vocab_001", "2099-12-31", make_vocab_data)

    result = schedule_review()
    assert result["due_count"] == 0
    assert result["due_words"] == []


def test_schedule_review_nonexistent_returns_error(isolated_storage):
    """不存在词汇返回 error"""
    result = schedule_review("vocab_999")
    assert "error" in result


def test_schedule_review_is_due_flag(isolated_storage, make_vocab_data):
    """is_due 标记：到期词 True，未到期 False"""
    today = datetime.now(timezone.utc).date().isoformat()
    _save_with_review("due", "vocab_001", today, make_vocab_data)
    _save_with_review("notdue", "vocab_002", "2099-12-31", make_vocab_data)

    assert schedule_review("vocab_001")["is_due"] is True
    assert schedule_review("vocab_002")["is_due"] is False
