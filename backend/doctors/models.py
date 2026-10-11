from django.db import models
from django.db import transaction
import uuid
from patients.models import Patient
from accounts.models import DoctorProfile

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Requested', 'Requested'),
        ('No Show', 'No Show'),
    )
    CONSULTATION_TYPES = (
        ('In-person', 'In-person'),
        ('Online', 'Online'),
    )

    appointment_id = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    time_slot = models.CharField(max_length=30, default="10:00 AM - 10:30 AM")
    consultation_type = models.CharField(max_length=20, choices=CONSULTATION_TYPES, default='In-person')
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    symptoms = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-appointment_date', '-created_at']

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.full_name} with {self.doctor.full_name}"


class Consultation(models.Model):
    consultation_id = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultations')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='consultations')
    visit_date = models.DateField()
    symptoms = models.TextField()
    diagnosis = models.TextField()
    doctor_notes = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    operation_recommended = models.BooleanField(default=False)
    operation_details = models.TextField(blank=True)
    pathology_referral = models.BooleanField(default=False)
    pathology_tests_recommended = models.TextField(blank=True)
    pharmacy_referral = models.BooleanField(default=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    status = models.CharField(max_length=30, default='Completed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visit_date', '-created_at']

    def __str__(self):
        return f"{self.consultation_id} - {self.patient.patient_id} ({self.diagnosis})"


class Prescription(models.Model):
    prescription_id = models.CharField(max_length=30, unique=True, db_index=True)
    consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='prescriptions')
    medicines = models.TextField() # e.g. Paracetamol 650mg TDS x 5 days, Amoxicillin 500mg BD x 7 days
    instructions = models.TextField(blank=True)
    date_prescribed = models.DateField()
    is_dispensed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_prescribed', '-created_at']

    def __str__(self):
        return f"{self.prescription_id} for {self.patient.patient_id}"


class DoctorAvailability(models.Model):
    DAY_CHOICES = [
        ('Monday','Monday'), ('Tuesday','Tuesday'), ('Wednesday','Wednesday'),
        ('Thursday','Thursday'), ('Friday','Friday'), ('Saturday','Saturday'), ('Sunday','Sunday'),
    ]
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.CharField(max_length=15, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_appointments = models.PositiveIntegerField(default=20)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'day_of_week', 'start_time')

    def __str__(self):
        return f"{self.doctor.full_name} - {self.day_of_week} {self.start_time}-{self.end_time}"


class AppointmentToken(models.Model):
    STATUS_CHOICES = [
        ('Waiting', 'Waiting'),
        ('Called', 'Called'),
        ('In Consultation', 'In Consultation'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('No Show', 'No Show'),
    ]

    token_number = models.PositiveIntegerField()
    appointment = models.OneToOneField('Appointment', on_delete=models.CASCADE, related_name='token')
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='tokens')
    session_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Waiting')
    called_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=64, unique=True, db_index=True)

    class Meta:
        ordering = ['session_date', 'token_number']
        unique_together = ('doctor', 'session_date', 'token_number')

    def __str__(self):
        return f"Token #{self.token_number} - {self.appointment.appointment_id} - {self.status}"
