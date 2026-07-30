#!/usr/bin/env python3
# scripts/migrate_def_pos.py
"""将 definitions[i].text 中嵌入的【词性】前缀提取到 part_of_speech 字段。

背景：旧版解析 prompt 未提供 part_of_speech 字段，LLM 将文言文义项词性
编码为【名词】步伐，脚步 格式嵌入 text。新版 Definition 模型新增 part_of_speech
字段，本脚本一次性清理存量数据。

行为约定：
- 扫描所有 *.json，匹配 definitions[i].text 以【开头的记录
- 提取【词性】到 part_of_speech，清理 text
- 默认 --dry-run：只打印不写盘；加 --apply 落盘
- 幂等：已无【前缀的记录不受影响
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_VOCABS_DIR = Path("vocabcraft-mcp/data/vocabs")
_POS_PATTERN = re.compile(r"^【(.+?)】\s*(.*)$", re.DOTALL)


def find_targets(vocabs_dir: Path) -> list[Path]:
    """扫描所有 *.json，挑出 definitions 中含【词性】前缀的文件。"""
    targets: list[Path] = []
    for fp in sorted(vocabs_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"[WARN] JSON 解析失败，跳过: {fp.name}", file=sys.stderr)
            continue
        definitions = data.get("structured", {}).get("definitions", [])
        for d in definitions:
            if isinstance(d, dict) and _POS_PATTERN.match(d.get("text", "")):
                targets.append(fp)
                break
    return targets


def build_migrated(data: dict) -> dict:
    """对单个 vocab 字典执行迁移，返回新字典。"""
    import copy
    new_data = copy.deepcopy(data)
    definitions = new_data.get("structured", {}).get("definitions", [])
    for d in definitions:
        if not isinstance(d, dict):
            continue
        text = d.get("text", "")
        match = _POS_PATTERN.match(text)
        if match:
            d["part_of_speech"] = match.group(1).strip()
            d["text"] = match.group(2).strip()
    return new_data


def render_diff(before: dict, after: dict) -> str:
    """生成精简 diff。"""
    lines = []
    word = before.get("structured", {}).get("word", "?")
    lines.append(f"  word: {word!r}")
    old_defs = before.get("structured", {}).get("definitions", [])
    new_defs = after.get("structured", {}).get("definitions", [])
    for i, (old, new) in enumerate(zip(old_defs, new_defs)):
        if old.get("text") != new.get("text") or old.get("part_of_speech") != new.get("part_of_speech"):
            lines.append(f"  def[{i}]: {old.get('text')!r} → {new.get('text')!r}")
            lines.append(f"    part_of_speech: {old.get('part_of_speech', '')!r} → {new.get('part_of_speech', '')!r}")
    return "\n".join(lines)


def apply_migration(fp: Path, migrated: dict) -> None:
    """原子写回。"""
    tmp_fp = fp.with_suffix(fp.suffix + ".tmp")
    tmp_fp.write_text(
        json.dumps(migrated, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(tmp_fp, fp)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="提取 definitions[i].text 中的【词性】前缀到 part_of_speech 字段",
    )
    parser.add_argument("--vocabs-dir", type=Path, default=DEFAULT_VOCABS_DIR)
    parser.add_argument("--apply", action="store_true", help="实际写盘（默认 dry-run）")
    parser.add_argument("--limit", type=int, default=0, help="最多处理 N 个文件（0=全部）")
    args = parser.parse_args()

    vocabs_dir = args.vocabs_dir
    if not vocabs_dir.is_dir():
        print(f"[ERROR] 词汇目录不存在: {vocabs_dir}", file=sys.stderr)
        return 1

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"== {mode} | 扫描目录: {vocabs_dir} ==")

    targets = find_targets(vocabs_dir)
    if args.limit:
        targets = targets[:args.limit]
    print(f"匹配到 {len(targets)} 个待迁移文件\n")

    if not targets:
        print("无需迁移，退出。")
        return 0

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
