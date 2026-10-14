from django.conf import settings
from django.db import models


BOTTLE_SIZE_CHOICES = (
    ("250ml", "250 ml"),
    ("330ml", "330 ml"),
    ("350ml", "350 ml"),
    ("500ml", "500 ml"),
    ("750ml", "750 ml"),
    ("1L", "1 L"),
    ("Crate/Tot", "Crate / Tot"),
)


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Optional image URL for the POS category card.")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True, help_text="Barcode or Stock Keeping Unit")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    image = models.ImageField(upload_to="products/", blank=True)
    image_url = models.URLField(blank=True, help_text="Optional product image URL.")
    bottle_size = models.CharField(
        max_length=10,
        choices=BOTTLE_SIZE_CHOICES,
        blank=True,
        help_text="Bottle or package size for drinks.",
    )
    
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2)
    units_per_case = models.PositiveIntegerField(
        default=1,
        help_text="Number of individual units in a crate or carton.",
    )
    case_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional selling price for one full crate or carton.",
    )
    
    # Stock Management
    is_service = models.BooleanField(default=False)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Stock: {self.stock_quantity})"


class StockAdjustment(models.Model):
    client_reference = models.UUIDField(unique=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Restock {self.product.name} (+{self.quantity})"
