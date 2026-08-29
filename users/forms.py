from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm

from .models import CustomUser, ShopSettings


class ShopSettingsForm(forms.ModelForm):
    class Meta:
        model = ShopSettings
        fields = ["shop_name", "phone", "email", "address", "low_stock_alerts"]
        widgets = {"address": forms.Textarea(attrs={"rows": 3})}


class StaffUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "phone_number", "role"]


class PublicRegistrationForm(UserCreationForm):
    """Account creation form available from the sign-in screen.

    Publicly created accounts always start as cashiers.  Roles remain under
    the control of an administrator from the user-management screen.
    """

    class Meta:
        model = CustomUser
        fields = ["username", "first_name", "last_name", "email", "phone_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "cashier"
        if commit:
            user.save()
            self.save_m2m()
        return user


class StaffPasswordForm(SetPasswordForm):
    pass
