from django.urls import path
from .views import (
    GovernmentSchemeListCreateView,
    GovernmentSchemeDetailView,
    GovernmentDashboardStatsView,
    SchemeApplicationView
)

urlpatterns = [
    path('schemes/', GovernmentSchemeListCreateView.as_view(), name='government-schemes'),
    path('schemes/<int:pk>/', GovernmentSchemeDetailView.as_view(), name='government-scheme-detail'),
    path('stats/', GovernmentDashboardStatsView.as_view(), name='government-stats'),
    path('applications/', SchemeApplicationView.as_view(), name='scheme-applications'),
    path('applications/<str:application_id>/', SchemeApplicationView.as_view(), name='scheme-application-detail'),
]
