from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import datetime

from accounts.models import User, DoctorProfile, PathologyProfile, PharmacyProfile
from pathology.models import PathologyTest
from pharmacy.models import Medicine
from government.models import GovernmentScheme
from insurance.models import InsuranceCompany
from funds.models import AllocationConfiguration

class Command(BaseCommand):
    help = 'Seeds database with realistic healthcare schemes, catalogs, medicines, and initial provider accounts'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding healthcare database infrastructure...")

        # 1. System Administrator
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@patientcare.org',
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        # 2. Government Officer
        gov_user, _ = User.objects.get_or_create(
            username='govt_officer',
            defaults={
                'email': 'officer@health.gov.in',
                'mobile': '9811002233',
                'role': 'GOVERNMENT',
                'is_verified': True
            }
        )
        gov_user.set_password('govt123')
        gov_user.save()

        # 3. Doctor Account
        doc_user, _ = User.objects.get_or_create(
            username='dr_kadam',
            defaults={
                'email': 'dr.kadam@apexmed.org',
                'mobile': '9822114455',
                'role': 'DOCTOR',
                'is_verified': True
            }
        )
        doc_user.set_password('doc123')
        doc_user.save()

        DoctorProfile.objects.get_or_create(
            user=doc_user,
            defaults={
                'doctor_id': 'DOC-2026-0001',
                'full_name': 'Dr. S. Kadam, MD',
                'qualification': 'MBBS, MD (Internal Medicine)',
                'specialization': 'General Medicine & Cardiology',
                'registration_number': 'MCI-REG-98124',
                'experience_years': 14,
                'hospital_name': 'Apex Multi-Speciality Hospital',
                'contact_number': '9822114455',
                'email': 'dr.kadam@apexmed.org',
                'address': '402 Health Towers, Shivajinagar, Pune',
                'is_approved': True
            }
        )

        # 4. Pathology Lab Account
        lab_user, _ = User.objects.get_or_create(
            username='city_pathology',
            defaults={
                'email': 'reports@citydiagnostics.org',
                'mobile': '9833225566',
                'role': 'PATHOLOGY',
                'is_verified': True
            }
        )
        lab_user.set_password('lab123')
        lab_user.save()

        PathologyProfile.objects.get_or_create(
            user=lab_user,
            defaults={
                'lab_id': 'LAB-2026-0001',
                'lab_name': 'City Care Diagnostics & Imaging',
                'license_number': 'NABL-LIC-2026-44',
                'registration_number': 'REG-LAB-8812',
                'owner_name': 'Dr. Meena Swaminathan',
                'contact_number': '9833225566',
                'email': 'reports@citydiagnostics.org',
                'address': 'Plot 12, Diagnostic Hub, Deccan, Pune',
                'services_offered': 'Hematology, Clinical Biochemistry, Serology, Microbiology, Ultrasound',
                'is_approved': True
            }
        )

        # 5. Pharmacy Account
        pharm_user, _ = User.objects.get_or_create(
            username='apex_pharmacy',
            defaults={
                'email': 'pharmacy@apexcare.org',
                'mobile': '9844336677',
                'role': 'PHARMACY',
                'is_verified': True
            }
        )
        pharm_user.set_password('med123')
        pharm_user.save()

        PharmacyProfile.objects.get_or_create(
            user=pharm_user,
            defaults={
                'pharmacy_id': 'PHARM-2026-0001',
                'pharmacy_name': 'Apex Healthcare Chemists & Druggists',
                'license_number': 'FDA-20B-21B-9981',
                'pharmacist_name': 'Rajesh Verma, B.Pharm',
                'contact_number': '9844336677',
                'email': 'pharmacy@apexcare.org',
                'address': 'Shop 4, Hospital Arcade, Pune',
                'is_approved': True
            }
        )

        # 6. Allocation Configuration (Database Rule)
        AllocationConfiguration.objects.get_or_create(
            id=1,
            defaults={
                'name': 'National Healthcare Standard Fund Distribution Policy',
                'doctor_percentage': Decimal('10.00'),
                'pathology_percentage': Decimal('10.00'),
                'pharmacy_percentage': Decimal('5.00'),
                'government_percentage': Decimal('5.00'),
                'patient_benefit_percentage': Decimal('70.00'),
                'is_active': True,
                'updated_by': admin_user
            }
        )

        # 7. Government Schemes
        GovernmentScheme.objects.get_or_create(
            scheme_code='PM-JAY-01',
            defaults={
                'scheme_name': 'Ayushman Bharat Pradhan Mantri Jan Arogya Yojana (PM-JAY)',
                'description': 'Universal secondary and tertiary cashless hospitalization cover providing up to ₹5 Lakhs per family per year.',
                'eligibility': 'Economically vulnerable families identified by SECC deprivation criteria, BPL cardholders, and low-income citizens.',
                'maximum_fund': Decimal('500000.00'),
                'coverage_percentage': Decimal('100.00'),
                'start_date': datetime.date(2024, 1, 1),
                'end_date': datetime.date(2030, 12, 31),
                'status': 'Active',
                'terms_and_conditions': 'Valid at all empanelled public and private healthcare networks with permanent Patient ID.'
            }
        )

        GovernmentScheme.objects.get_or_create(
            scheme_code='PMSBY-02',
            defaults={
                'scheme_name': 'Pradhan Mantri Suraksha Bima Yojana (PMSBY)',
                'description': 'Accident and trauma protection insurance policy providing hospital expense coverage up to ₹2 Lakhs.',
                'eligibility': 'Indian citizens aged 18 to 70 with an active bank account and universal health identifier.',
                'maximum_fund': Decimal('200000.00'),
                'coverage_percentage': Decimal('90.00'),
                'start_date': datetime.date(2024, 1, 1),
                'end_date': datetime.date(2030, 12, 31),
                'status': 'Active',
                'terms_and_conditions': 'Direct settlement against medical emergency bills.'
            }
        )

        # 8. Pathology Tests Catalog
        tests_data = [
            ('CBC-01', 'Complete Blood Count (CBC) with Platelet Count', 'Hematology', Decimal('800.00'), 'Hb: 13-17 g/dL, TLC: 4,000-11,000 /mcL, Platelets: 1.5-4.5 Lakhs'),
            ('LIPID-02', 'Comprehensive Lipid Profile Panel', 'Biochemistry', Decimal('1200.00'), 'Total Cholesterol: <200 mg/dL, HDL: >40 mg/dL, LDL: <100 mg/dL'),
            ('LFT-03', 'Liver Function Test (LFT) with Enzymes', 'Biochemistry', Decimal('950.00'), 'Bilirubin Total: 0.2-1.2 mg/dL, SGOT/AST: <40 U/L, SGPT/ALT: <45 U/L'),
            ('HBA1C-04', 'Glycated Hemoglobin (HbA1c) Fasting', 'Biochemistry', Decimal('650.00'), 'Normal: <5.7%, Prediabetes: 5.7-6.4%, Diabetes: >=6.5%'),
            ('XRAY-05', 'Digital Chest Radiography (PA View)', 'Radiology', Decimal('750.00'), 'Both lung fields clear. Heart size normal. No active focal lesion.'),
        ]
        for code, name, cat, price, normal in tests_data:
            PathologyTest.objects.get_or_create(
                test_code=code,
                defaults={'test_name': name, 'category': cat, 'standard_price': price, 'normal_range': normal}
            )

        # 9. Medicine Catalog
        meds_data = [
            ('Paracetamol 650mg', 'Paracetamol', 'Analgesic & Antipyretic', Decimal('35.00'), 1000, 'Tablet'),
            ('Azithromycin 500mg', 'Azithromycin', 'Antibiotic (Macrolide)', Decimal('120.00'), 500, 'Tablet'),
            ('Amoxicillin 500mg', 'Amoxicillin Trihydrate', 'Antibiotic (Penicillin)', Decimal('85.00'), 600, 'Capsule'),
            ('Pantoprazole 40mg', 'Pantoprazole Sodium', 'Proton Pump Inhibitor', Decimal('65.00'), 800, 'Tablet'),
            ('Cetirizine 10mg', 'Cetirizine Hydrochloride', 'Antihistamine', Decimal('40.00'), 750, 'Tablet'),
            ('Vitamin C 500mg & Zinc', 'Ascorbic Acid + Zinc', 'Nutritional Supplement', Decimal('50.00'), 900, 'Chewable Tablet'),
        ]
        for m_name, g_name, cat, price, stock, form in meds_data:
            Medicine.objects.get_or_create(
                medicine_name=m_name,
                defaults={'generic_name': g_name, 'category': cat, 'unit_price': price, 'stock_quantity': stock, 'dosage_form': form}
            )

        # 10. Insurance Company
        InsuranceCompany.objects.get_or_create(
            company_name='National Health Assurance Corporation',
            defaults={
                'contact_email': 'support@nationalassurance.org',
                'contact_phone': '1800-22-9900',
                'license_number': 'IRDA-LIC-2026-004',
                'address': 'Tower C, Financial Plaza, Mumbai'
            }
        )

        self.stdout.write(self.style.SUCCESS("Healthcare system infrastructure seeded successfully (Admin, Schemes, Catalog, Medicines, Fund Policy)!"))
