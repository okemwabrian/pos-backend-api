from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import calendar
import csv
from datetime import date, timedelta

from django.db.models import Count, F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from finance.forms import ExpenseForm
from finance.models import Expense
from inventory.models import Product
from crm.models import Customer
from sales.models import Invoice, Quotation
from users.models import ShopSettings
from users.forms import ShopSettingsForm

from .permissions import can_use_pos, is_admin_or_manager
from .exporting import pdf_response, xlsx_response


def _period_bounds(period):
    today = timezone.localdate()
    if period == "weekly":
        return today - timedelta(days=today.weekday()), today, "This week"
    if period == "monthly":
        return today.replace(day=1), today, "This month"
    return today, today, "Today"


def _sales_activity(invoices, quotations, limit=50):
    activity = [
        {
            "kind": "Invoice",
            "number": invoice.pk,
            "created_at": invoice.created_at,
            "cashier": invoice.cashier,
            "customer": invoice.customer,
            "total": invoice.total_amount,
        }
        for invoice in invoices
    ]
    activity.extend(
        {
            "kind": "Quotation",
            "number": quotation.pk,
            "created_at": quotation.created_at,
            "cashier": quotation.cashier,
            "customer": quotation.customer,
            "total": quotation.total_amount,
        }
        for quotation in quotations
    )
    return sorted(activity, key=lambda item: item["created_at"], reverse=True)[:limit]


def _activity_calendar(month_value):
    """Build a month grid with invoice, quotation, and expense totals per day."""
    today = timezone.localdate()
    try:
        displayed_month = date.fromisoformat(f"{month_value}-01") if month_value else today.replace(day=1)
    except ValueError:
        displayed_month = today.replace(day=1)

    month_start = displayed_month.replace(day=1)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)
    month_end = next_month - timedelta(days=1)

    invoice_counts = {}
    for created_at in Invoice.objects.filter(
        created_at__date__range=(month_start, month_end)
    ).values_list("created_at", flat=True):
        day = timezone.localtime(created_at).date()
        invoice_counts[day] = invoice_counts.get(day, 0) + 1

    quotation_counts = {}
    for created_at in Quotation.objects.filter(
        created_at__date__range=(month_start, month_end)
    ).values_list("created_at", flat=True):
        day = timezone.localtime(created_at).date()
        quotation_counts[day] = quotation_counts.get(day, 0) + 1

    expense_counts = {
        row["date"]: row["count"]
        for row in Expense.objects.filter(date__range=(month_start, month_end))
        .values("date")
        .annotate(count=Count("id"))
    }

    weeks = []
    for week in calendar.Calendar(firstweekday=0).monthdatescalendar(
        month_start.year, month_start.month
    ):
        weeks.append(
            [
                {
                    "date": day,
                    "is_current_month": day.month == month_start.month,
                    "is_today": day == today,
                    "invoices": invoice_counts.get(day, 0),
                    "quotations": quotation_counts.get(day, 0),
                    "expenses": expense_counts.get(day, 0),
                }
                for day in week
            ]
        )

    return {
        "calendar_month": month_start,
        "calendar_weeks": weeks,
        "previous_month": month_start - timedelta(days=1),
        "next_month": next_month,
    }


def report_preview_data(report_type):
    """The one data source used by the on-screen preview and file downloads."""
    if report_type == "stock":
        headers = ["SKU", "Product", "Category", "Stock", "Threshold"]
        rows = [
            [product.sku, product.name, product.category or "Uncategorised", product.stock_quantity, product.low_stock_threshold]
            for product in Product.objects.select_related("category").filter(is_service=False).order_by("name")
        ]
        return "Inventory Preview", headers, rows
    if report_type == "sales":
        headers = ["Type", "Reference", "Date", "Cashier", "Customer", "Total"]
        rows = [
            [item["kind"], f"#{item['number']}", item["created_at"].strftime("%d %b %Y %H:%M"), item["cashier"].username, item["customer"] or "Walk-in", item["total"]]
            for item in _sales_activity(
                Invoice.objects.select_related("cashier", "customer").all(),
                Quotation.objects.select_related("cashier", "customer").all(),
                limit=500,
            )
        ]
        return "Sales & Quotations Preview", headers, rows
    revenue = Invoice.objects.aggregate(total=Sum("total_amount"))["total"] or 0
    expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    return "Profit Preview", ["Metric", "Amount"], [["Revenue", revenue], ["Expenses", expenses], ["Profit", revenue - expenses]]


@require_http_methods(["GET", "POST"])
@login_required
def dashboard_view(request):
    # Cashiers sign in directly to the only operational screen they need.
    if not is_admin_or_manager(request.user):
        if can_use_pos(request.user):
            return redirect("sales:pos_terminal")
        return redirect("login")
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

    period = request.GET.get("period", "daily")
    if period not in {"daily", "weekly", "monthly"}:
        period = "daily"
    start_date, end_date, period_label = _period_bounds(period)
    invoices = Invoice.objects.filter(created_at__date__range=(start_date, end_date))
    quotations = Quotation.objects.filter(created_at__date__range=(start_date, end_date))
    total_revenue = invoices.aggregate(total=Sum("total_amount"))["total"] or 0
    total_expenses = Expense.objects.filter(date__range=(start_date, end_date)).aggregate(total=Sum("amount"))["total"] or 0
    calendar_context = _activity_calendar(request.GET.get("month"))

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
            "period": period,
            "period_label": period_label,
            "period_start": start_date,
            "period_end": end_date,
            "recent_activity": _sales_activity(
                invoices.select_related("cashier", "customer"),
                quotations.select_related("cashier", "customer"),
                limit=8,
            ),
            "recent_expenses": Expense.objects.select_related("user").order_by("-date", "-pk")[:8],
            "low_stock_products": Product.objects.filter(is_service=False, stock_quantity__lte=F("low_stock_threshold")).order_by("stock_quantity")[:8],
            **calendar_context,
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
    preview_type = request.GET.get("preview", "sales")
    if preview_type not in {"stock", "sales", "profit"}:
        preview_type = "sales"
    preview_title, preview_headers, preview_rows = report_preview_data(preview_type)
    quotations = Quotation.objects.select_related("cashier", "customer").order_by("-created_at")
    return render(
        request,
        "core/reports.html",
        {
            "activity": _sales_activity(invoices, quotations),
            "quotations": quotations[:50],
            "revenue": revenue,
            "expenses": expenses,
            "profit": revenue - expenses,
            "low_stock": low_stock,
            "report_products": Product.objects.select_related("category").order_by("name"),
            "report_customers": Customer.objects.order_by("name"),
            "preview_type": preview_type,
            "preview_title": preview_title,
            "preview_headers": preview_headers,
            "preview_rows": preview_rows[:100],
        },
    )


@login_required
@user_passes_test(is_admin_or_manager)
def product_report_view(request, product_id):
    product = get_object_or_404(Product.objects.select_related("category"), pk=product_id)
    invoice_items = list(
        product.invoiceitem_set.select_related("invoice", "invoice__customer", "invoice__cashier")
        .order_by("-invoice__created_at")
    )
    units_sold = sum(item.quantity for item in invoice_items)
    sales_total = 0
    for item in invoice_items:
        item.line_total = item.quantity * item.price_at_sale
        sales_total += item.line_total
    return render(
        request,
        "core/product_report.html",
        {
            "product": product,
            "invoice_items": invoice_items,
            "units_sold": units_sold,
            "sales_total": sales_total,
        },
    )


@login_required
@user_passes_test(is_admin_or_manager)
def customer_report_view(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    invoices = customer.invoice_set.select_related("cashier").prefetch_related("items__product").order_by("-created_at")
    total_spent = invoices.aggregate(total=Sum("total_amount"))["total"] or 0
    return render(
        request,
        "core/customer_report.html",
        {"customer": customer, "invoices": invoices, "total_spent": total_spent},
    )


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


@login_required
@user_passes_test(is_admin_or_manager)
def reports_download_view(request, report_type, export_format):
    if report_type not in {"stock", "sales", "profit"} or export_format not in {"xlsx", "pdf"}:
        return HttpResponse("Unknown report export.", status=404)
    title, headers, rows = report_preview_data(report_type)
    filename = report_type + "_report"
    if export_format == "xlsx":
        return xlsx_response(filename, title, headers, rows)
    return pdf_response(filename, title, headers, rows)
