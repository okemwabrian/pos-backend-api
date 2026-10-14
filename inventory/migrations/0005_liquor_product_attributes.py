from django.db import migrations, models


LIQUOR_CATEGORIES = (
    "Spirits",
    "Beers",
    "Wines",
    "Ciders",
    "Soft Drinks",
    "Mixers",
)


def create_liquor_categories(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    for category_name in LIQUOR_CATEGORIES:
        Category.objects.get_or_create(name=category_name)


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0004_product_image_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="bottle_size",
            field=models.CharField(
                blank=True,
                choices=[
                    ("250ml", "250 ml"),
                    ("330ml", "330 ml"),
                    ("500ml", "500 ml"),
                    ("750ml", "750 ml"),
                    ("1L", "1 L"),
                ],
                help_text="Bottle or package size for drinks.",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="units_per_case",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Number of individual units in a crate or carton.",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="case_price",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Optional selling price for one full crate or carton.",
                max_digits=10,
                null=True,
            ),
        ),
        migrations.RunPython(create_liquor_categories, migrations.RunPython.noop),
    ]
