from core.views import dashboard_view
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from core.permissions import is_admin
from .forms import StaffPasswordForm, StaffUserForm
from .models import CustomUser

__all__ = ["dashboard_view"]


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def user_management_view(request):
    form = StaffUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "User created.")
        return redirect("users:manage")
    return render(request, "users/manage.html", {"form": form, "users": CustomUser.objects.order_by("username")})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def reset_password_view(request, user_id):
    staff_user = get_object_or_404(CustomUser, pk=user_id)
    form = StaffPasswordForm(staff_user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Password reset for {staff_user.username}.")
        return redirect("users:manage")
    return render(request, "users/reset_password.html", {"form": form, "staff_user": staff_user})
