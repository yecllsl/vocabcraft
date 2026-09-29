#!/usr/bin/env python3
"""Generate AAIF platform runtime configs into vocabcraft.plugin/runtime/.

Mirrors the previous Node script (scripts/generate-platform-configs.js) but uses
the project's Python stack. The generated files are consumed by
    scripts/sync-agent-configs(.ps1/.sh), which distributes them to the
    .trae / .opencode platform directories.
    (CodeBuddy 走 Tier 1 插件市场通道，不生成 codebuddy.json)

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
        "$schema": "https://opencode.ai/config.json",
        "mcp": {
            "vocabcraft-mcp": {
                "type": "local",
                "command": ["uv", "run", "--no-sync", "vocabcraft-mcp"],
                "cwd": "vocabcraft.plugin/vocabcraft-mcp",
            }
        },
        "instructions": ["vocabcraft.plugin/AGENTS.md"],
    }


def main() -> None:
    (RUNTIME_DIR / "trae.json").write_text(
        json.dumps(generate_trae(), indent=2) + "\n", encoding="utf-8"
    )
    (RUNTIME_DIR / "opencode.json").write_text(
        json.dumps(generate_opencode(), indent=2) + "\n", encoding="utf-8"
    )
    print("已生成平台配置 (vocabcraft.plugin/runtime/: trae.json, opencode.json)")


if __name__ == "__main__":
    main()
