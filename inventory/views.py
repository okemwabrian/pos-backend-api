import csv

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from core.permissions import IsAdminOrManager, is_admin_or_manager
from core.exporting import pdf_response, xlsx_response
from .forms import CategoryForm, ProductForm, RestockForm
from django.db import transaction
from django.db.models import F, Q

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrManager]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrManager]


def inventory_preview_data():
    headers = ["SKU", "Product", "Category", "Type", "Current Stock", "Retail Price"]
    rows = [
        [
            product.sku,
            product.name,
            product.category or "Uncategorised",
            "Service" if product.is_service else "Product",
            product.stock_quantity,
            product.retail_price,
        ]
        for product in Product.objects.select_related("category").order_by("name")
    ]
    return headers, rows


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
def inventory_export_preview_view(request):
    headers, rows = inventory_preview_data()
    return render(
        request,
        "inventory/export_preview.html",
        {"headers": headers, "rows": rows[:100], "total_rows": len(rows)},
    )


@login_required
@user_passes_test(is_admin_or_manager)
def inventory_export_download_view(request, export_format):
    if export_format not in {"xlsx", "pdf"}:
        return HttpResponseBadRequest("Choose an XLSX or PDF export.")
    headers, rows = inventory_preview_data()
    if export_format == "xlsx":
        return xlsx_response("inventory", "Inventory Export", headers, rows)
    return pdf_response("inventory", "Inventory Export", headers, rows)


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
    products = Product.objects.select_related("category").order_by("name")
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    return render(
        request,
        "inventory/products.html",
        {"form": form, "products": products, "edit_id": instance.pk if instance else None, "query": query},
    )


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
def categories_view(request):
    """Manage product categories from the POS instead of Django admin."""
    instance = (
        get_object_or_404(Category, pk=request.POST.get("id"))
        if request.POST.get("id")
        else None
    )
    form = CategoryForm(request.POST or None, instance=instance)
    if request.method == "POST" and request.POST.get("delete"):
        instance.delete()
        messages.success(request, "Category deleted. Products in it are now uncategorised.")
        return redirect("inventory:categories")
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category saved.")
        return redirect("inventory:categories")
    return render(
        request,
        "inventory/categories.html",
        {
            "form": form,
            "categories": Category.objects.prefetch_related("products").order_by("name"),
            "edit_id": instance.pk if instance else None,
        },
    )


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def restock_view(request, product_id=None):
    product = get_object_or_404(Product, pk=product_id) if product_id else None
    form = RestockForm(request.POST or None, initial={"sku": product.sku} if product else None)
    if request.method == "POST" and form.is_valid():
        sku = form.cleaned_data["sku"].strip()
        if product and sku != product.sku:
            form.add_error("sku", "The confirmed SKU does not match this product.")
        else:
            product = Product.objects.select_for_update().filter(sku=sku).first()
            if not product:
                form.add_error("sku", "No product with this SKU exists.")
            elif product.is_service:
                form.add_error("sku", "Services cannot be restocked.")
            else:
                product.stock_quantity = F("stock_quantity") + form.cleaned_data["quantity"]
                product.save(update_fields=["stock_quantity", "updated_at"])
                messages.success(request, f"Added {form.cleaned_data['quantity']} units to {product.name}. SKU {product.sku} confirmed.")
                return redirect("inventory:products")
    return render(request, "inventory/restock.html", {"form": form, "product": product})
