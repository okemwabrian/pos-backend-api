from django.db import migrations


STARTER_CATEGORIES = (
    (
        "Soft Drinks",
        "KE-SOFT",
        (
            ("Cola soft drink 500ml", "500ml", "45.00", "70.00", "65.00"),
            ("Orange soft drink 500ml", "500ml", "45.00", "70.00", "65.00"),
            ("Lemon-lime soft drink 500ml", "500ml", "45.00", "70.00", "65.00"),
            ("Bottled water 500ml", "500ml", "20.00", "35.00", "30.00"),
            ("Bottled water 1L", "1L", "35.00", "60.00", "55.00"),
        ),
    ),
    (
        "Beers",
        "KE-BEER",
        (
            ("Tusker Lager 500ml", "500ml", "165.00", "250.00", "230.00"),
            ("Tusker Lite 500ml", "500ml", "175.00", "260.00", "240.00"),
            ("White Cap Lager 500ml", "500ml", "160.00", "240.00", "220.00"),
            ("Pilsner Lager 500ml", "500ml", "155.00", "230.00", "210.00"),
            ("Local lager 500ml", "500ml", "145.00", "220.00", "200.00"),
        ),
    ),
    (
        "Spirits",
        "KE-SPIRIT",
        (
            ("Kenya Cane 250ml", "250ml", "180.00", "280.00", "250.00"),
            ("Kenya Cane 750ml", "750ml", "520.00", "750.00", "700.00"),
            ("Chrome Vodka 250ml", "250ml", "200.00", "300.00", "270.00"),
            ("Gilbeys Gin 250ml", "250ml", "250.00", "380.00", "350.00"),
            ("Brandy 250ml", "250ml", "260.00", "400.00", "370.00"),
        ),
    ),
    (
        "Wines",
        "KE-WINE",
        (
            ("Red wine 750ml", "750ml", "450.00", "700.00", "650.00"),
            ("White wine 750ml", "750ml", "450.00", "700.00", "650.00"),
            ("Sweet red wine 750ml", "750ml", "420.00", "650.00", "600.00"),
            ("Dry white wine 750ml", "750ml", "500.00", "780.00", "730.00"),
            ("Fortified wine 750ml", "750ml", "350.00", "550.00", "500.00"),
        ),
    ),
    (
        "Ciders",
        "KE-CIDER",
        (
            ("Apple cider 330ml", "330ml", "150.00", "230.00", "210.00"),
            ("Savanna Dry 330ml", "330ml", "175.00", "270.00", "250.00"),
            ("Flavoured cider 330ml", "330ml", "150.00", "230.00", "210.00"),
            ("Pear cider 330ml", "330ml", "160.00", "245.00", "225.00"),
            ("Cider 500ml", "500ml", "190.00", "290.00", "270.00"),
        ),
    ),
    (
        "Mixers",
        "KE-MIX",
        (
            ("Soda water 300ml", "330ml", "35.00", "60.00", "55.00"),
            ("Tonic water 300ml", "330ml", "45.00", "75.00", "70.00"),
            ("Ginger ale 300ml", "330ml", "45.00", "75.00", "70.00"),
            ("Energy drink 250ml", "250ml", "80.00", "130.00", "120.00"),
            ("Juice 1L", "1L", "150.00", "230.00", "210.00"),
        ),
    ),
    (
        "Staple Groceries",
        "KE-GROC",
        (
            ("Maize flour 2kg", "", "130.00", "180.00", "170.00"),
            ("Wheat flour 2kg", "", "140.00", "190.00", "180.00"),
            ("White rice 1kg", "", "140.00", "190.00", "180.00"),
            ("Sugar 1kg", "", "150.00", "200.00", "190.00"),
            ("Cooking oil 1L", "1L", "250.00", "330.00", "310.00"),
        ),
    ),
    (
        "Fresh Produce",
        "KE-PROD",
        (
            ("Potatoes 1kg", "", "60.00", "100.00", "90.00"),
            ("Tomatoes 1kg", "", "80.00", "130.00", "120.00"),
            ("Onions 1kg", "", "90.00", "140.00", "130.00"),
            ("Sukuma wiki bunch", "", "20.00", "40.00", "35.00"),
            ("Bananas 1kg", "", "80.00", "130.00", "120.00"),
        ),
    ),
    (
        "Dairy & Eggs",
        "KE-DAIRY",
        (
            ("Fresh milk 500ml", "500ml", "55.00", "75.00", "70.00"),
            ("Fresh milk 1L", "1L", "105.00", "140.00", "130.00"),
            ("Mala 500ml", "500ml", "65.00", "90.00", "85.00"),
            ("Yoghurt 250ml", "250ml", "55.00", "80.00", "75.00"),
            ("Eggs tray of 30", "", "400.00", "500.00", "470.00"),
        ),
    ),
    (
        "Household & Personal Care",
        "KE-HOUSE",
        (
            ("Laundry detergent 1kg", "", "180.00", "250.00", "230.00"),
            ("Bar soap 800g", "", "100.00", "150.00", "140.00"),
            ("Dishwashing liquid 500ml", "500ml", "100.00", "150.00", "140.00"),
            ("Toilet tissue 10-pack", "", "250.00", "350.00", "330.00"),
            ("Toothpaste 100ml", "", "100.00", "160.00", "150.00"),
        ),
    ),
)


def seed_kenyan_catalog(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    Product = apps.get_model("inventory", "Product")
    database = schema_editor.connection.alias

    for category_name, sku_prefix, products in STARTER_CATEGORIES:
        category, _ = Category.objects.using(database).get_or_create(
            name=category_name
        )
        for index, (name, bottle_size, cost, retail, wholesale) in enumerate(
            products, start=1
        ):
            sku = f"{sku_prefix}-{index:02d}"
            if Product.objects.using(database).filter(sku=sku).exists():
                continue
            if Product.objects.using(database).filter(
                name=name, category_id=category.pk
            ).exists():
                continue
            Product.objects.using(database).create(
                name=name,
                sku=sku,
                category_id=category.pk,
                bottle_size=bottle_size,
                cost_price=cost,
                retail_price=retail,
                wholesale_price=wholesale,
                stock_quantity=0,
                low_stock_threshold=10,
                units_per_case=1,
            )


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0008_alter_product_bottle_size"),
    ]

    operations = [
        migrations.RunPython(seed_kenyan_catalog, migrations.RunPython.noop),
    ]
