from django.db import models
from patients.models import Patient
from accounts.models import User

class ReportDownloadLog(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='download_logs')
    downloaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    report_format = models.CharField(max_length=20, default='PDF') # PDF, CSV, WEB
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_format} report for {self.patient.patient_id} at {self.downloaded_at}"
