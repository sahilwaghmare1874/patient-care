from rest_framework import serializers
from .models import Medicine, PharmacyTransaction
from patients.models import Patient
from accounts.models import PharmacyProfile, DoctorProfile
from doctors.models import Prescription

class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'


class PharmacyTransactionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)
    pharmacy_name = serializers.CharField(source='pharmacy.pharmacy_name', read_only=True)

    patient_id = serializers.CharField(write_only=True, required=False)
    pharmacy_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = PharmacyTransaction
        fields = '__all__'
        read_only_fields = ('invoice_number', 'dispensed_at')
