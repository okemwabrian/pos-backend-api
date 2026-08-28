from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import csv

from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from finance.forms import ExpenseForm
from finance.models import Expense
from inventory.models import Product
from sales.models import Invoice
from users.models import ShopSettings
from users.forms import ShopSettingsForm

from .permissions import is_admin_or_manager


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
def dashboard_view(request):
    if request.method == "POST":
        expense_form = ExpenseForm(request.POST)
        if expense_form.is_valid():
            expense = expense_form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, "Expense recorded successfully.")
            return redirect("users:dashboard")
    else:
        expense_form = ExpenseForm()

    total_revenue = Invoice.objects.aggregate(total=Sum("total_amount"))["total"] or 0
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0

    return render(
        request,
        "users/dashboard.html",
        {
            "expense_form": expense_form,
            "revenue": total_revenue,
            "expenses": total_expenses,
            "profit": total_revenue - total_expenses,
            "chart_revenue": float(total_revenue),
            "chart_expenses": float(total_expenses),
            "recent_invoices": Invoice.objects.select_related("cashier", "customer").order_by("-created_at")[:8],
            "recent_expenses": Expense.objects.select_related("user").order_by("-date", "-pk")[:8],
            "low_stock_products": Product.objects.filter(is_service=False, stock_quantity__lte=F("low_stock_threshold")).order_by("stock_quantity")[:8],
        },
    )


@login_required
@user_passes_test(is_admin_or_manager)
@require_http_methods(["GET", "POST"])
def settings_view(request):
    settings = ShopSettings.load()
    form = ShopSettingsForm(request.POST or None, instance=settings)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Shop settings updated.")
        return redirect("settings")
    return render(request, "core/settings.html", {"form": form})


@login_required
@user_passes_test(is_admin_or_manager)
def reports_view(request):
    invoices = Invoice.objects.select_related("cashier", "customer").order_by("-created_at")
    revenue = invoices.aggregate(total=Sum("total_amount"))["total"] or 0
    expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    low_stock = Product.objects.filter(is_service=False, stock_quantity__lte=F("low_stock_threshold")).order_by("stock_quantity")
    return render(request, "core/reports.html", {"invoices": invoices[:50], "revenue": revenue, "expenses": expenses, "profit": revenue - expenses, "low_stock": low_stock})


@login_required
@user_passes_test(is_admin_or_manager)
def reports_csv_view(request, report_type):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{report_type}_report.csv"'
    writer = csv.writer(response)
    if report_type == "stock":
        writer.writerow(["SKU", "Product", "Stock", "Threshold"])
        for product in Product.objects.filter(is_service=False).order_by("name"):
            writer.writerow([product.sku, product.name, product.stock_quantity, product.low_stock_threshold])
    elif report_type == "sales":
        writer.writerow(["Invoice", "Date", "Cashier", "Customer", "Total"])
        for invoice in Invoice.objects.select_related("cashier", "customer").order_by("-created_at"):
            writer.writerow([invoice.pk, invoice.created_at, invoice.cashier.username, invoice.customer or "Walk-in", invoice.total_amount])
    else:
        revenue = Invoice.objects.aggregate(total=Sum("total_amount"))["total"] or 0
        expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
        writer.writerow(["Revenue", "Expenses", "Profit"])
        writer.writerow([revenue, expenses, revenue - expenses])
    return response
