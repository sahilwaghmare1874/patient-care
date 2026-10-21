"""
PatientCare Healthcare Platform — Payment Views
Implements server-side payment order creation, verified webhook processing,
status polling, and atomic health protection fund contribution crediting.

Contribution Rates (configurable, server-authoritative):
  - Doctor Consultation:    10%
  - Pathology Diagnostic:   10%
  - Pharmacy Purchase:       5%
"""

import hashlib
import hmac
import json
import logging
import uuid
from decimal import Decimal, ROUND_DOWN

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import views, status, permissions
from rest_framework.response import Response

from .gateway import get_payment_gateway, SignatureVerificationError, GatewayError
from .models import Payment, PaymentOrder, WebhookDelivery, PaymentRefund
from .serializers import PaymentSerializer, PaymentOrderSerializer, PaymentRefundSerializer
from patients.models import Patient
from accounts.views import create_audit_log
from notifications.models import Notification

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Healthcare service category → contribution rule mapping (server-side)
# ─────────────────────────────────────────────────────────────────────────────
PAYMENT_TYPE_TO_CATEGORY = {
    'Doctor Payment':    'Doctor Consultation',
    'Pathology Payment': 'Pathology Diagnostic',
    'Pharmacy Payment':  'Pharmacy Purchase',
}

CATEGORY_CONTRIBUTION_RATE = {
    'Doctor Consultation': Decimal('10.00'),
    'Pathology Diagnostic': Decimal('10.00'),
    'Pharmacy Purchase': Decimal('5.00'),
}

PAYMENT_TYPE_TO_PROVIDER_CATEGORY = {
    'Doctor Payment':    'DOCTOR',
    'Pathology Payment': 'PATHOLOGY',
    'Pharmacy Payment':  'PHARMACY',
}


def _paise_from_decimal(amount_decimal):
    """Convert a Decimal INR amount to integer paise without floating-point loss."""
    return int((Decimal(str(amount_decimal)) * 100).to_integral_value())


def _generate_order_id():
    return f"ORD-PC-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def _get_contribution_rate(payment_type):
    """Return the server-authoritative contribution rate for a payment type."""
    from funds.services import get_rule_percentage_for_service
    category = PAYMENT_TYPE_TO_CATEGORY.get(payment_type)
    if not category:
        return Decimal('0.00')
    try:
        return get_rule_percentage_for_service(category)
    except Exception:
        return CATEGORY_CONTRIBUTION_RATE.get(category, Decimal('0.00'))


# ─────────────────────────────────────────────────────────────────────────────
# CREATE ORDER: Initiate payment session before checkout
# ─────────────────────────────────────────────────────────────────────────────
class CreatePaymentOrderView(views.APIView):
    """
    POST /api/payments/orders/create/
    Creates a pending PaymentOrder with a server-generated order ID,
    contacts YouPI-PG (or Sandbox), and returns a checkout URL.
    Never trusts a client-submitted contribution amount or rate.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        patient_id_input = data.get('patient_id', '')
        payment_type = data.get('payment_type', 'Doctor Payment')
        service_description = data.get('service_description', f'Healthcare service: {payment_type}')
        provider_id = str(data.get('provider_id', '')).strip()
        provider_name = str(data.get('provider_name', '')).strip()
        return_url = data.get('return_url', '')

        # ── Validate amount (base bill, excluding GST for doctor/pathology)
        try:
            amount = Decimal(str(data.get('amount', '0'))).quantize(Decimal('0.01'))
        except Exception:
            return Response({'error': 'Invalid amount.'}, status=status.HTTP_400_BAD_REQUEST)
        if amount <= Decimal('0'):
            return Response({'error': 'Amount must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

        # ── Resolve patient
        patient = Patient.objects.filter(patient_id__iexact=patient_id_input).first()
        if not patient:
            return Response({'error': 'Patient not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # ── Server-authoritative rate and contribution (never from browser)
        rate = _get_contribution_rate(payment_type)
        contribution_amount = (amount * rate / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        amount_paise = _paise_from_decimal(amount)
        contribution_paise = _paise_from_decimal(contribution_amount)

        # ── GST (clinical 0%, pharmacy 5%)
        gst = Decimal('0.00')
        if 'Pharmacy' in payment_type:
            gst = (amount * Decimal('0.05')).quantize(Decimal('0.01'))

        provider_category = PAYMENT_TYPE_TO_PROVIDER_CATEGORY.get(payment_type, 'GENERAL')
        order_id = _generate_order_id()
        idempotency_key = f"PCO-{patient.patient_id}-{uuid.uuid4().hex}"

        # ── Initiate gateway checkout session
        gateway = get_payment_gateway()
        order = PaymentOrder(
            order_id=order_id,
            patient=patient,
            provider_id=provider_id,
            provider_name=provider_name,
            provider_category=provider_category,
            service_description=service_description,
            amount=amount,
            amount_paise=amount_paise,
            gst_amount=gst,
            currency='INR',
            contribution_rate=rate,
            expected_contribution_paise=contribution_paise,
            expected_contribution_amount=contribution_amount,
            gateway_name='YOUPI_PG' if getattr(settings, 'PAYMENT_GATEWAY_MODE', 'sandbox').lower() == 'live' else 'SANDBOX',
            idempotency_key=idempotency_key,
            status='PENDING',
            metadata={
                'payment_type': payment_type,
                'gst_amount': str(gst),
            }
        )

        # Need pk for gateway call, so save PENDING first
        order.save()

        try:
            gw_result = gateway.create_payment_session(order, return_url=return_url or None)
            order.gateway_payment_id = gw_result.get('payment_id', '')
            order.checkout_url = gw_result.get('checkout_url', '')
            order.status = 'ACTIVE'
            order.save(update_fields=['gateway_payment_id', 'checkout_url', 'status', 'updated_at'])
        except GatewayError as gw_err:
            order.status = 'FAILED'
            order.save(update_fields=['status', 'updated_at'])
            logger.error("Gateway order creation failed for %s: %s", order_id, str(gw_err))
            return Response(
                {'error': f'Payment gateway could not initiate checkout: {str(gw_err)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "PAYMENT",
            f"Payment order {order_id} created for {patient.patient_id} ₹{amount} ({payment_type}, rate {rate}%, contribution ₹{contribution_amount})",
            patient_id=patient.patient_id,
            request=request
        )

        return Response({
            'order_id': order.order_id,
            'checkout_url': order.checkout_url,
            'amount': float(amount),
            'amount_paise': amount_paise,
            'gst_amount': float(gst),
            'currency': 'INR',
            'contribution_rate': float(rate),
            'expected_contribution': float(contribution_amount),
            'status': order.status,
            'gateway': order.gateway_name,
            'sandbox_mode': getattr(settings, 'PAYMENT_GATEWAY_MODE', 'sandbox').lower() != 'live',
            'message': 'Payment session initiated. Redirect to checkout_url to complete payment.',
        }, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# SANDBOX SIMULATE: Simulate payment completion in sandbox mode (testing only)
# ─────────────────────────────────────────────────────────────────────────────
class SandboxSimulatePaymentView(views.APIView):
    """
    POST /api/payments/sandbox/simulate/
    Sandbox-only: simulates gateway webhook call for an ACTIVE order.
    Only available when PAYMENT_GATEWAY_MODE = 'sandbox'.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if getattr(settings, 'PAYMENT_GATEWAY_MODE', 'sandbox').lower() == 'live':
            return Response({'error': 'Sandbox simulation not available in live mode.'}, status=status.HTTP_403_FORBIDDEN)

        order_id = request.data.get('order_id', '')
        event = request.data.get('event', 'SUCCESS')

        # Normalize event names: accept dotted format (payment.success) or uppercase (SUCCESS)
        _event_map = {
            'payment.success': 'SUCCESS',
            'payment.failed': 'FAILED',
            'payment.expired': 'EXPIRED',
            'payment.cancelled': 'CANCELLED',
        }
        event = _event_map.get(event.lower(), event.upper())

        order = PaymentOrder.objects.filter(order_id=order_id).first()
        if not order:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        if order.status not in ('ACTIVE', 'PENDING'):
            return Response({'error': f'Order is already in status {order.status}.'}, status=status.HTTP_400_BAD_REQUEST)

        from .gateway import SandboxPaymentGateway
        gw = SandboxPaymentGateway()
        raw_body, sig_header = gw.create_signed_webhook_payload(order, event=event)

        # Internally call webhook processing logic directly
        result = _process_webhook_payload(raw_body, sig_header, request.META.get('REMOTE_ADDR', '127.0.0.1'))
        return Response({
            'simulated': True,
            'event': event,
            'order_id': order_id,
            'webhook_result': result,
        })


# ─────────────────────────────────────────────────────────────────────────────
# WEBHOOK: Receive and cryptographically verify payment gateway notifications
# ─────────────────────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(views.APIView):
    """
    POST /api/payments/webhook/
    Receives gateway webhook, verifies HMAC-SHA256 signature using constant-time
    comparison, enforces idempotency/replay protection, and atomically processes
    payment + health protection fund contribution.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        raw_body = request.body
        signature_header = request.META.get('HTTP_X_GATEWAY_SIGNATURE', '')
        ip_address = request.META.get('REMOTE_ADDR', '')

        result = _process_webhook_payload(raw_body, signature_header, ip_address)
        http_status = status.HTTP_200_OK if result.get('accepted') else status.HTTP_400_BAD_REQUEST
        return Response(result, status=http_status)


def _process_webhook_payload(raw_body, signature_header, ip_address):
    """
    Core webhook processing logic (shared by webhook endpoint and sandbox simulator).
    Returns a dict describing the result.
    """
    gateway = get_payment_gateway()

    # ── 1. Signature verification (cryptographic, constant-time)
    try:
        gateway.verify_webhook_signature(raw_body, signature_header)
    except SignatureVerificationError as sig_err:
        logger.warning("Webhook signature verification failed from %s: %s", ip_address, str(sig_err))
        _record_webhook(None, raw_body, signature_header, 'UNKNOWN', 'REJECTED', str(sig_err), ip_address)
        return {'accepted': False, 'error': 'Invalid signature.'}

    # ── 2. Parse payload
    try:
        payload = gateway.parse_webhook_payload(raw_body)
    except Exception as parse_err:
        logger.error("Webhook parse error from %s: %s", ip_address, str(parse_err))
        return {'accepted': False, 'error': 'Malformed payload.'}

    order_id = payload.get('orderId', '')
    event_type = payload.get('event', 'UNKNOWN')
    gateway_payment_id = payload.get('paymentId', '')
    utr = payload.get('utr', '')
    amount_str = payload.get('amount', '0')

    # ── 3. Delivery ID for replay protection
    delivery_id = payload.get('deliveryId') or f"WH-{order_id}-{event_type}-{gateway_payment_id or uuid.uuid4().hex[:8]}"

    # ── 4. Replay protection: check duplicate delivery_id
    if WebhookDelivery.objects.filter(delivery_id=delivery_id, status='PROCESSED').exists():
        logger.info("Duplicate webhook delivery %s — returning idempotent OK.", delivery_id)
        _record_webhook(order_id, raw_body, signature_header, event_type, 'DUPLICATE', 'Already processed.', ip_address, delivery_id=delivery_id)
        return {'accepted': True, 'duplicate': True, 'message': 'Already processed (idempotent).'}

    # ── 5. Resolve order
    order = PaymentOrder.objects.filter(order_id=order_id).first()
    if not order:
        logger.warning("Webhook for unknown order_id: %s", order_id)
        _record_webhook(None, raw_body, signature_header, event_type, 'REJECTED', f'Unknown order {order_id}.', ip_address, delivery_id=delivery_id)
        return {'accepted': False, 'error': f'Unknown order: {order_id}'}

    # ── 6. Amount validation (compare integer paise to prevent float discrepancies)
    try:
        incoming_paise = _paise_from_decimal(Decimal(amount_str))
    except Exception:
        incoming_paise = 0

    if event_type == 'SUCCESS' and incoming_paise != order.amount_paise:
        msg = f"Amount mismatch: expected {order.amount_paise} paise, received {incoming_paise} paise."
        logger.error("Webhook amount mismatch for order %s: %s", order_id, msg)
        _record_webhook(order_id, raw_body, signature_header, event_type, 'REJECTED', msg, ip_address, order=order, delivery_id=delivery_id)
        return {'accepted': False, 'error': msg}

    # ── 7. Handle events
    if event_type in ('FAILED', 'EXPIRED', 'CANCELLED'):
        with transaction.atomic():
            order.status = event_type
            order.save(update_fields=['status', 'updated_at'])
        _record_webhook(order_id, raw_body, signature_header, event_type, 'PROCESSED', '', ip_address, order=order, delivery_id=delivery_id)
        return {'accepted': True, 'event': event_type, 'order_id': order_id}

    if event_type != 'SUCCESS':
        _record_webhook(order_id, raw_body, signature_header, event_type, 'REJECTED', f'Unrecognised event: {event_type}', ip_address, order=order, delivery_id=delivery_id)
        return {'accepted': False, 'error': f'Unrecognised event type: {event_type}'}

    # ── 8. Idempotency: already SUCCESS?
    if order.status == 'SUCCESS':
        logger.info("Order %s already SUCCESS — idempotent.", order_id)
        _record_webhook(order_id, raw_body, signature_header, event_type, 'DUPLICATE', 'Order already succeeded.', ip_address, order=order, delivery_id=delivery_id)
        return {'accepted': True, 'duplicate': True, 'message': 'Already credited (idempotent).'}

    # ── 9. Atomic: mark order SUCCESS + create Payment + credit Health Protection Fund
    payment_type = order.metadata.get('payment_type', 'Doctor Payment')
    service_category = PAYMENT_TYPE_TO_CATEGORY.get(payment_type, '')

    try:
        with transaction.atomic():
            # Mark order as SUCCESS
            order.status = 'SUCCESS'
            order.utr = utr
            order.gateway_payment_id = gateway_payment_id or order.gateway_payment_id
            order.completed_at = timezone.now()
            order.save(update_fields=['status', 'utr', 'gateway_payment_id', 'completed_at', 'updated_at'])

            # Create verified Payment record
            import random
            txn_id = f"TXN-{timezone.now().strftime('%Y%m%d')}-{random.randint(100000, 999999)}"
            payment = Payment.objects.create(
                transaction_id=txn_id,
                order=order,
                patient=order.patient,
                provider_id=order.provider_id,
                payment_type=payment_type,
                service_description=order.service_description,
                amount=order.amount,
                amount_paise=order.amount_paise,
                gst_amount=order.gst_amount,
                payment_method=f"{order.gateway_name} | UPI",
                reference_number=utr,
                utr=utr,
                contribution_rate=order.contribution_rate,
                contribution_amount=order.expected_contribution_amount,
                idempotency_key=f"PAY-{order.idempotency_key}",
                status='Completed',
            )

            # Credit Health Protection Fund (10% Doctor/Pathology, 5% Pharmacy)
            fund_contribution = None
            if service_category:
                try:
                    from funds.services import credit_health_protection_fund
                    fund_contribution = credit_health_protection_fund(
                        payment=payment,
                        patient=order.patient,
                        provider_id=order.provider_id,
                        provider_name=order.provider_name,
                        service_category=service_category,
                        eligible_amount=order.amount,
                        idempotency_key=f"HPF-WH-{order.order_id}",
                    )
                except Exception as hpf_exc:
                    logger.error("HPF credit failed for verified order %s: %s", order_id, str(hpf_exc), exc_info=True)

            # Notify patient
            try:
                if order.patient.user:
                    contribution_msg = (
                        f" Health Protection Fund contribution of ₹{order.expected_contribution_amount} "
                        f"({order.contribution_rate}%) credited to your wallet."
                        if fund_contribution and not fund_contribution.get('is_duplicate') else ""
                    )
                    Notification.objects.create(
                        recipient=order.patient.user,
                        title="Payment Verified & Confirmed ✅",
                        message=(
                            f"Payment ₹{order.amount} for {order.service_description} "
                            f"verified via {order.gateway_name}. Txn: {txn_id}.{contribution_msg}"
                        ),
                        notification_type="PAYMENT",
                    )
            except Exception:
                pass

        _record_webhook(order_id, raw_body, signature_header, event_type, 'PROCESSED', '', ip_address, order=order, delivery_id=delivery_id)

        result = {
            'accepted': True,
            'event': 'SUCCESS',
            'order_id': order_id,
            'transaction_id': payment.transaction_id,
            'utr': utr,
            'amount': float(order.amount),
        }
        if fund_contribution:
            result['health_protection_contribution'] = {
                'credited': not fund_contribution.get('is_duplicate', False),
                'amount': float(fund_contribution.get('credit_amount', 0)),
                'rate': float(order.contribution_rate),
                'account_reference': fund_contribution.get('account_reference', ''),
                'available_balance': float(fund_contribution.get('available_balance', 0)),
            }
        return result

    except Exception as exc:
        logger.error("Atomic payment processing failed for order %s: %s", order_id, str(exc), exc_info=True)
        _record_webhook(order_id, raw_body, signature_header, event_type, 'REJECTED', str(exc), ip_address, order=order, delivery_id=delivery_id)
        return {'accepted': False, 'error': 'Internal processing error. Payment not credited.'}


def _paise_from_decimal(amount_decimal):
    return int((Decimal(str(amount_decimal)) * 100).to_integral_value())


def _record_webhook(order_id, raw_body, signature, event_type, wh_status, error_msg, ip_address, order=None, delivery_id=None):
    try:
        raw_str = raw_body.decode('utf-8') if isinstance(raw_body, bytes) else str(raw_body)
        try:
            payload_dict = json.loads(raw_str)
        except Exception:
            payload_dict = {'raw': raw_str[:2000]}

        _delivery_id = delivery_id or f"WH-{order_id or 'UNKNOWN'}-{uuid.uuid4().hex[:8]}"
        WebhookDelivery.objects.get_or_create(
            delivery_id=_delivery_id,
            defaults={
                'order': order,
                'signature': signature[:255] if signature else '',
                'event_type': event_type,
                'payload': payload_dict,
                'raw_body': raw_str[:10000],
                'status': wh_status,
                'ip_address': ip_address[:45] if ip_address else None,
                'error_message': error_msg[:2000] if error_msg else '',
            }
        )
    except Exception as e:
        logger.error("Failed to record webhook delivery log: %s", str(e))


# ─────────────────────────────────────────────────────────────────────────────
# ORDER STATUS: Frontend polling endpoint
# ─────────────────────────────────────────────────────────────────────────────
class PaymentOrderStatusView(views.APIView):
    """
    GET /api/payments/orders/<order_id>/status/
    Returns current order status for frontend polling during checkout.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, order_id):
        order = PaymentOrder.objects.filter(order_id=order_id).first()
        if not order:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        response_data = {
            'order_id': order.order_id,
            'status': order.status,
            'amount': float(order.amount),
            'contribution_rate': float(order.contribution_rate),
            'expected_contribution': float(order.expected_contribution_amount),
            'completed_at': order.completed_at.isoformat() if order.completed_at else None,
            'utr': order.utr,
        }

        if order.status == 'SUCCESS':
            payment = Payment.objects.filter(order=order).first()
            if payment:
                response_data['transaction_id'] = payment.transaction_id
                response_data['contribution_amount'] = float(payment.contribution_amount)
                # Fetch HPF balance
                try:
                    from funds.models import PatientHealthProtectionAccount
                    acct = PatientHealthProtectionAccount.objects.filter(patient=order.patient).first()
                    if acct:
                        response_data['wallet_balance'] = float(acct.available_balance)
                        response_data['total_contributions'] = float(acct.total_contributions)
                except Exception:
                    pass

        return Response(response_data)


# ─────────────────────────────────────────────────────────────────────────────
# LEGACY: Payment list/create (preserved for backward-compat with existing UI)
# ─────────────────────────────────────────────────────────────────────────────
class PaymentListCreateView(views.APIView):
    """
    GET/POST /api/payments/
    Legacy endpoint preserved for backwards compatibility with existing provider dashboards.
    Direct payment creation (without gateway checkout) is retained for internal
    admin/simulation use; new patient-facing flows must use /api/payments/orders/create/.
    """
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

        import random
        rnd = random.randint(100000, 999999)
        transaction_id = f"TXN-{timezone.now().strftime('%Y%m%d')}-{rnd}"

        amount = Decimal(str(data.get('amount', 500.00)))
        payment_type = data.get('payment_type', 'Doctor Payment')

        # Authoritative rate from DB rules
        rate = _get_contribution_rate(payment_type)
        contribution_amount = (amount * rate / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_DOWN)

        gst = Decimal('0.00')
        if 'Pharmacy' in payment_type or 'Medicine' in data.get('service_description', ''):
            gst = (amount * Decimal('0.05')).quantize(Decimal('0.01'))

        payment = Payment.objects.create(
            transaction_id=transaction_id,
            patient=patient,
            provider_id=data.get('provider_id', ''),
            payment_type=payment_type,
            service_description=data.get('service_description', f"Payment for {payment_type}"),
            amount=amount,
            amount_paise=_paise_from_decimal(amount),
            gst_amount=gst,
            payment_method=data.get('payment_method', 'Assurance Benefit Wallet'),
            reference_number=f"REF-{random.randint(10000000, 99999999)}",
            contribution_rate=rate,
            contribution_amount=contribution_amount,
            status='Completed'
        )

        fund_contribution = None
        service_category = PAYMENT_TYPE_TO_CATEGORY.get(payment_type)
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
                logger.error("HPF credit failed for legacy payment %s: %s", payment.transaction_id, str(hpf_exc), exc_info=True)

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "PAYMENT",
            f"Legacy payment {payment.transaction_id} for {patient.patient_id} ₹{payment.amount} (rate {rate}%, contribution ₹{contribution_amount})",
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
                "credited": not fund_contribution.get('is_duplicate', False),
                "credit_amount": float(fund_contribution.get('credit_amount', 0)),
                "rate": float(rate),
                "account_reference": fund_contribution.get('account_reference', ''),
                "available_balance": float(fund_contribution.get('available_balance', 0)),
                "is_duplicate": fund_contribution.get('is_duplicate', False),
            }

        return Response(response_data, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# RECEIPT: Existing receipt endpoint (preserved)
# ─────────────────────────────────────────────────────────────────────────────
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
            "utr": payment.utr,
            "amount": float(payment.amount),
            "gst_amount": float(payment.gst_amount),
            "total_paid": float(payment.amount + payment.gst_amount),
            "contribution_rate": float(payment.contribution_rate),
            "contribution_amount": float(payment.contribution_amount),
            "status": payment.status,
            "order_id": payment.order.order_id if payment.order else None,
        }

        try:
            from funds.models import HealthProtectionTransaction
            hpf_txn = HealthProtectionTransaction.objects.filter(source_payment=payment).first()
            if hpf_txn:
                receipt["health_protection_contribution"] = float(hpf_txn.amount)
                receipt["wallet_balance_after"] = float(hpf_txn.balance_after)
        except Exception as e:
            logger.warning("Could not retrieve HPF transaction for receipt %s: %s", transaction_id, str(e))

        return Response({"receipt": receipt})


# ─────────────────────────────────────────────────────────────────────────────
# REFUND: Process verified refund with compensating ledger reversal
# ─────────────────────────────────────────────────────────────────────────────
class PaymentRefundView(views.APIView):
    """
    POST /api/payments/orders/<order_id>/refund/
    Processes a refund on a SUCCESS order, records a PaymentRefund,
    and creates a compensating REVERSAL entry in the Health Protection Fund ledger.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, order_id):
        order = PaymentOrder.objects.filter(order_id=order_id).first()
        if not order:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        if order.status != 'SUCCESS':
            return Response({'error': f'Cannot refund order in status {order.status}. Only SUCCESS orders can be refunded.'}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get('reason', 'Merchant-initiated refund')
        try:
            refund_amount = Decimal(str(request.data.get('amount', str(order.amount))))
        except Exception:
            return Response({'error': 'Invalid refund amount.'}, status=status.HTTP_400_BAD_REQUEST)

        if refund_amount <= 0 or refund_amount > order.amount:
            return Response({'error': f'Refund amount must be between 0 and ₹{order.amount}.'}, status=status.HTTP_400_BAD_REQUEST)

        refund_paise = _paise_from_decimal(refund_amount)
        refund_ref = f"REF-{order_id}-{uuid.uuid4().hex[:8].upper()}"
        reversal_ref = ''

        try:
            with transaction.atomic():
                # Update order status
                order.status = 'REFUNDED'
                order.save(update_fields=['status', 'updated_at'])

                # Update linked payment
                payment = Payment.objects.filter(order=order).first()
                if payment:
                    payment.status = 'Refunded'
                    payment.save(update_fields=['status'])

                # Create compensating HPF reversal
                if payment:
                    try:
                        from funds.services import reverse_health_protection_fund
                        reversal = reverse_health_protection_fund(
                            source_payment=payment,
                            patient=order.patient,
                            reason=reason,
                            idempotency_key=f"REV-{refund_ref}",
                        )
                        reversal_ref = reversal.get('transaction_reference', '')
                    except Exception as rev_exc:
                        logger.error("HPF reversal failed for refund %s: %s", refund_ref, str(rev_exc), exc_info=True)

                # Record refund
                PaymentRefund.objects.create(
                    refund_reference=refund_ref,
                    payment_order=order,
                    refund_amount_paise=refund_paise,
                    refund_amount=refund_amount,
                    reason=reason,
                    reversal_ledger_reference=reversal_ref,
                    status='COMPLETED',
                )

            create_audit_log(
                request.user if request.user.is_authenticated else None,
                "PAYMENT",
                f"Refund {refund_ref} processed for order {order_id} ₹{refund_amount}. Reason: {reason}",
                request=request
            )

            return Response({
                'refund_reference': refund_ref,
                'order_id': order_id,
                'refund_amount': float(refund_amount),
                'reversal_ledger_reference': reversal_ref,
                'status': 'COMPLETED',
                'message': 'Refund processed and Health Protection Fund reversal recorded.',
            })

        except Exception as exc:
            logger.error("Refund processing failed for order %s: %s", order_id, str(exc), exc_info=True)
            return Response({'error': 'Refund processing failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─────────────────────────────────────────────────────────────────────────────
# ORDERS LIST: For admin/dashboard
# ─────────────────────────────────────────────────────────────────────────────
class PaymentOrderListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        orders = PaymentOrder.objects.select_related('patient').all()
        if patient_id:
            orders = orders.filter(patient__patient_id__iexact=patient_id)
        serializer = PaymentOrderSerializer(orders[:50], many=True)
        return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# WEBHOOK DELIVERY AUDIT LOG (Admin only)
# ─────────────────────────────────────────────────────────────────────────────
class WebhookDeliveryListView(views.APIView):
    """
    GET /api/payments/webhook-deliveries/
    Returns paginated webhook delivery audit log. Admin-only.
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from django.db.models import Q
        limit = min(int(request.query_params.get('limit', 50)), 200)
        offset = int(request.query_params.get('offset', 0))
        order_id_filter = request.query_params.get('order_id', '')

        qs = WebhookDelivery.objects.select_related('order').order_by('-created_at')
        if order_id_filter:
            qs = qs.filter(Q(order__order_id=order_id_filter) | Q(payload__orderId=order_id_filter))

        total = qs.count()
        deliveries = qs[offset:offset + limit]

        data = []
        for d in deliveries:
            resolved_order_id = d.order.order_id if d.order else (d.payload.get('orderId') if isinstance(d.payload, dict) else None)
            data.append({
                'id': d.id,
                'delivery_id': d.delivery_id,
                'order_id': resolved_order_id,
                'event_type': d.event_type,
                'status': d.status,
                'error_message': d.error_message,
                'ip_address': d.ip_address,
                'received_at': d.created_at.isoformat() if d.created_at else None,
            })

        return Response({
            'total': total,
            'offset': offset,
            'limit': limit,
            'results': data,
        })
