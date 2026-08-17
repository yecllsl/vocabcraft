#!/usr/bin/env python3
"""Generate AAIF platform runtime configs into vocabcraft.plugin/runtime/.

Mirrors the previous Node script (scripts/generate-platform-configs.js) but uses
the project's Python stack. The generated files are consumed by
    scripts/sync-agent-configs(.ps1/.sh), which distributes them to the
    .trae / .opencode / .codebuddy / .goose platform directories.

Usage:
    python scripts/generate-platform-configs.py
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = PROJECT_ROOT / "vocabcraft.plugin" / "runtime"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def generate_trae() -> dict:
    return {
        "mcpServers": {
            "vocabcraft-mcp": {
                "command": "uv",
                "args": [
                    "run",
                    "--no-sync",
                    "--directory",
                    "${workspaceFolder}/vocabcraft.plugin/vocabcraft-mcp",
                    "vocabcraft-mcp",
                ],
            }
        }
    }


def generate_opencode() -> dict:
    return {
        "mcp": {
            "vocabcraft-mcp": {
                "type": "local",
                "command": ["uv", "run", "--no-sync", "vocabcraft-mcp"],
                "cwd": "vocabcraft.plugin/vocabcraft-mcp",
            }
        },
        "instructions": ["vocabcraft.plugin/AGENTS.md"],
    }


def generate_codebuddy() -> dict:
    return {
        "mcpServers": {
            "vocabcraft-mcp": {
                "command": "uv",
                "args": [
                    "run",
                    "--no-sync",
                    "--directory",
                    "${workspaceFolder}/vocabcraft.plugin/vocabcraft-mcp",
                    "vocabcraft-mcp",
                ],
            }
        }
    }


def generate_goose() -> dict:
    # Goose 原生 extension schema（非 mcpServers/mcp）。
    # --directory 用相对路径 "vocabcraft-mcp"，由 generate-goose-config.py
    # 解析为绝对路径写入 .goose/config.yaml，保证 Goose 可在任意工作目录启动。
    return {
        "extensions": {
            "vocabcraft-mcp": {
                "name": "vocabcraft-mcp",
                "enabled": True,
                "type": "stdio",
                "cmd": "uv",
                "args": [
                    "run",
                    "--no-sync",
                    "--directory",
                    "vocabcraft.plugin/vocabcraft-mcp",
                    "vocabcraft-mcp",
                ],
                "timeout": 300,
                "description": "VocabCraft 词汇学习与制作 MCP 服务",
            }
        }
    }


def main() -> None:
    (RUNTIME_DIR / "trae.json").write_text(
        json.dumps(generate_trae(), indent=2) + "\n", encoding="utf-8"
    )
    (RUNTIME_DIR / "opencode.json").write_text(
        json.dumps(generate_opencode(), indent=2) + "\n", encoding="utf-8"
    )
    (RUNTIME_DIR / "codebuddy.json").write_text(
        json.dumps(generate_codebuddy(), indent=2) + "\n", encoding="utf-8"
    )
    (RUNTIME_DIR / "goose.json").write_text(
        json.dumps(generate_goose(), indent=2) + "\n", encoding="utf-8"
    )
    print("已生成所有平台配置 (vocabcraft.plugin/runtime/)")


if __name__ == "__main__":
    main()
