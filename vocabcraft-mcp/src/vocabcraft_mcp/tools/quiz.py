# src/vocabcraft_mcp/tools/quiz.py
"""考题生成与评分 Tool

- generate_quiz: 根据词汇渲染命题 prompt（交宿主 LLM 执行），生成占位 Quiz 并持久化
- grade_quiz: 评分并按 SM-2 更新词汇记忆状态

设计决策（用户确认）: 工具只渲染 prompt，真实命题/主观评分交宿主 LLM 执行。
    - generate_quiz 返回 generate_prompt，宿主 LLM 据此输出题干/选项/答案，
      再调用 update_vocab 或重新 save_quiz 写回真实题目
    - grade_quiz 客观题（选择/填空/拼写）工具内精确匹配；
      释义题（主观）返回 grade_prompt 交宿主 LLM 评分，骨架阶段默认 grade=3
"""
import random

from vocabcraft_mcp.models import Definition, Quiz, ReviewRecord
from vocabcraft_mcp.algorithms import compute_next_review
from vocabcraft_mcp.prompts.quiz_generate_prompt import CLASSICAL_GENERATE_PROMPT, GENERATE_PROMPT
from vocabcraft_mcp.prompts.quiz_grade_prompt import GRADE_PROMPT
from vocabcraft_mcp.tools.crud import get_storage, update_vocab, _now_utc

# 客观题：工具内精确匹配评分；zh_classical 释义题按 "词性|释义" 客观评分；
# 其他释义题为主观题交 LLM
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


def _least_reviewed_definition_index(vocab_id: str, defs: list[Definition], storage) -> int:
    """返回复习次数最少的义项下标；次数相同按下标升序取第一个。

    统计粒度为 (definition_index, example_index) 对，
    按义项聚合后选择总复习次数最少的义项。
    """
    counts: dict[tuple[int, int], int] = {}
    for i, d in enumerate(defs):
        for j in range(len(d.examples)):
            counts[(i, j)] = 0
    if not counts:
        return 0

    for r in storage.list_all_review_records():
        if r.vocab_id == vocab_id and r.definition_index is not None:
            key = (r.definition_index, r.example_index or 0)
            if key in counts:
                counts[key] += 1

    def_counts: dict[int, int] = {i: 0 for i in range(len(defs))}
    for (di, _ei), c in counts.items():
        def_counts[di] = def_counts.get(di, 0) + c

    return min(def_counts, key=lambda i: (def_counts[i], i))


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
    if quiz_type:
        qtype = quiz_type
    else:
        qtype = "释义" if v.structured.language.startswith("zh") else "拼写"

    # 渲染命题 prompt 交宿主 LLM（含语言上下文，命题语言与词汇匹配）
    # ponytail: 多义词随机选一个义项考查并记录 definition_index，
    #           为 Phase 2 义项级掌握度可视化采集数据；
    #           zh_classical 释义题改为按复习次数轮询，保证义项覆盖。
    defs = v.structured.definitions
    if defs:
        if qtype == "释义" and v.structured.language == "zh_classical":
            definition_index = _least_reviewed_definition_index(vocab_id, defs, storage)
        elif len(defs) > 1:
            definition_index = random.randrange(len(defs))
        else:
            definition_index = 0
        selected = defs[definition_index]
        defs_block = f"1. {selected.text}" + "".join(f"\n   - {e}" for e in selected.examples)
    else:
        definition_index = None
        defs_block = "（无）"
    # zh_classical 释义题：为每个例句生成独立 quiz
    if qtype == "释义" and v.structured.language == "zh_classical":
        quizzes = []
        if defs and definition_index is not None:
            selected = defs[definition_index]
            pos = selected.part_of_speech or v.structured.part_of_speech.strip()
            pos = zh_to_en_pos(pos) if pos else "?"
            answer = f"{pos}|{selected.text}"
        else:
            selected = None
            answer = "?|"

        if selected and selected.examples:
            for ex_idx, example in enumerate(selected.examples):
                defs_block = f"1. {selected.text}\n   - {example}"
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
                    definition_index=definition_index,
                    example_index=ex_idx,
                )
                storage.save_quiz(quiz)
                quizzes.append({"quiz_id": quiz.id, "quiz": quiz.model_dump(), "generate_prompt": prompt})
        else:
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
                definition_index=definition_index,
                example_index=None,
            )
            storage.save_quiz(quiz)
            quizzes.append({"quiz_id": quiz.id, "quiz": quiz.model_dump(), "generate_prompt": prompt})

        return {"quizzes": quizzes}

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
        answer = defs[definition_index].text if defs else ""
    quiz = Quiz(
        id=_generate_quiz_id(storage),
        vocab_id=vocab_id,
        quiz_type=qtype,
        question=f"（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
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

    客观题（选择/填空/拼写）: 精确匹配（忽略大小写与空白），答对 grade=5/答错 grade=0
    zh_classical 释义题: 按 "词性|释义" 客观精确评分，词性大小写不敏感，释义严格一致
    其他释义题（主观）: 返回 grade_prompt 交宿主 LLM 评分，骨架阶段默认 grade=3 推进 SM-2

    评分后:
        1. 调用 compute_next_review 计算新记忆状态
        2. update_vocab 回写 review_state
        3. 写入 ReviewRecord 记录评分前后 EF
        4. 标记 quiz.graded=True

    Args:
        quiz_id: 考题 ID
        response: 用户作答文本

    Returns:
        包含 grade/correct/updated_review_state 的字典；
        主观释义题额外返回 grade_prompt；考题不存在返回 error
    """
    storage = get_storage()
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        return {"error": f"考题不存在: {quiz_id}"}

    vocab = storage.load_vocab(quiz.vocab_id)
    if vocab is None:
        return {"error": f"关联词汇不存在: {quiz.vocab_id}"}

    rs = vocab.review_state
    result: dict = {"quiz_id": quiz_id, "vocab_id": quiz.vocab_id}

    # 评分：客观题精确匹配；zh_classical 释义题按 "词性|释义" 客观评分；其他释义题交 LLM
    if quiz.quiz_type in _OBJECTIVE_TYPES:
        correct = response.strip().lower() == quiz.answer.strip().lower()
        grade = 5 if correct else 0
        result["correct"] = correct
    elif quiz.quiz_type == "释义" and vocab.structured.language == "zh_classical":
        expected_pos, _, expected_meaning = quiz.answer.partition("|")
        actual_pos, _, actual_meaning = response.partition("|")
        expected_pos = zh_to_en_pos(expected_pos.strip().lower())
        actual_pos = zh_to_en_pos(actual_pos.strip().lower())
        correct = expected_pos == actual_pos and expected_meaning.strip() == actual_meaning.strip()
        grade = 5 if correct else 0
        result["correct"] = correct
    else:
        # 其他释义题主观题：渲染 grade_prompt 交宿主 LLM，骨架阶段用 grade=3 推进
        result["grade_prompt"] = GRADE_PROMPT.format(
            question=quiz.question,
            reference_answer=quiz.answer,
            user_answer=response,
        )
        result["correct"] = None  # 主观题正误交 LLM 判定
        grade = 3  # ponytail: 骨架默认值，宿主 LLM 评分后可调 update_vocab 修正

    # SM-2 更新记忆状态
    prev_ease = rs.ease_factor
    new_state = compute_next_review(prev_ease, rs.interval, rs.repetitions, grade)

    # 回写 review_state（patch 语义，不动 structured）
    update_result = update_vocab({
        "id": quiz.vocab_id,
        "review_state": {
            "ease_factor": new_state["ease_factor"],
            "interval": new_state["interval"],
            "repetitions": new_state["repetitions"],
            "next_review": new_state["next_review_date"],
            "last_review": _now_utc().date().isoformat(),
        },
    })
    if "error" in update_result:
        return {**result, "error": update_result["error"], "grade": grade}

    # 写复习记录（评分前后 EF；透传 definition_index 为 Phase 2 采集数据）
    record = ReviewRecord(
        record_id=_generate_record_id(storage),
        vocab_id=quiz.vocab_id,
        review_time=_now_utc(),
        grade=grade,
        prev_ease=prev_ease,
        new_ease=new_state["ease_factor"],
        definition_index=quiz.definition_index,
    )
    storage.save_review_record(record)

    # 标记考题已评分
    storage.save_quiz(quiz.model_copy(update={"graded": True}))

    result["grade"] = grade
    result["updated_review_state"] = new_state
    result["review_record_id"] = record.record_id
    return result
