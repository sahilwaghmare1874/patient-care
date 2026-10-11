from django.urls import path
from .views import (
    RegisterView, LoginView, SendOTPView, VerifyOTPView,
    CurrentUserView, VerifyProviderView, AuditLogListView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('verify-provider/<str:provider_type>/<str:provider_id>/', VerifyProviderView.as_view(), name='verify-provider'),
    path('audit-logs/', AuditLogListView.as_view(), name='audit-logs'),
]
