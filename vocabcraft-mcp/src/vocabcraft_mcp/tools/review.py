# src/vocabcraft_mcp/tools/review.py
"""复习排程 Tool - 基于遗忘曲线（SM-2）

根据词汇的复习状态查询到期词汇并生成复习计划。
评分时由 quiz.grade_quiz 调用 algorithms.compute_next_review 更新记忆状态，
再通过 crud.update_vocab 回写 review_state。

到期定义: review_state.next_review <= 今天（YYYY-MM-DD 字符串比较）。
"""

from vocabcraft_mcp.algorithms import _now_utc
from vocabcraft_mcp.tools.crud import get_storage


def schedule_review(vocab_id: str = "", language: str = "") -> dict:
    """生成复习计划

    - 指定 vocab_id：返回该词汇的复习状态与到期日
    - 未指定 vocab_id：返回所有到期词汇列表，按到期日升序

    Args:
        vocab_id: 指定词汇 ID，空串则查询全部到期词
        language: 按语种过滤（en/zh 等），空串则不过滤

    Returns:
        指定 vocab_id 时: {vocab_id, word, review_state, due_date, is_due}
        未指定时: {today, due_count, due_words: [{vocab_id, word, due_date}]}
        词汇不存在时: {error}
    """
    storage = get_storage()
    today = _now_utc().date().isoformat()

    # 单词汇模式：返回复习状态
    if vocab_id:
        v = storage.load_vocab(vocab_id)
        if v is None:
            return {"error": f"词汇不存在: {vocab_id}"}
        due_date = v.review_state.next_review
        return {
            "vocab_id": v.id,
            "word": v.structured.word,
            "review_state": v.review_state.model_dump(),
            "due_date": due_date,
            "is_due": bool(due_date) and due_date <= today,
        }

    # 全局模式：查询所有到期词汇
    all_vocabs = storage.get_all_vocabs_for_statistics()
    due = [
        v for v in all_vocabs
        if v.review_state.next_review and v.review_state.next_review <= today
        and (not language or v.structured.language == language)
    ]
    # 按到期日升序，早到期的优先
    due.sort(key=lambda v: v.review_state.next_review)

    return {
        "today": today,
        "due_count": len(due),
        "due_words": [
            {
                "vocab_id": v.id,
                "word": v.structured.word,
                "due_date": v.review_state.next_review,
            }
            for v in due
        ],
    }
