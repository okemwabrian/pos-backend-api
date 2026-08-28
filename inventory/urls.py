from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, export_inventory_csv

# The DefaultRouter automatically generates the standard RESTful routes
router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('export/csv/', export_inventory_csv, name='export_inventory_csv'),
    path('', include(router.urls)),
]
