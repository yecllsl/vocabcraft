# tests/test_tools_parse.py
"""词汇解析 Tool 单元测试（骨架阶段）

验证 import + 空文本降级 + prompt 拼装。
LLM 对接用例待后续 Task 补全。
"""

from vocabcraft_mcp.tools.parse_vocab import parse_vocab


def test_parse_importable():
    """骨架测试：模块可正常 import"""
    assert callable(parse_vocab)


def test_parse_empty_text():
    """空文本时返回 error"""
    result = parse_vocab(ocr_text="")
    assert "error" in result
    assert result["structured_vocab"] is None


def test_parse_returns_prompt():
    """正常文本返回 parse_prompt"""
    result = parse_vocab(image_path="/tmp/x.jpg", ocr_text="hello /həˈləʊ/ int. 你好")
    assert result["structured_vocab"] is None  # 骨架阶段未对接 LLM
    assert "parse_prompt" in result
    assert result["image_path"] == "/tmp/x.jpg"


# TODO: 对接 LLM 客户端后补全以下用例
# - test_parse_llm_integration: 验证 LLM 返回的 structured_vocab 结构
# - test_parse_multi_definition: 多义词解析
# - test_parse_unrecognizable_text: 无法识别为词汇时的兜底
