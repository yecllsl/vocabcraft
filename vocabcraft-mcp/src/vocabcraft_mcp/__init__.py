"""VocabCraft MCP Server - 词汇学习与制作一体"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

try:
    # 单一真相源：pyproject.toml。硬编码副本曾漂移到 0.3.0 而无人察觉。
    __version__ = _pkg_version("vocabcraft-mcp")
except PackageNotFoundError:  # 未安装（如直接从源码树 import）时的兜底
    __version__ = "0.0.0+unknown"
