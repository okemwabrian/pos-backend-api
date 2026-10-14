from django.db import migrations, models


OLD_STORE_NAME = "CHIWAS LIQUOR STORE"
NEW_STORE_NAME = "CHIWAS LIQUOR STORE & RESTAURANT (Opposite Quickmart)"


def rename_store(apps, schema_editor):
    ShopSettings = apps.get_model("users", "ShopSettings")
    ShopSettings.objects.filter(shop_name=OLD_STORE_NAME).update(
        shop_name=NEW_STORE_NAME
    )


def restore_store_name(apps, schema_editor):
    ShopSettings = apps.get_model("users", "ShopSettings")
    ShopSettings.objects.filter(shop_name=NEW_STORE_NAME).update(
        shop_name=OLD_STORE_NAME
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0004_rebrand_shop_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shopsettings",
            name="shop_name",
            field=models.CharField(
                default=NEW_STORE_NAME,
                max_length=150,
            ),
        ),
        migrations.RunPython(rename_store, restore_store_name),
    ]
