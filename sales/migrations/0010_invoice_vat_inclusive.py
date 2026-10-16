from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0009_invoice_subtotal_amount_invoice_vat_amount_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="vat_inclusive",
            field=models.BooleanField(default=False),
        ),
    ]
