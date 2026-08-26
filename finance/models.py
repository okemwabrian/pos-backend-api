from django.db import models
from django.conf import settings

class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('salaries', 'Salaries'),
        ('supplies', 'Supplies'),
        ('other', 'Other'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.amount}"