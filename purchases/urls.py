from django.urls import path

from .views import receive_stock_view

app_name = "purchases"

urlpatterns = [
    path("receive/", receive_stock_view, name="receive_stock"),
]
