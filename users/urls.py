from django.urls import path

from .views import dashboard_view, reset_password_view, user_management_view

app_name = "users"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("users/", user_management_view, name="manage"),
    path("users/<int:user_id>/password/", reset_password_view, name="reset_password"),
]
