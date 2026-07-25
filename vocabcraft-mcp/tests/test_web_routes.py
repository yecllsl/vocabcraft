# tests/test_web_routes.py
"""测试 Web 路由层 — Dashboard、统计、复习、出题端点"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from vocabcraft_mcp.models import Definition, ReviewState, StructuredVocab, VocabRecord
from vocabcraft_mcp.storage import Storage
from vocabcraft_mcp.web import services
from vocabcraft_mcp.web.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    """创建已隔离 storage 的 TestClient"""
    storage = Storage(base_dir=tmp_path)
    monkeypatch.setattr(services, "_get_storage", lambda: storage)
    monkeypatch.setattr("vocabcraft_mcp.tools.crud._DEFAULT_DATA_DIR", tmp_path)
    app = create_app()
    return TestClient(app), storage


def _make_vocab(word, vid, language="en", repetitions=0, next_review=""):
    """构造完整测试词汇（definitions 内嵌 examples 新格式）"""
    return VocabRecord(
        id=vid,
        structured=StructuredVocab(
            word=word,
            phonetic="/test/",
            part_of_speech="n.",
            definitions=[Definition(text=f"{word} def", examples=[f"This is {word}."])],
            language=language,
        ),
        review_state=ReviewState(
            repetitions=repetitions,
            next_review=next_review,
        ),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def test_index_returns_base_html(client):
    """根路由返回单页外壳"""
    test_client, _ = client
    response = test_client.get("/")
    assert response.status_code == 200
    assert "VocabCraft" in response.text


def test_dashboard_partial(client):
    """Dashboard 片段包含 KPI 和图表容器"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001"))

    response = test_client.get("/partials/dashboard")
    assert response.status_code == 200
    assert "词汇总量" in response.text
    assert "language_distribution" in response.text or "data-echart" in response.text


def test_dashboard_summary_api(client):
    """Dashboard JSON API 返回概览数据"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001"))

    response = test_client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "language_distribution" in data
    assert "trends" in data


def test_stats_partial(client):
    """统计片段返回图表容器"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001"))

    response = test_client.get("/partials/stats")
    assert response.status_code == 200
    assert "维度切换器" in response.text or "按语言" in response.text


def test_stats_api(client):
    """统计 API 按维度返回数据"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))

    response = test_client.get("/api/stats?group_by=language")
    assert response.status_code == 200
    data = response.json()
    assert data["group_by"] == "language"
    assert data["total"] == 1


def test_review_partial(client):
    """复习片段返回待复习清单"""
    test_client, storage = client
    today = datetime.now(timezone.utc).date().isoformat()
    storage.save_vocab(_make_vocab("due", "vocab_001", next_review=today))

    response = test_client.get("/partials/review")
    assert response.status_code == 200
    assert "今日待复习" in response.text


def test_generate_quiz_route(client):
    """出题端点返回考题片段"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001"))

    response = test_client.post("/api/quiz/vocab_001/generate?quiz_type=拼写")
    assert response.status_code == 200
    assert "quiz-container" in response.text
    assert "提交答案" in response.text


def test_grade_quiz_route(client):
    """评分端点返回结果片段"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001"))

    # 生成考题
    response = test_client.post("/api/quiz/vocab_001/generate?quiz_type=拼写")
    assert response.status_code == 200

    # 找到生成的 quiz_id
    quizzes = [storage.load_quiz(qid) for qid in storage.list_all_quiz_ids()]
    assert len(quizzes) == 1
    quiz_id = quizzes[0].id

    response = test_client.post(f"/api/quiz/{quiz_id}/grade?response=hello")
    assert response.status_code == 200
    assert "回答正确" in response.text or "评分" in response.text


def test_generate_quiz_route_unknown_vocab(client):
    """词汇不存在返回 404"""
    test_client, _ = client
    response = test_client.post("/api/quiz/vocab_missing/generate")
    assert response.status_code == 404


# ──────────────────────────────────────────
# 词汇管理路由测试
# ──────────────────────────────────────────

def test_vocab_list_partial(client):
    """词汇列表片段返回筛选表单与词汇卡片"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))

    response = test_client.get("/partials/vocab")
    assert response.status_code == 200
    assert "词汇管理" in response.text
    assert "hello" in response.text


def test_vocab_detail_partial(client):
    """词汇详情片段返回结构化信息"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))

    response = test_client.get("/partials/vocab/vocab_001")
    assert response.status_code == 200
    assert "hello" in response.text
    assert "出题" in response.text


def test_vocab_edit_partial(client):
    """词汇编辑表单包含现有字段"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))

    response = test_client.get("/partials/vocab/vocab_001/edit")
    assert response.status_code == 200
    assert "编辑词汇" in response.text
    assert 'name="word"' in response.text
    assert 'value="hello"' in response.text


def test_vocab_update_route(client):
    """提交编辑表单后返回更新后的详情

    表单 definitions textarea 每行格式：`释义文本|例句1;例句2`
    """
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001", language="en"))

    response = test_client.post(
        "/api/vocab/vocab_001/update",
        data={
            "word": "hi",
            "phonetic": "/haɪ/",
            "part_of_speech": "int.",
            "language": "de",
            # 新格式：释义|例句
            "definitions": "你好|Hi!;Hi there!",
        },
    )
    assert response.status_code == 200
    assert "hi" in response.text
    assert "de" in response.text

    # 确认已持久化（definitions 内嵌 examples）
    reloaded = storage.load_vocab("vocab_001")
    assert reloaded.structured.word == "hi"
    assert reloaded.structured.language == "de"
    assert len(reloaded.structured.definitions) == 1
    assert reloaded.structured.definitions[0].text == "你好"
    assert reloaded.structured.definitions[0].examples == ["Hi!", "Hi there!"]


def test_vocab_delete_route(client):
    """删除词汇后返回列表"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001"))

    response = test_client.delete("/api/vocab/vocab_001")
    assert response.status_code == 200
    assert storage.load_vocab("vocab_001") is None


def test_vocab_detail_unknown_vocab(client):
    """词汇不存在返回 404"""
    test_client, _ = client
    response = test_client.get("/partials/vocab/missing")
    assert response.status_code == 404


# ──────────────────────────────────────────
# 批量复习路由测试
# ──────────────────────────────────────────

def _today_iso():
    """当前 UTC 日期字符串"""
    return datetime.now(timezone.utc).date().isoformat()


def test_start_batch_review_route(client):
    """开始批量复习应返回批量复习页面"""
    test_client, storage = client
    today = _today_iso()
    storage.save_vocab(_make_vocab("hello", "vocab_001", next_review=today))
    storage.save_vocab(_make_vocab("world", "vocab_002", next_review=today))

    response = test_client.post("/api/review/batch/start")
    assert response.status_code == 200
    assert "今日批量复习" in response.text
    assert "第 1 / 2 题" in response.text


def test_start_batch_review_no_due_route(client):
    """无到期词汇时返回复习页并提示"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hello", "vocab_001", next_review="2099-01-01"))

    response = test_client.post("/api/review/batch/start")
    assert response.status_code == 200
    assert "今天没有需要复习的单词" in response.text


def test_batch_review_full_flow(client):
    """批量复习完整流程：开始 → 答题 → 汇总"""
    test_client, storage = client
    today = _today_iso()
    storage.save_vocab(_make_vocab("hello", "vocab_001", next_review=today))
    storage.save_vocab(_make_vocab("world", "vocab_002", next_review=today))

    # 开始
    response = test_client.post("/api/review/batch/start")
    assert response.status_code == 200
    assert "今日批量复习" in response.text

    # 从响应中解析 batch_id（hx-post 链接中）
    import re
    batch_match = re.search(r'/api/review/batch/(batch_[a-f0-9]+)/item/0/grade', response.text)
    assert batch_match is not None
    batch_id = batch_match.group(1)

    # 第一题（hello，拼写题，答案 hello）
    response = test_client.post(f"/api/review/batch/{batch_id}/item/0/grade", data={"response": "hello"})
    assert response.status_code == 200
    assert "第 2 / 2 题" in response.text

    # 第二题（world）
    response = test_client.post(f"/api/review/batch/{batch_id}/item/1/grade", data={"response": "world"})
    assert response.status_code == 200
    assert "复习完成" in response.text
    assert "完成题数" in response.text


def test_batch_review_unknown_item(client):
    """访问不存在的批量复习题目返回 404"""
    test_client, _ = client
    response = test_client.get("/api/review/batch/not_exist/item/0")
    assert response.status_code == 404


# ──────────────────────────────────────────
# N-05 insights 路由测试
# ──────────────────────────────────────────

def test_insights_page_default_language(client):
    """/insights 返回 200，包含语种切换器与 insights-body"""
    test_client, _ = client
    response = test_client.get("/insights")
    assert response.status_code == 200
    assert "语种洞察" in response.text
    assert "language=de" in response.text
    assert "language=zh_classical" in response.text
    assert 'id="insights-body"' in response.text


def test_insights_partial_with_language(client):
    """/partials/insights?language=de 返回 partial HTML"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hallo", "vocab_001", language="de"))
    response = test_client.get("/partials/insights", params={"language": "de"})
    assert response.status_code == 200
    assert "hallo" in response.text or "词汇总量" in response.text or "总数" in response.text


def test_insights_partial_invalid_language_falls_back_to_de(client):
    """非法 language 参数回退到 de"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hallo", "vocab_001", language="de"))
    response = test_client.get("/partials/insights", params={"language": "fr"})
    assert response.status_code == 200
    # 不应崩溃，应回退到 de 并正常渲染
    assert "总数" in response.text or "词汇" in response.text


def test_insights_api_returns_json(client):
    """/api/insights?language=de 返回 JSON"""
    test_client, storage = client
    storage.save_vocab(_make_vocab("hallo", "vocab_001", language="de"))
    response = test_client.get("/api/insights", params={"language": "de"})
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "de"
    assert "kpi" in data
    assert "forgetting_curve" in data
    assert "weak_words" in data
    assert "mastery_distribution" in data
    assert "sample_size_flag" in data


def test_base_page_has_insights_nav_tab(client):
    """base.html 导航栏含'语种洞察' tab，指向 /insights"""
    test_client, _ = client
    response = test_client.get("/")
    assert response.status_code == 200
    assert "语种洞察" in response.text
    assert 'hx-get="/insights"' in response.text
