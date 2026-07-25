# src/vocabcraft_mcp/storage.py
"""本地 JSON 文件存储引擎

提供词汇、复习记录、考题的 CRUD 操作、查询过滤支持。
数据以 JSON 文件形式存储在本地文件系统中，按实体类型分目录管理。

目录结构约定（相对于 base_dir）:
    base_dir/
    ├── vocabs/    # 词汇记录 JSON，文件名 {vocab_id}.json
    ├── reviews/   # 复习记录 JSON，文件名 {record_id}.json
    ├── quizzes/   # 考题 JSON，文件名 {quiz_id}.json
    └── images/    # 词汇原图（由 ocr_recognize 写入）

写入策略：原子写（先写 .tmp，再 os.replace 原子替换），防止中途崩溃损坏数据。
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from vocabcraft_mcp.models import VocabRecord, Quiz, ReviewRecord


class Storage:
    """本地 JSON 文件存储引擎

    骨架阶段提供基础 CRUD 与查询，复杂业务逻辑（如批量统计、复合过滤）
    由 tools/* 层组合调用实现。
    """

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.vocabs_dir = self.base_dir / "vocabs"
        self.reviews_dir = self.base_dir / "reviews"
        self.quizzes_dir = self.base_dir / "quizzes"
        self.images_dir = self.base_dir / "images"
        # 确保所有子目录存在
        for d in [
            self.vocabs_dir, self.reviews_dir,
            self.quizzes_dir, self.images_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────
    # 通用原子写
    # ──────────────────────────────────────────

    @staticmethod
    def _atomic_write(fp: Path, data: str) -> None:
        """原子写入：先写 .tmp，再 os.replace 原子替换

        os.replace 在同文件系统内是原子操作，避免写入中途崩溃导致 JSON 损坏。
        """
        tmp_fp = fp.with_suffix(fp.suffix + ".tmp")
        tmp_fp.write_text(data, encoding="utf-8")
        os.replace(tmp_fp, fp)

    # ──────────────────────────────────────────
    # 词汇 CRUD
    # ──────────────────────────────────────────

    def save_vocab(self, vocab: VocabRecord, overwrite: bool = False) -> dict:
        """保存词汇记录到 JSON 文件（原子写入）

        Args:
            vocab: 词汇记录
            overwrite: 是否允许覆盖已有文件（update/patch 传 True，新建传 False）

        Returns:
            包含 vocab_id 和 saved_path 的字典；文件已存在且不允许覆盖时返回 error
        """
        fp = self.vocabs_dir / f"{vocab.id}.json"
        if fp.exists() and not overwrite:
            return {"error": f"词汇文件已存在，禁止覆盖: {vocab.id}"}
        self._atomic_write(fp, vocab.model_dump_json(indent=2, ensure_ascii=False))
        return {"vocab_id": vocab.id, "saved_path": str(fp)}

    def load_vocab(self, vocab_id: str) -> Optional[VocabRecord]:
        """根据 ID 加载词汇记录，不存在返回 None"""
        fp = self.vocabs_dir / f"{vocab_id}.json"
        if not fp.exists():
            return None
        return VocabRecord.model_validate(json.loads(fp.read_text(encoding="utf-8")))

    def update_vocab(self, vocab: VocabRecord) -> dict:
        """更新词汇（覆盖写入），语义等同于 save"""
        return self.save_vocab(vocab, overwrite=True)

    def patch_vocab(self, vocab_id: str, patch: dict) -> Optional[VocabRecord]:
        """部分更新词汇，仅修改 patch 中包含的字段

        加载现有记录 → 递归合并 patch → 原子写回。
        嵌套字段（如 structured.part_of_speech、review_state.ease_factor）
        通过 _deep_merge 递归合并，不覆盖未提及的子字段。

        Returns:
            更新后的 VocabRecord；ID 不存在返回 None
        """
        existing = self.load_vocab(vocab_id)
        if existing is None:
            return None
        merged = _deep_merge(existing.model_dump(), patch)
        updated = VocabRecord.model_validate(merged)
        self.save_vocab(updated, overwrite=True)
        return updated

    def delete_vocab(self, vocab_id: str) -> bool:
        """删除词汇文件，返回是否删除成功"""
        fp = self.vocabs_dir / f"{vocab_id}.json"
        if fp.exists():
            fp.unlink()
            return True
        return False

    def list_all_vocab_ids(self) -> list[str]:
        """列出所有词汇 ID（文件名不含扩展名）"""
        return [f.stem for f in self.vocabs_dir.glob("*.json")]

    def query_vocabs(self, filters: dict) -> dict:
        """根据过滤条件查询词汇

        支持的过滤条件:
            - language: 语言代码精确匹配（structured.language）
            - word: 词形模糊匹配（structured.word 子串包含）
            - date_range: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
        """
        vocabs = []
        for vid in self.list_all_vocab_ids():
            v = self.load_vocab(vid)
            if v and self._matches(v, filters):
                vocabs.append(v.model_dump())
        # 按创建时间倒序排列
        vocabs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"vocabs": vocabs, "total_count": len(vocabs)}

    def _matches(self, v: VocabRecord, f: dict) -> bool:
        """判断词汇是否匹配过滤条件"""
        if not f:
            return True
        # 语言过滤（嵌套在 structured.language）
        if f.get("language") and v.structured.language != f["language"]:
            return False
        # 词形模糊匹配（structured.word 子串包含）
        if f.get("word") and f["word"] not in v.structured.word:
            return False
        # 创建日期范围过滤
        dr = f.get("date_range")
        if dr:
            created = v.created_at.isoformat()[:10]
            if dr.get("start") and created < dr["start"]:
                return False
            if dr.get("end") and created > dr["end"]:
                return False
        return True

    # ──────────────────────────────────────────
    # 考题 CRUD
    # ──────────────────────────────────────────

    def save_quiz(self, quiz: Quiz) -> dict:
        """保存考题（原子写入）"""
        fp = self.quizzes_dir / f"{quiz.id}.json"
        self._atomic_write(fp, quiz.model_dump_json(indent=2, ensure_ascii=False))
        return {"quiz_id": quiz.id, "saved_path": str(fp)}

    def load_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """根据 ID 加载考题，不存在返回 None"""
        fp = self.quizzes_dir / f"{quiz_id}.json"
        if not fp.exists():
            return None
        return Quiz.model_validate(json.loads(fp.read_text(encoding="utf-8")))

    def list_all_quiz_ids(self) -> list[str]:
        """列出所有考题 ID"""
        return [f.stem for f in self.quizzes_dir.glob("*.json")]

    # ──────────────────────────────────────────
    # 复习记录 CRUD
    # ──────────────────────────────────────────

    def save_review_record(self, record: ReviewRecord) -> dict:
        """保存复习记录（原子写入）"""
        fp = self.reviews_dir / f"{record.record_id}.json"
        self._atomic_write(fp, record.model_dump_json(indent=2, ensure_ascii=False))
        return {"record_id": record.record_id, "saved_path": str(fp)}

    def list_all_review_records(self) -> list[ReviewRecord]:
        """列出所有复习记录"""
        records = []
        for fp in self.reviews_dir.glob("*.json"):
            records.append(
                ReviewRecord.model_validate(json.loads(fp.read_text(encoding="utf-8")))
            )
        return records

    # ──────────────────────────────────────────
    # 统计辅助
    # ──────────────────────────────────────────

    def get_all_vocabs_for_statistics(self) -> list[VocabRecord]:
        """获取全部词汇用于统计计算"""
        return [v for vid in self.list_all_vocab_ids() if (v := self.load_vocab(vid))]


def _deep_merge(base: dict, patch: dict) -> dict:
    """递归合并 patch 到 base 字典

    对于嵌套 dict，递归合并而非覆盖。
    对于非 dict 值，用 patch 的值覆盖 base。
    用于 patch_vocab 的部分更新（支持 structured.*/review_state.* 嵌套字段）。
    """
    result = dict(base)
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
