# src/vocabcraft_mcp/tools/quiz.py
"""考题生成与评分 Tool

- generate_quiz: 根据词汇渲染命题 prompt（交宿主 LLM 执行），生成占位 Quiz 并持久化
- grade_quiz: 评分并按 SM-2 更新词汇记忆状态

设计决策（用户确认）: 工具只渲染 prompt，真实命题/主观评分交宿主 LLM 执行。
    - generate_quiz 返回 generate_prompt，宿主 LLM 据此输出题干/选项/答案，
      再调用 update_vocab 或重新 save_quiz 写回真实题目
    - grade_quiz 客观题（选择/填空/拼写）工具内精确匹配；
      释义题（主观）返回 grade_prompt 交宿主 LLM 评分，骨架阶段默认 grade=3
    - 评分四级制 4/3/2/1（4 完全记住 / 3 勉强记住 / 2 部分错 / 1 几乎忘），
      grade<3 视为失败、重置复习周期（与 SM-2 边界一致）
"""
import random

from vocabcraft_mcp.algorithms import compute_next_review
from vocabcraft_mcp.models import Quiz, ReviewRecord
from vocabcraft_mcp.prompts.quiz_generate_prompt import (
    CLASSICAL_GENERATE_PROMPT,
    GENERATE_PROMPT,
)
from vocabcraft_mcp.prompts.quiz_grade_prompt import GRADE_PROMPT
from vocabcraft_mcp.tools.crud import _now_utc, get_storage, update_vocab

# 客观题：工具内精确匹配评分；zh_classical 释义题按 "词性|释义" 客观评分；
# 其他释义题为主观题交 LLM。
# 四级评分制 4/3/2/1：客观题答对=4、答错=1；zh_classical 释义题见 _grade_definition
_OBJECTIVE_TYPES = {"选择", "填空", "拼写"}



# ──────────────────────────────────────────
# 词性解析与中英文映射（Web 层复用）
# ──────────────────────────────────────────

_POS_ZH_TO_EN = {
    "名词": "n.",
    "动词": "v.",
    "形容词": "adj.",
    "副词": "adv.",
    "代词": "pron.",
    "数词": "num.",
    "量词": "量",
    "连词": "连",
    "介词": "介",
    "助词": "助",
    "叹词": "叹",
}
_POS_EN_TO_ZH = {v: k for k, v in _POS_ZH_TO_EN.items()}


def zh_to_en_pos(zh: str) -> str:
    """中文词性（支持组合）转英文简写。无法识别的片段原样保留。"""
    parts = [p.strip() for p in zh.split("/") if p.strip()]
    mapped = [_POS_ZH_TO_EN.get(p, p) for p in parts]
    return "/".join(mapped)


def en_to_zh_pos(en: str) -> str:
    """英文简写（支持组合）转中文。无法识别的片段原样保留。"""
    parts = [p.strip() for p in en.split("/") if p.strip()]
    mapped = [_POS_EN_TO_ZH.get(p, p) for p in parts]
    return "/".join(mapped)


def _generate_quiz_id(storage) -> str:
    """生成 quiz_YYYYMMDD_NNN"""
    from vocabcraft_mcp.tools.crud import _generate_id
    return _generate_id("quiz", storage.list_all_quiz_ids())


def _generate_record_id(storage) -> str:
    """生成 rec_YYYYMMDD_NNN"""
    from vocabcraft_mcp.tools.crud import _generate_id
    return _generate_id("rec", [r.record_id for r in storage.list_all_review_records()])


_CLASSICAL_POS_POOL = ["n.", "v.", "adj.", "adv.", "pron.", "num.", "量", "连", "介", "助", "叹"]

# 义项文本中的 【词性】 前缀模式
_POS_PREFIX_RE = __import__("re").compile(r"^[【\[](.*?)[】\]]\s*")


def strip_pos_prefix(text: str) -> str:
    """去除义项文本开头的 【词性】 前缀

    '【动词】放逐,流放' → '放逐,流放'
    '放逐,流放' → '放逐,流放'  (无前缀不变)
    """
    return _POS_PREFIX_RE.sub("", text)


def extract_pos_from_text(text: str) -> str:
    """从义项文本提取 【词性】 前缀中的词性

    '【动词】放逐,流放' → '动词'
    '【副词】曾经' → '副词'
    '放逐,流放' → ''  (无前缀返回空串)
    """
    m = _POS_PREFIX_RE.match(text)
    return m.group(1) if m else ""

# ──────────────────────────────────────────
# 义项级评分（fuzzy matching）
# ──────────────────────────────────────────

# 组合词性分隔符
_POS_SEP_RE = __import__("re").compile(r"[/、,，]")


def _normalize_pos(pos_str: str) -> set[str]:
    """将词性字符串标准化为英文简写集合

    "v./adj." → {"v.", "adj."}
    "动词/使动" → {"v."}  (忽略使动/意动等修饰)
    """
    parts = _POS_SEP_RE.split(pos_str.strip().lower())
    result: set[str] = set()
    modifiers = {"使动", "意动", "为动", "被动", "主动", "及物", "不及物"}
    for p in parts:
        p = p.strip()
        if not p:
            continue
        en = _POS_ZH_TO_EN.get(p, p)
        # 去除修饰前缀
        for prefix in modifiers:
            if en.startswith(prefix):
                en = en[len(prefix):]
                break
        en = en.strip()
        if en:
            result.add(en)
    return result


def _match_pos(expected: str, actual: str) -> bool:
    """词性模糊匹配：集合相等即匹配"""
    return _normalize_pos(expected) == _normalize_pos(actual)


# 释义分隔符
_MEANING_SEP_RE = __import__("re").compile(r"[，、；;,]")


def _normalize_meaning(meaning: str) -> set[str]:
    """将释义拆分为义素集合"""
    parts = _MEANING_SEP_RE.split(meaning.strip())
    return {p.strip().strip("也矣乎哉之").strip() for p in parts if p.strip()}


def _match_meaning(expected: str, actual: str) -> bool:
    """释义模糊匹配

    规则：
    - 多义项（含分隔符如 '放逐，流放'）：任一义素匹配即可
    - 单义项（如 '兵器也'）：义素去虚词后严格子串匹配
    - 双向子串：义素⊂答案 或 答案⊂义素
    - 空白归一化：义素内空格（。后空格等）不影响匹配
    """
    raw_parts = _MEANING_SEP_RE.split(expected.strip())
    # 去除文言虚词后缀，统一比较基准
    _particles = "也矣乎哉之者"
    parts = [p.strip().strip(_particles).strip() for p in raw_parts if p.strip()]
    actual_text = actual.strip()
    if not parts or not actual_text:
        return False

    # ponytail: 移除所有空格以容忍标点后的格式差异（如 '。' vs '。 '）
    def _no_ws(s: str) -> str:
        return s.replace(" ", "")

    actual_clean = _no_ws(actual_text)

    if len(parts) > 1:
        # 多义项：任一义素匹配即可（双向子串，但反向匹配要求答案>=2字且>=义素一半长度）
        return any(
            _no_ws(ep) in actual_clean
            or (
                actual_clean in _no_ws(ep)
                and len(actual_clean) >= 2
                and len(actual_clean) >= len(_no_ws(ep)) // 2
            )
            for ep in parts
        )
    else:
        # 单义项：严格匹配（义素是答案的子串，或答案是义素的子串）
        # 但不允许太短的匹配（如 '草' 匹配 '草本植物名'）
        ep_clean = _no_ws(parts[0])
        if ep_clean in actual_clean:
            return True
        return actual_clean in ep_clean and len(actual_clean) >= len(ep_clean) // 2


def _grade_definition(expected_answer: str, user_response: str) -> int:
    """义项级评分：按词性和释义两个维度分别匹配（四级制 4/3/2/1）

    Returns:
        4: 词性+释义都对（完全记住）
        3: 词性对但释义错（勉强记住）
        2: 词性错但释义对（部分错）
        1: 都错（几乎忘）
    """
    exp_pos, _, exp_meaning = expected_answer.partition("|")
    act_pos, _, act_meaning = user_response.partition("|")

    pos_ok = _match_pos(exp_pos, act_pos)
    meaning_ok = _match_meaning(exp_meaning, act_meaning)

    if pos_ok and meaning_ok:
        return 4
    if pos_ok:
        return 3
    if meaning_ok:
        return 2
    return 1


def _composite_word_grade(definition_grades: list[int]) -> int:
    """从义项级 grade 列表计算词级综合 grade

    公式: round(avg * 0.8 + min * 0.2)
    - avg 反映整体掌握度（权重 80%）
    - min 捕捉最薄弱义项（权重 20%，避免单个低分拖垮全词）
    """
    if not definition_grades:
        return 0
    min_g = min(definition_grades)
    avg_g = sum(definition_grades) / len(definition_grades)
    return round(avg_g * 0.8 + min_g * 0.2)


def generate_quiz(vocab_id: str, quiz_type: str = "") -> dict:
    """为指定词汇生成考题

    渲染 GENERATE_PROMPT 交宿主 LLM 命题，同时生成占位 Quiz 持久化
    （question/answer 为占位值，宿主 LLM 输出后可回写）。

    Args:
        vocab_id: 词汇 ID
        quiz_type: 题型 选择/填空/拼写/释义，空串则默认"拼写"

    Returns:
        包含 quiz_id/quiz/generate_prompt 的字典；词汇不存在返回 error
    """
    storage = get_storage()
    v = storage.load_vocab(vocab_id)
    if v is None:
        return {"error": f"词汇不存在: {vocab_id}"}

    # 题型：用户提供 or 按语言默认
    # ponytail: 中文/文言文默认"释义"（汉字无"拼写"概念），英语/德语默认"拼写"
    qtype = quiz_type or ("释义" if v.structured.language.startswith("zh") else "拼写")

    # zh_classical 释义题：遍历所有义项的所有例句，每条例句生成独立 quiz
    # 确保每个义项的所有例句都被考查到，避免只考一个义项的部分例句
    defs = v.structured.definitions
    if qtype == "释义" and v.structured.language == "zh_classical":
        if not defs:
            return {"error": "词汇无释义，无法生成考题"}
        quizzes = []
        for di, d in enumerate(defs):
            pos = d.part_of_speech or v.structured.part_of_speech.strip()
            pos = zh_to_en_pos(pos) if pos else "?"
            meaning = strip_pos_prefix(d.text)
            answer = f"{pos}|{meaning}"
            if d.examples:
                for ex_idx, example in enumerate(d.examples):
                    defs_block = f"1. {meaning}\n   - {example}"
                    prompt = CLASSICAL_GENERATE_PROMPT.format(
                        word=v.structured.word,
                        part_of_speech=v.structured.part_of_speech,
                        definitions_block=defs_block,
                    )
                    quiz = Quiz(
                        id=_generate_quiz_id(storage),
                        vocab_id=vocab_id,
                        quiz_type=qtype,
                        question="（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
                        answer=answer,
                        generated_at=_now_utc(),
                        definition_index=di,
                        example_index=ex_idx,
                    )
                    storage.save_quiz(quiz)
                    quizzes.append({"quiz_id": quiz.id, "quiz": quiz.model_dump(), "generate_prompt": prompt})
            else:
                # 无例句的义项也考释义
                defs_block = f"1. {meaning}\n   （无例句）"
                prompt = CLASSICAL_GENERATE_PROMPT.format(
                    word=v.structured.word,
                    part_of_speech=v.structured.part_of_speech,
                    definitions_block=defs_block,
                )
                quiz = Quiz(
                    id=_generate_quiz_id(storage),
                    vocab_id=vocab_id,
                    quiz_type=qtype,
                    question="（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
                    answer=answer,
                    generated_at=_now_utc(),
                    definition_index=di,
                    example_index=None,
                )
                storage.save_quiz(quiz)
                quizzes.append({"quiz_id": quiz.id, "quiz": quiz.model_dump(), "generate_prompt": prompt})
        return {"quizzes": quizzes}

    # 非 zh_classical：选一个义项，单个 quiz
    if defs:
        definition_index = random.randrange(len(defs)) if len(defs) > 1 else 0  # noqa: B311  # 仅出题采样义项，非安全用途
        selected = defs[definition_index]
        defs_block = f"1. {selected.text}" + "".join(f"\n   - {e}" for e in selected.examples)
    else:
        definition_index = None
        defs_block = "（无）"

    # 非 zh_classical：单 quiz 返回
    prompt = GENERATE_PROMPT.format(
        word=v.structured.word,
        phonetic=v.structured.phonetic,
        definitions_block=defs_block,
        quiz_type=qtype,
        language=v.structured.language,
    )

    if qtype == "拼写":
        answer = v.structured.word
    else:
        answer = defs[definition_index].text if defs and definition_index is not None else ""
    quiz = Quiz(
        id=_generate_quiz_id(storage),
        vocab_id=vocab_id,
        quiz_type=qtype,
        question="（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
        answer=answer,
        generated_at=_now_utc(),
        definition_index=definition_index,
    )
    storage.save_quiz(quiz)

    return {
        "quiz_id": quiz.id,
        "quiz": quiz.model_dump(),
        "generate_prompt": prompt,
        "message": "请使用 generate_prompt 调用 LLM 生成题干，结果可回写 quizzes/" + quiz.id + ".json",
    }


def grade_quiz(quiz_id: str, response: str) -> dict:
    """评分并按 SM-2 更新词汇记忆状态

    评分分两层：
    1. 义项级（individual_grade）：每道题独立评分
       - zh_classical 释义题: 按词性+释义两个维度 fuzzy matching → 4/3/2/1
       - 客观题（选择/填空/拼写）: 精确匹配 → 4/1
       - 其他释义题（主观）: 交宿主 LLM，骨架阶段默认 3
    2. 词级（word_grade）：该词所有 quiz 评完后聚合
       - 公式: round((min + avg) / 2)
       - 只在所有 quiz 评完后才更新 SM-2

    Args:
        quiz_id: 考题 ID
        response: 用户作答文本

    Returns:
        单题评分阶段: {quiz_id, individual_grade, remaining}
        词级聚合阶段: {quiz_id, word_grade, details, sm2_updated, ...}
        考题不存在: {error}
    """
    storage = get_storage()
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        return {"error": f"考题不存在: {quiz_id}"}

    vocab = storage.load_vocab(quiz.vocab_id)
    if vocab is None:
        return {"error": f"关联词汇不存在: {quiz.vocab_id}"}

    result: dict = {"quiz_id": quiz_id, "vocab_id": quiz.vocab_id}

    # ── 1. 计算义项级 grade ──
    if quiz.quiz_type in _OBJECTIVE_TYPES:
        correct = response.strip().lower() == quiz.answer.strip().lower()
        individual_grade = 4 if correct else 1
        result["correct"] = correct
    elif quiz.quiz_type == "释义" and vocab.structured.language == "zh_classical":
        individual_grade = _grade_definition(quiz.answer, response)
        result["correct"] = individual_grade == 4
    else:
        result["grade_prompt"] = GRADE_PROMPT.format(
            question=quiz.question,
            reference_answer=quiz.answer,
            user_answer=response,
        )
        result["correct"] = None
        individual_grade = 3  # ponytail: 骨架默认值

    result["individual_grade"] = individual_grade

    # ── 2. 保存当前 quiz 的评分结果 ──
    storage.save_quiz(quiz.model_copy(update={
        "graded": True,
        "individual_grade": individual_grade,
    }))

    # ── 3. 检查该词所有 quiz 是否全部评完 ──
    # 只把同一批次（生成时间差≤60s）的 quiz 纳入判定，多次出题不互相污染
    today_str = _now_utc().date().isoformat()
    all_quiz_ids = storage.list_all_quiz_ids()
    vocab_quizzes: list[Quiz] = []
    for qid in all_quiz_ids:
        q = storage.load_quiz(qid)
        if q is not None and q.vocab_id == quiz.vocab_id:
            gen_date = q.generated_at.date().isoformat() if q.generated_at else ""
            if gen_date >= today_str:
                # 同批次判定：生成时间差 ≤ 60s
                has_both = q.generated_at is not None and quiz.generated_at is not None
                time_diff = (
                    abs((q.generated_at - quiz.generated_at).total_seconds())
                    if has_both
                    else 999
                )
                if time_diff <= 60:
                    vocab_quizzes.append(q)
    ungraded = [q for q in vocab_quizzes if not q.graded]
    graded = [q for q in vocab_quizzes if q.graded]

    if ungraded:
        result["remaining"] = len(ungraded)
        result["message"] = f"还有 {len(ungraded)} 道题未答"
        return result

    # ── 4. 全部评完 → 计算词级综合 grade ──
    definition_grades = [q.individual_grade for q in graded if q.individual_grade is not None]
    word_grade = _composite_word_grade(definition_grades)

    result["word_grade"] = word_grade
    result["details"] = [
        {"quiz_id": q.id, "definition_index": q.definition_index,
         "example_index": q.example_index, "grade": q.individual_grade}
        for q in graded
    ]

    # ── 5. SM-2 更新（每词只调一次） ──
    rs = vocab.review_state
    prev_ease = rs.ease_factor
    new_state = compute_next_review(prev_ease, rs.interval, rs.repetitions, word_grade)

    update_result = update_vocab({
        "id": quiz.vocab_id,
        "review_state": {
            "ease_factor": new_state["ease_factor"],
            "interval": new_state["interval"],
            "repetitions": new_state["repetitions"],
            "next_review": new_state["next_review_date"],
            "last_review": _now_utc().date().isoformat(),
            "last_word_grade": word_grade,
        },
    })
    if "error" in update_result:
        result["error"] = update_result["error"]
        return result

    record = ReviewRecord(
        record_id=_generate_record_id(storage),
        vocab_id=quiz.vocab_id,
        review_time=_now_utc(),
        grade=word_grade,
        prev_ease=prev_ease,
        new_ease=new_state["ease_factor"],
        definition_index=None,
        example_index=None,
    )
    storage.save_review_record(record)

    result["grade"] = word_grade
    result["updated_review_state"] = new_state
    result["review_record_id"] = record.record_id
    result["remaining"] = 0
    return result
