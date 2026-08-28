import json
from collections import Counter
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets

from inventory.models import Product
from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-created_at')
    serializer_class = InvoiceSerializer


@login_required
@require_http_methods(["GET", "POST"])
@transaction.atomic
def pos_terminal_view(request):
    products = Product.objects.filter(
        Q(stock_quantity__gt=0) | Q(is_service=True)
    ).order_by("name")

    if request.method == "GET":
        return render(request, "sales/pos_terminal.html", {"products": products})

    try:
        submitted_cart = json.loads(request.POST.get("cart", "[]"))
        payment_method = request.POST.get("payment_method", "cash")
        price_type = request.POST.get("price_type", "retail")

        if payment_method not in dict(Invoice.PAYMENT_CHOICES):
            raise ValueError("Choose a valid payment method.")
        if price_type not in {"retail", "wholesale"}:
            raise ValueError("Choose a valid price type.")

        quantities = Counter()
        for item in submitted_cart:
            product_id = int(item["product_id"])
            quantity = int(item["quantity"])
            if quantity <= 0:
                raise ValueError("Product quantities must be greater than zero.")
            quantities[product_id] += quantity

        if not quantities:
            raise ValueError("The cart is empty.")

        locked_products = Product.objects.select_for_update().filter(
            id__in=quantities.keys()
        )
        products_by_id = {product.id: product for product in locked_products}

        if len(products_by_id) != len(quantities):
            raise ValueError("One or more selected products no longer exist.")

        total_amount = Decimal("0.00")
        sale_lines = []

        for product_id, quantity in quantities.items():
            product = products_by_id[product_id]
            if not product.is_service and product.stock_quantity < quantity:
                raise ValueError(
                    f"Not enough stock for {product.name}. "
                    f"Only {product.stock_quantity} remaining."
                )

            price_at_sale = (
                product.wholesale_price
                if price_type == "wholesale"
                else product.retail_price
            )
            total_amount += price_at_sale * quantity
            sale_lines.append((product, quantity, price_at_sale))

        invoice = Invoice.objects.create(
            cashier=request.user,
            payment_method=payment_method,
            total_amount=total_amount,
        )

        InvoiceItem.objects.bulk_create(
            [
                InvoiceItem(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    price_at_sale=price_at_sale,
                )
                for product, quantity, price_at_sale in sale_lines
            ]
        )

        for product, quantity, _ in sale_lines:
            if product.is_service:
                continue
            product.stock_quantity -= quantity
            product.save(update_fields=["stock_quantity", "updated_at"])

    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        transaction.set_rollback(True)
        messages.error(request, str(error) or "The submitted cart is invalid.")
        return redirect("sales:pos_terminal")

    messages.success(request, f"Invoice #{invoice.pk} completed successfully.")
    return redirect("sales:pos_terminal")


@login_required
def generate_receipt_pdf(request, invoice_id):
    invoice = get_object_or_404(
        Invoice.objects.select_related("cashier", "customer").prefetch_related(
            "items__product"
        ),
        pk=invoice_id,
    )
    receipt_items = list(invoice.items.all())
    for item in receipt_items:
        item.line_total = item.quantity * item.price_at_sale

    return render(
        request,
        "sales/receipt.html",
        {"invoice": invoice, "receipt_items": receipt_items},
    )
