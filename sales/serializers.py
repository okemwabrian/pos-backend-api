from rest_framework import serializers
from django.db import transaction
from .models import Invoice, InvoiceItem

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'quantity', 'price_at_sale']

class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = ['id', 'cashier', 'customer', 'payment_method', 'total_amount', 'created_at', 'items']

    # The atomic decorator ensures everything succeeds, or nothing saves at all
    @transaction.atomic 
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        
        # 1. Create the main Invoice
        invoice = Invoice.objects.create(**validated_data)
        
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
            InvoiceItem.objects.create(invoice=invoice, **item_data)
            
            # Deduct the stock and save the product
            product.stock_quantity -= quantity_sold
            product.save()
            
        return invoice