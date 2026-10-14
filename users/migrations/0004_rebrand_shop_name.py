from django.db import migrations, models


def rename_default_shop(apps, schema_editor):
    ShopSettings = apps.get_model("users", "ShopSettings")
    ShopSettings.objects.filter(shop_name="CorePoint POS").update(
        shop_name="CHIWAS LIQUOR STORE"
    )


def restore_default_shop(apps, schema_editor):
    ShopSettings = apps.get_model("users", "ShopSettings")
    ShopSettings.objects.filter(shop_name="CHIWAS LIQUOR STORE").update(
        shop_name="CorePoint POS"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_remove_shopsettings_currency"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shopsettings",
            name="shop_name",
            field=models.CharField(
                default="CHIWAS LIQUOR STORE", max_length=150
            ),
        ),
        migrations.RunPython(rename_default_shop, restore_default_shop),
    ]
