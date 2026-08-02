# src/vocabcraft_mcp/tools/parse_vocab.py
"""AI 结构化解析词汇 Tool

三模式解析（按优先级排列）：
1. **对话多模态模式（首选）**：无参数调用，宿主 LLM 读取对话上下文中的图片
2. **本地路径多模态模式**：传入 image_path，宿主 LLM 读取指定路径的图片
3. **文本模式（后备）**：传入 text，宿主 LLM 基于文本完成解析

骨架阶段：仅返回 prompt 与默认值模板，不对接具体 LLM 客户端。
"""
from vocabcraft_mcp.models import normalize_language
from vocabcraft_mcp.prompts.vocab_parse_prompt import (
    render_multimodal_parse_prompt,
    render_parse_prompt,
)


def parse_vocab(image_path: str = "", text: str = "", language: str = "en") -> dict:
    """AI 结构化解析词汇（三模式）

    优先级：对话多模态 > 本地路径多模态 > 文本模式。

    Args:
        image_path: 词汇图片本地路径（可选，多模态模式使用）
        text: 文本内容（文本模式使用）
        language: 语言代码（支持别名归一化，如 "中文"/"german"/"文言文"）

    Returns:
        包含以下字段的字典:
        - structured_vocab: 解析结果（骨架阶段为 None，由宿主 LLM 填充）
        - parse_prompt: AI 解析提示词（含按语言分支的词性/例句引导）
        - language: 归一化后的 canonical 语言代码
        - image_path: 回显图片路径（dialog 模式为空串）
        - mode: 当前解析模式，"dialog"/"multimodal"/"text"
        - error: 错误信息（仅在出错时存在）
    """
    # 归一化语言代码，驱动 prompt 按语言分支
    lang = normalize_language(language)

    # 模式 1：对话多模态模式（首选）— 用户直接在对话中上传了图片
    if not image_path and not text:
        prompt = render_multimodal_parse_prompt(lang)
        return {
            "structured_vocab": None,
            "language": lang,
            "parse_prompt": prompt,
            "image_path": "",
            "mode": "dialog",
            "message": "请使用 parse_prompt 读取对话中的图片完成解析，结果填入 structured_vocab",
        }

    # 模式 2：本地路径多模态模式 — 用户提供了本地图片路径
    if image_path and image_path.strip():
        prompt = render_multimodal_parse_prompt(lang)
        return {
            "structured_vocab": None,
            "language": lang,
            "parse_prompt": prompt,
            "image_path": image_path,
            "mode": "multimodal",
            "message": "请使用 parse_prompt 读取指定路径图片完成解析，结果填入 structured_vocab",
        }

    # 模式 3：文本模式（后备）
    if text and text.strip():
        prompt = render_parse_prompt(text, lang)
        return {
            "structured_vocab": None,
            "language": lang,
            "parse_prompt": prompt,
            "image_path": "",
            "mode": "text",
            "message": "请使用 parse_prompt 完成解析，结果填入 structured_vocab",
        }

    # 不应到达此处（前两个条件覆盖了所有输入组合），但保留兜底
    return {
        "structured_vocab": None,
        "language": lang,
        "image_path": "",
        "error": "解析失败：请提供图片（对话上传或本地路径）或文本",
    }
