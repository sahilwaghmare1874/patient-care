from django.urls import path
from .views import (
    PatientListCreateView, PatientDetailView,
    PatientLookupView, PatientCentralizedRecordView
)

urlpatterns = [
    path('', PatientListCreateView.as_view(), name='patient-list-create'),
    path('lookup/', PatientLookupView.as_view(), name='patient-lookup'),
    path('<str:identifier>/', PatientDetailView.as_view(), name='patient-detail'),
    path('<str:identifier>/centralized-record/', PatientCentralizedRecordView.as_view(), name='patient-centralized-record'),
]
