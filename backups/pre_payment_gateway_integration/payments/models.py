from django.db import models
from patients.models import Patient

class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = (
        ('Doctor Payment', 'Doctor Payment'),
        ('Pathology Payment', 'Pathology Payment'),
        ('Pharmacy Payment', 'Pharmacy Payment'),
        ('Government Payment', 'Government Payment'),
        ('Insurance Payment', 'Insurance Payment'),
        ('Patient Payment', 'Patient Payment'),
    )

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    )

    transaction_id = models.CharField(max_length=35, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='payments')
    provider_id = models.CharField(max_length=50, blank=True)
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPE_CHOICES)
    service_description = models.CharField(max_length=200, default='Healthcare Service Settlement')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=60, default='Assurance Benefit Wallet')
    reference_number = models.CharField(max_length=60, blank=True)
    idempotency_key = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Completed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.patient.patient_id} - {self.payment_type} (₹{self.amount})"
