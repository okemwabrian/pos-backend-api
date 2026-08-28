from rest_framework import viewsets
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from .models import Customer, Supplier
from .serializers import CustomerSerializer, SupplierSerializer
from .forms import CustomerForm, SupplierForm
from core.permissions import is_admin_or_manager

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


def _crud_view(request, model, form_class, title, object_name):
    instance = get_object_or_404(model, pk=request.POST.get("id")) if request.POST.get("id") else None
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST" and request.POST.get("delete"):
        instance.delete()
        messages.success(request, f"{title} deleted.")
        return redirect(object_name)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"{title} saved.")
        return redirect(object_name)
    return render(request, "crm/entity_list.html", {"title": title, "objects": model.objects.all().order_by("name"), "form": form, "object_name": object_name, "edit_id": instance.pk if instance else None})


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
def customers_view(request):
    return _crud_view(request, Customer, CustomerForm, "Customers", "crm:customers")


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
def suppliers_view(request):
    return _crud_view(request, Supplier, SupplierForm, "Suppliers", "crm:suppliers")
