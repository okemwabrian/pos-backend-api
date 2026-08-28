def is_admin_or_manager(user):
    return user.is_authenticated and user.role in {"admin", "manager"}


def is_admin(user):
    return user.is_authenticated and user.role == "admin"
