from app_aibroker.views.health_view import HealthView
from app_aibroker.views.reg_view import RegListCreateView, RegDetailView
from app_aibroker.views.text_view import TextGenerateView
from app_aibroker.views.embedding_view import EmbeddingCreateView
from app_aibroker.views.provider_view import (
    ProviderListCreateView,
    ProviderDetailView,
    ModelListCreateView,
    ModelDetailView,
)
from app_aibroker.views.template_view import (
    TemplateListCreateView,
    TemplateDetailView,
)
from app_aibroker.views.job_view import JobCreateView, JobDetailView
from app_aibroker.views.asset_view import AssetCreateView, AssetDetailView
from app_aibroker.views.metrics_view import MetricsSummaryView

__all__ = [
    "HealthView",
    "RegListCreateView",
    "RegDetailView",
    "TextGenerateView",
    "EmbeddingCreateView",
    "ProviderListCreateView",
    "ProviderDetailView",
    "ModelListCreateView",
    "ModelDetailView",
    "TemplateListCreateView",
    "TemplateDetailView",
    "JobCreateView",
    "JobDetailView",
    "AssetCreateView",
    "AssetDetailView",
    "MetricsSummaryView",
]
