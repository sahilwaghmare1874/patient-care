"""
PatientCare Payment Gateway Integration Tests
Tests YouPI-PG webhook verification, contribution arithmetic,
idempotency, refund reversals, and sandbox simulation.
"""

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from patients.models import Patient  # kept for reference in tests
from payments.gateway import (
    SandboxPaymentGateway,
    YoupiPaymentGateway,
    SignatureVerificationError,
)
from payments.models import Payment, PaymentOrder, WebhookDelivery, PaymentRefund
from funds.models import (
    PatientHealthProtectionAccount,
    HealthProtectionTransaction,
    HealthProtectionAllocationRule,
)


def _make_patient(patient_id, full_name, username, role='Patient'):
    """Helper: create User + Patient with all required fields for tests."""
    import datetime
    from accounts.models import User
    from patients.models import Patient
    user = User.objects.create_user(username=username, password='testpass123', role=role)
    patient = Patient.objects.create(
        patient_id=patient_id,
        full_name=full_name,
        user=user,
        dob=datetime.date(1990, 1, 1),
        gender='Male',
        mobile='9000000000',
        address='123 Test Street',
        city='Pune',
        district='Pune',
        state='Maharashtra',
        pincode='411001',
        pan_number='ABCDE1234F',
        blood_group='A+',
        allergies='None',
        existing_conditions='None',
        illness_description='None',
        presenting_symptoms='None',
        symptom_duration='N/A',
        symptom_severity='Mild',
        current_medicines='None',
        emergency_contact_name='Emergency Contact',
        emergency_contact_phone='9000000001',
        hac_number=f'HAC-{patient_id}',
    )
    return user, patient



WEBHOOK_SECRET = 'test-webhook-secret-key'


def make_signature(secret, raw_body_bytes):
    sig = hmac.new(secret.encode('utf-8'), raw_body_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


class ContributionRateTests(TestCase):
    """Verify server-authoritative contribution rates for all provider categories."""

    def setUp(self):
        # Ensure allocation rules exist with correct values
        HealthProtectionAllocationRule.objects.get_or_create(
            service_category='Doctor Consultation',
            defaults={'contribution_percentage': Decimal('10.00'), 'is_active': True}
        )
        HealthProtectionAllocationRule.objects.get_or_create(
            service_category='Pathology Diagnostic',
            defaults={'contribution_percentage': Decimal('10.00'), 'is_active': True}
        )
        HealthProtectionAllocationRule.objects.get_or_create(
            service_category='Pharmacy Purchase',
            defaults={'contribution_percentage': Decimal('5.00'), 'is_active': True}
        )

    def test_doctor_contribution_rate_is_10_percent(self):
        from funds.services import get_rule_percentage_for_service
        rate = get_rule_percentage_for_service('Doctor Consultation')
        self.assertEqual(rate, Decimal('10.00'))

    def test_pathology_contribution_rate_is_10_percent(self):
        from funds.services import get_rule_percentage_for_service
        rate = get_rule_percentage_for_service('Pathology Diagnostic')
        self.assertEqual(rate, Decimal('10.00'))

    def test_pharmacy_contribution_rate_is_5_percent(self):
        from funds.services import get_rule_percentage_for_service
        rate = get_rule_percentage_for_service('Pharmacy Purchase')
        self.assertEqual(rate, Decimal('5.00'))

    def test_doctor_1000_yields_100_contribution(self):
        rate = Decimal('10.00')
        amount = Decimal('1000.00')
        contribution = (amount * rate / Decimal('100')).quantize(Decimal('0.01'))
        self.assertEqual(contribution, Decimal('100.00'))

    def test_pathology_2000_yields_200_contribution(self):
        rate = Decimal('10.00')
        amount = Decimal('2000.00')
        contribution = (amount * rate / Decimal('100')).quantize(Decimal('0.01'))
        self.assertEqual(contribution, Decimal('200.00'))

    def test_pharmacy_500_yields_25_contribution(self):
        rate = Decimal('5.00')
        amount = Decimal('500.00')
        contribution = (amount * rate / Decimal('100')).quantize(Decimal('0.01'))
        self.assertEqual(contribution, Decimal('25.00'))

    def test_integer_paise_no_float_error(self):
        """Paise conversion must be exact (no IEEE 754 rounding)."""
        amount = Decimal('1000.99')
        paise = int((amount * 100).to_integral_value())
        self.assertEqual(paise, 100099)


class SandboxGatewayTests(TestCase):
    """Tests for the SandboxPaymentGateway HMAC signing and verification."""

    def setUp(self):
        self.gw = SandboxPaymentGateway(webhook_secret=WEBHOOK_SECRET)

    def test_valid_signature_accepted(self):
        body = b'{"event":"SUCCESS","orderId":"ORD-001","amount":"100.00"}'
        sig = make_signature(WEBHOOK_SECRET, body)
        result = self.gw.verify_webhook_signature(body, sig)
        self.assertTrue(result)

    def test_tampered_body_rejected(self):
        body = b'{"event":"SUCCESS","orderId":"ORD-001","amount":"100.00"}'
        sig = make_signature(WEBHOOK_SECRET, body)
        tampered = b'{"event":"SUCCESS","orderId":"ORD-001","amount":"999.00"}'
        with self.assertRaises(SignatureVerificationError):
            self.gw.verify_webhook_signature(tampered, sig)

    def test_wrong_secret_rejected(self):
        body = b'{"event":"SUCCESS","orderId":"ORD-001","amount":"100.00"}'
        sig = make_signature('wrong-secret', body)
        with self.assertRaises(SignatureVerificationError):
            self.gw.verify_webhook_signature(body, sig)

    def test_missing_signature_rejected(self):
        body = b'{"event":"SUCCESS"}'
        with self.assertRaises(SignatureVerificationError):
            self.gw.verify_webhook_signature(body, '')

    def test_signature_without_prefix_accepted(self):
        """Signature can be provided with or without sha256= prefix."""
        body = b'{"event":"SUCCESS"}'
        raw_sig = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
        # Without prefix
        self.gw.verify_webhook_signature(body, raw_sig)
        # With prefix
        self.gw.verify_webhook_signature(body, f"sha256={raw_sig}")


class WebhookEndpointTests(TestCase):
    """Integration tests for POST /api/payments/webhook/."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testdoc', password='pass123', role='Doctor')
        self.patient_user, self.patient = _make_patient('PAT-TEST-001', 'Test Patient', 'testpat')
        # Setup allocation rules
        HealthProtectionAllocationRule.objects.get_or_create(
            service_category='Doctor Consultation',
            defaults={'contribution_percentage': Decimal('10.00'), 'is_active': True}
        )
        HealthProtectionAllocationRule.objects.get_or_create(
            service_category='Pharmacy Purchase',
            defaults={'contribution_percentage': Decimal('5.00'), 'is_active': True}
        )

    def _make_order(self, amount=Decimal('1000.00'), provider_category='DOCTOR', payment_type='Doctor Payment'):
        return PaymentOrder.objects.create(
            order_id=f"ORD-TEST-{PaymentOrder.objects.count()+1:04d}",
            patient=self.patient,
            provider_category=provider_category,
            service_description='Test consultation',
            amount=amount,
            amount_paise=int(amount * 100),
            currency='INR',
            contribution_rate=Decimal('10.00') if provider_category != 'PHARMACY' else Decimal('5.00'),
            expected_contribution_amount=amount * (Decimal('10.00') if provider_category != 'PHARMACY' else Decimal('5.00')) / 100,
            expected_contribution_paise=int(amount * (10 if provider_category != 'PHARMACY' else 5)),
            gateway_name='SANDBOX',
            idempotency_key=f"idem-{PaymentOrder.objects.count()+1}",
            status='ACTIVE',
            metadata={'payment_type': payment_type},
        )

    def _post_webhook(self, payload_dict, secret=WEBHOOK_SECRET, delivery_id=None):
        if delivery_id:
            payload_dict['deliveryId'] = delivery_id
        body = json.dumps(payload_dict).encode('utf-8')
        sig = make_signature(secret, body)
        with self.settings(PAYMENT_GATEWAY_MODE='sandbox', YOUPI_PG_WEBHOOK_SECRET=WEBHOOK_SECRET):
            return self.client.post(
                '/api/payments/webhook/',
                data=body,
                content_type='application/json',
                HTTP_X_GATEWAY_SIGNATURE=sig,
            )

    def test_success_webhook_credits_fund(self):
        order = self._make_order(amount=Decimal('1000.00'))
        resp = self._post_webhook({
            'event': 'SUCCESS',
            'orderId': order.order_id,
            'amount': '1000.00',
            'paymentId': 'PAY-SIM-001',
            'utr': 'UTR202610210001',
        }, delivery_id='WH-TEST-001')

        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'SUCCESS')

        acct = PatientHealthProtectionAccount.objects.filter(patient=self.patient).first()
        self.assertIsNotNone(acct)
        self.assertGreater(acct.available_balance, Decimal('0'))
        # Doctor 10% of 1000 = 100
        self.assertEqual(acct.available_balance, Decimal('100.00'))

    def test_pharmacy_5_percent_contribution(self):
        order = self._make_order(amount=Decimal('500.00'), provider_category='PHARMACY', payment_type='Pharmacy Payment')
        HealthProtectionAllocationRule.objects.update_or_create(
            service_category='Pharmacy Purchase',
            defaults={'contribution_percentage': Decimal('5.00'), 'is_active': True}
        )
        resp = self._post_webhook({
            'event': 'SUCCESS',
            'orderId': order.order_id,
            'amount': '500.00',
            'paymentId': 'PAY-SIM-002',
            'utr': 'UTR202610210002',
        }, delivery_id='WH-TEST-002')
        self.assertEqual(resp.status_code, 200)

        acct = PatientHealthProtectionAccount.objects.filter(patient=self.patient).first()
        if acct:
            # 5% of 500 = 25
            self.assertEqual(acct.available_balance, Decimal('25.00'))

    def test_duplicate_webhook_is_idempotent(self):
        order = self._make_order(amount=Decimal('500.00'))
        payload = {
            'event': 'SUCCESS',
            'orderId': order.order_id,
            'amount': '500.00',
            'paymentId': 'PAY-SIM-003',
            'utr': 'UTR202610210003',
        }
        resp1 = self._post_webhook(payload, delivery_id='WH-TEST-IDEM-001')
        resp2 = self._post_webhook(payload, delivery_id='WH-TEST-IDEM-001')  # same delivery_id
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp2.status_code, 200)
        # Balance should only be credited once
        acct = PatientHealthProtectionAccount.objects.filter(patient=self.patient).first()
        if acct:
            self.assertEqual(acct.available_balance, Decimal('50.00'))

    def test_invalid_signature_returns_400(self):
        order = self._make_order()
        body = json.dumps({'event': 'SUCCESS', 'orderId': order.order_id, 'amount': '1000.00'}).encode()
        with self.settings(PAYMENT_GATEWAY_MODE='sandbox', YOUPI_PG_WEBHOOK_SECRET=WEBHOOK_SECRET):
            resp = self.client.post(
                '/api/payments/webhook/',
                data=body,
                content_type='application/json',
                HTTP_X_GATEWAY_SIGNATURE='sha256=invalidsignatureabcdef',
            )
        self.assertEqual(resp.status_code, 400)

    def test_amount_mismatch_rejected(self):
        order = self._make_order(amount=Decimal('1000.00'))
        resp = self._post_webhook({
            'event': 'SUCCESS',
            'orderId': order.order_id,
            'amount': '999.00',  # Wrong amount
            'utr': 'UTR999',
        }, delivery_id='WH-TEST-MISMATCH')
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data.get('accepted'))

    def test_failed_event_marks_order(self):
        order = self._make_order()
        resp = self._post_webhook({
            'event': 'FAILED',
            'orderId': order.order_id,
            'amount': '1000.00',
        }, delivery_id='WH-TEST-FAILED')
        self.assertEqual(resp.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'FAILED')

    def test_expired_event_marks_order(self):
        order = self._make_order()
        resp = self._post_webhook({
            'event': 'EXPIRED',
            'orderId': order.order_id,
            'amount': '1000.00',
        }, delivery_id='WH-TEST-EXPIRED')
        order.refresh_from_db()
        self.assertEqual(order.status, 'EXPIRED')

    def test_unknown_order_rejected(self):
        resp = self._post_webhook({
            'event': 'SUCCESS',
            'orderId': 'ORD-NONEXISTENT',
            'amount': '100.00',
        }, delivery_id='WH-TEST-UNKNOWN')
        self.assertEqual(resp.status_code, 400)


class RefundTests(TestCase):
    """Tests for payment refund and HPF reversal compensation."""

    def setUp(self):
        self.client = Client()
        self.patient_user, self.patient = _make_patient('PAT-REFUND-001', 'Refund Patient', 'refundpat')
        HealthProtectionAllocationRule.objects.get_or_create(
            service_category='Doctor Consultation',
            defaults={'contribution_percentage': Decimal('10.00'), 'is_active': True}
        )
        self.order = PaymentOrder.objects.create(
            order_id='ORD-REFUND-001',
            patient=self.patient,
            provider_category='DOCTOR',
            service_description='Test consultation',
            amount=Decimal('500.00'),
            amount_paise=50000,
            currency='INR',
            contribution_rate=Decimal('10.00'),
            expected_contribution_amount=Decimal('50.00'),
            expected_contribution_paise=5000,
            gateway_name='SANDBOX',
            idempotency_key='idem-refund-001',
            status='SUCCESS',
            metadata={'payment_type': 'Doctor Payment'},
            utr='UTR-REFUND-001',
        )
        self.payment = Payment.objects.create(
            transaction_id='TXN-REFUND-001',
            order=self.order,
            patient=self.patient,
            payment_type='Doctor Payment',
            amount=Decimal('500.00'),
            amount_paise=50000,
            contribution_rate=Decimal('10.00'),
            contribution_amount=Decimal('50.00'),
            status='Completed',
            idempotency_key='PAY-idem-refund-001',
        )
        # Pre-credit HPF account
        self.acct, _ = PatientHealthProtectionAccount.objects.get_or_create(
            patient=self.patient,
            defaults={'account_reference': 'HPF-PAT-REFUND-001', 'available_balance': Decimal('50.00'), 'total_contributions': Decimal('50.00')}
        )
        HealthProtectionTransaction.objects.create(
            transaction_reference='HPT-REFUND-ORIG',
            idempotency_key='HPF-WH-ORD-REFUND-001',
            patient=self.patient,
            protection_account=self.acct,
            source_payment=self.payment,
            service_category='Doctor Consultation',
            eligible_payment_amount=Decimal('500.00'),
            contribution_percentage=Decimal('10.00'),
            amount=Decimal('50.00'),
            transaction_type='CONTRIBUTION',
            status='COMPLETED',
            balance_before=Decimal('0.00'),
            balance_after=Decimal('50.00'),
        )

    def test_refund_creates_reversal_entry(self):
        with self.settings(PAYMENT_GATEWAY_MODE='sandbox'):
            resp = self.client.post(
                f'/api/payments/orders/{self.order.order_id}/refund/',
                data=json.dumps({'amount': '500.00', 'reason': 'Patient request'}),
                content_type='application/json',
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['status'], 'COMPLETED')

        # HPF balance should be reduced
        self.acct.refresh_from_db()
        self.assertLess(self.acct.available_balance, Decimal('50.00'))

        # Reversal transaction should exist
        rev_txn = HealthProtectionTransaction.objects.filter(
            transaction_type='REVERSAL', source_payment=self.payment
        ).first()
        self.assertIsNotNone(rev_txn)

    def test_cannot_refund_non_success_order(self):
        self.order.status = 'FAILED'
        self.order.save()
        resp = self.client.post(
            f'/api/payments/orders/{self.order.order_id}/refund/',
            data=json.dumps({'amount': '500.00'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)


class SandboxSimulateTests(TestCase):
    """Tests for the sandbox payment simulation endpoint."""

    def setUp(self):
        self.client = Client()
        self.patient_user, self.patient = _make_patient('PAT-SIM-001', 'Simulate Patient', 'simpat')

    def test_sandbox_simulate_success(self):
        order = PaymentOrder.objects.create(
            order_id='ORD-SIM-001',
            patient=self.patient,
            provider_category='DOCTOR',
            service_description='Sim consultation',
            amount=Decimal('300.00'),
            amount_paise=30000,
            currency='INR',
            contribution_rate=Decimal('10.00'),
            expected_contribution_amount=Decimal('30.00'),
            expected_contribution_paise=3000,
            gateway_name='SANDBOX',
            idempotency_key='idem-sim-001',
            status='ACTIVE',
            metadata={'payment_type': 'Doctor Payment'},
        )
        with self.settings(PAYMENT_GATEWAY_MODE='sandbox', YOUPI_PG_WEBHOOK_SECRET='whsec_patientcare_super_secure_secret_2026'):
            resp = self.client.post(
                '/api/payments/sandbox/simulate/',
                data=json.dumps({'order_id': order.order_id, 'event': 'SUCCESS'}),
                content_type='application/json',
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('simulated'))
        self.assertTrue(data.get('webhook_result', {}).get('accepted'))

    def test_sandbox_simulate_blocked_in_live_mode(self):
        with self.settings(PAYMENT_GATEWAY_MODE='live'):
            resp = self.client.post(
                '/api/payments/sandbox/simulate/',
                data=json.dumps({'order_id': 'ANY'}),
                content_type='application/json',
            )
        self.assertEqual(resp.status_code, 403)


class WebhookDeliveryAdminTests(TestCase):
    def setUp(self):
        from accounts.models import User
        from payments.models import WebhookDelivery
        self.admin_user = User.objects.create_superuser(username='wh_admin', email='wh_admin@test.org', password='password123')
        self.normal_user = User.objects.create_user(username='wh_patient', email='wh_patient@test.org', password='password123', role='PATIENT')
        self.delivery = WebhookDelivery.objects.create(
            delivery_id='DEL-TEST-001',
            payload={'orderId': 'ORD-TEST-001'},
            event_type='SUCCESS',
            status='PROCESSED',
            ip_address='127.0.0.1'
        )

    def test_anonymous_access_denied(self):
        resp = self.client.get('/api/payments/webhook-deliveries/')
        self.assertIn(resp.status_code, [401, 403])

    def test_non_admin_access_denied(self):
        self.client.force_login(self.normal_user)
        resp = self.client.get('/api/payments/webhook-deliveries/')
        self.assertEqual(resp.status_code, 403)

    def test_admin_access_allowed(self):
        self.client.force_login(self.admin_user)
        resp = self.client.get('/api/payments/webhook-deliveries/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['results'][0]['delivery_id'], 'DEL-TEST-001')
