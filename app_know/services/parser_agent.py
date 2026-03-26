"""
Parser Agent: split text into sentences, classify, write MySQL + sentence_raw.
Stage 0 (创建): sentence creation with optional classification.
"""
import logging
import re
from typing import List

from app_know.consts import CLASS_CHOICES, CLASS_FACT
from app_know.enums.classification_enum import ClassificationEnum
from app_know.repos import knowledge_point_repo
from app_know.repos.sentence_raw_repo import delete_by_sentence_ids, save_sentence_raw
from common.consts.string_const import EMPTY_STRING

logger = logging.getLogger(__name__)

# Sentence split: split after 。！？!? (do not split on "3.14" - period not in set)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?])\s*")

CLASS_QUESTION = (
    "Classify this sentence into exactly one of: claim, fact, event, concept, definition, argument. "
    "claim=opinion/assertion; fact=factual statement; event=something that happened; "
    "concept=abstract idea; definition=defining a term; argument=reasoning/argumentation. "
    "Reply with one word only, lowercase."
)


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences by 。！？!?
    Filters empty strings.
    """
    if not text or not isinstance(text, str):
        return []
    text = text.strip()
    if not text:
        return []
    parts = SENTENCE_SPLIT_PATTERN.split(text)
    return [p.strip() for p in parts if p and p.strip()]


def classify_sentence(sentence: str) -> str:
    """
    Classify sentence into claim/fact/event/concept/definition/argument.
    Uses app_aibroker (HTTP) only; on failure returns CLASS_FACT.
    """
    if not sentence or not sentence.strip():
        return CLASS_FACT
    try:
        from common.services.aibroker_client import aibroker_ask_and_answer

        result = aibroker_ask_and_answer(
            text=sentence[:500],
            role="sentence classifier",
            question=CLASS_QUESTION,
            additional_question=EMPTY_STRING,
            temperature=0,
        )
        if result and isinstance(result, str):
            c = result.strip().lower()
            valid = {cls[0] for cls in CLASS_CHOICES}
            if c in valid:
                return c
    except Exception as e:
        logger.debug("[parser_agent] classify_sentence aibroker error: %s", e)
    return CLASS_FACT


def parse_and_store(
        batch_id: int,
        content: str,
        use_ai_classify: bool = True,
        write_sentence_raw: bool = True,
) -> List[dict]:
    """
    Parse content into sentences, optionally classify, store in MySQL + sentence_raw.
    Returns list of dicts with id, content, classification, seq for each sentence.
    """
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        raise ValueError("batch_id must be a positive integer")
    if content is None:
        content = ""
    if not isinstance(content, str):
        raise ValueError("content must be a string")

    sentences = split_sentences(content)
    if not sentences:
        return []

    # Classify (optional)
    classified = []
    for s in sentences:
        cls = classify_sentence(s) if use_ai_classify else CLASS_FACT
        classified.append((s, cls))

    # Delete existing knowledge points (and sentence_raw) for this batch
    existing_ids = knowledge_point_repo.get_ids_by_batch(batch_id)
    if existing_ids:
        try:
            delete_by_sentence_ids(existing_ids)
        except Exception as e:
            logger.warning("[parser_agent] delete_by_sentence_ids failed: %s", e)
    knowledge_point_repo.delete_by_batch(batch_id)

    # Batch create in MySQL（classification 存为 int）
    contents = [c[0] for c in classified]
    classifications = [
        ClassificationEnum.CODE_TO_ID.get(c[1], ClassificationEnum.FACT)
        for c in classified
    ]
    created = knowledge_point_repo.batch_create(batch_id, contents, classifications=classifications)

    results = []
    for i, s in enumerate(created):
        cls_id = classifications[i] if i < len(classifications) else ClassificationEnum.FACT
        if write_sentence_raw:
            try:
                save_sentence_raw(sentence_id=s.id, content=s.content)
            except Exception as e:
                logger.warning("[parser_agent] save_sentence_raw failed for id=%s: %s", s.id, e)
        results.append({
            "id": s.id,
            "content": s.content,
            "classification": cls_id,
            "seq": s.seq,
        })

    # Update stage to created (0) - already default
    return results
