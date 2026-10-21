from django.urls import path
from .views import (
    PaymentListCreateView,
    PaymentReceiptDetailView,
    CreatePaymentOrderView,
    PaymentWebhookView,
    PaymentOrderStatusView,
    PaymentRefundView,
    PaymentOrderListView,
    SandboxSimulatePaymentView,
    WebhookDeliveryListView,
)

urlpatterns = [
    # ── Legacy endpoint (backward-compatible)
    path('', PaymentListCreateView.as_view(), name='payment-list-create'),
    path('receipt/<str:transaction_id>/', PaymentReceiptDetailView.as_view(), name='payment-receipt-detail'),

    # ── YouPI-PG Payment Gateway Integration
    path('orders/', PaymentOrderListView.as_view(), name='payment-order-list'),
    path('orders/create/', CreatePaymentOrderView.as_view(), name='payment-order-create'),
    path('orders/<str:order_id>/status/', PaymentOrderStatusView.as_view(), name='payment-order-status'),
    path('orders/<str:order_id>/refund/', PaymentRefundView.as_view(), name='payment-order-refund'),
    path('webhook/', PaymentWebhookView.as_view(), name='payment-webhook'),

    # ── Sandbox simulation (disabled in live mode)
    path('sandbox/simulate/', SandboxSimulatePaymentView.as_view(), name='payment-sandbox-simulate'),
    path('webhook-deliveries/', WebhookDeliveryListView.as_view(), name='webhook-delivery-list'),
]
