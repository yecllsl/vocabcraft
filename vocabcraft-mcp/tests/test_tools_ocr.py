# tests/test_tools_ocr.py
"""OCR Tool 单元测试（骨架阶段）

验证 import + 文件不存在降级响应。
真实 PaddleOCR 调用需 mock，待后续 Task 补全。
"""

from vocabcraft_mcp.tools.ocr_recognize import ocr_recognize


def test_ocr_importable():
    """骨架测试：模块可正常 import"""
    assert callable(ocr_recognize)


def test_ocr_file_not_exist():
    """文件不存在时返回友好降级响应"""
    result = ocr_recognize("nonexistent_file_12345.jpg")
    assert result["raw_text"] == ""
    assert "error" in result
    assert "不存在" in result["error"]


# TODO: 以下用例需 mock PaddleOCR 引擎，待 OCR 模块对接 paddleocr 后补全
# - test_ocr_with_mock: 模拟 PaddleOCR 正常识别流程
# - test_ocr_empty_result: 模拟 OCR 返回空结果
# - test_ocr_paddleocr_not_installed: 模拟未安装 paddleocr 时的降级
# - test_ocr_success_returns_parse_prompt: 验证返回 parse_prompt
