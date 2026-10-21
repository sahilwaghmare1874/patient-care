from django.contrib import admin
from .models import Payment, PaymentOrder, WebhookDelivery, PaymentRefund


@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'patient', 'provider_category', 'amount', 'contribution_rate',
                    'expected_contribution_amount', 'gateway_name', 'status', 'created_at')
    list_filter = ('status', 'provider_category', 'gateway_name')
    search_fields = ('order_id', 'patient__patient_id', 'patient__full_name', 'provider_id', 'utr')
    readonly_fields = ('order_id', 'amount_paise', 'expected_contribution_paise', 'idempotency_key',
                       'created_at', 'updated_at', 'completed_at')
    ordering = ('-created_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'patient', 'payment_type', 'amount',
                    'contribution_rate', 'contribution_amount', 'utr', 'status', 'created_at')
    list_filter = ('status', 'payment_type')
    search_fields = ('transaction_id', 'patient__patient_id', 'patient__full_name', 'utr', 'reference_number')
    readonly_fields = ('transaction_id', 'amount_paise', 'idempotency_key', 'created_at')
    ordering = ('-created_at',)


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ('delivery_id', 'event_type', 'status', 'ip_address', 'created_at')
    list_filter = ('status', 'event_type')
    search_fields = ('delivery_id', 'error_message')
    readonly_fields = ('delivery_id', 'created_at', 'raw_body', 'payload', 'signature')
    ordering = ('-created_at',)


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = ('refund_reference', 'payment_order', 'refund_amount', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('refund_reference', 'payment_order__order_id')
    readonly_fields = ('refund_reference', 'created_at')
    ordering = ('-created_at',)
