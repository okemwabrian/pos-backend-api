import uuid
from decimal import Decimal

from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import Category, Product, StockAdjustment
from sales.models import Invoice
from users.models import CustomUser


class OfflineSyncApiTests(APITestCase):
    def setUp(self):
        self.cashier = CustomUser.objects.create_user(
            username="offline-cashier",
            password="test-password",
            role="cashier",
        )
        self.manager = CustomUser.objects.create_user(
            username="offline-manager",
            password="test-password",
            role="manager",
        )
        self.product = Product.objects.create(
            name="Test Bottle",
            sku="OFFLINE-001",
            category=Category.objects.create(name="Offline Test"),
            cost_price=Decimal("50.00"),
            retail_price=Decimal("100.00"),
            wholesale_price=Decimal("80.00"),
            stock_quantity=10,
            low_stock_threshold=5,
        )

    def authenticate_as(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_cashier_can_login_and_fetch_catalog(self):
        response = self.client.post(
            reverse("offline:login"),
            {"username": self.cashier.username, "password": "test-password"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "cashier")
        self.assertTrue(response.data["can_adjust_stock"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")

        catalog = self.client.get(reverse("offline:catalog"))
        self.assertEqual(catalog.status_code, 200)
        self.assertEqual(catalog.data["products"][0]["low_stock_threshold"], 5)

    def test_sale_sync_is_idempotent_and_deducts_stock_once(self):
        self.authenticate_as(self.cashier)
        operation = {
            "id": str(uuid.uuid4()),
            "type": "sale",
            "data": {
                "items": [{"product_id": self.product.pk, "quantity": 2}],
                "payment_method": "paybill",
                "paybill_number": "123456",
                "account_number": "ORDER-8",
                "customer_name": "Mobile Customer",
                "price_type": "retail",
                "discount": "0",
            },
        }

        first = self.client.post(
            reverse("offline:sync"), {"operations": [operation]}, format="json"
        )
        duplicate = self.client.post(
            reverse("offline:sync"), {"operations": [operation]}, format="json"
        )

        self.assertEqual(first.data["results"][0]["status"], "synced")
        self.assertTrue(duplicate.data["results"][0]["already_synced"])
        self.assertEqual(Invoice.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8)

    def test_invalid_sale_details_do_not_deduct_stock(self):
        self.authenticate_as(self.cashier)
        response = self.client.post(
            reverse("offline:sync"),
            {
                "operations": [
                    {
                        "id": str(uuid.uuid4()),
                        "type": "sale",
                        "data": {
                            "items": [{"product_id": self.product.pk, "quantity": 1}],
                            "payment_method": "paybill",
                            "paybill_number": "123456",
                            "customer_name": "Mobile Customer",
                            "price_type": "retail",
                            "discount": "0",
                        },
                    }
                ]
            },
            format="json",
        )

        self.assertEqual(response.data["results"][0]["status"], "rejected")
        self.assertFalse(Invoice.objects.exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

    def test_manager_restock_sync_is_idempotent(self):
        self.authenticate_as(self.manager)
        operation = {
            "id": str(uuid.uuid4()),
            "type": "restock",
            "data": {"product_id": self.product.pk, "quantity": 4},
        }

        first = self.client.post(
            reverse("offline:sync"), {"operations": [operation]}, format="json"
        )
        duplicate = self.client.post(
            reverse("offline:sync"), {"operations": [operation]}, format="json"
        )

        self.assertEqual(first.data["results"][0]["status"], "synced")
        self.assertTrue(duplicate.data["results"][0]["already_synced"])
        self.assertEqual(StockAdjustment.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 14)

    def test_cashier_can_sync_restock_idempotently(self):
        self.authenticate_as(self.cashier)
        operation = {
            "id": str(uuid.uuid4()),
            "type": "restock",
            "data": {"product_id": self.product.pk, "quantity": 2},
        }
        response = self.client.post(
            reverse("offline:sync"),
            {"operations": [operation]},
            format="json",
        )

        self.assertEqual(response.data["results"][0]["status"], "synced")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 12)
        duplicate = self.client.post(
            reverse("offline:sync"),
            {"operations": [operation]},
            format="json",
        )
        self.assertTrue(duplicate.data["results"][0]["already_synced"])
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 12)
