from django.core.management.base import BaseCommand
from patients.models import Patient
from accounts.models import User
from doctors.models import Consultation, Prescription
from pathology.models import PathologyReport
from pharmacy.models import PharmacyTransaction
from funds.models import FundAllocation
from payments.models import Payment
from insurance.models import InsuranceClaim

class Command(BaseCommand):
    help = 'Removes all demo patient records and associated demo transactions'

    def handle(self, *args, **kwargs):
        self.stdout.write("Purging demo patient IDs and transactions...")

        demo_patient_ids = ['PAT-2026-000001', 'PAT-2026-000002']
        demo_usernames = ['rahul_patient', 'priya_patient']

        # Remove transactions tied to demo patients
        deleted_consults, _ = Consultation.objects.filter(patient__patient_id__in=demo_patient_ids).delete()
        deleted_reports, _ = PathologyReport.objects.filter(patient__patient_id__in=demo_patient_ids).delete()
        deleted_pharms, _ = PharmacyTransaction.objects.filter(patient__patient_id__in=demo_patient_ids).delete()
        deleted_funds, _ = FundAllocation.objects.filter(patient__patient_id__in=demo_patient_ids).delete()
        deleted_payments, _ = Payment.objects.filter(patient__patient_id__in=demo_patient_ids).delete()
        deleted_claims, _ = InsuranceClaim.objects.filter(patient__patient_id__in=demo_patient_ids).delete()

        # Remove demo patients
        deleted_patients, _ = Patient.objects.filter(patient_id__in=demo_patient_ids).delete()

        # Remove demo users
        deleted_users, _ = User.objects.filter(username__in=demo_usernames).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Successfully removed demo IDs:\n"
            f"- Patients removed: {deleted_patients}\n"
            f"- Users removed: {deleted_users}\n"
            f"- Consultations: {deleted_consults}\n"
            f"- Lab reports: {deleted_reports}\n"
            f"- Pharmacy transactions: {deleted_pharms}\n"
            f"- Fund allocations: {deleted_funds}\n"
            f"- Payments: {deleted_payments}\n"
            f"- Claims: {deleted_claims}"
        ))
