from django.urls import path
from .views import (
    CentralizedPatientReportView,
    PDFReportDownloadView,
    CSVReportDownloadView,
    AIPatientAssistantChatView,
    AIExplainReportView,
    AIDuplicateClaimDetectorView,
    CentralizedFinancialReportingView
)

urlpatterns = [
    path('patient/<str:patient_id>/', CentralizedPatientReportView.as_view(), name='report-patient'),
    path('fund/<str:patient_id>/', CentralizedPatientReportView.as_view(), name='report-fund'),
    path('pdf/<str:patient_id>/', PDFReportDownloadView.as_view(), name='report-pdf'),
    path('csv/<str:patient_id>/', CSVReportDownloadView.as_view(), name='report-csv'),
    # Phase 7 & 11: AI Assistant & Centralized Financial Reporting
    path('ai/chat/', AIPatientAssistantChatView.as_view(), name='ai-chat'),
    path('ai/explain/', AIExplainReportView.as_view(), name='ai-explain'),
    path('ai/audit-claims/', AIDuplicateClaimDetectorView.as_view(), name='ai-audit-claims'),
    path('financial-overview/', CentralizedFinancialReportingView.as_view(), name='financial-overview'),
]
