"""从 .xlsx 文件批量导入词汇到词汇学习系统

用法:
    uv run python scripts/import_xlsx.py <文件或目录路径> [选项]

示例:
    # 导入单个文件
    uv run python scripts/import_xlsx.py data/images/61.xlsx

    # 导入目录下所有 .xlsx 文件
    uv run python scripts/import_xlsx.py data/images/

    # 指定语言
    uv run python scripts/import_xlsx.py data/images/61.xlsx -l zh_classical

    # 指定工作表
    uv run python scripts/import_xlsx.py data/images/61.xlsx -s Sheet1

    # 预览模式（不实际保存）
    uv run python scripts/import_xlsx.py data/images/61.xlsx -n
"""
import argparse
import json
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，确保能直接 import
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from vocabcraft_mcp.tools.xlsx_import import import_xlsx_vocab  # noqa: E402


def _format_summary(results: list[dict], file_names: list[str]) -> str:
    """格式化导入结果摘要"""
    total_success = sum(r["success_count"] for r in results)
    total_error = sum(r["error_count"] for r in results)
    lines = ["=" * 60, "导入结果摘要", "=" * 60]
    for fname, result in zip(file_names, results):
        status = "✓" if result["error_count"] == 0 else "✗"
        ids = ", ".join(result["imported_vocabs"]) if result["imported_vocabs"] else "-"
        errs = "; ".join(result["errors"]) if result["errors"] else ""
        lines.append(f"  {status} {fname}")
        lines.append(f"     成功: {result['success_count']}  |  失败: {result['error_count']}")
        lines.append(f"     ID: {ids}")
        if errs:
            lines.append(f"     错误: {errs}")
        lines.append("")
    lines.append(f"总计: 成功 {total_success} 个词汇, 失败 {total_error} 个")
    lines.append("=" * 60)
    return "\n".join(lines)


def import_single(path: str, language: str, sheet_name: str | None, dry_run: bool) -> dict:
    """导入单个 .xlsx 文件"""
    path_obj = Path(path)
    if not path_obj.exists():
        return {"success_count": 0, "error_count": 1, "errors": [f"文件不存在: {path}"], "imported_vocabs": []}
    if path_obj.suffix.lower() != ".xlsx":
        return {"success_count": 0, "error_count": 1, "errors": [f"非 .xlsx 文件: {path}"], "imported_vocabs": []}

    if dry_run:
        # 预览模式：只解析不保存
        import openpyxl
        wb = openpyxl.load_workbook(str(path_obj), read_only=True, data_only=True)
        ws = wb[sheet_name] if sheet_name else wb.active
        # 读取前 20 行展示结构
        lines = []
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= 20:
                break
            lines.append([str(c)[:40] if c is not None else "" for c in (row or [])])
        wb.close()
        print(f"--- 预览: {path_obj.name} (前 {min(len(lines), 20)} 行) ---")
        for l in lines:
            print(f"  {l}")
        print()
        # 返回模拟结果
        return {"success_count": 0, "error_count": 0, "errors": [], "imported_vocabs": ["(预览模式，未保存)"]}

    return import_xlsx_vocab(str(path_obj), sheet_name=sheet_name, language=language)


def import_directory(
    directory: str,
    language: str,
    sheet_name: str | None,
    dry_run: bool,
    recursive: bool = False,
) -> tuple[list[dict], list[str]]:
    """导入目录下所有 .xlsx 文件"""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return [{"success_count": 0, "error_count": 1, "errors": [f"目录不存在: {directory}"], "imported_vocabs": []}], [directory]

    pattern = "**/*.xlsx" if recursive else "*.xlsx"
    files = sorted(dir_path.glob(pattern))
    if not files:
        return [{"success_count": 0, "error_count": 0, "errors": [f"目录 '{directory}' 下没有 .xlsx 文件"], "imported_vocabs": []}], [directory]

    results = []
    names = []
    for f in files:
        print(f"正在导入: {f.name} ...", end=" ", flush=True)
        result = import_single(str(f), language, sheet_name, dry_run)
        results.append(result)
        names.append(f.name)
        if result["error_count"] == 0:
            print(f"✓ 成功 ({result['success_count']} 个)")
        else:
            print(f"✗ 失败 ({'; '.join(result['errors'])})")
    return results, names


def main():
    parser = argparse.ArgumentParser(
        description="从 .xlsx 文件导入词汇到 VocabCraft 系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("path", help=".xlsx 文件路径或包含 .xlsx 文件的目录路径")
    parser.add_argument("-l", "--language", default="zh_classical", help="语言代码（默认: zh_classical）")
    parser.add_argument("-s", "--sheet", default=None, help="工作表名称（默认: 第一个工作表）")
    parser.add_argument("-n", "--dry-run", action="store_true", help="预览模式，只解析不保存")
    parser.add_argument("-r", "--recursive", action="store_true", help="递归扫描子目录（与目录模式配合使用）")

    args = parser.parse_args()
    input_path = args.path

    if Path(input_path).is_dir():
        results, file_names = import_directory(
            input_path, args.language, args.sheet, args.dry_run, args.recursive,
        )
    else:
        result = import_single(input_path, args.language, args.sheet, args.dry_run)
        results = [result]
        file_names = [Path(input_path).name]

    print()
    print(_format_summary(results, file_names))

    # 非零退出码表示有失败
    total_error = sum(r["error_count"] for r in results)
    sys.exit(1 if total_error > 0 else 0)


if __name__ == "__main__":
    main()