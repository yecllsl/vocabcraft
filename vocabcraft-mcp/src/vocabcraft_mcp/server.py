# src/vocabcraft_mcp/server.py
"""VocabCraft MCP Server 入口

注册所有 MCP 工具（4 个 CRUD + 7 个业务工具），通过 FastMCP 框架对外提供服务。
业务工具模块使用懒导入（函数体内 import），确保 server.py 本身可正常加载，
后续 Task 可逐个替换 NotImplementedError 实现而不影响 server 注册。

业务流程: 拍照 → OCR → 结构化解析 → 保存词汇 → 遗忘曲线排程 → 到期提醒 → 出考题 → 评分 → 更新记忆状态
"""

from fastmcp import FastMCP

mcp = FastMCP(name="vocabcraft-mcp", instructions="词汇学习与制作MCP Server")


# ──────────────────────────────────────────
# CRUD 工具（懒导入）
# ──────────────────────────────────────────

@mcp.tool()
def save_vocab(vocab_data: dict) -> dict:
    """保存词汇记录到本地 JSON 文件"""
    from vocabcraft_mcp.tools.crud import save_vocab as _save
    return _save(vocab_data)


@mcp.tool()
def query_vocab(filters: dict) -> dict:
    """按条件查询词汇"""
    from vocabcraft_mcp.tools.crud import query_vocab as _query
    return _query(filters)


@mcp.tool()
def update_vocab(vocab_data: dict) -> dict:
    """更新词汇记录"""
    from vocabcraft_mcp.tools.crud import update_vocab as _update
    return _update(vocab_data)


@mcp.tool()
def delete_vocab(vocab_id: str) -> dict:
    """删除词汇记录"""
    from vocabcraft_mcp.tools.crud import delete_vocab as _delete
    return _delete(vocab_id)


# ──────────────────────────────────────────
# 业务工具（懒导入，后续 Task 逐个实现）
# ──────────────────────────────────────────

@mcp.tool()
def ocr_recognize(image_path: str, language: str = "") -> dict:
    """OCR 识别词汇图片，返回原始文本"""
    from vocabcraft_mcp.tools.ocr_recognize import ocr_recognize as _ocr
    return _ocr(image_path, language)


@mcp.tool()
def parse_vocab(image_path: str = "", ocr_text: str = "", language: str = "") -> dict:
    """AI 结构化解析词汇（词形/音标/词性/释义/例句）"""
    from vocabcraft_mcp.tools.parse_vocab import parse_vocab as _parse
    return _parse(image_path, ocr_text, language)


@mcp.tool()
def schedule_review(vocab_id: str = "") -> dict:
    """基于遗忘曲线生成复习计划"""
    from vocabcraft_mcp.tools.review import schedule_review as _sched
    return _sched(vocab_id)


@mcp.tool()
def generate_quiz(vocab_id: str, quiz_type: str = "") -> dict:
    """为指定词汇生成考题（选择/填空/拼写/释义）"""
    from vocabcraft_mcp.tools.quiz import generate_quiz as _gen
    return _gen(vocab_id, quiz_type)


@mcp.tool()
def grade_quiz(quiz_id: str, response: str) -> dict:
    """评分并按 SM-2 更新词汇记忆状态"""
    from vocabcraft_mcp.tools.quiz import grade_quiz as _grade
    return _grade(quiz_id, response)


@mcp.tool()
def get_statistics(group_by: str) -> dict:
    """统计词汇量、掌握度、题型分布"""
    from vocabcraft_mcp.tools.statistics import get_statistics as _stats
    return _stats(group_by)


@mcp.tool()
def export_data(format: str = "json", filters: dict = None) -> dict:
    """导出词汇数据为 JSON/CSV"""
    from vocabcraft_mcp.tools.export import export_data as _export
    return _export(format, filters or {})


def main():
    """启动 MCP Server（stdio 传输模式）"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
