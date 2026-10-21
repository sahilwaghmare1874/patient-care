from django.db import models
from decimal import Decimal
from patients.models import Patient
from accounts.models import User
from government.models import GovernmentScheme
from insurance.models import InsuranceClaim

class AllocationConfiguration(models.Model):
    name = models.CharField(max_length=150, default="Healthcare Fund Distribution Policy")
    doctor_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    pathology_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    pharmacy_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    government_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    patient_benefit_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('70.00'))
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def total_percentage(self):
        return (
            self.doctor_percentage +
            self.pathology_percentage +
            self.pharmacy_percentage +
            self.government_percentage +
            self.patient_benefit_percentage
        )

    def is_valid(self):
        return self.total_percentage() == Decimal('100.00')

    def __str__(self):
        return f"{self.name} (Doc: {self.doctor_percentage}%, Path: {self.pathology_percentage}%, Med: {self.pharmacy_percentage}%, Gov: {self.government_percentage}%, Benefit: {self.patient_benefit_percentage}%)"


class FundAllocation(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Distributed', 'Distributed'),
        ('Settled', 'Settled'),
    )

    allocation_id = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='fund_allocations')
    scheme = models.ForeignKey(GovernmentScheme, on_delete=models.SET_NULL, null=True, blank=True, related_name='fund_allocations')
    insurance_claim = models.ForeignKey(InsuranceClaim, on_delete=models.SET_NULL, null=True, blank=True, related_name='fund_allocations')
    
    total_treatment_cost = models.DecimalField(max_digits=12, decimal_places=2)
    approved_government_fund = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    approved_insurance_fund = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_approved_fund = models.DecimalField(max_digits=12, decimal_places=2)

    # Department Allocations
    doctor_allocation = models.DecimalField(max_digits=12, decimal_places=2)
    pathology_allocation = models.DecimalField(max_digits=12, decimal_places=2)
    pharmacy_allocation = models.DecimalField(max_digits=12, decimal_places=2)
    government_allocation = models.DecimalField(max_digits=12, decimal_places=2)
    patient_benefit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    patient_out_of_pocket = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Snapshot of applied percentages
    applied_doctor_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    applied_pathology_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    applied_pharmacy_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    applied_government_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    applied_benefit_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('70.00'))

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Approved')
    calculation_basis = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.allocation_id} - {self.patient.patient_id} - Total Fund: ₹{self.total_approved_fund}"


class HealthcareReserveAccount(models.Model):
    """Patient healthcare reserve/savings account."""
    account_number = models.CharField(max_length=30, unique=True, db_index=True)
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='reserve_account')
    reserve_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('90.00'))
    available_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    reserved_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    utilized_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_credited = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_debited = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Reserve {self.account_number} — {self.patient.patient_id} — Available: {self.available_balance}'

    @property
    def total_balance(self):
        return self.available_balance + self.reserved_balance


class ReserveLedgerEntry(models.Model):
    """Immutable ledger entry for every reserve account transaction."""
    ENTRY_TYPE_CHOICES = [
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
        ('RESERVE', 'Reserve'),
        ('RELEASE', 'Release'),
        ('REVERSAL', 'Reversal'),
        ('SETTLEMENT', 'Settlement'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
    ]

    idempotency_key = models.CharField(max_length=64, unique=True, db_index=True)
    account = models.ForeignKey(HealthcareReserveAccount, on_delete=models.PROTECT, related_name='ledger_entries')
    entry_type = models.CharField(max_length=15, choices=ENTRY_TYPE_CHOICES)
    original_invoice_amount = models.DecimalField(max_digits=12, decimal_places=2)
    eligible_amount = models.DecimalField(max_digits=12, decimal_places=2)
    reserve_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    credit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    funding_source = models.CharField(max_length=100, default='Simulation — Pending Contractual Approval')
    service_type = models.CharField(max_length=60)  # 'Doctor', 'Pharmacy', 'Pathology'
    reference_id = models.CharField(max_length=60)  # consultation_id / invoice_number / report_id
    description = models.TextField(blank=True)
    balance_before = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    is_simulated = models.BooleanField(default=True, help_text='True = simulation only, no real money movement')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.entry_type} {self.credit_amount} — {self.account.patient.patient_id} — {self.reference_id}'

    def save(self, *args, **kwargs):
        if self.pk:
            # Financial ledger entries are immutable after creation
            raise ValueError('Ledger entries cannot be modified after creation. Use a reversal entry.')
        super().save(*args, **kwargs)


class PatientHealthProtectionAccount(models.Model):
    """
    Dedicated PatientCare Health Protection Fund Account.
    Accumulates 10% from qualifying doctor, pathology, and pharmacy payments
    to build financial protection for future eligible healthcare expenses.
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('CLOSED', 'Closed'),
    )

    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='health_protection_account')
    account_reference = models.CharField(max_length=40, unique=True, db_index=True)
    available_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_contributions = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_approved_withdrawals = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    total_reversals = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Protection Fund {self.account_reference} — {self.patient.patient_id} — Balance: ₹{self.available_balance}"


class HealthProtectionAllocationRule(models.Model):
    """
    Database-backed configuration for Health Protection Fund contribution percentages.
    Default: 10% for Doctor, Pathology, and Pharmacy.
    """
    service_category = models.CharField(max_length=60, unique=True)
    contribution_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    is_active = models.BooleanField(default=True)
    min_eligible_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    max_contribution_per_txn = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10000.00'))
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['service_category']

    def __str__(self):
        return f"{self.service_category}: {self.contribution_percentage}% (Active: {self.is_active})"


class HealthProtectionTransaction(models.Model):
    """
    Immutable ledger of all PatientCare Health Protection Fund movements:
    contributions (10% on qualifying payments), withdrawals (claim disbursements), and reversals (refunds).
    """
    TRANSACTION_TYPES = (
        ('CONTRIBUTION', 'Contribution'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('REVERSAL', 'Reversal'),
    )
    STATUS_CHOICES = (
        ('COMPLETED', 'Completed'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
        ('REVERSED', 'Reversed'),
    )

    transaction_reference = models.CharField(max_length=40, unique=True, db_index=True)
    idempotency_key = models.CharField(max_length=100, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name='protection_transactions')
    protection_account = models.ForeignKey(PatientHealthProtectionAccount, on_delete=models.PROTECT, related_name='transactions')
    source_payment = models.ForeignKey('payments.Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='protection_contributions')
    provider_id = models.CharField(max_length=60, blank=True)
    provider_name = models.CharField(max_length=150, blank=True)
    service_category = models.CharField(max_length=60)
    eligible_payment_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    contribution_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    balance_before = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    reversal_reference = models.CharField(max_length=40, blank=True, default='')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_reference} [{self.transaction_type}] ₹{self.amount} ({self.service_category})"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError('Health Protection ledger entries are immutable and cannot be updated. Use a reversal entry.')
        super().save(*args, **kwargs)


class HealthProtectionClaim(models.Model):
    """
    Future healthcare expense claim against the patient's accumulated Health Protection Fund balance.
    Controlled workflow: SUBMITTED -> UNDER_REVIEW -> APPROVED -> PAID (or REJECTED / CANCELLED).
    """
    STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    )
    CATEGORY_CHOICES = (
        ('Doctor Consultation', 'Doctor Consultation'),
        ('Hospitalization', 'Hospitalization'),
        ('Diagnostic Tests', 'Diagnostic Tests'),
        ('Prescription Medicines', 'Prescription Medicines'),
        ('Preventive Health Checkup', 'Preventive Health Checkup'),
        ('Surgical Procedure', 'Surgical Procedure'),
        ('Other Eligible Healthcare', 'Other Eligible Healthcare'),
    )

    claim_reference = models.CharField(max_length=40, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='health_protection_claims')
    protection_account = models.ForeignKey(PatientHealthProtectionAccount, on_delete=models.CASCADE, related_name='claims')
    expense_category = models.CharField(max_length=60, choices=CATEGORY_CHOICES, default='Doctor Consultation')
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    provider_name = models.CharField(max_length=150)
    invoice_number = models.CharField(max_length=60, blank=True)
    invoice_date = models.DateField()
    description = models.TextField(blank=True)
    supporting_documents = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUBMITTED')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_protection_claims')
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    linked_transaction = models.ForeignKey(HealthProtectionTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.claim_reference} - {self.patient.patient_id} - ₹{self.requested_amount} ({self.status})"

