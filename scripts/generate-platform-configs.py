#!/usr/bin/env python3
"""Generate AAIF platform runtime configs into .agents/runtime/.

Mirrors the previous Node script (scripts/generate-platform-configs.js) but uses
the project's Python stack. The generated files are consumed by
scripts/sync-agent-configs(.ps1/.sh), which distributes them to the
.trae / .opencode / .workbuddy platform directories.

Usage:
    python scripts/generate-platform-configs.py
"""
from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = PROJECT_ROOT / ".agents" / "runtime"
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
                    "${workspaceFolder}/vocabcraft-mcp",
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
                "cwd": "vocabcraft-mcp",
            }
        },
        "instructions": [".agents/AGENTS.md"],
    }


def generate_workbuddy() -> dict:
    return {
        "mcpServers": {
            "vocabcraft-mcp": {
                "command": "uv",
                "args": [
                    "run",
                    "--no-sync",
                    "--directory",
                    "${workspaceFolder}/vocabcraft-mcp",
                    "vocabcraft-mcp",
                ],
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
    (RUNTIME_DIR / "workbuddy.json").write_text(
        json.dumps(generate_workbuddy(), indent=2) + "\n", encoding="utf-8"
    )
    print("已生成所有平台配置 (.agents/runtime/)")


if __name__ == "__main__":
    main()
