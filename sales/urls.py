from django.urls import path

from .views import generate_receipt_pdf, pos_terminal_view

app_name = 'sales'

urlpatterns = [
    path('pos/', pos_terminal_view, name='pos_terminal'),
    path('invoices/<int:invoice_id>/receipt/', generate_receipt_pdf, name='receipt'),
]
