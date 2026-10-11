from django.urls import path
from .views import (
    PathologyTestListView,
    PathologyReportListCreateView,
    PathologyDashboardStatsView
)

urlpatterns = [
    path('tests/', PathologyTestListView.as_view(), name='pathology-test-list'),
    path('reports/', PathologyReportListCreateView.as_view(), name='pathology-report-list-create'),
    path('stats/', PathologyDashboardStatsView.as_view(), name='pathology-stats'),
]
