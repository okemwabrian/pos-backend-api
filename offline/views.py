from collections import Counter
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import F
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.store import TILL_NUMBER, VAT_RATE, calculate_included_vat
from core.permissions import can_use_pos, is_admin_or_manager
from crm.models import Customer
from inventory.models import Product, StockAdjustment
from inventory.serializers import ProductSerializer
from sales.models import Invoice, InvoiceItem


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def token_login(request):
    if not isinstance(request.data, dict):
        return Response(
            {"detail": "The sign-in payload must be an object."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    user = authenticate(
        request,
        username=request.data.get("username"),
        password=request.data.get("password"),
    )
    if user is None or not can_use_pos(user):
        return Response(
            {"detail": "Invalid credentials or account does not have POS access."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {
            "token": token.key,
            "user_id": user.pk,
            "username": user.username,
            "display_name": user.get_full_name() or user.username,
            "role": user.role,
            "can_adjust_stock": is_admin_or_manager(user),
        }
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def token_logout(request):
    Token.objects.filter(user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def catalog(request):
    if not can_use_pos(request.user):
        return Response(
            {"detail": "POS access is required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    products = Product.objects.select_related("category").order_by("name")
    return Response(
        {
            "products": ProductSerializer(products, many=True).data,
            "customers": list(
                Customer.objects.order_by("name").values("id", "name", "phone")
            ),
        }
    )


def _reference(value):
    try:
        return UUID(str(value))
    except (TypeError, ValueError, AttributeError) as error:
        raise ValueError("Each sync operation must have a valid UUID.") from error


def _positive_integer(value, field_name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive whole number.")
    return value


def _sale_result(invoice, operation_id, already_synced=False):
    return {
        "id": str(operation_id),
        "status": "synced",
        "already_synced": already_synced,
        "invoice_id": invoice.pk,
        "total_amount": str(invoice.total_amount),
    }


def _sync_sale(user, operation_id, data):
    reference = _reference(operation_id)
    try:
        with transaction.atomic():
            existing = Invoice.objects.filter(client_reference=reference).first()
            if existing:
                if existing.cashier_id != user.pk:
                    raise ValueError("This operation reference belongs to another user.")
                return _sale_result(existing, reference, already_synced=True)

            items = data.get("items")
            if not isinstance(items, list) or not items:
                raise ValueError("A sale must contain at least one item.")

            quantities = Counter()
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError("Each sale item must be an object.")
                product_id = _positive_integer(item.get("product_id"), "Product ID")
                quantity = _positive_integer(item.get("quantity"), "Quantity")
                quantities[product_id] += quantity

            price_type = data.get("price_type", "retail")
            if price_type not in {"retail", "wholesale"}:
                raise ValueError("Choose a valid price type.")
            payment_method = data.get("payment_method", "")
            if payment_method not in dict(Invoice.PAYMENT_CHOICES):
                raise ValueError("Choose a valid payment method.")

            products = Product.objects.select_for_update().filter(
                pk__in=quantities.keys()
            )
            products_by_id = {product.pk: product for product in products}
            if len(products_by_id) != len(quantities):
                raise ValueError("One or more selected products no longer exist.")

            subtotal = Decimal("0.00")
            sale_lines = []
            for product_id, quantity in quantities.items():
                product = products_by_id[product_id]
                if not product.is_service and product.stock_quantity < quantity:
                    raise ValueError(
                        f"Not enough stock for {product.name}. "
                        f"Only {product.stock_quantity} remaining."
                    )
                price = (
                    product.wholesale_price
                    if price_type == "wholesale"
                    else product.retail_price
                )
                subtotal += price * quantity
                sale_lines.append((product, quantity, price))

            discount = Decimal(str(data.get("discount", "0") or "0"))
            if discount < 0 or discount > subtotal:
                raise ValueError("Discount must be between zero and the subtotal.")

            customer_id = data.get("customer_id")
            customer_name = data.get("customer_name", "")
            if not isinstance(customer_name, str):
                raise ValueError("Customer name must be text.")
            customer_name = customer_name.strip()
            customer = None
            if customer_id:
                customer = Customer.objects.filter(pk=customer_id).first()
                if customer is None:
                    raise ValueError("The selected customer no longer exists.")
            if not customer_name and customer is None:
                raise ValueError("Enter the customer name for the receipt.")

            payment_fields = {
                field: data.get(field, "") or ""
                for field in (
                    "till_number",
                    "transaction_code",
                    "payer_name",
                    "paybill_number",
                    "account_number",
                    "phone_number",
                )
            }
            if any(not isinstance(value, str) for value in payment_fields.values()):
                raise ValueError("Payment details must be text.")
            payment_fields = {
                field: value.strip() for field, value in payment_fields.items()
            }
            if payment_method == "till_number":
                payment_fields["till_number"] = TILL_NUMBER
            amount_tendered = data.get("amount_tendered")
            if payment_method == "cash":
                if amount_tendered in (None, ""):
                    raise ValueError("Enter the cash amount received.")
                amount_tendered = Decimal(str(amount_tendered))
            else:
                amount_tendered = None
            comment = data.get("comment", "")
            if not isinstance(comment, str):
                raise ValueError("Sale note must be text.")
            total_amount = subtotal - discount
            vat_amount = calculate_included_vat(total_amount)
            invoice = Invoice(
                client_reference=reference,
                cashier=user,
                customer=customer,
                customer_name=customer_name or (customer.name if customer else ""),
                payment_method=payment_method,
                subtotal_amount=subtotal,
                vat_rate=VAT_RATE,
                vat_amount=vat_amount,
                total_amount=total_amount,
                discount_amount=discount,
                vat_inclusive=True,
                amount_tendered=amount_tendered,
                comment=comment.strip(),
                **payment_fields,
            )
            try:
                invoice.clean()
            except ValidationError as error:
                raise ValueError("; ".join(error.messages)) from error
            invoice.save()

            InvoiceItem.objects.bulk_create(
                [
                    InvoiceItem(
                        invoice=invoice,
                        product=product,
                        quantity=quantity,
                        price_at_sale=price,
                        cost_at_sale=product.cost_price,
                    )
                    for product, quantity, price in sale_lines
                ]
            )
            for product, quantity, _ in sale_lines:
                if not product.is_service:
                    product.stock_quantity -= quantity
                    product.save(update_fields=["stock_quantity", "updated_at"])

            return _sale_result(invoice, reference)
    except IntegrityError:
        existing = Invoice.objects.filter(client_reference=reference).first()
        if existing and existing.cashier_id == user.pk:
            return _sale_result(existing, reference, already_synced=True)
        raise


def _sync_restock(user, operation_id, data):
    if not is_admin_or_manager(user):
        raise ValueError("Only managers can sync stock adjustments.")

    reference = _reference(operation_id)
    try:
        with transaction.atomic():
            existing = StockAdjustment.objects.filter(
                client_reference=reference
            ).first()
            if existing:
                if existing.created_by_id != user.pk:
                    raise ValueError("This operation reference belongs to another user.")
                return {
                    "id": str(reference),
                    "status": "synced",
                    "already_synced": True,
                    "product_id": existing.product_id,
                }

            product_id = _positive_integer(data.get("product_id"), "Product ID")
            quantity = _positive_integer(data.get("quantity"), "Quantity")
            product = Product.objects.select_for_update().filter(pk=product_id).first()
            if product is None:
                raise ValueError("The selected product no longer exists.")
            if product.is_service:
                raise ValueError("Services cannot be restocked.")

            adjustment = StockAdjustment.objects.create(
                client_reference=reference,
                product=product,
                quantity=quantity,
                created_by=user,
            )
            Product.objects.filter(pk=product.pk).update(
                stock_quantity=F("stock_quantity") + quantity
            )
            return {
                "id": str(reference),
                "status": "synced",
                "already_synced": False,
                "product_id": adjustment.product_id,
                "stock_quantity": product.stock_quantity + quantity,
            }
    except IntegrityError:
        existing = StockAdjustment.objects.filter(
            client_reference=reference
        ).first()
        if existing and existing.created_by_id == user.pk:
            return {
                "id": str(reference),
                "status": "synced",
                "already_synced": True,
                "product_id": existing.product_id,
            }
        raise


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def sync_operations(request):
    if not can_use_pos(request.user):
        return Response(
            {"detail": "POS access is required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    if not isinstance(request.data, dict):
        return Response(
            {"detail": "The sync payload must be an object."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    operations = request.data.get("operations")
    if not isinstance(operations, list):
        return Response(
            {"detail": "operations must be a list."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(operations) > 100:
        return Response(
            {"detail": "A sync batch cannot exceed 100 operations."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results = []
    for operation in operations:
        operation_id = operation.get("id") if isinstance(operation, dict) else None
        try:
            if not isinstance(operation, dict):
                raise ValueError("Each operation must be an object.")
            operation_type = operation.get("type")
            data = operation.get("data")
            if not isinstance(data, dict):
                raise ValueError("Each operation must include an object data payload.")
            if operation_type == "sale":
                result = _sync_sale(request.user, operation_id, data)
            elif operation_type == "restock":
                result = _sync_restock(request.user, operation_id, data)
            else:
                raise ValueError("Unsupported sync operation.")
        except (
            InvalidOperation,
            KeyError,
            TypeError,
            ValueError,
            ValidationError,
        ) as error:
            detail = "; ".join(error.messages) if isinstance(error, ValidationError) else str(error)
            result = {
                "id": str(operation_id) if operation_id is not None else None,
                "status": "rejected",
                "error": detail or "Invalid operation payload.",
            }
        results.append(result)

    return Response({"results": results})
