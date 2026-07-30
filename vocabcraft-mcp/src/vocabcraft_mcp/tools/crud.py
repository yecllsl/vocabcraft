# src/vocabcraft_mcp/tools/crud.py
"""词汇数据 CRUD 操作 Tools

提供词汇的保存、查询、更新、删除功能，作为 MCP Tool 的业务逻辑层。
底层调用 Storage 引擎完成实际的文件 IO 操作。

设计:
    - save_vocab: 自动生成 vocab_id（vocab_YYYYMMDD_NNN）、注入时间戳、
      初始化 review_state（含首次复习排程 next_review）
    - update_vocab: patch 语义（合并更新），仅改传入字段，避免覆盖丢字段；
      自动刷新 updated_at；grade_quiz 通过它只改 review_state 子字段
    - query_vocab / delete_vocab: 透传 storage
"""
from pathlib import Path

from vocabcraft_mcp.algorithms import get_initial_schedule, _now_utc
from vocabcraft_mcp.models import VocabRecord, StructuredVocab, ReviewState
from vocabcraft_mcp.storage import Storage

# 默认数据目录：项目根目录下的 data/ 文件夹
# tools/crud.py → vocabcraft_mcp/tools/ → vocabcraft_mcp/ → src/ → vocabcraft-mcp/
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def get_storage() -> Storage:
    """获取默认 Storage 实例（指向项目 data 目录）"""
    return Storage(base_dir=_DEFAULT_DATA_DIR)


def _generate_id(prefix: str, existing_ids: list[str]) -> str:
    """生成 {prefix}_YYYYMMDD_NNN，基于当天已有编号 +1

    Args:
        prefix: ID 前缀，如 "vocab"/"quiz"/"rec"
        existing_ids: 同类型已有 ID 列表
    """
    today = _now_utc().strftime("%Y%m%d")
    p = f"{prefix}_{today}_"
    existing = [eid for eid in existing_ids if eid.startswith(p)]
    nnn = max((int(eid.split("_")[-1]) for eid in existing), default=0) + 1
    return f"{p}{nnn:03d}"


def _generate_vocab_id(storage: Storage) -> str:
    """生成 vocab_YYYYMMDD_NNN"""
    return _generate_id("vocab", storage.list_all_vocab_ids())


def _find_existing_vocab_id(storage: Storage, word: str, language: str) -> str | None:
    """查找相同 (word, language) 的已有 vocab_id，不存在返回 None

    当前实现为全量扫描（数据规模小，O(n) 可接受）。若未来词数显著增长，
    可在 Storage 层维护 word -> vocab_id 索引以加速。
    """
    for vocab_id in storage.list_all_vocab_ids():
        record = storage.load_vocab(vocab_id)
        if record and record.structured.word == word and record.structured.language == language:
            return vocab_id
    return None


def save_vocab(vocab_data: dict) -> dict:
    """保存词汇记录

    自动生成 vocab_id（若未提供）、注入 created_at/updated_at、初始化
    review_state（含首次复习排程 next_review = 今天+1天）。

    Args:
        vocab_data: 词汇数据字典，支持字段:
            - id: 可选，未提供则自动生成 vocab_YYYYMMDD_NNN
            - structured: 必填，StructuredVocab 字段 dict（word/phonetic/...）
            - created_at/updated_at: 可选，默认当前 UTC 时间
            - review_state: 可选，默认初始化（EF=2.5, next_review=今天+1天）

    Returns:
        包含 vocab_id 和 saved_path 的字典；structured 缺失或重复时返回 error
    """
    storage = get_storage()

    # 构造结构化信息（必填）
    structured_data = vocab_data.get("structured")
    if not structured_data or "word" not in structured_data:
        return {"error": "vocab_data.structured.word 为必填项"}
    structured = StructuredVocab(**structured_data)

    # 校验 (word, language) 唯一性，防止同一词重复入库
    existing_id = _find_existing_vocab_id(storage, structured.word, structured.language)
    if existing_id:
        return {
            "error": f"词汇已存在: {structured.word} ({structured.language})",
            "existing_vocab_id": existing_id,
        }

    # ID: 用户提供 or 自动生成（带重试，防止并发撞号）
    vocab_id = vocab_data.get("id")
    if not vocab_id:
        for _ in range(3):  # ponytail: 最多重试 3 次，单用户场景极低概率需重试
            vocab_id = _generate_vocab_id(storage)
            if not (storage.vocabs_dir / f"{vocab_id}.json").exists():
                break
        else:
            return {"error": "无法生成唯一 vocab_id，请稍后重试"}

    # review_state: 用户提供 or 初始化（注入首次排程）
    review_state_data = vocab_data.get("review_state")
    if review_state_data:
        review_state = ReviewState(**review_state_data)
    else:
        sched = get_initial_schedule()
        review_state = ReviewState(next_review=sched["next_review"])

    now = _now_utc()
    record = VocabRecord(
        id=vocab_id,
        structured=structured,
        review_state=review_state,
        created_at=vocab_data.get("created_at", now),
        updated_at=vocab_data.get("updated_at", now),
    )
    return storage.save_vocab(record)


def query_vocab(filters: dict) -> dict:
    """按条件查询词汇

    Args:
        filters: 过滤条件字典，支持:
            - language: 语言代码精确匹配
            - word: 词形模糊匹配（子串包含）
            - date_range: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

    Returns:
        包含 vocabs 列表和 total_count 的字典
    """
    return get_storage().query_vocabs(filters or {})


def update_vocab(vocab_data: dict) -> dict:
    """更新词汇记录（patch 合并语义）

    仅修改 vocab_data 中包含的字段，未提及字段保留原值；
    自动刷新 updated_at。grade_quiz 通过传入 {"id":..., "review_state": {...}}
    只更新记忆状态而不动 structured。

    Args:
        vocab_data: 待更新字段字典，必须包含 id

    Returns:
        包含 vocab_id 和 saved_path 的字典；ID 缺失或不存在返回 error
    """
    vocab_id = vocab_data.get("id")
    if not vocab_id:
        return {"error": "更新词汇需提供 id"}

    storage = get_storage()
    # 构造 patch：剥离 id，刷新 updated_at
    patch = {k: v for k, v in vocab_data.items() if k != "id"}
    patch["updated_at"] = _now_utc().isoformat()

    updated = storage.patch_vocab(vocab_id, patch)
    if updated is None:
        return {"error": f"词汇不存在: {vocab_id}"}
    return {"vocab_id": updated.id, "saved_path": str(storage.vocabs_dir / f"{updated.id}.json")}


def delete_vocab(vocab_id: str) -> dict:
    """删除词汇记录

    Args:
        vocab_id: 要删除的词汇 ID

    Returns:
        包含 deleted 状态和 vocab_id 的字典
    """
    storage = get_storage()
    deleted = storage.delete_vocab(vocab_id)
    return {"vocab_id": vocab_id, "deleted": deleted}
