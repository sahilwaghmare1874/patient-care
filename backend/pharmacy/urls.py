from django.urls import path
from .views import (
    MedicineListView,
    PharmacyTransactionListCreateView,
    PharmacyDashboardStatsView
)

urlpatterns = [
    path('medicines/', MedicineListView.as_view(), name='medicine-list'),
    path('transactions/', PharmacyTransactionListCreateView.as_view(), name='pharmacy-transactions'),
    path('stats/', PharmacyDashboardStatsView.as_view(), name='pharmacy-stats'),
]
