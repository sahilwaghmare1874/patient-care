from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OTPVerification, DoctorProfile, PathologyProfile, PharmacyProfile, AuditLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'mobile', 'role', 'is_verified', 'created_at')


class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = '__all__'


class PathologyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathologyProfile
        fields = '__all__'


class PharmacyProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyProfile
        fields = '__all__'


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    full_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    hospital_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    specialization = serializers.CharField(write_only=True, required=False, allow_blank=True)
    registration_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    qualification = serializers.CharField(write_only=True, required=False, allow_blank=True)
    lab_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    license_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    pharmacy_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    pharmacist_name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'mobile', 'role', 'password', 'confirm_password',
            'full_name', 'hospital_name', 'specialization', 'registration_number',
            'qualification', 'lab_name', 'license_number', 'pharmacy_name',
            'pharmacist_name', 'address'
        )

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('confirm_password', None)
        role = validated_data.get('role', 'PATIENT')

        # Extract provider-specific fields
        full_name = validated_data.pop('full_name', '')
        hospital_name = validated_data.pop('hospital_name', '')
        specialization = validated_data.pop('specialization', '')
        registration_number = validated_data.pop('registration_number', '')
        qualification = validated_data.pop('qualification', '')
        lab_name = validated_data.pop('lab_name', '')
        license_number = validated_data.pop('license_number', '')
        pharmacy_name = validated_data.pop('pharmacy_name', '')
        pharmacist_name = validated_data.pop('pharmacist_name', '')
        address = validated_data.pop('address', '')

        # Auto-verify patients and admin; providers require admin/gov verification
        is_verified = True if role in ('PATIENT', 'ADMIN', 'GOVERNMENT') else False

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            mobile=validated_data.get('mobile', ''),
            role=role,
            is_verified=is_verified
        )
        user.set_password(password)
        user.save()

        # Create role-specific profiles
        if role == 'DOCTOR':
            count = DoctorProfile.objects.count() + 1
            DoctorProfile.objects.create(
                user=user,
                doctor_id=f"DOC-2026-{count:04d}",
                full_name=full_name or user.username,
                qualification=qualification or "MBBS, MD",
                specialization=specialization or "General Medicine",
                registration_number=registration_number or f"REG-DOC-{count:04d}",
                hospital_name=hospital_name or "Apex Multi-Speciality Hospital",
                contact_number=user.mobile or "9876543210",
                email=user.email,
                address=address or "Medical Council Avenue",
                is_approved=True # Demo auto-approved or pending verification
            )
        elif role == 'PATHOLOGY':
            count = PathologyProfile.objects.count() + 1
            PathologyProfile.objects.create(
                user=user,
                lab_id=f"LAB-2026-{count:04d}",
                lab_name=lab_name or f"{user.username} Diagnostics",
                license_number=license_number or f"LIC-LAB-{count:04d}",
                owner_name=full_name or user.username,
                contact_number=user.mobile or "9876543210",
                email=user.email,
                address=address or "Diagnostic Center Street",
                is_approved=True
            )
        elif role == 'PHARMACY':
            count = PharmacyProfile.objects.count() + 1
            PharmacyProfile.objects.create(
                user=user,
                pharmacy_id=f"PHARM-2026-{count:04d}",
                pharmacy_name=pharmacy_name or f"{user.username} Chemists",
                license_number=license_number or f"LIC-PHARM-{count:04d}",
                pharmacist_name=pharmacist_name or full_name or user.username,
                contact_number=user.mobile or "9876543210",
                email=user.email,
                address=address or "Pharmacy Market Street",
                is_approved=True
            )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    otp = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        username_input = data.get('username')
        password = data.get('password')

        # Support login by username, email, or mobile
        user = None
        if '@' in username_input:
            user = User.objects.filter(email=username_input).first()
        elif username_input.isdigit():
            user = User.objects.filter(mobile=username_input).first()
        else:
            user = User.objects.filter(username=username_input).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials. Please verify your username and password.")

        if not user.is_active:
            raise serializers.ValidationError("Account is inactive.")

        refresh = RefreshToken.for_user(user)
        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = AuditLog
        fields = '__all__'
