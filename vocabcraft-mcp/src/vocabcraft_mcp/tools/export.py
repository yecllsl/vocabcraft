# src/vocabcraft_mcp/tools/export.py
"""数据导出 Tool

支持将词汇数据导出为 JSON 或 CSV 格式文件。
导出文件落在 data/exports/ 目录，文件名带时间戳避免覆盖。

格式说明:
    - json: 完整记录（含 structured + review_state），用于备份/迁移回本工具
    - csv: 扁平化核心字段，utf-8-sig BOM 兼容 Excel 直接打开

导出前确认由 command/skill 层负责（vocabcraft-data-safety-rules.md），
本工具层只执行导出动作。
"""
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path

from vocabcraft_mcp.tools.crud import get_storage

# 默认数据目录：与 crud.py 一致
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"

# 支持的导出格式
_VALID_FORMATS = {"json", "csv"}


def _json_default(o):
    """JSON 序列化兜底：datetime/date 转 ISO 字符串

    storage.query_vocabs 返回 model_dump()，created_at/updated_at 为 datetime 对象，
    json.dumps 默认无法序列化，需兜底转 ISO 字符串。
    """
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")

# CSV 扁平化字段顺序（核心字段，便于 Excel 查看）
_CSV_FIELDS = [
    "id", "word", "phonetic", "part_of_speech", "definitions",
    "language", "ease_factor", "interval", "repetitions", "next_review",
    "created_at", "updated_at",
]


def _flatten_vocab(v: dict) -> dict:
    """将嵌套词汇记录扁平化为 CSV 单行

    structured.* 与 review_state.* 提升到顶层；definitions 取每项 text 用分号连接。
    definitions 为 list[Definition]（每项 {text, examples}），CSV 仅导出释义文本，
    例句与释义的关联保留在 JSON 导出中。
    """
    s = v.get("structured", {})
    r = v.get("review_state", {})
    defs = s.get("definitions", [])
    return {
        "id": v.get("id", ""),
        "word": s.get("word", ""),
        "phonetic": s.get("phonetic", ""),
        "part_of_speech": s.get("part_of_speech", ""),
        "definitions": "; ".join(d.get("text", "") for d in defs),
        "language": s.get("language", ""),
        "ease_factor": r.get("ease_factor", ""),
        "interval": r.get("interval", ""),
        "repetitions": r.get("repetitions", ""),
        "next_review": r.get("next_review", ""),
        "created_at": v.get("created_at", ""),
        "updated_at": v.get("updated_at", ""),
    }


def export_data(format: str = "json", filters: dict = None) -> dict:
    """导出词汇数据到文件

    Args:
        format: 导出格式，"json" 或 "csv"
        filters: 过滤条件字典，同 query_vocab 的 filters（None 或 {} 表示全量）

    Returns:
        包含 file_path 和 total_exported 的字典；格式不支持返回 error
    """
    if format not in _VALID_FORMATS:
        return {"error": f"不支持的格式: {format}，支持 {sorted(_VALID_FORMATS)}"}

    storage = get_storage()
    vocabs = storage.query_vocabs(filters or {})["vocabs"]

    exports_dir = _DEFAULT_DATA_DIR / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if format == "json":
        fp = exports_dir / f"vocabs_{timestamp}.json"
        fp.write_text(
            json.dumps(vocabs, ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )
    else:  # csv
        fp = exports_dir / f"vocabs_{timestamp}.csv"
        # utf-8-sig BOM 让 Excel 正确识别 UTF-8
        with open(fp, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
            writer.writeheader()
            for v in vocabs:
                writer.writerow(_flatten_vocab(v))

    return {"file_path": str(fp), "total_exported": len(vocabs)}
