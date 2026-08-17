# tests/test_tools_statistics.py
"""统计 Tool 单元测试

验证 get_statistics 真实行为:
    - language/mastery/date/quiz_type 四维分组
    - total 与 items 计数正确
    - 空数据返回空 items
    - 不支持维度返回 error
    - trends 固定 30 天
"""


from vocabcraft_mcp.tools.crud import save_vocab
from vocabcraft_mcp.tools.statistics import get_statistics


def test_statistics_importable():
    """模块可正常 import"""
    assert callable(get_statistics)


def test_stats_by_language(isolated_storage, make_vocab_data):
    """按 language 分组统计"""
    save_vocab(make_vocab_data("hello", "vocab_001", language="en"))
    save_vocab(make_vocab_data("bonjour", "vocab_002", language="fr"))
    save_vocab(make_vocab_data("world", "vocab_003", language="en"))

    result = get_statistics("language")
    assert result["total"] == 3
    items = {i["key"]: i["count"] for i in result["items"]}
    assert items == {"en": 2, "fr": 1}


def test_stats_by_mastery(isolated_storage, make_vocab_data):
    """按掌握度分组：新词（repetitions=0）"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    save_vocab(make_vocab_data("world", "vocab_002"))

    result = get_statistics("mastery")
    assert result["total"] == 2
    items = {i["key"]: i["count"] for i in result["items"]}
    # 新词未复习，repetitions=0 → "新词"
    assert items.get("新词") == 2


def test_stats_by_quiz_type(isolated_storage, make_vocab_data):
    """按题型分组统计考题数"""
    from vocabcraft_mcp.tools.quiz import generate_quiz
    save_vocab(make_vocab_data("hello", "vocab_001"))
    generate_quiz("vocab_001", "拼写")
    generate_quiz("vocab_001", "选择")

    result = get_statistics("quiz_type")
    assert result["total"] == 2
    items = {i["key"]: i["count"] for i in result["items"]}
    assert items == {"拼写": 1, "选择": 1}


def test_stats_by_date(isolated_storage, make_vocab_data):
    """按创建日期分组"""
    save_vocab(make_vocab_data("hello", "vocab_001"))

    result = get_statistics("date")
    assert result["total"] == 1
    assert len(result["items"]) == 1


def test_stats_empty_storage(isolated_storage):
    """空数据返回 total=0, items=[]"""
    result = get_statistics("language")
    assert result["total"] == 0
    assert result["items"] == []


def test_stats_invalid_group_returns_error(isolated_storage):
    """不支持维度返回 error"""
    result = get_statistics("invalid_dim")
    assert "error" in result


def test_stats_trends_30_days(isolated_storage, make_vocab_data):
    """trends 固定 30 天"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    result = get_statistics("language")
    assert len(result["trends"]) == 30
    assert "date" in result["trends"][0]
    assert "count" in result["trends"][0]
