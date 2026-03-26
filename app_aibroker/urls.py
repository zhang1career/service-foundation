from django.urls import path

from app_aibroker.views import (
    AssetCreateView,
    AssetDetailView,
    HealthView,
    JobCreateView,
    JobDetailView,
    MetricsSummaryView,
    ModelDetailView,
    ModelListCreateView,
    ProviderDetailView,
    ProviderListCreateView,
    RegDetailView,
    RegListCreateView,
    TemplateDetailView,
    TemplateListCreateView,
    TextGenerateView,
    EmbeddingCreateView,
)

urlpatterns = [
    path("v1/health", HealthView.as_view(), name="aibroker-health"),
    path("v1/text/generate", TextGenerateView.as_view(), name="aibroker-text-generate"),
    path("v1/embeddings", EmbeddingCreateView.as_view(), name="aibroker-embeddings"),
    path("v1/metrics/summary", MetricsSummaryView.as_view(), name="aibroker-metrics-summary"),
    path("v1/regs", RegListCreateView.as_view(), name="aibroker-reg-list-create"),
    path("v1/regs/<int:reg_id>", RegDetailView.as_view(), name="aibroker-reg-detail"),
    path("v1/providers", ProviderListCreateView.as_view(), name="aibroker-provider-list-create"),
    path("v1/providers/<int:provider_id>", ProviderDetailView.as_view(), name="aibroker-provider-detail"),
    path(
        "v1/providers/<int:provider_id>/models",
        ModelListCreateView.as_view(),
        name="aibroker-model-list-create",
    ),
    path(
        "v1/providers/<int:provider_id>/models/<int:model_id>",
        ModelDetailView.as_view(),
        name="aibroker-model-detail",
    ),
    path("v1/templates", TemplateListCreateView.as_view(), name="aibroker-template-list-create"),
    path(
        "v1/templates/<int:template_id>",
        TemplateDetailView.as_view(),
        name="aibroker-template-detail",
    ),
    path("v1/jobs", JobCreateView.as_view(), name="aibroker-job-create"),
    path("v1/jobs/<int:job_id>", JobDetailView.as_view(), name="aibroker-job-detail"),
    path("v1/assets", AssetCreateView.as_view(), name="aibroker-asset-create"),
    path("v1/assets/<int:asset_id>", AssetDetailView.as_view(), name="aibroker-asset-detail"),
]
