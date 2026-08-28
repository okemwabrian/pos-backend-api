import csv

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from core.permissions import is_admin_or_manager
from .forms import ProductForm

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


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
def products_view(request):
    instance = get_object_or_404(Product, pk=request.POST.get("id")) if request.POST.get("id") else None
    form = ProductForm(request.POST or None, instance=instance)
    if request.method == "POST" and request.POST.get("delete"):
        instance.delete()
        messages.success(request, "Product deleted.")
        return redirect("inventory:products")
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product saved.")
        return redirect("inventory:products")
    return render(request, "inventory/products.html", {"form": form, "products": Product.objects.select_related("category").order_by("name"), "edit_id": instance.pk if instance else None})
