#!/usr/bin/env python3
"""版本一致性校验 —— AGENTS.md「质量与合规规则 > 文档」的机械防线

真相源：`vocabcraft-mcp/pyproject.toml` 的 `[project].version`。

校验项：
    1. CHANGELOG.md 最新条目版本
    2. README.md / DEPLOY.md 中的发行包名 `VocabCraft-vX.Y.Z.*`
    3. README.md / DEPLOY.md 中的 `build-release.{ps1,sh}` 示例版本参数
    4. （可选 --tag）发布 tag 与真相源一致，防止打错 tag

背景：`__init__.py` 的硬编码 `__version__` 曾停在 0.3.0，而 pyproject 已到 0.5.1，
漂移 5 个版本无人察觉——因为没有任何机制校验它。该副本现已改为
`importlib.metadata` 动态读取；文档中的版本引用则由本脚本兜底。

用法：
    python scripts/check_version.py              # 校验文档
    python scripts/check_version.py --tag v0.5.1 # 额外校验发布 tag
退出码：0 全部一致；1 存在不一致。
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "vocabcraft-mcp" / "pyproject.toml"

# 只匹配确定指向本项目版本的位置，避免把依赖约束（如 fastmcp>=3.0.0）当成误报
PATTERNS: list[tuple[str, str]] = [
    # dist/VocabCraft-v0.5.1.zip / VocabCraft-v0.5.1.tar.zst
    (r"VocabCraft-v(\d+\.\d+\.\d+)", "发行包名"),
    # build-release.ps1 -Version 0.5.1 / build-release.sh 0.5.1
    (r"build-release\.(?:ps1|sh)(?:\s+-Version)?\s+(\d+\.\d+\.\d+)", "构建命令示例"),
]

DOCS = ["README.md", "DEPLOY.md", "QUICKSTART.md"]


def source_version() -> str:
    """从 pyproject.toml 读取真相源版本"""
    with PYPROJECT.open("rb") as f:
        return tomllib.load(f)["project"]["version"]


def changelog_version() -> str | None:
    """取 CHANGELOG.md 中最新的 `## [X.Y.Z]` 条目"""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", text, re.MULTILINE)
    return m.group(1) if m else None


def scan_docs(expected: str) -> list[str]:
    """扫描文档中的版本引用，返回不一致项描述"""
    problems: list[str] = []
    for name in DOCS:
        path = ROOT / name
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for pattern, label in PATTERNS:
                for found in re.findall(pattern, line):
                    if found != expected:
                        problems.append(
                            f"{name}:{lineno} {label}为 {found}，应为 {expected}"
                        )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="校验版本号在各处保持一致")
    parser.add_argument("--tag", help="发布 tag（形如 v0.5.1 或 0.5.1）")
    args = parser.parse_args()

    expected = source_version()
    problems = scan_docs(expected)

    changelog = changelog_version()
    if changelog is None:
        problems.append("CHANGELOG.md 未找到形如 `## [X.Y.Z]` 的版本条目")
    elif changelog != expected:
        problems.append(f"CHANGELOG.md 最新条目为 {changelog}，应为 {expected}")

    if args.tag:
        tag = args.tag.lstrip("v")
        if tag != expected:
            problems.append(f"发布 tag 为 v{tag}，但 pyproject.toml 为 {expected}")

    if problems:
        print(f"版本不一致（真相源 pyproject.toml = {expected}）：", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print("\n修正后重试；真相源本身需变更时，请先改 pyproject.toml。", file=sys.stderr)
        return 1

    print(f"版本一致性校验通过：{expected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
