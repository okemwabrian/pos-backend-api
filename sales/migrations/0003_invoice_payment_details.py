from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0002_invoice_comment_invoice_discount_amount_quotation_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="payment_method",
            field=models.CharField(
                choices=[
                    ("cash", "Cash"),
                    ("till_number", "TILL NUMBER"),
                    ("paybill", "PAYBILL"),
                    ("send_money", "SEND MONEY"),
                    ("mpesa", "M-Pesa"),
                    ("card", "Card"),
                ],
                default="cash",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="invoice",
            name="till_number",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="invoice",
            name="transaction_code",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="invoice",
            name="paybill_number",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="invoice",
            name="account_number",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="invoice",
            name="phone_number",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
