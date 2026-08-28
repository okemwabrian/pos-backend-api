from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

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

        for item in purchase_order.items.select_related("product").select_for_update():
            item.product.stock_quantity += item.quantity
            item.product.save(update_fields=["stock_quantity", "updated_at"])

        purchase_order.is_received = True
        purchase_order.save(update_fields=["is_received"])
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
