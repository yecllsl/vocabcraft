# tests/test_match_meaning_issue.py
"""测试 _match_meaning 函数对特殊字符的处理

特别是对含有引号、句号等特殊字符的释义的匹配。
"""

import pytest

from vocabcraft_mcp.tools.quiz import _match_meaning


def test_match_meaning_with_quotes_and_period():
    """测试含引号和句号的释义匹配"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返,返回'
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_period_partial():
    """测试用户只输入核心义素"""
    expected = '同"返"。 往返,返回'
    actual = '往返,返回'
    # 根据多义项匹配规则，任一义素匹配即可
    # 预期：'返回' in '往返,返回' -> True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_period_no_comma():
    """测试用户输入无逗号的情况"""
    expected = '同"返"。 往返,返回'
    actual = '往返 返回'
    # 预期：'返回' in '往返 返回' -> True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_period_exact():
    """测试完全匹配的情况"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返,返回'
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_period_missing_part():
    """测试用户输入不完整的情况"""
    expected = '同"返"。 往返,返回'
    actual = '往返'
    # 预期：'往返' in '同"返"。 往返' -> False
    # 但 '同"返"。 往返' in '往返' -> False
    # 所以应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_period_wrong_answer():
    """测试完全错误的答案"""
    expected = '同"返"。 往返,返回'
    actual = '错误答案'
    assert _match_meaning(expected, actual) is False


def test_match_meaning_single_meaning_with_special_chars():
    """测试单义项含特殊字符的情况"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返,返回'
    # 单义项：严格匹配
    assert _match_meaning(expected, actual) is True


def test_match_meaning_single_meaning_partial():
    """测试单义项部分匹配"""
    expected = '同"返"。 往返,返回'
    actual = '往返'
    # 单义项：义素是答案的子串或答案是义素的子串
    # '同"返"。 往返' in '往返' -> False
    # '往返' in '同"返"。 往返' -> True
    # 但需要 len(actual) >= len(expected) // 2
    # len('往返') = 2, len('同"返"。 往返') = 8, 2 >= 4 -> False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_different_quote_styles():
    """测试不同引号风格"""
    expected = '同"返"。 往返,返回'
    actual = "同'返'。 往返,返回"
    # 引号不匹配，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_extra_spaces():
    """测试多余空格的情况"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。  往返,返回'
    # 多余空格，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_period_in_actual():
    """测试实际回答中包含句号"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。往返,返回'
    # 句号后无空格，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_space_before_comma():
    """测试逗号前有空格"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返 ,返回'
    # 逗号前有空格，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_comma_only():
    """测试只有逗号分隔的情况"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返, 返回'
    # 逗号后有空格，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_period_and_comma():
    """测试句号和逗号的组合"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。往返,返回'
    # 句号后无空格，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma():
    """测试引号和逗号的组合"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返,返回'
    # 完全匹配，应该返回 True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_comma_partial():
    """测试引号和逗号的部分匹配"""
    expected = '同"返"。 往返,返回'
    actual = '往返,返回'
    # 部分匹配，应该返回 True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_comma_wrong():
    """测试引号和逗号的错误匹配"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返'
    # 缺少"返回"，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_missing():
    """测试引号和逗号的缺失匹配"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 返回'
    # 缺少"往返"，但有"返回"，应该返回 True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_comma_wrong_order():
    """测试引号和逗号的错误顺序"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 返回,往返'
    # 顺序错误，但包含"返回"，应该返回 True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_comma_extra():
    """测试引号和逗号的多余内容"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返,返回,额外内容'
    # 包含额外内容，但包含"返回"，应该返回 True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_comma_missing_all():
    """测试引号和逗号的完全缺失"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 '
    # 完全缺失，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_empty():
    """测试引号和逗号的空字符串"""
    expected = '同"返"。 往返,返回'
    actual = ''
    # 空字符串，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_whitespace():
    """测试引号和逗号的空白字符串"""
    expected = '同"返"。 往返,返回'
    actual = '   '
    # 空白字符串，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_newline():
    """测试引号和逗号的换行符"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返,返回\n'
    # 换行符，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_tab():
    """测试引号和逗号的制表符"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。\t往返,返回'
    # 制表符，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_multiple_spaces():
    """测试引号和逗号的多个空格"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。   往返,返回'
    # 多个空格，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_missing_quote():
    """测试引号和逗号的缺失引号"""
    expected = '同"返"。 往返,返回'
    actual = '同返。 往返,返回'
    # 缺失引号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_wrong_quote():
    """测试引号和逗号的错误引号"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返,返回'
    # 正确引号，应该返回 True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_comma_mixed_quotes():
    """测试引号和逗号的混合引号"""
    expected = '同"返"。 往返,返回'
    actual = "同'返'。 往返,返回"
    # 混合引号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_double_quotes():
    """测试引号和逗号的双引号"""
    expected = '同"返"。 往返,返回'
    actual = '同"返"。 往返,返回'
    # 双引号，应该返回 True
    assert _match_meaning(expected, actual) is True


def test_match_meaning_with_quotes_and_comma_single_quotes():
    """测试引号和逗号的单引号"""
    expected = '同"返"。 往返,返回'
    actual = "同'返'。 往返,返回"
    # 单引号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_backticks():
    """测试引号和逗号的反引号"""
    expected = '同"返"。 往返,返回'
    actual = '同`返`。 往返,返回'
    # 反引号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_angle_brackets():
    """测试引号和逗号的尖括号"""
    expected = '同"返"。 往返,返回'
    actual = '同<返>。 往返,返回'
    # 尖括号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_square_brackets():
    """测试引号和逗号的方括号"""
    expected = '同"返"。 往返,返回'
    actual = '同[返]。 往返,返回'
    # 方括号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_curly_brackets():
    """测试引号和逗号的花括号"""
    expected = '同"返"。 往返,返回'
    actual = '同{返}。 往返,返回'
    # 花括号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_parentheses():
    """测试引号和逗号的圆括号"""
    expected = '同"返"。 往返,返回'
    actual = '同(返)。 往返,返回'
    # 圆括号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_slash():
    """测试引号和逗号的斜杠"""
    expected = '同"返"。 往返,返回'
    actual = '同/返/。 往返,返回'
    # 斜杠，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_backslash():
    """测试引号和逗号的反斜杠"""
    expected = '同"返"。 往返,返回'
    actual = '同\\返\\。 往返,返回'
    # 反斜杠，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_pipe():
    """测试引号和逗号的管道符"""
    expected = '同"返"。 往返,返回'
    actual = '同|返|。 往返,返回'
    # 管道符，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_ampersand():
    """测试引号和逗号的和号"""
    expected = '同"返"。 往返,返回'
    actual = '同&返&。 往返,返回'
    # 和号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_at_sign():
    """测试引号和逗号的@符号"""
    expected = '同"返"。 往返,返回'
    actual = '同@返@。 往返,返回'
    # @符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_hash():
    """测试引号和逗号的井号"""
    expected = '同"返"。 往返,返回'
    actual = '同#返#。 往返,返回'
    # 井号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_dollar():
    """测试引号和逗号的美元符号"""
    expected = '同"返"。 往返,返回'
    actual = '同$返$。 往返,返回'
    # 美元符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_percent():
    """测试引号和逗号的百分号"""
    expected = '同"返"。 往返,返回'
    actual = '同%返%。 往返,返回'
    # 百分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_caret():
    """测试引号和逗号的脱字符"""
    expected = '同"返"。 往返,返回'
    actual = '同^返^。 往返,返回'
    # 脱字符，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_underscore():
    """测试引号和逗号的下划线"""
    expected = '同"返"。 往返,返回'
    actual = '同_返_。 往返,返回'
    # 下划线，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_plus():
    """测试引号和逗号的加号"""
    expected = '同"返"。 往返,返回'
    actual = '同+返+。 往返,返回'
    # 加号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_minus():
    """测试引号和逗号的减号"""
    expected = '同"返"。 往返,返回'
    actual = '同-返-。 往返,返回'
    # 减号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_equals():
    """测试引号和逗号的等号"""
    expected = '同"返"。 往返,返回'
    actual = '同=返=。 往返,返回'
    # 等号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_tilde():
    """测试引号和逗号的波浪号"""
    expected = '同"返"。 往返,返回'
    actual = '同~返~。 往返,返回'
    # 波浪号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_grave_accent():
    """测试引号和逗号的重音符"""
    expected = '同"返"。 往返,返回'
    actual = '同`返`。 往返,返回'
    # 重音符，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_exclamation():
    """测试引号和逗号的感叹号"""
    expected = '同"返"。 往返,返回'
    actual = '同!返!。 往返,返回'
    # 感叹号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_question_mark():
    """测试引号和逗号的问号"""
    expected = '同"返"。 往返,返回'
    actual = '同?返?。 往返,返回'
    # 问号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_colon():
    """测试引号和逗号的冒号"""
    expected = '同"返"。 往返,返回'
    actual = '同:返:。 往返,返回'
    # 冒号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_semicolon():
    """测试引号和逗号的分号"""
    expected = '同"返"。 往返,返回'
    actual = '同;返;。 往返,返回'
    # 分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_comma():
    """测试引号和逗号的逗号"""
    expected = '同"返"。 往返,返回'
    actual = '同,返,。 往返,返回'
    # 逗号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_period():
    """测试引号和逗号的句号"""
    expected = '同"返"。 往返,返回'
    actual = '同。返。。 往返,返回'
    # 句号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_full_stop():
    """测试引号和逗号的句点"""
    expected = '同"返"。 往返,返回'
    actual = '同.返.。 往返,返回'
    # 句点，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_ellipsis():
    """测试引号和逗号的省略号"""
    expected = '同"返"。 往返,返回'
    actual = '同...返...。 往返,返回'
    # 省略号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_dash():
    """测试引号和逗号的破折号"""
    expected = '同"返"。 往返,返回'
    actual = '同—返—。 往返,返回'
    # 破折号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_en_dash():
    """测试引号和逗号的短破折号"""
    expected = '同"返"。 往返,返回'
    actual = '同–返–。 往返,返回'
    # 短破折号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_em_dash():
    """测试引号和逗号的长破折号"""
    expected = '同"返"。 往返,返回'
    actual = '同—返—。 往返,返回'
    # 长破折号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_hyphen():
    """测试引号和逗号的连字符"""
    expected = '同"返"。 往返,返回'
    actual = '同‐返‐。 往返,返回'
    # 连字符，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_bullet():
    """测试引号和逗号的项目符号"""
    expected = '同"返"。 往返,返回'
    actual = '同•返•。 往返,返回'
    # 项目符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_middle_dot():
    """测试引号和逗号的中间点"""
    expected = '同"返"。 往返,返回'
    actual = '同·返·。 往返,返回'
    # 中间点，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_multiplication_sign():
    """测试引号和逗号的乘号"""
    expected = '同"返"。 往返,返回'
    actual = '同×返×。 往返,返回'
    # 乘号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_division_sign():
    """测试引号和逗号的除号"""
    expected = '同"返"。 往返,返回'
    actual = '同÷返÷。 往返,返回'
    # 除号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_plus_minus_sign():
    """测试引号和逗号的正负号"""
    expected = '同"返"。 往返,返回'
    actual = '同±返±。 往返,返回'
    # 正负号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_not_equal_sign():
    """测试引号和逗号的不等号"""
    expected = '同"返"。 往返,返回'
    actual = '同≠返≠。 往返,返回'
    # 不等号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_less_than_sign():
    """测试引号和逗号的小于号"""
    expected = '同"返"。 往返,返回'
    actual = '同<返<。 往返,返回'
    # 小于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_greater_than_sign():
    """测试引号和逗号的大于号"""
    expected = '同"返"。 往返,返回'
    actual = '同>返>。 往返,返回'
    # 大于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_less_than_or_equal_sign():
    """测试引号和逗号的小于等于号"""
    expected = '同"返"。 往返,返回'
    actual = '同≤返≤。 往返,返回'
    # 小于等于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_greater_than_or_equal_sign():
    """测试引号和逗号的大于等于号"""
    expected = '同"返"。 往返,返回'
    actual = '同≥返≥。 往返,返回'
    # 大于等于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_approximately_equal_sign():
    """测试引号和逗号的约等于号"""
    expected = '同"返"。 往返,返回'
    actual = '同≈返≈。 往返,返回'
    # 约等于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_identical_to_sign():
    """测试引号和逗号的恒等于号"""
    expected = '同"返"。 往返,返回'
    actual = '同≡返≡。 往返,返回'
    # 恒等于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_equivalent_to_sign():
    """测试引号和逗号的等价于号"""
    expected = '同"返"。 往返,返回'
    actual = '同⇔返⇔。 往返,返回'
    # 等价于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_implies_sign():
    """测试引号和逗号的蕴含号"""
    expected = '同"返"。 往返,返回'
    actual = '同⇒返⇒。 往返,返回'
    # 蕴含号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_and_sign():
    """测试引号和逗号的逻辑与号"""
    expected = '同"返"。 往返,返回'
    actual = '同∧返∧。 往返,返回'
    # 逻辑与号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_or_sign():
    """测试引号和逗号的逻辑或号"""
    expected = '同"返"。 往返,返回'
    actual = '同∨返∨。 往返,返回'
    # 逻辑或号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_not_sign():
    """测试引号和逗号的逻辑非号"""
    expected = '同"返"。 往返,返回'
    actual = '同¬返¬。 往返,返回'
    # 逻辑非号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_for_all_sign():
    """测试引号和逗号的全称量词号"""
    expected = '同"返"。 往返,返回'
    actual = '同∀返∀。 往返,返回'
    # 全称量词号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_exists_sign():
    """测试引号和逗号的存在量词号"""
    expected = '同"返"。 往返,返回'
    actual = '同∃返∃。 往返,返回'
    # 存在量词号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_element_of_sign():
    """测试引号和逗号的属于号"""
    expected = '同"返"。 往返,返回'
    actual = '同∈返∈。 往返,返回'
    # 属于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_not_element_of_sign():
    """测试引号和逗号的不属于号"""
    expected = '同"返"。 往返,返回'
    actual = '同∉返∉。 往返,返回'
    # 不属于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_subset_sign():
    """测试引号和逗号的子集号"""
    expected = '同"返"。 往返,返回'
    actual = '同⊂返⊂。 往返,返回'
    # 子集号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_superset_sign():
    """测试引号和逗号的超集号"""
    expected = '同"返"。 往返,返回'
    actual = '同⊃返⊃。 往返,返回'
    # 超集号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_union_sign():
    """测试引号和逗号的并集号"""
    expected = '同"返"。 往返,返回'
    actual = '同∪返∪。 往返,返回'
    # 并集号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_intersection_sign():
    """测试引号和逗号的交集号"""
    expected = '同"返"。 往返,返回'
    actual = '同∩返∩。 往返,返回'
    # 交集号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_empty_set_sign():
    """测试引号和逗号的空集号"""
    expected = '同"返"。 往返,返回'
    actual = '同∅返∅。 往返,返回'
    # 空集号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_nabla_sign():
    """测试引号和逗号的纳布拉符"""
    expected = '同"返"。 往返,返回'
    actual = '同∇返∇。 往返,返回'
    # 纳布拉符，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_partial_derivative_sign():
    """测试引号和逗号的偏导数号"""
    expected = '同"返"。 往返,返回'
    actual = '同∂返∂。 往返,返回'
    # 偏导数号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_infinity_sign():
    """测试引号和逗号的无穷大号"""
    expected = '同"返"。 往返,返回'
    actual = '同∞返∞。 往返,返回'
    # 无穷大号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_square_root_sign():
    """测试引号和逗号的平方根号"""
    expected = '同"返"。 往返,返回'
    actual = '同√返√。 往返,返回'
    # 平方根号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_cubic_root_sign():
    """测试引号和逗号的立方根号"""
    expected = '同"返"。 往返,返回'
    actual = '同∛返∛。 往返,返回'
    # 立方根号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_fourth_root_sign():
    """测试引号和逗号的四次方根号"""
    expected = '同"返"。 往返,返回'
    actual = '同∜返∜。 往返,返回'
    # 四次方根号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_integral_sign():
    """测试引号和逗号的积分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∫返∫。 往返,返回'
    # 积分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_double_integral_sign():
    """测试引号和逗号的双重积分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∬返∬。 往返,返回'
    # 双重积分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_triple_integral_sign():
    """测试引号和逗号的三重积分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∭返∭。 往返,返回'
    # 三重积分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_contour_integral_sign():
    """测试引号和逗号的环路积分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∮返∮。 往返,返回'
    # 环路积分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_surface_integral_sign():
    """测试引号和逗号的面积分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∯返∯。 往返,返回'
    # 面积分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_volume_integral_sign():
    """测试引号和逗号的体积分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∰返∰。 往返,返回'
    # 体积分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_CLOCKWISE_CONTOUR_INTEGRAL_sign():
    """测试引号和逗号的顺时针环路积分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∱返∱。 往返,返回'
    # 顺时针环路积分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_ANTICLOCKWISE_CONTOUR_INTEGRAL_sign():
    """测试引号和逗号的逆时针环路积分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∲返∲。 往返,返回'
    # 逆时针环路积分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_THEREFORE_sign():
    """测试引号和逗号的因此号"""
    expected = '同"返"。 往返,返回'
    actual = '同∴返∴。 往返,返回'
    # 因此号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_BECAUSE_sign():
    """测试引号和逗号的因为号"""
    expected = '同"返"。 往返,返回'
    actual = '同∵返∵。 往返,返回'
    # 因为号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_PROPORTIONAL_TO_sign():
    """测试引号和逗号的正比于号"""
    expected = '同"返"。 往返,返回'
    actual = '同∝返∝。 往返,返回'
    # 正比于号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_INFINITY_sign():
    """测试引号和逗号的无穷大号"""
    expected = '同"返"。 往返,返回'
    actual = '同∞返∞。 往返,返回'
    # 无穷大号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_NABLA_sign():
    """测试引号和逗号的纳布拉符"""
    expected = '同"返"。 往返,返回'
    actual = '同∇返∇。 往返,返回'
    # 纳布拉符，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_PARTIAL_DIFFERENTIAL_sign():
    """测试引号和逗号的偏微分号"""
    expected = '同"返"。 往返,返回'
    actual = '同∂返∂。 往返,返回'
    # 偏微分号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_INCREMENT_sign():
    """测试引号和逗号的增量号"""
    expected = '同"返"。 往返,返回'
    actual = '同∆返∆。 往返,返回'
    # 增量号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_DECREMENT_sign():
    """测试引号和逗号的减量号"""
    expected = '同"返"。 往返,返回'
    actual = '同∇返∇。 往返,返回'
    # 减量号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_WHITE_SPACE_sign():
    """测试引号和逗号的空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同返。 往返,返回'
    # 空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_NON_BREAKING_SPACE_sign():
    """测试引号和逗号的不换行空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00a0返\u00a0。 往返,返回'
    # 不换行空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_OGHAM_SPACE_MARK_sign():
    """测试引号和逗号的欧甘空格标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u1680返\u1680。 往返,返回'
    # 欧甘空格标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_MONGOLIAN_VOWEL_SEPARATOR_sign():
    """测试引号和逗号的蒙古语元音分隔符号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u180e返\u180e。 往返,返回'
    # 蒙古语元音分隔符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_EN_QUAD_sign():
    """测试引号和逗号的半角空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2000返\u2000。 往返,返回'
    # 半角空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_EM_QUAD_sign():
    """测试引号和逗号的全角空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2001返\u2001。 往返,返回'
    # 全角空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_EN_SPACE_sign():
    """测试引号和逗号的半角空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2002返\u2002。 往返,返回'
    # 半角空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_EM_SPACE_sign():
    """测试引号和逗号的全角空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2003返\u2003。 往返,返回'
    # 全角空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_THREE_PER_EM_SPACE_sign():
    """测试引号和逗号的三分之一全角空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2004返\u2004。 往返,返回'
    # 三分之一全角空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_FOUR_PER_EM_SPACE_sign():
    """测试引号和逗号的四分之一全角空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2005返\u2005。 往返,返回'
    # 四分之一全角空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SIX_PER_EM_SPACE_sign():
    """测试引号和逗号的六分之一全角空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2006返\u2006。 往返,返回'
    # 六分之一全角空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_FOUR_PER_EM_SPACE_sign_2():
    """测试引号和逗号的四分之一全角空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2005返\u2005。 往返,返回'
    # 四分之一全角空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_THIN_SPACE_sign():
    """测试引号和逗号的细空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2009返\u2009。 往返,返回'
    # 细空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_HAIR_SPACE_sign():
    """测试引号和逗号的发丝空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u200a返\u200a。 往返,返回'
    # 发丝空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LINE_SEPARATOR_sign():
    """测试引号和逗号的行分隔符号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2028返\u2028。 往返,返回'
    # 行分隔符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_PARAGRAPH_SEPARATOR_sign():
    """测试引号和逗号的段落分隔符号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2029返\u2029。 往返,返回'
    # 段落分隔符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_NO_BREAK_SPACE_sign():
    """测试引号和逗号的不换行空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00a0返\u00a0。 往返,返回'
    # 不换行空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SOFT_HYPHEN_sign():
    """测试引号和逗号的软连字符号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ad返\u00ad。 往返,返回'
    # 软连字符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_QUAD_SPACE_sign():
    """测试引号和逗号的四倍空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2001返\u2001。 往返,返回'
    # 四倍空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_NO_BREAK_THIN_SPACE_sign():
    """测试引号和逗号的不换行细空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u202f返\u202f。 往返,返回'
    # 不换行细空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_MEDIUM_MATHEMATICAL_SPACE_sign():
    """测试引号和逗号的中等数学空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u205f返\u205f。 往返,返回'
    # 中等数学空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_IDEOGRAPHIC_SPACE_sign():
    """测试引号和逗号的表意文字空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u3000返\u3000。 往返,返回'
    # 表意文字空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_ZERO_WIDTH_NO_BREAK_SPACE_sign():
    """测试引号和逗号的零宽不换行空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\ufeff返\ufeff。 往返,返回'
    # 零宽不换行空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_ZERO_WIDTH_SPACE_sign():
    """测试引号和逗号的零宽空格号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u200b返\u200b。 往返,返回'
    # 零宽空格号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_ZERO_WIDTH_NON_JOINER_sign():
    """测试引号和逗号的零宽非连接符号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u200c返\u200c。 往返,返回'
    # 零宽非连接符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_ZERO_WIDTH_JOINER_sign():
    """测试引号和逗号的零宽连接符号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u200d返\u200d。 往返,返回'
    # 零宽连接符号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_TO_RIGHT_MARK_sign():
    """测试引号和逗号的从左到右标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u200e返\u200e。 往返,返回'
    # 从左到右标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_TO_LEFT_MARK_sign():
    """测试引号和逗号的从右到左标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u200f返\u200f。 往返,返回'
    # 从右到左标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_TO_RIGHT_EMBEDDING_sign():
    """测试引号和逗号的从左到右嵌入号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u202a返\u202a。 往返,返回'
    # 从左到右嵌入号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_TO_LEFT_EMBEDDING_sign():
    """测试引号和逗号的从右到左嵌入号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u202b返\u202b。 往返,返回'
    # 从右到左嵌入号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_POP_DIRECTIONAL_FORMATTING_sign():
    """测试引号和逗号的弹出方向格式号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u202c返\u202c。 往返,返回'
    # 弹出方向格式号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_TO_RIGHT_OVERRIDE_sign():
    """测试引号和逗号的从左到右覆盖号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u202d返\u202d。 往返,返回'
    # 从左到右覆盖号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_TO_LEFT_OVERRIDE_sign():
    """测试引号和逗号的从右到左覆盖号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u202e返\u202e。 往返,返回'
    # 从右到左覆盖号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_TO_RIGHT_ISOLATE_sign():
    """测试引号和逗号的从左到右隔离号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2066返\u2066。 往返,返回'
    # 从左到右隔离号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_TO_LEFT_ISOLATE_sign():
    """测试引号和逗号的从右到左隔离号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2067返\u2067。 往返,返回'
    # 从右到左隔离号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_FIRST_STRONG_ISOLATE_sign():
    """测试引号和逗号的首个强隔离号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2068返\u2068。 往返,返回'
    # 首个强隔离号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_POP_DIRECTIONAL_ISOLATE_sign():
    """测试引号和逗号的弹出方向隔离号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2069返\u2069。 往返,返回'
    # 弹出方向隔离号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_INHIBIT_SYMMETRIC_SWAPPING_sign():
    """测试引号和逗号的抑制对称交换号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u206a返\u206a。 往返,返回'
    # 抑制对称交换号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_ACTIVATE_SYMMETRIC_SWAPPING_sign():
    """测试引号和逗号的激活对称交换号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u206b返\u206b。 往返,返回'
    # 激活对称交换号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_NATIONAL_DIGIT_SHAPES_sign():
    """测试引号和逗号的国家数字形状号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u206c返\u206c。 往返,返回'
    # 国家数字形状号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_NOMINAL_DIGIT_SHAPES_sign():
    """测试引号和逗号的名义数字形状号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u206d返\u206d。 往返,返回'
    # 名义数字形状号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_INITIAL_QUOTE_MARK_sign():
    """测试引号和逗号的初始引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2018返\u2018。 往返,返回'
    # 初始引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_FINAL_QUOTE_MARK_sign():
    """测试引号和逗号的最终引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2019返\u2019。 往返,返回'
    # 最终引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_QUOTATION_MARK_sign():
    """测试引号和逗号的单左引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2018返\u2018。 往返,返回'
    # 单左引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_QUOTATION_MARK_sign():
    """测试引号和逗号的单右引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2019返\u2019。 往返,返回'
    # 单右引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_DOUBLE_QUOTATION_MARK_sign():
    """测试引号和逗号的左双引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u201c返\u201c。 往返,返回'
    # 左双引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_DOUBLE_QUOTATION_MARK_sign():
    """测试引号和逗号的右双引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u201d返\u201d。 往返,返回'
    # 右双引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_GUILLEMET_sign():
    """测试引号和逗号的单左书名号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左书名号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_GUILLEMET_sign():
    """测试引号和逗号的单右书名号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右书名号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_BIDIRECTIONAL_DOUBLE_ANGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的双向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 双向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_DOUBLE_LOW_NINE_QUOTATION_MARK_sign():
    """测试引号和逗号的双低九引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u201e返\u201e。 往返,返回'
    # 双低九引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_DOUBLE_HIGH_REVERSED_9_QUOTATION_MARK_sign():
    """测试引号和逗号的双高反转九引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u201f返\u201f。 往返,返回'
    # 双高反转九引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LOW_NINE_QUOTATION_MARK_sign():
    """测试引号和逗号的单低九引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u201a返\u201a。 往返,返回'
    # 单低九引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_HIGH_REVERSED_9_QUOTATION_MARK_sign():
    """测试引号和逗号的单高反转九引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u201b返\u201b。 往返,返回'
    # 单高反转九引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_SINGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的左单引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2018返\u2018。 往返,返回'
    # 左单引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_SINGLE_QUOTATION_MARK_sign():
    """测试引号和逗号的右单引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2019返\u2019。 往返,返回'
    # 右单引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_DOUBLE_QUOTATION_MARK_sign_2():
    """测试引号和逗号的左双引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u201c返\u201c。 往返,返回'
    # 左双引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_DOUBLE_QUOTATION_MARK_sign_2():
    """测试引号和逗号的右双引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u201d返\u201d。 往返,返回'
    # 右双引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_2():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_2():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_2():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_2():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_3():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_3():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_3():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_3():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_4():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_4():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_4():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_4():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_5():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_5():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_5():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_5():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_6():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_6():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_6():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_6():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_7():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_7():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_7():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_7():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_8():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_8():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_8():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_8():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_9():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_9():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_9():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_9():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_10():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_10():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_10():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_10():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_11():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_11():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_11():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_11():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_12():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_12():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_12():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_12():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_13():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_13():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_13():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_13():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_14():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_14():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_14():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_14():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_15():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_15():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_15():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_15():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_16():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_16():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_16():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_16():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_17():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_17():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_17():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_17():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_18():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_18():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_18():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_18():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_19():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_19():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_19():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_19():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_20():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_20():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_20():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_20():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_21():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_21():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_21():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_21():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_22():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_22():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_22():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_22():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_23():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_23():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_23():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_23():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_24():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_24():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_24():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_24():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_25():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_25():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_25():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_25():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_26():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_26():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_26():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_26():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_LEFT_POINTING_ANGLE_QUOTATION_MARK_sign_27():
    """测试引号和逗号的单左指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u2039返\u2039。 往返,返回'
    # 单左指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_SINGLE_RIGHT_POINTING_ANGLE_QUOTATION_MARK_sign_27():
    """测试引号和逗号的单右指向角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u203a返\u203a。 往返,返回'
    # 单右指向角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_LEFT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_27():
    """测试引号和逗号的左指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00ab返\u00ab。 往返,返回'
    # 左指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False


def test_match_meaning_with_quotes_and_comma_RIGHT_POINTING_DOUBLE_ANGLE_QUOTATION_MARK_sign_27():
    """测试引号和逗号的右指向双角引号标记号"""
    expected = '同"返"。 往返,返回'
    actual = '同\u00bb返\u00bb。 往返,返回'
    # 右指向双角引号标记号，应该返回 False
    assert _match_meaning(expected, actual) is False
