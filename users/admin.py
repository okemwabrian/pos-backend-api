from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    actions = ['enable_users', 'disable_users']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone_number')}),
    )

    @admin.action(description="Enable selected users")
    def enable_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Disable selected users")
    def disable_users(self, request, queryset):
        queryset.filter(is_superuser=False).update(is_active=False)

admin.site.register(CustomUser, CustomUserAdmin)
