from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from crm.models import Customer
from inventory.models import Product

class Invoice(models.Model):
    PAYMENT_CHOICES = (
        ('cash', 'Cash'),
        ('till_number', 'TILL NUMBER'),
        ('paybill', 'PAYBILL'),
        ('send_money', 'SEND MONEY'),
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
    )
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    client_reference = models.UUIDField(null=True, blank=True, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    customer_name = models.CharField(max_length=150, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    till_number = models.CharField(max_length=32, blank=True)
    transaction_code = models.CharField(max_length=64, blank=True)
    payer_name = models.CharField(max_length=150, blank=True)
    paybill_number = models.CharField(max_length=32, blank=True)
    account_number = models.CharField(max_length=64, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    amount_tendered = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    change_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.payment_method == "cash":
            if self.amount_tendered is None:
                raise ValidationError(
                    {"amount_tendered": "Enter the cash amount received."}
                )
            if self.amount_tendered < self.total_amount:
                raise ValidationError(
                    {"amount_tendered": "Amount tendered cannot be less than the total."}
                )
            self.change_amount = self.amount_tendered - self.total_amount
        else:
            self.amount_tendered = None
            self.change_amount = 0

        required_fields = {
            'till_number': self.payment_method == 'till_number',
            'paybill_number': self.payment_method == 'paybill',
            'account_number': self.payment_method == 'paybill',
            'phone_number': self.payment_method == 'send_money',
        }
        errors = {
            field: 'This field is required for the selected payment method.'
            for field, is_required in required_fields.items()
            if is_required and not getattr(self, field).strip()
        }
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Invoice #{self.id} - {self.total_amount}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)
    cost_at_sale = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class Quotation(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quotation #{self.pk} - {self.total_amount}"


class QuotationItem(models.Model):
    quotation = models.ForeignKey(Quotation, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    price_at_quote = models.DecimalField(max_digits=10, decimal_places=2)
