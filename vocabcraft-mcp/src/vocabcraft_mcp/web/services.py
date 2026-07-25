# src/vocabcraft_mcp/web/services.py
"""Web 服务层 — 编排 storage / statistics / review / quiz

作为路由层和数据层之间的薄编排层，不复制数据访问逻辑。
所有读写都通过 storage / statistics / review / quiz 完成。
"""
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from random import sample
from typing import Optional
from uuid import uuid4

from vocabcraft_mcp.algorithms import _INITIAL_INTERVALS_DAYS
from vocabcraft_mcp.models import Quiz, ReviewRecord, VocabRecord
from vocabcraft_mcp.storage import Storage
from vocabcraft_mcp.tools.crud import get_storage as _default_get_storage
from vocabcraft_mcp.tools.quiz import generate_quiz as _generate_quiz_tool, grade_quiz as _grade_quiz_tool
from vocabcraft_mcp.tools.statistics import _mastery_level, get_statistics


def _get_storage() -> Storage:
    """获取 Storage 实例（可被测试 monkeypatch 覆盖）"""
    return _default_get_storage()


def _today_utc_iso() -> str:
    """当前 UTC 日期 YYYY-MM-DD"""
    return datetime.now(timezone.utc).date().isoformat()


# ──────────────────────────────────────────
# Dashboard 概览
# ──────────────────────────────────────────

def get_dashboard_summary() -> dict:
    """获取 Dashboard 概览数据

    返回：KPI 指标 + 语言分布 + 掌握度分布 + 30天创建趋势
    """
    storage = _get_storage()
    vocabs = storage.get_all_vocabs_for_statistics()

    today = _today_utc_iso()
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()

    # KPI 指标
    total = len(vocabs)
    today_pending = sum(
        1 for v in vocabs
        if v.review_state.next_review and v.review_state.next_review <= today
    )
    week_new = sum(
        1 for v in vocabs
        if v.created_at.date().isoformat() >= week_ago
    )
    mastered = sum(
        1 for v in vocabs
        if _mastery_level(v.review_state.repetitions) == "掌握"
    )

    # 语言分布
    language_counter = Counter(v.structured.language for v in vocabs)

    # 掌握度分布
    mastery_counter = Counter(_mastery_level(v.review_state.repetitions) for v in vocabs)
    # 固定顺序，保证图表颜色稳定
    mastery_order = ["新词", "生疏", "熟悉", "掌握"]

    # 30天创建趋势
    trend_counter = Counter(v.created_at.date().isoformat() for v in vocabs)
    trends = {}
    for i in range(30):
        day = (datetime.now(timezone.utc) - timedelta(days=29 - i)).date().isoformat()
        trends[day] = trend_counter.get(day, 0)

    return {
        "total": total,
        "today_pending": today_pending,
        "week_new": week_new,
        "mastered": mastered,
        "language_distribution": [
            {"name": k, "value": v} for k, v in language_counter.most_common()
        ],
        "mastery_distribution": [
            {"name": level, "value": mastery_counter.get(level, 0)}
            for level in mastery_order
        ],
        "trends": trends,
    }


# ──────────────────────────────────────────
# 多维统计（统计图表页）
# ──────────────────────────────────────────

def get_multi_dim_stats() -> dict:
    """获取多维度统计数据

    返回：语言分布、掌握度分布、题型分布、30天创建趋势
    """
    language_stats = get_statistics("language")
    mastery_stats = get_statistics("mastery")
    quiz_type_stats = get_statistics("quiz_type")

    return {
        "language_distribution": language_stats.get("items", []),
        "mastery_distribution": [
            {"name": item["key"], "value": item["count"]}
            for item in mastery_stats.get("items", [])
        ],
        "quiz_type_distribution": [
            {"name": item["key"], "value": item["count"]}
            for item in quiz_type_stats.get("items", [])
        ],
        "trend_data": language_stats.get("trends", []),
        "total": language_stats.get("total", 0),
    }


def get_stats_by_dimension(group_by: str) -> dict:
    """按维度获取统计（复用 statistics.get_statistics）"""
    return get_statistics(group_by=group_by)


# ──────────────────────────────────────────
# 待复习列表
# ──────────────────────────────────────────

def get_upcoming_reviews() -> list[dict]:
    """获取待复习词汇列表

    返回已到期（next_review <= 今天）的词汇列表，按到期日升序排列。
    """
    storage = _get_storage()
    today = _today_utc_iso()

    upcoming = []
    for v in storage.get_all_vocabs_for_statistics():
        due_date = v.review_state.next_review
        if not due_date or due_date > today:
            continue
        upcoming.append({
            "vocab_id": v.id,
            "word": v.structured.word,
            "language": v.structured.language,
            "due_date": due_date,
            "repetitions": v.review_state.repetitions,
            "is_overdue": due_date < today,
        })

    upcoming.sort(key=lambda x: x["due_date"])
    return upcoming


# ──────────────────────────────────────────
# 复习日历
# ──────────────────────────────────────────

def get_review_calendar() -> dict:
    """获取当前月复习日历数据

    返回：当前年月标题、每日复习任务数、是否今天。
    """
    storage = _get_storage()
    today = datetime.now(timezone.utc)
    month_start = today.replace(day=1)
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    month_days = (next_month - month_start).days

    # 统计当月每天需要复习的词汇数
    review_calendar: dict[str, int] = {}
    for v in storage.get_all_vocabs_for_statistics():
        due_date = v.review_state.next_review
        if not due_date:
            continue
        if due_date.startswith(today.strftime("%Y-%m")):
            review_calendar[due_date] = review_calendar.get(due_date, 0) + 1

    calendar_days = []
    for day in range(1, month_days + 1):
        date_str = month_start.replace(day=day).date().isoformat()
        calendar_days.append({
            "day": day,
            "date": date_str,
            "count": review_calendar.get(date_str, 0),
            "is_today": date_str == today.date().isoformat(),
        })

    return {
        "calendar_days": calendar_days,
        "current_month": today.strftime("%Y年%m月"),
    }


# ──────────────────────────────────────────
# 语言/学科复习完成率
# ──────────────────────────────────────────

def get_language_progress() -> list[dict]:
    """按语言统计复习进度

    进度 = 至少复习过 1 次的词汇数 / 该语言总词汇数
    """
    storage = _get_storage()
    lang_stats: dict[str, dict] = {}
    for v in storage.get_all_vocabs_for_statistics():
        lang = v.structured.language
        if lang not in lang_stats:
            lang_stats[lang] = {"total": 0, "reviewed": 0}
        lang_stats[lang]["total"] += 1
        if v.review_state.repetitions > 0:
            lang_stats[lang]["reviewed"] += 1

    return [
        {
            "language": lang,
            "total": d["total"],
            "reviewed": d["reviewed"],
            "rate": int(d["reviewed"] / d["total"] * 100) if d["total"] > 0 else 0,
        }
        for lang, d in sorted(lang_stats.items())
    ]


# ──────────────────────────────────────────
# 遗忘曲线数据
# ──────────────────────────────────────────

def get_forgetting_curve() -> list[dict]:
    """获取简化遗忘曲线数据

    基于初始复习间隔节点，展示理论保留率变化。
    ponytail: 简化模型，非真实艾宾浩斯公式，仅用于可视化参考。
    """
    curve = []
    for i, interval in enumerate(_INITIAL_INTERVALS_DAYS):
        # 简化保留率：随复习次数递增，第一次后约 60%，之后逐步提升
        retention = max(35, 100 - (i + 1) * 12)
        curve.append({"review": i, "interval": interval, "retention": retention})
    return curve


# ──────────────────────────────────────────
# 出题（Web 层自包含，不依赖外部 LLM）
# ──────────────────────────────────────────

_MAX_DISTRACTORS = 3


def _pick_distractors(correct_vocab: VocabRecord, count: int = _MAX_DISTRACTORS) -> list[str]:
    """从其他词汇中挑选干扰项

    优先挑选与目标词汇相同语言的其他词形。
    数量不足时用占位符补齐。
    """
    storage = _get_storage()
    candidates = [
        v.structured.word
        for v in storage.get_all_vocabs_for_statistics()
        if v.id != correct_vocab.id and v.structured.language == correct_vocab.structured.language
    ]
    if len(candidates) >= count:
        return sample(candidates, count)
    # 不足时返回全部候选 + 占位符
    return candidates + [f"选项{i + 1}" for i in range(count - len(candidates))]


def generate_web_quiz(vocab_id: str, quiz_type: str = "") -> Optional[dict]:
    """生成可在 Web 上直接作答的考题

    复用 tools.generate_quiz 创建 quiz 记录，再由 Web 层填充真实题干/选项/答案。
    不依赖外部 LLM，适合本地自包含使用。

    Returns:
        {"quiz_id": str, "quiz": dict}；词汇不存在返回 None
    """
    storage = _get_storage()
    vocab = storage.load_vocab(vocab_id)
    if vocab is None:
        return None

    # 复用工具创建 quiz 记录（含 ID、时间戳、占位内容）
    result = _generate_quiz_tool(vocab_id, quiz_type)
    if "error" in result:
        return None

    quiz_id = result["quiz_id"]
    quiz = storage.load_quiz(quiz_id)
    if quiz is None:
        return None

    qtype = quiz.quiz_type
    word = vocab.structured.word
    defs = vocab.structured.definitions
    # 例句已内嵌到各释义的 examples，按义项顺序收集所有例句
    all_examples = [e for d in defs for e in d.examples]
    # 首条释义文本（多处置答/展示用）
    first_def_text = defs[0].text if defs else ""

    # 根据题型生成题干与答案
    if qtype == "选择":
        prompt = f"请选择释义为「{first_def_text or word}」的单词"
        answer = word
        options = [word] + _pick_distractors(vocab)
    elif qtype == "填空":
        if all_examples:
            sentence = all_examples[0]
            # 简单替换：将词形替换为下划线空白
            question = sentence.replace(word, "______")
        elif defs:
            question = f"请根据释义「{first_def_text}」填写单词"
        else:
            question = f"请填写单词（词性：{vocab.structured.part_of_speech}）"
        prompt = question
        answer = word
        options = None
    elif qtype == "拼写":
        prompt = f"释义：{first_def_text if defs else '（请根据例句拼写）'}"
        answer = word
        options = None
    else:  # 释义
        prompt = f"请写出单词「{word}」的释义"
        answer = first_def_text if defs else word
        options = None

    updated_quiz = quiz.model_copy(update={
        "question": prompt,
        "answer": answer,
        "options": options,
    })
    storage.save_quiz(updated_quiz)

    return {"quiz_id": quiz_id, "quiz": updated_quiz.model_dump()}


def grade_web_quiz(quiz_id: str, response: str) -> dict:
    """评分并返回结果

    复用 tools.grade_quiz，返回格式化的结果字典。
    """
    return _grade_quiz_tool(quiz_id, response)


# ──────────────────────────────────────────
# 批量复习（今日到期词汇连续出题）
# ──────────────────────────────────────────

@dataclass
class _BatchReviewSession:
    """批量复习会话状态

    ponytail: 使用内存字典存储，单用户本地场景足够；
    服务器重启后 session 丢失，但已评分的 quiz/review_state 已持久化。
    """
    batch_id: str
    quiz_ids: list[str]
    graded: dict[int, dict] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# 批量复习会话缓存：batch_id -> _BatchReviewSession
# ponytail: 无 TTL 清理，本地使用且数据量小，长期运行可能累积；
# 如需升级可改为按创建时间淘汰的 LRU。
_batch_sessions: dict[str, _BatchReviewSession] = {}


def start_batch_review() -> Optional[dict]:
    """为今日到期词汇创建批量复习会话

    Returns:
        {"batch_id": str, "total": int}；无到期词汇返回 None
    """
    from vocabcraft_mcp.tools.review import schedule_review

    schedule = schedule_review()
    due_words = schedule.get("due_words", [])
    if not due_words:
        return None

    quiz_ids: list[str] = []
    for item in due_words:
        result = generate_web_quiz(item["vocab_id"], "")
        if result:
            quiz_ids.append(result["quiz_id"])

    if not quiz_ids:
        return None

    batch_id = f"batch_{uuid4().hex[:8]}"
    _batch_sessions[batch_id] = _BatchReviewSession(batch_id=batch_id, quiz_ids=quiz_ids)
    return {"batch_id": batch_id, "total": len(quiz_ids)}


def get_batch_review_item(batch_id: str, index: int) -> Optional[dict]:
    """获取批量复习中的指定题目"""
    session = _batch_sessions.get(batch_id)
    if session is None or index < 0 or index >= len(session.quiz_ids):
        return None

    storage = _get_storage()
    quiz = storage.load_quiz(session.quiz_ids[index])
    if quiz is None:
        return None

    return {
        "batch_id": batch_id,
        "index": index,
        "total": len(session.quiz_ids),
        "quiz": quiz.model_dump(),
    }


def grade_batch_review_item(batch_id: str, index: int, response: str) -> Optional[dict]:
    """评批量复习中的指定题目

    Returns:
        {"result": dict, "is_last": bool, "next_index": int|None}
        题目不存在返回 None
    """
    session = _batch_sessions.get(batch_id)
    if session is None or index < 0 or index >= len(session.quiz_ids):
        return None

    quiz_id = session.quiz_ids[index]
    result = grade_web_quiz(quiz_id, response)
    session.graded[index] = result

    is_last = index == len(session.quiz_ids) - 1
    return {
        "result": result,
        "is_last": is_last,
        "next_index": None if is_last else index + 1,
    }


def get_batch_review_summary(batch_id: str) -> Optional[dict]:
    """获取批量复习汇总

    返回：题数、均分、grade<3 薄弱词列表、下次复习日期分布
    """
    session = _batch_sessions.get(batch_id)
    if session is None:
        return None

    storage = _get_storage()
    total = len(session.quiz_ids)
    graded_count = len(session.graded)
    grades = [r["grade"] for r in session.graded.values()]
    avg_grade = round(sum(grades) / len(grades), 2) if grades else 0.0

    weak_words: list[dict] = []
    for idx, result in session.graded.items():
        if result["grade"] < 3:
            quiz = storage.load_quiz(session.quiz_ids[idx])
            if quiz:
                vocab = storage.load_vocab(quiz.vocab_id)
                if vocab:
                    weak_words.append({
                        "vocab_id": vocab.id,
                        "word": vocab.structured.word,
                        "grade": result["grade"],
                    })

    # 下次复习日期分布
    next_review_distribution: dict[str, int] = {}
    for quiz_id in session.quiz_ids:
        quiz = storage.load_quiz(quiz_id)
        if quiz:
            vocab = storage.load_vocab(quiz.vocab_id)
            if vocab:
                date = vocab.review_state.next_review
                if date:
                    next_review_distribution[date] = next_review_distribution.get(date, 0) + 1

    return {
        "batch_id": batch_id,
        "total": total,
        "graded_count": graded_count,
        "avg_grade": avg_grade,
        "weak_words": weak_words,
        "next_review_distribution": dict(sorted(next_review_distribution.items())),
    }


# ──────────────────────────────────────────
# 词汇详情
# ──────────────────────────────────────────

def get_vocab_detail(vocab_id: str) -> Optional[dict]:
    """获取词汇详情（用于 Web 展示）

    definitions 返回 list[dict]（每项 {text, examples}），供模板按义项分组展示例句。
    """
    storage = _get_storage()
    vocab = storage.load_vocab(vocab_id)
    if vocab is None:
        return None
    return {
        "vocab_id": vocab.id,
        "word": vocab.structured.word,
        "phonetic": vocab.structured.phonetic,
        "part_of_speech": vocab.structured.part_of_speech,
        "definitions": [d.model_dump() for d in vocab.structured.definitions],
        "language": vocab.structured.language,
        "review_state": vocab.review_state.model_dump(),
        "created_at": vocab.created_at.isoformat(),
        "updated_at": vocab.updated_at.isoformat(),
    }


# ──────────────────────────────────────────
# 词汇管理（列表 / 搜索 / 更新 / 删除）
# ──────────────────────────────────────────

_SUPPORTED_LANGUAGES = [("en", "英语"), ("zh", "中文"), ("zh_classical", "文言文"), ("de", "德语")]


def list_vocabs_for_web(language: str = "", keyword: str = "") -> list[dict]:
    """获取词汇列表，支持按语言和关键词过滤

    返回按创建时间倒序排列的词汇摘要列表。
    """
    storage = _get_storage()
    filters: dict = {}
    if language:
        filters["language"] = language
    if keyword:
        filters["word"] = keyword

    result = storage.query_vocabs(filters)
    return [
        {
            "vocab_id": v["id"],
            "word": v["structured"]["word"],
            "language": v["structured"]["language"],
            "part_of_speech": v["structured"]["part_of_speech"],
            # 列表卡片只显示释义文本摘要（不含例句，保持轻量）
            "definitions": [d["text"] for d in v["structured"]["definitions"]],
            "next_review": v["review_state"]["next_review"],
            "repetitions": v["review_state"]["repetitions"],
        }
        for v in result["vocabs"]
    ]


def delete_vocab(vocab_id: str) -> bool:
    """删除词汇"""
    storage = _get_storage()
    return storage.delete_vocab(vocab_id)


def _parse_definitions_block(value: str) -> list[dict]:
    """解析编辑表单的 definitions textarea 为 list[dict]

    每行一条释义，格式：`释义文本|例句1;例句2`
    - `|` 分隔释义与例句区段（无例句时省略 `|`）
    - `;` 分隔多个例句
    - 空行跳过

    示例：
        兵器|收天下之兵;此所谓藉寇兵
        士兵，军队
    → [{"text": "兵器", "examples": ["收天下之兵", "此所谓藉寇兵"]},
       {"text": "士兵，军队", "examples": []}]
    """
    result: list[dict] = []
    for line in value.replace("\r\n", "\n").split("\n"):
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            text, ex_str = line.split("|", 1)
            examples = [e.strip() for e in ex_str.split(";") if e.strip()]
        else:
            text, examples = line, []
        result.append({"text": text.strip(), "examples": examples})
    return result


def update_vocab_from_web(vocab_id: str, form: dict) -> Optional[dict]:
    """从 Web 表单更新词汇结构化信息

    Args:
        vocab_id: 词汇 ID
        form: 表单字段字典，支持 word/phonetic/part_of_speech/language/definitions
              definitions textarea 每行格式：`释义文本|例句1;例句2`

    Returns:
        更新后的词汇详情；ID 不存在返回 None
    """
    storage = _get_storage()
    existing = storage.load_vocab(vocab_id)
    if existing is None:
        return None

    # 保留原例句关联结构：若表单未提供 definitions（异常情况），回退到原值
    raw_defs = form.get("definitions", "")
    if raw_defs:
        new_defs = _parse_definitions_block(raw_defs)
    else:
        new_defs = [d.model_dump() for d in existing.structured.definitions]

    patch: dict = {
        "structured": {
            "word": form.get("word", existing.structured.word).strip(),
            "phonetic": form.get("phonetic", existing.structured.phonetic).strip(),
            "part_of_speech": form.get("part_of_speech", existing.structured.part_of_speech).strip(),
            "language": form.get("language", existing.structured.language).strip(),
            "definitions": new_defs,
            "source_image": existing.structured.source_image,
        }
    }

    updated = storage.patch_vocab(vocab_id, patch)
    if updated is None:
        return None
    return get_vocab_detail(updated.id)


def get_language_options() -> list[tuple[str, str]]:
    """返回 Web 表单可用的语言选项"""
    return list(_SUPPORTED_LANGUAGES)


# ──────────────────────────────────────────
# N-05 语种洞察：遗忘曲线
# ──────────────────────────────────────────

# 对数桶定义：[下界, 上界, 代表 days, 标签]
# ponytail: 对数桶而非逐日，因为逐日数据稀疏；x 轴用「距首次复习天数」
#           而非「距上次复习天数」，避免逐 vocab 排序 ReviewRecord 的复杂度。
#           升级路径：数据量大后改「距上次复习天数」+ 逐日滑动窗口
_RETENTION_BUCKETS = [
    (0, 0, 0, "0天"),
    (1, 1, 1, "1天"),
    (2, 3, 3, "2-3天"),
    (4, 7, 7, "4-7天"),
    (8, 15, 15, "8-15天"),
    (16, 30, 30, "16-30天"),
    (31, 10**9, 31, "31+天"),
]
_MIN_BUCKET_SAMPLE = 3  # 桶内少于 3 条样本则丢弃，避免单点噪声


def _bucket_of(days: int) -> Optional[tuple[int, int, int, str]]:
    """返回 days 所属的桶元组 (low, high, rep_days, label)；无匹配返回 None"""
    for b in _RETENTION_BUCKETS:
        if b[0] <= days <= b[1]:
            return b
    return None


def _theoretical_curve() -> list[dict]:
    """理论遗忘曲线（参考线）

    复用 _INITIAL_INTERVALS_DAYS 与现有简化公式。
    ponytail: 简化模型，非真实艾宾浩斯公式，仅作参考线。
    """
    curve = []
    for i, interval in enumerate(_INITIAL_INTERVALS_DAYS):
        retention = max(35, 100 - (i + 1) * 12)
        curve.append({"days": interval, "retention": retention})
    return curve


def _real_retention_curve(language: str) -> list[dict]:
    """基于 ReviewRecord 计算真实保留率散点（按语言过滤）

    算法：
        1. 取所有 ReviewRecord，按 vocab_id 关联 vocab 拿语言与首次复习时间
        2. 首次复习时间 = 该 vocab 所有 ReviewRecord 的 min(review_time)
        3. 每条记录 x = (review_time - 首次复习时间).days
        4. 按 x 落入对数桶
        5. 桶内 grade>=3 百分比 = 保留率；sample_size < _MIN_BUCKET_SAMPLE 丢弃

    返回：[{bucket_label, days, retention, sample_size}]，按 days 升序
          retention 为百分比 [0, 100]，与 _theoretical_curve 刻度一致。

    ponytail: 对数桶而非逐日，因为逐日数据稀疏；x 轴用「距首次复习天数」
              而非「距上次复习天数」，避免逐 vocab 排序 ReviewRecord 的复杂度。
              升级路径：数据量大后改「距上次复习天数」+ 逐日滑动窗口，
              并将 N+1 load_vocab 换成 get_all_vocabs_for_statistics 一次性加载内存 join。
    """
    storage = _get_storage()
    records = storage.list_all_review_records()
    if not records:
        return []

    # 按 vocab_id 分组，过滤到目标语言
    by_vocab: dict[str, list[ReviewRecord]] = {}
    for r in records:
        v = storage.load_vocab(r.vocab_id)
        if v is None or v.structured.language != language:
            continue
        by_vocab.setdefault(r.vocab_id, []).append(r)

    if not by_vocab:
        return []

    # 桶聚合
    bucket_stats: dict[int, list[int]] = {}  # rep_days -> [grades]
    for vid, recs in by_vocab.items():
        first_review = min(r.review_time for r in recs)
        for r in recs:
            x = (r.review_time - first_review).days
            b = _bucket_of(x)
            if b is None:
                continue
            rep_days = b[2]
            bucket_stats.setdefault(rep_days, []).append(r.grade)

    curve = []
    for rep_days in sorted(bucket_stats.keys()):
        grades = bucket_stats[rep_days]
        if len(grades) < _MIN_BUCKET_SAMPLE:
            continue
        retention = sum(1 for g in grades if g >= 3) / len(grades) * 100
        label = next(b[3] for b in _RETENTION_BUCKETS if b[2] == rep_days)
        curve.append({
            "bucket_label": label,
            "days": rep_days,
            "retention": round(retention, 1),
            "sample_size": len(grades),
        })
    return curve


# ──────────────────────────────────────────
# N-05 语种洞察：薄弱词 + 掌握度分布
# ──────────────────────────────────────────

def _weak_words_by_language(language: str) -> list[dict]:
    """该语言下最近一次 ReviewRecord.grade < 3 的词

    依据：复习规则第 10 条「grade<3 薄弱词列表」

    返回：[{vocab_id, word, last_grade, last_review_time, repetitions, ease_factor}]
    排序：last_grade 升序（最差在前），grade 相同按 last_review_time 降序（最近复习的在前）
    """
    storage = _get_storage()
    records = storage.list_all_review_records()
    if not records:
        return []

    # 按 vocab_id 分组，取每词最近一条记录
    latest_by_vocab: dict[str, ReviewRecord] = {}
    for r in records:
        existing = latest_by_vocab.get(r.vocab_id)
        if existing is None or r.review_time > existing.review_time:
            latest_by_vocab[r.vocab_id] = r

    weak = []
    for vid, latest in latest_by_vocab.items():
        if latest.grade >= 3:
            continue
        v = storage.load_vocab(vid)
        if v is None or v.structured.language != language:
            continue
        weak.append({
            "vocab_id": vid,
            "word": v.structured.word,
            "last_grade": latest.grade,
            "last_review_time": latest.review_time.isoformat(),
            "repetitions": v.review_state.repetitions,
            "ease_factor": v.review_state.ease_factor,
        })

    # grade 升序（最差在前）；grade 相同按时间倒序（最近在前）
    # 用稳定排序分两步：先按时间倒序，再按 grade 升序（保持时间倒序关系）
    from operator import itemgetter
    weak.sort(key=itemgetter("last_review_time"), reverse=True)  # 先按时间倒序
    weak.sort(key=itemgetter("last_grade"))  # 再按 grade 升序（稳定排序保持时间倒序）
    return weak


def _mastery_distribution_by_language(language: str) -> list[dict]:
    """该语言掌握度分布（新词/生疏/熟悉/掌握）

    复用 _mastery_level，固定顺序保证图表颜色稳定。
    """
    storage = _get_storage()
    mastery_counter: dict[str, int] = {"新词": 0, "生疏": 0, "熟悉": 0, "掌握": 0}
    for v in storage.get_all_vocabs_for_statistics():
        if v.structured.language != language:
            continue
        level = _mastery_level(v.review_state.repetitions)
        mastery_counter[level] += 1
    return [{"name": k, "value": v} for k, v in mastery_counter.items()]


# ──────────────────────────────────────────
# N-05 语种洞察：汇总入口
# ──────────────────────────────────────────

_SMALL_SAMPLE_THRESHOLD = 10  # total < 10 触发小样本降级


def get_insights_summary(language: str) -> dict:
    """语种洞察汇总：KPI + 遗忘曲线 + 薄弱词 + 掌握度分布

    Args:
        language: 语言代码（de / zh_classical）

    Returns:
        {
            "language": str,
            "kpi": {total, today_pending, mastered, avg_ease},
            "forgetting_curve": {"theoretical": [...], "real": [...]},
            "weak_words": [...],
            "mastery_distribution": [...],
            "sample_size_flag": "small" | "normal"
        }
    """
    storage = _get_storage()
    today = _today_utc_iso()
    vocabs = [v for v in storage.get_all_vocabs_for_statistics()
              if v.structured.language == language]

    total = len(vocabs)
    today_pending = sum(
        1 for v in vocabs
        if v.review_state.next_review and v.review_state.next_review <= today
    )
    mastered = sum(1 for v in vocabs if _mastery_level(v.review_state.repetitions) == "掌握")
    avg_ease = (sum(v.review_state.ease_factor for v in vocabs) / total) if total > 0 else 0.0

    return {
        "language": language,
        "kpi": {
            "total": total,
            "today_pending": today_pending,
            "mastered": mastered,
            "avg_ease": round(avg_ease, 2),
        },
        "forgetting_curve": {
            "theoretical": _theoretical_curve(),
            "real": _real_retention_curve(language),
        },
        "weak_words": _weak_words_by_language(language),
        "mastery_distribution": _mastery_distribution_by_language(language),
        "sample_size_flag": "small" if total < _SMALL_SAMPLE_THRESHOLD else "normal",
    }
