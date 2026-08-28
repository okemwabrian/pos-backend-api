from django import forms

from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "description", "amount"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Expense description"}
            ),
            "amount": forms.NumberInput(
                attrs={"class": "form-control", "min": "0.01", "step": "0.01"}
            ),
        }
