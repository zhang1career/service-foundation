"""
Batch service: create, delete, analyze operations for batch table.
"""
import logging
from typing import Dict, Any, Optional

from app_know.consts import SOURCE_TYPE_FILE, SOURCE_TYPE_INSTANT
from app_know.repos.batch_repo import create_batch, delete_batch
from app_know.repos.knowledge_point_repo import delete_by_batch
from app_know.services.parser_agent import parse_and_store

logger = logging.getLogger(__name__)

MAX_CONTENT_LEN = 500 * 1024  # 500KB
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def create_from_text(content: str) -> Dict[str, Any]:
    """Create batch from form text. No sentence split; use 分析 in batch detail to split."""
    content = (content or "").strip()
    if not content:
        raise ValueError("content is required")
    if len(content) > MAX_CONTENT_LEN:
        raise ValueError(f"content too long (max {MAX_CONTENT_LEN // 1024}KB)")

    batch_record = create_batch(content=content, source_type=SOURCE_TYPE_INSTANT)
    batch_id = batch_record.id

    return {
        "id": batch_id,
        "content": content,
        "sentence_count": 0,
        "sentences": [],
    }


def create_from_upload(
        file_content: str,
        file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Create batch from uploaded file. file_path stored in batch.content (for OSS). No sentence split; use 分析 in batch detail."""
    if not file_content:
        raise ValueError("file content is required")

    content = file_path or ""
    batch_record = create_batch(content=content, source_type=SOURCE_TYPE_FILE)
    batch_id = batch_record.id

    return {
        "id": batch_id,
        "content": content,
        "sentence_count": 0,
        "sentences": [],
    }


def delete_batch_and_knowledge(batch_id: int) -> int:
    """Delete batch record and all knowledge points. Returns count of deleted knowledge points."""
    count = delete_by_batch(batch_id)
    delete_batch(batch_id)
    return count


def analyze_batch(
        batch_id: int,
        content: str,
        use_ai_classify: bool = True,
        write_sentence_raw: bool = True,
) -> Dict[str, Any]:
    """Split content into sentences, save to knowledge table. Returns sentence count and list."""
    content = (content or "").strip()
    if not content:
        raise ValueError("content is required in body")

    sentences = parse_and_store(
        batch_id=batch_id,
        content=content,
        use_ai_classify=use_ai_classify,
        write_sentence_raw=write_sentence_raw,
    )

    return {
        "kid": batch_id,
        "sentence_count": len(sentences),
        "sentences": sentences,
    }
