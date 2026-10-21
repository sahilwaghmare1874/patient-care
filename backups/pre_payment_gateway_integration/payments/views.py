import logging
from rest_framework import views, status, permissions
from rest_framework.response import Response
from decimal import Decimal
import random
from .models import Payment
from .serializers import PaymentSerializer
from patients.models import Patient
from accounts.views import create_audit_log
from notifications.models import Notification

logger = logging.getLogger(__name__)

# Payment type → Health Protection Fund service category mapping
ELIGIBLE_SERVICE_CATEGORIES = {
    'Doctor Payment': 'Doctor Consultation',
    'Pathology Payment': 'Pathology Diagnostic',
    'Pharmacy Payment': 'Pharmacy Purchase',
}


class PaymentListCreateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        payments = Payment.objects.all()
        if patient_id:
            payments = payments.filter(patient__patient_id__iexact=patient_id)
        serializer = PaymentSerializer(payments, many=True)
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

        rnd = random.randint(100000, 999999)
        transaction_id = f"TXN-2026-{rnd}"

        amount = Decimal(str(data.get('amount', 500.00)))
        payment_type = data.get('payment_type', 'Doctor Payment')

        # Clinical services (Doctor, Pathology) are 0% GST exempt by Indian Ministry of Finance; Medicines have 5% GST
        gst = Decimal('0.00')
        if 'Pharmacy' in payment_type or 'Medicine' in data.get('service_description', ''):
            gst = Decimal(str(round(float(amount) * 0.05, 2)))

        payment = Payment.objects.create(
            transaction_id=transaction_id,
            patient=patient,
            provider_id=data.get('provider_id', ''),
            payment_type=payment_type,
            service_description=data.get('service_description', f"Payment for {payment_type}"),
            amount=amount,
            gst_amount=gst,
            payment_method=data.get('payment_method', 'Assurance Benefit Wallet'),
            reference_number=f"REF-{random.randint(10000000, 99999999)}",
            status='Completed'
        )

        # --- Health Protection Fund: automatic 10% credit on eligible payment types ---
        fund_contribution = None
        service_category = ELIGIBLE_SERVICE_CATEGORIES.get(payment_type)
        if service_category:
            try:
                from funds.services import credit_health_protection_fund
                fund_contribution = credit_health_protection_fund(
                    payment=payment,
                    patient=patient,
                    service_category=service_category,
                    idempotency_key=payment.transaction_id,
                )
            except Exception as hpf_exc:
                # Fund credit failure must NOT fail the payment — log and continue
                logger.error(
                    "Health Protection Fund credit failed for payment %s: %s",
                    payment.transaction_id,
                    str(hpf_exc),
                    exc_info=True,
                )
        # --- End Health Protection Fund ---

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "PAYMENT",
            f"Processed payment {payment.transaction_id} for {patient.patient_id} (Amount: ₹{payment.amount})",
            patient_id=patient.patient_id,
            request=request
        )

        if patient.user:
            Notification.objects.create(
                recipient=patient.user,
                title="Payment Processed Successfully",
                message=f"Payment receipt {payment.transaction_id} generated for ₹{payment.amount} ({payment.payment_type}).",
                notification_type="PAYMENT"
            )

        response_data = {
            "message": "Payment completed successfully.",
            "payment": PaymentSerializer(payment).data
        }
        if fund_contribution:
            response_data["health_protection_contribution"] = {
                "credited": True,
                "credit_amount": float(fund_contribution.get('credit_amount', 0)),
                "account_reference": fund_contribution.get('account_reference', ''),
                "available_balance": float(fund_contribution.get('available_balance', 0)),
                "is_duplicate": fund_contribution.get('is_duplicate', False),
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


class PaymentReceiptDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, transaction_id):
        payment = Payment.objects.filter(transaction_id__iexact=transaction_id).first()
        if not payment:
            return Response({"error": "Payment receipt not found."}, status=status.HTTP_404_NOT_FOUND)

        receipt = {
            "transaction_id": payment.transaction_id,
            "date": payment.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "patient_id": payment.patient.patient_id,
            "patient_name": payment.patient.full_name,
            "hac_number": payment.patient.hac_number,
            "payment_type": payment.payment_type,
            "service_description": payment.service_description,
            "payment_method": payment.payment_method,
            "reference_number": payment.reference_number,
            "amount": float(payment.amount),
            "gst_amount": float(payment.gst_amount),
            "total_paid": float(payment.amount + payment.gst_amount),
            "status": payment.status
        }

        # Include Health Protection Fund contribution if one was recorded for this payment
        try:
            from funds.models import HealthProtectionTransaction
            hpf_txn = HealthProtectionTransaction.objects.filter(source_payment=payment).first()
            if hpf_txn:
                receipt["health_protection_contribution"] = float(hpf_txn.amount)
        except Exception as hpf_exc:
            logger.warning(
                "Could not retrieve HPF transaction for receipt %s: %s",
                transaction_id,
                str(hpf_exc),
            )

        return Response({"receipt": receipt})
