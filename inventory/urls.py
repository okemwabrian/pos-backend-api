from django.urls import path
from .views import categories_view, export_inventory_csv, inventory_export_download_view, inventory_export_preview_view, products_view, restock_view

app_name = "inventory"

# The DefaultRouter automatically generates the standard RESTful routes
urlpatterns = [
    path('products/', products_view, name='products'),
    path('categories/', categories_view, name='categories'),
    path('restock/', restock_view, name='restock'),
    path('products/<int:product_id>/restock/', restock_view, name='product_restock'),
    path('export/csv/', export_inventory_csv, name='export_inventory_csv'),
    path('export/preview/', inventory_export_preview_view, name='export_preview'),
    path('export/download/<str:export_format>/', inventory_export_download_view, name='export_download'),
]
