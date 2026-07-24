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
from datetime import datetime, timezone

from vocabcraft_mcp.models import Quiz, ReviewRecord
from vocabcraft_mcp.algorithms import compute_next_review
from vocabcraft_mcp.prompts.quiz_generate_prompt import GENERATE_PROMPT
from vocabcraft_mcp.prompts.quiz_grade_prompt import GRADE_PROMPT
from vocabcraft_mcp.tools.crud import get_storage, update_vocab, _now_utc

# 客观题：工具内精确匹配评分；释义题为主观题交 LLM
_OBJECTIVE_TYPES = {"选择", "填空", "拼写"}


def _generate_quiz_id(storage) -> str:
    """生成 quiz_YYYYMMDD_NNN，基于当天已有考题数 +1"""
    today = _now_utc().strftime("%Y%m%d")
    prefix = f"quiz_{today}_"
    existing = [qid for qid in storage.list_all_quiz_ids() if qid.startswith(prefix)]
    return f"{prefix}{len(existing) + 1:03d}"


def _generate_record_id(storage) -> str:
    """生成 rec_YYYYMMDD_NNN，基于当天已有复习记录数 +1"""
    today = _now_utc().strftime("%Y%m%d")
    prefix = f"rec_{today}_"
    existing = [r.record_id for r in storage.list_all_review_records() if r.record_id.startswith(prefix)]
    return f"{prefix}{len(existing) + 1:03d}"


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
    # definitions_block 按义项分组展示释义与关联例句
    defs = v.structured.definitions
    if defs:
        defs_block = "\n".join(
            f"{i + 1}. {d.text}" + "".join(f"\n   - {e}" for e in d.examples)
            for i, d in enumerate(defs)
        )
    else:
        defs_block = "（无）"
    prompt = GENERATE_PROMPT.format(
        word=v.structured.word,
        phonetic=v.structured.phonetic,
        definitions_block=defs_block,
        quiz_type=qtype,
        language=v.structured.language,
    )

    # 占位 Quiz：answer 取词形（拼写题）或首条释义文本，宿主 LLM 输出后可回写
    answer = v.structured.word if qtype == "拼写" else (defs[0].text if defs else "")
    quiz = Quiz(
        id=_generate_quiz_id(storage),
        vocab_id=vocab_id,
        quiz_type=qtype,
        question=f"（占位题干，请用 generate_prompt 调用 LLM 生成真实题干）",
        answer=answer,
        generated_at=_now_utc(),
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
    释义题（主观）: 返回 grade_prompt 交宿主 LLM 评分，骨架阶段默认 grade=3 推进 SM-2

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
        释义题额外返回 grade_prompt；考题不存在返回 error
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

    # 评分：客观题精确匹配，释义题交 LLM
    if quiz.quiz_type in _OBJECTIVE_TYPES:
        correct = response.strip().lower() == quiz.answer.strip().lower()
        grade = 5 if correct else 0
        result["correct"] = correct
    else:
        # 释义题主观题：渲染 grade_prompt 交宿主 LLM，骨架阶段用 grade=3 推进
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

    # 写复习记录（评分前后 EF）
    record = ReviewRecord(
        record_id=_generate_record_id(storage),
        vocab_id=quiz.vocab_id,
        review_time=_now_utc(),
        grade=grade,
        prev_ease=prev_ease,
        new_ease=new_state["ease_factor"],
    )
    storage.save_review_record(record)

    # 标记考题已评分
    storage.save_quiz(quiz.model_copy(update={"graded": True}))

    result["grade"] = grade
    result["updated_review_state"] = new_state
    result["review_record_id"] = record.record_id
    return result
