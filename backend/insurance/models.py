from django.db import models
from patients.models import Patient

class InsuranceCompany(models.Model):
    company_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    license_number = models.CharField(max_length=60, unique=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.company_name


class InsurancePolicy(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='insurance_policies')
    company = models.ForeignKey(InsuranceCompany, on_delete=models.CASCADE, related_name='policies')
    policy_number = models.CharField(max_length=50, unique=True)
    coverage_limit = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.policy_number} - {self.company.company_name} ({self.patient.patient_id})"


class InsuranceClaim(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Review', 'In Review'),
        ('Approved', 'Approved'),
        ('Partially Approved', 'Partially Approved'),
        ('Rejected', 'Rejected'),
    )

    claim_id = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='insurance_claims')
    policy = models.ForeignKey(InsurancePolicy, on_delete=models.CASCADE, related_name='claims')
    insurance_company = models.CharField(max_length=150)
    treatment_cost = models.DecimalField(max_digits=12, decimal_places=2)
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    rejected_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='Pending')
    documents = models.FileField(upload_to='insurance_docs/', blank=True, null=True)
    submission_date = models.DateField(auto_now_add=True)
    approval_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-submission_date']

    def __str__(self):
        return f"{self.claim_id} - {self.patient.patient_id} ({self.status}) - ₹{self.approved_amount}"
