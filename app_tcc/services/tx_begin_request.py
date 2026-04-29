from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TccTxBeginInput:
    biz_id: int
    branch_items: list[dict[str, Any]]
    auto_confirm: bool | None
    context: dict[str, Any] | None


def parse_tcc_tx_post_json(data: dict[str, Any]) -> TccTxBeginInput:
    if "saga_instance_id" in data and isinstance(data.get("payload"), dict):
        return _from_saga(data)
    return _from_classic(data)


def _from_saga(data: dict[str, Any]) -> TccTxBeginInput:
    pld: dict[str, Any] = data["payload"]
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
