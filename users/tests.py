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

    def test_public_registration_creates_a_cashier_account(self):
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
        user = CustomUser.objects.get(username="new-cashier")
        self.assertEqual(user.role, "cashier")
        self.assertTrue(user.is_active)

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
