# tests/test_storage.py
"""JSON 存储引擎单元测试

验证 Storage 基础 CRUD、原子写、查询过滤、部分更新可正常工作。
"""

import json
import pytest
from datetime import datetime, timezone

from vocabcraft_mcp.storage import Storage, _deep_merge
from vocabcraft_mcp.models import VocabRecord, StructuredVocab, Definition


@pytest.fixture
def tmp_storage(tmp_path):
    return Storage(base_dir=tmp_path)


def _make_vocab(vocab_id: str = "vocab_20260723_001") -> VocabRecord:
    """构造测试用词汇记录（definitions 内嵌 examples 新格式）"""
    now = datetime(2026, 7, 23, 10, 30, tzinfo=timezone.utc)
    return VocabRecord(
        id=vocab_id,
        structured=StructuredVocab(
            word="hello", phonetic="/həˈləʊ/", part_of_speech="int.",
            language="en",
            definitions=[Definition(text="你好", examples=["Hello, world!"])],
        ),
        created_at=now, updated_at=now,
    )


def test_save_and_load(tmp_storage):
    """保存后能正确加载"""
    result = tmp_storage.save_vocab(_make_vocab())
    assert result["vocab_id"] == "vocab_20260723_001"
    loaded = tmp_storage.load_vocab("vocab_20260723_001")
    assert loaded is not None
    assert loaded.structured.word == "hello"


def test_load_nonexistent(tmp_storage):
    """加载不存在的 ID 返回 None"""
    assert tmp_storage.load_vocab("vocab_99999999_999") is None


def test_delete(tmp_storage):
    """删除后无法再加载"""
    tmp_storage.save_vocab(_make_vocab())
    assert tmp_storage.delete_vocab("vocab_20260723_001") is True
    assert tmp_storage.load_vocab("vocab_20260723_001") is None
    # 重复删除返回 False
    assert tmp_storage.delete_vocab("vocab_20260723_001") is False


def test_list_all_vocab_ids(tmp_storage):
    """列出所有词汇 ID"""
    tmp_storage.save_vocab(_make_vocab("vocab_001"))
    tmp_storage.save_vocab(_make_vocab("vocab_002"))
    ids = tmp_storage.list_all_vocab_ids()
    assert set(ids) == {"vocab_001", "vocab_002"}


def test_query_by_language(tmp_storage):
    """按 language 过滤（匹配 structured.language）"""
    tmp_storage.save_vocab(_make_vocab())
    assert tmp_storage.query_vocabs(filters={"language": "en"})["total_count"] == 1
    assert tmp_storage.query_vocabs(filters={"language": "fr"})["total_count"] == 0


def test_query_by_word_substring(tmp_storage):
    """词形模糊匹配（structured.word 子串包含）"""
    tmp_storage.save_vocab(_make_vocab())
    assert tmp_storage.query_vocabs(filters={"word": "hell"})["total_count"] == 1
    assert tmp_storage.query_vocabs(filters={"word": "world"})["total_count"] == 0


def test_patch_vocab_partial_update(tmp_storage):
    """部分更新：嵌套字段 structured.part_of_speech"""
    tmp_storage.save_vocab(_make_vocab())
    updated = tmp_storage.patch_vocab(
        "vocab_20260723_001",
        {"structured": {"part_of_speech": "n."}},
    )
    assert updated is not None
    assert updated.structured.part_of_speech == "n."
    # 未修改的字段保留原值
    assert updated.structured.word == "hello"


def test_patch_nonexistent(tmp_storage):
    """patch 不存在的 ID 返回 None"""
    assert tmp_storage.patch_vocab("vocab_99999999_999", {"x": 1}) is None


def test_atomic_write_no_tmp_residue(tmp_storage):
    """原子写完成后不留 .tmp 残留"""
    tmp_storage.save_vocab(_make_vocab())
    tmp_files = list(tmp_storage.vocabs_dir.glob("*.tmp"))
    assert tmp_files == []


def test_deep_merge():
    """递归合并：嵌套 dict 合并，非 dict 覆盖"""
    base = {"a": 1, "b": {"x": 10, "y": 20}, "c": 3}
    patch = {"b": {"y": 99, "z": 30}, "d": 4}
    merged = _deep_merge(base, patch)
    assert merged == {"a": 1, "b": {"x": 10, "y": 99, "z": 30}, "c": 3, "d": 4}


def test_query_vocabs_handles_mixed_naive_and_aware_datetimes(tmp_storage):
    """query_vocabs 排序时，created_at 混合 offset-naive 与 offset-aware 不应抛错

    复现 /partials/vocab 500 错误：历史脏数据（如 xlsx 批量导入或外部脚本）
    写入了无时区的 ISO 字符串，正常路径（_now_utc）写入的是带 Z 的 ISO 字符串。
    Pydantic 反序列化后分别为 naive 与 aware datetime，直接用 datetime 对象
    比较会触发 TypeError。修复后 sort 走字符串比较，行为与时间序一致。
    """
    # 直接写两份 JSON：一份 naive，一份 aware（模拟历史脏数据）
    aware_iso = "2026-07-23T10:30:00.000000Z"  # offset-aware
    naive_iso = "2026-07-23T11:00:00.000000"    # offset-naive

    (tmp_storage.vocabs_dir / "vocab_20260723_001.json").write_text(
        json.dumps({
            "id": "vocab_20260723_001",
            "structured": {"word": "aware", "definitions": [], "language": "en"},
            "review_state": {"next_review": ""},
            "created_at": aware_iso,
            "updated_at": aware_iso,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    (tmp_storage.vocabs_dir / "vocab_20260723_002.json").write_text(
        json.dumps({
            "id": "vocab_20260723_002",
            "structured": {"word": "naive", "definitions": [], "language": "en"},
            "review_state": {"next_review": ""},
            "created_at": naive_iso,
            "updated_at": naive_iso,
        }, ensure_ascii=False),
        encoding="utf-8",
    )

    # 不应抛 TypeError；按 created_at 倒序，naive (11:00) 排第一
    result = tmp_storage.query_vocabs(filters={})
    assert result["total_count"] == 2
    assert [v["id"] for v in result["vocabs"]] == [
        "vocab_20260723_002",  # naive 11:00
        "vocab_20260723_001",  # aware 10:30
    ]
