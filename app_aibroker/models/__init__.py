from importlib import import_module

__all__ = [
    "Reg",
    "AiProvider",
    "AiModel",
    "PromptTemplate",
    "AiCallLog",
    "AiJob",
    "AiAsset",
    "AiIdempotency",
]

_LAZY_ATTRS: dict[str, tuple[str, str]] = {
    "Reg": ("app_aibroker.models.reg", "Reg"),
    "AiProvider": ("app_aibroker.models.ai_provider", "AiProvider"),
    "AiModel": ("app_aibroker.models.ai_model", "AiModel"),
    "PromptTemplate": ("app_aibroker.models.prompt_template", "PromptTemplate"),
    "AiCallLog": ("app_aibroker.models.ai_call_log", "AiCallLog"),
    "AiJob": ("app_aibroker.models.ai_job", "AiJob"),
    "AiAsset": ("app_aibroker.models.ai_asset", "AiAsset"),
    "AiIdempotency": ("app_aibroker.models.ai_idempotency", "AiIdempotency"),
}


def __getattr__(name: str):
    if name in _LAZY_ATTRS:
        module_path, attr_name = _LAZY_ATTRS[name]
        module = import_module(module_path)
        return getattr(module, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
