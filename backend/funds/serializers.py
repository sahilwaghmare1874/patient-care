from rest_framework import serializers
from decimal import Decimal
from .models import AllocationConfiguration, FundAllocation
from patients.models import Patient
from government.models import GovernmentScheme
from insurance.models import InsuranceClaim

class AllocationConfigurationSerializer(serializers.ModelSerializer):
    total_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = AllocationConfiguration
        fields = '__all__'

    def validate(self, data):
        doc = data.get('doctor_percentage', Decimal('10.00'))
        path = data.get('pathology_percentage', Decimal('10.00'))
        med = data.get('pharmacy_percentage', Decimal('5.00'))
        gov = data.get('government_percentage', Decimal('5.00'))
        benefit = data.get('patient_benefit_percentage', Decimal('70.00'))

        for name, val in [('Doctor', doc), ('Pathology', path), ('Pharmacy', med), ('Government', gov), ('Patient Benefit', benefit)]:
            if val < Decimal('0.00'):
                raise serializers.ValidationError({name: "Percentage cannot be negative."})

        total = doc + path + med + gov + benefit
        if total != Decimal('100.00'):
            raise serializers.ValidationError({
                "non_field_errors": f"Total allocation percentage must equal exactly 100.00%. Current sum is {total}%."
            })
        return data


class FundAllocationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    patient_id_display = serializers.CharField(source='patient.patient_id', read_only=True)
    scheme_name = serializers.CharField(source='scheme.scheme_name', read_only=True, default="Ayushman Bharat (PM-JAY)")

    patient_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = FundAllocation
        fields = '__all__'
        read_only_fields = ('allocation_id', 'created_at')


from .models import (
    PatientHealthProtectionAccount,
    HealthProtectionTransaction,
    HealthProtectionAllocationRule,
    HealthProtectionClaim
)

class PatientHealthProtectionAccountSerializer(serializers.ModelSerializer):
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    hac_number = serializers.CharField(source='patient.hac_number', read_only=True)

    class Meta:
        model = PatientHealthProtectionAccount
        fields = (
            'id', 'account_reference', 'patient_id', 'patient_name', 'hac_number',
            'available_balance', 'total_contributions', 'total_approved_withdrawals',
            'total_reversals', 'status', 'created_at', 'updated_at'
        )
        read_only_fields = fields


class HealthProtectionTransactionSerializer(serializers.ModelSerializer):
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    source_payment_txn = serializers.CharField(source='source_payment.transaction_id', read_only=True, default='')

    class Meta:
        model = HealthProtectionTransaction
        fields = (
            'id', 'transaction_reference', 'idempotency_key', 'patient_id', 'patient_name',
            'source_payment_txn', 'provider_id', 'provider_name', 'service_category',
            'eligible_payment_amount', 'contribution_percentage', 'amount',
            'transaction_type', 'status', 'balance_before', 'balance_after',
            'reversal_reference', 'description', 'created_at'
        )
        read_only_fields = fields


class HealthProtectionAllocationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthProtectionAllocationRule
        fields = '__all__'


class HealthProtectionClaimSerializer(serializers.ModelSerializer):
    patient_id = serializers.CharField(source='patient.patient_id', read_only=True)
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True, default='')

    class Meta:
        model = HealthProtectionClaim
        fields = (
            'id', 'claim_reference', 'patient_id', 'patient_name', 'expense_category',
            'requested_amount', 'approved_amount', 'provider_name', 'invoice_number',
            'invoice_date', 'description', 'supporting_documents', 'status',
            'reviewer_name', 'review_notes', 'reviewed_at', 'paid_at',
            'created_at', 'updated_at'
        )
        read_only_fields = ('claim_reference', 'approved_amount', 'status', 'reviewed_at', 'paid_at', 'created_at', 'updated_at')

