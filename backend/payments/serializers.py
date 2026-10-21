from rest_framework import serializers
from .models import Payment, PaymentOrder, WebhookDelivery, PaymentRefund


class PaymentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)
    patient_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('transaction_id', 'created_at', 'amount_paise',
                            'contribution_amount', 'contribution_rate', 'utr')


class PaymentOrderSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)
    amount_inr = serializers.SerializerMethodField()
    contribution_inr = serializers.SerializerMethodField()

    class Meta:
        model = PaymentOrder
        fields = '__all__'
        read_only_fields = (
            'order_id', 'created_at', 'updated_at', 'completed_at',
            'gateway_payment_id', 'checkout_url', 'utr',
            'amount_paise', 'expected_contribution_paise', 'expected_contribution_amount',
        )

    def get_amount_inr(self, obj):
        return float(obj.amount)

    def get_contribution_inr(self, obj):
        return float(obj.expected_contribution_amount)


class WebhookDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = ('delivery_id', 'event_type', 'status', 'created_at', 'error_message')
        read_only_fields = '__all__'


class PaymentRefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentRefund
        fields = '__all__'
        read_only_fields = ('refund_reference', 'created_at')
