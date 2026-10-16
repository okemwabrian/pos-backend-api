from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from inventory.forms import ProductForm, RestockForm
from inventory.models import Category, Product
from users.models import CustomUser


class LiquorCatalogTests(TestCase):
    def test_liquor_categories_are_seeded(self):
        self.assertTrue(
            {
                "Spirits",
                "Beers",
                "Wines",
                "Ciders",
                "Soft Drinks",
                "Mixers",
            }.issubset(set(Category.objects.values_list("name", flat=True)))
        )

    def test_kenyan_starter_catalog_has_ten_categories_and_fifty_zero_stock_items(self):
        expected_categories = {
            "Soft Drinks",
            "Beers",
            "Spirits",
            "Wines",
            "Ciders",
            "Mixers",
            "Staple Groceries",
            "Fresh Produce",
            "Dairy & Eggs",
            "Household & Personal Care",
        }
        categories = Category.objects.filter(name__in=expected_categories)

        self.assertEqual(categories.count(), 10)
        self.assertEqual(
            Product.objects.filter(category__in=categories).count(), 50
        )
        self.assertFalse(
            Product.objects.filter(category__in=categories)
            .exclude(stock_quantity=0)
            .exists()
        )

    def test_product_form_exposes_drink_size_and_case_pricing(self):
        self.assertTrue(
            {"bottle_size", "units_per_case", "case_price"}.issubset(
                ProductForm().fields
            )
        )
        self.assertEqual(Product._meta.get_field("units_per_case").default, 1)
        self.assertIn("autofocus", ProductForm().fields["sku"].widget.attrs)
        self.assertIn("autofocus", RestockForm().fields["sku"].widget.attrs)

    def test_inventory_form_accepts_uploaded_product_image(self):
        image_data = BytesIO()
        Image.new("RGB", (2, 2), color="red").save(image_data, format="PNG")
        image = SimpleUploadedFile(
            "bottle.png", image_data.getvalue(), content_type="image/png"
        )
        user = CustomUser.objects.create_user(
            username="inventory-owner",
            password="Strong-Test-Password123",
            role="cashier",
        )
        category = Category.objects.create(name="Uploaded Image Test")
        self.client.force_login(user)

        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            response = self.client.post(
                reverse("inventory:products"),
                {
                    "name": "Uploaded Bottle",
                    "sku": "UPLOADED-001",
                    "category": category.pk,
                    "bottle_size": "",
                    "cost_price": "50.00",
                    "retail_price": "100.00",
                    "wholesale_price": "80.00",
                    "units_per_case": "1",
                    "case_price": "",
                    "is_service": "",
                    "stock_quantity": "5",
                    "low_stock_threshold": "5",
                    "image": image,
                },
            )
            self.assertEqual(response.status_code, 302)
            product = Product.objects.get(sku="UPLOADED-001")
            self.assertTrue(product.image.name.endswith("bottle.png"))
            self.assertTrue(product.image.storage.exists(product.image.name))
            self.assertIn("/media/products/", product.image.url)
