# tests/test_tools_export.py
"""导出 Tool 单元测试

验证 export_data 真实行为:
    - JSON 导出文件可正确解析，含完整 structured + review_state
    - CSV 导出含表头与数据行，utf-8-sig BOM 兼容 Excel
    - 过滤条件下导出
    - 空数据导出空集合
    - 不支持格式返回 error
"""

import csv
import json

from vocabcraft_mcp.tools.crud import save_vocab
from vocabcraft_mcp.tools.export import export_data


def test_export_importable():
    """模块可正常 import"""
    assert callable(export_data)


def test_export_json(isolated_storage, make_vocab_data):
    """JSON 导出文件可正确解析"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    save_vocab(make_vocab_data("world", "vocab_002"))

    result = export_data("json")
    assert result["total_exported"] == 2
    assert result["file_path"].endswith(".json")

    with open(result["file_path"], encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2
    # 完整记录含 structured + review_state
    assert "structured" in data[0]
    assert "review_state" in data[0]
    assert data[0]["structured"]["word"] in {"hello", "world"}


def test_export_csv(isolated_storage, make_vocab_data):
    """CSV 导出含表头与数据行"""
    save_vocab(make_vocab_data("hello", "vocab_001"))

    result = export_data("csv")
    assert result["total_exported"] == 1
    assert result["file_path"].endswith(".csv")

    # utf-8-sig BOM 兼容 Excel
    with open(result["file_path"], encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 1
    assert rows[0]["word"] == "hello"
    assert rows[0]["id"] == "vocab_001"
    assert "ease_factor" in rows[0]  # 扁平化字段


def test_export_with_filters(isolated_storage, make_vocab_data):
    """过滤条件下导出"""
    save_vocab(make_vocab_data("hello", "vocab_001", language="en"))
    save_vocab(make_vocab_data("bonjour", "vocab_002", language="fr"))

    result = export_data("json", {"language": "en"})
    assert result["total_exported"] == 1
    with open(result["file_path"], encoding="utf-8") as f:
        data = json.load(f)
    assert data[0]["structured"]["word"] == "hello"


def test_export_empty_storage(isolated_storage):
    """空数据导出 total_exported=0"""
    result = export_data("json")
    assert result["total_exported"] == 0
    with open(result["file_path"], encoding="utf-8") as f:
        data = json.load(f)
    assert data == []


def test_export_invalid_format_returns_error(isolated_storage):
    """不支持格式返回 error"""
    result = export_data("xml")
    assert "error" in result


def test_export_does_not_mutate_original(isolated_storage, make_vocab_data):
    """导出不损坏原数据：导出后仍能查到"""
    save_vocab(make_vocab_data("hello", "vocab_001"))
    export_data("json")
    export_data("csv")

    from vocabcraft_mcp.tools.crud import query_vocab
    assert query_vocab({})["total_count"] == 1
