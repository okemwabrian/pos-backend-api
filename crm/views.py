from rest_framework import viewsets
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .models import Customer, Supplier
from .serializers import CustomerSerializer, SupplierSerializer
from .forms import CustomerForm, SupplierForm
from core.permissions import IsAdminOrManager, is_admin_or_manager

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrManager]

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminOrManager]


def _crm_redirect(tab):
    return redirect(f"{reverse('crm:manage')}?tab={tab}")


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
def crm_management_view(request):
    """Unified customer and supplier management workspace."""
    active_tab = request.GET.get("tab", "customers")
    if active_tab not in {"customers", "suppliers"}:
        active_tab = "customers"

    if request.method == "POST":
        entity = request.POST.get("entity")
        config = {
            "customer": (Customer, CustomerForm, "customers", "Customer"),
            "supplier": (Supplier, SupplierForm, "suppliers", "Supplier"),
        }.get(entity)
        if not config:
            messages.error(request, "Choose a valid CRM record type.")
            return _crm_redirect(active_tab)

        model, form_class, tab, label = config
        instance = get_object_or_404(model, pk=request.POST.get("id")) if request.POST.get("id") else None
        if request.POST.get("delete"):
            instance.delete()
            messages.success(request, f"{label} deleted.")
            return _crm_redirect(tab)

        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{label} saved.")
            return _crm_redirect(tab)
        active_tab = tab
        customer_form = form if entity == "customer" else CustomerForm()
        supplier_form = form if entity == "supplier" else SupplierForm()
    else:
        customer_instance = (
            get_object_or_404(Customer, pk=request.GET.get("edit_customer"))
            if request.GET.get("edit_customer")
            else None
        )
        supplier_instance = (
            get_object_or_404(Supplier, pk=request.GET.get("edit_supplier"))
            if request.GET.get("edit_supplier")
            else None
        )
        customer_form = CustomerForm(instance=customer_instance)
        supplier_form = SupplierForm(instance=supplier_instance)

    return render(
        request,
        "crm/manage.html",
        {
            "active_tab": active_tab,
            "customers": Customer.objects.order_by("name"),
            "suppliers": Supplier.objects.order_by("name"),
            "customer_form": customer_form,
            "supplier_form": supplier_form,
            "edit_customer_id": customer_form.instance.pk if customer_form.instance.pk else None,
            "edit_supplier_id": supplier_form.instance.pk if supplier_form.instance.pk else None,
        },
    )


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
def customers_view(request):
    return _crm_redirect("customers")


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET"])
def suppliers_view(request):
    return _crm_redirect("suppliers")
