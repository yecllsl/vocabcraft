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
from datetime import datetime, timezone
from pathlib import Path

from vocabcraft_mcp.models import VocabRecord, StructuredVocab, ReviewState
from vocabcraft_mcp.algorithms import get_initial_schedule
from vocabcraft_mcp.storage import Storage

# 默认数据目录：项目根目录下的 data/ 文件夹
# tools/crud.py → vocabcraft_mcp/tools/ → vocabcraft_mcp/ → src/ → vocabcraft-mcp/
_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def get_storage() -> Storage:
    """获取默认 Storage 实例（指向项目 data 目录）"""
    return Storage(base_dir=_DEFAULT_DATA_DIR)


def _now_utc() -> datetime:
    """当前 UTC 时间，统一时间基准"""
    return datetime.now(timezone.utc)


def _generate_vocab_id(storage: Storage) -> str:
    """生成 vocab_YYYYMMDD_NNN，NNN 基于当天最大编号 +1

    当天序号按已有词汇最大编号递增，避免不连续或并发写入时撞号覆盖。
    """
    today = _now_utc().strftime("%Y%m%d")
    prefix = f"vocab_{today}_"
    existing = [vid for vid in storage.list_all_vocab_ids() if vid.startswith(prefix)]
    if not existing:
        nnn = 1
    else:
        max_nnn = max(int(vid.split("_")[-1]) for vid in existing)
        nnn = max_nnn + 1
    return f"{prefix}{nnn:03d}"


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
        包含 vocab_id 和 saved_path 的字典；structured 缺失时返回 error
    """
    storage = get_storage()

    # 构造结构化信息（必填）
    structured_data = vocab_data.get("structured")
    if not structured_data or "word" not in structured_data:
        return {"error": "vocab_data.structured.word 为必填项"}
    structured = StructuredVocab(**structured_data)

    # ID: 用户提供 or 自动生成
    vocab_id = vocab_data.get("id") or _generate_vocab_id(storage)

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
