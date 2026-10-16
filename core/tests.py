from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.permissions import can_use_pos, is_admin, is_admin_or_manager
from finance.models import Expense
from inventory.models import Category, Product
from sales.models import Invoice, InvoiceItem
from users.models import CustomUser


class ZReportTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="report-admin",
            password="test-password",
            role="admin",
        )
        self.product = Product.objects.create(
            name="Report Bottle",
            sku="REPORT-001",
            category=Category.objects.create(name="Report Category"),
            cost_price=Decimal("40.00"),
            retail_price=Decimal("60.00"),
            wholesale_price=Decimal("50.00"),
            stock_quantity=5,
        )
        self.invoice = Invoice.objects.create(
            cashier=self.user,
            customer_name="Report Customer",
            payment_method="till_number",
            till_number="5453103",
            subtotal_amount=Decimal("120.00"),
            vat_rate=Decimal("16.00"),
            vat_amount=Decimal("19.20"),
            total_amount=Decimal("139.20"),
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=2,
            price_at_sale=Decimal("60.00"),
            cost_at_sale=Decimal("40.00"),
        )
        Expense.objects.create(
            user=self.user,
            description="Daily supplies",
            amount=Decimal("10.00"),
        )
        self.client.force_login(self.user)

    def test_date_range_z_report_includes_revenue_cost_expenses_and_payment_totals(self):
        today = timezone.localdate().isoformat()
        response = self.client.get(
            reverse("reports"),
            {"start_date": today, "end_date": today},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["z_revenue"], Decimal("120.00"))
        self.assertEqual(response.context["z_vat_collected"], Decimal("19.20"))
        self.assertEqual(response.context["z_cost_of_goods"], Decimal("80.00"))
        self.assertEqual(response.context["z_expenses"], Decimal("10.00"))
        self.assertEqual(response.context["z_profit"], Decimal("30.00"))
        self.assertTrue(response.context["z_cost_data_complete"])
        till_total = next(
            row["total"]
            for row in response.context["z_payment_breakdown"]
            if row["key"] == "till_number"
        )
        self.assertEqual(till_total, Decimal("139.20"))

    def test_z_report_marks_legacy_costs_as_incomplete(self):
        InvoiceItem.objects.filter(invoice=self.invoice).update(cost_at_sale=None)
        response = self.client.get(reverse("reports"))

        self.assertFalse(response.context["z_cost_data_complete"])

    def test_z_report_nets_vat_inclusive_sales_without_changing_legacy_sales(self):
        Invoice.objects.create(
            cashier=self.user,
            customer_name="VAT Inclusive Customer",
            payment_method="cash",
            amount_tendered=Decimal("4500.00"),
            subtotal_amount=Decimal("4500.00"),
            vat_rate=Decimal("16.00"),
            vat_amount=Decimal("620.69"),
            total_amount=Decimal("4500.00"),
            vat_inclusive=True,
        )

        response = self.client.get(reverse("reports"))

        self.assertEqual(response.context["z_revenue"], Decimal("3999.31"))
        self.assertEqual(response.context["z_vat_collected"], Decimal("639.89"))

    def test_superuser_has_full_store_management_access(self):
        superuser = CustomUser.objects.create_superuser(
            username="full-access",
            password="test-password",
        )
        self.client.force_login(superuser)

        self.assertTrue(can_use_pos(superuser))
        self.assertTrue(is_admin_or_manager(superuser))
        self.assertTrue(is_admin(superuser))
        for url_name in (
            "users:manage",
            "inventory:products",
            "sales:pos_terminal",
            "reports",
        ):
            with self.subTest(url_name=url_name):
                self.assertEqual(
                    self.client.get(reverse(url_name)).status_code,
                    200,
                )
