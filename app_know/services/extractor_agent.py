"""
Extractor Agent: extract 摘要 + 主谓宾定状补 from each sentence.
Stage 1: fills brief, graph_brief, graph_subject, graph_object.
"""
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

from common.consts.string_const import EMPTY_STRING

from app_know.enums.stage_enum import StageEnum
from app_know.enums.knowledge_status_enum import KnowledgeStatusEnum
from app_know.repos import knowledge_point_repo

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = (
    "对下面这句话做成分分析，提取：主语、谓语、宾语、定语（修饰主语或宾语的）、状语（修饰谓语的）、补语（补充宾语的）。\n"
    "同时给出该句的摘要（一句话概括）。\n\n"
    "规则：\n"
    "1. 主语、谓语、宾语：提取核心语义，可适度概括（如「我们」->「团队」）\n"
    "2. 谓语使用规范形式（如「正在买」->「买」）\n"
    "3. 宾语提取核心概念，去掉修饰语\n"
    "4. 定语、状语、补语若无则留空\n"
    "5. 摘要用一句话概括句意，不超过50字\n\n"
    "输出纯JSON，不要其他内容。格式：\n"
    '{"brief": "摘要", "subject": "主语", "predicate": "谓语", "object": "宾语", '
    '"attributive": "定语", "adverbial": "状语", "complement": "补语"}'
)

# 成分分析专用：区分 定语(主语) 与 定语(宾语)，避免混淆。同一字段多个元素用中文分号「；」分隔。
COMPONENTS_PROMPT = (
    "对下面这句话做成分分析，按（定语-主语）-（状语-谓语）-（定语-宾语-补语）结构提取。\n\n"
    "规则：\n"
    "1. 定语(主)：只填修饰主语的定语，若无则留空\n"
    "2. 定语(宾)：只填修饰宾语的定语，若无则留空\n"
    "3. 主语、谓语、宾语：提取核心语义\n"
    "4. 状语、补语若无则留空\n"
    "5. 若某字段有多个元素（如多个状语），用英文竖线「|」分隔，例如：\"20世纪初|给美国\"\n\n"
    "输出纯JSON，不要其他内容。格式：\n"
    '{"attributive_subject": "定语(主语)", "subject": "主语", "adverbial": "状语", "predicate": "谓语", '
    '"attributive_object": "定语(宾语)", "object": "宾语", "complement": "补语"}'
)

# 定制单选题：按（定语-主语）-谓语-（定语-宾语-补语）提取摘要，主语/谓语从给定选项中选或 -1
PROMPT_BRIEF_SINGLE_CHOICE = """把以下的句子，按照（定语-主语）-谓语-（定语-宾语-补语）的句子成分结构，提取成摘要信息。其中，主语、谓语的可选范围下面给出，如果可选项不合适就使用你认为合适的词语。
答案格式：json。
答案内容：brief（摘要），要求一句话、50 字内；sub_idx(主语选项集的选中序号，-1表示没选中)；prd_idx(谓语选项集的选中序号，-1表示没选中)。
说明：定语、补语可空缺；括号仅表示局部完整的句子成分，连线号仅表示句子成分之间的划分，这些都不要出现在结果中。

主语选项（序号从0开始）：
{subject_options}

谓语选项（序号从0开始）：
{predicate_options}

请只输出一个 JSON 对象，不要其他文字。"""

_text_ai_client = None


def _get_text_ai():
    global _text_ai_client
    if _text_ai_client is not None:
        return _text_ai_client
    try:
        from common.services.ai.text_ai import TextAI
    except ImportError:
        return None
    base_url = os.environ.get("AIGC_API_URL", EMPTY_STRING)
    api_key = os.environ.get("AIGC_API_KEY", EMPTY_STRING)
    model = os.environ.get("AIGC_GPT_MODEL", "gpt-4o-mini")
    if not api_key:
        return None
    try:
        _text_ai_client = TextAI(base_url, api_key, model)
        return _text_ai_client
    except Exception as e:
        logger.warning("[extractor_agent] TextAI init failed: %s", e)
        return None


def _parse_extract_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from AI response."""
    if not response or not isinstance(response, str):
        return None
    resp = response.strip()
    # Try to find JSON block
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', resp, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "subject" in parsed and "predicate" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass
    try:
        parsed = json.loads(resp)
        if isinstance(parsed, dict) and "subject" in parsed and "predicate" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass
    return None


def _parse_components_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from 成分分析 response (attributive_subject / attributive_object 分开)."""
    if not response or not isinstance(response, str):
        return None
    resp = response.strip()
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', resp, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "subject" in parsed and "predicate" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass
    try:
        parsed = json.loads(resp)
        if isinstance(parsed, dict) and "subject" in parsed and "predicate" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass
    return None


def _build_graph_brief(parsed: Dict[str, Any]) -> str:
    """Build graph_brief text from parsed components."""
    parts = []
    if parsed.get("subject"):
        parts.append(f"主:{parsed['subject']}")
    if parsed.get("predicate"):
        parts.append(f"谓:{parsed['predicate']}")
    if parsed.get("object"):
        parts.append(f"宾:{parsed['object']}")
    if parsed.get("attributive"):
        parts.append(f"定:{parsed['attributive']}")
    if parsed.get("adverbial"):
        parts.append(f"状:{parsed['adverbial']}")
    if parsed.get("complement"):
        parts.append(f"补:{parsed['complement']}")
    return " | ".join(parts) if parts else ""


def _parse_brief_single_choice_response(response: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from custom single-choice brief response: brief, sub_idx, prd_idx."""
    if not response or not isinstance(response, str):
        return None
    resp = response.strip()
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', resp, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "brief" in parsed:
                return {
                    "brief": (parsed.get("brief") or "").strip(),
                    "sub_idx": int(parsed.get("sub_idx", -1)) if parsed.get("sub_idx") is not None else -1,
                    "prd_idx": int(parsed.get("prd_idx", -1)) if parsed.get("prd_idx") is not None else -1,
                }
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    try:
        parsed = json.loads(resp)
        if isinstance(parsed, dict) and "brief" in parsed:
            return {
                "brief": (parsed.get("brief") or "").strip(),
                "sub_idx": int(parsed.get("sub_idx", -1)) if parsed.get("sub_idx") is not None else -1,
                "prd_idx": int(parsed.get("prd_idx", -1)) if parsed.get("prd_idx") is not None else -1,
            }
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return None


def extract_brief_with_options(
    sentence_content: str,
    subject_options: List[str],
    predicate_options: List[str],
) -> Optional[Dict[str, Any]]:
    """
    Extract brief using 题目限定: single-choice over subject and predicate option lists.
    Calls OpenAI-compatible API with custom prompt; returns { brief, sub_idx, prd_idx } or None.
    """
    if not sentence_content or not isinstance(sentence_content, str):
        return None
    content = sentence_content.strip()
    if not content:
        return None
    subject_list = list(subject_options) if subject_options else []
    predicate_list = list(predicate_options) if predicate_options else []
    subject_options_str = "\n".join(f"{i}. {s}" for i, s in enumerate(subject_list))
    predicate_options_str = "\n".join(f"{i}. {p}" for i, p in enumerate(predicate_list))
    client = _get_text_ai()
    if client is None:
        return None
    try:
        question_part = PROMPT_BRIEF_SINGLE_CHOICE.format(
            subject_options=subject_options_str or "（无）",
            predicate_options=predicate_options_str or "（无）",
        )
        _, result = client.ask_and_answer(
            text=content[:1500],
            role="摘要提取助手",
            question=question_part,
            additional_question="必须只输出一个 JSON 对象，包含 brief、sub_idx、prd_idx，不要其他文字。",
            temperature=0,
        )
        if not result:
            return None
        parsed = _parse_brief_single_choice_response(result)
        if not parsed:
            logger.warning("[extractor_agent] Failed to parse brief single-choice: %s", result[:200])
            return None
        brief = (parsed.get("brief") or "").strip() or content[:100]
        parsed["brief"] = brief
        return parsed
    except Exception as e:
        logger.exception("[extractor_agent] extract_brief_with_options error: %s", e)
        return None


def extract_sentence(sentence_content: str) -> Optional[Dict[str, Any]]:
    """
    Extract brief + 主谓宾定状补 from one sentence.
    Returns dict with brief, graph_brief, graph_subject, graph_object, or None on failure.
    """
    if not sentence_content or not isinstance(sentence_content, str):
        return None
    content = sentence_content.strip()
    if not content:
        return None
    client = _get_text_ai()
    if client is None:
        return None
    try:
        _, result = client.ask_and_answer(
            text=content[:1500],
            role="成分分析助手",
            question=EXTRACT_PROMPT,
            additional_question="必须严格按上述JSON格式输出，不要输出其他文字。",
            temperature=0,
        )
        if not result:
            return None
        parsed = _parse_extract_response(result)
        if not parsed:
            logger.warning("[extractor_agent] Failed to parse: %s", result[:200])
            return None
        brief = (parsed.get("brief") or "").strip() or content[:100]
        subject = (parsed.get("subject") or "").strip()
        predicate = (parsed.get("predicate") or "").strip()
        obj = (parsed.get("object") or "").strip()
        graph_brief = _build_graph_brief(parsed)
        return {
            "brief": brief,
            "graph_brief": graph_brief or f"主:{subject} 谓:{predicate} 宾:{obj}",
            "graph_subject": subject,
            "graph_object": obj,
        }
    except Exception as e:
        logger.exception("[extractor_agent] extract_sentence error: %s", e)
        return None


def extract_and_store_for_batch(
    batch_id: int,
    use_ai: bool = True,
) -> List[Dict[str, Any]]:
    """
    Extract for all sentences of a knowledge document.
    Updates brief, graph_brief, graph_subject, graph_object; sets stage=2, status=1.
    Returns list of {sentence_id, content, brief, graph_subject, graph_object, ok, error}.
    """
    if batch_id is None or not isinstance(batch_id, int) or batch_id <= 0:
        raise ValueError("batch_id must be a positive integer")
    items, _ = knowledge_point_repo.list_by_batch(batch_id, limit=500)
    results = []
    for s in items:
        rec = {
            "sentence_id": s.id,
            "content": s.content,
            "brief": None,
            "graph_subject": None,
            "graph_object": None,
            "ok": False,
            "error": None,
        }
        if not use_ai:
            rec["error"] = "use_ai=false, skip"
            results.append(rec)
            continue
        extracted = extract_sentence(s.content)
        if extracted is None:
            rec["error"] = "extract failed or AI unavailable"
            results.append(rec)
            continue
        rec["brief"] = extracted.get("brief")
        rec["graph_subject"] = extracted.get("graph_subject")
        rec["graph_object"] = extracted.get("graph_object")
        try:
            knowledge_point_repo.update(
                s.id,
                brief=extracted.get("brief"),
                graph_brief=extracted.get("graph_brief"),
                graph_subject=extracted.get("graph_subject"),
                graph_object=extracted.get("graph_object"),
                stage=StageEnum.PARSE,
                status=KnowledgeStatusEnum.COMPLETED,
            )
            rec["ok"] = True
        except Exception as e:
            rec["error"] = str(e)
            logger.warning("[extractor_agent] update_sentence failed for id=%s: %s", s.id, e)
        results.append(rec)
    return results


def analyze_components(sentence_content: str) -> Optional[Dict[str, Any]]:
    """
    Get sentence components under (定语-主语)-(状语-谓语)-(定语-宾语-补语).
    Returns dict with: attributive_subject, subject, adverbial, predicate,
    attributive_object, object, complement (all strings). 定语(主)与定语(宾)分开，不混淆。
    """
    if not sentence_content or not isinstance(sentence_content, str):
        return None
    content = sentence_content.strip()
    if not content:
        return None
    client = _get_text_ai()
    if client is None:
        return None
    try:
        _, result = client.ask_and_answer(
            text=content[:1500],
            role="成分分析助手",
            question=COMPONENTS_PROMPT,
            additional_question="必须严格按上述JSON格式输出，不要输出其他文字。",
            temperature=0,
        )
        if not result:
            return None
        parsed = _parse_components_response(result)
        if not parsed:
            return None
        attributive_subject = (parsed.get("attributive_subject") or "").strip()
        attributive_object = (parsed.get("attributive_object") or "").strip()
        subject = (parsed.get("subject") or "").strip()
        adverbial = (parsed.get("adverbial") or "").strip()
        predicate = (parsed.get("predicate") or "").strip()
        obj = (parsed.get("object") or "").strip()
        complement = (parsed.get("complement") or "").strip()
        return {
            "attributive_subject": attributive_subject,
            "subject": subject,
            "adverbial": adverbial,
            "predicate": predicate,
            "attributive_object": attributive_object,
            "object": obj,
            "complement": complement,
        }
    except Exception as e:
        logger.exception("[extractor_agent] analyze_components error: %s", e)
        return None
