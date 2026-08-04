# src/vocabcraft_mcp/tools/statistics.py
"""统计查询 Tool

提供多维度词汇统计，支持按 language/mastery/date/quiz_type 分组。
返回分组 items、总数 total、30 天创建趋势 trends。

只读操作，不修改任何数据。
"""

from collections import Counter
from datetime import datetime, timedelta, timezone

from vocabcraft_mcp.tools.crud import get_storage

# 支持的分组维度
_VALID_GROUPS = {"language", "mastery", "date", "quiz_type"}


def _mastery_level(word_grade: int | None) -> str:
    """按词级综合评分划分掌握度

    基于 grade_quiz 计算的 word_grade（0-5）：
        None / 0-1: 新词（未评分或完全不会）
        2:         生疏（需重学）
        3:         熟悉（勉强记住）
        4:         掌握（记忆良好）
        5:         精通（完美记忆）
    """
    if word_grade is None or word_grade <= 1:
        return "新词"
    if word_grade == 2:
        return "生疏"
    if word_grade == 3:
        return "熟悉"
    if word_grade == 4:
        return "掌握"
    return "精通"


def get_statistics(group_by: str) -> dict:
    """按指定维度统计词汇分布

    Args:
        group_by: 分组维度，支持:
            - language: 按 structured.language 分组
            - mastery: 按掌握度分组（新词/生疏/熟悉/掌握）
            - date: 按创建日期分组
            - quiz_type: 按考题题型分组（统计考题而非词汇）

    Returns:
        包含以下字段的字典:
        - group_by: 分组维度
        - items: [{key, count}] 分组统计列表
        - total: 总数（quiz_type 维度为考题总数，其余为词汇总数）
        - trends: [{date, count}] 近 30 天词汇创建趋势
        不支持维度返回 {error}
    """
    if group_by not in _VALID_GROUPS:
        return {"error": f"不支持的分组维度: {group_by}，支持 {sorted(_VALID_GROUPS)}"}

    storage = get_storage()
    vocabs = storage.get_all_vocabs_for_statistics()

    # 按维度聚合
    if group_by == "language":
        counter = Counter(v.structured.language for v in vocabs)
        total = len(vocabs)
    elif group_by == "mastery":
        counter = Counter(_mastery_level(v.review_state.last_word_grade) for v in vocabs)
        total = len(vocabs)
    elif group_by == "date":
        counter = Counter(v.created_at.date().isoformat() for v in vocabs)
        total = len(vocabs)
    else:  # quiz_type
        quizzes = [storage.load_quiz(qid) for qid in storage.list_all_quiz_ids()]
        quizzes = [q for q in quizzes if q]
        counter = Counter(q.quiz_type for q in quizzes)
        total = len(quizzes)

    items = [{"key": k, "count": v} for k, v in sorted(counter.items())]

    # 30 天词汇创建趋势（所有维度都返回，便于看增长曲线）
    today = datetime.now(timezone.utc).date()
    trends = []
    for i in range(29, -1, -1):
        day = (today - timedelta(days=i)).isoformat()
        day_count = sum(1 for v in vocabs if v.created_at.date().isoformat() == day)
        trends.append({"date": day, "count": day_count})

    return {
        "group_by": group_by,
        "items": items,
        "total": total,
        "trends": trends,
    }
