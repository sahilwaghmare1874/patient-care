from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from decimal import Decimal
import logging
from .models import Medicine, PharmacyTransaction
from .serializers import MedicineSerializer, PharmacyTransactionSerializer
from patients.models import Patient
from accounts.models import PharmacyProfile
from doctors.models import Prescription
from accounts.views import create_audit_log
from notifications.models import Notification
from funds.services import credit_health_protection_fund

logger = logging.getLogger(__name__)

class MedicineListView(generics.ListCreateAPIView):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [permissions.AllowAny]


class PharmacyTransactionListCreateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        transactions = PharmacyTransaction.objects.all()
        if patient_id:
            transactions = transactions.filter(patient__patient_id__iexact=patient_id)
        serializer = PharmacyTransactionSerializer(transactions, many=True)
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
            return Response({"error": "Patient not found. Search patient first."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve Pharmacy profile
        pharmacy = None
        if request.user.is_authenticated and hasattr(request.user, 'pharmacy_profile'):
            pharmacy = request.user.pharmacy_profile
        else:
            pharmacy_id_input = data.pop('pharmacy_id', None)
            if pharmacy_id_input:
                pharmacy = PharmacyProfile.objects.filter(pharmacy_id__iexact=pharmacy_id_input).first()
            if not pharmacy:
                pharmacy = PharmacyProfile.objects.first()

        if not pharmacy:
            return Response({"error": "Pharmacy profile not found."}, status=status.HTTP_400_BAD_REQUEST)

        count = PharmacyTransaction.objects.count() + 1
        invoice_number = f"MED-2026-{count:04d}"

        subtotal = Decimal(str(data.get('subtotal_amount', 450.00)))
        # GST on life-saving medicines is standard 5%
        gst = Decimal(str(data.get('gst_amount', round(float(subtotal) * 0.05, 2))))
        total = subtotal + gst

        prescription_obj = None
        rx_id = data.pop('prescription_id', None)
        if rx_id:
            prescription_obj = Prescription.objects.filter(prescription_id__iexact=rx_id).first()
            if prescription_obj:
                prescription_obj.is_dispensed = True
                prescription_obj.save()

        tx = PharmacyTransaction.objects.create(
            invoice_number=invoice_number,
            patient=patient,
            pharmacy=pharmacy,
            prescription=prescription_obj,
            doctor=prescription_obj.doctor if prescription_obj else None,
            medicines_dispensed=data.get('medicines_dispensed', 'Standard prescribed medications'),
            subtotal_amount=subtotal,
            gst_amount=gst,
            total_amount=total,
            payment_status=data.get('payment_status', 'Paid'),
            reimbursement_status=data.get('reimbursement_status', 'Not Claimed')
        )

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "PHARMACY",
            f"Dispensed medicines invoice: {tx.invoice_number} for {patient.patient_id} (Total: ₹{tx.total_amount})",
            patient_id=patient.patient_id,
            request=request
        )

        if patient.user:
            Notification.objects.create(
                recipient=patient.user,
                title="Medicines Dispensed",
                message=f"Prescription dispensed at {pharmacy.pharmacy_name}. Tax invoice: {tx.invoice_number} (₹{tx.total_amount}).",
                notification_type="PHARMACY"
            )

        # --- Health Protection Fund: 10% auto-credit on pharmacy invoice (subtotal, GST-exclusive) ---
        hpf_contribution = None
        try:
            hpf_result = credit_health_protection_fund(
                payment=None,
                patient=patient,
                provider_id=pharmacy.pharmacy_id,
                provider_name=pharmacy.pharmacy_name,
                service_category='Pharmacy Purchase',
                eligible_amount=subtotal,
                idempotency_key=f"PHARM-{tx.invoice_number}"
            )
            if not hpf_result.get('is_duplicate'):
                hpf_contribution = {
                    'credited': True,
                    'credit_amount': float(hpf_result.get('credit_amount', 0)),
                    'available_balance': float(hpf_result.get('available_balance', 0)),
                    'account_reference': hpf_result.get('account_reference'),
                    'is_duplicate': False,
                }
            else:
                hpf_contribution = {'credited': False, 'is_duplicate': True}
        except Exception as hpf_err:
            logger.error(
                "HPF credit failed for pharmacy invoice %s (patient %s): %s",
                tx.invoice_number, patient.patient_id, hpf_err
            )

        response_data = {
            "message": "Medicines successfully dispensed.",
            "transaction": PharmacyTransactionSerializer(tx).data
        }
        if hpf_contribution:
            response_data["health_protection_contribution"] = hpf_contribution

        return Response(response_data, status=status.HTTP_201_CREATED)


class PharmacyDashboardStatsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_tx = PharmacyTransaction.objects.count()
        medicines_count = Medicine.objects.count()
        total_revenue = sum(float(t.total_amount) for t in PharmacyTransaction.objects.all())

        return Response({
            "total_transactions": total_tx,
            "medicines_in_stock": medicines_count,
            "total_dispensed_amount": total_revenue,
            "recent_transactions": PharmacyTransactionSerializer(PharmacyTransaction.objects.all()[:5], many=True).data
        })
