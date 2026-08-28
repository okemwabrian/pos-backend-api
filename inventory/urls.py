from django.urls import path
from .views import export_inventory_csv, products_view

app_name = "inventory"

# The DefaultRouter automatically generates the standard RESTful routes
urlpatterns = [
    path('products/', products_view, name='products'),
    path('export/csv/', export_inventory_csv, name='export_inventory_csv'),
]
