from django.db import models
from patients.models import Patient
from accounts.models import PharmacyProfile, DoctorProfile
from doctors.models import Prescription

class Medicine(models.Model):
    medicine_name = models.CharField(max_length=150)
    generic_name = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=80, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=500)
    dosage_form = models.CharField(max_length=50, default="Tablet")

    def __str__(self):
        return f"{self.medicine_name} - ₹{self.unit_price}"


class PharmacyTransaction(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Reimbursed', 'Reimbursed'),
    )

    REIMBURSEMENT_CHOICES = (
        ('Not Claimed', 'Not Claimed'),
        ('Claimed', 'Claimed'),
        ('Approved', 'Approved'),
    )

    invoice_number = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pharmacy_transactions')
    pharmacy = models.ForeignKey(PharmacyProfile, on_delete=models.CASCADE, related_name='transactions')
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensations')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True)
    medicines_dispensed = models.TextField()
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='Paid')
    reimbursement_status = models.CharField(max_length=30, choices=REIMBURSEMENT_CHOICES, default='Not Claimed')
    dispensed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-dispensed_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.patient.patient_id} (₹{self.total_amount})"
