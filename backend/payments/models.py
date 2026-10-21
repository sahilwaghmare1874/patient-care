from decimal import Decimal
from django.db import models
from patients.models import Patient


class PaymentOrder(models.Model):
    """
    Authoritative server-generated payment order created before checkout.
    Monetary values are stored in integer minor units (paise: 1 INR = 100 paise)
    to eliminate floating-point rounding errors.
    """
    CATEGORY_CHOICES = (
        ('DOCTOR', 'Doctor Consultation'),
        ('PATHOLOGY', 'Pathology Diagnostic'),
        ('PHARMACY', 'Pharmacy Purchase'),
        ('GENERAL', 'General Healthcare'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active / In Checkout'),
        ('SUCCESS', 'Success / Verified'),
        ('FAILED', 'Failed'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    )

    order_id = models.CharField(max_length=64, unique=True, db_index=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='payment_orders')
    provider_id = models.CharField(max_length=64, blank=True)
    provider_name = models.CharField(max_length=150, blank=True)
    provider_category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='DOCTOR')
    service_description = models.CharField(max_length=255, default='Healthcare Service Payment')

    # Monetary values in integer paise
    amount_paise = models.BigIntegerField(help_text="Bill amount in integer paise (100 paise = 1 INR)")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=10, default='INR')

    # Configurable healthcare contribution
    contribution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))
    expected_contribution_paise = models.BigIntegerField(default=0)
    expected_contribution_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Gateway integration tracking
    gateway_name = models.CharField(max_length=50, default='YOUPI_PG')
    gateway_payment_id = models.CharField(max_length=100, blank=True)
    checkout_url = models.TextField(blank=True)
    return_url = models.TextField(blank=True)
    utr = models.CharField(max_length=100, blank=True)
    idempotency_key = models.CharField(max_length=100, unique=True, db_index=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_id} - {self.patient.patient_id} - ₹{self.amount} ({self.status})"

    @property
    def amount_inr(self):
        return Decimal(self.amount_paise) / Decimal(100)

    @property
    def contribution_inr(self):
        return Decimal(self.expected_contribution_paise) / Decimal(100)


class WebhookDelivery(models.Model):
    """
    Audit log of all incoming payment gateway webhook payloads.
    Guarantees replay protection, cryptographic verification audit, and delivery tracking.
    """
    STATUS_CHOICES = (
        ('RECEIVED', 'Received'),
        ('PROCESSED', 'Processed'),
        ('REJECTED', 'Rejected'),
        ('DUPLICATE', 'Duplicate'),
    )

    delivery_id = models.CharField(max_length=100, unique=True, db_index=True)
    order = models.ForeignKey(PaymentOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name='webhook_deliveries')
    signature = models.CharField(max_length=255)
    event_type = models.CharField(max_length=50, default='SUCCESS')
    payload = models.JSONField(default=dict)
    raw_body = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='RECEIVED')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Webhook {self.delivery_id} - {self.event_type} ({self.status})"


class Payment(models.Model):
    """
    Authoritative settled payment record linked to patient, provider, and healthcare ledger.
    """
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
    order = models.ForeignKey(PaymentOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_payments')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='payments')
    provider_id = models.CharField(max_length=50, blank=True)
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPE_CHOICES)
    service_description = models.CharField(max_length=200, default='Healthcare Service Settlement')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paise = models.BigIntegerField(default=0)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=60, default='YouPI-PG Sovereign UPI')
    reference_number = models.CharField(max_length=60, blank=True)
    utr = models.CharField(max_length=100, blank=True)
    contribution_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    contribution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    idempotency_key = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Completed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.patient.patient_id} - {self.payment_type} (₹{self.amount})"


class PaymentRefund(models.Model):
    """
    Record of partial or full refund on a verified payment order.
    Requires an immutable compensating reversal entry in the Health Protection ledger.
    """
    STATUS_CHOICES = (
        ('INITIATED', 'Initiated'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    refund_reference = models.CharField(max_length=64, unique=True, db_index=True)
    payment_order = models.ForeignKey(PaymentOrder, on_delete=models.PROTECT, related_name='refunds')
    refund_amount_paise = models.BigIntegerField()
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    reversal_ledger_reference = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund {self.refund_reference} - {self.payment_order.order_id} - ₹{self.refund_amount}"
