from django.test import TestCase
from django.urls import reverse

from .models import CustomUser

class AccountAccessTests(TestCase):
    def setUp(self):
        self.admin_user = CustomUser.objects.create_user(
            username="admin", password="safe-password", role="admin"
        )
        self.cashier = CustomUser.objects.create_user(
            username="cashier", password="safe-password", role="cashier"
        )

    def test_public_registration_does_not_create_privileged_accounts(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "new-cashier",
                "first_name": "New",
                "last_name": "Cashier",
                "email": "new@example.com",
                "phone_number": "0712345678",
                "password1": "A-secure-password123",
                "password2": "A-secure-password123",
            },
        )

        self.assertRedirects(response, reverse("login"))
        self.assertFalse(CustomUser.objects.filter(username="new-cashier").exists())
        self.assertContains(self.client.get(reverse("login")), "Ask the store administrator")

    def test_empty_database_allows_owner_created_first_admin_only_once(self):
        self.client.logout()
        CustomUser.objects.all().delete()
        response = self.client.get(reverse("users:first_admin_setup"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("users:first_admin_setup"),
            {
                "username": "store-owner",
                "first_name": "Store",
                "last_name": "Owner",
                "email": "owner@example.com",
                "phone_number": "0712345678",
                "password1": "Stronger-Owner-Password-882!",
                "password2": "Stronger-Owner-Password-882!",
            },
        )

        self.assertRedirects(response, reverse("users:dashboard"))
        owner = CustomUser.objects.get(username="store-owner")
        self.assertTrue(owner.is_superuser)
        self.assertTrue(owner.is_staff)
        self.assertEqual(owner.role, "admin")
        self.assertTrue("_auth_user_id" in self.client.session)
        self.assertRedirects(
            self.client.get(reverse("users:first_admin_setup")),
            reverse("login"),
        )

    def test_admin_can_disable_a_user_and_disabled_user_cannot_sign_in(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse("users:manage"),
            {"action": "toggle_active", "user_id": self.cashier.pk},
        )

        self.assertRedirects(response, reverse("users:manage"))
        self.cashier.refresh_from_db()
        self.assertFalse(self.cashier.is_active)
        self.client.logout()
        response = self.client.post(
            reverse("login"),
            {"username": "cashier", "password": "safe-password"},
        )
        self.assertContains(response, "disabled")

    def test_cashier_can_manage_store_data_and_view_reports(self):
        self.client.force_login(self.cashier)
        urls = [
            reverse("users:dashboard"),
            reverse("inventory:products"),
            reverse("inventory:categories"),
            reverse("inventory:restock"),
            reverse("purchases:receive_stock"),
            reverse("crm:manage"),
            reverse("reports"),
            reverse("settings"),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
