"""
PatientCare Health Protection Fund — Financial Ledger & Accounting Service
Handles:
- Dedicated PatientHealthProtectionAccount lifecycle
- Automatic 10% fund crediting on qualifying payments (Doctor, Pathology, Pharmacy)
- Idempotency protection to prevent duplicate credits
- Transparent distinction between provider settlement (90%) and patient protection fund (10%)
- Reversals on payment refunds
- Controlled healthcare expense claim workflow (SUBMITTED -> UNDER_REVIEW -> APPROVED -> PAID)
"""

from decimal import Decimal
import uuid
from django.db import transaction
from django.utils import timezone
from .models import (
    PatientHealthProtectionAccount,
    HealthProtectionTransaction,
    HealthProtectionAllocationRule,
    HealthProtectionClaim,
)
from patients.models import Patient
from accounts.models import User, AuditLog
from notifications.models import Notification


DEFAULT_RULES = {
    'Doctor Consultation': Decimal('10.00'),
    'Pathology Diagnostic': Decimal('10.00'),
    'Pharmacy Purchase': Decimal('5.00'),
}


def ensure_default_allocation_rules():
    """Ensure database-backed rules exist: Doctor 10%, Pathology 10%, Pharmacy 5%."""
    for category, pct in DEFAULT_RULES.items():
        rule, created = HealthProtectionAllocationRule.objects.get_or_create(
            service_category=category,
            defaults={
                'contribution_percentage': pct,
                'is_active': True,
                'min_eligible_amount': Decimal('0.00'),
                'max_contribution_per_txn': Decimal('10000.00'),
                'description': f'Automatic {pct}% contribution to patient healthcare protection fund from {category.lower()} payment.'
            }
        )
        if not created and category == 'Pharmacy Purchase' and rule.contribution_percentage == Decimal('10.00'):
            rule.contribution_percentage = Decimal('5.00')
            rule.description = f'Automatic 5.00% contribution to patient healthcare protection fund from pharmacy purchase payment.'
            rule.save(update_fields=['contribution_percentage', 'description', 'updated_at'])


def get_or_create_protection_account(patient):
    """Retrieve or initialize a patient's dedicated Health Protection Fund account."""
    account, created = PatientHealthProtectionAccount.objects.get_or_create(
        patient=patient,
        defaults={
            'account_reference': f'HPF-{patient.patient_id}',
            'available_balance': Decimal('0.00'),
            'total_contributions': Decimal('0.00'),
            'total_approved_withdrawals': Decimal('0.00'),
            'total_reversals': Decimal('0.00'),
            'status': 'ACTIVE',
        }
    )
    return account


def get_rule_percentage_for_service(service_category):
    """Fetch database-backed percentage for a service category, defaulting to 10%."""
    ensure_default_allocation_rules()
    rule = HealthProtectionAllocationRule.objects.filter(
        service_category__iexact=service_category,
        is_active=True
    ).first()
    if not rule:
        # Check partial matches e.g. 'Doctor' in 'Doctor Consultation'
        rule = HealthProtectionAllocationRule.objects.filter(
            service_category__icontains=service_category.split()[0],
            is_active=True
        ).first()
    return rule.contribution_percentage if rule else Decimal('10.00')


@transaction.atomic
def credit_health_protection_fund(
    payment,
    patient=None,
    provider_id='',
    provider_name='',
    service_category='Doctor Consultation',
    eligible_amount=None,
    user=None,
    idempotency_key=None
):
    """
    Credits 10% of eligible payment to the patient's Health Protection Fund.
    Rules:
    - Succeeded/Completed payment only.
    - Idempotent: checks payment reference / idempotency_key to prevent duplicate credits.
    - Uses Decimal arithmetic with 2 decimal precision.
    - Distinguishes provider settlement amount from patient protection fund credit.
    - Generates immutable financial ledger entry.
    """
    if payment and payment.status != 'Completed':
        raise ValueError(f"Cannot credit fund for payment with status '{payment.status}'. Payment must be 'Completed'.")

    target_patient = patient or (payment.patient if payment else None)
    if not target_patient:
        raise ValueError("A valid patient is required to credit the Health Protection Fund.")

    # Idempotency Key validation
    key = idempotency_key or (f"HPF-PAY-{payment.transaction_id}" if payment else str(uuid.uuid4()))

    existing_txn = HealthProtectionTransaction.objects.filter(idempotency_key=key).first()
    if existing_txn:
        # Already processed — return existing transaction without double crediting
        account = existing_txn.protection_account
        return {
            'is_duplicate': True,
            'message': 'Protection fund contribution already processed (idempotent).',
            'transaction': existing_txn,
            'credit_amount': existing_txn.amount,
            'available_balance': account.available_balance,
            'account_reference': account.account_reference,
            'provider_settlement': (existing_txn.eligible_payment_amount - existing_txn.amount).quantize(Decimal('0.01')),
        }

    # Also check if payment was already credited via source_payment
    if payment:
        prior_credit = HealthProtectionTransaction.objects.filter(
            source_payment=payment,
            transaction_type='CONTRIBUTION',
            status='COMPLETED'
        ).first()
        if prior_credit:
            account = prior_credit.protection_account
            return {
                'is_duplicate': True,
                'message': 'Payment already has an active protection fund credit.',
                'transaction': prior_credit,
                'credit_amount': prior_credit.amount,
                'available_balance': account.available_balance,
                'account_reference': account.account_reference,
                'provider_settlement': (prior_credit.eligible_payment_amount - prior_credit.amount).quantize(Decimal('0.01')),
            }

    base_amount = Decimal(str(eligible_amount if eligible_amount is not None else (payment.amount if payment else Decimal('0.00'))))
    if base_amount <= Decimal('0.00'):
        raise ValueError("Eligible payment amount must be greater than zero.")

    percentage = get_rule_percentage_for_service(service_category)
    credit_amount = (base_amount * percentage / Decimal('100.00')).quantize(Decimal('0.01'))
    provider_settlement = (base_amount - credit_amount).quantize(Decimal('0.01'))

    # Lock account row for update to prevent concurrent race conditions
    account = PatientHealthProtectionAccount.objects.select_for_update().get_or_create(
        patient=target_patient,
        defaults={
            'account_reference': f'HPF-{target_patient.patient_id}',
            'available_balance': Decimal('0.00'),
            'total_contributions': Decimal('0.00'),
            'total_approved_withdrawals': Decimal('0.00'),
            'total_reversals': Decimal('0.00'),
            'status': 'ACTIVE',
        }
    )[0]

    balance_before = account.available_balance
    balance_after = balance_before + credit_amount

    # Update account balances
    account.available_balance = balance_after
    account.total_contributions = account.total_contributions + credit_amount
    account.save(update_fields=['available_balance', 'total_contributions', 'updated_at'])

    # Generate unique transaction reference
    count = HealthProtectionTransaction.objects.count() + 1
    ref = f"HPT-{timezone.now().strftime('%Y%m%d')}-{count:05d}"
    while HealthProtectionTransaction.objects.filter(transaction_reference=ref).exists():
        count += 1
        ref = f"HPT-{timezone.now().strftime('%Y%m%d')}-{count:05d}"

    txn = HealthProtectionTransaction(
        transaction_reference=ref,
        idempotency_key=key,
        patient=target_patient,
        protection_account=account,
        source_payment=payment,
        provider_id=provider_id or (payment.provider_id if payment else ''),
        provider_name=provider_name or '',
        service_category=service_category,
        eligible_payment_amount=base_amount,
        contribution_percentage=percentage,
        amount=credit_amount,
        transaction_type='CONTRIBUTION',
        status='COMPLETED',
        balance_before=balance_before,
        balance_after=balance_after,
        description=f"Automatic {percentage}% Health Protection contribution from {service_category} (₹{base_amount}).",
        created_by=user
    )
    txn.save()

    # Create notifications and audit log
    if target_patient.user:
        Notification.objects.create(
            recipient=target_patient.user,
            title="Health Protection Fund Credited",
            message=(
                f"₹{credit_amount} (10%) has been credited to your PatientCare Health Protection Fund "
                f"from your {service_category} payment. Current balance: ₹{balance_after}."
            ),
            notification_type="PAYMENT"
        )

    AuditLog.objects.create(
        user=user if (user and user.is_authenticated) else None,
        role='FINANCE',
        action=f"CREDIT_HEALTH_PROTECTION_FUND: ₹{credit_amount} credited to {account.account_reference} for {target_patient.patient_id} (Txn: {ref})",
        patient_id=target_patient.patient_id,
        details=f"Payment: {payment.transaction_id if payment else 'Manual'} | Service: {service_category} | Eligible: ₹{base_amount} | Provider Settlement: ₹{provider_settlement}"
    )

    return {
        'is_duplicate': False,
        'message': f"₹{credit_amount} ({percentage}%) successfully credited to Health Protection Fund.",
        'transaction': txn,
        'credit_amount': credit_amount,
        'provider_settlement': provider_settlement,
        'available_balance': balance_after,
        'account_reference': account.account_reference,
    }


@transaction.atomic
def reverse_health_protection_fund(source_payment=None, payment=None, patient=None, user=None, reason='Payment refund', idempotency_key=None):
    """
    Reverses the Health Protection Fund contribution associated with a payment upon refund.
    Ensures ledger consistency and prevents orphaned or duplicate balances.
    Idempotent: if a reversal already exists for the idempotency_key, returns existing result.
    """
    # Support both 'payment' and 'source_payment' for backward compatibility
    payment = source_payment or payment
    if not payment:
        raise ValueError("Payment is required for reversal.")

    # Idempotency check
    if idempotency_key:
        existing_rev = HealthProtectionTransaction.objects.filter(idempotency_key=idempotency_key).first()
        if existing_rev:
            return {
                'reversed': True,
                'duplicate': True,
                'message': 'Reversal already processed (idempotent).',
                'transaction_reference': existing_rev.transaction_reference,
                'available_balance': existing_rev.balance_after,
            }

    orig_txn = HealthProtectionTransaction.objects.filter(
        source_payment=payment,
        transaction_type='CONTRIBUTION',
        status='COMPLETED'
    ).first()

    if not orig_txn:
        return {
            'reversed': False,
            'message': 'No active Health Protection contribution found for this payment.'
        }

    account = PatientHealthProtectionAccount.objects.select_for_update().get(id=orig_txn.protection_account_id)
    reversal_amount = orig_txn.amount
    balance_before = account.available_balance

    # Protect against negative balances: minimum balance is 0.00
    balance_after = max(Decimal('0.00'), balance_before - reversal_amount)

    account.available_balance = balance_after
    account.total_reversals = account.total_reversals + reversal_amount
    account.save(update_fields=['available_balance', 'total_reversals', 'updated_at'])

    count = HealthProtectionTransaction.objects.count() + 1
    rev_ref = f"HPT-REV-{timezone.now().strftime('%Y%m%d')}-{count:05d}"
    while HealthProtectionTransaction.objects.filter(transaction_reference=rev_ref).exists():
        count += 1
        rev_ref = f"HPT-REV-{timezone.now().strftime('%Y%m%d')}-{count:05d}"

    rev_txn = HealthProtectionTransaction(
        transaction_reference=rev_ref,
        idempotency_key=idempotency_key or f"REV-{orig_txn.idempotency_key}",
        patient=orig_txn.patient,
        protection_account=account,
        source_payment=payment,
        provider_id=orig_txn.provider_id,
        provider_name=orig_txn.provider_name,
        service_category=orig_txn.service_category,
        eligible_payment_amount=orig_txn.eligible_payment_amount,
        contribution_percentage=orig_txn.contribution_percentage,
        amount=reversal_amount,
        transaction_type='REVERSAL',
        status='COMPLETED',
        balance_before=balance_before,
        balance_after=balance_after,
        reversal_reference=orig_txn.transaction_reference,
        description=f"Reversal of {orig_txn.transaction_reference} due to {reason}.",
        created_by=user
    )
    rev_txn.save()

    # Mark original transaction as REVERSED
    HealthProtectionTransaction.objects.filter(id=orig_txn.id).update(status='REVERSED')

    AuditLog.objects.create(
        user=user if (user and user.is_authenticated) else None,
        role='FINANCE',
        action=f"REVERSE_HEALTH_PROTECTION_FUND: ₹{reversal_amount} reversed from {account.account_reference} (Txn: {rev_ref})",
        patient_id=orig_txn.patient.patient_id,
        details=f"Original Txn: {orig_txn.transaction_reference} | Payment: {payment.transaction_id} | Reason: {reason}"
    )

    return {
        'reversed': True,
        'message': f"₹{reversal_amount} successfully reversed from Health Protection Fund.",
        'reversal_transaction': rev_txn,
        'transaction_reference': rev_txn.transaction_reference,
        'available_balance': balance_after,
    }


@transaction.atomic
def settle_health_protection_claim(claim, approved_amount=None, reviewer=None, review_notes=''):
    """
    Settles an approved Health Protection claim by deducting funds from available balance.
    Enforces authorization, available balance check, and atomic withdrawal ledger entry.
    """
    account = PatientHealthProtectionAccount.objects.select_for_update().get(id=claim.protection_account_id)
    payout = Decimal(str(approved_amount if approved_amount is not None else claim.requested_amount))

    if payout <= Decimal('0.00'):
        raise ValueError("Approved amount must be greater than zero.")

    if payout > account.available_balance:
        raise ValueError(
            f"Insufficient protection balance. Requested ₹{payout}, but available balance is ₹{account.available_balance}."
        )

    balance_before = account.available_balance
    balance_after = balance_before - payout

    account.available_balance = balance_after
    account.total_approved_withdrawals = account.total_approved_withdrawals + payout
    account.save(update_fields=['available_balance', 'total_approved_withdrawals', 'updated_at'])

    count = HealthProtectionTransaction.objects.count() + 1
    txn_ref = f"HPT-CLM-{timezone.now().strftime('%Y%m%d')}-{count:05d}"
    while HealthProtectionTransaction.objects.filter(transaction_reference=txn_ref).exists():
        count += 1
        txn_ref = f"HPT-CLM-{timezone.now().strftime('%Y%m%d')}-{count:05d}"

    withdrawal_txn = HealthProtectionTransaction(
        transaction_reference=txn_ref,
        idempotency_key=f"CLM-{claim.claim_reference}",
        patient=claim.patient,
        protection_account=account,
        provider_name=claim.provider_name,
        service_category=claim.expense_category,
        eligible_payment_amount=claim.requested_amount,
        contribution_percentage=Decimal('100.00'),
        amount=payout,
        transaction_type='WITHDRAWAL',
        status='COMPLETED',
        balance_before=balance_before,
        balance_after=balance_after,
        description=f"Claim settlement for {claim.expense_category} (Invoice #{claim.invoice_number})",
        created_by=reviewer
    )
    withdrawal_txn.save()

    claim.status = 'PAID'
    claim.approved_amount = payout
    claim.reviewer = reviewer
    claim.review_notes = review_notes
    claim.reviewed_at = timezone.now()
    claim.paid_at = timezone.now()
    claim.linked_transaction = withdrawal_txn
    claim.save()

    if claim.patient.user:
        Notification.objects.create(
            recipient=claim.patient.user,
            title="Healthcare Expense Claim Paid",
            message=f"Claim {claim.claim_reference} of ₹{payout} has been approved and paid from your Health Protection Fund. Remaining balance: ₹{balance_after}.",
            notification_type="FUNDING"
        )

    AuditLog.objects.create(
        user=reviewer if (reviewer and reviewer.is_authenticated) else None,
        role='FINANCE',
        action=f"PAID_HEALTH_PROTECTION_CLAIM: {claim.claim_reference} (₹{payout}) for {claim.patient.patient_id}",
        patient_id=claim.patient.patient_id,
        details=f"Withdrawal Txn: {txn_ref} | Balance After: ₹{balance_after}"
    )

    return {
        'claim': claim,
        'withdrawal_transaction': withdrawal_txn,
        'remaining_balance': balance_after,
    }
