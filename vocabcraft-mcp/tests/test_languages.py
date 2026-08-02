# tests/test_languages.py
"""多语言支持单元测试

覆盖中/德/英三语完整处理链路:
    - normalize_language: 别名归一化、未知值保留、None 默认
    - StructuredVocab.language 校验器触发归一化
    - render_parse_prompt 按语言分支（文言文实词/虚词/通假字、德语词性 der/die/das）
    - parse_vocab language 参数透传与归一化
    - generate_quiz 默认题型按语言（中文/文言文→释义，英语/德语→拼写）
"""

import pytest

from vocabcraft_mcp.models import (
    StructuredVocab,
    SUPPORTED_LANGUAGES,
    normalize_language,
)
from vocabcraft_mcp.prompts.vocab_parse_prompt import (
    render_parse_prompt,
    _LANGUAGE_GUIDE,
)
from vocabcraft_mcp.tools.parse_vocab import parse_vocab
from vocabcraft_mcp.tools.crud import save_vocab
from vocabcraft_mcp.tools.quiz import generate_quiz


# ──────────────────────────────────────────
# normalize_language
# ──────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    # 英语别名
    ("en", "en"), ("EN", "en"), ("english", "en"), ("English", "en"), ("英语", "en"), ("英文", "en"),
    # 现代中文别名
    ("zh", "zh"), ("chinese", "zh"), ("中文", "zh"), ("汉语", "zh"), ("现代汉语", "zh"),
    # 文言文别名（实词/虚词/通假字场景）
    ("zh_classical", "zh_classical"), ("文言", "zh_classical"),
    ("文言文", "zh_classical"), ("lzh", "zh_classical"), ("古汉语", "zh_classical"),
    ("classical_chinese", "zh_classical"),
    # 德语别名
    ("de", "de"), ("german", "de"), ("Deutsch", "de"), ("deutsch", "de"), ("德语", "de"), ("德文", "de"),
    # 未知值小写保留（不拒绝，兼容 fr 等测试数据与未来扩展）
    ("fr", "fr"), ("FR", "fr"), ("klingon", "klingon"),
    # 空白 strip
    ("  EN  ", "en"), ("\tzh\n", "zh"),
])
def test_normalize_language(raw, expected):
    """语言别名归一化：已知别名→canonical，未知值小写保留"""
    assert normalize_language(raw) == expected


def test_normalize_language_none():
    """None 回退 en"""
    assert normalize_language(None) == "en"


def test_supported_languages_contains_core():
    """SUPPORTED_LANGUAGES 必含中/德/英及文言文"""
    assert {"en", "zh", "zh_classical", "de"}.issubset(SUPPORTED_LANGUAGES)


# ──────────────────────────────────────────
# StructuredVocab.language 校验器
# ──────────────────────────────────────────

def test_structured_vocab_language_normalized():
    """StructuredVocab 构造时 language 经校验器归一化"""
    v = StructuredVocab(word="之", language="文言文")
    assert v.language == "zh_classical"
    v2 = StructuredVocab(word="Hallo", language="Deutsch")
    assert v2.language == "de"
    v3 = StructuredVocab(word="hello", language="English")
    assert v3.language == "en"


def test_structured_vocab_language_unknown_preserved():
    """未知语言原样小写保留（校验器不拒绝）"""
    v = StructuredVocab(word="bonjour", language="FR")
    assert v.language == "fr"


def test_structured_vocab_language_default_en():
    """未传 language 默认 en"""
    v = StructuredVocab(word="hello")
    assert v.language == "en"


# ──────────────────────────────────────────
# render_parse_prompt 按语言分支
# ──────────────────────────────────────────

def test_language_guide_keys_match_supported():
    """_LANGUAGE_GUIDE 覆盖所有支持语言"""
    for lang in SUPPORTED_LANGUAGES:
        assert lang in _LANGUAGE_GUIDE, f"语言 {lang} 缺少解析引导"


def test_parse_prompt_classical_chinese_branch():
    """文言文 prompt 含实词/虚词/通假字引导"""
    prompt = render_parse_prompt("之", "zh_classical")
    assert "实词" in prompt
    assert "虚词" in prompt
    assert "通假" in prompt
    assert "之/乎/者/也" in prompt
    assert "zh_classical" in prompt  # language 字段回写


def test_parse_prompt_german_branch():
    """德语 prompt 含 der/die/das 词性与复数引导"""
    prompt = render_parse_prompt("Haus", "de")
    assert "der" in prompt
    assert "die" in prompt
    assert "das" in prompt
    assert "复数" in prompt


def test_parse_prompt_english_branch():
    """英语 prompt 含基础词性引导与中文翻译要求"""
    prompt = render_parse_prompt("hello", "en")
    assert "n./v./adj" in prompt
    assert "中文翻译" in prompt


def test_parse_prompt_modern_chinese_branch():
    """现代中文 prompt 含现代汉语词性体系"""
    prompt = render_parse_prompt("学习", "zh")
    assert "名词/动词/形容词" in prompt


def test_parse_prompt_unknown_language_falls_back():
    """未知语言回退英语引导"""
    prompt = render_parse_prompt("bonjour", "fr")
    assert "n./v./adj" in prompt  # 英语引导作为兜底


# ──────────────────────────────────────────
# parse_vocab language 透传
# ──────────────────────────────────────────

def test_parse_vocab_normalizes_language():
    """parse_vocab 归一化 language 并透传到 prompt"""
    result = parse_vocab(ocr_text="之乎者也", language="文言")
    assert result["language"] == "zh_classical"
    assert "通假" in result["parse_prompt"]


def test_parse_vocab_german_branch():
    """parse_vocab 德语分支渲染"""
    result = parse_vocab(ocr_text="Haus", language="deutsch")
    assert result["language"] == "de"
    assert "der" in result["parse_prompt"]


def test_parse_vocab_empty_text_with_language():
    """空文本时进入对话多模态模式（dialog），language 仍归一化"""
    result = parse_vocab(ocr_text="", language="Deutsch")
    assert result["language"] == "de"
    assert result["mode"] == "dialog"
    assert "parse_prompt" in result
    assert result["structured_vocab"] is None


# ──────────────────────────────────────────
# generate_quiz 默认题型按语言
# ──────────────────────────────────────────

def test_generate_quiz_default_type_classical_chinese(isolated_storage, make_vocab_data):
    """文言文词汇默认题型为'释义'（汉字无拼写概念），answer 编码为 '词性|释义'"""
    save_vocab(make_vocab_data("之", "vocab_lzh_01", language="zh_classical"))
    result = generate_quiz("vocab_lzh_01")
    quizzes = result["quizzes"]
    assert len(quizzes) == 1
    assert quizzes[0]["quiz"]["quiz_type"] == "释义"
    # zh_classical 释义题 answer 编码为 "词性|释义"（make_vocab_data 默认 part_of_speech="int."、definitions[0]="你好"）
    assert quizzes[0]["quiz"]["answer"] == "int.|你好"


def test_generate_quiz_default_type_modern_chinese(isolated_storage, make_vocab_data):
    """现代中文词汇默认题型为'释义'"""
    save_vocab(make_vocab_data("学习", "vocab_zh_01", language="zh"))
    result = generate_quiz("vocab_zh_01")
    assert result["quiz"]["quiz_type"] == "释义"


def test_generate_quiz_default_type_german(isolated_storage, make_vocab_data):
    """德语词汇默认题型为'拼写'"""
    save_vocab(make_vocab_data("Haus", "vocab_de_01", language="de"))
    result = generate_quiz("vocab_de_01")
    assert result["quiz"]["quiz_type"] == "拼写"
    assert result["quiz"]["answer"] == "Haus"  # 拼写题 answer=词形


def test_generate_quiz_default_type_english(isolated_storage, make_vocab_data):
    """英语词汇默认题型为'拼写'（向后兼容）"""
    save_vocab(make_vocab_data("hello", "vocab_en_01", language="en"))
    result = generate_quiz("vocab_en_01")
    assert result["quiz"]["quiz_type"] == "拼写"


def test_generate_prompt_contains_language_context(isolated_storage, make_vocab_data):
    """命题 prompt 含语言上下文，按词汇语言匹配"""
    save_vocab(make_vocab_data("Haus", "vocab_de_02", language="de"))
    result = generate_quiz("vocab_de_02")
    assert "语言：de" in result["generate_prompt"]
