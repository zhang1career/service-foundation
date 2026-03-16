"""
观点页「查询知识」：按路径表达式（ATTR:/PRED: 前缀）查 knowledge，去重后按 classification 排序并经 AI 整合.
"""
import logging
from typing import Any, Dict, List, Tuple

from app_know.enums.classification_enum import ClassificationEnum
from app_know.repos.knowledge_point_repo import (
    list_by_g_brief_exact,
    list_by_g_brief_hashes,
    list_by_g_sub_or_g_obj_exact,
)
from app_know.services.graph_builder_agent import graph_string_to_hash

logger = logging.getLogger(__name__)

PREFIX_ATTR = "ATTR:"
PREFIX_PRED = "PRED:"


def _integrate_sentences_with_ai(ordered_items: List[Dict[str, Any]]) -> str:
    """将 content + classification（替换为枚举名）发送给 AI 整合成一段连贯观点文本."""
    try:
        from app_know.services.extractor_agent import _get_text_ai
    except ImportError:
        return "\n".join((item.get("content") or "").strip() for item in ordered_items)

    id_to_code = {id_: code for id_, code in ClassificationEnum.ITEMS}
    lines = []
    for item in ordered_items:
        cls_id = item.get("classification")
        code = id_to_code.get(cls_id, "fact") if isinstance(cls_id, int) else (cls_id if isinstance(cls_id, str) else "fact")
        content = (item.get("content") or "").strip()
        if content:
            lines.append("【{}】 {}".format(code, content))
    if not lines:
        return ""
    text_block = "\n".join(lines)
    client = _get_text_ai()
    if not client:
        return "\n".join((item.get("content") or "").strip() for item in ordered_items)
    try:
        _, answer = client.ask_and_answer(
            text=text_block,
            role="assistant",
            question="请将以上按类型标注的句子整合成一段连贯的观点，注意句子间的衔接与过渡。只输出整合后的观点文本，不要其他说明或编号。",
            additional_question="",
            temperature=0,
        )
        return (answer or "").strip() or "\n".join((item.get("content") or "").strip() for item in ordered_items)
    except Exception as e:
        logger.warning("[_integrate_sentences_with_ai] AI 整合失败: %s", e)
        return "\n".join((item.get("content") or "").strip() for item in ordered_items)


def _split_lines_by_prefix(lines: List[str]) -> Tuple[List[str], List[str]]:
    """Split lines into ATTR expressions (no prefix in value) and PRED expressions (no prefix)."""
    attr_exprs: List[str] = []
    pred_exprs: List[str] = []
    for raw in lines:
        s = (raw or "").strip()
        if not s:
            continue
        if s.startswith(PREFIX_ATTR):
            attr_exprs.append(s[len(PREFIX_ATTR) :].strip())
        elif s.startswith(PREFIX_PRED):
            pred_exprs.append(s[len(PREFIX_PRED) :].strip())
        else:
            pred_exprs.append(s)
    return attr_exprs, pred_exprs


def _classification_to_label(cls_id: Any) -> str:
    """classification 字段值（数字）转枚举名称."""
    id_to_code = {id_: code for id_, code in ClassificationEnum.ITEMS}
    return id_to_code.get(cls_id, "fact") if cls_id is not None else "fact"


def query_knowledge_by_path_expressions(
    lines: List[str], integrate_ai: bool = True
) -> Dict[str, Any]:
    """
    根据路径表达式行（每行可为 ATTR:... 或 PRED:...）查询 knowledge，去重后按 classification 排序.
    若 integrate_ai=True 则经 AI 整合返回 viewpoint_text；否则 viewpoint_text 为空.

    Returns:
        {"rows": [{"id", "content", "classification", "classification_label", ...}], "viewpoint_text": str}
    """
    if not lines:
        return {"rows": [], "viewpoint_text": ""}

    lines = [str(x).strip() for x in lines if x and str(x).strip()]
    if not lines:
        return {"rows": [], "viewpoint_text": ""}

    attr_exprs, pred_exprs = _split_lines_by_prefix(lines)

    seen_ids: set = set()
    all_rows: List[Dict[str, Any]] = []

    if attr_exprs:
        by_attr = list_by_g_sub_or_g_obj_exact(attr_exprs)
        for k in by_attr:
            if k.id not in seen_ids:
                seen_ids.add(k.id)
                all_rows.append({
                    "id": k.id,
                    "content": (k.content or "").strip(),
                    "classification": k.classification,
                    "classification_label": _classification_to_label(k.classification),
                    "g_brief": (k.graph_brief or "").strip(),
                })

    if pred_exprs:
        hashes = [graph_string_to_hash(ln) for ln in pred_exprs]
        by_hash = list_by_g_brief_hashes(hashes)
        matched_briefs = {(k.graph_brief or "").strip() for k in by_hash}
        missing = [ln for ln in pred_exprs if ln not in matched_briefs]
        by_exact = list_by_g_brief_exact(missing) if missing else []

        for k in by_hash:
            if k.id not in seen_ids:
                seen_ids.add(k.id)
                all_rows.append({
                    "id": k.id,
                    "content": (k.content or "").strip(),
                    "classification": k.classification,
                    "classification_label": _classification_to_label(k.classification),
                    "g_brief": (k.graph_brief or "").strip(),
                })
        for k in by_exact:
            if k.id not in seen_ids:
                seen_ids.add(k.id)
                all_rows.append({
                    "id": k.id,
                    "content": (k.content or "").strip(),
                    "classification": k.classification,
                    "classification_label": _classification_to_label(k.classification),
                    "g_brief": (k.graph_brief or "").strip(),
                })

    order_by_cls = [id_ for id_, _ in ClassificationEnum.ITEMS]
    all_rows.sort(key=lambda r: (order_by_cls.index(r["classification"]) if r["classification"] in order_by_cls else 999, r["id"]))

    viewpoint_text = _integrate_sentences_with_ai(all_rows) if integrate_ai else ""
    return {"rows": all_rows, "viewpoint_text": viewpoint_text}


def integrate_viewpoint_from_items(items: List[Dict[str, Any]]) -> str:
    """
    将列表 [{ content, classification }]（classification 为枚举名称）发送给 AI 整合成一段观点文本.
    """
    if not items:
        return ""
    ordered = [{"content": (x.get("content") or "").strip(), "classification": x.get("classification")} for x in items]
    ordered = [x for x in ordered if x["content"]]
    return _integrate_sentences_with_ai(ordered)
