from django.db import models

class GovernmentScheme(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    )

    scheme_code = models.CharField(max_length=30, unique=True, db_index=True)
    scheme_name = models.CharField(max_length=200)
    description = models.TextField()
    eligibility = models.TextField()
    maximum_fund = models.DecimalField(max_digits=12, decimal_places=2) # e.g. 500000.00
    coverage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00) # e.g. 80.00 or 100.00
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    terms_and_conditions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheme_code']

    def __str__(self):
        return f"{self.scheme_name} ({self.scheme_code}) - Max: ₹{self.maximum_fund}"


class SchemeApplication(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Pre-Authorized', 'Pre-Authorized'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Claimed', 'Claimed'),
    ]

    application_id = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='scheme_applications')
    scheme = models.ForeignKey(GovernmentScheme, on_delete=models.CASCADE, related_name='applications')
    hospital_name = models.CharField(max_length=200, blank=True)
    treatment_description = models.TextField()
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    documents = models.JSONField(default=list, blank=True)  # list of uploaded doc names
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    officer_remarks = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.application_id} — {self.scheme.scheme_name} — {self.patient.patient_id} ({self.status})'
