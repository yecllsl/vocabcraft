# src/vocabcraft_mcp/server.py
"""VocabCraft MCP Server 入口

注册所有 MCP 工具（4 个 CRUD + 6 个业务工具），通过 FastMCP 框架对外提供服务。

业务流程: 拍照 → 结构化解析 → 保存词汇 → 遗忘曲线排程 → 到期提醒 → 出考题 → 评分 → 更新记忆状态
"""

from fastmcp import FastMCP

from vocabcraft_mcp.tools import crud, parse_vocab, review, quiz, statistics, export

mcp = FastMCP(name="vocabcraft-mcp", instructions="词汇学习与制作MCP Server")


# ──────────────────────────────────────────
# CRUD 工具
# ──────────────────────────────────────────

@mcp.tool()
def save_vocab(vocab_data: dict) -> dict:
    """保存词汇记录到本地 JSON 文件"""
    return crud.save_vocab(vocab_data)


@mcp.tool()
def query_vocab(filters: dict) -> dict:
    """按条件查询词汇"""
    return crud.query_vocab(filters)


@mcp.tool()
def update_vocab(vocab_data: dict) -> dict:
    """更新词汇记录"""
    return crud.update_vocab(vocab_data)


@mcp.tool()
def delete_vocab(vocab_id: str) -> dict:
    """删除词汇记录"""
    return crud.delete_vocab(vocab_id)


# ──────────────────────────────────────────
# 业务工具
# ──────────────────────────────────────────

@mcp.tool()
def parse_vocab(image_path: str = "", ocr_text: str = "", language: str = "en") -> dict:
    """AI 结构化解析词汇（词形/音标/词性/释义/例句）。
    三模式优先级：对话多模态（无参数）> 本地路径多模态（image_path）> OCR 文本（ocr_text）。"""
    return parse_vocab.parse_vocab(image_path, ocr_text, language)


@mcp.tool()
def schedule_review(vocab_id: str = "") -> dict:
    """基于遗忘曲线生成复习计划"""
    return review.schedule_review(vocab_id)


@mcp.tool()
def generate_quiz(vocab_id: str, quiz_type: str = "") -> dict:
    """为指定词汇生成考题（选择/填空/拼写/释义）"""
    return quiz.generate_quiz(vocab_id, quiz_type)


@mcp.tool()
def grade_quiz(quiz_id: str, response: str) -> dict:
    """评分并按 SM-2 更新词汇记忆状态"""
    return quiz.grade_quiz(quiz_id, response)


@mcp.tool()
def get_statistics(group_by: str) -> dict:
    """统计词汇量、掌握度、题型分布"""
    return statistics.get_statistics(group_by)


@mcp.tool()
def export_data(format: str = "json", filters: dict = None) -> dict:
    """导出词汇数据为 JSON/CSV"""
    return export.export_data(format, filters or {})


@mcp.tool()
def import_xlsx_vocab(
    xlsx_path: str,
    sheet_name: str = "",
    language: str = "en",
) -> dict:
    """从 .xlsx 文件批量导入词汇"""
    from vocabcraft_mcp.tools.xlsx_import import import_xlsx_vocab as _import
    return _import(xlsx_path, sheet_name or None, language)


def main():
    """启动 MCP Server（stdio 传输模式）"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()