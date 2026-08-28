import csv
import json
from collections import Counter
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets

from inventory.models import Category, Product
from crm.models import Customer
from .models import Invoice, InvoiceItem, Quotation, QuotationItem
from .serializers import InvoiceSerializer
from core.permissions import IsAdminOrManager, can_use_pos

class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-created_at')
    serializer_class = InvoiceSerializer
    permission_classes = [IsAdminOrManager]


@login_required
@user_passes_test(can_use_pos)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def pos_terminal_view(request):
    products = Product.objects.filter(
        Q(stock_quantity__gt=0) | Q(is_service=True)
    ).order_by("name")

    if request.method == "GET":
        return render(
            request,
            "sales/pos_terminal.html",
            {
                "products": products.select_related("category"),
                "categories": Category.objects.filter(products__in=products)
                .distinct()
                .annotate(
                    product_count=Count(
                        "products",
                        filter=Q(products__stock_quantity__gt=0)
                        | Q(products__is_service=True),
                    )
                )
                .order_by("name"),
                "customers": Customer.objects.order_by("name"),
            },
        )

    try:
        submitted_cart = json.loads(request.POST.get("cart", "[]"))
        payment_method = request.POST.get("payment_method", "cash")
        price_type = request.POST.get("price_type", "retail")
        action = request.POST.get("action", "invoice")
        customer_id = request.POST.get("customer_id")
        discount = Decimal(request.POST.get("discount", "0") or "0")
        comment = request.POST.get("comment", "").strip()

        if payment_method not in dict(Invoice.PAYMENT_CHOICES):
            raise ValueError("Choose a valid payment method.")
        if price_type not in {"retail", "wholesale"}:
            raise ValueError("Choose a valid price type.")
        if action not in {"invoice", "quotation"}:
            raise ValueError("Choose a valid checkout action.")
        if discount < 0:
            raise ValueError("Discount cannot be negative.")

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

        subtotal = Decimal("0.00")
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
            subtotal += price_at_sale * quantity
            sale_lines.append((product, quantity, price_at_sale))

        if discount > subtotal:
            raise ValueError("Discount cannot exceed the cart subtotal.")
        customer = Customer.objects.filter(pk=customer_id).first() if customer_id else None
        total_amount = subtotal - discount
        if action == "quotation":
            quotation = Quotation.objects.create(customer=customer, cashier=request.user, subtotal=subtotal, discount_amount=discount, total_amount=total_amount, comment=comment)
            QuotationItem.objects.bulk_create([QuotationItem(quotation=quotation, product=product, quantity=quantity, price_at_quote=price) for product, quantity, price in sale_lines])
            messages.success(request, f"Quotation #{quotation.pk} saved. Stock was not deducted.")
            return redirect("sales:bills_quotes")

        invoice = Invoice.objects.create(
            cashier=request.user,
            customer=customer,
            payment_method=payment_method,
            total_amount=total_amount,
            discount_amount=discount,
            comment=comment,
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

    except (json.JSONDecodeError, KeyError, TypeError, ValueError, InvalidOperation) as error:
        transaction.set_rollback(True)
        messages.error(request, str(error) or "The submitted cart is invalid.")
        return redirect("sales:pos_terminal")

    messages.success(request, f"Invoice #{invoice.pk} completed successfully.")
    return redirect("sales:receipt", invoice_id=invoice.pk)


@login_required
@user_passes_test(can_use_pos)
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


@login_required
@user_passes_test(can_use_pos)
def bills_and_quotes_view(request):
    """Display lists of Invoices (Bills) and Quotations in a single view.

    Both QuerySets are ordered by most recent creation date.
    """
    invoices = (
        Invoice.objects.select_related("customer", "cashier")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )
    quotations = (
        Quotation.objects.select_related("customer", "cashier")
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    return render(
        request,
        "sales/bills_quotes.html",
        {"invoices": invoices, "quotations": quotations},
    )


@login_required
@user_passes_test(can_use_pos)
def quotation_detail_view(request, quotation_id):
    quotation = get_object_or_404(Quotation.objects.select_related("customer", "cashier").prefetch_related("items__product"), pk=quotation_id)
    return render(request, "sales/quotation_detail.html", {"quotation": quotation})


@login_required
@user_passes_test(can_use_pos)
def quotation_csv_view(request, quotation_id):
    quotation = get_object_or_404(Quotation.objects.prefetch_related("items__product"), pk=quotation_id)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="quotation-{quotation.pk}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Product", "Quantity", "Unit price", "Line total"])
    for item in quotation.items.all():
        writer.writerow([item.product.name, item.quantity, item.price_at_quote, item.quantity * item.price_at_quote])
    writer.writerow(["", "", "Discount", quotation.discount_amount])
    writer.writerow(["", "", "Total", quotation.total_amount])
    return response
