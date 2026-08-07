# src/vocabcraft_mcp/models.py
"""数据模型定义 - 词汇学习与制作系统的核心数据结构

模型层级:
    StructuredVocab          词汇结构化信息（词形/音标/词性/释义/例句）
    ReviewState              SM-2 记忆状态（EF/interval/repetitions/next_review）
    VocabRecord              词汇记录 = StructuredVocab + ReviewState + 时间戳
    Quiz                     考题（选择/填空/拼写/释义）
    ReviewRecord             单次复习记录（含评分前后 EF）
    ReviewSchedule           复习计划项（到期日/状态/关联考题）

设计: 结构化信息与记忆状态分离，便于 grade_quiz 通过 patch_vocab 只改
review_state 子字段而不动 structured，避免覆盖用户确认过的词汇内容。
使用 Pydantic v2，字段校验器保证 ID 前缀与枚举值合法性。
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

# 题型枚举：四种固定题型，校验器统一引用
VALID_QUIZ_TYPES = {"选择", "填空", "拼写", "释义"}
# 复习计划状态枚举
VALID_SCHEDULE_STATUS = {"待复习", "已完成", "已跳过"}

# 支持的语言 canonical 代码（中/德/英完整处理，其他语言可存储但不保证完整处理）
SUPPORTED_LANGUAGES = {"en", "zh", "zh_classical", "de"}

# 词性简称→全称映射（标准化导入数据用）
_POS_ABBR_MAP: dict[str, str] = {
    # 中文简称
    "介": "介词", "动": "动词", "名": "名词",
    "形": "形容词", "副": "副词", "连": "连词",
    "量": "量词", "代": "代词", "数": "数词",
    "叹": "叹词", "助": "助词", "拟": "拟声词",
    "词": "名词",
    # 英文缩写
    "n": "名词", "noun": "名词",
    "v": "动词", "verb": "动词", "vi": "动词", "vt": "动词",
    "adj": "形容词", "adjective": "形容词",
    "adv": "副词", "adverb": "副词",
    "prep": "介词", "conj": "连词",
    "pron": "代词", "num": "数词",
    "interj": "叹词", "aux": "助词",
    "part": "助词", "particle": "助词",
}


def normalize_pos(text: str) -> str:
    """标准化词性字符串：简称→全称、/→、、去重

    处理 '动、介' → '动词、介词'
    处理 'n./v./adj.' → '名词、动词、形容词'
    处理 '名 词、动词' → '名词、动词'

    供 save_vocab / xlsx_import 等所有数据入库路径使用，防止脏数据产生。
    """
    import re  # noqa: WPS433 (内联导入，避免 models.py 顶层 import re)

    if not text:
        return text

    # 1. 替换 / 为 、
    text = text.replace("/", "、")

    # 2. 按 、分割，再按空格拆分每个子项
    parts = text.split("、")
    result_parts: list[str] = []
    for part in parts:
        subs = [s.strip() for s in re.split(r"\s+", part) if s.strip()]
        expanded: list[str] = []
        for s in subs:
            key = s.strip().rstrip(".").lower()
            e = _POS_ABBR_MAP.get(key, s)
            if e not in expanded:
                expanded.append(e)
        result_parts.extend(expanded)

    # 3. 去重保持顺序
    seen: list[str] = []
    final: list[str] = []
    for p in result_parts:
        if p not in seen:
            seen.append(p)
            final.append(p)
    return "、".join(final)


# 语言别名归一化映射：常见同义词/大小写变体/中文别名 → canonical 代码
# ponytail: 单点归一化，比每个调用点判断省；覆盖解析/出题全链路入口
_LANGUAGE_ALIASES = {
    # 英语
    "en": "en", "eng": "en", "english": "en", "英语": "en", "英文": "en",
    # 现代中文
    "zh": "zh", "zhs": "zh", "chinese": "zh", "中文": "zh", "汉语": "zh", "现代汉语": "zh",
    # 文言文（实词/虚词/通假字）
    "zh_classical": "zh_classical", "classical_chinese": "zh_classical",
    "文言": "zh_classical", "文言文": "zh_classical", "古汉语": "zh_classical",
    "lzh": "zh_classical",
    # 德语
    "de": "de", "deu": "de", "german": "de", "deutsch": "de", "德语": "de", "德文": "de",
}


def normalize_language(v) -> str:
    """语言代码归一化：已知别名映射到 canonical，未知值小写保留

    供 OCR/解析/出题等入口复用，保证全链路语言代码一致。
    ponytail: 不做白名单拒绝，兼容现有数据与未来扩展。
    """
    if v is None:
        return "en"
    key = v.strip().lower()
    return _LANGUAGE_ALIASES.get(key, key)


class Definition(BaseModel):
    """释义项（含关联例句）

    每条释义内嵌自己的例句列表，建立"释义 ↔ 例句"的对应关系，
    解决多义词例句归属问题（如文言文"兵"的兵器/士兵/战争/战略四义各有例句）。
    """
    text: str = Field(description="释义文本")
    examples: list[str] = Field(default_factory=list, description="该释义对应的例句列表")
    part_of_speech: str = Field(default="", description="义项级词性（zh_classical 必填，其他语言可选）")


class StructuredVocab(BaseModel):
    """词汇结构化信息

    由 parse_vocab 渲染 prompt 交宿主 LLM 解析后填充。
    source_image 为原图路径，用于溯源；None 表示手动录入无图。

    definitions 为 list[Definition]，每项内嵌该释义的例句，
    体现"释义 ↔ 例句"的对应关系；旧数据（list[str] definitions +
    顶层 examples）由 _merge_legacy_examples 自动归并转换。
    """
    word: str = Field(description="词形")
    phonetic: str = Field(default="", description="音标，如 /həˈloʊ/")
    part_of_speech: str = Field(default="", description="词性，如 n./v./adj.")
    definitions: list[Definition] = Field(default_factory=list, description="释义列表，每项含 text 与关联例句 examples")
    language: str = Field(default="en", description="语言代码（en/zh/zh_classical/de，支持别名归一化）")
    source_image: str | None = Field(default=None, description="原图路径，手动录入为 None")

    @model_validator(mode="before")
    @classmethod
    def _merge_legacy_examples(cls, data):
        """旧格式兼容：list[str] definitions 与顶层 examples 自动归并为新结构

        处理两种旧数据形态：
        1. definitions: ["释义1", "释义2"]  →  [{"text": "释义1", "examples": []}, ...]
        2. 顶层 examples: ["例句1", "例句2"] →  全部归并到 definitions[0].examples
           （旧数据无法判断例句归属，统一挂到首个释义下，用户可手动编辑重分配）
        若 definitions 为空但 examples 非空，建一个空 text 的释义承载，避免数据丢失。
        """
        if not isinstance(data, dict):
            return data
        data = dict(data)  # 浅拷贝，避免改坏调用方传入的字典

        # 1. 归一化 definitions 为 list[dict]
        raw_defs = data.get("definitions", [])
        norm_defs: list[dict] = []
        for d in raw_defs or []:
            if isinstance(d, str):
                norm_defs.append({"text": d, "examples": []})
            elif isinstance(d, dict):
                # 兼容缺 examples 字段的 dict
                item = dict(d)
                item.setdefault("examples", [])
                norm_defs.append(item)
            elif isinstance(d, BaseModel):
                # 已构造的 Definition 对象（如代码内显式传 Definition(...)）
                item = d.model_dump()
                item.setdefault("examples", [])
                norm_defs.append(item)
            else:
                norm_defs.append({"text": str(d), "examples": []})

        # 2. 旧顶层 examples 归并到 definitions[0].examples
        legacy_examples = data.pop("examples", None)
        if legacy_examples:
            if norm_defs:
                first = norm_defs[0]
                first["examples"] = list(first.get("examples", [])) + list(legacy_examples)
            else:
                # 无 definitions 但有 examples：建空释义承载，避免数据丢失
                norm_defs.append({"text": "", "examples": list(legacy_examples)})

        data["definitions"] = norm_defs
        return data

    @field_validator("language")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        """语言代码归一化（委托模块级 normalize_language，详见该函数 docstring）"""
        return normalize_language(v)


class ReviewState(BaseModel):
    """SM-2 记忆状态

    由 algorithms.compute_next_review 更新。新词初始值: EF=2.5, interval=0, repetitions=0。
    next_review 为 YYYY-MM-DD 字符串，空串表示尚未排程（新建词由 save_vocab 注入首次排程）。
    """
    ease_factor: float = Field(default=2.5, description="SM-2 难度系数")
    interval: int = Field(default=0, description="当前复习间隔(天)")
    repetitions: int = Field(default=0, description="已连续答对次数")
    next_review: str = Field(default="", description="下次到期复习日期 YYYY-MM-DD，空串=未排程")
    last_review: str | None = Field(default=None, description="上次复习日期 YYYY-MM-DD")
    last_word_grade: int | None = Field(default=None, description="上次词级综合评分 1-4，用于掌握度判定")


class VocabRecord(BaseModel):
    """词汇记录 = 结构化信息 + 记忆状态 + 时间戳

    id 格式: vocab_YYYYMMDD_NNN，由 save_vocab 自动生成或由调用方提供。
    review_state 默认注入新词初始状态，调用方可传已存在状态覆盖。
    """
    id: str = Field(description="词汇唯一ID，格式 vocab_YYYYMMDD_NNN")
    structured: StructuredVocab = Field(description="词汇结构化信息")
    review_state: ReviewState = Field(default_factory=ReviewState, description="SM-2 记忆状态")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="最近更新时间")

    @field_validator("id")
    @classmethod
    def validate_id_prefix(cls, v: str) -> str:
        """ID 必须以 vocab_ 开头，与 storage 文件命名约定一致"""
        if not v.startswith("vocab_"):
            raise ValueError(f"vocab id 必须以 'vocab_' 开头，收到: {v}")
        return v


class Quiz(BaseModel):
    """考题模型

    quiz_type 限定为选择/填空/拼写/释义四种。
    options 默认 None（填空/拼写/释义题无选项），选择题填入 4 个选项。
    graded 标记是否已评分，grade_quiz 调用后置 True。
    """
    id: str = Field(description="考题唯一ID，格式 quiz_YYYYMMDD_NNN")
    vocab_id: str = Field(description="关联词汇ID")
    quiz_type: str = Field(description="题型：选择/填空/拼写/释义")
    question: str = Field(description="题干内容")
    options: list[str] | None = Field(default=None, description="选项列表，仅选择题填值")
    answer: str = Field(description="正确答案")
    generated_at: datetime = Field(description="生成时间")
    graded: bool = Field(default=False, description="是否已评分")
    individual_grade: int | None = Field(
        default=None,
        description="义项级评分 4/3/2/1，仅 zh_classical 释义题填充"
    )
    definition_index: int | None = Field(
        default=None,
        description="考查的义项索引（definitions 列表下标），单词义词为 0"
    )
    example_index: int | None = Field(
        default=None,
        description="考查的例句索引（definitions[i].examples 列表下标）"
    )

    @field_validator("quiz_type")
    @classmethod
    def validate_quiz_type(cls, v: str) -> str:
        """校验题型必须为预定义值"""
        if v not in VALID_QUIZ_TYPES:
            raise ValueError(f"quiz_type 必须是{VALID_QUIZ_TYPES}之一，收到: {v}")
        return v

    @field_validator("id")
    @classmethod
    def validate_id_prefix(cls, v: str) -> str:
        """ID 必须以 quiz_ 开头"""
        if not v.startswith("quiz_"):
            raise ValueError(f"quiz id 必须以 'quiz_' 开头，收到: {v}")
        return v


class ReviewRecord(BaseModel):
    """单次复习记录

    每次评分后写入一条，记录评分前后 EF 用于追溯难度变化。
    """
    record_id: str = Field(description="复习记录唯一ID")
    vocab_id: str = Field(description="关联词汇ID")
    review_time: datetime = Field(description="复习时间")
    grade: int = Field(description="评分 1-4（参考 SM-2：4 完全记住/3 勉强记住/2 部分错/1 几乎忘）")
    prev_ease: float = Field(description="评分前 EF")
    new_ease: float = Field(description="评分后 EF")
    definition_index: int | None = Field(
        default=None,
        description="本次复习考查的义项索引，透传自 Quiz"
    )
    example_index: int | None = Field(
        default=None,
        description="本次复习考查的例句索引，透传自 Quiz"
    )

    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: int) -> int:
        """校验 grade 必须在 0-5 范围内"""
        if not 0 <= v <= 5:
            raise ValueError(f"grade 必须在 0-5 之间，收到: {v}")
        return v


class ReviewSchedule(BaseModel):
    """复习计划项

    表示某词汇在某日的复习安排。status 由复习流程推进：
    待复习 → 已完成（评分后） / 已跳过（用户跳过）。
    quiz_id 关联本次复习所用考题，未生成考题时为 None。
    """
    vocab_id: str = Field(description="关联词汇ID")
    due_date: str = Field(description="到期日期 YYYY-MM-DD")
    status: str = Field(default="待复习", description="状态：待复习/已完成/已跳过")
    quiz_id: str | None = Field(default=None, description="关联考题ID，未生成为 None")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """校验状态必须为预定义值"""
        if v not in VALID_SCHEDULE_STATUS:
            raise ValueError(f"status 必须是{VALID_SCHEDULE_STATUS}之一，收到: {v}")
        return v
