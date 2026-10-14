import json
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from crm.models import Customer
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
        data = {
            "cart": json.dumps([{"product_id": self.product.pk, "quantity": 2}]),
            "action": action,
            "payment_method": "cash",
            "price_type": "retail",
            "discount": "0",
            "customer_name": "POS Customer",
        }
        if action == "invoice":
            data["amount_tendered"] = "200.00"
        return self.client.post(reverse("sales:pos_terminal"), data)

    def test_invoice_creates_items_deducts_stock_and_opens_receipt(self):
        response = self.post_cart("invoice")

        invoice = Invoice.objects.get()
        self.assertRedirects(response, reverse("sales:receipt", args=[invoice.pk]))
        self.assertEqual(invoice.total_amount, Decimal("200.00"))
        self.assertEqual(invoice.amount_tendered, Decimal("200.00"))
        self.assertEqual(invoice.change_amount, Decimal("0.00"))
        self.assertEqual(invoice.items.count(), 1)
        self.assertEqual(invoice.items.get().cost_at_sale, Decimal("50.00"))
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

    def test_paybill_details_are_saved_and_printed_on_receipt(self):
        response = self.client.post(
            reverse("sales:pos_terminal"),
            {
                "cart": json.dumps([{"product_id": self.product.pk, "quantity": 1}]),
                "action": "invoice",
                "payment_method": "paybill",
                "paybill_number": "123456",
                "account_number": "ORDER-9",
                "customer_name": "Alice Buyer",
                "price_type": "retail",
                "discount": "0",
            },
        )

        invoice = Invoice.objects.get()
        self.assertRedirects(response, reverse("sales:receipt", args=[invoice.pk]))
        self.assertEqual(invoice.paybill_number, "123456")
        self.assertEqual(invoice.account_number, "ORDER-9")
        receipt = self.client.get(reverse("sales:receipt", args=[invoice.pk]))
        self.assertContains(receipt, "Paid via:</strong> PAYBILL")
        self.assertContains(receipt, "Paybill:</strong> 123456")
        self.assertContains(receipt, "Acc:</strong> ORDER-9")
        self.assertContains(receipt, "CHIWAS LIQUOR STORE &amp; RESTAURANT")
        self.assertContains(receipt, "Alice Buyer")
        self.assertContains(receipt, "chiwas-logo.svg")

    def test_cash_tender_calculates_change_and_receipt_customer(self):
        customer = Customer.objects.create(name="Jane Customer", phone="0712345678")
        response = self.client.post(
            reverse("sales:pos_terminal"),
            {
                "cart": json.dumps([{"product_id": self.product.pk, "quantity": 1}]),
                "action": "invoice",
                "payment_method": "cash",
                "amount_tendered": "150.00",
                "customer_id": customer.pk,
                "price_type": "retail",
                "discount": "0",
            },
        )

        invoice = Invoice.objects.get()
        self.assertRedirects(response, reverse("sales:receipt", args=[invoice.pk]))
        self.assertEqual(invoice.amount_tendered, Decimal("150.00"))
        self.assertEqual(invoice.change_amount, Decimal("50.00"))
        receipt = self.client.get(reverse("sales:receipt", args=[invoice.pk]))
        self.assertContains(receipt, "Customer:</strong> Jane Customer")
        self.assertContains(receipt, "CHANGE")
        self.assertContains(receipt, "50.00")

    def test_till_payer_name_is_saved_and_printed(self):
        response = self.client.post(
            reverse("sales:pos_terminal"),
            {
                "cart": json.dumps([{"product_id": self.product.pk, "quantity": 1}]),
                "action": "invoice",
                "payment_method": "till_number",
                "till_number": "987654",
                "transaction_code": "QW123",
                "payer_name": "A. Customer",
                "customer_name": "Till Customer",
                "price_type": "retail",
                "discount": "0",
            },
        )

        invoice = Invoice.objects.get()
        self.assertRedirects(response, reverse("sales:receipt", args=[invoice.pk]))
        self.assertEqual(invoice.payer_name, "A. Customer")
        receipt = self.client.get(reverse("sales:receipt", args=[invoice.pk]))
        self.assertContains(receipt, "Payer:</strong> A. Customer")

    def test_invoice_requires_receipt_customer_name(self):
        response = self.client.post(
            reverse("sales:pos_terminal"),
            {
                "cart": json.dumps([{"product_id": self.product.pk, "quantity": 1}]),
                "action": "invoice",
                "payment_method": "paybill",
                "paybill_number": "123456",
                "account_number": "ORDER-9",
                "price_type": "retail",
                "discount": "0",
            },
        )

        self.assertRedirects(response, reverse("sales:pos_terminal"))
        self.assertFalse(Invoice.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

    def test_cash_tender_below_total_is_rejected_without_stock_deduction(self):
        response = self.client.post(
            reverse("sales:pos_terminal"),
            {
                "cart": json.dumps([{"product_id": self.product.pk, "quantity": 1}]),
                "action": "invoice",
                "payment_method": "cash",
                "amount_tendered": "99.99",
                "price_type": "retail",
                "discount": "0",
            },
        )

        self.assertRedirects(response, reverse("sales:pos_terminal"))
        self.assertFalse(Invoice.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

    def test_cash_tender_is_required(self):
        response = self.client.post(
            reverse("sales:pos_terminal"),
            {
                "cart": json.dumps([{"product_id": self.product.pk, "quantity": 1}]),
                "action": "invoice",
                "payment_method": "cash",
                "price_type": "retail",
                "discount": "0",
            },
        )

        self.assertRedirects(response, reverse("sales:pos_terminal"))
        self.assertFalse(Invoice.objects.exists())

    def test_invoice_requires_payment_details_for_selected_method(self):
        response = self.client.post(
            reverse("sales:pos_terminal"),
            {
                "cart": json.dumps([{"product_id": self.product.pk, "quantity": 1}]),
                "action": "invoice",
                "payment_method": "paybill",
                "price_type": "retail",
                "discount": "0",
            },
        )

        self.assertRedirects(response, reverse("sales:pos_terminal"))
        self.assertFalse(Invoice.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)
