from django.urls import path

from . import views


app_name = "offline"

urlpatterns = [
    path("login/", views.token_login, name="login"),
    path("logout/", views.token_logout, name="logout"),
    path("catalog/", views.catalog, name="catalog"),
    path("sync/", views.sync_operations, name="sync"),
]
