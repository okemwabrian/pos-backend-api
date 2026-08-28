from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm

from .models import CustomUser, ShopSettings


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = ["shop_name", "phone", "email", "address", "currency", "low_stock_alerts"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class StaffUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "phone_number", "role"]


class StaffPasswordForm(SetPasswordForm):
    pass
