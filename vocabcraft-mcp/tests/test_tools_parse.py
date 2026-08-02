# tests/test_tools_parse.py
"""词汇解析 Tool 单元测试

验证三模式解析（按优先级）：
1. 对话多模态模式（dialog）— 无参数，宿主 LLM 读取对话上下文中的图片
2. 本地路径多模态模式（multimodal）— 传入 image_path
3. 文本模式（text）— 传入 text
"""

from vocabcraft_mcp.tools.parse_vocab import parse_vocab


def test_parse_importable():
    """骨架测试：模块可正常 import"""
    assert callable(parse_vocab)


# ── 模式 1：对话多模态（首选） ──

def test_parse_dialog_mode():
    """无参数时使用对话多模态模式（首选）"""
    result = parse_vocab()
    assert result["mode"] == "dialog"
    assert "parse_prompt" in result
    assert "图片" in result["parse_prompt"]
    assert result["image_path"] == ""
    assert result["structured_vocab"] is None


def test_parse_dialog_with_language():
    """对话多模态模式支持语言参数"""
    result = parse_vocab(language="文言文")
    assert result["mode"] == "dialog"
    assert result["language"] == "zh_classical"


def test_parse_dialog_only_language():
    """仅传 language 时仍为对话多模态模式"""
    result = parse_vocab(language="de")
    assert result["mode"] == "dialog"
    assert result["language"] == "de"


# ── 模式 2：本地路径多模态 ──

def test_parse_multimodal_mode():
    """有 image_path 时使用本地路径多模态模式"""
    result = parse_vocab(image_path="/tmp/vocab.jpg", language="en")
    assert result["mode"] == "multimodal"
    assert "parse_prompt" in result
    assert "图片" in result["parse_prompt"]
    assert result["image_path"] == "/tmp/vocab.jpg"
    assert result["structured_vocab"] is None


def test_parse_multimodal_with_language():
    """本地路径多模态模式支持语言参数"""
    result = parse_vocab(image_path="/tmp/vocab.jpg", language="文言文")
    assert result["mode"] == "multimodal"
    assert result["language"] == "zh_classical"


def test_parse_multimodal_priority_over_text():
    """同时提供 image_path 和 text 时，image_path 优先"""
    result = parse_vocab(
        image_path="/tmp/vocab.jpg",
        text="hello /həˈləʊ/ int. 你好",
    )
    assert result["mode"] == "multimodal"


# ── 模式 3：文本模式（后备） ──

def test_parse_text_fallback_mode():
    """无 image_path 但有 text 时使用文本模式"""
    result = parse_vocab(text="hello /həˈləʊ/ int. 你好")
    assert result["mode"] == "text"
    assert "parse_prompt" in result
    assert result["structured_vocab"] is None


def test_parse_text_empty_image_path():
    """image_path 为空字符串但 text 非空时回退到文本模式"""
    result = parse_vocab(image_path="", text="test word")
    assert result["mode"] == "text"
    assert "parse_prompt" in result


# TODO: 对接 LLM 客户端后补全以下用例
# - test_parse_llm_integration: 验证 LLM 返回的 structured_vocab 结构
# - test_parse_multi_definition: 多义词解析
# - test_parse_unrecognizable_text: 无法识别为词汇时的兜底