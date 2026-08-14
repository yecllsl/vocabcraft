# tests/test_composite_and_match_fixes.py
"""TDD tests for fixing composite word grade and meaning matching

Root cause: quiz_005 for word "反" got grade=3 when user typed
'同"返"。往返' (without comma and second义素). Two bugs:
1. _match_meaning doesn't normalize whitespace in义素 (。+space vs 。)
2. _composite_word_grade formula round((min+avg)/2) is too harsh
   (one grade=3 among nine grade=4s → word_grade=3)
"""

import pytest

from vocabcraft_mcp.tools.quiz import (
    _composite_word_grade,
    _grade_definition,
    _match_meaning,
)


# ── _match_meaning: whitespace normalization ──


class TestMatchMeaningWhitespace:
    """义素内的空白（。后空格等）不应影响匹配"""

    def test_space_after_period_matches(self):
        """'同"返"。 往返' 应匹配 '同"返"。往返'（。后空格可省）"""
        assert _match_meaning('同"返"。 往返,返回', '同"返"。往返') is True

    def test_space_after_period_in_both(self):
        """双方都有。+空格，应匹配"""
        assert _match_meaning('同"返"。 往返,返回', '同"返"。 往返') is True

    def test_no_space_in_expected(self):
        """expected 无空格，actual 无空格，应匹配"""
        assert _match_meaning('同"返"。往返,返回', '同"返"。往返') is True

    def test_extra_spaces_normalized(self):
        """多余空格不影响匹配"""
        assert _match_meaning('同"返"。  往返,返回', '同"返"。往返') is True

    def test_comma_separated_still_works(self):
        """逗号分隔的多义项仍正常工作"""
        assert _match_meaning('同"返"。 往返,返回', '返回') is True

    def test_wrong_meaning_still_fails(self):
        """完全不同的释义仍返回 False"""
        assert _match_meaning('同"返"。 往返,返回', '相反') is False


# ── _grade_definition: end-to-end with whitespace ──


class TestGradeDefinitionWhitespace:
    """词性+释义评分对空白容错"""

    def test_grade4_with_space_after_period(self):
        """。后无空格仍得 grade=4"""
        expected = 'v.|同"返"。 往返,返回'
        actual = 'v.|同"返"。往返'
        assert _grade_definition(expected, actual) == 4

    def test_grade4_exact(self):
        """完全匹配得 grade=4"""
        expected = 'v.|同"返"。 往返,返回'
        actual = 'v.|同"返"。 往返,返回'
        assert _grade_definition(expected, actual) == 4

    def test_grade4_just_second_part(self):
        """只写第二义素也得 grade=4"""
        expected = 'v.|同"返"。 往返,返回'
        actual = 'v.|返回'
        assert _grade_definition(expected, actual) == 4


# ── _composite_word_grade: reduced min weight ──


class TestCompositeWordGrade:
    """综合评分不应被单个较低 grade 拖垮"""

    def test_all_grade4_returns4(self):
        """全部 grade=4 → 词级 4"""
        assert _composite_word_grade([4] * 9) == 4

    def test_one_grade3_among_grade4_returns4(self):
        """8个4 + 1个3 → 词级应为4（用户基本掌握）"""
        grades = [4, 4, 4, 4, 4, 4, 4, 4, 3]
        assert _composite_word_grade(grades) == 4

    def test_one_grade2_among_grade4_returns3(self):
        """8个4 + 1个2 → 词级应为3（有明显薄弱项）"""
        grades = [4, 4, 4, 4, 4, 4, 4, 4, 2]
        assert _composite_word_grade(grades) == 3

    def test_all_grade3_returns3(self):
        """全部 grade=3 → 词级 3"""
        assert _composite_word_grade([3] * 9) == 3

    def test_mixed_3_and_4_majority3(self):
        """5个4 + 4个3 → 词级 3"""
        grades = [4, 4, 4, 4, 4, 3, 3, 3, 3]
        assert _composite_word_grade(grades) == 3

    def test_empty_returns0(self):
        """空列表 → 0"""
        assert _composite_word_grade([]) == 0

    def test_single_grade4(self):
        """单个 grade=4 → 4"""
        assert _composite_word_grade([4]) == 4

    def test_single_grade3(self):
        """单个 grade=3 → 3"""
        assert _composite_word_grade([3]) == 3

    def test_grade1_drags_down(self):
        """有 grade=1 应该明显拉低"""
        grades = [4, 4, 4, 4, 4, 4, 4, 4, 1]
        result = _composite_word_grade(grades)
        assert result <= 3
