from django.urls import path

from .views import (
    dashboard_view,
    first_admin_setup_view,
    register_view,
    reset_password_view,
    user_management_view,
)

app_name = "users"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("setup/", first_admin_setup_view, name="first_admin_setup"),
    path("accounts/register/", register_view, name="register"),
    path("users/", user_management_view, name="manage"),
    path("users/<int:user_id>/password/", reset_password_view, name="reset_password"),
]
