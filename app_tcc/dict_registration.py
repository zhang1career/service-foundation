"""Side-effect imports: TCC dict codes on catalog."""

from app_tcc.enums import BranchStatus, CancelReason, GlobalTxStatus
from common.dict_catalog import register_dict_code


@register_dict_code("tcc_global_tx_status")
class _TccGlobalTxStatusDict:
    @classmethod
    def to_dict_list(cls) -> list[dict]:
        pairs = [
            ("INIT", GlobalTxStatus.INIT),
            ("TRYING", GlobalTxStatus.TRYING),
            ("AWAIT_CONFIRM", GlobalTxStatus.AWAIT_CONFIRM),
            ("CONFIRMING", GlobalTxStatus.CONFIRMING),
            ("CANCELING", GlobalTxStatus.CANCELING),
            ("COMMITTED", GlobalTxStatus.COMMITTED),
            ("ROLLED_BACK", GlobalTxStatus.ROLLED_BACK),
            ("NEEDS_MANUAL", GlobalTxStatus.NEEDS_MANUAL),
        ]
        return [{"k": a, "v": str(b)} for a, b in pairs]


@register_dict_code("tcc_branch_status")
class _TccBranchStatusDict:
    @classmethod
    def to_dict_list(cls) -> list[dict]:
        pairs = [
            ("PENDING_TRY", BranchStatus.PENDING_TRY),
            ("TRY_SUCCEEDED", BranchStatus.TRY_SUCCEEDED),
            ("TRY_FAILED", BranchStatus.TRY_FAILED),
            ("CONFIRM_SUCCEEDED", BranchStatus.CONFIRM_SUCCEEDED),
            ("CONFIRM_FAILED", BranchStatus.CONFIRM_FAILED),
            ("CANCEL_SUCCEEDED", BranchStatus.CANCEL_SUCCEEDED),
            ("CANCEL_FAILED", BranchStatus.CANCEL_FAILED),
        ]
        return [{"k": a, "v": str(b)} for a, b in pairs]


@register_dict_code("tcc_cancel_reason")
class _TccCancelReasonDict:
    @classmethod
    def to_dict_list(cls) -> list[dict]:
        pairs = [
            ("UNPAID", CancelReason.UNPAID),
            ("ORDER_CLOSED", CancelReason.ORDER_CLOSED),
            ("DUPLICATE_CALLBACK", CancelReason.DUPLICATE_CALLBACK),
        ]
        return [{"k": a, "v": str(b)} for a, b in pairs]
