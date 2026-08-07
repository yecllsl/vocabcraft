# tests/test_server_wiring.py
"""MCP Server 层接线测试

tools/ 层已有充分的业务逻辑测试，本文件**只**验证 server.py 这层薄封装：

    1. 每个 @mcp.tool 包装函数能被真实调用，不因导入/名字遮蔽而崩溃
    2. server 层签名不丢失底层 tool 的参数（防止能力在 MCP 层不可达）

背景：`from ...tools import parse_vocab` 曾被同名包装函数遮蔽，导致
`parse_vocab.parse_vocab(...)` 解析到函数自身，抛
`AttributeError: 'function' object has no attribute 'parse_vocab'`。
这是「拍照录词」主链路入口，但 tools 层测试全绿——因为没人测过 server 层。

同类问题还有 `schedule_review` 在 MCP 层漏传 `language`，使按语种过滤
只有 Web 层能用。故本文件用签名比对做机械防线。
"""

import inspect

import pytest

from vocabcraft_mcp import server
from vocabcraft_mcp.tools import crud, export, quiz, review, statistics, xlsx_import
from vocabcraft_mcp.tools import parse_vocab as parse_vocab_tool


def _unwrap(tool):
    """取出 @mcp.tool 包装下的原始函数（兼容 FastMCP 返回包装对象或原函数）"""
    return getattr(tool, "fn", tool)


def _call(name, *args, **kwargs):
    """按 tool 名调用 server 层包装函数"""
    return _unwrap(getattr(server, name))(*args, **kwargs)


# server 包装函数名 → 底层实现函数
WIRING = [
    ("save_vocab", crud.save_vocab),
    ("query_vocab", crud.query_vocab),
    ("update_vocab", crud.update_vocab),
    ("delete_vocab", crud.delete_vocab),
    ("parse_vocab", parse_vocab_tool.parse_vocab),
    ("schedule_review", review.schedule_review),
    ("generate_quiz", quiz.generate_quiz),
    ("grade_quiz", quiz.grade_quiz),
    ("get_statistics", statistics.get_statistics),
    ("export_data", export.export_data),
    ("import_xlsx_vocab", xlsx_import.import_xlsx_vocab),
]

_IDS = [name for name, _ in WIRING]


@pytest.mark.parametrize(("name", "impl"), WIRING, ids=_IDS)
def test_server_tool_is_callable(name, impl):
    """每个 tool 都已注册为可调用对象（防止导入错误/名字遮蔽）"""
    assert callable(_unwrap(getattr(server, name))), f"{name} 未正确注册"


@pytest.mark.parametrize(("name", "impl"), WIRING, ids=_IDS)
def test_server_signature_covers_impl(name, impl):
    """server 层不得丢失底层 tool 的参数，否则该能力在 MCP 层不可达"""
    exposed = set(inspect.signature(_unwrap(getattr(server, name))).parameters)
    underlying = set(inspect.signature(impl).parameters)
    missing = underlying - exposed
    assert not missing, f"{name} 在 MCP 层丢失参数: {sorted(missing)}"


def test_full_tool_chain_smoke(isolated_storage, make_vocab_data):
    """按真实业务顺序走通全部 11 个 tool，验证 MCP 层接线通畅

    只断言「能调通且无 error」，字段级行为由 tools 层测试负责，避免重复。
    """
    # 1. 解析（曾经崩在这里）
    parsed = _call("parse_vocab", text="apple", language="en")
    assert parsed["mode"] == "text"

    # 2. 保存
    saved = _call("save_vocab", make_vocab_data("hello", "vocab_001"))
    assert "error" not in saved

    # 3. 查询
    assert "error" not in _call("query_vocab", {})

    # 4. 更新
    assert "error" not in _call("update_vocab", {"id": "vocab_001", "structured": {"phonetic": "/x/"}})

    # 5. 排程（含 language 过滤，验证参数确实透传到底层）
    assert "error" not in _call("schedule_review")
    assert "error" not in _call("schedule_review", "", "en")

    # 6. 出题 → 7. 评分
    generated = _call("generate_quiz", "vocab_001")
    assert "error" not in generated
    graded = _call("grade_quiz", generated["quiz_id"], "hello")
    assert "error" not in graded

    # 8. 统计
    # 注意：实现只支持 language/mastery/date/quiz_type，
    # 而 vocabcraft-stats/SKILL.md 教 agent 用 overview/review —— 两者不一致，待修。
    assert "error" not in _call("get_statistics", "mastery")

    # 9. 导出
    assert "error" not in _call("export_data", "json", {})

    # 10. 导入：路径不存在时必须优雅报错，而不是抛异常
    bad_xlsx = _call("import_xlsx_vocab", str(isolated_storage / "missing.xlsx"))
    assert bad_xlsx["errors"], "文件不存在时应在 errors 中报告"

    # 11. 删除
    assert "error" not in _call("delete_vocab", "vocab_001")
