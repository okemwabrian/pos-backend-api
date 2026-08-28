from django.urls import path

from .views import (
    generate_receipt_pdf,
    pos_terminal_view,
    quotation_csv_view,
    quotation_detail_view,
    bills_and_quotes_view,
)

app_name = 'sales'

urlpatterns = [
    path('pos/', pos_terminal_view, name='pos_terminal'),
    path('bills-quotes/', bills_and_quotes_view, name='bills_quotes'),
    path('invoices/<int:invoice_id>/receipt/', generate_receipt_pdf, name='receipt'),
    path('quotations/<int:quotation_id>/', quotation_detail_view, name='quotation_detail'),
    path('quotations/<int:quotation_id>/export/', quotation_csv_view, name='quotation_csv'),
]
