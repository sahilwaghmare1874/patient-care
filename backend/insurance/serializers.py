from rest_framework import serializers
from .models import InsuranceCompany, InsurancePolicy, InsuranceClaim
from patients.models import Patient

class InsuranceCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceCompany
        fields = '__all__'


class InsurancePolicySerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)

    class Meta:
        model = InsurancePolicy
        fields = '__all__'


class InsuranceClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)
    policy_number = serializers.CharField(source='policy.policy_number', read_only=True)

    patient_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = InsuranceClaim
        fields = '__all__'
        read_only_fields = ('claim_id', 'submission_date')
