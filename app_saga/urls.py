from django.urls import path

from app_saga.views.instance_api_view import SagaInstanceDetailView, SagaInstanceStartView
from app_saga.views.saga_health_view import SagaHealthView

urlpatterns = [
    path("health", SagaHealthView.as_view(), name="saga-health"),
    path("instances/start", SagaInstanceStartView.as_view(), name="saga-instance-start"),
    path("instances/detail", SagaInstanceDetailView.as_view(), name="saga-instance-detail"),
]
