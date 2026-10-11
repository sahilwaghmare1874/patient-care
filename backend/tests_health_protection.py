"""
PatientCare Platform — Comprehensive Health Protection Fund & Doctor Recommendation Tests
Tests covering:
- 10% automatic credit calculation on completed eligible payments (Doctor, Pathology, Pharmacy)
- Payment idempotency and double-credit prevention
- Failed/Pending payment isolation (0% credit)
- Reversal and refund ledger consistency
- Claim workflow (submission, balance validation, approval, settlement/payout)
- Doctor recommendation engine (specialty matching, real doctor profile ranking, emergency red-flags)
"""

from django.test import TestCase
from rest_framework.test import APIClient
from decimal import Decimal
import json

from accounts.models import User, DoctorProfile
from patients.models import Patient
from payments.models import Payment
from funds.models import (
    PatientHealthProtectionAccount,
    HealthProtectionTransaction,
    HealthProtectionClaim,
    HealthProtectionAllocationRule,
)
from funds.services import (
    credit_health_protection_fund,
    reverse_health_protection_fund,
    settle_health_protection_claim,
    get_or_create_protection_account,
)


class HealthProtectionFundComprehensiveTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test patient
        self.user = User.objects.create_user(
            username='hpf_test_user',
            password='TestPassword@123',
            role='PATIENT'
        )
        self.patient = Patient.objects.create(
            user=self.user,
            patient_id='PAT-2026-TEST01',
            hac_number='HAC-91-998877665544',
            full_name='Aarav Shinde',
            dob='1992-04-15',
            gender='Male',
            mobile='9822001122',
            email='aarav.shinde@example.com',
            address='102 Shiv Road',
            city='Pune',
            district='Pune',
            state='Maharashtra',
            pincode='411001',
            pan_number='ABCDE1234F',
            blood_group='O+'
        )

        # Create approved doctor
        self.doc_user = User.objects.create_user(
            username='dr_patil',
            password='DocPassword@123',
            role='DOCTOR'
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            doctor_id='DOC-2026-TEST01',
            full_name='Dr. Rajesh Patil, MD',
            qualification='MD (Cardiology)',
            specialization='Cardiology',
            registration_number='MCI-998811',
            experience_years=14,
            hospital_name='Pune Heart Institute',
            address='Deccan Gymkhana, Pune',
            contact_number='9822334455',
            email='dr.patil@example.com',
            is_approved=True
        )

    def test_01_doctor_payment_triggers_10_percent_credit(self):
        """Completed payment for Doctor Consultation credits exact 10% to HealthProtectionAccount."""
        payload = {
            'patient_id': self.patient.patient_id,
            'payment_type': 'Doctor Payment',
            'amount': '1000.00',
            'service_description': 'Consultation with Cardiologist',
            'provider_id': self.doctor.doctor_id
        }
        res = self.client.post('/api/payments/', data=payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertIn('health_protection_contribution', res.data)

        contrib = res.data['health_protection_contribution']
        self.assertTrue(contrib['credited'])
        self.assertEqual(Decimal(str(contrib['credit_amount'])), Decimal('100.00'))

        # Verify database account and ledger
        account = PatientHealthProtectionAccount.objects.get(patient=self.patient)
        self.assertEqual(account.available_balance, Decimal('100.00'))
        self.assertEqual(account.total_contributions, Decimal('100.00'))

        txn = HealthProtectionTransaction.objects.get(patient=self.patient)
        self.assertEqual(txn.amount, Decimal('100.00'))
        self.assertEqual(txn.contribution_percentage, Decimal('10.00'))
        self.assertEqual(txn.transaction_type, 'CONTRIBUTION')
        self.assertEqual(txn.status, 'COMPLETED')

    def test_02_failed_payment_no_fund_credit(self):
        """Payments with status != 'Completed' do NOT trigger fund credits."""
        account = get_or_create_protection_account(self.patient)
        initial_balance = account.available_balance

        payment = Payment.objects.create(
            transaction_id='TXN-TEST-FAILED-01',
            patient=self.patient,
            payment_type='Doctor Payment',
            amount=Decimal('800.00'),
            gst_amount=Decimal('0.00'),
            payment_method='UPI',
            status='Failed'
        )

        with self.assertRaises(ValueError):
            credit_health_protection_fund(
                payment=payment,
                patient=self.patient,
                service_category='Doctor Consultation',
                idempotency_key='TXN-TEST-FAILED-01'
            )

        account.refresh_from_db()
        self.assertEqual(account.available_balance, initial_balance)

    def test_03_idempotency_prevents_duplicate_credit(self):
        """Calling credit with identical idempotency_key returns is_duplicate and preserves balance."""
        payment = Payment.objects.create(
            transaction_id='TXN-TEST-IDEM-01',
            patient=self.patient,
            payment_type='Doctor Payment',
            amount=Decimal('500.00'),
            gst_amount=Decimal('0.00'),
            payment_method='NetBanking',
            status='Completed'
        )

        res1 = credit_health_protection_fund(
            payment=payment,
            patient=self.patient,
            service_category='Doctor Consultation',
            idempotency_key='IDEM-KEY-UNIQUE-99'
        )
        self.assertFalse(res1['is_duplicate'])
        self.assertEqual(res1['credit_amount'], Decimal('50.00'))

        # Duplicate attempt with identical key
        res2 = credit_health_protection_fund(
            payment=payment,
            patient=self.patient,
            service_category='Doctor Consultation',
            idempotency_key='IDEM-KEY-UNIQUE-99'
        )
        self.assertTrue(res2['is_duplicate'])

        # Confirm account balance is ₹50 (10% of 500), NOT ₹100
        account = PatientHealthProtectionAccount.objects.get(patient=self.patient)
        self.assertEqual(account.available_balance, Decimal('50.00'))
        self.assertEqual(HealthProtectionTransaction.objects.filter(patient=self.patient).count(), 1)

    def test_04_reversal_decrements_balance(self):
        """Reversing a payment creates an immutable REVERSAL transaction and decreases available balance."""
        payment = Payment.objects.create(
            transaction_id='TXN-TEST-REV-01',
            patient=self.patient,
            payment_type='Pathology Payment',
            amount=Decimal('1200.00'),
            gst_amount=Decimal('0.00'),
            payment_method='Card',
            status='Completed'
        )

        # Credit 10% (₹120)
        credit_health_protection_fund(
            payment=payment,
            patient=self.patient,
            service_category='Pathology Diagnostic',
            idempotency_key=payment.transaction_id
        )

        account = PatientHealthProtectionAccount.objects.get(patient=self.patient)
        self.assertEqual(account.available_balance, Decimal('120.00'))

        # Reverse payment
        rev_result = reverse_health_protection_fund(
            payment=payment,
            reason='Customer requested full refund for cancelled diagnostic test'
        )
        self.assertTrue(rev_result['reversed'])

        account.refresh_from_db()
        self.assertEqual(account.available_balance, Decimal('0.00'))
        self.assertEqual(account.total_reversals, Decimal('120.00'))

        reversal_txns = HealthProtectionTransaction.objects.filter(
            patient=self.patient,
            transaction_type='REVERSAL'
        )
        self.assertEqual(reversal_txns.count(), 1)
        self.assertEqual(reversal_txns.first().amount, Decimal('120.00'))

    def test_05_claim_submission_and_settlement(self):
        """Test claim lifecycle: submission within balance, approval, and settlement."""
        account = get_or_create_protection_account(self.patient)
        # Seed balance with a completed payment (₹2000 payment -> ₹200 fund)
        payment = Payment.objects.create(
            transaction_id='TXN-SEED-CLAIM-01',
            patient=self.patient,
            payment_type='Doctor Payment',
            amount=Decimal('2000.00'),
            gst_amount=Decimal('0.00'),
            status='Completed'
        )
        credit_health_protection_fund(
            payment=payment,
            patient=self.patient,
            service_category='Doctor Consultation',
            idempotency_key=payment.transaction_id
        )
        account.refresh_from_db()
        self.assertEqual(account.available_balance, Decimal('200.00'))

        # 1. Submitting claim exceeding balance returns 400
        res_fail = self.client.post('/api/funds/claims/', data={
            'patient_id': self.patient.patient_id,
            'expense_category': 'Prescription Medicines',
            'requested_amount': '300.00',
            'provider_name': 'Care Chemist'
        }, format='json')
        self.assertEqual(res_fail.status_code, 400)

        # 2. Submitting valid claim within balance returns 201
        res_ok = self.client.post('/api/funds/claims/', data={
            'patient_id': self.patient.patient_id,
            'expense_category': 'Prescription Medicines',
            'requested_amount': '150.00',
            'provider_name': 'Care Chemist',
            'description': 'Post-op cardiac medicines'
        }, format='json')
        self.assertEqual(res_ok.status_code, 201)
        claim_ref = res_ok.data['claim']['claim_reference']

        # 3. Settle / Pay the claim
        claim = HealthProtectionClaim.objects.get(claim_reference=claim_ref)
        settle_result = settle_health_protection_claim(claim, approved_amount=Decimal('150.00'))
        self.assertEqual(settle_result['claim'].status, 'PAID')
        self.assertEqual(settle_result['remaining_balance'], Decimal('50.00'))

        claim.refresh_from_db()
        self.assertEqual(claim.status, 'PAID')
        self.assertEqual(claim.approved_amount, Decimal('150.00'))

        account.refresh_from_db()
        self.assertEqual(account.available_balance, Decimal('50.00'))
        self.assertEqual(account.total_approved_withdrawals, Decimal('150.00'))

    def test_06_doctor_recommendations_matching(self):
        """Querying recommendations returns actual approved doctors matching specialty."""
        res = self.client.post('/api/doctors/recommendations/', data={
            'symptoms': 'heart palpitations, mild chest flutter',
            'health_concern': 'High blood pressure and pulse',
            'language': 'en'
        }, format='json')

        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.data['is_urgent'])
        self.assertIn('doctors', res.data)
        self.assertGreater(len(res.data['doctors']), 0)

        first_doc = res.data['doctors'][0]
        self.assertEqual(first_doc['doctor_id'], self.doctor.doctor_id)
        self.assertEqual(first_doc['specialization'], 'Cardiology')
        self.assertTrue(first_doc['is_approved'])
        self.assertIn('why_recommended', first_doc)

    def test_07_emergency_red_flags_triggers_urgent_care(self):
        """Red-flag emergency symptoms immediately return urgent care instructions."""
        res = self.client.post('/api/doctors/recommendations/', data={
            'symptoms': 'severe crushing chest pain and breathing difficulty',
            'health_concern': 'Sudden onset',
            'language': 'en'
        }, format='json')

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['is_urgent'])
        self.assertIn('urgent_message', res.data)
        self.assertIn('108', res.data['urgent_message'])
        self.assertEqual(len(res.data['doctors']), 0)
