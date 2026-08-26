from django.contrib import admin
from .models import PurchaseOrder, PurchaseItem

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'total_cost', 'is_received', 'order_date')
    inlines = [PurchaseItemInline]