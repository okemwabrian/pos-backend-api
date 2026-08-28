from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from inventory.models import Product
from .models import PurchaseOrder
from core.permissions import is_admin_or_manager


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
@transaction.atomic
def receive_stock_view(request):
    if request.method == "POST":
        purchase_order_id = request.POST.get("purchase_order_id")
        purchase_order = get_object_or_404(
            PurchaseOrder.objects.select_for_update(),
            pk=purchase_order_id,
            is_received=False,
        )

        received_quantities = {}
        for item in purchase_order.items.all():
            received_quantities[item.product_id] = (
                received_quantities.get(item.product_id, 0) + item.quantity
            )

        if not received_quantities:
            messages.error(request, "This purchase order has no items to receive.")
            return redirect("purchases:receive_stock")

        locked_products = Product.objects.select_for_update().filter(
            pk__in=received_quantities
        )
        for product in locked_products:
            product.stock_quantity = F("stock_quantity") + received_quantities[product.pk]
            product.save(update_fields=["stock_quantity", "updated_at"])

        purchase_order.is_received = True
        purchase_order.received_by = request.user
        purchase_order.received_at = timezone.now()
        purchase_order.save(update_fields=["is_received", "received_by", "received_at"])
        messages.success(request, f"Purchase order #{purchase_order.pk} received.")
        return redirect("purchases:receive_stock")

    purchase_orders = PurchaseOrder.objects.filter(is_received=False).select_related(
        "supplier"
    ).prefetch_related("items__product")
    return render(
        request,
        "purchases/receive_stock.html",
        {"purchase_orders": purchase_orders},
    )
