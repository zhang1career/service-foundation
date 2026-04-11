from django.urls import path

from common.views.dict_codes_view import DictCodesView
from app_user.views import (
    RegisterView,
    RegisterVerifyView,
    LoginView,
    PasswordResetView,
    PasswordResetVerifyView,
    UserMeView,
    UserMeUpdateRequestView,
    UserMeUpdateVerifyView,
    UserListView,
    UserDetailView,
    UserConsoleListView,
    UserConsoleVerifyView,
    UserConsoleDispositionRestoreView,
    UserConsoleDetailView,
    EventConsoleListView,
    EventConsoleDetailView,
)
from app_user.views.health_view import UserHealthView


urlpatterns = [
    path("dict", DictCodesView.as_view(), name="user-dict"),
    path("health", UserHealthView.as_view(), name="user-health"),
    path("register", RegisterView.as_view(), name="user-register"),
    path("register/verify", RegisterVerifyView.as_view(), name="user-register-verify"),
    path("login", LoginView.as_view(), name="user-login"),
    path("reset-password", PasswordResetView.as_view(), name="user-reset-request"),
    path("reset-password/verify", PasswordResetVerifyView.as_view(), name="user-reset-verify"),
    path("me", UserMeView.as_view(), name="user-me"),
    path("me/update/request", UserMeUpdateRequestView.as_view(), name="user-me-update-request"),
    path("me/update/verify", UserMeUpdateVerifyView.as_view(), name="user-me-update-verify"),
    path("users", UserListView.as_view(), name="user-list"),
    path("users/<int:user_id>", UserDetailView.as_view(), name="user-detail"),
    # Console admin APIs
    path("console/users", UserConsoleListView.as_view(), name="console-user-create"),
    path(
        "console/users/<int:user_id>/disposition/restore",
        UserConsoleDispositionRestoreView.as_view(),
        name="console-user-disposition-restore",
    ),
    path("console/users/<int:user_id>/verify", UserConsoleVerifyView.as_view(), name="console-user-verify"),
    path("console/users/<int:user_id>", UserConsoleDetailView.as_view(), name="console-user-update"),
    path("console/events", EventConsoleListView.as_view(), name="console-event-list"),
    path("console/events/<int:event_id>", EventConsoleDetailView.as_view(), name="console-event-detail"),
]
