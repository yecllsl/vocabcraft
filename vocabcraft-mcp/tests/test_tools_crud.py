# tests/test_tools_crud.py
"""CRUD Tool 单元测试

验证 save/query/update/delete 真实行为:
    - 自动生成 vocab_id、注入 review_state
    - 查询过滤（language/word 子串）
    - patch 语义更新（合并，未改字段保留）
    - 删除幂等
所有测试通过 monkeypatch 隔离数据目录到 tmp_path，不污染真实 data/。
"""

import pytest

from vocabcraft_mcp.tools.crud import (
    save_vocab, query_vocab, update_vocab, delete_vocab, get_storage,
)
from vocabcraft_mcp.storage import Storage


def _make_vocab_data(word: str = "hello", vocab_id: str | None = None) -> dict:
    """构造测试用词汇数据 dict（definitions 内嵌 examples 新格式）"""
    data = {
        "structured": {
            "word": word,
            "phonetic": "/həˈləʊ/",
            "part_of_speech": "int.",
            "definitions": [
                {"text": "你好", "examples": ["Hello, world!"]},
            ],
            "language": "en",
        },
    }
    if vocab_id:
        data["id"] = vocab_id
    return data


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """隔离数据目录到 tmp_path，避免污染真实 data/"""
    monkeypatch.setattr("vocabcraft_mcp.tools.crud._DEFAULT_DATA_DIR", tmp_path)
    return tmp_path


# ──────────────────────────────────────────
# import 与 get_storage
# ──────────────────────────────────────────

def test_crud_importable():
    """模块可正常 import，函数可调用"""
    assert callable(save_vocab)
    assert callable(query_vocab)
    assert callable(update_vocab)
    assert callable(delete_vocab)


def test_get_storage_returns_storage_instance(tmp_path, monkeypatch):
    """get_storage 返回可用 Storage 实例"""
    monkeypatch.setattr("vocabcraft_mcp.tools.crud._DEFAULT_DATA_DIR", tmp_path)
    s = get_storage()
    assert isinstance(s, Storage)
    assert s.base_dir == tmp_path


# ──────────────────────────────────────────
# save + query 往返
# ──────────────────────────────────────────

def test_save_and_query_roundtrip(isolated_storage):
    """保存后能按 word 查到"""
    result = save_vocab(_make_vocab_data("hello", "vocab_20260723_001"))
    assert result["vocab_id"] == "vocab_20260723_001"

    q = query_vocab({"word": "hello"})
    assert q["total_count"] == 1
    assert q["vocabs"][0]["structured"]["word"] == "hello"


def test_save_auto_generate_id(isolated_storage):
    """未提供 id 时自动生成 vocab_YYYYMMDD_NNN"""
    result = save_vocab(_make_vocab_data("world"))
    assert result["vocab_id"].startswith("vocab_")
    # 自动注入 review_state（含首次排程 next_review）
    v = get_storage().load_vocab(result["vocab_id"])
    assert v.review_state.next_review  # 非空
    assert v.review_state.ease_factor == 2.5  # 新词默认 EF


def test_save_missing_structured_word_returns_error():
    """structured.word 缺失返回 error"""
    result = save_vocab({"structured": {}})
    assert "error" in result


def test_query_by_language(isolated_storage):
    """按 language 过滤"""
    save_vocab(_make_vocab_data("hello", "vocab_001"))
    assert query_vocab({"language": "en"})["total_count"] == 1
    assert query_vocab({"language": "fr"})["total_count"] == 0


def test_query_by_word_substring(isolated_storage):
    """词形模糊匹配（子串包含）"""
    save_vocab(_make_vocab_data("hello", "vocab_001"))
    save_vocab(_make_vocab_data("world", "vocab_002"))
    assert query_vocab({"word": "hell"})["total_count"] == 1
    assert query_vocab({"word": "world"})["total_count"] == 1
    assert query_vocab({})["total_count"] == 2


# ──────────────────────────────────────────
# update（patch 语义）
# ──────────────────────────────────────────

def test_update_vocab_patch_merge(isolated_storage):
    """patch 合并：仅改传入字段，未改字段保留"""
    save_vocab(_make_vocab_data("hello", "vocab_001"))
    result = update_vocab({"id": "vocab_001", "structured": {"part_of_speech": "n."}})
    assert result["vocab_id"] == "vocab_001"

    v = get_storage().load_vocab("vocab_001")
    assert v.structured.part_of_speech == "n."  # 已改
    assert v.structured.word == "hello"  # 未改保留


def test_update_vocab_review_state_only(isolated_storage):
    """仅更新 review_state，不动 structured"""
    save_vocab(_make_vocab_data("hello", "vocab_001"))
    update_vocab({
        "id": "vocab_001",
        "review_state": {"ease_factor": 2.6, "interval": 6, "repetitions": 2, "next_review": "2026-07-30"},
    })
    v = get_storage().load_vocab("vocab_001")
    assert v.review_state.ease_factor == 2.6
    assert v.structured.word == "hello"  # structured 未被动


def test_update_nonexistent_returns_error(isolated_storage):
    """更新不存在的 ID 返回 error"""
    result = update_vocab({"id": "vocab_999", "structured": {"word": "x"}})
    assert "error" in result


def test_update_missing_id_returns_error(isolated_storage):
    """更新缺 id 返回 error"""
    result = update_vocab({"structured": {"word": "x"}})
    assert "error" in result


# ──────────────────────────────────────────
# delete
# ──────────────────────────────────────────

def test_delete_success(isolated_storage):
    """删除后查不到"""
    save_vocab(_make_vocab_data("hello", "vocab_001"))
    assert delete_vocab("vocab_001")["deleted"] is True
    assert query_vocab({})["total_count"] == 0


def test_delete_idempotent(isolated_storage):
    """重复删除返回 deleted=False"""
    save_vocab(_make_vocab_data("hello", "vocab_001"))
    assert delete_vocab("vocab_001")["deleted"] is True
    assert delete_vocab("vocab_001")["deleted"] is False
