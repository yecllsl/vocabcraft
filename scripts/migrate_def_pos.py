#!/usr/bin/env python3
# scripts/migrate_def_pos.py
"""将 definitions[i].text 中嵌入的【词性】前缀提取到 part_of_speech 字段，
并为缺失 part_of_speech 的义项从词汇级 part_of_speech 回填。

背景：旧版解析 prompt 未提供 part_of_speech 字段，LLM 将文言文义项词性
编码为【名词】步伐，脚步 格式嵌入 text。新版 Definition 模型新增 part_of_speech
字段，本脚本一次性清理存量数据。

行为约定：
- 第一轮：匹配 definitions[i].text 以【开头的记录，提取【词性】到 part_of_speech
- 第二轮：definitions[i].part_of_speech 为空但 vocab 级 part_of_speech 为单一
  可识别词性时，从 vocab 级回填（compound POS 如"形容词、动词、名词"不回填）
- 默认 --dry-run：只打印不写盘；加 --apply 落盘
- 幂等：已无【前缀且已填充 part_of_speech 的记录不受影响
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

# 英文词性简写 → 中文映射（用于 vocab 级 part_of_speech 回填）
_EN_TO_ZH_POS = {
    "n.": "名词", "v.": "动词", "adj.": "形容词", "adv.": "副词",
    "pron.": "代词", "num.": "数词", "prep.": "介词", "conj.": "连词",
    "int.": "叹词", "konj.": "连词",
}

# 单一中文词性正则（不含顿号/斜杠分隔符）
_SINGLE_ZH_POS = re.compile(r"^[\u4e00-\u9fa5]+$")


def _normalize_vocab_pos(vocab_pos: str) -> str:
    """将 vocab 级 part_of_speech 归一化为中文，compound 返回空串。"""
    pos = vocab_pos.strip()
    if not pos:
        return ""
    # 含分隔符 → compound，不回填
    if any(sep in pos for sep in ("、", "/", "，")):
        return ""
    # 英文简写 → 中文
    lower = pos.lower()
    if lower in _EN_TO_ZH_POS:
        return _EN_TO_ZH_POS[lower]
    # 已是中文单一词性
    if _SINGLE_ZH_POS.match(pos):
        return pos
    return ""


def find_targets(vocabs_dir: Path) -> list[Path]:
    """扫描所有 *.json，挑出 definitions 中含【词性】前缀或 def_pos 为空的文件。"""
    targets: list[Path] = []
    for fp in sorted(vocabs_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"[WARN] JSON 解析失败，跳过: {fp.name}", file=sys.stderr)
            continue
        definitions = data.get("structured", {}).get("definitions", [])
        vocab_pos = _normalize_vocab_pos(
            data.get("structured", {}).get("part_of_speech", "")
        )
        needs_work = False
        for d in definitions:
            if not isinstance(d, dict):
                continue
            text = d.get("text", "")
            def_pos = d.get("part_of_speech", "")
            if _POS_PATTERN.match(text):
                needs_work = True
                break
            if not def_pos and vocab_pos:
                needs_work = True
                break
        if needs_work:
            targets.append(fp)
    return targets


def build_migrated(data: dict) -> dict:
    """对单个 vocab 字典执行迁移，返回新字典。"""
    import copy
    new_data = copy.deepcopy(data)
    structured = new_data.get("structured", {})
    definitions = structured.get("definitions", [])
    vocab_pos = _normalize_vocab_pos(structured.get("part_of_speech", ""))
    for d in definitions:
        if not isinstance(d, dict):
            continue
        text = d.get("text", "")
        match = _POS_PATTERN.match(text)
        if match:
            d["part_of_speech"] = match.group(1).strip()
            d["text"] = match.group(2).strip()
        elif not d.get("part_of_speech") and vocab_pos:
            d["part_of_speech"] = vocab_pos
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
