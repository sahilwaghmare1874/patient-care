from django.db import models
from accounts.models import User

class Patient(models.Model):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    BLOOD_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    )

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='patient_profile')
    patient_id = models.CharField(max_length=30, unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    dob = models.DateField()
    gender = models.CharField(max_length=15, choices=GENDER_CHOICES)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    # PAN unique constraint (Requirement 5)
    pan_number = models.CharField(max_length=10, unique=True, db_index=True)
    aadhaar_number = models.CharField(max_length=20, blank=True, null=True)
    government_scheme_id = models.CharField(max_length=50, blank=True, null=True)

    # Healthcare details
    blood_group = models.CharField(max_length=10, choices=BLOOD_CHOICES, default='O+')
    allergies = models.TextField(blank=True)
    existing_conditions = models.TextField(blank=True)
    
    # Phase 2 Medical Registration Fields
    illness_description = models.TextField(blank=True, verbose_name='Current Illness / Chief Complaint')
    presenting_symptoms = models.TextField(blank=True, verbose_name='Presenting Symptoms')
    symptom_duration = models.CharField(max_length=100, blank=True, verbose_name='Symptom Duration', help_text='e.g. 3 days, 2 weeks')
    symptom_severity = models.CharField(
        max_length=20,
        choices=[('Mild','Mild'),('Moderate','Moderate'),('Severe','Severe'),('Critical','Critical')],
        blank=True,
        verbose_name='Symptom Severity'
    )
    current_medicines = models.TextField(blank=True, verbose_name='Current Medicines / Ongoing Treatment')
    consent_data_processing = models.BooleanField(default=False, verbose_name='Consent for Medical Data Processing')
    consent_timestamp = models.DateTimeField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=15)

    # Permanent Healthcare Assurance Card (HAC) Number
    hac_number = models.CharField(max_length=35, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.patient_id}) - PAN: {self.masked_pan}"

    @property
    def masked_pan(self):
        if self.pan_number and len(self.pan_number) == 10:
            return f"XXXXX{self.pan_number[5:9]}X"
        return "XXXXXXXXXX"

    @property
    def masked_aadhaar(self):
        if self.aadhaar_number and len(self.aadhaar_number) >= 12:
            return f"XXXX-XXXX-{self.aadhaar_number[-4:]}"
        return "XXXX-XXXX-XXXX"
