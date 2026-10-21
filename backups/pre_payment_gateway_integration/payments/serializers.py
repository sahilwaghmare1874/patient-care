from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)

    patient_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('transaction_id', 'created_at')
