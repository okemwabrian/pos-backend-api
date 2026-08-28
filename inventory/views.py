import csv

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from rest_framework import viewsets
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from core.permissions import is_admin_or_manager

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


@login_required
@user_passes_test(is_admin_or_manager)
def export_inventory_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="inventory.csv"'

    writer = csv.writer(response)
    writer.writerow(["SKU", "Product", "Type", "Current Stock", "Retail Price"])
    for product in Product.objects.order_by("name"):
        writer.writerow(
            [
                product.sku,
                product.name,
                "Service" if product.is_service else "Product",
                product.stock_quantity,
                product.retail_price,
            ]
        )
    return response
