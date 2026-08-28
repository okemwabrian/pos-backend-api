import random
from decimal import Decimal
from urllib.parse import quote

from django.core.management.base import BaseCommand
from django.db import transaction

from inventory.models import Category, Product


ADJECTIVES = (
    "Classic", "Premium", "Fresh", "Deluxe", "Compact", "Smart", "Everyday",
    "Professional", "Eco", "Select",
)
PRODUCT_TYPES = (
    "Pack", "Blend", "Kit", "Edition", "Supply", "Choice", "Essential",
    "Value Set", "Standard", "Plus",
)

# These broad Flickr search terms give each category a relevant photo instead of
# a text-only placeholder.  The fallback keeps new categories supported too.
IMAGE_KEYWORDS = {
    "Bedroom Furniture": "bedroom,furniture",
    "Burgers & Fast Food": "burger,fast-food",
    "Cold Drinks & Shakes": "cold-drink,milkshake",
    "Computer Accessories": "computer,accessories",
    "Delivery Fees": "delivery,package",
    "Desserts & Pastries": "dessert,pastry",
    "Footwear": "shoes,footwear",
    "Furniture Assembly": "furniture,assembly",
    "Home Decor": "home,decor",
    "Hot Beverages": "coffee,tea",
    "Kitchen Appliances": "kitchen,appliance",
    "Laptops & Computers": "laptop,computer",
    "Living Room Furniture": "living-room,furniture",
    "Men's Apparel": "mens,fashion",
    "Miscellaneous": "shopping,product",
    "Office Desks & Stands": "office,desk",
    "Seafood & Sushi": "seafood,sushi",
    "Storage & Racks": "storage,shelves",
    "Technical Repair": "electronics,repair",
    "Women's Apparel": "womens,fashion",
}


def money(minimum, maximum):
    """Return a two-decimal price without binary floating-point arithmetic."""
    return Decimal(random.randint(minimum * 100, maximum * 100)) / Decimal("100")


def product_image_url(category, sequence):
    """Create a stable, category-relevant public image URL for a product."""
    keywords = IMAGE_KEYWORDS.get(category.name, category.name.replace(" ", ","))
    encoded_keywords = quote(keywords, safe=",")
    lock = category.pk * 1000 + sequence
    return f"https://loremflickr.com/600/400/{encoded_keywords}?lock={lock}"


def category_image_url(category):
    """Create a stable, category-relevant public image URL for POS category cards."""
    keywords = IMAGE_KEYWORDS.get(category.name, category.name.replace(" ", ","))
    encoded_keywords = quote(keywords, safe=",")
    return f"https://loremflickr.com/900/600/{encoded_keywords}?lock={category.pk}"


class Command(BaseCommand):
    help = "Fill every category up to 20 realistic mock products (or a chosen amount)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-category",
            type=int,
            default=20,
            help="Target number of products in each category (default: 20).",
        )
        parser.add_argument(
            "--refresh-images",
            action="store_true",
            help="Replace product and category image URLs with category-matched photo URLs.",
        )

    def handle(self, *args, **options):
        target_count = options["per_category"]
        refresh_images = options["refresh_images"]
        if target_count < 1:
            self.stderr.write("--per-category must be at least 1.")
            return

        categories = Category.objects.order_by("name")
        if not categories.exists():
            self.stdout.write(self.style.WARNING("No categories found. Create categories first."))
            return

        total_created = 0
        for category in categories:
            with transaction.atomic():
                if refresh_images:
                    category.image_url = category_image_url(category)
                    category.save(update_fields=["image_url"])

                existing_count = Product.objects.filter(category=category).count()
                if refresh_images and existing_count:
                    existing_products = list(
                        Product.objects.filter(category=category).order_by("pk")
                    )
                    for sequence, product in enumerate(existing_products, start=1):
                        product.image_url = product_image_url(category, sequence)
                    Product.objects.bulk_update(existing_products, ["image_url"])

                missing_count = max(0, target_count - existing_count)

                if not missing_count:
                    self.stdout.write(
                        f"{category.name}: already has {existing_count} products; skipped."
                    )
                    continue

                products = []
                for sequence in range(existing_count + 1, target_count + 1):
                    name = (
                        f"{random.choice(ADJECTIVES)} {category.name} "
                        f"{random.choice(PRODUCT_TYPES)} {sequence}"
                    )
                    sku = f"CAT{category.pk:04d}-{sequence:04d}"
                    cost_price = money(50, 5000)
                    retail_price = (
                        cost_price * Decimal(random.randint(130, 180)) / 100
                    ).quantize(Decimal("0.01"))
                    wholesale_price = (
                        retail_price * Decimal(random.randint(75, 95)) / 100
                    ).quantize(Decimal("0.01"))
                    products.append(
                        Product(
                            name=name,
                            sku=sku,
                            category=category,
                            cost_price=cost_price,
                            retail_price=retail_price,
                            wholesale_price=wholesale_price,
                            stock_quantity=random.randint(10, 500),
                            image_url=product_image_url(category, sequence),
                        )
                    )

                Product.objects.bulk_create(products)
                total_created += len(products)
                self.stdout.write(
                    self.style.SUCCESS(f"{category.name}: created {len(products)} products.")
                )

        self.stdout.write(self.style.SUCCESS(f"Seeding complete: {total_created} products created."))
