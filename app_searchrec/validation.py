"""SearchRec 写入侧校验。"""

import math


def parse_optional_unit_interval(raw, field_name: str) -> float:
    """
    将可选字段解析为闭区间 [0, 1] 内的有限浮点数（归一化分值）。
    raw 为 None 时视为缺省，返回 0.0。
    """
    if raw is None:
        return 0.0
    try:
        v = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"field `{field_name}` must be a number") from exc
    if not math.isfinite(v):
        raise ValueError(f"field `{field_name}` must be a finite number")
    if v < 0 or v > 1:
        raise ValueError(f"field `{field_name}` must be normalized in the closed interval [0, 1]")
    return v


def normalize_upsert_document_payload(doc: dict) -> dict:
    """返回新 dict：对 popularity_score / freshness_score 做 [0,1] 校验与规范化。"""
    out = dict(doc)
    out["popularity_score"] = parse_optional_unit_interval(
        out.get("popularity_score"), "popularity_score"
    )
    out["freshness_score"] = parse_optional_unit_interval(
        out.get("freshness_score"), "freshness_score"
    )
    return out
