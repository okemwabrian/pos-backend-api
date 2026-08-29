from django.urls import path

from .views import dashboard_view, register_view, reset_password_view, user_management_view

app_name = "users"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("accounts/register/", register_view, name="register"),
    path("users/", user_management_view, name="manage"),
    path("users/<int:user_id>/password/", reset_password_view, name="reset_password"),
]
