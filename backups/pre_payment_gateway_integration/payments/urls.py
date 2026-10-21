from django.urls import path
from .views import (
    PaymentListCreateView,
    PaymentReceiptDetailView
)

urlpatterns = [
    path('', PaymentListCreateView.as_view(), name='payment-list-create'),
    path('receipt/<str:transaction_id>/', PaymentReceiptDetailView.as_view(), name='payment-receipt-detail'),
]
