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
    key = shared.get("tcc_access_key") or data.get("tcc_access_key")
    if isinstance(key, str) and key.strip():
        logger.debug("TCC begin (Saga): tcc_access_key present, len=%s", len(key.strip()))

    bi = pld.get("biz_id")
    if not isinstance(bi, int) or bi <= 0:
        raise ValueError("Saga TCC: payload.biz_id (positive int) is required")

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
        biz_id=bi,
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
