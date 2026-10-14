from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0004_invoice_client_reference"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="amount_tendered",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="change_amount",
            field=models.DecimalField(
                decimal_places=2, default=0, max_digits=10
            ),
        ),
    ]
