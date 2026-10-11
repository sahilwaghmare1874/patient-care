from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from django.utils import timezone
import datetime
from .models import User, OTPVerification, DoctorProfile, PathologyProfile, PharmacyProfile, AuditLog
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    DoctorProfileSerializer, PathologyProfileSerializer, PharmacyProfileSerializer,
    AuditLogSerializer
)

def create_audit_log(user, role, action, patient_id="", details="", request=None):
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        role=role or (user.role if user and user.is_authenticated else 'SYSTEM'),
        action=action,
        patient_id=patient_id,
        ip_address=ip_address,
        details=details
    )


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        create_audit_log(user, user.role, f"Registered new account: {user.username}", request=request)
        return Response({
            "message": "Registration successful. You can now login.",
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = data['user']

        profile_data = {}
        if user.role == 'DOCTOR' and hasattr(user, 'doctor_profile'):
            profile_data = DoctorProfileSerializer(user.doctor_profile).data
        elif user.role == 'PATHOLOGY' and hasattr(user, 'pathology_profile'):
            profile_data = PathologyProfileSerializer(user.pathology_profile).data
        elif user.role == 'PHARMACY' and hasattr(user, 'pharmacy_profile'):
            profile_data = PharmacyProfileSerializer(user.pharmacy_profile).data
        elif user.role == 'PATIENT' and hasattr(user, 'patient_profile'):
            from patients.serializers import PatientSerializer
            profile_data = PatientSerializer(user.patient_profile).data

        create_audit_log(user, user.role, f"User logged in: {user.username}", request=request)

        return Response({
            "message": "Login successful.",
            "access": data['access'],
            "refresh": data['refresh'],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "mobile": user.mobile,
                "role": user.role,
                "is_verified": user.is_verified,
                "profile": profile_data
            }
        }, status=status.HTTP_200_OK)


class SendOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = request.data.get('identifier', '').strip()
        purpose = request.data.get('purpose', 'REGISTRATION')

        if not identifier:
            return Response({"error": "Mobile number or Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Standard predictable OTP for ease of testing / demo or generate random
        otp_code = '123456'
        expires_at = timezone.now() + datetime.timedelta(minutes=10)

        OTPVerification.objects.create(
            identifier=identifier,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=expires_at
        )

        return Response({
            "message": f"Verification OTP sent to {identifier}.",
            "otp_demo": otp_code,
            "expires_in_minutes": 10
        }, status=status.HTTP_200_OK)


class VerifyOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        identifier = request.data.get('identifier', '').strip()
        otp = request.data.get('otp', '').strip()

        record = OTPVerification.objects.filter(
            identifier=identifier,
            otp_code=otp,
            is_verified=False
        ).order_by('-created_at').first()

        if record and record.is_valid():
            record.is_verified = True
            record.save()
            return Response({"success": True, "message": "OTP verified successfully."}, status=status.HTTP_200_OK)

        return Response({"success": False, "error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(views.APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"authenticated": False}, status=status.HTTP_200_OK)

        user = request.user
        profile_data = {}
        if user.role == 'DOCTOR' and hasattr(user, 'doctor_profile'):
            profile_data = DoctorProfileSerializer(user.doctor_profile).data
        elif user.role == 'PATHOLOGY' and hasattr(user, 'pathology_profile'):
            profile_data = PathologyProfileSerializer(user.pathology_profile).data
        elif user.role == 'PHARMACY' and hasattr(user, 'pharmacy_profile'):
            profile_data = PharmacyProfileSerializer(user.pharmacy_profile).data
        elif user.role == 'PATIENT' and hasattr(user, 'patient_profile'):
            from patients.serializers import PatientSerializer
            profile_data = PatientSerializer(user.patient_profile).data

        return Response({
            "authenticated": True,
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "mobile": user.mobile,
            "role": user.role,
            "is_verified": user.is_verified,
            "profile": profile_data
        })


class VerifyProviderView(views.APIView):
    def post(self, request, provider_type, provider_id):
        # Admin or Government can verify doctors/labs/pharmacies
        if provider_type == 'doctor':
            obj = DoctorProfile.objects.filter(doctor_id=provider_id).first()
        elif provider_type == 'pathology':
            obj = PathologyProfile.objects.filter(lab_id=provider_id).first()
        elif provider_type == 'pharmacy':
            obj = PharmacyProfile.objects.filter(pharmacy_id=provider_id).first()
        else:
            return Response({"error": "Invalid provider type."}, status=status.HTTP_400_BAD_REQUEST)

        if not obj:
            return Response({"error": "Provider not found."}, status=status.HTTP_404_NOT_FOUND)

        obj.is_approved = True
        obj.save()
        obj.user.is_verified = True
        obj.user.save()

        create_audit_log(request.user, "ADMIN", f"Verified provider {provider_type}: {provider_id}", request=request)
        return Response({"message": f"{provider_type.capitalize()} {provider_id} verified successfully."})


class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.AllowAny]
