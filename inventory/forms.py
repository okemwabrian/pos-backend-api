from django import forms

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "sku", "category", "cost_price", "retail_price", "wholesale_price", "is_service", "stock_quantity", "low_stock_threshold"]
