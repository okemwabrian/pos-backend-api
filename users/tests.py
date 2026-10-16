from django.test import TestCase
from django.urls import reverse

from django.conf import settings

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

    def test_empty_database_allows_creation_of_both_superusers_only_once(self):
        self.client.logout()
        CustomUser.objects.all().delete()
        response = self.client.get(reverse("users:first_admin_setup"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("users:first_admin_setup"),
            {
                "brian_password": "1234",
                "brian_password_confirm": "1234",
                "chiwas_password": "2580",
                "chiwas_password_confirm": "2580",
            },
        )

        self.assertRedirects(response, reverse("users:dashboard"))
        administrators = CustomUser.objects.order_by("username")
        self.assertEqual(list(administrators.values_list("username", flat=True)), ["Brian", "Chiwas"])
        for administrator, password in zip(
            administrators,
            ["1234", "2580"],
            strict=True,
        ):
            self.assertTrue(administrator.is_superuser)
            self.assertTrue(administrator.is_staff)
            self.assertEqual(administrator.role, "admin")
            self.assertTrue(administrator.check_password(password))
        self.assertTrue("_auth_user_id" in self.client.session)
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertEqual(
            self.client.cookies[settings.SESSION_COOKIE_NAME]["max-age"],
            settings.SESSION_COOKIE_AGE,
        )
        self.client.get(reverse("users:dashboard"))
        self.assertEqual(self.client.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)
        for username, password in (("Brian", "1234"), ("Chiwas", "2580")):
            with self.subTest(username=username):
                response = self.client.post(
                    reverse("login"),
                    {"username": username, "password": password},
                )
                self.assertRedirects(response, reverse("users:dashboard"))
                self.assertEqual(
                    int(self.client.session["_auth_user_id"]),
                    CustomUser.objects.get(username=username).pk,
                )
                self.client.post(reverse("logout"))
        self.assertRedirects(
            self.client.get(reverse("users:first_admin_setup")),
            reverse("login"),
        )

    def test_first_admin_password_requires_at_least_four_digits(self):
        self.client.logout()
        CustomUser.objects.all().delete()
        response = self.client.post(
            reverse("users:first_admin_setup"),
            {
                "brian_password": "123",
                "brian_password_confirm": "123",
                "chiwas_password": "2580",
                "chiwas_password_confirm": "2580",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(username="Brian").exists())
        self.assertFalse(CustomUser.objects.filter(username="Chiwas").exists())
        self.assertContains(response, "at least 4 digits")

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
