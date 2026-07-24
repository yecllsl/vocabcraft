# src/vocabcraft_mcp/tools/ocr_recognize.py
"""OCR 识别 Tool

使用 PaddleOCR 对词汇图片进行文字识别，返回原始文本。
支持懒加载 OCR 引擎，避免模块导入时加载模型导致启动缓慢。
按语言选择 PaddleOCR lang 参数（en/ch/german），引擎实例按 lang 分键缓存。

PaddleOCR 为可选依赖（见 pyproject.toml [ocr] extra），
未安装时调用 OCR 会得到友好降级响应，而非崩溃。

骨架阶段：完成文件存在性检查与懒加载框架，OCR 引擎调用与解析 prompt 拼装已就绪，
后续 Task 可在此基础上对接真实 paddleocr 调用结果。
"""
from pathlib import Path

from vocabcraft_mcp.models import normalize_language
from vocabcraft_mcp.prompts.vocab_parse_prompt import render_parse_prompt

# 语言 canonical 代码 → PaddleOCR lang 参数映射
# ponytail: zh/zh_classical 共用 "ch"（中英混合模型），文言文 vs 现代中文依赖解析层区分
_PADDLE_LANG = {
    "en": "en",
    "zh": "ch",
    "zh_classical": "ch",
    "de": "german",
}

# OCR 引擎实例缓存：按 PaddleOCR lang 分键，避免重复加载模型
_ocr_engines: dict = {}


def _get_ocr_engine(language: str):
    """获取 PaddleOCR 引擎实例（按语言懒加载单例）

    首次调用某语言时初始化对应 PaddleOCR 引擎，后续复用。
    使用 use_angle_cls=True 支持旋转文字识别，lang 按语言选择。

    PaddleOCR 为可选依赖，未安装时抛 ImportError 并附安装指引，
    由上层 ocr_recognize 转为友好降级响应。
    """
    paddle_lang = _PADDLE_LANG.get(language, "en")
    if paddle_lang not in _ocr_engines:
        try:
            from paddleocr import PaddleOCR  # noqa: WPS433 (懒加载)
        except ImportError as exc:
            raise ImportError(
                "未安装 PaddleOCR。请运行 `uv sync --extra ocr` "
                "或 `uv pip install paddleocr paddlepaddle` 后重试。"
            ) from exc
        _ocr_engines[paddle_lang] = PaddleOCR(
            use_angle_cls=True, lang=paddle_lang, show_log=False
        )
    return _ocr_engines[paddle_lang]


def _run_paddle_ocr(image_path: str, language: str) -> str:
    """执行 PaddleOCR 识别，返回识别文本

    Args:
        image_path: 图片文件路径
        language: canonical 语言代码，用于选择 OCR 引擎

    Returns:
        识别文本，每行一个结果，用换行符连接
    """
    engine = _get_ocr_engine(language)
    result = engine.ocr(image_path, cls=True)
    lines = []
    if result and result[0]:
        for line in result[0]:
            # PaddleOCR 返回格式: [坐标列表, (文本, 置信度)]
            if line and len(line) >= 2:
                lines.append(line[1][0])
    return "\n".join(lines)


def ocr_recognize(image_path: str, language: str = "en") -> dict:
    """OCR 识别词汇图片

    对图片进行 OCR 文字识别，返回原始文本及结构化解析提示。
    识别失败时提供降级处理，提示用户手动输入。

    Args:
        image_path: 词汇图片的文件路径
        language: 语言代码（支持别名归一化，如 "中文"/"german"/"文言文"）

    Returns:
        包含以下字段的字典:
        - raw_text: OCR 识别的原始文本
        - parse_prompt: 词汇解析提示（含语言上下文，供 AI 解析使用）
        - language: 归一化后的 canonical 语言代码
        - error: 错误信息（仅在出错时存在）
    """
    # 归一化语言代码（接受别名/大小写变体）
    lang = normalize_language(language)

    # 文件存在性检查
    if not Path(image_path).exists():
        return {
            "raw_text": "",
            "language": lang,
            "error": f"图片文件不存在: {image_path}",
        }

    # 执行 OCR 识别
    try:
        raw_text = _run_paddle_ocr(image_path, lang)
    except Exception as e:
        return {
            "raw_text": "",
            "language": lang,
            "error": f"OCR 识别失败: {str(e)}，请尝试手动输入词汇文本",
        }

    # 识别结果为空
    if not raw_text.strip():
        return {
            "raw_text": "",
            "language": lang,
            "error": "OCR 未识别到任何文字，请尝试手动输入",
        }

    # 返回识别结果及结构化解析提示（含语言上下文）
    return {
        "raw_text": raw_text,
        "language": lang,
        "parse_prompt": render_parse_prompt(raw_text, lang),
    }
