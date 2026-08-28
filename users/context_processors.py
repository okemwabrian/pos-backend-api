"""Template context shared by every customer-facing POS screen."""

from django.urls import reverse

from .models import ShopSettings


PAGE_LABELS = {
    "dashboard": "Dashboard",
    "pos_terminal": "POS Terminal",
    "quotation_detail": "Bills & Quotes",
    "receive_stock": "Receive Stock",
    "products": "Inventory",
    "categories": "Categories",
    "customers": "CRM",
    "suppliers": "CRM",
    "reports": "Reports",
    "settings": "Settings",
    "manage": "User Management",
}


def shop_context(request):
    """Expose the single shop settings record and a simple breadcrumb trail."""
    shop_settings = ShopSettings.load()
    match = getattr(request, "resolver_match", None)
    current_page = PAGE_LABELS.get(
        getattr(match, "url_name", None), "Management Area"
    )

    return {
        "shop_settings": shop_settings,
        "shop_name": shop_settings.shop_name,
        "current_page": current_page,
        "dashboard_url": reverse("users:dashboard"),
    }
