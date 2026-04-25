from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TccTxBeginInput:
    biz_id: int
    branch_items: list[dict[str, Any]]
    auto_confirm: bool | None
    context: dict[str, Any] | None


def _as_shared(data: dict[str, Any]) -> dict[str, Any]:
    s = data.get("saga_shared")
    return s if isinstance(s, dict) else {}


def parse_tcc_tx_post_json(data: dict[str, Any]) -> TccTxBeginInput:
    if "saga_instance_id" in data and isinstance(data.get("payload"), dict):
        return _from_saga(data)
    return _from_classic(data)


def _from_saga(data: dict[str, Any]) -> TccTxBeginInput:
    shared = _as_shared(data)
    pld: dict[str, Any] = data["payload"]
    token = (
        shared.get("tcc_access_key")
        or shared.get("tcc_access_token")
        or data.get("tcc_access_key")
        or data.get("tcc_access_token")
    )
    if isinstance(token, str) and token.strip():
        logger.debug("TCC begin (Saga): tcc access key present, len=%s", len(token.strip()))

    biz: int | None = None
    c = shared.get("tcc_flow_id")
    if isinstance(c, int) and c > 0:
        biz = c
    if biz is None and isinstance(pld.get("biz_id"), int) and pld["biz_id"] > 0:
        biz = pld["biz_id"]
    if not isinstance(biz, int) or biz <= 0:
        raise ValueError(
            "Saga TCC: saga_shared.tcc_flow_id (positive int) or payload.biz_id is required"
        )

    br = pld.get("branches")
    if not isinstance(br, list) or not br:
        raise ValueError("Saga TCC: payload.branches (non-empty array) is required")
    ac = pld.get("auto_confirm")
    if ac is not None and not isinstance(ac, bool):
        raise ValueError("Saga TCC: auto_confirm must be boolean when present")
    ctx = pld.get("context")
    if ctx is not None and not isinstance(ctx, dict):
        raise ValueError("Saga TCC: context must be object when present")
    return TccTxBeginInput(
        biz_id=biz,
        branch_items=br,
        auto_confirm=ac,
        context=ctx,
    )


def _from_classic(data: dict[str, Any]) -> TccTxBeginInput:
    bi = data.get("biz_id")
    if not isinstance(bi, int):
        raise ValueError("biz_id is required and must be int")
    br = data.get("branches")
    if not isinstance(br, list) or not br:
        raise ValueError("branches[] required")
    ac = data.get("auto_confirm")
    if ac is not None and not isinstance(ac, bool):
        raise ValueError("auto_confirm must be boolean")
    ctx = data.get("context")
    if ctx is not None and not isinstance(ctx, dict):
        raise ValueError("context must be object")
    return TccTxBeginInput(
        biz_id=bi,
        branch_items=br,
        auto_confirm=ac,
        context=ctx,
    )
