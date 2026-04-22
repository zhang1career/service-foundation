from django.urls import path

from app_saga.views.instance_api_view import SagaInstanceDetailView, SagaInstanceStartView
from app_saga.views.saga_health_view import SagaHealthView
from common.views.xxl_job_view import XxlJobBeatView, XxlJobKillView, XxlJobRunView

urlpatterns = [
    path("health", SagaHealthView.as_view(), name="saga-health"),
    path("instances/start", SagaInstanceStartView.as_view(), name="saga-instance-start"),
    path("instances/detail", SagaInstanceDetailView.as_view(), name="saga-instance-detail"),
    path("xxl-job/beat", XxlJobBeatView.as_view(), name="saga-xxl-beat"),
    path("xxl-job/run", XxlJobRunView.as_view(), name="saga-xxl-run"),
    path("xxl-job/kill", XxlJobKillView.as_view(), name="saga-xxl-kill"),
]
