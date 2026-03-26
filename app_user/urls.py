from django.urls import path

from app_user.views import (
    RegisterView,
    RegisterVerifyView,
    LoginView,
    RefreshView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    UserMeView,
    UserMeUpdateRequestView,
    UserMeUpdateVerifyView,
    UserListView,
    UserDetailView,
    UserConsoleCreateView,
    UserConsoleVerifyView,
    UserConsoleUpdateView,
    EventConsoleListView,
    EventConsoleDetailView,
)


urlpatterns = [
    path("register", RegisterView.as_view(), name="user-register"),
    path("register/verify", RegisterVerifyView.as_view(), name="user-register-verify"),
    path("login", LoginView.as_view(), name="user-login"),
    path("refresh", RefreshView.as_view(), name="user-refresh"),
    path("reset-password/request", PasswordResetRequestView.as_view(), name="user-reset-request"),
    path("reset-password/verify", PasswordResetVerifyView.as_view(), name="user-reset-verify"),
    path("me", UserMeView.as_view(), name="user-me"),
    path("me/update/request", UserMeUpdateRequestView.as_view(), name="user-me-update-request"),
    path("me/update/verify", UserMeUpdateVerifyView.as_view(), name="user-me-update-verify"),
    path("users", UserListView.as_view(), name="user-list"),
    path("users/<int:user_id>", UserDetailView.as_view(), name="user-detail"),
    # Console admin APIs
    path("console/users", UserConsoleCreateView.as_view(), name="console-user-create"),
    path("console/users/<int:user_id>/verify", UserConsoleVerifyView.as_view(), name="console-user-verify"),
    path("console/users/<int:user_id>", UserConsoleUpdateView.as_view(), name="console-user-update"),
    path("console/events", EventConsoleListView.as_view(), name="console-event-list"),
    path("console/events/<int:event_id>", EventConsoleDetailView.as_view(), name="console-event-detail"),
]
