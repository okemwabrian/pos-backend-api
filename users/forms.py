from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import CustomUser, ShopSettings


class FirstAdminSetupForm(forms.Form):
    brian_password = forms.CharField(
        label="Brian's password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    brian_password_confirm = forms.CharField(
        label="Confirm Brian's password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    chiwas_password = forms.CharField(
        label="Chiwas's password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    chiwas_password_confirm = forms.CharField(
        label="Confirm Chiwas's password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned_data = super().clean()
        accounts = (
            ("Brian", "brian_password", "brian_password_confirm"),
            ("Chiwas", "chiwas_password", "chiwas_password_confirm"),
        )
        for username, password_field, confirmation_field in accounts:
            password = cleaned_data.get(password_field)
            confirmation = cleaned_data.get(confirmation_field)
            if not password or not confirmation:
                continue
            if password != confirmation:
                self.add_error(confirmation_field, "The passwords do not match.")
                continue
            user = CustomUser(username=username, first_name=username)
            try:
                password_validation.validate_password(password, user=user)
            except ValidationError as error:
                self.add_error(password_field, error)
        return cleaned_data

    def save(self):
        if not self.is_valid():
            raise ValueError("Cannot create the initial administrators from an invalid form.")
        brian = CustomUser.objects.create_superuser(
            username="Brian",
            first_name="Brian",
            role="admin",
            password=self.cleaned_data["brian_password"],
        )
        CustomUser.objects.create_superuser(
            username="Chiwas",
            first_name="Chiwas",
            role="admin",
            password=self.cleaned_data["chiwas_password"],
        )
        return brian


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
