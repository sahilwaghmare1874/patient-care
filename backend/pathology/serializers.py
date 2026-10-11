from rest_framework import serializers
from .models import PathologyTest, PathologyReport
from patients.models import Patient
from accounts.models import PathologyProfile, DoctorProfile

class PathologyTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathologyTest
        fields = '__all__'


class PathologyReportSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)
    lab_name = serializers.CharField(source='lab.lab_name', read_only=True)
    referring_doctor_name = serializers.CharField(source='referring_doctor.full_name', read_only=True)

    # Input fields
    patient_id = serializers.CharField(write_only=True, required=False)
    lab_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = PathologyReport
        fields = '__all__'
        read_only_fields = ('report_id', 'created_at')
