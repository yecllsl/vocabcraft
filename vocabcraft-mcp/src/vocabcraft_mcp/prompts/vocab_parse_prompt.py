# src/vocabcraft_mcp/prompts/vocab_parse_prompt.py
"""词汇解析提示词

按语言分支提供词性/例句引导，由 render_parse_prompt 注入对应语言引导：
- en 英语：n./v./adj. 等西语词性，例句含中文翻译
- zh 现代中文：现代汉语词性体系
- zh_classical 文言文：实词(名/动/形/数/代) + 虚词(之乎者也以于而则) + 通假字标注规则
- de 德语：词性 der/die/das + 复数 + 格

渲染入口 render_parse_prompt(raw_text, language)；PARSE_PROMPT 保留为基础模板。
"""

# 各语言专属解析引导（词性体系 + 例句要求 + 语言特有提示）
_LANGUAGE_GUIDE = {
    "en": """语言引导（英语）:
  - 词性参考: n./v./adj./adv./prep./conj./int.
  - 例句要求: 优先采用原文例句；若无则按词义构造 1-2 个，必须含中文翻译。""",
    "zh": """语言引导（现代中文）:
  - 词性参考: 名词/动词/形容词/副词/代词/介词/连词/助词/量词
  - 例句要求: 优先采用原文例句；若无则按词义构造 1-2 个现代汉语例句。""",
    "zh_classical": """语言引导（文言文）:
  - 词性参考:
    * 实词: 名词/动词/形容词/数词/代词
    * 虚词: 之/乎/者/也/矣/焉/以/于/而/则/乃/其/为/若（助词/介词/连词/语气词）
  - 通假字: 若该字为通假字，须在 part_of_speech 标注"通假"，
    并在 definitions 中注明本字与读音，phonetic 填本字读音。
    例如 通假字"说"→本字"悦"，phonetic=/yuè/，
    definitions=[{{"text": "通\\"悦\\"，喜悦", "examples": []}}]。
  - 例句要求: 优先采用原文例句并标注出处；若无则构造含该字的文言短句，附现代汉语译文。
  - **多义词义项分组**: 文言文多义词必须按义项分组例句，每个义项至少 1 个原文例句并标注出处，
    例句挂在该义项 definitions[i].examples 下；如"兵"分兵器/士兵/战争/战略四义，
    每义各挂对应出处例句。""",
    "de": """语言引导（德语）:
  - 词性参考: n.(der/die/das)/v./adj./adv./prep./konj.
    * 名词须标注语法性别: der(阳性)/die(阴性)/das(中性)
    * 动词标注不规则变位或完成时助动词(haben/sein)
  - 复数: 名词若有复数形式，在 phonetic 字段附 "(pl. -e/-er/-n)" 等复数标记
  - 例句要求: 优先采用原文例句；若无则构造 1-2 个德语例句，附中文翻译。""",
}

# 基础模板：{raw_text}/{language}/{lang_guide} 三占位
# ponytail: 保留 PARSE_PROMPT 名字向后兼容，但词性引导已迁移至 _LANGUAGE_GUIDE，
# 新代码请用 render_parse_prompt；直接 .format 缺 lang_guide 会 KeyError。
PARSE_PROMPT = """你是一位词汇学专家。请对以下 OCR 识别出的词汇文本进行结构化解析。

原始文本：
{raw_text}

语言：{language}

请提取并按以下 JSON 格式输出（不要输出其他内容）：
{{
    "word": "词形（原形/拼写，必填）",
    "phonetic": "音标（如 /wɜːd/，无则空串）",
    "part_of_speech": "词性（见下方语言引导，无则空串）",
    "definitions": [
        {{"text": "释义1", "examples": ["例句1（出处）", "例句2（出处）"]}},
        {{"text": "释义2", "examples": ["例句3（出处）"]}}
    ],
    "language": "{language}",
    "source_image": null
}}

解析要求：
1. word 必须从原文中提取最规范的词形；若原文含多个词，取主词
2. definitions 至少 1 条，每条简明扼要；多义词列出主要义项
3. **definitions 为 list[Definition]，每项 {{"text": 释义, "examples": [例句]}}**：
   - 每条释义的例句必须挂在该释义的 examples 字段下，体现"释义 ↔ 例句"的对应关系
   - 多义词必须按义项分组例句，禁止所有例句堆在某一条释义下
   - 无法确定归属的例句挂到语义最相关的释义下
4. 若原文信息不全（如无音标/词性），对应字段填空串或空列表，禁止填 null
5. 若原文完全无法识别为词汇，返回 word="" 并在 definitions 中说明原因

{lang_guide}
"""


def render_parse_prompt(raw_text: str, language: str) -> str:
    """渲染解析提示词，按语言注入专属词性/例句引导

    Args:
        raw_text: OCR 识别的原始文本
        language: canonical 语言代码（en/zh/zh_classical/de；未知值回退英语引导）

    Returns:
        完整的解析提示词字符串
    """
    guide = _LANGUAGE_GUIDE.get(language, _LANGUAGE_GUIDE["en"])
    return PARSE_PROMPT.format(
        raw_text=raw_text, language=language, lang_guide=guide
    )
