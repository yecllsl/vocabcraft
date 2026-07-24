# src/vocabcraft_mcp/tools/parse_vocab.py
"""AI 结构化解析词汇 Tool

接收图片路径或 OCR 原始文本，构造 AI 解析 prompt，由调用方（宿主 LLM）执行解析。
返回包含 parse_prompt 的字典，宿主 LLM 据此输出词汇结构化 JSON。

骨架阶段：仅返回 prompt 与默认值模板，不对接具体 LLM 客户端。
完整实现 TODO：对接 LLM 客户端，直接返回解析结果。
"""
from vocabcraft_mcp.models import normalize_language
from vocabcraft_mcp.prompts.vocab_parse_prompt import render_parse_prompt


def parse_vocab(image_path: str = "", ocr_text: str = "", language: str = "en") -> dict:
    """AI 结构化解析词汇

    优先使用 ocr_text；若 ocr_text 为空且提供 image_path，
    可由调用方先调用 ocr_recognize 获取文本后再传入。

    Args:
        image_path: 词汇图片路径（可选，骨架阶段不直接读取）
        ocr_text: OCR 识别的原始文本
        language: 语言代码（支持别名归一化，如 "中文"/"german"/"文言文"）

    Returns:
        包含以下字段的字典:
        - structured_vocab: 解析结果（骨架阶段为 None，由宿主 LLM 填充）
        - parse_prompt: AI 解析提示词（含按语言分支的词性/例句引导）
        - language: 归一化后的 canonical 语言代码
        - image_path: 回显图片路径
        - error: 错误信息（仅在出错时存在）
    """
    # 归一化语言代码（接受别名/大小写变体），驱动 prompt 按语言分支
    lang = normalize_language(language)

    if not ocr_text or not ocr_text.strip():
        return {
            "structured_vocab": None,
            "language": lang,
            "image_path": image_path,
            "error": "OCR 文本为空，无法解析；请先调用 ocr_recognize 或手动提供 ocr_text",
        }

    # 渲染解析 prompt（render_parse_prompt 按 language 分支提供词性/例句引导）
    prompt = render_parse_prompt(ocr_text, lang)

    # TODO: 对接 LLM 客户端，直接调用并解析 JSON 返回 structured_vocab
    return {
        "structured_vocab": None,
        "language": lang,
        "parse_prompt": prompt,
        "image_path": image_path,
        "message": "请使用 parse_prompt 调用 LLM 完成解析，结果填入 structured_vocab",
    }
