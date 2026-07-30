# tests/test_web_services.py
"""测试 Web 服务层 — 编排 storage/statistics/review/quiz"""
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from vocabcraft_mcp.models import Definition, ReviewRecord, ReviewState, StructuredVocab, VocabRecord
from vocabcraft_mcp.storage import Storage
from vocabcraft_mcp.web import services


@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    """创建临时 storage 并注入 services 模块"""
    storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: storage)
    # 同时隔离底层 crud 的默认目录，避免 quiz 工具读到真实数据
    monkeypatch.setattr("vocabcraft_mcp.tools.crud._DEFAULT_DATA_DIR", tmp_path)
    return storage


def _make_vocab(word, vid, language="en", repetitions=0, next_review=""):
    """构造完整测试词汇（definitions 内嵌 examples 新格式）"""
    return VocabRecord(
        id=vid,
        structured=StructuredVocab(
            word=word,
            phonetic="/test/",
            part_of_speech="n.",
            definitions=[Definition(text=f"{word} 的释义", examples=[f"This is {word}."])],
            language=language,
        ),
        review_state=ReviewState(
            repetitions=repetitions,
            next_review=next_review,
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_classical_vocab(word, vid, part_of_speech="n.", definitions=None, next_review=""):
    """构造文言文测试词汇（definition.text 含【词性】标记）"""
    if definitions is None:
        definitions = [Definition(text=f"【名词】{word} 的释义", examples=[f"此{word}乃测试例句。"])]
    return VocabRecord(
        id=vid,
        structured=StructuredVocab(
            word=word,
            phonetic="",
            part_of_speech=part_of_speech,
            definitions=definitions,
            language="zh_classical",
        ),
        review_state=ReviewState(
            repetitions=0,
            next_review=next_review,
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ──────────────────────────────────────────
# Dashboard summary 测试
# ──────────────────────────────────────────

def test_dashboard_summary_empty(temp_storage):
    """无数据时应返回零值"""
    summary = services.get_dashboard_summary()
    assert summary["total"] == 0
    assert summary["today_pending"] == 0
    assert summary["week_new"] == 0
    assert summary["mastered"] == 0
    assert summary["language_distribution"] == []
    assert summary["mastery_distribution"] == [
        {"name": "新词", "value": 0},
        {"name": "生疏", "value": 0},
        {"name": "熟悉", "value": 0},
        {"name": "掌握", "value": 0},
    ]
    assert len(summary["trends"]) == 30
    assert all(v == 0 for v in summary["trends"].values())


def test_dashboard_summary_with_data(temp_storage):
    """有数据时应正确统计"""
    today = datetime.now(timezone.utc).date().isoformat()
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", language="en", next_review=today))
    temp_storage.save_vocab(_make_vocab("世界", "vocab_002", language="zh", repetitions=6))

    summary = services.get_dashboard_summary()
    assert summary["total"] == 2
    assert summary["today_pending"] == 1
    assert summary["mastered"] == 1

    languages = {item["name"] for item in summary["language_distribution"]}
    assert "en" in languages
    assert "zh" in languages


# ──────────────────────────────────────────
# Multi-dim stats 测试
# ──────────────────────────────────────────

def test_multi_dim_stats(temp_storage):
    """多维统计应返回分布与趋势数据"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))
    temp_storage.save_vocab(_make_vocab("world", "vocab_002", language="en"))

    multi = services.get_multi_dim_stats()
    assert "language_distribution" in multi
    assert "mastery_distribution" in multi
    assert "quiz_type_distribution" in multi
    assert "trend_data" in multi
    assert len(multi["trend_data"]) == 30


# ──────────────────────────────────────────
# 待复习列表测试
# ──────────────────────────────────────────

def test_upcoming_reviews(temp_storage):
    """应返回已到期的词汇"""
    today = datetime.now(timezone.utc).date().isoformat()
    temp_storage.save_vocab(_make_vocab("due", "vocab_001", next_review=today))
    temp_storage.save_vocab(_make_vocab("future", "vocab_002", next_review="2099-01-01"))

    upcoming = services.get_upcoming_reviews()
    assert len(upcoming) == 1
    assert upcoming[0]["vocab_id"] == "vocab_001"


# ──────────────────────────────────────────
# 复习日历测试
# ──────────────────────────────────────────

def test_review_calendar(temp_storage):
    """日历应包含当月每一天"""
    today = datetime.now(timezone.utc)
    temp_storage.save_vocab(_make_vocab("due", "vocab_001", next_review=today.date().isoformat()))

    calendar = services.get_review_calendar()
    assert "calendar_days" in calendar
    assert len(calendar["calendar_days"]) >= 28
    assert any(day["is_today"] for day in calendar["calendar_days"])


# ──────────────────────────────────────────
# 出题与评分测试
# ──────────────────────────────────────────

def test_generate_web_quiz(temp_storage):
    """应能生成 Web 考题并填充题干"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001"))
    result = services.generate_web_quiz("vocab_001", "拼写")
    assert result is not None
    assert result["quiz"]["quiz_type"] == "拼写"
    assert "释义" in result["quiz"]["question"] or "拼写" in result["quiz"]["question"]


def test_generate_web_quiz_unknown_vocab(temp_storage):
    """词汇不存在返回 None"""
    assert services.generate_web_quiz("vocab_missing", "拼写") is None


def test_grade_web_quiz(temp_storage):
    """评分后应更新记忆状态"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001"))
    quiz_result = services.generate_web_quiz("vocab_001", "拼写")
    quiz_id = quiz_result["quiz_id"]

    result = services.grade_web_quiz(quiz_id, "hello")
    assert result["grade"] == 5
    assert result["correct"] is True
    assert "updated_review_state" in result


# ──────────────────────────────────────────
# 文言释义题测试（Task 4）
# ──────────────────────────────────────────

def test_generate_web_classical_quiz_with_example(temp_storage):
    """zh_classical 释义题有例句时，题干高亮目标词并含 4 个词性选项"""
    definitions = [Definition(text="兵器", examples=["收天下之兵，聚之咸阳。"])]
    temp_storage.save_vocab(_make_classical_vocab("兵", "vocab_001", part_of_speech="n.", definitions=definitions))

    result = services.generate_web_quiz("vocab_001", "释义")
    assert result is not None
    quiz = result["quiz"]
    assert quiz["quiz_type"] == "释义"
    assert "<mark>兵</mark>" in quiz["question"]
    assert quiz["options"] is not None
    assert len(quiz["options"]) == 4
    assert "n." in quiz["options"]
    assert quiz["answer"] == "n.|兵器"
    assert quiz["language"] == "zh_classical"


def test_generate_web_classical_quiz_uses_def_pos(temp_storage):
    """zh_classical 释义题使用 definition.part_of_speech 字段"""
    definitions = [
        Definition(text="行走", examples=["老臣今者殊不欲食，乃自强步。"], part_of_speech="动词"),
    ]
    temp_storage.save_vocab(_make_classical_vocab("步", "vocab_001", part_of_speech="n.", definitions=definitions))

    result = services.generate_web_quiz("vocab_001", "释义")
    quiz = result["quiz"]
    assert quiz["answer"] == "v.|行走"
    assert "v." in quiz["options"]


def test_generate_web_classical_quiz_without_example(temp_storage):
    """zh_classical 释义题无例句时，题干降级为释义文本提示"""
    definitions = [Definition(text="兵器", examples=[])]
    temp_storage.save_vocab(_make_classical_vocab("兵", "vocab_001", part_of_speech="n.", definitions=definitions))

    result = services.generate_web_quiz("vocab_001", "释义")
    assert result is not None
    quiz = result["quiz"]
    assert "请写出" in quiz["question"]
    assert "<mark>" not in quiz["question"]
    assert quiz["answer"] == "n.|兵器"
    assert quiz["language"] == "zh_classical"


def test_generate_web_classical_quiz_options_format(temp_storage):
    """zh_classical 释义题选项为 4 个不重复词性，答案为 词性|释义 编码"""
    definitions = [Definition(text="兵器", examples=["收天下之兵"])]
    temp_storage.save_vocab(_make_classical_vocab("兵", "vocab_001", part_of_speech="n.", definitions=definitions))

    result = services.generate_web_quiz("vocab_001", "释义")
    quiz = result["quiz"]
    assert isinstance(quiz["options"], list)
    assert len(set(quiz["options"])) == 4
    assert "n." in quiz["options"]
    assert quiz["answer"] == "n.|兵器"
    assert quiz["language"] == "zh_classical"


# ──────────────────────────────────────────
# 词汇管理测试
# ──────────────────────────────────────────

def test_list_vocabs_for_web(temp_storage):
    """词汇列表应支持按语言/关键词过滤"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))
    temp_storage.save_vocab(_make_vocab("世界", "vocab_002", language="zh"))

    all_vocabs = services.list_vocabs_for_web()
    assert len(all_vocabs) == 2

    en_vocabs = services.list_vocabs_for_web(language="en")
    assert len(en_vocabs) == 1
    assert en_vocabs[0]["word"] == "hello"

    filtered = services.list_vocabs_for_web(keyword="世界")
    assert len(filtered) == 1
    assert filtered[0]["word"] == "世界"


def test_get_vocab_detail(temp_storage):
    """词汇详情应包含结构化字段与时间戳"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))
    detail = services.get_vocab_detail("vocab_001")
    assert detail is not None
    assert detail["word"] == "hello"
    assert detail["language"] == "en"
    assert "created_at" in detail
    assert "updated_at" in detail


def test_update_vocab_from_web(temp_storage):
    """Web 表单更新应修改词汇结构化信息并保留 source_image

    表单 definitions textarea 每行格式：`释义文本|例句1;例句2`
    """
    vocab = _make_vocab("hello", "vocab_001", language="en")
    vocab.structured.source_image = "images/test.png"
    temp_storage.save_vocab(vocab)

    updated = services.update_vocab_from_web("vocab_001", {
        "word": "hi",
        "phonetic": "/haɪ/",
        "part_of_speech": "int.",
        "language": "de",
        # 新格式：两行释义，第一行带例句
        "definitions": "你好|Hi, there.;Hi!\n您好",
    })
    assert updated is not None
    assert updated["word"] == "hi"
    assert updated["language"] == "de"
    # definitions 返回 list[dict]（每项 {text, examples}）
    assert len(updated["definitions"]) == 2
    assert updated["definitions"][0]["text"] == "你好"
    assert updated["definitions"][0]["examples"] == ["Hi, there.", "Hi!"]
    assert updated["definitions"][1]["text"] == "您好"
    assert updated["definitions"][1]["examples"] == []

    # source_image 应保留
    reloaded = temp_storage.load_vocab("vocab_001")
    assert reloaded.structured.source_image == "images/test.png"


def test_delete_vocab(temp_storage):
    """删除词汇应成功"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001"))
    assert services.delete_vocab("vocab_001") is True
    assert temp_storage.load_vocab("vocab_001") is None


# ──────────────────────────────────────────
# 批量复习测试
# ──────────────────────────────────────────

def _today_iso():
    """当前 UTC 日期字符串"""
    return datetime.now(timezone.utc).date().isoformat()


def test_start_batch_review_with_due_words(temp_storage):
    """有到期词汇时应创建批量复习会话"""
    today = _today_iso()
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", next_review=today))
    temp_storage.save_vocab(_make_vocab("world", "vocab_002", next_review=today))
    temp_storage.save_vocab(_make_vocab("future", "vocab_003", next_review="2099-01-01"))

    batch = services.start_batch_review()
    assert batch is not None
    assert batch["total"] == 2

    # 第 0 题应存在
    item = services.get_batch_review_item(batch["batch_id"], 0)
    assert item is not None
    assert item["index"] == 0
    assert item["total"] == 2
    assert item["quiz"]["language"] == "en"


def test_start_batch_review_no_due_words(temp_storage):
    """无到期词汇时返回 None"""
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", next_review="2099-01-01"))
    assert services.start_batch_review() is None


def test_grade_batch_review_item(temp_storage):
    """批量评分应推进到下一题并更新记忆状态"""
    today = _today_iso()
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", next_review=today))
    temp_storage.save_vocab(_make_vocab("world", "vocab_002", next_review=today))

    batch = services.start_batch_review()
    batch_id = batch["batch_id"]

    # 第一题答错
    graded = services.grade_batch_review_item(batch_id, 0, "wrong")
    assert graded is not None
    assert graded["is_last"] is False
    assert graded["next_index"] == 1

    # 第二题答对
    graded = services.grade_batch_review_item(batch_id, 1, "world")
    assert graded is not None
    assert graded["is_last"] is True
    assert graded["next_index"] is None


def test_get_batch_review_summary(temp_storage):
    """汇总应包含题数、均分、薄弱词、下次复习分布"""
    today = _today_iso()
    temp_storage.save_vocab(_make_vocab("hello", "vocab_001", next_review=today))
    temp_storage.save_vocab(_make_vocab("world", "vocab_002", next_review=today))

    batch = services.start_batch_review()
    batch_id = batch["batch_id"]
    services.grade_batch_review_item(batch_id, 0, "wrong")
    services.grade_batch_review_item(batch_id, 1, "world")

    summary = services.get_batch_review_summary(batch_id)
    assert summary is not None
    assert summary["total"] == 2
    assert summary["graded_count"] == 2
    assert summary["avg_grade"] == 2.5
    assert len(summary["weak_words"]) == 1
    assert summary["weak_words"][0]["word"] == "hello"
    assert summary["next_review_distribution"] != {}


# ──────────────────────────────────────────
# N-05 insights 服务层测试
# ──────────────────────────────────────────


def _make_review_record(rid, vid, review_time, grade, prev_ease=2.5, new_ease=2.5, definition_index=None):
    """构造复习记录"""
    return ReviewRecord(
        record_id=rid,
        vocab_id=vid,
        review_time=review_time,
        grade=grade,
        prev_ease=prev_ease,
        new_ease=new_ease,
        definition_index=definition_index,
    )


def test_theoretical_curve_returns_intervals(temp_storage):
    """理论曲线返回 INITIAL_INTERVALS_DAYS 对应的天数与保留率"""
    from vocabcraft_mcp.web.services import get_forgetting_curve
    curve = get_forgetting_curve()
    assert len(curve) == 5  # INITIAL_INTERVALS_DAYS 5 个节点
    assert all("days" in c and "retention" in c for c in curve)
    # 保留率应在 [35, 100] 范围内（现有公式 max(35, 100-(i+1)*12)）
    assert all(35 <= c["retention"] <= 100 for c in curve)


def test_real_retention_curve_empty_when_no_records(temp_storage):
    """无复习记录时返回空列表"""
    from vocabcraft_mcp.web.services import _real_retention_curve
    temp_storage.save_vocab(_make_vocab("hallo", "vocab_001", language="de"))
    curve = _real_retention_curve("de")
    assert curve == []


def test_real_retention_curve_buckets_by_days_since_first_review(temp_storage):
    """按距首次复习天数分桶，桶内 grade>=3 比例 = 保留率"""
    from vocabcraft_mcp.web.services import _real_retention_curve
    base = datetime(2026, 7, 1, tzinfo=timezone.utc)
    temp_storage.save_vocab(_make_vocab("hallo", "vocab_001", language="de"))

    # 5 条记录：第 0 天 2 条（grade 5, 2），第 3 天 2 条（grade 4, 1），第 10 天 1 条（grade 5）
    # 第 0 天桶：保留率 = 1/2 = 50%（sample_size=2 >= 3? 不，<3，丢弃）
    # 改为：第 0 天 3 条（grade 5, 4, 2）→ 保留率 2/3，sample_size=3 保留
    records = [
        _make_review_record("rec_001", "vocab_001", base, grade=5),                       # 第 0 天
        _make_review_record("rec_002", "vocab_001", base + timedelta(days=0), grade=4),   # 第 0 天
        _make_review_record("rec_003", "vocab_001", base + timedelta(days=0), grade=2),   # 第 0 天
        _make_review_record("rec_004", "vocab_001", base + timedelta(days=3), grade=5),   # 第 3 天 → 桶 2-3
        _make_review_record("rec_005", "vocab_001", base + timedelta(days=10), grade=1),  # 第 10 天 → 桶 8-15
    ]
    for r in records:
        temp_storage.save_review_record(r)

    curve = _real_retention_curve("de")
    # 找到第 0 天桶（days=0）
    bucket_0 = next((c for c in curve if c["days"] == 0), None)
    assert bucket_0 is not None
    assert bucket_0["sample_size"] == 3
    assert bucket_0["retention"] == pytest.approx(100 * 2 / 3, abs=0.1)  # grade 5,4 通过，2 失败 → 66.7%

    # 第 2-3 天桶（days=3）sample_size=1 < 3，应被丢弃
    bucket_3 = next((c for c in curve if c["days"] == 3), None)
    assert bucket_3 is None


def test_real_retention_curve_filters_by_language(temp_storage):
    """只统计指定语言的复习记录"""
    from vocabcraft_mcp.web.services import _real_retention_curve
    base = datetime(2026, 7, 1, tzinfo=timezone.utc)
    temp_storage.save_vocab(_make_vocab("hallo", "vocab_de", language="de"))
    temp_storage.save_vocab(_make_vocab("病", "vocab_zh", language="zh_classical"))

    # de 与 zh_classical 各 3 条第 0 天记录
    for i, grade in enumerate([5, 4, 3]):
        temp_storage.save_review_record(_make_review_record(f"rec_de_{i}", "vocab_de", base, grade=grade))
    for i, grade in enumerate([2, 1, 0]):
        temp_storage.save_review_record(_make_review_record(f"rec_zh_{i}", "vocab_zh", base, grade=grade))

    de_curve = _real_retention_curve("de")
    zh_curve = _real_retention_curve("zh_classical")
    # de 桶 0：3 条全 >=3，保留率 100%
    assert de_curve[0]["retention"] == pytest.approx(100.0, abs=0.1)
    # zh_classical 桶 0：3 条全 <3，保留率 0%
    assert zh_curve[0]["retention"] == pytest.approx(0.0, abs=0.1)


# ──────────────────────────────────────────
# N-05 Task 5: 薄弱词分布 + 掌握度分布
# ──────────────────────────────────────────


def test_weak_words_by_language_filters_grade_below_3(temp_storage):
    """薄弱词 = 该语言下最近一次 ReviewRecord.grade < 3"""
    from vocabcraft_mcp.web.services import _weak_words_by_language
    base = datetime(2026, 7, 1, tzinfo=timezone.utc)
    temp_storage.save_vocab(_make_vocab("hallo", "vocab_001", language="de"))
    temp_storage.save_vocab(_make_vocab("welt", "vocab_002", language="de", repetitions=2))

    # vocab_001 最近一次 grade=2（薄弱）
    temp_storage.save_review_record(_make_review_record("rec_001", "vocab_001", base, grade=5))
    temp_storage.save_review_record(_make_review_record("rec_002", "vocab_001", base + timedelta(days=1), grade=2))
    # vocab_002 最近一次 grade=4（不薄弱）
    temp_storage.save_review_record(_make_review_record("rec_003", "vocab_002", base, grade=4))

    weak = _weak_words_by_language("de")
    assert len(weak) == 1
    assert weak[0]["vocab_id"] == "vocab_001"
    assert weak[0]["last_grade"] == 2
    assert weak[0]["word"] == "hallo"


def test_weak_words_by_language_excludes_other_languages(temp_storage):
    """薄弱词只统计指定语言"""
    from vocabcraft_mcp.web.services import _weak_words_by_language
    base = datetime(2026, 7, 1, tzinfo=timezone.utc)
    temp_storage.save_vocab(_make_vocab("hallo", "vocab_de", language="de"))
    temp_storage.save_vocab(_make_vocab("病", "vocab_zh", language="zh_classical"))
    temp_storage.save_review_record(_make_review_record("rec_de", "vocab_de", base, grade=1))
    temp_storage.save_review_record(_make_review_record("rec_zh", "vocab_zh", base, grade=1))

    weak_de = _weak_words_by_language("de")
    assert len(weak_de) == 1
    assert weak_de[0]["vocab_id"] == "vocab_de"


def test_weak_words_by_language_empty_when_no_records(temp_storage):
    """无复习记录时返回空列表"""
    from vocabcraft_mcp.web.services import _weak_words_by_language
    temp_storage.save_vocab(_make_vocab("hallo", "vocab_001", language="de"))
    assert _weak_words_by_language("de") == []


def test_mastery_distribution_by_language(temp_storage):
    """按语言统计掌握度分布"""
    from vocabcraft_mcp.web.services import _mastery_distribution_by_language
    # de: 1 新词(rep=0), 1 生疏(rep=2), 1 熟悉(rep=4), 1 掌握(rep=6)
    temp_storage.save_vocab(_make_vocab("w1", "vocab_001", language="de", repetitions=0))
    temp_storage.save_vocab(_make_vocab("w2", "vocab_002", language="de", repetitions=2))
    temp_storage.save_vocab(_make_vocab("w3", "vocab_003", language="de", repetitions=4))
    temp_storage.save_vocab(_make_vocab("w4", "vocab_004", language="de", repetitions=6))
    # zh_classical: 1 新词（不应出现在 de 分布中）
    temp_storage.save_vocab(_make_vocab("病", "vocab_zh", language="zh_classical", repetitions=0))

    dist = _mastery_distribution_by_language("de")
    assert dist == [
        {"name": "新词", "value": 1},
        {"name": "生疏", "value": 1},
        {"name": "熟悉", "value": 1},
        {"name": "掌握", "value": 1},
    ]


def test_mastery_distribution_by_language_empty(temp_storage):
    """无该语言词汇时全 0"""
    from vocabcraft_mcp.web.services import _mastery_distribution_by_language
    dist = _mastery_distribution_by_language("de")
    assert dist == [
        {"name": "新词", "value": 0},
        {"name": "生疏", "value": 0},
        {"name": "熟悉", "value": 0},
        {"name": "掌握", "value": 0},
    ]


# ──────────────────────────────────────────
# Task 1: 词性解析与中英文映射
# ──────────────────────────────────────────

from vocabcraft_mcp.tools.quiz import _parse_def_pos, en_to_zh_pos, zh_to_en_pos


def test_parse_def_pos_with_marker():
    """【词性】标记可被解析为中文词性和纯释义"""
    pos, meaning = _parse_def_pos("【名词】步伐，脚步")
    assert pos == "名词"
    assert meaning == "步伐，脚步"


def test_parse_def_pos_without_marker():
    """无标记时返回空词性和原文本"""
    pos, meaning = _parse_def_pos("步伐，脚步")
    assert pos == ""
    assert meaning == "步伐，脚步"


def test_parse_def_pos_leading_spaces():
    """前导空格不影响词性标记解析"""
    pos, meaning = _parse_def_pos("  【名词】  步伐，脚步  ")
    assert pos == "名词"
    assert meaning == "步伐，脚步"


def test_parse_def_pos_combined():
    """组合词性标记可被解析"""
    pos, meaning = _parse_def_pos("【名词/动词】步伐")
    assert pos == "名词/动词"
    assert meaning == "步伐"


def test_parse_def_pos_unrecognized():
    """非标准词性标记原样保留"""
    pos, meaning = _parse_def_pos("【形】步伐")
    assert pos == "形"
    assert meaning == "步伐"


def test_zh_to_en_pos_single():
    """单个中文词性映射为英文简写"""
    assert zh_to_en_pos("名词") == "n."
    assert zh_to_en_pos("动词") == "v."


def test_zh_to_en_pos_combined():
    """组合中文词性映射为组合英文简写"""
    assert zh_to_en_pos("名词/动词") == "n./v."


def test_en_to_zh_pos_single():
    """单个英文简写映射为中文"""
    assert en_to_zh_pos("n.") == "名词"


def test_en_to_zh_pos_combined():
    """组合英文简写映射为中文"""
    assert en_to_zh_pos("n./v.") == "名词/动词"


# ──────────────────────────────────────────
# N-05 Task 6: get_insights_summary 汇总 + 小样本降级
# ──────────────────────────────────────────


def test_insights_summary_normal_sample(temp_storage):
    """total >= 10 时 sample_size_flag = 'normal'"""
    from vocabcraft_mcp.web.services import get_insights_summary
    # 造 10 个 de 词
    for i in range(10):
        temp_storage.save_vocab(_make_vocab(f"w{i}", f"vocab_{i:03d}", language="de", repetitions=i % 6))

    summary = get_insights_summary("de")
    assert summary["language"] == "de"
    assert summary["kpi"]["total"] == 10
    assert summary["sample_size_flag"] == "normal"
    assert "theoretical" in summary["forgetting_curve"]
    assert "real" in summary["forgetting_curve"]
    assert isinstance(summary["weak_words"], list)
    assert len(summary["mastery_distribution"]) == 4


def test_insights_summary_small_sample(temp_storage):
    """total < 10 时 sample_size_flag = 'small'（zh_classical 4 词场景）"""
    from vocabcraft_mcp.web.services import get_insights_summary
    for i in range(4):
        temp_storage.save_vocab(_make_vocab(f"字{i}", f"vocab_zh_{i}", language="zh_classical"))

    summary = get_insights_summary("zh_classical")
    assert summary["kpi"]["total"] == 4
    assert summary["sample_size_flag"] == "small"


def test_insights_summary_kpi_today_pending(temp_storage):
    """KPI today_pending 统计该语言今日到期词汇"""
    from vocabcraft_mcp.web.services import get_insights_summary
    today = datetime.now(timezone.utc).date().isoformat()
    temp_storage.save_vocab(_make_vocab("hallo", "vocab_001", language="de", next_review=today))
    temp_storage.save_vocab(_make_vocab("welt", "vocab_002", language="de", next_review="2099-01-01"))
    temp_storage.save_vocab(_make_vocab("病", "vocab_zh", language="zh_classical", next_review=today))

    summary = get_insights_summary("de")
    assert summary["kpi"]["today_pending"] == 1  # 只算 de


def test_insights_summary_kpi_avg_ease(temp_storage):
    """KPI avg_ease = 该语言所有词 EF 平均值"""
    from vocabcraft_mcp.web.services import get_insights_summary
    from vocabcraft_mcp.models import ReviewState
    v1 = _make_vocab("w1", "vocab_001", language="de")
    v1.review_state = ReviewState(ease_factor=2.5)
    v2 = _make_vocab("w2", "vocab_002", language="de")
    v2.review_state = ReviewState(ease_factor=3.0)
    temp_storage.save_vocab(v1)
    temp_storage.save_vocab(v2)

    summary = get_insights_summary("de")
    assert summary["kpi"]["avg_ease"] == pytest.approx(2.75, abs=0.01)


def test_insights_summary_empty_language(temp_storage):
    """无该语言词汇时返回零值 KPI"""
    from vocabcraft_mcp.web.services import get_insights_summary
    summary = get_insights_summary("de")
    assert summary["kpi"]["total"] == 0
    assert summary["kpi"]["today_pending"] == 0
    assert summary["kpi"]["mastered"] == 0
    assert summary["kpi"]["avg_ease"] == 0
    assert summary["sample_size_flag"] == "small"
    assert summary["weak_words"] == []
