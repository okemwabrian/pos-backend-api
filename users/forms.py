from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm

from .models import CustomUser, ShopSettings


class FirstAdminSetupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "phone_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "admin"
        user.is_staff = True
        user.is_superuser = True
        if commit:
            user.save()
        return user


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = ["phone", "email", "address", "low_stock_alerts"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class StaffUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "phone_number", "role"]


class StaffPasswordForm(SetPasswordForm):
    pass
