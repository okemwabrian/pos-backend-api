from django.urls import path
from .views import customers_view, suppliers_view

app_name = "crm"

urlpatterns = [
    path('customers/', customers_view, name='customers'),
    path('suppliers/', suppliers_view, name='suppliers'),
]
