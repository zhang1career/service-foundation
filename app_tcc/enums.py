"""TCC coordinator status enums (int for DB storage)."""


class GlobalTxStatus:
    INIT = 10
    TRYING = 20
    AWAIT_CONFIRM = 30
    CONFIRMING = 40
    CANCELING = 50
    COMMITTED = 60
    ROLLED_BACK = 70
    NEEDS_MANUAL = 80


class BranchStatus:
    PENDING_TRY = 10
    TRY_SUCCEEDED = 20
    TRY_FAILED = 30
    CONFIRM_SUCCEEDED = 40
    CONFIRM_FAILED = 50
    CANCEL_SUCCEEDED = 60
    CANCEL_FAILED = 70
