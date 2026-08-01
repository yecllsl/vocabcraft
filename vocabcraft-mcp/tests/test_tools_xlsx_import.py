# tests/test_tools_xlsx_import.py
"""xlsx_import Tool 单元测试

验证 import_xlsx_vocab 真实行为:
    - 文件验证（不存在/格式错误/openpyxl缺失）
    - Excel读取（工作表不存在/缺少必需列）
    - 数据解析（空字段/多义词合并/例句解析）
    - 批量保存（成功计数/错误计数/词汇ID列表）
所有测试通过 monkeypatch 隔离数据目录到 tmp_path，不污染真实 data/。
"""

import pytest

from vocabcraft_mcp.tools.xlsx_import import import_xlsx_vocab


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """隔离数据目录到 tmp_path"""
    monkeypatch.setattr("vocabcraft_mcp.tools.crud._DEFAULT_DATA_DIR", tmp_path)
    return tmp_path


def _create_xlsx(tmp_path, filename, headers, rows):
    """创建测试用 xlsx 文件"""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    path = tmp_path / filename
    wb.save(path)
    wb.close()
    return path


# ──────────────────────────────────────────
# 文件验证
# ──────────────────────────────────────────

def test_import_xlsx_not_exists(isolated_storage):
    """文件不存在返回错误"""
    result = import_xlsx_vocab("/nonexistent/file.xlsx")
    assert result["success_count"] == 0
    assert result["error_count"] == 0
    assert "文件不存在" in result["errors"][0]


def test_import_xlsx_wrong_extension(isolated_storage):
    """非 .xlsx 文件返回错误"""
    path = isolated_storage / "test.txt"
    path.write_text("hello")
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 0
    assert "文件格式错误" in result["errors"][0]


def test_import_xlsx_openpyxl_not_installed(isolated_storage):
    """openpyxl 未安装时抛出 ImportError"""
    import sys
    # Create a dummy .xlsx file so file validation passes
    dummy = isolated_storage / "dummy.xlsx"
    dummy.write_bytes(b"fake")

    # Temporarily remove openpyxl from sys.modules
    saved = sys.modules.pop("openpyxl", None)
    sys.modules["openpyxl"] = None  # type: ignore[assignment]
    try:
        with pytest.raises(ImportError, match="openpyxl"):
            import_xlsx_vocab(str(dummy))
    finally:
        if saved is not None:
            sys.modules["openpyxl"] = saved
        else:
            sys.modules.pop("openpyxl", None)


# ──────────────────────────────────────────
# Excel 读取
# ──────────────────────────────────────────

def test_import_xlsx_sheet_not_found(isolated_storage):
    """工作表不存在返回错误"""
    path = _create_xlsx(isolated_storage, "test.xlsx", ["word", "definitions"], [])
    result = import_xlsx_vocab(str(path), sheet_name="NonExistent")
    assert result["success_count"] == 0
    assert "工作表" in result["errors"][0]


def test_import_xlsx_missing_required_columns(isolated_storage):
    """缺少必需列返回错误"""
    path = _create_xlsx(isolated_storage, "test.xlsx", ["word", "phonetic"], [])
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 0
    assert "缺少必需列" in result["errors"][0]


# ──────────────────────────────────────────
# 数据解析
# ──────────────────────────────────────────

def test_import_xlsx_empty_word(isolated_storage):
    """空词汇行被跳过"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions"],
        [
            ["", "definition1"],
            ["word2", "definition2"],
        ],
    )
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 1
    assert len(result["errors"]) == 1
    assert "词汇(word)为空" in result["errors"][0]


def test_import_xlsx_empty_definitions(isolated_storage):
    """空释义行被跳过"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions"],
        [
            ["word1", ""],
            ["word2", "definition2"],
        ],
    )
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 1
    assert len(result["errors"]) == 1
    assert "释义(definitions)为空" in result["errors"][0]


def test_import_xlsx_single_vocab(isolated_storage):
    """单个词汇成功导入"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions", "phonetic", "part_of_speech", "examples"],
        [
            ["hello", "你好", "/həˈloʊ/", "int.", "Hello, world!"],
        ],
    )
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 1
    assert result["error_count"] == 0
    assert len(result["imported_vocabs"]) == 1
    assert result["imported_vocabs"][0].startswith("vocab_")


def test_import_xlsx_multiple_definitions_same_word(isolated_storage):
    """同一词汇多义项合并"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions", "examples"],
        [
            ["bank", "银行", "I went to the bank."],
            ["bank", "河岸", "We sat by the river bank."],
        ],
    )
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 1
    assert result["error_count"] == 0


def test_import_xlsx_examples_parsing(isolated_storage):
    """例句分号分隔正确解析"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions", "examples"],
        [
            ["hello", "你好", "Hello!;How are you?;你好吗"],
        ],
    )
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 1


def test_import_xlsx_skip_empty_rows(isolated_storage):
    """空行被跳过"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions"],
        [
            ["hello", "你好"],
            [None, None],
            ["world", "世界"],
        ],
    )
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 2


def test_import_xlsx_language_override(isolated_storage):
    """行级语言覆盖"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions", "language"],
        [
            ["hello", "你好", "zh"],
            ["world", "世界", "en"],
        ],
    )
    result = import_xlsx_vocab(str(path), language="en")
    assert result["success_count"] == 2


def test_import_xlsx_duplicate_word_same_language(isolated_storage):
    """相同 (word, language) 行合并为一个词汇条目"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions", "language"],
        [
            ["hello", "你好", "en"],
            ["hello", "Hello!", "en"],
        ],
    )
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 1
    assert result["error_count"] == 0


def test_import_xlsx_duplicate_word_different_language(isolated_storage):
    """相同 word 不同 language 保持独立条目"""
    path = _create_xlsx(
        isolated_storage, "test.xlsx",
        ["word", "definitions", "language"],
        [
            ["hello", "你好", "zh"],
            ["hello", "greeting", "en"],
        ],
    )
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 2
    assert result["error_count"] == 0
    assert len(result["imported_vocabs"]) == 2


def test_import_xlsx_empty_file(isolated_storage):
    """空 Excel 文件（仅表头无数据）"""
    path = _create_xlsx(isolated_storage, "test.xlsx", ["word", "definitions"], [])
    result = import_xlsx_vocab(str(path))
    assert result["success_count"] == 0
    assert result["error_count"] == 0
    assert result["errors"] == []
    assert result["imported_vocabs"] == []
