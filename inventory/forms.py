from django import forms

from .models import Category, Product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "image_url"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "sku", "category", "image_url", "cost_price", "retail_price", "wholesale_price", "is_service", "stock_quantity", "low_stock_threshold"]


class RestockForm(forms.Form):
    sku = forms.CharField(max_length=50, help_text="Scan or type the product SKU to confirm.")
    quantity = forms.IntegerField(min_value=1, help_text="Quantity to add to stock.")
