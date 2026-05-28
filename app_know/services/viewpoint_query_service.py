"""
Viewpoint integration helper.
"""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _integrate_sentences_with_ai(ordered_items: List[Dict[str, Any]]) -> str:
    """将 content + classification（替换为枚举名）经 app_aibroker 整合成一段连贯观点文本."""
    id_to_code = {id_: code for id_, code in ClassificationEnum.ITEMS}
    lines = []
    for item in ordered_items:
        cls_id = item.get("classification")
        code = id_to_code.get(cls_id, "fact") if isinstance(cls_id, int) else (
            cls_id if isinstance(cls_id, str) else "fact")
        content = (item.get("content") or "").strip()
        if content:
            lines.append("【{}】 {}".format(code, content))
    if not lines:
        return ""
    text_block = "\n".join(lines)
    try:
        from app_aibroker.outbound_client import aibroker_ask_and_answer

        answer = aibroker_ask_and_answer(
            text=text_block,
            role="assistant",
            question="请将以上按类型标注的句子整合成一段连贯的观点，注意句子间的衔接与过渡。只输出整合后的观点文本，不要其他说明或编号。",
            additional_question="",
            temperature=0,
        )
        stripped = (answer or "").strip()
        if stripped:
            return stripped
        return "\n".join((item.get("content") or "").strip() for item in ordered_items)
    except Exception as e:
        logger.warning("[_integrate_sentences_with_ai] AI 整合失败: %s", e)
        return "\n".join((item.get("content") or "").strip() for item in ordered_items)


def integrate_viewpoint_from_items(items: List[Dict[str, Any]]) -> str:
    """
    将列表 [{ content, classification }]（classification 为枚举名称）发送给 AI 整合成一段观点文本.
    """
    if not items:
        return ""
    ordered = [{"content": (x.get("content") or "").strip(), "classification": x.get("classification")} for x in items]
    ordered = [x for x in ordered if x["content"]]
    return _integrate_sentences_with_ai(ordered)