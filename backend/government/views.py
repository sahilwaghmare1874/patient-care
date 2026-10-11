from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from .models import GovernmentScheme
from .serializers import GovernmentSchemeSerializer
from patients.models import Patient
from funds.models import FundAllocation, AllocationConfiguration, PatientHealthProtectionAccount, HealthProtectionTransaction
from insurance.models import InsuranceClaim
from accounts.models import DoctorProfile, PathologyProfile, PharmacyProfile
from accounts.views import create_audit_log

class GovernmentSchemeListCreateView(generics.ListCreateAPIView):
    queryset = GovernmentScheme.objects.all()
    serializer_class = GovernmentSchemeSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        scheme = serializer.save()
        create_audit_log(
            self.request.user if self.request.user.is_authenticated else None,
            "GOVERNMENT",
            f"Created new healthcare scheme: {scheme.scheme_code} - {scheme.scheme_name}",
            request=self.request
        )


class GovernmentSchemeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GovernmentScheme.objects.all()
    serializer_class = GovernmentSchemeSerializer
    permission_classes = [permissions.AllowAny]


class GovernmentDashboardStatsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_patients = Patient.objects.count()
        total_schemes = GovernmentScheme.objects.count()
        active_schemes = GovernmentScheme.objects.filter(status='Active').count()
        
        allocations = FundAllocation.objects.all()
        total_approved_funds = sum(float(a.total_approved_fund) for a in allocations)
        total_gov_funds = sum(float(a.approved_government_fund) for a in allocations)
        total_insurance_funds = sum(float(a.approved_insurance_fund) for a in allocations)
        
        total_doctor_payouts = sum(float(a.doctor_allocation) for a in allocations)
        total_pathology_payouts = sum(float(a.pathology_allocation) for a in allocations)
        total_pharmacy_payouts = sum(float(a.pharmacy_allocation) for a in allocations)
        total_patient_benefits = sum(float(a.patient_benefit_amount) for a in allocations)
        
        pending_claims = InsuranceClaim.objects.filter(status='Pending').count()
        
        config = AllocationConfiguration.objects.filter(is_active=True).first()
        config_data = {
            "doctor_percentage": float(config.doctor_percentage) if config else 10.0,
            "pathology_percentage": float(config.pathology_percentage) if config else 10.0,
            "pharmacy_percentage": float(config.pharmacy_percentage) if config else 5.0,
            "government_percentage": float(config.government_percentage) if config else 5.0,
            "patient_benefit_percentage": float(config.patient_benefit_percentage) if config else 70.0,
        }

        # Health Protection Fund platform-wide totals
        from django.db.models import Sum
        hpf_totals = PatientHealthProtectionAccount.objects.aggregate(
            total_contributions=Sum('total_contributions'),
            total_available=Sum('available_balance'),
            total_withdrawals=Sum('total_approved_withdrawals'),
        )
        hpf_contribution_count = HealthProtectionTransaction.objects.filter(
            transaction_type='CONTRIBUTION', status='COMPLETED'
        ).count()
        hpf_active_accounts = PatientHealthProtectionAccount.objects.filter(status='ACTIVE').count()

        return Response({
            "total_patients": total_patients,
            "total_schemes": total_schemes,
            "active_schemes": active_schemes,
            "total_approved_funds": total_approved_funds,
            "total_gov_funds": total_gov_funds,
            "total_insurance_funds": total_insurance_funds,
            "total_distributed_funds": total_doctor_payouts + total_pathology_payouts + total_pharmacy_payouts,
            "total_doctor_payouts": total_doctor_payouts,
            "total_pathology_payouts": total_pathology_payouts,
            "total_pharmacy_payouts": total_pharmacy_payouts,
            "total_patient_benefits": total_patient_benefits,
            "pending_claims": pending_claims,
            "total_doctors": DoctorProfile.objects.count(),
            "total_pathology_labs": PathologyProfile.objects.count(),
            "total_pharmacies": PharmacyProfile.objects.count(),
            "allocation_config": config_data,
            "health_protection_fund": {
                "total_contributions_credited": float(hpf_totals['total_contributions'] or 0),
                "total_available_balance": float(hpf_totals['total_available'] or 0),
                "total_approved_withdrawals": float(hpf_totals['total_withdrawals'] or 0),
                "contribution_transactions": hpf_contribution_count,
                "active_accounts": hpf_active_accounts,
                "policy": "10% auto-credit from Doctor, Pathology, and Pharmacy payments.",
            }
        })


from .models import SchemeApplication
from django.utils import timezone
import datetime

class SchemeApplicationView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, application_id=None):
        patient_id = request.query_params.get('patient_id')
        qs = SchemeApplication.objects.select_related('patient', 'scheme').all()
        if patient_id:
            qs = qs.filter(patient__patient_id__iexact=patient_id)
        if application_id:
            app = qs.filter(application_id=application_id).first()
            if not app:
                return Response({'error': 'Application not found.'}, status=404)
            return Response(self._serialize(app))
        return Response([self._serialize(a) for a in qs])

    def _serialize(self, app):
        return {
            'application_id': app.application_id,
            'patient_id': app.patient.patient_id,
            'patient_name': app.patient.full_name,
            'scheme_code': app.scheme.scheme_code,
            'scheme_name': app.scheme.scheme_name,
            'hospital_name': app.hospital_name,
            'treatment_description': app.treatment_description,
            'estimated_cost': float(app.estimated_cost),
            'requested_amount': float(app.requested_amount),
            'approved_amount': float(app.approved_amount),
            'status': app.status,
            'officer_remarks': app.officer_remarks,
            'submitted_at': str(app.submitted_at) if app.submitted_at else None,
            'approved_at': str(app.approved_at) if app.approved_at else None,
            'created_at': str(app.created_at),
        }

    def post(self, request, application_id=None):
        if application_id:
            return self._update(request, application_id)
        return self._create(request)

    def _create(self, request):
        patient_id = request.data.get('patient_id')
        scheme_code = request.data.get('scheme_code')
        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient:
            return Response({'error': 'Patient not found.'}, status=400)
        scheme = GovernmentScheme.objects.filter(scheme_code=scheme_code, status='Active').first()
        if not scheme:
            return Response({'error': 'Active scheme not found.'}, status=400)

        count = SchemeApplication.objects.count() + 1
        app_id = f'SCHAPP-{datetime.date.today().year}-{count:05d}'

        app = SchemeApplication.objects.create(
            application_id=app_id,
            patient=patient,
            scheme=scheme,
            hospital_name=request.data.get('hospital_name', ''),
            treatment_description=request.data.get('treatment_description', ''),
            estimated_cost=request.data.get('estimated_cost', 0),
            requested_amount=request.data.get('requested_amount', 0),
            status='Submitted',
            submitted_at=timezone.now(),
        )
        return Response({'message': 'Scheme application submitted.', 'application': self._serialize(app)}, status=201)

    def _update(self, request, application_id):
        app = SchemeApplication.objects.filter(application_id=application_id).first()
        if not app:
            return Response({'error': 'Application not found.'}, status=404)
        new_status = request.data.get('status')
        officer_remarks = request.data.get('officer_remarks', '')
        approved_amount = request.data.get('approved_amount')
        if new_status:
            app.status = new_status
            if new_status == 'Approved':
                app.approved_at = timezone.now()
        if officer_remarks:
            app.officer_remarks = officer_remarks
        if approved_amount is not None:
            app.approved_amount = approved_amount
        app.save()
        return Response({'message': 'Application updated.', 'application': self._serialize(app)})
