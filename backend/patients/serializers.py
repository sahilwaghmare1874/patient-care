from rest_framework import serializers
from .models import Patient
import re

class PatientSerializer(serializers.ModelSerializer):
    masked_pan = serializers.CharField(read_only=True)
    masked_aadhaar = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = (
            'id', 'patient_id', 'full_name', 'dob', 'gender', 'mobile',
            'email', 'address', 'city', 'district', 'state', 'pincode',
            'pan_number', 'masked_pan', 'aadhaar_number', 'masked_aadhaar',
            'government_scheme_id', 'blood_group', 'allergies', 'existing_conditions',
            'illness_description', 'presenting_symptoms', 'symptom_duration', 'symptom_severity', 'current_medicines', 'consent_data_processing',
            'emergency_contact_name', 'emergency_contact_phone', 'hac_number',
            'is_active', 'created_at', 'updated_at'
        )
        read_only_fields = ('patient_id', 'hac_number', 'created_at', 'updated_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Always mask PAN in general representation for security
        ret['pan_number'] = instance.masked_pan
        if instance.aadhaar_number:
            ret['aadhaar_number'] = instance.masked_aadhaar
        return ret


class PatientCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = Patient
        fields = (
            'full_name', 'dob', 'gender', 'mobile', 'email',
            'address', 'city', 'district', 'state', 'pincode',
            'pan_number', 'aadhaar_number', 'government_scheme_id',
            'blood_group', 'allergies', 'existing_conditions',
            'illness_description', 'presenting_symptoms', 'symptom_duration', 'symptom_severity', 'current_medicines', 'consent_data_processing',
            'emergency_contact_name', 'emergency_contact_phone',
            'username', 'password'
        )

    def validate_consent_data_processing(self, value):
        if not value:
            raise serializers.ValidationError("Consent for medical data processing is required to register.")
        return value

    def validate_pan_number(self, value):
        val = value.strip().upper()
        pan_regex = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pan_regex, val):
            raise serializers.ValidationError("Invalid Indian PAN format. Format must be 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F).")
        return val

    def validate_mobile(self, value):
        val = re.sub(r'\D', '', value)
        if len(val) > 10:
            val = val[-10:]
        if len(val) != 10:
            raise serializers.ValidationError("Mobile number must be a 10-digit Indian phone number.")
        return val
