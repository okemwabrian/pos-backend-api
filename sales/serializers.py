from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError
from core.store import TILL_NUMBER, VAT_RATE, calculate_vat
from .models import Invoice, InvoiceItem

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'price_at_sale', 'cost_at_sale']
        read_only_fields = ['cost_at_sale']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = [
            'id',
            'cashier',
            'customer',
            'customer_name',
            'payment_method',
            'till_number',
            'transaction_code',
            'payer_name',
            'paybill_number',
            'account_number',
            'phone_number',
            'amount_tendered',
            'change_amount',
            'subtotal_amount',
            'vat_rate',
            'vat_amount',
            'total_amount',
            'created_at',
            'items',
        ]
        read_only_fields = [
            'change_amount',
            'subtotal_amount',
            'vat_rate',
            'vat_amount',
            'total_amount',
        ]

    def validate(self, attrs):
        items = attrs.get("items", [])
        subtotal = sum(
            (
                item["price_at_sale"] * item["quantity"]
                for item in items
            ),
            start=0,
        )
        discount = attrs.get("discount_amount", 0)
        if discount < 0 or discount > subtotal:
            raise serializers.ValidationError(
                {"discount_amount": "Discount must be between zero and the subtotal."}
            )
        taxable_amount = subtotal - discount
        vat_amount = calculate_vat(taxable_amount)
        invoice_data = {key: value for key, value in attrs.items() if key != 'items'}
        invoice_data.update(
            subtotal_amount=subtotal,
            vat_rate=VAT_RATE,
            vat_amount=vat_amount,
            total_amount=taxable_amount + vat_amount,
        )
        if invoice_data.get("payment_method") == "till_number":
            invoice_data["till_number"] = TILL_NUMBER
        invoice = Invoice(**invoice_data)
        try:
            invoice.clean()
        except ValidationError as error:
            raise serializers.ValidationError(error.message_dict) from error
        attrs['change_amount'] = invoice.change_amount
        attrs.update(
            subtotal_amount=subtotal,
            vat_rate=VAT_RATE,
            vat_amount=vat_amount,
            total_amount=taxable_amount + vat_amount,
            till_number=invoice.till_number,
        )
        return attrs

    # The atomic decorator ensures everything succeeds, or nothing saves at all
    @transaction.atomic 
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # 1. Create the main Invoice
        invoice = Invoice(**validated_data)
        invoice.full_clean()
        invoice.save()
        
        # 2. Loop through items to save them AND update stock
        for item_data in items_data:
            product = item_data['product']
            quantity_sold = item_data['quantity']
            
            # Smart check: Prevent selling more than you have
            if product.stock_quantity < quantity_sold:
                raise serializers.ValidationError(
                    f"Not enough stock for {product.name}. Only {product.stock_quantity} remaining."
                )
            
            # Save the invoice item
            InvoiceItem.objects.create(
                invoice=invoice,
                cost_at_sale=product.cost_price,
                **item_data,
            )
            
            # Deduct the stock and save the product
            product.stock_quantity -= quantity_sold
            product.save()
            
        return invoice