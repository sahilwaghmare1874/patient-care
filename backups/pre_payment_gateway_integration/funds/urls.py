from django.urls import path
from .views import (
    AllocationConfigurationView, FundAllocationListCreateView, FundAllocationDetailView,
    ReserveAccountView, ReserveLedgerView, ReserveCreditView,
    HealthProtectionAccountView, HealthProtectionTransactionsView,
    HealthProtectionRulesView, HealthProtectionClaimListCreateView,
    HealthProtectionClaimDetailReviewView,
)

urlpatterns = [
    # Support both /config/ and /configuration/
    path('config/', AllocationConfigurationView.as_view(), name='fund-config'),
    path('configuration/', AllocationConfigurationView.as_view(), name='fund-configuration'),
    # Support both /allocations/ and /allocate/
    path('allocations/', FundAllocationListCreateView.as_view(), name='fund-allocations'),
    path('allocate/', FundAllocationListCreateView.as_view(), name='fund-allocate'),
    path('allocations/<str:allocation_id>/', FundAllocationDetailView.as_view(), name='fund-allocation-detail'),
    # PatientCare Health Protection Fund (10% Automatic Core Policy)
    path('protection-account/', HealthProtectionAccountView.as_view(), name='protection-account'),
    path('protection-account/<str:patient_id>/', HealthProtectionAccountView.as_view(), name='protection-account-detail'),
    path('protection-transactions/', HealthProtectionTransactionsView.as_view(), name='protection-transactions'),
    path('protection-transactions/<str:patient_id>/', HealthProtectionTransactionsView.as_view(), name='protection-transactions-detail'),
    path('protection-rules/', HealthProtectionRulesView.as_view(), name='protection-rules'),
    path('claims/', HealthProtectionClaimListCreateView.as_view(), name='protection-claims'),
    path('claims/<str:claim_reference>/', HealthProtectionClaimDetailReviewView.as_view(), name='protection-claim-detail'),
    path('claims/<str:claim_reference>/review/', HealthProtectionClaimDetailReviewView.as_view(), name='protection-claim-review'),
    # Legacy Reserve Account compatibility
    path('reserve/credit/', ReserveCreditView.as_view(), name='reserve-credit'),
    path('reserve/<str:patient_id>/ledger/', ReserveLedgerView.as_view(), name='reserve-ledger'),
    path('reserve/<str:patient_id>/', ReserveAccountView.as_view(), name='reserve-account'),
]

