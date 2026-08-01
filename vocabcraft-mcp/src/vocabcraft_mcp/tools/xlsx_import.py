# src/vocabcraft_mcp/tools/xlsx_import.py
"""Excel 文件词汇导入 Tool

从 .xlsx 文件批量导入词汇到词汇学习系统。
支持多义词处理、错误跳过、批量保存。
"""
from pathlib import Path

from vocabcraft_mcp.models import normalize_language
from vocabcraft_mcp.tools.crud import save_vocab


def import_xlsx_vocab(
    xlsx_path: str,
    sheet_name: str | None = None,
    language: str = "en",
) -> dict:
    """从 .xlsx 文件批量导入词汇

    Args:
        xlsx_path: .xlsx 文件的本地路径
        sheet_name: 工作表名称，None 则使用第一个工作表
        language: 默认语言代码（支持别名归一化）

    Returns:
        包含以下字段的字典:
        - success_count: 成功导入的词汇数
        - error_count: 失败的词汇数
        - errors: 错误详情列表
        - imported_vocabs: 成功导入的词汇ID列表
    """
    lang = normalize_language(language)
    xlsx_path_obj = Path(xlsx_path)

    if not xlsx_path_obj.exists():
        return {
            "success_count": 0,
            "error_count": 0,
            "errors": [f"文件不存在: {xlsx_path}"],
            "imported_vocabs": [],
        }

    if xlsx_path_obj.suffix.lower() != ".xlsx":
        return {
            "success_count": 0,
            "error_count": 0,
            "errors": [f"文件格式错误: {xlsx_path}，请提供 .xlsx 文件"],
            "imported_vocabs": [],
        }

    try:
        import openpyxl  # type: ignore[import-untyped]  # noqa: WPS433 (懒加载)
    except ImportError as exc:
        raise ImportError(
            "未安装 openpyxl。请运行 `uv sync --extra xlsx` "
            "或 `uv pip install openpyxl` 后重试。"
        ) from exc

    try:
        workbook = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001 - openpyxl raises various exceptions
        return {
            "success_count": 0,
            "error_count": 0,
            "errors": [f"读取 Excel 文件失败: {e!s}"],
            "imported_vocabs": [],
        }

    if sheet_name:
        if sheet_name not in workbook.sheetnames:
            workbook.close()
            return {
                "success_count": 0,
                "error_count": 0,
                "errors": [f"工作表 '{sheet_name}' 不存在，可用工作表: {workbook.sheetnames}"],
                "imported_vocabs": [],
            }
        worksheet = workbook[sheet_name]
    else:
        worksheet = workbook.active

    headers = []
    for cell in next(worksheet.iter_rows(min_row=1, max_row=1, values_only=True)):
        if cell:
            headers.append(str(cell).strip().lower())
        else:
            headers.append("")

    required_columns = {"word", "definitions"}
    if not required_columns.issubset(set(headers)):
        workbook.close()
        missing = required_columns - set(headers)
        return {
            "success_count": 0,
            "error_count": 0,
            "errors": [f"缺少必需列: {missing}，当前列: {headers}"],
            "imported_vocabs": [],
        }

    vocab_groups: dict[tuple[str, str], list[dict]] = {}
    errors: list[str] = []

    for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
        if not row or all(cell is None for cell in row):
            continue

        row_data: dict = {}
        for header, cell in zip(headers, row):
            if header:
                row_data[header] = cell

        word = row_data.get("word")
        def_text_raw = row_data.get("definitions")

        if not word or not str(word).strip():
            errors.append(f"行 {row_idx}: 词汇(word)为空")
            continue

        if not def_text_raw or not str(def_text_raw).strip():
            errors.append(f"行 {row_idx}: 释义(definitions)为空")
            continue

        word = str(word).strip()
        row_language = lang
        if row_data.get("language"):
            row_language = normalize_language(str(row_data["language"]))
        group_key = (word, row_language)
        if group_key not in vocab_groups:
            vocab_groups[group_key] = []
        vocab_groups[group_key].append(row_data)

    workbook.close()

    success_count = 0
    error_count = 0
    imported_vocabs: list[str] = []

    for (word, word_language), rows in vocab_groups.items():
        definitions: list[dict] = []
        phonetic = ""
        part_of_speech = ""

        for row in rows:
            if not phonetic and row.get("phonetic"):
                phonetic = str(row["phonetic"]).strip()
            if not part_of_speech and row.get("part_of_speech"):
                part_of_speech = str(row["part_of_speech"]).strip()

            def_text = str(row.get("definitions", "")).strip()
            if def_text:
                examples_raw = row.get("examples", "")
                if examples_raw:
                    examples = [
                        e.strip()
                        for e in str(examples_raw).replace("；", "\n").replace(";", "\n").split("\n")
                        if e.strip()
                    ]
                else:
                    examples = []

                definitions.append({
                    "text": def_text,
                    "examples": examples,
                })

        vocab_data = {
            "structured": {
                "word": word,
                "phonetic": phonetic,
                "part_of_speech": part_of_speech,
                "definitions": definitions,
                "language": word_language,
            }
        }

        result = save_vocab(vocab_data)
        if "error" in result:
            error_count += 1
            errors.append(f"词汇 '{word}' 保存失败: {result['error']}")
        else:
            success_count += 1
            imported_vocabs.append(result.get("vocab_id", ""))

    return {
        "success_count": success_count,
        "error_count": error_count,
        "errors": errors,
        "imported_vocabs": imported_vocabs,
    }
