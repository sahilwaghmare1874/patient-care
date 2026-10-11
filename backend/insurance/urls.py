from django.urls import path
from .views import (
    InsuranceCompanyListView,
    InsurancePolicyListView,
    InsuranceClaimListCreateView,
    InsuranceClaimDetailView
)

urlpatterns = [
    path('companies/', InsuranceCompanyListView.as_view(), name='insurance-companies'),
    path('policies/', InsurancePolicyListView.as_view(), name='insurance-policies'),
    path('claims/', InsuranceClaimListCreateView.as_view(), name='insurance-claims'),
    path('claims/<str:claim_id>/', InsuranceClaimDetailView.as_view(), name='insurance-claim-detail'),
]
