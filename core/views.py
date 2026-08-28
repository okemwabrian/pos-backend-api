from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from finance.forms import ExpenseForm

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

    return render(request, "users/dashboard.html", {"expense_form": expense_form})
