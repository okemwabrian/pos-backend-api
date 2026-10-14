from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0003_invoice_payment_details"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="client_reference",
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
    ]
