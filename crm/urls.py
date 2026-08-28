from django.urls import path
from .views import crm_management_view, customers_view, suppliers_view

app_name = "crm"

urlpatterns = [
    path('', crm_management_view, name='manage'),
    path('customers/', customers_view, name='customers'),
    path('suppliers/', suppliers_view, name='suppliers'),
]
