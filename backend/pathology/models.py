from django.db import models
from patients.models import Patient
from accounts.models import PathologyProfile, DoctorProfile

class PathologyTest(models.Model):
    test_code = models.CharField(max_length=30, unique=True, db_index=True)
    test_name = models.CharField(max_length=150)
    category = models.CharField(max_length=60) # Hematology, Biochemistry, Radiology, etc.
    standard_price = models.DecimalField(max_digits=10, decimal_places=2)
    normal_range = models.TextField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.test_name} ({self.test_code}) - ₹{self.standard_price}"


class PathologyReport(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Verified', 'Verified'),
    )

    report_id = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='pathology_reports')
    lab = models.ForeignKey(PathologyProfile, on_delete=models.CASCADE, related_name='pathology_reports')
    referring_doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='referred_pathology_reports')
    test_name = models.CharField(max_length=150)
    test_category = models.CharField(max_length=60, default='Clinical Pathology')
    test_date = models.DateField()
    test_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    results_summary = models.TextField()
    detailed_findings = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Verified')
    payment_status = models.CharField(max_length=30, default='Paid')
    document_file = models.FileField(upload_to='pathology_reports/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-test_date', '-created_at']

    def __str__(self):
        return f"{self.report_id} - {self.patient.patient_id} ({self.test_name})"
