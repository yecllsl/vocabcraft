# src/vocabcraft_mcp/algorithms.py
"""遗忘曲线算法

包含 SM-2 间隔重复算法和初始复习排程。

SM-2 算法原理（SuperMemo 2, 1987 Piotr Wozniak）:
    用户对每张卡片打分 grade (0-5)：
        0-2: 完全不记得 → 视为失败：重置 repetitions=0, interval=1（明天重背）
        3:   勉强记住 → 视为通过（SM-2 标准 q>=3 即成功）：reps 递增、间隔正常推进
        4:   记住但有迟疑 → 正常推进，ease 不变
        5:   完美记忆 → 正常推进，ease 略升
    ease factor (EF) 无论答对答错都更新（反映真实难度），下限 1.3 防止间隔不增长。

参考: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

# SM-2 算法常量
MIN_EASE_FACTOR = 1.3  # EF 下限，防止间隔不增长
DEFAULT_EASE_FACTOR = 2.5  # 新词初始 EF

# 初始复习计划间隔（天）：简化 5 节点，覆盖短期到中期复习
# ponytail: 不用经典艾宾浩斯 7 节点（含 sub-day），date 粒度下 5 节点已够用
# 公开常量：services.py 跨模块复用，故去下划线前缀
INITIAL_INTERVALS_DAYS = [1, 2, 4, 7, 15]


def _now_utc() -> datetime:
    """当前 UTC 日期时间，统一时间基准，供全模块复用"""
    return datetime.now(timezone.utc)


def _today_utc() -> date:
    """获取当前 UTC 日期，统一日期基准便于测试与回放"""
    return _now_utc().date()


def compute_next_review(
    ease_factor: float,
    interval: int,
    repetitions: int,
    grade: int,
) -> dict:
    """SM-2 算法核心：根据评分更新记忆状态

    Args:
        ease_factor: 当前难度系数（下限 MIN_EASE_FACTOR）
        interval: 当前复习间隔（天）
        repetitions: 已连续答对次数（grade>=3 才递增）
        grade: 本次评分 0-5

    Returns:
        包含以下字段的字典:
        - ease_factor: 更新后的难度系数（>=MIN_EASE_FACTOR）
        - interval: 下次复习间隔（天）
        - repetitions: 更新后的连续答对次数
        - next_review_date: 下次到期日期 YYYY-MM-DD

    Raises:
        ValueError: grade 不在 0-5 范围
    """
    if not 0 <= grade <= 5:
        raise ValueError(f"grade 必须在 0-5 之间，收到: {grade}")

    # grade < 3 视为复习失败：重置 repetitions，interval=1（明天重背）
    if grade < 3:
        new_repetitions = 0
        new_interval = 1
    else:
        # 答对：递增 repetitions，按 SM-2 规则推进 interval
        new_repetitions = repetitions + 1
        if repetitions == 0:
            new_interval = 1
        elif repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(interval * ease_factor)

    # 更新 ease_factor：EF = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
    # 无论答对答错都更新 EF，反映真实难度
    new_ease = ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if new_ease < MIN_EASE_FACTOR:
        new_ease = MIN_EASE_FACTOR

    # 下次到期日 = 今天 + interval 天
    next_review_date = (_today_utc() + timedelta(days=new_interval)).isoformat()

    return {
        "ease_factor": new_ease,
        "interval": new_interval,
        "repetitions": new_repetitions,
        "next_review_date": next_review_date,
    }


def get_initial_schedule(today: date | None = None) -> dict:
    """返回新词初始复习计划（5 节点）

    间隔 [1, 2, 4, 7, 15] 天，基于 today 计算 5 个到期日。
    next_review 为首个到期日（1 天后），写入 ReviewState.next_review。

    Args:
        today: 基准日期，默认今天(UTC)，传参便于测试回放

    Returns:
        包含以下字段的字典:
        - intervals_days: 间隔列表 [1, 2, 4, 7, 15]
        - due_dates: 5 个到期日期字符串列表 YYYY-MM-DD
        - next_review: 首个到期日，等于 due_dates[0]
    """
    base = today if today is not None else _today_utc()
    due_dates = [(base + timedelta(days=d)).isoformat() for d in INITIAL_INTERVALS_DAYS]
    return {
        "intervals_days": list(INITIAL_INTERVALS_DAYS),
        "due_dates": due_dates,
        "next_review": due_dates[0],
    }
