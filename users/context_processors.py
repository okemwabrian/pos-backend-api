"""Template context shared by every customer-facing POS screen."""

from django.urls import reverse

from core.store import STORE_NAME, TILL_NUMBER, VAT_RATE
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
        "shop_name": STORE_NAME,
        "store_till_number": TILL_NUMBER,
        "vat_rate": VAT_RATE,
        "current_page": current_page,
        "dashboard_url": reverse("users:dashboard"),
    }
