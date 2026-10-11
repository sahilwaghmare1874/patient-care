from django.urls import path
from .views import (
    ConsultationListCreateView,
    PrescriptionListView,
    DoctorDashboardStatsView,
    DoctorListView,
    AppointmentListCreateView,
    AppointmentTokenView,
    TokenQueueView,
    CallNextTokenView,
    AISymptomRecommendationView,
    DoctorRecommendationView,
)

urlpatterns = [
    path('consultations/', ConsultationListCreateView.as_view(), name='consultation-list-create'),
    path('prescriptions/', PrescriptionListView.as_view(), name='prescription-list'),
    path('stats/', DoctorDashboardStatsView.as_view(), name='doctor-stats'),
    path('list/', DoctorListView.as_view(), name='doctor-list'),
    path('appointments/', AppointmentListCreateView.as_view(), name='appointment-list-create'),
    path('appointments/<str:appointment_id>/', AppointmentListCreateView.as_view(), name='appointment-detail'),
    path('token/<str:appointment_id>/', AppointmentTokenView.as_view(), name='appointment-token'),
    path('queue/', TokenQueueView.as_view(), name='token-queue'),
    path('queue/call-next/', CallNextTokenView.as_view(), name='call-next-token'),
    path('ai/recommend/', AISymptomRecommendationView.as_view(), name='ai-recommend'),
    path('recommendations/', DoctorRecommendationView.as_view(), name='doctor-recommendations'),
]
