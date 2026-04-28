from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_saga.views.instance_api_view import SagaInstanceDetailView, SagaInstanceStartView
from app_saga.views.saga_health_view import SagaHealthView
from common.views.xxl_job_view import XxlJobBeatView, XxlJobKillView, XxlJobRunView

urlpatterns = [
    path("dict", DictCodesView.as_view(), name="saga-dict"),
    path("health", SagaHealthView.as_view(), name="saga-health"),
    path("instances", SagaInstanceStartView.as_view(), name="saga-instance-start"),
    path(
        "instances/<str:instance_id>",
        SagaInstanceDetailView.as_view(),
        name="saga-instance-detail",
    ),
    path("xxl-job/beat", XxlJobBeatView.as_view(), name="saga-xxl-beat"),
    path("xxl-job/run", XxlJobRunView.as_view(), name="saga-xxl-run"),
    path("xxl-job/kill", XxlJobKillView.as_view(), name="saga-xxl-kill"),
]
