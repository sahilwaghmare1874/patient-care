from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
import random
from accounts.models import User
from accounts.views import create_audit_log
from notifications.models import Notification
from .models import Patient
from .serializers import PatientSerializer, PatientCreateSerializer

def generate_patient_id():
    import re
    existing_ids = list(Patient.objects.filter(patient_id__startswith='PAT-2026-').values_list('patient_id', flat=True))
    max_num = 0
    for pid in existing_ids:
        match = re.search(r'PAT-2026-(\d+)', pid)
        if match:
            try:
                max_num = max(max_num, int(match.group(1)))
            except ValueError:
                pass
    next_num = max(max_num + 1, Patient.objects.count() + 1)
    new_pid = f"PAT-2026-{next_num:06d}"
    while Patient.objects.filter(patient_id=new_pid).exists():
        next_num += 1
        new_pid = f"PAT-2026-{next_num:06d}"
    return new_pid

def generate_hac_number():
    while True:
        part1 = random.randint(1000, 9999)
        part2 = random.randint(1000, 9999)
        hac = f"HAC-91-{part1}-{part2}-2026"
        if not Patient.objects.filter(hac_number=hac).exists():
            return hac


class PatientListCreateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('search', '').strip()
        patients = Patient.objects.all()
        if query:
            patients = patients.filter(
                patient_id__icontains=query
            ) | patients.filter(
                full_name__icontains=query
            ) | patients.filter(
                mobile__icontains=query
            ) | patients.filter(
                pan_number__iexact=query
            )
        serializer = PatientSerializer(patients[:50], many=True)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        pan = request.data.get('pan_number', '').strip().upper()
        if not pan:
            return Response({"error": "PAN Card Number is mandatory."}, status=status.HTTP_400_BAD_REQUEST)

        # STEP 1: Check whether PAN already exists
        existing_patient = Patient.objects.filter(pan_number=pan).first()
        if existing_patient:
            create_audit_log(
                request.user if request.user.is_authenticated else None,
                "PATIENT",
                f"Existing PAN lookup: {existing_patient.patient_id}",
                patient_id=existing_patient.patient_id,
                request=request
            )
            return Response({
                "is_existing": True,
                "message": f"Patient record already exists with Patient ID: {existing_patient.patient_id}. Please use your existing account.",
                "patient": PatientSerializer(existing_patient).data
            }, status=status.HTTP_200_OK)

        # STEP 2: Create new patient
        serializer = PatientCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        username = data.pop('username', None)
        password = data.pop('password', None)

        user = None
        if username and password:
            final_username = username
            while User.objects.filter(username=final_username).exists():
                final_username = f"{username}_{random.randint(100, 9999)}"
            user = User.objects.create_user(
                username=final_username,
                email=data.get('email') or f"{final_username}@patientcare.org",
                mobile=data.get('mobile'),
                role='PATIENT'
            )
            user.set_password(password)
            user.save()

        patient_id = generate_patient_id()
        hac_number = generate_hac_number()
        data.pop('pan_number', None)

        if data.get('consent_data_processing'):
            data['consent_timestamp'] = timezone.now()

        patient = Patient.objects.create(
            user=user,
            patient_id=patient_id,
            hac_number=hac_number,
            pan_number=pan,
            **data
        )

        create_audit_log(
            user,
            "PATIENT",
            f"Created new Patient record: {patient.patient_id}",
            patient_id=patient.patient_id,
            request=request
        )

        if user:
            Notification.objects.create(
                recipient=user,
                title="Health ID Created",
                message=f"Welcome to PatientCare! Your permanent Patient ID is {patient.patient_id} and HAC Card is {patient.hac_number}.",
                notification_type="REGISTRATION"
            )

        return Response({
            "is_existing": False,
            "message": f"New patient registered successfully with Patient ID: {patient.patient_id}",
            "patient": PatientSerializer(patient).data
        }, status=status.HTTP_201_CREATED)


class PatientDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, identifier):
        patient = Patient.objects.filter(patient_id__iexact=identifier).first()
        if not patient and identifier.isdigit():
            patient = Patient.objects.filter(id=identifier).first()

        if not patient:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            request.user.role if request.user.is_authenticated else "GUEST",
            f"Viewed patient profile: {patient.patient_id}",
            patient_id=patient.patient_id,
            request=request
        )
        return Response(PatientSerializer(patient).data)


class PatientLookupView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('query', '').strip()
        if not query:
            return Response({"error": "Search query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

        patient = Patient.objects.filter(
            patient_id__iexact=query
        ).first() or Patient.objects.filter(
            pan_number__iexact=query
        ).first() or Patient.objects.filter(
            mobile=query
        ).first() or Patient.objects.filter(
            hac_number__iexact=query
        ).first()

        if not patient:
            return Response({"error": f"Patient with identifier '{query}' not found."}, status=status.HTTP_404_NOT_FOUND)

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            request.user.role if request.user.is_authenticated else "PROVIDER",
            f"Searched patient: {patient.patient_id}",
            patient_id=patient.patient_id,
            request=request
        )

        return Response(PatientSerializer(patient).data)


class PatientCentralizedRecordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, identifier):
        patient = Patient.objects.filter(patient_id__iexact=identifier).first()
        if not patient and identifier.isdigit():
            patient = Patient.objects.filter(id=identifier).first()

        if not patient:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve all connected records
        from doctors.serializers import ConsultationSerializer, PrescriptionSerializer
        from pathology.serializers import PathologyReportSerializer
        from pharmacy.serializers import PharmacyTransactionSerializer
        from funds.serializers import FundAllocationSerializer, HealthProtectionTransactionSerializer
        from funds.models import PatientHealthProtectionAccount, HealthProtectionTransaction
        from insurance.serializers import InsuranceClaimSerializer
        from payments.serializers import PaymentSerializer

        consultations = ConsultationSerializer(patient.consultations.all(), many=True).data
        prescriptions = PrescriptionSerializer(patient.prescriptions.all(), many=True).data
        pathology_reports = PathologyReportSerializer(patient.pathology_reports.all(), many=True).data
        pharmacy_transactions = PharmacyTransactionSerializer(patient.pharmacy_transactions.all(), many=True).data
        fund_allocations = FundAllocationSerializer(patient.fund_allocations.all(), many=True).data
        insurance_claims = InsuranceClaimSerializer(patient.insurance_claims.all(), many=True).data
        payments = PaymentSerializer(patient.payments.all(), many=True).data

        # Calculate totals
        total_consultation_fees = sum(float(c.get('consultation_fee', 0)) for c in consultations)
        total_lab_fees = sum(float(p.get('test_cost', 0)) for p in pathology_reports)
        total_pharmacy_bills = sum(float(m.get('total_amount', 0)) for m in pharmacy_transactions)
        total_treatment_cost = total_consultation_fees + total_lab_fees + total_pharmacy_bills

        total_funds_approved = sum(float(f.get('total_approved_fund', 0)) for f in fund_allocations)
        total_patient_benefits = sum(float(f.get('patient_benefit_amount', 0)) for f in fund_allocations)

        # Health Protection Fund snapshot
        hpf_data = {
            'account_reference': None,
            'available_balance': 0.0,
            'total_contributions': 0.0,
            'total_approved_withdrawals': 0.0,
            'status': None,
            'recent_transactions': []
        }
        hpf_account = PatientHealthProtectionAccount.objects.filter(patient=patient).first()
        if hpf_account:
            recent_hpf_txns = HealthProtectionTransaction.objects.filter(
                protection_account=hpf_account
            ).order_by('-created_at')[:5]
            hpf_data.update({
                'account_reference': hpf_account.account_reference,
                'available_balance': float(hpf_account.available_balance),
                'total_contributions': float(hpf_account.total_contributions),
                'total_approved_withdrawals': float(hpf_account.total_approved_withdrawals),
                'status': hpf_account.status,
                'recent_transactions': HealthProtectionTransactionSerializer(recent_hpf_txns, many=True).data
            })

        return Response({
            "patient": PatientSerializer(patient).data,
            "summary": {
                "total_consultations": len(consultations),
                "total_pathology_tests": len(pathology_reports),
                "total_pharmacy_orders": len(pharmacy_transactions),
                "total_treatment_cost": total_treatment_cost,
                "total_funds_approved": total_funds_approved,
                "total_patient_benefits": total_patient_benefits,
                "hpf_available_balance": hpf_data['available_balance'],
            },
            "health_protection_fund": hpf_data,
            "consultations": consultations,
            "prescriptions": prescriptions,
            "pathology_reports": pathology_reports,
            "pharmacy_transactions": pharmacy_transactions,
            "fund_allocations": fund_allocations,
            "insurance_claims": insurance_claims,
            "payments": payments
        })
