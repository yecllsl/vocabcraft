# tests/test_algorithms.py
"""SM-2 间隔重复算法与初始复习计划测试

公式参考: https://www.supermemo.com/en/blog/application-of-a-computer-to-improve-the-results-obtained-in-working-with-the-supermemo-method
本文件为 algorithms.py 的真实单元测试（纯函数，无需 mock）。
"""

import pytest

from vocabcraft_mcp.algorithms import (
    DEFAULT_EASE_FACTOR,
    MIN_EASE_FACTOR,
    compute_next_review,
    get_initial_schedule,
)

# ──────────────────────────────────────────
# 输入校验
# ──────────────────────────────────────────

def test_grade_below_one_rejected():
    """grade < 1 应抛 ValueError"""
    with pytest.raises(ValueError):
        compute_next_review(2.5, 0, 0, 0)


def test_grade_above_four_rejected():
    """grade > 4 应抛 ValueError"""
    with pytest.raises(ValueError):
        compute_next_review(2.5, 0, 0, 5)


# ──────────────────────────────────────────
# EF 更新公式：EF' = EF + (0.1 - (5-q)*(0.08 + (5-q)*0.02))
# ──────────────────────────────────────────

def test_grade_4_ef_unchanged():
    """q=4: EF' = EF + 0 = EF（不变）"""
    result = compute_next_review(2.5, 0, 0, 4)
    assert result["ease_factor"] == pytest.approx(2.5, abs=1e-3)


def test_grade_3_decreases_ef_by_0_14():
    """q=3: EF' = EF - 0.14"""
    result = compute_next_review(2.5, 0, 0, 3)
    assert result["ease_factor"] == pytest.approx(2.36, abs=1e-3)


def test_grade_1_ef_decreases():
    """q=1: EF' = EF - 0.54"""
    result = compute_next_review(2.5, 0, 0, 1)
    assert result["ease_factor"] == pytest.approx(1.96, abs=1e-3)


def test_ef_minimum_clamp():
    """EF 下限 1.3：连续低分不应使 EF 跌破 1.3"""
    # 从 1.5 起，grade=1 应使 EF = 1.5 - 0.54 = 0.96，被夹紧到 1.3
    result = compute_next_review(1.5, 1, 1, 1)
    assert result["ease_factor"] == MIN_EASE_FACTOR


# ──────────────────────────────────────────
# 答错重置逻辑 (grade < 3)
# ──────────────────────────────────────────

def test_grade_below_3_resets_repetitions_and_interval():
    """grade < 3: repetitions 归零，interval=1"""
    result = compute_next_review(2.5, 15, 5, 2)
    assert result["repetitions"] == 0
    assert result["interval"] == 1


def test_grade_below_3_still_updates_ef():
    """grade < 3 也更新 EF（反映真实难度）"""
    result = compute_next_review(2.5, 1, 0, 2)
    # q=2: EF' = EF + (0.1 - 3*(0.08+3*0.02)) = EF - 0.32
    assert result["ease_factor"] == pytest.approx(2.18, abs=1e-3)


# ──────────────────────────────────────────
# 答对递推逻辑 (grade >= 3)
# rep 0 → interval 1; rep 1 → interval 6; rep>=2 → round(interval*EF)
# ──────────────────────────────────────────

def test_first_success_interval_1():
    """rep=0, grade>=3 → interval=1, rep=1"""
    result = compute_next_review(2.5, 0, 0, 4)
    assert result["interval"] == 1
    assert result["repetitions"] == 1


def test_second_success_interval_6():
    """rep=1, grade>=3 → interval=6, rep=2"""
    result = compute_next_review(2.5, 1, 1, 4)
    assert result["interval"] == 6
    assert result["repetitions"] == 2


def test_third_success_interval_multiplied_by_ef():
    """rep=2, grade>=3 → interval=round(prev_interval*EF)=round(6*2.5)=15, rep=3"""
    result = compute_next_review(2.5, 6, 2, 4)
    assert result["interval"] == 15
    assert result["repetitions"] == 3


def test_fourth_success_interval_multiplied_by_ef():
    """rep=3, grade>=3 → interval=round(15*2.5)=38, rep=4"""
    result = compute_next_review(2.5, 15, 3, 4)
    assert result["interval"] == 38
    assert result["repetitions"] == 4


def test_interval_rounding():
    """interval = round(prev_interval * EF) 四舍五入（银行家舍入）"""
    # prev_interval=15, EF=2.3 → round(34.5) = 34（Python3 银行家舍入到偶数）
    result = compute_next_review(2.3, 15, 3, 4)
    assert result["interval"] == 34


# ──────────────────────────────────────────
# 返回契约
# ──────────────────────────────────────────

def test_return_dict_has_required_keys():
    """返回 dict 含 ease_factor/repetitions/interval/next_review_date"""
    result = compute_next_review(2.5, 0, 0, 4)
    assert isinstance(result, dict)
    for key in ("ease_factor", "repetitions", "interval", "next_review_date"):
        assert key in result, f"缺少返回字段: {key}"


def test_next_review_date_format():
    """next_review_date 格式 YYYY-MM-DD"""
    result = compute_next_review(2.5, 0, 0, 4)
    d = result["next_review_date"]
    assert len(d) == 10
    assert d[4] == "-" and d[7] == "-"


# ──────────────────────────────────────────
# 初始复习计划
# ──────────────────────────────────────────

def test_get_initial_schedule_returns_five_points():
    """初始复习计划含 5 个节点"""
    sched = get_initial_schedule()
    assert len(sched["intervals_days"]) == 5
    assert len(sched["due_dates"]) == 5


def test_get_initial_schedule_intervals():
    """间隔为 [1, 2, 4, 7, 15]"""
    sched = get_initial_schedule()
    assert sched["intervals_days"] == [1, 2, 4, 7, 15]


def test_get_initial_schedule_next_review_is_first_due():
    """next_review 等于 due_dates[0]"""
    sched = get_initial_schedule()
    assert sched["next_review"] == sched["due_dates"][0]


# ──────────────────────────────────────────
# 常量
# ──────────────────────────────────────────

def test_default_ease_factor_constant():
    """DEFAULT_EASE_FACTOR = 2.5"""
    assert DEFAULT_EASE_FACTOR == 2.5


def test_min_ease_factor_constant():
    """MIN_EASE_FACTOR = 1.3"""
    assert MIN_EASE_FACTOR == 1.3
