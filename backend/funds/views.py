from rest_framework import views, status, permissions
from rest_framework.response import Response
from decimal import Decimal
from django.utils import timezone
from .models import AllocationConfiguration, FundAllocation
from .serializers import AllocationConfigurationSerializer, FundAllocationSerializer
from patients.models import Patient
from government.models import GovernmentScheme
from insurance.models import InsuranceClaim
from accounts.views import create_audit_log
from notifications.models import Notification

class AllocationConfigurationView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        config = AllocationConfiguration.objects.filter(is_active=True).first()
        if not config:
            config = AllocationConfiguration.objects.create(
                name="National Healthcare Fund Distribution Policy",
                doctor_percentage=Decimal('10.00'),
                pathology_percentage=Decimal('10.00'),
                pharmacy_percentage=Decimal('5.00'),
                government_percentage=Decimal('5.00'),
                patient_benefit_percentage=Decimal('70.00'),
                is_active=True
            )
        serializer = AllocationConfigurationSerializer(config)
        return Response(serializer.data)

    def post(self, request):
        config = AllocationConfiguration.objects.filter(is_active=True).first()
        if not config:
            config = AllocationConfiguration(name="National Healthcare Fund Distribution Policy")

        serializer = AllocationConfigurationSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_config = serializer.save(updated_by=request.user if request.user.is_authenticated else None)

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "ADMIN",
            f"Updated Fund Allocation Rules: Doctor={updated_config.doctor_percentage}%, Pathology={updated_config.pathology_percentage}%, Pharmacy={updated_config.pharmacy_percentage}%, Gov={updated_config.government_percentage}%, Benefit={updated_config.patient_benefit_percentage}%",
            request=request
        )

        return Response({
            "message": "Allocation configuration successfully updated and activated.",
            "configuration": AllocationConfigurationSerializer(updated_config).data
        })


class FundAllocationListCreateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        allocations = FundAllocation.objects.all()
        if patient_id:
            allocations = allocations.filter(patient__patient_id__iexact=patient_id)
        serializer = FundAllocationSerializer(allocations, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        patient_id_input = data.pop('patient_id', None)
        if isinstance(patient_id_input, list):
            patient_id_input = patient_id_input[0]

        patient = None
        if patient_id_input:
            patient = Patient.objects.filter(patient_id__iexact=patient_id_input).first()
        if not patient and 'patient' in data:
            patient = Patient.objects.filter(id=data['patient']).first()

        if not patient:
            return Response({"error": "Patient not found. Search patient first."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve active configuration from DATABASE (never hard-coded)
        config = AllocationConfiguration.objects.filter(is_active=True).first()
        if not config:
            config = AllocationConfiguration.objects.create(
                name="National Healthcare Fund Distribution Policy",
                doctor_percentage=Decimal('10.00'),
                pathology_percentage=Decimal('10.00'),
                pharmacy_percentage=Decimal('5.00'),
                government_percentage=Decimal('5.00'),
                patient_benefit_percentage=Decimal('70.00'),
                is_active=True
            )

        treatment_cost = Decimal(str(data.get('total_treatment_cost', 50000.00)))
        gov_fund = Decimal(str(data.get('approved_government_fund', 40000.00)))
        ins_fund = Decimal(str(data.get('approved_insurance_fund', 0.00)))

        # Total Approved Fund
        total_approved = gov_fund + ins_fund
        if total_approved > treatment_cost:
            total_approved = treatment_cost

        # Precise financial calculations based on DB config percentages
        doc_pct = config.doctor_percentage
        path_pct = config.pathology_percentage
        med_pct = config.pharmacy_percentage
        gov_pct = config.government_percentage
        benefit_pct = config.patient_benefit_percentage

        doctor_alloc = (total_approved * doc_pct) / Decimal('100.00')
        pathology_alloc = (total_approved * path_pct) / Decimal('100.00')
        pharmacy_alloc = (total_approved * med_pct) / Decimal('100.00')
        government_alloc = (total_approved * gov_pct) / Decimal('100.00')
        benefit_alloc = (total_approved * benefit_pct) / Decimal('100.00')

        out_of_pocket = Decimal('0.00')
        if treatment_cost > total_approved:
            out_of_pocket = treatment_cost - total_approved

        count = FundAllocation.objects.count() + 1
        allocation_id = f"FUND-2026-{count:04d}"

        # Scheme linkage
        scheme = None
        scheme_id = data.get('scheme') or data.get('scheme_id')
        if scheme_id:
            scheme = GovernmentScheme.objects.filter(id=scheme_id).first()
        if not scheme:
            scheme = GovernmentScheme.objects.filter(status='Active').first()

        # Insurance claim linkage
        claim = None
        claim_id = data.get('insurance_claim_id')
        if claim_id:
            claim = InsuranceClaim.objects.filter(claim_id__iexact=claim_id).first()

        allocation = FundAllocation.objects.create(
            allocation_id=allocation_id,
            patient=patient,
            scheme=scheme,
            insurance_claim=claim,
            total_treatment_cost=treatment_cost,
            approved_government_fund=gov_fund,
            approved_insurance_fund=ins_fund,
            total_approved_fund=total_approved,
            doctor_allocation=doctor_alloc,
            pathology_allocation=pathology_alloc,
            pharmacy_allocation=pharmacy_alloc,
            government_allocation=government_alloc,
            patient_benefit_amount=benefit_alloc,
            patient_out_of_pocket=out_of_pocket,
            remaining_balance=Decimal('0.00'),
            applied_doctor_pct=doc_pct,
            applied_pathology_pct=path_pct,
            applied_pharmacy_pct=med_pct,
            applied_government_pct=gov_pct,
            applied_benefit_pct=benefit_pct,
            status='Approved',
            approval_date=timezone.now().date(),
            calculation_basis=f"Calculated using {config.name}: Doc {doc_pct}%, Path {path_pct}%, Med {med_pct}%, Gov {gov_pct}%, Benefit {benefit_pct}%"
        )

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "GOVERNMENT",
            f"Approved fund allocation: {allocation.allocation_id} for {patient.patient_id} (Approved Fund: ₹{allocation.total_approved_fund})",
            patient_id=patient.patient_id,
            request=request
        )

        if patient.user:
            Notification.objects.create(
                recipient=patient.user,
                title="Healthcare Fund Approved",
                message=f"Government healthcare funding of ₹{allocation.total_approved_fund} approved. Patient Benefit: ₹{allocation.patient_benefit_amount}.",
                notification_type="FUNDING"
            )

        return Response({
            "message": "Healthcare fund allocated and distributed successfully.",
            "allocation": FundAllocationSerializer(allocation).data
        }, status=status.HTTP_201_CREATED)


class PatientFundSummaryView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, patient_id):
        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient and patient_id.isdigit():
            patient = Patient.objects.filter(id=patient_id).first()

        if not patient:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        allocations = patient.fund_allocations.all()
        total_treatment_cost = sum(float(a.total_treatment_cost) for a in allocations)
        total_gov_fund = sum(float(a.approved_government_fund) for a in allocations)
        total_ins_fund = sum(float(a.approved_insurance_fund) for a in allocations)
        total_approved = sum(float(a.total_approved_fund) for a in allocations)
        total_benefit = sum(float(a.patient_benefit_amount) for a in allocations)
        total_out_of_pocket = sum(float(a.patient_out_of_pocket) for a in allocations)

        doctor_payout = sum(float(a.doctor_allocation) for a in allocations)
        pathology_payout = sum(float(a.pathology_allocation) for a in allocations)
        pharmacy_payout = sum(float(a.pharmacy_allocation) for a in allocations)
        gov_admin_payout = sum(float(a.government_allocation) for a in allocations)

        return Response({
            "patient_id": patient.patient_id,
            "patient_name": patient.full_name,
            "total_treatment_cost": total_treatment_cost,
            "total_government_funding": total_gov_fund,
            "total_insurance_funding": total_ins_fund,
            "total_approved_fund": total_approved,
            "patient_benefit_wallet": total_benefit,
            "patient_out_of_pocket": total_out_of_pocket,
            "breakdown": {
                "doctor_payout": doctor_payout,
                "pathology_payout": pathology_payout,
                "pharmacy_payout": pharmacy_payout,
                "government_admin_allocation": gov_admin_payout,
                "patient_benefit": total_benefit
            },
            "history": FundAllocationSerializer(allocations, many=True).data
        })


from django.conf import settings as settings_module
from django.db import transaction
from .models import HealthcareReserveAccount, ReserveLedgerEntry
import uuid

class FundAllocationDetailView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, allocation_id):
        fa = FundAllocation.objects.filter(allocation_id=allocation_id).first()
        if not fa:
            return Response({'error': 'Allocation not found.'}, status=404)
        return Response(FundAllocationSerializer(fa).data)


class ReserveAccountView(views.APIView):
    """Get or create a patient reserve account."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, patient_id):
        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        account, created = HealthcareReserveAccount.objects.get_or_create(
            patient=patient,
            defaults={
                'account_number': f'HCRA-{patient.patient_id}',
                'reserve_percentage': Decimal(str(getattr(settings_module, 'RESERVE_CREDIT_PERCENTAGE', 90.0))),
            }
        )
        return Response({
            'account_number': account.account_number,
            'patient_id': patient_id,
            'patient_name': patient.full_name,
            'reserve_percentage': float(account.reserve_percentage),
            'available_balance': float(account.available_balance),
            'reserved_balance': float(account.reserved_balance),
            'utilized_balance': float(account.utilized_balance),
            'total_credited': float(account.total_credited),
            'total_debited': float(account.total_debited),
            'total_balance': float(account.total_balance),
            'is_active': account.is_active,
            'is_simulated': True,
            'simulation_notice': 'This reserve account operates in simulation mode. No real money is transferred until contractual agreements are in place.',
            'created': created
        })


class ReserveLedgerView(views.APIView):
    """Get ledger entries for a patient reserve account."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, patient_id):
        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        account = HealthcareReserveAccount.objects.filter(patient=patient).first()
        if not account:
            return Response({'entries': [], 'message': 'No reserve account found. Make an eligible transaction first.'})

        entries = account.ledger_entries.all().order_by('-created_at')
        data = [{
            'entry_type': e.entry_type,
            'original_invoice_amount': float(e.original_invoice_amount),
            'eligible_amount': float(e.eligible_amount),
            'reserve_percentage': float(e.reserve_percentage),
            'credit_amount': float(e.credit_amount),
            'service_type': e.service_type,
            'reference_id': e.reference_id,
            'description': e.description,
            'balance_before': float(e.balance_before),
            'balance_after': float(e.balance_after),
            'status': e.status,
            'is_simulated': e.is_simulated,
            'created_at': str(e.created_at),
        } for e in entries]
        return Response({
            'account_number': account.account_number,
            'entries': data,
            'total_entries': len(data)
        })


class ReserveCreditView(views.APIView):
    """Record a reserve credit for an eligible transaction. Idempotent."""
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        from django.conf import settings as django_settings
        patient_id = request.data.get('patient_id')
        service_type = request.data.get('service_type')  # Doctor/Pharmacy/Pathology
        reference_id = request.data.get('reference_id')  # consultation_id etc.
        invoice_amount = Decimal(str(request.data.get('invoice_amount', 0)))
        idempotency_key = request.data.get('idempotency_key') or str(uuid.uuid4())

        # Check idempotency
        existing = ReserveLedgerEntry.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return Response({'message': 'Credit already recorded (idempotent).', 'entry_id': existing.id})

        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient:
            return Response({'error': 'Patient not found.'}, status=404)

        account, _ = HealthcareReserveAccount.objects.select_for_update().get_or_create(
            patient=patient,
            defaults={
                'account_number': f'HCRA-{patient.patient_id}',
                'reserve_percentage': Decimal(str(getattr(django_settings, 'RESERVE_CREDIT_PERCENTAGE', 90.0))),
            }
        )

        pct = account.reserve_percentage
        credit_amount = (invoice_amount * pct / Decimal('100')).quantize(Decimal('0.01'))
        balance_before = account.available_balance
        balance_after = balance_before + credit_amount

        # Update account atomically
        account.available_balance = balance_after
        account.total_credited = account.total_credited + credit_amount
        account.save(update_fields=['available_balance', 'total_credited', 'updated_at'])

        # Create immutable ledger entry
        entry = ReserveLedgerEntry(
            idempotency_key=idempotency_key,
            account=account,
            entry_type='CREDIT',
            original_invoice_amount=invoice_amount,
            eligible_amount=invoice_amount,
            reserve_percentage=pct,
            credit_amount=credit_amount,
            funding_source='Simulation — Pending Contractual Approval',
            service_type=service_type or 'Unknown',
            reference_id=reference_id or '',
            description=f'{service_type} service reserve credit at {pct}%',
            balance_before=balance_before,
            balance_after=balance_after,
            status='COMPLETED',
            is_simulated=True,
            created_by=request.user if request.user.is_authenticated else None,
        )
        entry.save()

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            'FINANCE',
            f'Reserve credit of {credit_amount} for {patient_id} — {service_type} ref:{reference_id}',
            patient_id=patient_id,
            request=request
        )

        return Response({
            'message': f'Reserve credit of ₹{credit_amount} ({pct}%) recorded successfully.',
            'credit_amount': float(credit_amount),
            'balance_after': float(balance_after),
            'is_simulated': True,
            'simulation_notice': 'This is a simulated credit. No real funds transferred.',
        }, status=201)


from .models import (
    PatientHealthProtectionAccount,
    HealthProtectionTransaction,
    HealthProtectionAllocationRule,
    HealthProtectionClaim,
)
from .serializers import (
    PatientHealthProtectionAccountSerializer,
    HealthProtectionTransactionSerializer,
    HealthProtectionAllocationRuleSerializer,
    HealthProtectionClaimSerializer,
)
from .services import (
    get_or_create_protection_account,
    credit_health_protection_fund,
    reverse_health_protection_fund,
    settle_health_protection_claim,
    ensure_default_allocation_rules,
)


class HealthProtectionAccountView(views.APIView):
    """
    Get patient's dedicated PatientCare Health Protection Fund account.
    Returns available balance, accumulated contributions, provider breakdown, and recent ledger entries.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, patient_id=None):
        pid = patient_id or request.query_params.get('patient_id')
        if not pid and request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
            pid = request.user.patient_profile.patient_id

        if not pid:
            return Response({'error': 'patient_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        patient = Patient.objects.filter(patient_id__iexact=pid).first()
        if not patient and pid.isdigit():
            patient = Patient.objects.filter(id=pid).first()

        if not patient:
            return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        account = get_or_create_protection_account(patient)

        # Categorized breakdown of contributions
        txns = account.transactions.filter(transaction_type='CONTRIBUTION', status='COMPLETED')
        doctor_contrib = sum((t.amount for t in txns if 'doctor' in t.service_category.lower()), Decimal('0.00'))
        pathology_contrib = sum((t.amount for t in txns if 'pathology' in t.service_category.lower() or 'diagnostic' in t.service_category.lower() or 'lab' in t.service_category.lower()), Decimal('0.00'))
        pharmacy_contrib = sum((t.amount for t in txns if 'pharmacy' in t.service_category.lower() or 'medicine' in t.service_category.lower()), Decimal('0.00'))

        # Claims summary
        claims = account.claims.all()
        pending_claims = claims.filter(status__in=['SUBMITTED', 'UNDER_REVIEW'])
        paid_claims = claims.filter(status='PAID')
        total_paid_expenses = sum((c.approved_amount for c in paid_claims), Decimal('0.00'))
        pending_amount = sum((c.requested_amount for c in pending_claims), Decimal('0.00'))

        # Latest transaction
        latest_txn = account.transactions.order_by('-created_at').first()

        return Response({
            'account_reference': account.account_reference,
            'patient_id': patient.patient_id,
            'patient_name': patient.full_name,
            'hac_number': patient.hac_number,
            'available_balance': float(account.available_balance),
            'total_contributions': float(account.total_contributions),
            'total_approved_withdrawals': float(account.total_approved_withdrawals),
            'total_reversals': float(account.total_reversals),
            'status': account.status,
            'default_percentage': 10.0,
            'breakdown': {
                'doctor_contributions': float(doctor_contrib),
                'pathology_contributions': float(pathology_contrib),
                'pharmacy_contributions': float(pharmacy_contrib),
            },
            'claims_summary': {
                'total_claims_count': claims.count(),
                'pending_claims_count': pending_claims.count(),
                'pending_claims_amount': float(pending_amount),
                'paid_claims_count': paid_claims.count(),
                'total_healthcare_expenses_paid': float(total_paid_expenses),
            },
            'latest_contribution': {
                'amount': float(latest_txn.amount) if latest_txn else 0.0,
                'service_category': latest_txn.service_category if latest_txn else None,
                'date': latest_txn.created_at.strftime('%Y-%m-%d %H:%M') if latest_txn else None,
            } if latest_txn else None,
            'notice': 'Your PatientCare Health Protection Fund accumulates 10% of every qualifying healthcare payment for future eligible healthcare expenses.',
        })


class HealthProtectionTransactionsView(views.APIView):
    """
    Get full auditable ledger of all transactions in patient's Health Protection Fund.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, patient_id=None):
        pid = patient_id or request.query_params.get('patient_id')
        if not pid and request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
            pid = request.user.patient_profile.patient_id

        if not pid:
            return Response({'error': 'patient_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        patient = Patient.objects.filter(patient_id__iexact=pid).first()
        if not patient and pid.isdigit():
            patient = Patient.objects.filter(id=pid).first()

        if not patient:
            return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        account = get_or_create_protection_account(patient)
        txns = account.transactions.all().order_by('-created_at')
        serializer = HealthProtectionTransactionSerializer(txns, many=True)
        return Response({
            'account_reference': account.account_reference,
            'patient_id': patient.patient_id,
            'available_balance': float(account.available_balance),
            'total_transactions': txns.count(),
            'transactions': serializer.data,
        })


class HealthProtectionRulesView(views.APIView):
    """
    List active Health Protection Fund allocation percentage rules.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ensure_default_allocation_rules()
        rules = HealthProtectionAllocationRule.objects.filter(is_active=True)
        serializer = HealthProtectionAllocationRuleSerializer(rules, many=True)
        return Response(serializer.data)


class HealthProtectionClaimListCreateView(views.APIView):
    """
    Submit and list claims against the patient's Health Protection Fund.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        pid = request.query_params.get('patient_id')
        claim_status = request.query_params.get('status')
        claims = HealthProtectionClaim.objects.all()

        if pid:
            claims = claims.filter(patient__patient_id__iexact=pid)
        elif request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
            claims = claims.filter(patient=request.user.patient_profile)

        if claim_status:
            claims = claims.filter(status__iexact=claim_status)

        serializer = HealthProtectionClaimSerializer(claims, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data
        pid = data.get('patient_id')
        if not pid and request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
            pid = request.user.patient_profile.patient_id

        if not pid:
            return Response({'error': 'patient_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        patient = Patient.objects.filter(patient_id__iexact=pid).first()
        if not patient and str(pid).isdigit():
            patient = Patient.objects.filter(id=pid).first()

        if not patient:
            return Response({'error': 'Patient not found.'}, status=status.HTTP_404_NOT_FOUND)

        account = get_or_create_protection_account(patient)

        raw_amount = data.get('requested_amount') or data.get('claimed_amount') or data.get('amount', 0)
        try:
            req_amount = Decimal(str(raw_amount))
        except Exception:
            return Response({'error': 'Invalid requested_amount format.'}, status=status.HTTP_400_BAD_REQUEST)

        if req_amount <= Decimal('0.00'):
            return Response({'error': 'Requested amount must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)

        if req_amount > account.available_balance:
            return Response({
                'error': f'Requested amount (₹{req_amount}) exceeds available protection balance (₹{account.available_balance}).'
            }, status=status.HTTP_400_BAD_REQUEST)

        provider_name = data.get('provider_name', '').strip() or 'Empanelled Healthcare Provider'
        invoice_date = data.get('invoice_date') or data.get('service_date') or timezone.now().date()

        count = HealthProtectionClaim.objects.count() + 1
        ref = f"HPC-{timezone.now().strftime('%Y%m%d')}-{count:05d}"
        while HealthProtectionClaim.objects.filter(claim_reference=ref).exists():
            count += 1
            ref = f"HPC-{timezone.now().strftime('%Y%m%d')}-{count:05d}"

        claim = HealthProtectionClaim.objects.create(
            claim_reference=ref,
            patient=patient,
            protection_account=account,
            expense_category=data.get('expense_category', 'Doctor Consultation'),
            requested_amount=req_amount,
            provider_name=provider_name,
            invoice_number=data.get('invoice_number', ''),
            invoice_date=invoice_date,
            description=data.get('description', ''),
            supporting_documents=data.get('supporting_documents', ''),
            status='SUBMITTED'
        )

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            'PATIENT',
            f'Submitted Health Protection claim {claim.claim_reference} for ₹{req_amount} ({claim.expense_category})',
            patient_id=patient.patient_id,
            request=request
        )

        return Response({
            'message': 'Healthcare expense claim submitted successfully. Status: SUBMITTED (Under Review).',
            'claim': HealthProtectionClaimSerializer(claim).data
        }, status=status.HTTP_201_CREATED)


class HealthProtectionClaimDetailReviewView(views.APIView):
    """
    View claim detail and process reviewer decision (APPROVE, REJECT, PAY).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, claim_reference):
        claim = HealthProtectionClaim.objects.filter(claim_reference=claim_reference).first()
        if not claim:
            return Response({'error': 'Claim not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(HealthProtectionClaimSerializer(claim).data)

    def post(self, request, claim_reference):
        claim = HealthProtectionClaim.objects.filter(claim_reference=claim_reference).first()
        if not claim:
            return Response({'error': 'Claim not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action', '').upper()
        review_notes = request.data.get('review_notes', '')

        if action in ['UNDER_REVIEW', 'REVIEW']:
            claim.status = 'UNDER_REVIEW'
            claim.review_notes = review_notes
            claim.reviewer = request.user if request.user.is_authenticated else None
            claim.reviewed_at = timezone.now()
            claim.save()
            return Response({'message': 'Claim marked Under Review.', 'claim': HealthProtectionClaimSerializer(claim).data})

        elif action == 'APPROVE':
            try:
                approved_amt = Decimal(str(request.data.get('approved_amount', claim.requested_amount)))
            except Exception:
                approved_amt = claim.requested_amount
            claim.status = 'APPROVED'
            claim.approved_amount = approved_amt
            claim.review_notes = review_notes
            claim.reviewer = request.user if request.user.is_authenticated else None
            claim.reviewed_at = timezone.now()
            claim.save()
            return Response({'message': f'Claim approved for ₹{approved_amt}. Ready for disbursement.', 'claim': HealthProtectionClaimSerializer(claim).data})

        elif action == 'REJECT':
            claim.status = 'REJECTED'
            claim.review_notes = review_notes
            claim.reviewer = request.user if request.user.is_authenticated else None
            claim.reviewed_at = timezone.now()
            claim.save()
            return Response({'message': 'Claim rejected.', 'claim': HealthProtectionClaimSerializer(claim).data})

        elif action in ['PAY', 'APPROVE_AND_PAY']:
            try:
                approved_amt = Decimal(str(request.data.get('approved_amount', claim.requested_amount)))
                result = settle_health_protection_claim(
                    claim=claim,
                    approved_amount=approved_amt,
                    reviewer=request.user if request.user.is_authenticated else None,
                    review_notes=review_notes
                )
                return Response({
                    'message': f'Claim {claim.claim_reference} paid successfully. ₹{approved_amt} disbursed.',
                    'claim': HealthProtectionClaimSerializer(result['claim']).data,
                    'remaining_balance': float(result['remaining_balance']),
                })
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'error': f"Invalid action '{action}'. Use UNDER_REVIEW, APPROVE, REJECT, or PAY."}, status=status.HTTP_400_BAD_REQUEST)

