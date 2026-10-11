from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from django.utils import timezone
from .models import InsuranceCompany, InsurancePolicy, InsuranceClaim
from .serializers import InsuranceCompanySerializer, InsurancePolicySerializer, InsuranceClaimSerializer
from patients.models import Patient
from accounts.views import create_audit_log
from notifications.models import Notification

class InsuranceCompanyListView(generics.ListCreateAPIView):
    queryset = InsuranceCompany.objects.all()
    serializer_class = InsuranceCompanySerializer
    permission_classes = [permissions.AllowAny]


class InsurancePolicyListView(generics.ListCreateAPIView):
    queryset = InsurancePolicy.objects.all()
    serializer_class = InsurancePolicySerializer
    permission_classes = [permissions.AllowAny]


class InsuranceClaimListCreateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        claims = InsuranceClaim.objects.all()
        if patient_id:
            claims = claims.filter(patient__patient_id__iexact=patient_id)
        serializer = InsuranceClaimSerializer(claims, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        patient_id_input = data.pop('patient_id', None)
        if isinstance(patient_id_input, list):
            patient_id_input = patient_id_input[0]

        patient = None
        if patient_id_input:
            patient = Patient.objects.filter(patient_id__iexact=patient_id_input).first()
        if not patient and 'patient' in data:
            patient = Patient.objects.filter(id=data['patient']).first()

        if not patient:
            return Response({"error": "Patient not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve or find active policy
        policy = patient.insurance_policies.filter(is_active=True).first()
        if not policy:
            company = InsuranceCompany.objects.first()
            if not company:
                company = InsuranceCompany.objects.create(
                    company_name="National Health Insurance Co.",
                    contact_email="claims@nationalhealth.gov.in",
                    contact_phone="1800-11-4455",
                    license_number="IRDA-NHI-2026-99"
                )
            policy = InsurancePolicy.objects.create(
                patient=patient,
                company=company,
                policy_number=f"POL-2026-{patient.id:04d}",
                coverage_limit=500000.00,
                start_date=timezone.now().date(),
                end_date=timezone.now().date().replace(year=timezone.now().year + 1)
            )

        count = InsuranceClaim.objects.count() + 1
        claim_id = f"CLM-2026-{count:04d}"

        treatment_cost = data.get('treatment_cost', 50000.00)
        requested_amount = data.get('requested_amount', 30000.00)

        claim = InsuranceClaim.objects.create(
            claim_id=claim_id,
            patient=patient,
            policy=policy,
            insurance_company=policy.company.company_name,
            treatment_cost=treatment_cost,
            requested_amount=requested_amount,
            approved_amount=0.00,
            status='Pending',
            remarks=data.get('remarks', 'Government funding deficit coverage claim.')
        )

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "INSURANCE",
            f"Submitted insurance claim: {claim.claim_id} for {patient.patient_id} (Requested: ₹{claim.requested_amount})",
            patient_id=patient.patient_id,
            request=request
        )

        if patient.user:
            Notification.objects.create(
                recipient=patient.user,
                title="Insurance Claim Submitted",
                message=f"Insurance claim {claim.claim_id} for ₹{claim.requested_amount} submitted successfully.",
                notification_type="INSURANCE"
            )

        return Response({
            "message": "Insurance claim submitted successfully.",
            "claim": InsuranceClaimSerializer(claim).data
        }, status=status.HTTP_201_CREATED)


class InsuranceClaimDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request, claim_id):
        claim = InsuranceClaim.objects.filter(claim_id__iexact=claim_id).first()
        if not claim:
            return Response({"error": "Claim not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status', claim.status)
        approved_amount = request.data.get('approved_amount', claim.approved_amount)
        remarks = request.data.get('remarks', claim.remarks)

        claim.status = new_status
        claim.approved_amount = approved_amount
        claim.remarks = remarks
        if new_status in ('Approved', 'Partially Approved'):
            claim.approval_date = timezone.now().date()
        claim.save()

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "INSURANCE",
            f"Updated insurance claim: {claim.claim_id} to {new_status} (Approved: ₹{claim.approved_amount})",
            patient_id=claim.patient.patient_id,
            request=request
        )

        if claim.patient.user:
            Notification.objects.create(
                recipient=claim.patient.user,
                title="Insurance Claim Status Updated",
                message=f"Claim {claim.claim_id} is now '{claim.status}' with approved amount: ₹{claim.approved_amount}.",
                notification_type="INSURANCE"
            )

        return Response({
            "message": f"Claim updated to {new_status}.",
            "claim": InsuranceClaimSerializer(claim).data
        })
