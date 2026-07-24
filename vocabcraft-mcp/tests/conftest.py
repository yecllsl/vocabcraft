# tests/conftest.py
"""Pytest 共享 fixture

isolated_storage: 将 crud 与 export 的 _DEFAULT_DATA_DIR 同时指向 tmp_path，
                  保证 tools 测试不污染真实 data/ 目录。
"""

import pytest


@pytest.fixture
def isolated_storage(tmp_path, monkeypatch):
    """隔离数据目录到 tmp_path

    crud 与 export 各自持有 _DEFAULT_DATA_DIR 模块变量，
    需同时 monkeypatch 才能完全隔离（export 用于 exports/ 目录）。
    """
    monkeypatch.setattr("vocabcraft_mcp.tools.crud._DEFAULT_DATA_DIR", tmp_path)
    monkeypatch.setattr("vocabcraft_mcp.tools.export._DEFAULT_DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def make_vocab_data():
    """构造测试用词汇数据 dict 的工厂

    definitions 采用新格式 list[Definition dict]（每项 {text, examples}），
    例句内嵌到对应释义，体现"释义 ↔ 例句"关联。
    """
    def _make(word: str = "hello", vocab_id: str | None = None, language: str = "en") -> dict:
        data = {
            "structured": {
                "word": word,
                "phonetic": "/həˈləʊ/",
                "part_of_speech": "int.",
                "definitions": [
                    {"text": "你好", "examples": ["Hello, world!"]},
                ],
                "language": language,
            },
        }
        if vocab_id:
            data["id"] = vocab_id
        return data
    return _make
