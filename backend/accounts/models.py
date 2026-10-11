from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import datetime

class User(AbstractUser):
    ROLE_CHOICES = (
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('PATHOLOGY', 'Pathology Lab'),
        ('PHARMACY', 'Medical / Pharmacy'),
        ('GOVERNMENT', 'Government Officer'),
        ('ADMIN', 'System Administrator'),
        ('HOSPITAL_ADMIN', 'Hospital Administrator'),
        ('FINANCE', 'Finance Officer'),
        ('INSURANCE_OFFICER', 'Insurance Officer'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    mobile = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class OTPVerification(models.Model):
    PURPOSE_CHOICES = (
        ('REGISTRATION', 'Registration'),
        ('LOGIN', 'Login'),
        ('PASSWORD_RESET', 'Password Reset'),
    )

    identifier = models.CharField(max_length=150) # Email or Mobile
    otp_code = models.CharField(max_length=6, default='123456')
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='REGISTRATION')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return not self.is_verified and timezone.now() <= self.expires_at


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    doctor_id = models.CharField(max_length=30, unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    qualification = models.CharField(max_length=150)
    specialization = models.CharField(max_length=150)
    registration_number = models.CharField(max_length=50, unique=True)
    experience_years = models.PositiveIntegerField(default=5)
    hospital_name = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.doctor_id}) - {self.specialization}"


class PathologyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pathology_profile')
    lab_id = models.CharField(max_length=30, unique=True, db_index=True)
    lab_name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    registration_number = models.CharField(max_length=50, blank=True)
    owner_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    services_offered = models.TextField(default="Hematology, Biochemistry, Radiology, Pathology")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lab_name} ({self.lab_id})"


class PharmacyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pharmacy_profile')
    pharmacy_id = models.CharField(max_length=30, unique=True, db_index=True)
    pharmacy_name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    pharmacist_name = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pharmacy_name} ({self.pharmacy_id})"


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=30)
    action = models.CharField(max_length=250)
    patient_id = models.CharField(max_length=35, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.role}: {self.action}"
