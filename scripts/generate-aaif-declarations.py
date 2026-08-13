#!/usr/bin/env python3
"""从真实源生成 AAIF 包声明文件。

产出 `.agents/` 下三个 AAIF 标准声明文件：
  - tools.json      ← 自省实时 MCP 服务（vocabcraft_mcp.server）得到工具与参数 schema
  - triggers.json   ← 聚合各 Skill 的「When to Use」自然语言触发词 + 命令别名
  - workflows.json  ← 聚合各 Skill 实际引用的 MCP 工具（按文中出现顺序）

这些文件是 AAIF 工具链（`agents publish .agents`）消费的声明产物，属**生成文件**，
请勿手工编辑；运行本脚本或 `scripts/sync-agent-configs` 即可重新生成。

工具自省依赖 vocabcraft-mcp 的运行环境，因此须通过 uv 运行：

    uv run --no-sync --directory vocabcraft-mcp python scripts/generate-aaif-declarations.py
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = PROJECT_ROOT / ".agents"
SKILLS_DIR = AGENTS_DIR / "skills"
MCP_PYPROJECT = PROJECT_ROOT / "vocabcraft-mcp" / "pyproject.toml"

TOOLS_SCHEMA = "https://agents.aaif.io/schemas/tools.json"
TRIGGERS_SCHEMA = "https://agents.aaif.io/schemas/triggers.json"
WORKFLOWS_SCHEMA = "https://agents.aaif.io/schemas/workflows.json"


def load_package_meta() -> dict:
    data = tomllib.loads(MCP_PYPROJECT.read_text(encoding="utf-8"))
    project = data["project"]
    return {
        "name": project["name"],
        "version": project["version"],
        "description": project.get("description", ""),
    }


def introspect_tools() -> list[dict]:
    """读取实时 MCP 工具注册表（FastMCP 自省）。"""
    try:
        from vocabcraft_mcp import server
    except ImportError as exc:  # 环境守卫：必须在 uv 环境运行
        raise SystemExit(
            "无法导入 vocabcraft_mcp。请通过 uv 运行本脚本：\n"
            "  uv run --no-sync --directory vocabcraft-mcp "
            "python scripts/generate-aaif-declarations.py"
        ) from exc
    tools = asyncio.run(server.mcp.list_tools())
    return [
        {"name": tool.name, "description": tool.description or "", "parameters": tool.parameters}
        for tool in tools
    ]


def parse_frontmatter(md: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", md, re.DOTALL)
    if not m:
        return {}
    meta: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
    return meta


def iter_skills() -> list[dict]:
    skills = []
    for skill_md in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)
        skills.append(
            {
                "name": meta.get("name", skill_md.parent.name),
                "description": meta.get("description", ""),
                "text": text,
            }
        )
    return skills


def extract_when_to_use(text: str) -> str:
    m = re.search(r"##\s*When to Use\s*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL)
    return m.group(1) if m else ""


def extract_keywords(text: str) -> list[str]:
    wtu = extract_when_to_use(text)
    found = re.findall(r'"([^"]+)"', wtu)
    # 仅保留含中/英文字的触发短语，剔除 "词性|释义" 这类代码片段
    keywords = [k for k in found if "|" not in k and re.search(r"[\u4e00-\u9fffA-Za-z]", k)]
    seen: set[str] = set()
    out = []
    for k in keywords:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def extract_skill_tools(text: str, known: list[str]) -> list[str]:
    # 按文中首次出现顺序去重，仅保留真实存在的 MCP 工具名
    order: list[str] = []
    for m in re.finditer(r"`([a-z_]+)`", text):
        name = m.group(1)
        if name in known and name not in order:
            order.append(name)
    return order


def generate_tools(meta: dict, tools: list[dict]) -> dict:
    return {
        "$schema": TOOLS_SCHEMA,
        "name": meta["name"],
        "version": meta["version"],
        "description": meta["description"],
        "tools": tools,
    }


def generate_triggers(skills: list[dict]) -> dict:
    triggers = []
    for skill in skills:
        name = skill["name"]
        suffix = name.split("vocabcraft-", 1)[-1]
        command = f"/{suffix}"
        triggers.append(
            {
                "type": "command",
                "pattern": f"^{re.escape(command)}(\\s.*)?$",
                "handler": "handle_command",
                "description": f"{name} 命令触发器",
            }
        )
        keywords = extract_keywords(skill["text"])
        if keywords:
            pattern = "(?i)(" + "|".join(re.escape(k) for k in keywords) + ")"
            triggers.append(
                {
                    "type": "conversation",
                    "pattern": pattern,
                    "handler": "handle_trigger",
                    "description": f"{name} 对话触发器",
                }
            )
    return {"$schema": TRIGGERS_SCHEMA, "triggers": triggers}


def generate_workflows(skills: list[dict], tools: list[dict]) -> dict:
    known = [t["name"] for t in tools]
    desc_by_tool = {t["name"]: t["description"] for t in tools}
    workflows = []
    for skill in skills:
        steps = [
            {"action": tool_name, "description": f"调用 {tool_name}：{desc_by_tool.get(tool_name, '')}"}
            for tool_name in extract_skill_tools(skill["text"], known)
        ]
        workflows.append(
            {"name": skill["name"], "description": skill["description"], "steps": steps}
        )
    return {"$schema": WORKFLOWS_SCHEMA, "workflows": workflows}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"已生成 {path.relative_to(PROJECT_ROOT)}")


def main() -> None:
    meta = load_package_meta()
    tools = introspect_tools()
    skills = iter_skills()
    write_json(AGENTS_DIR / "tools.json", generate_tools(meta, tools))
    write_json(AGENTS_DIR / "triggers.json", generate_triggers(skills))
    write_json(AGENTS_DIR / "workflows.json", generate_workflows(skills, tools))
    print("AAIF 声明文件已重新生成（请勿手工编辑，由脚本从真实源生成）")


if __name__ == "__main__":
    main()
