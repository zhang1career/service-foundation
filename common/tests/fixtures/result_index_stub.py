"""Test-only callable for :mod:`common.services.result_service` whitelist tests."""


def stub_result_fn(param_map: dict | None):
    return {"ok": True, "param_map": param_map}
