#!/usr/bin/env python3
# scripts/migrate_german_vocab_examples.py
"""将德语词汇的"违规"数据迁移到符合采集规则 v2 的结构。

背景
----
旧版采集把多义词的例句堆在顶层 `examples`，新规则（vocabcraft-capture-rules.md
第 6/9 条）要求 `definitions` 为 `list[Definition]`，每项内嵌自己的 `examples`。
运行规则时间点早于德语批次采集时间，所以现存 52 个德语词汇文件仍为旧格式。

注意：模型层 StructuredVocab 已通过 _merge_legacy_examples 兼容旧格式（自动归并），
本脚本不解决"必须迁移"的功能性需求，只清理磁盘上不符合规则的脏数据，
让文件结构与新规则、与其他语言（zh_classical）一致。

行为约定
--------
- 仅修改 language == "de" 的文件。其他语言即使违规也保持原状（用户明确要求）。
- 仅修改同时满足两个条件的 de 文件：
    1) 顶层有非空 `examples` 字段
    2) `definitions` 是 list[str]（旧格式；新格式已经是 list[dict]）
- 例句归并目标：全部挂到 `definitions[0]`（旧数据无例句-义项对应关系）。
  `definitions[0]` 是字符串 → 升级为 `{"text": 原字符串, "examples": [...例句...]}`。
- 迁移后：删除顶层 `examples` 字段，刷新 `updated_at`。
- 默认 --dry-run：只打印将改什么，不写盘。加 --apply 才落盘。
- 写入采用 storage._atomic_write 同款策略（.tmp + os.replace）。

退出码
------
0 = 成功（或 dry-run 全部扫描完成）
1 = 写盘失败
2 = JSON 解析失败（数据损坏，需人工介入）
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# 默认数据目录（相对仓库根）；可用 --vocabs-dir 覆盖
DEFAULT_VOCABS_DIR = Path("vocabcraft-mcp/data/vocabs")
TARGET_LANGUAGE = "de"


def find_targets(vocabs_dir: Path) -> list[Path]:
    """扫描所有 *.json，挑出需要迁移的 de 文件。

    判定条件（同时满足）：
      - top-level language == "de"
      - 顶层 examples 存在且非空列表
      - structured.definitions 是 list[str]（即旧格式）
    """
    targets: list[Path] = []
    for fp in sorted(vocabs_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"[WARN] JSON 解析失败，跳过: {fp.name}", file=sys.stderr)
            continue
        structured = data.get("structured") or {}
        if structured.get("language") != TARGET_LANGUAGE:
            continue
        legacy_examples = structured.get("examples")
        definitions = structured.get("definitions") or []
        is_legacy_definitions = bool(definitions) and all(isinstance(d, str) for d in definitions)
        if legacy_examples and is_legacy_definitions:
            targets.append(fp)
    return targets


def build_migrated(data: dict) -> dict:
    """对单个 vocab 字典执行内存中的迁移，返回新字典（不修改原对象）。

    迁移内容：
      1. 把 structured.definitions[0] 从字符串升级为对象，examples 字段 = 顶层 examples
      2. 删除顶层 examples
      3. 刷新 updated_at 为当前 UTC ISO 8601
    """
    import copy
    new_data = copy.deepcopy(data)
    structured = new_data["structured"]
    legacy_examples = structured.pop("examples", []) or []
    definitions = structured.get("definitions", [])
    # 把第一个释义从字符串升级为对象
    first = definitions[0]
    definitions[0] = {"text": first, "examples": list(legacy_examples)}
    structured["definitions"] = definitions
    new_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    return new_data


def render_diff(before: dict, after: dict) -> str:
    """生成给用户看的精简 diff（只显示 structured 层与 updated_at）。"""
    lines = []
    lines.append(f"  word:           {before['structured'].get('word')!r}")
    lines.append(f"  language:       {before['structured'].get('language')!r}")
    # 旧结构：definitions 是 list[str]，examples 是顶层
    old_defs = before["structured"].get("definitions", [])
    old_examples = before["structured"].get("examples", [])
    lines.append(f"  BEFORE:  definitions={len(old_defs)} strings, top-level examples={len(old_examples)}")
    lines.append(f"    defs[:2] = {old_defs[:2]}")
    if old_examples:
        lines.append(f"    examples[:2] = {old_examples[:2]}")
    # 新结构：definitions[0] 是对象
    new_defs = after["structured"]["definitions"]
    lines.append(f"  AFTER:   definitions[0] 升级为对象并承载 {len(new_defs[0]['examples'])} 个例句")
    lines.append(f"    defs[0] = {{text: {new_defs[0]['text']!r}, examples: {new_defs[0]['examples'][:2]}...}}")
    lines.append(f"    顶层 examples 已删除")
    lines.append(f"  updated_at:  {before.get('updated_at')}  →  {after.get('updated_at')}")
    return "\n".join(lines)


def apply_migration(fp: Path, migrated: dict) -> None:
    """原子写回：.tmp + os.replace，与 storage.py 的 _atomic_write 保持一致。"""
    tmp_fp = fp.with_suffix(fp.suffix + ".tmp")
    tmp_fp.write_text(
        json.dumps(migrated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp_fp, fp)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="迁移德语词汇的旧 examples 结构到 definitions[0].examples（仅 de 语言）",
    )
    parser.add_argument(
        "--vocabs-dir",
        type=Path,
        default=DEFAULT_VOCABS_DIR,
        help=f"词汇目录路径（默认: {DEFAULT_VOCABS_DIR}）",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="实际写盘。省略则 dry-run，只打印将改什么",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="最多处理 N 个文件（0 = 全部），用于抽样验证",
    )
    args = parser.parse_args()

    vocabs_dir = args.vocabs_dir
    if not vocabs_dir.is_dir():
        print(f"[ERROR] 词汇目录不存在: {vocabs_dir}", file=sys.stderr)
        return 1

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"== {mode} | 扫描目录: {vocabs_dir} | 仅处理 language={TARGET_LANGUAGE} ==")

    targets = find_targets(vocabs_dir)
    if args.limit:
        targets = targets[: args.limit]
    print(f"匹配到 {len(targets)} 个待迁移文件\n")

    if not targets:
        print("无需迁移，退出。")
        return 0

    # self-check: 确保筛选条件确实只命中 de 文件
    sample = json.loads(targets[0].read_text(encoding="utf-8"))
    if sample["structured"].get("language") != TARGET_LANGUAGE:
        print(f"[FATAL] 筛选条件失效: 第一个匹配项不是 de: {targets[0].name}",
              file=sys.stderr)
        return 1

    migrated_count = 0
    for i, fp in enumerate(targets, 1):
        before = json.loads(fp.read_text(encoding="utf-8"))
        after = build_migrated(before)
        print(f"[{i:3d}/{len(targets)}] {fp.name}")
        print(render_diff(before, after))
        if args.apply:
            try:
                apply_migration(fp, after)
                migrated_count += 1
            except OSError as e:
                print(f"[ERROR] 写盘失败: {fp.name} - {e}", file=sys.stderr)
                return 1
        print()

    if args.apply:
        print(f"== 完成：已迁移 {migrated_count} / {len(targets)} 个文件 ==")
    else:
        print(f"== DRY-RUN 完成：{len(targets)} 个文件待迁移，未写盘 ==")
        print("   确认无误后加 --apply 实际执行。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
