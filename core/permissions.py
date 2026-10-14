from rest_framework.permissions import BasePermission


def is_admin_or_manager(user):
    """Allow every POS role to manage store operations."""
    return user.is_authenticated and (
        user.is_superuser or user.role in {"admin", "manager", "cashier"}
    )


def is_admin(user):
    """Only an Admin role (or a Django superuser) can manage staff."""
    return user.is_authenticated and (user.is_superuser or user.role == "admin")


def can_use_pos(user):
    """All assigned POS roles may make sales; anonymous users may not."""
    return user.is_authenticated and (
        user.is_superuser or user.role in {"admin", "manager", "cashier"}
    )


class IsAdminOrManager(BasePermission):
    """DRF equivalent of ``is_admin_or_manager`` for protected APIs."""

    def has_permission(self, request, view):
        return is_admin_or_manager(request.user)
