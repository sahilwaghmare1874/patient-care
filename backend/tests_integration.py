from django.test import TestCase
from rest_framework.test import APIClient
from decimal import Decimal
import json

from accounts.models import User, DoctorProfile, PathologyProfile, PharmacyProfile
from patients.models import Patient
from funds.models import AllocationConfiguration, FundAllocation
from government.models import GovernmentScheme

class HealthcareSystemIntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed allocation configuration rule
        self.config = AllocationConfiguration.objects.create(
            name="Standard Test Rule",
            doctor_percentage=Decimal('10.00'),
            pathology_percentage=Decimal('10.00'),
            pharmacy_percentage=Decimal('5.00'),
            government_percentage=Decimal('5.00'),
            patient_benefit_percentage=Decimal('70.00'),
            is_active=True
        )

    def test_01_patient_registration_and_pan_deduplication(self):
        """Test Step 2-5: Patient registration, sequential ID generation, and duplicate PAN prevention"""
        # Register new patient
        payload = {
            "full_name": "Kunal Joshi",
            "dob": "1995-04-12",
            "gender": "Male",
            "mobile": "9812345678",
            "email": "kunal.joshi@example.com",
            "address": "12 Shivneri Path, Deccan",
            "city": "Pune",
            "district": "Pune",
            "state": "Maharashtra",
            "pincode": "411004",
            "pan_number": "ABCDE9999Z",
            "blood_group": "O+",
            "emergency_contact_name": "Anil Joshi",
            "emergency_contact_phone": "9812345670",
            "username": "kunal_user",
            "password": "patient_password_123"
        }

        resp = self.client.post('/api/patients/', data=payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertFalse(resp.data['is_existing'])
        created_id = resp.data['patient']['patient_id']
        self.assertTrue(created_id.startswith('PAT-2026-'))
        self.assertEqual(resp.data['patient']['pan_number'], 'XXXXX9999X') # Masked

        # Attempt to register AGAIN with the EXACT SAME PAN
        dup_payload = payload.copy()
        dup_payload['full_name'] = "Duplicate Attempt"
        dup_payload['username'] = "different_user"
        dup_resp = self.client.post('/api/patients/', data=dup_payload, format='json')
        self.assertEqual(dup_resp.status_code, 200)
        self.assertTrue(dup_resp.data['is_existing'])
        self.assertEqual(dup_resp.data['patient']['patient_id'], created_id)
        self.assertIn("already exists", dup_resp.data['message'])

    def test_02_doctor_consultation_and_prescription(self):
        """Test Step 6-10: Doctor creates diagnosis, treatment, and electronic prescription"""
        patient = Patient.objects.create(
            patient_id="PAT-2026-000099",
            hac_number="HAC-91-1111-2222-2026",
            full_name="Sunil Patil",
            dob="1992-01-01",
            gender="Male",
            mobile="9822334411",
            address="Camp, Pune",
            city="Pune",
            district="Pune",
            state="Maharashtra",
            pincode="411001",
            pan_number="XYZAB1234K",
            blood_group="B+",
            emergency_contact_name="Sunita Patil",
            emergency_contact_phone="9822334400"
        )

        doc_user = User.objects.create_user(username='doc_test', role='DOCTOR')
        doctor = DoctorProfile.objects.create(
            user=doc_user,
            doctor_id="DOC-2026-0099",
            full_name="Dr. Vikram Sen",
            qualification="MBBS, MS",
            specialization="General Surgery",
            registration_number="REG-DOC-99",
            hospital_name="City General Hospital",
            contact_number="9822114400",
            email="dr.vikram@cityhospital.org",
            address="Hospital Road",
            is_approved=True
        )

        consult_payload = {
            "patient_id": patient.patient_id,
            "doctor_id": doctor.doctor_id,
            "visit_date": "2026-10-07",
            "symptoms": "Acute abdominal discomfort and fever",
            "diagnosis": "Acute Appendicitis (Early Stage)",
            "doctor_notes": "Abdominal tenderness observed in right lower quadrant. Vitals stable.",
            "treatment_plan": "IV fluids, conservative antibiotics and surgical evaluation",
            "operation_recommended": True,
            "operation_details": "Laparoscopic Appendectomy Recommended",
            "pathology_referral": True,
            "pathology_tests_recommended": "Complete Blood Count & Abdominal Ultrasound",
            "prescribed_medicines": "1. Tab Cefixime 200mg BD x 5 days\n2. Tab Paracetamol 650mg SOS",
            "consultation_fee": 850.00
        }

        resp = self.client.post('/api/doctors/consultations/', data=consult_payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data['consultation']['consultation_id'].startswith('CON-2026-'))

        # Check prescription created
        rx_resp = self.client.get(f'/api/doctors/prescriptions/?patient_id={patient.patient_id}')
        self.assertEqual(rx_resp.status_code, 200)
        self.assertGreaterEqual(len(rx_resp.data), 1)

    def test_03_pathology_report_upload(self):
        """Test Step 11-15: Pathology test investigation and report verification"""
        patient = Patient.objects.create(
            patient_id="PAT-2026-000088",
            hac_number="HAC-91-3333-4444-2026",
            full_name="Geeta Rao",
            dob="1988-06-15",
            gender="Female",
            mobile="9822556677",
            address="Aundh, Pune",
            city="Pune",
            district="Pune",
            state="Maharashtra",
            pincode="411007",
            pan_number="QWERT5678L",
            blood_group="A+",
            emergency_contact_name="Ramesh Rao",
            emergency_contact_phone="9822556600"
        )

        lab_user = User.objects.create_user(username='lab_test', role='PATHOLOGY')
        lab = PathologyProfile.objects.create(
            user=lab_user,
            lab_id="LAB-2026-0099",
            lab_name="Metropolis Test Diagnostic",
            license_number="LIC-LAB-99",
            owner_name="Dr. Anil",
            contact_number="9833441122",
            email="lab@test.org",
            address="Deccan, Pune",
            is_approved=True
        )

        report_payload = {
            "patient_id": patient.patient_id,
            "lab_id": lab.lab_id,
            "test_name": "Complete Blood Count (CBC)",
            "test_category": "Hematology",
            "test_date": "2026-10-07",
            "test_cost": 850.00,
            "results_summary": "Hb: 13.8 g/dL, Total Leukocyte Count: 9,200 /mcL, Platelets: 2.10 Lakhs/mcL",
            "detailed_findings": "Normal differential count. Mild neutrophilia noted.",
            "status": "Verified"
        }

        resp = self.client.post('/api/pathology/reports/', data=report_payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['report']['status'], 'Verified')

    def test_04_fund_distribution_calculation_engine(self):
        """Test Step 16-27: Configurable fund distribution logic with precise calculations"""
        patient = Patient.objects.create(
            patient_id="PAT-2026-000077",
            hac_number="HAC-91-5555-6666-2026",
            full_name="Deepak Varma",
            dob="1985-03-20",
            gender="Male",
            mobile="9811223344",
            address="Baner, Pune",
            city="Pune",
            district="Pune",
            state="Maharashtra",
            pincode="411045",
            pan_number="LMNOP9876Q",
            blood_group="AB+",
            emergency_contact_name="Sunita Varma",
            emergency_contact_phone="9811223300"
        )

        # Approved treatment cost = ₹1,00,000; Gov fund = ₹80,000; Insurance = ₹20,000 -> Total = ₹1,00,000
        # Expected:
        # Doctor 10% = ₹10,000
        # Pathology 10% = ₹10,000
        # Pharmacy 5% = ₹5,000
        # Gov Admin 5% = ₹5,000
        # Patient Benefit 70% = ₹70,000
        alloc_payload = {
            "patient_id": patient.patient_id,
            "total_treatment_cost": 100000.00,
            "approved_government_fund": 80000.00,
            "approved_insurance_fund": 20000.00
        }

        resp = self.client.post('/api/funds/allocate/', data=alloc_payload, format='json')
        self.assertEqual(resp.status_code, 201)
        alloc = resp.data['allocation']

        self.assertEqual(float(alloc['total_approved_fund']), 100000.00)
        self.assertEqual(float(alloc['doctor_allocation']), 10000.00)
        self.assertEqual(float(alloc['pathology_allocation']), 10000.00)
        self.assertEqual(float(alloc['pharmacy_allocation']), 5000.00)
        self.assertEqual(float(alloc['government_allocation']), 5000.00)
        self.assertEqual(float(alloc['patient_benefit_amount']), 70000.00)
        self.assertEqual(float(alloc['patient_out_of_pocket']), 0.00)

    def test_05_centralized_report_and_pdf_export(self):
        """Test Step 27-28: Centralized report generation and PDF report download"""
        patient = Patient.objects.create(
            patient_id="PAT-2026-000066",
            hac_number="HAC-91-7777-8888-2026",
            full_name="Meera Joshi",
            dob="1999-11-11",
            gender="Female",
            mobile="9833669922",
            address="Kothrud, Pune",
            city="Pune",
            district="Pune",
            state="Maharashtra",
            pincode="411038",
            pan_number="POIUY1234T",
            blood_group="O-",
            emergency_contact_name="Vinay Joshi",
            emergency_contact_phone="9833669900"
        )

        # JSON Centralized Report
        rep_resp = self.client.get(f'/api/reports/patient/{patient.patient_id}/')
        self.assertEqual(rep_resp.status_code, 200)
        self.assertEqual(rep_resp.data['patient']['patient_id'], patient.patient_id)

        # PDF Download Response
        pdf_resp = self.client.get(f'/api/reports/pdf/{patient.patient_id}/')
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp['Content-Type'], 'application/pdf')
        self.assertTrue(len(pdf_resp.content) > 1000)

        # CSV Download Response
        csv_resp = self.client.get(f'/api/reports/csv/{patient.patient_id}/')
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp['Content-Type'], 'text/csv')
        self.assertIn("HEALTHCARE INSURANCE ASSURANCE", csv_resp.content.decode('utf-8'))

    def test_06_ai_symptom_and_urgent_care(self):
        """Phase 3 & 7: Test AI symptom recommendation, specialty matching, and red-flag emergency advice"""
        # Test normal symptom
        resp = self.client.post('/api/doctors/ai/recommend/', data={'symptoms': 'severe headache and dizziness', 'language': 'en'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['is_urgent'])
        self.assertEqual(resp.data['recommended_specialty'], 'Neurology')
        self.assertIn('AI-assisted suggestion only', resp.data['disclaimer'])

        # Test red-flag emergency symptom
        red_resp = self.client.post('/api/doctors/ai/recommend/', data={'symptoms': 'severe chest pain with difficulty breathing', 'language': 'en'}, format='json')
        self.assertEqual(red_resp.status_code, 200)
        self.assertTrue(red_resp.data['is_urgent'])
        self.assertIn('108', red_resp.data['urgent_message'])
        self.assertEqual(red_resp.data['recommended_specialty'], 'Emergency Medicine')

    def test_07_appointment_booking_and_atomic_token(self):
        """Phase 3 & 4: Test atomic appointment booking and unique sequential token generation"""
        patient = Patient.objects.create(
            patient_id="PAT-2026-TEST01",
            hac_number="HAC-91-TEST-0001-2026",
            full_name="Rajiv Kale",
            dob="1990-05-15",
            gender="Male",
            mobile="9822001122",
            address="Shivajinagar, Pune",
            city="Pune",
            district="Pune",
            state="Maharashtra",
            pincode="411005",
            pan_number="ABCDE5555K",
            blood_group="A+",
            emergency_contact_name="Rekha Kale",
            emergency_contact_phone="9822001120"
        )

        doc_user = User.objects.create_user(username='doc_token_test', role='DOCTOR')
        doctor = DoctorProfile.objects.create(
            user=doc_user,
            doctor_id="DOC-2026-TOK01",
            full_name="Dr. Alok Verma",
            qualification="MBBS, MD",
            specialization="Cardiology",
            registration_number="REG-CARD-01",
            hospital_name="Heart Care Hospital",
            contact_number="9811002233",
            email="dr.alok@heartcare.org",
            address="FC Road, Pune",
            is_approved=True
        )

        appt_payload = {
            "patient_id": patient.patient_id,
            "doctor_id": doctor.doctor_id,
            "appointment_date": "2026-10-15",
            "time_slot": "10:00 AM - 10:30 AM",
            "symptoms": "High BP follow-up",
            "idempotency_key": "idemp-test-token-01"
        }

        # Booking #1 -> Token #1
        resp1 = self.client.post('/api/doctors/appointments/', data=appt_payload, format='json')
        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp1.data['appointment']['token']['token_number'], 1)
        self.assertEqual(resp1.data['appointment']['token']['status'], 'Waiting')

        # Idempotency duplicate check with same key
        dup_resp = self.client.post('/api/doctors/appointments/', data=appt_payload, format='json')
        self.assertEqual(dup_resp.status_code, 200)
        self.assertIn("already booked", dup_resp.data['message'])

        # Booking #2 for same doctor & session date -> Token #2 (Atomic increment)
        appt_payload2 = appt_payload.copy()
        appt_payload2['idempotency_key'] = "idemp-test-token-02"
        appt_payload2['symptoms'] = "Second booking test"
        resp2 = self.client.post('/api/doctors/appointments/', data=appt_payload2, format='json')
        self.assertEqual(resp2.status_code, 201)
        self.assertEqual(resp2.data['appointment']['token']['token_number'], 2)

    def test_08_queue_calling_controls(self):
        """Phase 4: Test Doctor queue status and calling next patient controls"""
        patient = Patient.objects.create(
            patient_id="PAT-2026-QUEUE01",
            hac_number="HAC-91-QUEU-0001-2026",
            full_name="Asha Shinde",
            dob="1988-08-20",
            gender="Female",
            mobile="9833445566",
            address="Kothrud, Pune",
            city="Pune",
            district="Pune",
            state="Maharashtra",
            pincode="411038",
            pan_number="KLMNO6666P",
            blood_group="O-",
            emergency_contact_name="Dilip Shinde",
            emergency_contact_phone="9833445500"
        )
        doctor = DoctorProfile.objects.filter(is_approved=True).first()
        if not doctor:
            doc_user = User.objects.create_user(username='doc_q_test', role='DOCTOR')
            doctor = DoctorProfile.objects.create(
                user=doc_user,
                doctor_id="DOC-2026-Q01",
                full_name="Dr. Queue Test",
                qualification="MBBS",
                specialization="General Medicine",
                registration_number="REG-Q-01",
                hospital_name="Apex Hospital",
                contact_number="9877665544",
                email="q@hospital.org",
                address="Camp",
                is_approved=True
            )

        # Book an appointment
        self.client.post('/api/doctors/appointments/', data={
            "patient_id": patient.patient_id,
            "doctor_id": doctor.doctor_id,
            "appointment_date": "2026-10-20",
            "time_slot": "11:00 AM",
            "symptoms": "Fever check"
        }, format='json')

        # Check queue
        q_resp = self.client.get(f'/api/doctors/queue/?doctor_id={doctor.doctor_id}&date=2026-10-20')
        self.assertEqual(q_resp.status_code, 200)
        self.assertEqual(q_resp.data['total_tokens'], 1)
        self.assertEqual(q_resp.data['waiting_count'], 1)

        # Doctor calls next token
        call_resp = self.client.post('/api/doctors/queue/call-next/', data={
            "doctor_id": doctor.doctor_id,
            "date": "2026-10-20",
            "action": "call"
        }, format='json')
        self.assertEqual(call_resp.status_code, 200)
        self.assertEqual(call_resp.data['status'], 'In Consultation')

    def test_09_reserve_account_and_ledger_credit(self):
        """Phase 8: Test 90% Healthcare Reserve credit, immutable ledger, and balance tracking"""
        patient = Patient.objects.create(
            patient_id="PAT-2026-RES01",
            hac_number="HAC-91-RESV-0001-2026",
            full_name="Ganesh Jadhav",
            dob="1985-03-25",
            gender="Male",
            mobile="9899887766",
            address="Hadapsar, Pune",
            city="Pune",
            district="Pune",
            state="Maharashtra",
            pincode="411028",
            pan_number="PQRST7777W",
            blood_group="AB+",
            emergency_contact_name="Maya Jadhav",
            emergency_contact_phone="9899887700"
        )

        # Record 90% reserve credit on ₹1,000 doctor consultation fee
        credit_payload = {
            "patient_id": patient.patient_id,
            "service_type": "Doctor Consultation",
            "reference_id": "CON-2026-0001",
            "invoice_amount": 1000.00,
            "idempotency_key": "resv-idemp-01"
        }
        res = self.client.post('/api/funds/reserve/credit/', data=credit_payload, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['credit_amount'], 900.00) # 90% of 1000
        self.assertEqual(res.data['balance_after'], 900.00)

        # Idempotency check: repeated submission does not double credit
        dup_res = self.client.post('/api/funds/reserve/credit/', data=credit_payload, format='json')
        self.assertEqual(dup_res.status_code, 200)
        self.assertIn("already recorded", dup_res.data['message'])

        # Retrieve reserve account and verify ledger
        acct_res = self.client.get(f'/api/funds/reserve/{patient.patient_id}/')
        self.assertEqual(acct_res.status_code, 200)
        self.assertEqual(acct_res.data['available_balance'], 900.00)
        self.assertEqual(acct_res.data['reserve_percentage'], 90.0)

        ledger_res = self.client.get(f'/api/funds/reserve/{patient.patient_id}/ledger/')
        self.assertEqual(ledger_res.status_code, 200)
        self.assertEqual(ledger_res.data['total_entries'], 1)
        self.assertEqual(ledger_res.data['entries'][0]['entry_type'], 'CREDIT')

    def test_10_government_scheme_application(self):
        """Phase 6: Test Government scheme application submission and pre-authorization review"""
        patient = Patient.objects.create(
            patient_id="PAT-2026-SCH01",
            hac_number="HAC-91-SCHM-0001-2026",
            full_name="Lata Deshmukh",
            dob="1978-12-05",
            gender="Female",
            mobile="9844556677",
            address="Nagpur, Maharashtra",
            city="Nagpur",
            district="Nagpur",
            state="Maharashtra",
            pincode="440001",
            pan_number="LMNOP8888D",
            blood_group="B-",
            emergency_contact_name="Ramesh Deshmukh",
            emergency_contact_phone="9844556600"
        )
        scheme = GovernmentScheme.objects.create(
            scheme_code="MJPJAY-TEST-01",
            scheme_name="Mahatma Jyotirao Phule Jan Arogya Yojana Test",
            description="Maharashtra Cashless Scheme",
            eligibility="Orange/Yellow Ration Card",
            maximum_fund=Decimal('500000.00'),
            start_date="2020-01-01",
            end_date="2030-12-31",
            status="Active"
        )

        # Submit Application
        app_res = self.client.post('/api/government/applications/', data={
            "patient_id": patient.patient_id,
            "scheme_code": scheme.scheme_code,
            "hospital_name": "Apex Multispeciality Nagpur",
            "treatment_description": "Cardiac Angioplasty",
            "estimated_cost": 150000.00,
            "requested_amount": 150000.00
        }, format='json')
        self.assertEqual(app_res.status_code, 201)
        app_id = app_res.data['application']['application_id']
        self.assertEqual(app_res.data['application']['status'], 'Submitted')

        # Update to Pre-Authorized
        update_res = self.client.post(f'/api/government/applications/{app_id}/', data={
            "status": "Pre-Authorized",
            "approved_amount": 150000.00,
            "officer_remarks": "Eligible under MJPJAY category A"
        }, format='json')
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.data['application']['status'], 'Pre-Authorized')

    def test_11_ai_chat_and_duplicate_claims(self):
        """Phase 7, 9 & 11: Test AI Multilingual Chatbot, Duplicate Claim Scanner, and Financial Reporting"""
        # AI Multilingual Chat
        chat_en = self.client.post('/api/reports/ai/chat/', data={'message': 'How does the health protection fund work?', 'language': 'en'}, format='json')
        self.assertEqual(chat_en.status_code, 200)
        self.assertIn('10%', chat_en.data['reply'])

        chat_hi = self.client.post('/api/reports/ai/chat/', data={'message': 'योजना के बारे में बताएं', 'language': 'hi'}, format='json')
        self.assertEqual(chat_hi.status_code, 200)
        self.assertIn('आयुष्मान भारत', chat_hi.data['reply'])

        # AI Duplicate Claim Detection
        audit_res = self.client.get('/api/reports/ai/audit-claims/')
        self.assertEqual(audit_res.status_code, 200)
        self.assertIn('status', audit_res.data)

        # Centralized Financial Overview
        fin_res = self.client.get('/api/reports/financial-overview/')
        self.assertEqual(fin_res.status_code, 200)
        self.assertIn('financial_summary', fin_res.data)
        self.assertIn('reserve_account_summary', fin_res.data['financial_summary'])


class HealthProtectionFundIntegrationTests(TestCase):
    """
    test_12: Verifies the complete end-to-end Health Protection Fund auto-credit flow:
    Payment creation → automatic 10% HPF credit → idempotency → receipt includes
    contribution → centralized financial overview includes HPF totals.
    """

    def setUp(self):
        from accounts.models import User
        self.client = APIClient()
        # Minimal patient — no linked user (AllowAny endpoints)
        self.patient = Patient.objects.create(
            patient_id="PAT-2026-HPF01",
            hac_number="HAC-91-HPF1-0001-2026",
            full_name="Anita Kulkarni",
            dob="1990-06-15",
            gender="Female",
            mobile="9876543210",
            address="Kothrud, Pune",
            city="Pune",
            district="Pune",
            state="Maharashtra",
            pincode="411038",
            pan_number="ANITK9876P",
            blood_group="A+",
            emergency_contact_name="Suresh Kulkarni",
            emergency_contact_phone="9876543200"
        )

    def test_12_payment_triggers_hpf_auto_credit(self):
        """Step 1: POST /api/payments/ → 10% credited to HPF → receipt reflects contribution."""
        from funds.models import PatientHealthProtectionAccount, HealthProtectionTransaction

        # 1. Create a Doctor Payment of ₹1000
        payload = {
            "patient_id": self.patient.patient_id,
            "payment_type": "Doctor Payment",
            "amount": "1000.00",
            "service_description": "Cardiology Consultation",
            "payment_method": "Assurance Benefit Wallet",
        }
        resp = self.client.post('/api/payments/', data=payload, format='json')
        self.assertEqual(resp.status_code, 201, msg=resp.data)

        # Response must include health_protection_contribution block
        self.assertIn('health_protection_contribution', resp.data)
        hpf_resp = resp.data['health_protection_contribution']
        self.assertTrue(hpf_resp['credited'])
        self.assertAlmostEqual(hpf_resp['credit_amount'], 100.0, places=2)  # 10% of 1000
        self.assertFalse(hpf_resp['is_duplicate'])

        txn_id = resp.data['payment']['transaction_id']

        # 2. Verify HPF account and ledger in DB
        account = PatientHealthProtectionAccount.objects.filter(patient=self.patient).first()
        self.assertIsNotNone(account)
        self.assertAlmostEqual(float(account.available_balance), 100.0, places=2)
        self.assertAlmostEqual(float(account.total_contributions), 100.0, places=2)

        hpf_txn = HealthProtectionTransaction.objects.filter(
            patient=self.patient,
            transaction_type='CONTRIBUTION',
            status='COMPLETED'
        ).first()
        self.assertIsNotNone(hpf_txn)
        self.assertAlmostEqual(float(hpf_txn.amount), 100.0, places=2)
        self.assertEqual(hpf_txn.service_category, 'Doctor Consultation')

        # 3. GET /api/payments/receipt/{transaction_id}/ → includes HPF contribution
        receipt_resp = self.client.get(f'/api/payments/receipt/{txn_id}/')
        self.assertEqual(receipt_resp.status_code, 200, msg=getattr(receipt_resp, 'data', receipt_resp.content))
        self.assertIn('health_protection_contribution', receipt_resp.data['receipt'])
        self.assertAlmostEqual(
            float(receipt_resp.data['receipt']['health_protection_contribution']),
            100.0, places=2
        )

    def test_12b_hpf_idempotency_no_double_credit(self):
        """Posting a second payment for same patient does NOT duplicate the first payment's HPF credit."""
        from funds.models import PatientHealthProtectionAccount, HealthProtectionTransaction
        from funds.services import credit_health_protection_fund
        from payments.models import Payment

        # Manually create a payment and credit it
        payment = Payment.objects.create(
            transaction_id="TXN-2026-IDEMP01",
            patient=self.patient,
            payment_type="Pathology Payment",
            amount=500,
            gst_amount=0,
            status='Completed'
        )
        result1 = credit_health_protection_fund(
            payment=payment,
            service_category='Pathology Diagnostic',
            idempotency_key="TXN-2026-IDEMP01"
        )
        self.assertFalse(result1['is_duplicate'])
        self.assertAlmostEqual(float(result1['credit_amount']), 50.0, places=2)  # 10% of 500

        # Calling again with the same idempotency key must NOT create a second credit
        result2 = credit_health_protection_fund(
            payment=payment,
            service_category='Pathology Diagnostic',
            idempotency_key="TXN-2026-IDEMP01"
        )
        self.assertTrue(result2['is_duplicate'])

        # Account balance must still be only ₹50, not ₹100
        account = PatientHealthProtectionAccount.objects.get(patient=self.patient)
        self.assertAlmostEqual(float(account.available_balance), 50.0, places=2)
        self.assertEqual(
            HealthProtectionTransaction.objects.filter(patient=self.patient, transaction_type='CONTRIBUTION').count(),
            1
        )

    def test_12c_pharmacy_payment_earns_hpf(self):
        """Pharmacy Payment (with 5% GST) still credits 10% HPF on base amount."""
        payload = {
            "patient_id": self.patient.patient_id,
            "payment_type": "Pharmacy Payment",
            "amount": "2000.00",
            "service_description": "Antibiotics and Supplements",
            "payment_method": "Assurance Benefit Wallet",
        }
        resp = self.client.post('/api/payments/', data=payload, format='json')
        self.assertEqual(resp.status_code, 201, msg=resp.data)

        self.assertIn('health_protection_contribution', resp.data)
        hpf_resp = resp.data['health_protection_contribution']
        self.assertTrue(hpf_resp['credited'])
        self.assertAlmostEqual(hpf_resp['credit_amount'], 200.0, places=2)  # 10% of 2000

        # GST should also have been applied (5% of 2000 = 100)
        self.assertAlmostEqual(
            float(resp.data['payment']['gst_amount']), 100.0, places=2
        )

    def test_12d_financial_overview_includes_hpf(self):
        """GET /api/reports/financial-overview/ includes health_protection_fund_summary."""
        resp = self.client.get('/api/reports/financial-overview/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('financial_summary', resp.data)
        self.assertIn('health_protection_fund_summary', resp.data['financial_summary'])
        hpf_summary = resp.data['financial_summary']['health_protection_fund_summary']
        self.assertIn('total_contributions_credited', hpf_summary)
        self.assertIn('active_accounts', hpf_summary)
        self.assertIn('total_hpf_accounts', resp.data['counts'])
