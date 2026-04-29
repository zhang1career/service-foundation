"""Console helpers for dict_catalog (process-local LRU cache inside get_dict_by_codes)."""

from __future__ import annotations

from common.dict_catalog import get_dict_by_codes

CODE_CONFIG_ENTRY_PUBLIC = "config_entry_public"
CODE_KEEPCON_DEVICE_TYPE = "keepcon_device_type"
CODE_SAGA_INSTANCE_STATUS = "saga_instance_status"
CODE_SAGA_STEP_ACTION_STATUS = "saga_step_action_status"
CODE_SAGA_STEP_COMPENSATE_STATUS = "saga_step_compensate_status"
CODE_TCC_GLOBAL_TX_STATUS = "tcc_global_tx_status"
CODE_TCC_BRANCH_STATUS = "tcc_branch_status"


def int_kv(code: str) -> list[tuple[int, str]]:
    """Registered dict code -> sorted (value, label) for integer ``v`` in catalog."""
    data = get_dict_by_codes(code.strip())
    items = data.get(code.strip()) or []
    rows: list[tuple[int, str]] = []
    for it in items:
        if isinstance(it, dict):
            rows.append((int(it["v"]), str(it["k"])))
    return sorted(rows, key=lambda x: x[0])


def str_kv(code: str) -> list[tuple[str, str]]:
    """Same as ``int_kv`` but string values for HTML ``<option value=...``."""
    return [(str(v), k) for v, k in int_kv(code)]


def bundled_int_kv(*codes: str) -> dict[str, list[tuple[int, str]]]:
    """One ``get_dict_by_codes`` query for multiple codes (cache key = joined string)."""
    stripped = tuple(c.strip() for c in codes if c.strip())
    if not stripped:
        return {}
    raw = get_dict_by_codes(",".join(stripped))
    out: dict[str, list[tuple[int, str]]] = {}
    for c in stripped:
        items = raw.get(c) or []
        rows: list[tuple[int, str]] = []
        for it in items:
            if isinstance(it, dict):
                rows.append((int(it["v"]), str(it["k"])))
        out[c] = sorted(rows, key=lambda x: x[0])
    return out
