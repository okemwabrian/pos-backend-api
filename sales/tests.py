import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from inventory.models import Category, Product
from sales.models import Invoice, Quotation
from users.models import CustomUser


class PosTransactionFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="cashier", password="test-password", role="cashier"
        )
        self.product = Product.objects.create(
            name="Test Product",
            sku="TEST-POS-001",
            category=Category.objects.create(name="Test Category"),
            cost_price=Decimal("50.00"),
            retail_price=Decimal("100.00"),
            wholesale_price=Decimal("80.00"),
            stock_quantity=10,
        )
        self.client.force_login(self.user)

    def post_cart(self, action):
        return self.client.post(
            reverse("sales:pos_terminal"),
            {
                "cart": json.dumps([{"product_id": self.product.pk, "quantity": 2}]),
                "action": action,
                "payment_method": "cash",
                "price_type": "retail",
                "discount": "0",
            },
        )

    def test_invoice_creates_items_deducts_stock_and_opens_receipt(self):
        response = self.post_cart("invoice")

        invoice = Invoice.objects.get()
        self.assertRedirects(response, reverse("sales:receipt", args=[invoice.pk]))
        self.assertEqual(invoice.total_amount, Decimal("200.00"))
        self.assertEqual(invoice.items.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8)

    def test_quotation_creates_items_without_deducting_stock(self):
        response = self.post_cart("quotation")

        quotation = Quotation.objects.get()
        self.assertRedirects(response, reverse("sales:bills_quotes"))
        self.assertEqual(quotation.total_amount, Decimal("200.00"))
        self.assertEqual(quotation.items.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)
