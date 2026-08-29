from core.views import dashboard_view
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from core.permissions import is_admin
from .forms import PublicRegistrationForm, StaffPasswordForm, StaffUserForm
from .models import CustomUser

__all__ = ["dashboard_view"]


@login_required
@user_passes_test(is_admin)
@require_http_methods(["GET", "POST"])
def user_management_view(request):
    if request.method == "POST" and request.POST.get("action") == "update_role":
        staff_user = get_object_or_404(CustomUser, pk=request.POST.get("user_id"))
        role = request.POST.get("role")
        valid_roles = dict(CustomUser.ROLE_CHOICES)
        if role not in valid_roles:
            messages.error(request, "Choose a valid role.")
        elif staff_user.is_superuser:
            messages.error(request, "A Django superuser already has unrestricted access.")
        else:
            staff_user.role = role
            staff_user.save(update_fields=["role"])
            messages.success(request, f"Role updated for {staff_user.username}.")
        return redirect("users:manage")

    if request.method == "POST" and request.POST.get("action") == "toggle_active":
        staff_user = get_object_or_404(CustomUser, pk=request.POST.get("user_id"))
        if staff_user == request.user:
            messages.error(request, "You cannot disable your own account.")
        elif staff_user.is_superuser:
            messages.error(request, "Superuser accounts cannot be disabled here.")
        else:
            staff_user.is_active = not staff_user.is_active
            staff_user.save(update_fields=["is_active"])
            state = "enabled" if staff_user.is_active else "disabled"
            messages.success(request, f"{staff_user.username} has been {state}.")
        return redirect("users:manage")

    form = StaffUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "User created.")
        return redirect("users:manage")
    return render(
        request,
        "users/manage.html",
        {
            "form": form,
            "users": CustomUser.objects.order_by("username"),
            "role_choices": CustomUser.ROLE_CHOICES,
        },
    )


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    form = PublicRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created. You can now sign in.")
        return redirect("login")
    return render(request, "registration/register.html", {"form": form})


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
