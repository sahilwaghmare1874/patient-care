from rest_framework import serializers
from .models import Appointment, Consultation, Prescription
from patients.models import Patient
from accounts.models import DoctorProfile

class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'


class ConsultationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.full_name', read_only=True)
    hospital_name = serializers.CharField(source='doctor.hospital_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)

    # Allow passing patient_id as string (e.g. 'PAT-2026-XXXXXX') in input
    patient_id = serializers.CharField(write_only=True, required=False)
    doctor_id = serializers.CharField(write_only=True, required=False)
    prescribed_medicines = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Consultation
        fields = '__all__'
        read_only_fields = ('consultation_id', 'created_at')
