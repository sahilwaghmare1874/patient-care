from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.db import models
from .models import Appointment, Consultation, Prescription
from .serializers import AppointmentSerializer, ConsultationSerializer, PrescriptionSerializer
from patients.models import Patient
from accounts.models import DoctorProfile
from accounts.views import create_audit_log
from notifications.models import Notification

class ConsultationListCreateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        doctor_id = request.query_params.get('doctor_id')
        consultations = Consultation.objects.all()

        if patient_id:
            consultations = consultations.filter(patient__patient_id__iexact=patient_id)
        if doctor_id:
            consultations = consultations.filter(doctor__doctor_id__iexact=doctor_id)

        serializer = ConsultationSerializer(consultations, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        patient_id_input = data.pop('patient_id', None)
        if isinstance(patient_id_input, list):
            patient_id_input = patient_id_input[0]

        patient = None
        if patient_id_input:
            patient = Patient.objects.filter(patient_id__iexact=patient_id_input).first()
        if not patient and 'patient' in data:
            patient = Patient.objects.filter(id=data['patient']).first()

        if not patient:
            return Response({"error": "Valid patient is required. Search patient first."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve Doctor profile
        doctor = None
        if request.user.is_authenticated and hasattr(request.user, 'doctor_profile'):
            doctor = request.user.doctor_profile
        else:
            doctor_id_input = data.pop('doctor_id', None)
            if doctor_id_input:
                doctor = DoctorProfile.objects.filter(doctor_id__iexact=doctor_id_input).first()
            if not doctor:
                doctor = DoctorProfile.objects.first()

        if not doctor:
            return Response({"error": "Doctor profile not found."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate unique Consultation ID
        count = Consultation.objects.count() + 1
        consultation_id = f"CON-2026-{count:04d}"

        prescribed_meds = data.pop('prescribed_medicines', '')

        consultation = Consultation.objects.create(
            consultation_id=consultation_id,
            patient=patient,
            doctor=doctor,
            visit_date=data.get('visit_date') or timezone.now().date(),
            symptoms=data.get('symptoms', 'Consultation'),
            diagnosis=data.get('diagnosis', 'Clinical assessment'),
            doctor_notes=data.get('doctor_notes', ''),
            treatment_plan=data.get('treatment_plan', ''),
            operation_recommended=bool(data.get('operation_recommended', False)),
            operation_details=data.get('operation_details', ''),
            pathology_referral=bool(data.get('pathology_referral', False)),
            pathology_tests_recommended=data.get('pathology_tests_recommended', ''),
            pharmacy_referral=bool(data.get('pharmacy_referral', True)),
            consultation_fee=data.get('consultation_fee', 500.00)
        )

        # Automatically generate Prescription if medicines provided
        if prescribed_meds:
            rx_count = Prescription.objects.count() + 1
            rx_id = f"RX-2026-{rx_count:04d}"
            Prescription.objects.create(
                prescription_id=rx_id,
                consultation=consultation,
                patient=patient,
                doctor=doctor,
                medicines=prescribed_meds,
                instructions=consultation.doctor_notes or "Take medications as directed.",
                date_prescribed=consultation.visit_date
            )

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "DOCTOR",
            f"Created clinical consultation: {consultation.consultation_id} for {patient.patient_id}",
            patient_id=patient.patient_id,
            request=request
        )

        if patient.user:
            Notification.objects.create(
                recipient=patient.user,
                title="New Doctor Consultation Recorded",
                message=f"Dr. {doctor.full_name} recorded a consultation with diagnosis: '{consultation.diagnosis}'.",
                notification_type="CONSULTATION"
            )

        return Response({
            "message": "Consultation successfully saved.",
            "consultation": ConsultationSerializer(consultation).data
        }, status=status.HTTP_201_CREATED)


class PrescriptionListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = PrescriptionSerializer

    def get_queryset(self):
        qs = Prescription.objects.all()
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            qs = qs.filter(patient__patient_id__iexact=patient_id)
        return qs


class DoctorDashboardStatsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_patients = Patient.objects.count()
        total_consultations = Consultation.objects.count()
        total_prescriptions = Prescription.objects.count()
        today = timezone.now().date()
        today_consultations = Consultation.objects.filter(visit_date=today).count()

        return Response({
            "total_patients": total_patients,
            "total_consultations": total_consultations,
            "today_consultations": today_consultations,
            "total_prescriptions": total_prescriptions,
            "recent_consultations": ConsultationSerializer(Consultation.objects.all()[:5], many=True).data
        })


import uuid
import json
import urllib.request
import urllib.parse
from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from .models import DoctorAvailability, AppointmentToken


class DoctorListView(views.APIView):
    """List all approved doctors with availability and consultation fees."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        specialization = request.query_params.get('specialization', '').strip()
        doctors = DoctorProfile.objects.filter(is_approved=True)
        if specialization:
            doctors = doctors.filter(specialization__icontains=specialization)

        result = []
        for doc in doctors:
            availability = list(doc.availability_slots.filter(is_active=True).values(
                'id', 'day_of_week', 'start_time', 'end_time', 'max_appointments', 'consultation_fee'
            ))
            # Convert time fields to string
            for slot in availability:
                slot['start_time'] = str(slot['start_time'])[:5]
                slot['end_time'] = str(slot['end_time'])[:5]
            result.append({
                'doctor_id': doc.doctor_id,
                'full_name': doc.full_name,
                'qualification': doc.qualification,
                'specialization': doc.specialization,
                'registration_number': doc.registration_number,
                'experience_years': doc.experience_years,
                'hospital_name': doc.hospital_name,
                'contact_number': doc.contact_number,
                'email': doc.email,
                'availability': availability,
                'default_fee': float(availability[0]['consultation_fee']) if availability else 500.0,
            })
        return Response(result)


class AppointmentListCreateView(views.APIView):
    """Create or list appointments. Token generation is atomic."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, appointment_id=None):
        patient_id = request.query_params.get('patient_id')
        doctor_id = request.query_params.get('doctor_id')
        appointments = Appointment.objects.select_related('patient', 'doctor', 'token').all()
        if patient_id:
            appointments = appointments.filter(patient__patient_id__iexact=patient_id)
        if doctor_id:
            appointments = appointments.filter(doctor__doctor_id__iexact=doctor_id)
        if appointment_id:
            appt = appointments.filter(appointment_id=appointment_id).first()
            if not appt:
                return Response({'error': 'Appointment not found.'}, status=404)
            return Response(self._serialize(appt))
        return Response([self._serialize(a) for a in appointments])

    def _serialize(self, appt):
        token = None
        if hasattr(appt, 'token'):
            t = appt.token
            token = {
                'token_number': t.token_number,
                'status': t.status,
                'called_at': str(t.called_at) if t.called_at else None,
            }
        return {
            'appointment_id': appt.appointment_id,
            'patient_id': appt.patient.patient_id,
            'patient_name': appt.patient.full_name,
            'doctor_id': appt.doctor.doctor_id,
            'doctor_name': appt.doctor.full_name,
            'doctor_specialization': appt.doctor.specialization,
            'appointment_date': str(appt.appointment_date),
            'time_slot': appt.time_slot,
            'symptoms': appt.symptoms,
            'status': appt.status,
            'token': token,
            'created_at': str(appt.created_at),
        }

    @db_transaction.atomic
    def post(self, request, appointment_id=None):
        if appointment_id:
            # Update (cancel/reschedule)
            appt = Appointment.objects.select_for_update().filter(appointment_id=appointment_id).first()
            if not appt:
                return Response({'error': 'Appointment not found.'}, status=404)
            new_status = request.data.get('status')
            new_date = request.data.get('appointment_date')
            if new_status in ['Cancelled', 'Completed']:
                appt.status = new_status
                if hasattr(appt, 'token'):
                    appt.token.status = 'Cancelled' if new_status == 'Cancelled' else 'Completed'
                    appt.token.save()
                appt.save()
                if appt.patient.user:
                    Notification.objects.create(
                        recipient=appt.patient.user,
                        title=f'Appointment {new_status}',
                        message=f'Your appointment {appt.appointment_id} with Dr. {appt.doctor.full_name} has been {new_status.lower()}.',
                        notification_type='APPOINTMENT'
                    )
            if new_date:
                appt.appointment_date = new_date
                appt.status = 'Scheduled'
                appt.save()
            return Response({'message': 'Appointment updated.', 'appointment': self._serialize(appt)})

        # Create new appointment
        patient_id = request.data.get('patient_id', '')
        doctor_id = request.data.get('doctor_id', '')
        appt_date = request.data.get('appointment_date')
        time_slot = request.data.get('time_slot', '10:00 AM - 10:30 AM')
        symptoms = request.data.get('symptoms', '')
        idempotency_key = request.data.get('idempotency_key') or str(uuid.uuid4())

        # Check idempotency — prevent duplicate submissions
        existing_token = AppointmentToken.objects.filter(idempotency_key=idempotency_key).first()
        if existing_token:
            return Response({
                'message': 'Appointment already booked (idempotent).',
                'appointment': self._serialize(existing_token.appointment)
            })

        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient:
            return Response({'error': 'Patient not found.'}, status=400)

        doctor = DoctorProfile.objects.filter(doctor_id__iexact=doctor_id, is_approved=True).first()
        if not doctor:
            return Response({'error': 'Doctor not found or not approved.'}, status=400)

        if not appt_date:
            return Response({'error': 'appointment_date is required.'}, status=400)

        # Generate unique appointment ID
        from datetime import date
        from django.db.models import Max
        import hashlib
        count = Appointment.objects.count() + 1
        appt_id = f'APT-{date.today().strftime("%Y%m%d")}-{count:04d}'
        while Appointment.objects.filter(appointment_id=appt_id).exists():
            count += 1
            appt_id = f'APT-{date.today().strftime("%Y%m%d")}-{count:04d}'

        appt = Appointment.objects.create(
            appointment_id=appt_id,
            patient=patient,
            doctor=doctor,
            appointment_date=appt_date,
            time_slot=time_slot,
            symptoms=symptoms,
            status='Scheduled'
        )

        # Atomic token generation — SELECT FOR UPDATE prevents race conditions
        from django.db.models import Max
        from datetime import date as date_type
        session_date = appt_date if isinstance(appt_date, date_type) else date_type.fromisoformat(str(appt_date))
        max_token = AppointmentToken.objects.select_for_update().filter(
            doctor=doctor, session_date=session_date
        ).aggregate(Max('token_number'))['token_number__max'] or 0
        token_number = max_token + 1

        AppointmentToken.objects.create(
            token_number=token_number,
            appointment=appt,
            doctor=doctor,
            session_date=session_date,
            status='Waiting',
            idempotency_key=idempotency_key
        )

        # Notifications
        if patient.user:
            Notification.objects.create(
                recipient=patient.user,
                title='Appointment Confirmed',
                message=f'Your appointment with Dr. {doctor.full_name} ({doctor.specialization}) is confirmed for {appt_date}. Token #{token_number}.',
                notification_type='APPOINTMENT'
            )
        if doctor.user:
            Notification.objects.create(
                recipient=doctor.user,
                title='New Appointment Booked',
                message=f'Patient {patient.full_name} booked for {appt_date} (Token #{token_number}).',
                notification_type='APPOINTMENT'
            )

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            'PATIENT',
            f'Appointment {appt_id} booked for {patient.patient_id} with {doctor.doctor_id}. Token #{token_number}.',
            patient_id=patient.patient_id,
            request=request
        )

        return Response({
            'message': f'Appointment confirmed! Token #{token_number} assigned.',
            'appointment': self._serialize(appt)
        }, status=201)


class AppointmentTokenView(views.APIView):
    """Get token status for a specific appointment."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, appointment_id):
        appt = Appointment.objects.filter(appointment_id=appointment_id).first()
        if not appt:
            return Response({'error': 'Appointment not found.'}, status=404)
        if not hasattr(appt, 'token'):
            return Response({'error': 'No token generated for this appointment.'}, status=404)
        t = appt.token
        return Response({
            'token_number': t.token_number,
            'status': t.status,
            'session_date': str(t.session_date),
            'called_at': str(t.called_at) if t.called_at else None,
            'appointment_id': appointment_id,
            'doctor_name': appt.doctor.full_name,
            'specialization': appt.doctor.specialization,
        })


class TokenQueueView(views.APIView):
    """Get the queue for a doctor on a given date."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        doctor_id = request.query_params.get('doctor_id')
        date_param = request.query_params.get('date', str(timezone.now().date()))
        if not doctor_id:
            return Response({'error': 'doctor_id is required.'}, status=400)
        doctor = DoctorProfile.objects.filter(doctor_id__iexact=doctor_id).first()
        if not doctor:
            return Response({'error': 'Doctor not found.'}, status=404)
        tokens = AppointmentToken.objects.filter(
            doctor=doctor, session_date=date_param
        ).select_related('appointment__patient').order_by('token_number')
        queue = []
        for t in tokens:
            queue.append({
                'token_number': t.token_number,
                'patient_id': t.appointment.patient.patient_id,
                'patient_name': t.appointment.patient.full_name,
                'appointment_id': t.appointment.appointment_id,
                'time_slot': t.appointment.time_slot,
                'symptoms': t.appointment.symptoms,
                'status': t.status,
                'called_at': str(t.called_at) if t.called_at else None,
            })
        waiting = [q for q in queue if q['status'] == 'Waiting']
        in_progress = [q for q in queue if q['status'] == 'In Consultation']
        return Response({
            'doctor': doctor_id,
            'date': date_param,
            'total_tokens': len(queue),
            'waiting_count': len(waiting),
            'current_token': in_progress[0] if in_progress else None,
            'next_token': waiting[0] if waiting else None,
            'queue': queue,
        })


class CallNextTokenView(views.APIView):
    """Doctor or authorized staff calls the next patient token."""
    permission_classes = [permissions.AllowAny]

    @db_transaction.atomic
    def post(self, request):
        doctor_id = request.data.get('doctor_id')
        token_number = request.data.get('token_number')
        action = request.data.get('action', 'call')  # call | complete | no_show
        date_param = request.data.get('date', str(timezone.now().date()))

        doctor = DoctorProfile.objects.filter(doctor_id__iexact=doctor_id).first()
        if not doctor:
            return Response({'error': 'Doctor not found.'}, status=404)

        # If token_number not provided, get next waiting
        if token_number:
            token = AppointmentToken.objects.select_for_update().filter(
                doctor=doctor, session_date=date_param, token_number=token_number
            ).first()
        else:
            token = AppointmentToken.objects.select_for_update().filter(
                doctor=doctor, session_date=date_param, status='Waiting'
            ).order_by('token_number').first()

        if not token:
            return Response({'error': 'No waiting token found.'}, status=404)

        # Mark previous In Consultation as Completed
        AppointmentToken.objects.filter(
            doctor=doctor, session_date=date_param, status='In Consultation'
        ).update(status='Completed', completed_at=timezone.now())

        if action == 'call':
            token.status = 'In Consultation'
            token.called_at = timezone.now()
            token.save()
            # Notify patient that their token has been called
            patient = token.appointment.patient
            if patient.user:
                Notification.objects.create(
                    recipient=patient.user,
                    title=f'Your Turn — Token #{token.token_number}',
                    message=f'Dr. {doctor.full_name} is calling Token #{token.token_number}. Please proceed to the consultation room.',
                    notification_type='TOKEN_CALLED'
                )
        elif action == 'complete':
            token.status = 'Completed'
            token.completed_at = timezone.now()
            token.save()
        elif action == 'no_show':
            token.status = 'No Show'
            token.save()

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            'DOCTOR',
            f'{action.upper()} Token #{token.token_number} for doctor {doctor_id} on {date_param}',
            patient_id=token.appointment.patient.patient_id,
            request=request
        )

        return Response({
            'message': f'Token #{token.token_number} {action} successful.',
            'token_number': token.token_number,
            'status': token.status,
            'patient_name': token.appointment.patient.full_name,
        })


class AISymptomRecommendationView(views.APIView):
    """AI-based symptom to specialty recommendation. Does NOT diagnose or prescribe."""
    permission_classes = [permissions.AllowAny]

    # Safety: never recommend for these red-flag symptoms without urgent care advice
    RED_FLAG_SYMPTOMS = [
        'chest pain', 'heart attack', 'stroke', 'seizure', 'unconscious', 'breathing difficulty',
        'severe bleeding', 'head injury', 'paralysis', 'anaphylaxis', 'overdose', 'suicidal',
        'difficulty breathing', 'shortness of breath'
    ]

    SYMPTOM_SPECIALTY_MAP = {
        # Fallback rule-based map when AI is unavailable
        'headache': {'specialty': 'Neurology', 'reason': 'Headaches may require neurological evaluation.'},
        'migraine': {'specialty': 'Neurology', 'reason': 'Migraines are managed by neurologists.'},
        'fever': {'specialty': 'General Medicine', 'reason': 'Fever evaluation by a general physician.'},
        'cough': {'specialty': 'Pulmonology', 'reason': 'Persistent cough evaluated by a pulmonologist.'},
        'chest pain': {'specialty': 'Cardiology', 'reason': 'Chest pain needs urgent cardiac evaluation.', 'urgent': True},
        'heart': {'specialty': 'Cardiology', 'reason': 'Heart-related symptoms require a cardiologist.'},
        'stomach': {'specialty': 'Gastroenterology', 'reason': 'Stomach issues evaluated by a gastroenterologist.'},
        'skin': {'specialty': 'Dermatology', 'reason': 'Skin conditions managed by a dermatologist.'},
        'eye': {'specialty': 'Ophthalmology', 'reason': 'Eye conditions require an ophthalmologist.'},
        'joint': {'specialty': 'Orthopedics', 'reason': 'Joint issues evaluated by an orthopedic specialist.'},
        'bone': {'specialty': 'Orthopedics', 'reason': 'Bone issues evaluated by an orthopedic specialist.'},
        'diabetes': {'specialty': 'Endocrinology', 'reason': 'Diabetes managed by an endocrinologist.'},
        'thyroid': {'specialty': 'Endocrinology', 'reason': 'Thyroid conditions need endocrinology evaluation.'},
        'urinary': {'specialty': 'Urology', 'reason': 'Urinary issues evaluated by a urologist.'},
        'kidney': {'specialty': 'Nephrology', 'reason': 'Kidney conditions require nephrology care.'},
        'depression': {'specialty': 'Psychiatry', 'reason': 'Mental health conditions need psychiatric support.'},
        'anxiety': {'specialty': 'Psychiatry', 'reason': 'Anxiety disorders managed by a psychiatrist.'},
        'women': {'specialty': 'Gynecology', 'reason': "Women's health conditions need gynecology care."},
        'pregnancy': {'specialty': 'Obstetrics & Gynecology', 'reason': 'Pregnancy care by an OB/GYN.'},
        'child': {'specialty': 'Pediatrics', 'reason': 'Pediatric issues managed by a pediatrician.'},
        'ear': {'specialty': 'ENT', 'reason': 'Ear conditions require an ENT specialist.'},
        'nose': {'specialty': 'ENT', 'reason': 'Nasal conditions require an ENT specialist.'},
        'throat': {'specialty': 'ENT', 'reason': 'Throat conditions require an ENT specialist.'},
        'cancer': {'specialty': 'Oncology', 'reason': 'Cancer conditions require oncology evaluation.', 'urgent': True},
        'tumor': {'specialty': 'Oncology', 'reason': 'Tumor evaluation requires an oncologist.', 'urgent': True},
    }

    def post(self, request):
        symptoms = request.data.get('symptoms', '').strip()
        language = request.data.get('language', 'en')  # en | hi | mr

        if not symptoms:
            return Response({'error': 'symptoms field is required.'}, status=400)

        symptoms_lower = symptoms.lower()

        # Check for red-flag symptoms first — always advise urgent care
        is_urgent = any(flag in symptoms_lower for flag in self.RED_FLAG_SYMPTOMS)
        if is_urgent:
            return Response({
                'is_urgent': True,
                'urgent_message': (
                    'URGENT: These symptoms may indicate a medical emergency. '
                    'Please call emergency services (108 in India) immediately or proceed to the nearest emergency room. '
                    'Do not delay seeking emergency care.'
                ),
                'recommended_specialty': 'Emergency Medicine',
                'disclaimer': 'This is an AI-assisted suggestion only. This is NOT a diagnosis. Please consult a licensed medical professional immediately.',
                'symptoms_received': symptoms
            })

        # Try AI recommendation
        ai_result = self._try_ai_recommendation(symptoms, language)
        if ai_result:
            return Response(ai_result)

        # Fallback: rule-based recommendation
        recommendation = None
        for keyword, rec in self.SYMPTOM_SPECIALTY_MAP.items():
            if keyword in symptoms_lower:
                recommendation = rec
                break

        if not recommendation:
            recommendation = {'specialty': 'General Medicine', 'reason': 'For non-specific symptoms, a general physician will assess and refer as needed.'}

        return Response({
            'is_urgent': False,
            'recommended_specialty': recommendation['specialty'],
            'reason': recommendation['reason'],
            'disclaimer': 'This is an AI-assisted suggestion only. This is NOT a diagnosis. A qualified doctor will evaluate your condition.',
            'symptoms_received': symptoms,
            'source': 'rule_based'
        })

    def _try_ai_recommendation(self, symptoms, language):
        """Try Gemini AI for smart recommendation. Returns None on failure."""
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return None

        try:
            lang_instruction = {
                'en': 'Respond in English.',
                'hi': 'Respond in Hindi (हिंदी में उत्तर दें).',
                'mr': 'Respond in Marathi (मराठीत उत्तर द्या).'
            }.get(language, 'Respond in English.')

            prompt = (
                f"{lang_instruction}\n"
                "You are a healthcare assistant that ONLY recommends medical specialties based on symptoms. "
                "You CANNOT diagnose, prescribe, or replace a doctor. "
                "For the following symptoms, recommend ONE medical specialty and briefly explain why (2 sentences max). "
                "Also check if symptoms are urgent (require emergency care). "
                f"Symptoms: {symptoms}\n"
                "Respond in JSON format: {\"specialty\": \"...\", \"reason\": \"...\", \"is_urgent\": false}"
            )

            payload = json.dumps({
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'maxOutputTokens': 200, 'temperature': 0.2}
            }).encode('utf-8')

            url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})

            import socket
            socket.setdefaulttimeout(getattr(settings, 'AI_TIMEOUT_SECONDS', 30))

            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result['candidates'][0]['content']['parts'][0]['text']
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*?\}', text, re.DOTALL)
                if json_match:
                    ai_data = json.loads(json_match.group())
                    return {
                        'is_urgent': ai_data.get('is_urgent', False),
                        'recommended_specialty': ai_data.get('specialty', 'General Medicine'),
                        'reason': ai_data.get('reason', ''),
                        'disclaimer': 'This is an AI-assisted suggestion only. This is NOT a diagnosis. A qualified doctor will evaluate your condition.',
                        'symptoms_received': symptoms,
                        'source': 'gemini_ai'
                    }
        except Exception as e:
            # AI unavailable — fall through to rule-based
            pass
        return None


class DoctorRecommendationView(views.APIView):
    """Returns real doctor profiles matching symptom-derived or caller-specified specialty."""
    permission_classes = [permissions.AllowAny]

    # Mirrors red-flag list from AISymptomRecommendationView
    RED_FLAG_SYMPTOMS = [
        'chest pain', 'heart attack', 'stroke', 'seizure', 'unconscious', 'breathing difficulty',
        'severe bleeding', 'head injury', 'paralysis', 'anaphylaxis', 'overdose', 'suicidal',
        'difficulty breathing', 'shortness of breath'
    ]

    def post(self, request):
        symptoms = request.data.get('symptoms', '').strip()
        health_concern = request.data.get('health_concern', '').strip()
        specialty_param = request.data.get('specialty', '').strip()
        language = request.data.get('language', 'en')
        consultation_type = request.data.get('consultation_type', '').strip()
        preferred_language = request.data.get('preferred_language', '').strip()

        # Combine symptoms and health concern for analysis
        combined_input = ' '.join(filter(None, [symptoms, health_concern]))

        # Step 1 — Red-flag / urgent symptom check
        if combined_input:
            symptoms_lower = combined_input.lower()
            is_urgent = any(flag in symptoms_lower for flag in self.RED_FLAG_SYMPTOMS)
            if is_urgent:
                return Response({
                    'is_urgent': True,
                    'urgent_message': (
                        'URGENT: These symptoms may indicate a medical emergency. '
                        'Please call emergency services (108 in India) immediately or proceed to the nearest emergency room. '
                        'Do not delay seeking emergency care.'
                    ),
                    'recommended_specialty': 'Emergency Medicine',
                    'disclaimer': (
                        'This is an AI-assisted suggestion only. This is NOT a diagnosis. '
                        'Please consult a licensed medical professional immediately.'
                    ),
                    'symptoms_received': combined_input,
                    'doctors': [],
                    'total_found': 0,
                })

        # Step 2 — Determine recommended specialty
        recommended_specialty = specialty_param
        reason = ''
        source = 'user_specified'

        if not recommended_specialty and combined_input:
            # Try AI-based recommendation via AISymptomRecommendationView helper
            ai_result = AISymptomRecommendationView()._try_ai_recommendation(combined_input, language)
            if ai_result and not ai_result.get('is_urgent'):
                recommended_specialty = ai_result.get('recommended_specialty', '')
                reason = ai_result.get('reason', '')
                source = ai_result.get('source', 'gemini_ai')
            else:
                # Rule-based fallback
                symptoms_lower = combined_input.lower()
                for keyword, rec in AISymptomRecommendationView.SYMPTOM_SPECIALTY_MAP.items():
                    if keyword in symptoms_lower:
                        recommended_specialty = rec['specialty']
                        reason = rec['reason']
                        source = 'rule_based'
                        break
                if not recommended_specialty:
                    recommended_specialty = 'General Medicine'
                    reason = 'For non-specific symptoms, a general physician will assess and refer as needed.'
                    source = 'rule_based'

        # Step 3 — Query approved doctor profiles
        queryset = DoctorProfile.objects.filter(is_approved=True)

        location = request.data.get('location', '') or request.data.get('preferred_location', '')
        if location:
            queryset = queryset.filter(models.Q(hospital_name__icontains=location) | models.Q(address__icontains=location))

        SPECIALTY_ALIASES = {
            'cardiology': ['cardio', 'cardiology', 'heart'],
            'neurology': ['neuro', 'neurology', 'brain'],
            'orthopedics': ['ortho', 'orthopedic', 'bone', 'joint'],
            'general medicine': ['general', 'medicine', 'internal'],
            'internal medicine': ['internal', 'medicine', 'general'],
            'dermatology': ['derma', 'skin'],
            'pediatrics': ['pediatric', 'child'],
            'gastroenterology': ['gastro', 'stomach', 'digestive'],
            'psychiatry': ['psychiatry', 'mental'],
            'ophthalmology': ['ophthal', 'eye'],
            'ent': ['ent', 'ear', 'nose', 'throat'],
        }

        matched_qs = queryset
        if recommended_specialty:
            spec_lower = recommended_specialty.lower()
            aliases = SPECIALTY_ALIASES.get(spec_lower, [recommended_specialty])
            q_filter = models.Q(specialization__icontains=recommended_specialty)
            for a in aliases:
                q_filter |= models.Q(specialization__icontains=a)
            matched_qs = queryset.filter(q_filter)

            # If no direct match and not general medicine, fall back to general/internal medicine as alternative
            if not matched_qs.exists() and spec_lower not in ['general medicine', 'internal medicine']:
                matched_qs = queryset.filter(models.Q(specialization__icontains='medicine') | models.Q(specialization__icontains='general'))
                if matched_qs.exists():
                    reason = f"No specialist registered for {recommended_specialty} yet. Recommended General/Internal Medicine physician for initial clinical evaluation."

        # Step 4 — Rank by experience descending
        matched_qs = matched_qs.order_by('-experience_years')

        # Step 5 — Build response with availability & fees
        doctors_list = []
        for doc in matched_qs:
            slots = list(doc.availability_slots.filter(is_active=True).values(
                'id', 'day_of_week', 'start_time', 'end_time', 'max_appointments', 'consultation_fee'
            ))
            for s in slots:
                s['start_time'] = str(s['start_time'])[:5]
                s['end_time'] = str(s['end_time'])[:5]

            fee = float(slots[0]['consultation_fee']) if slots and slots[0].get('consultation_fee') else 500.0
            next_slot = f"{slots[0]['day_of_week']} {slots[0]['start_time']}" if slots else "Contact Clinic"

            doctors_list.append({
                'doctor_id': doc.doctor_id,
                'full_name': doc.full_name,
                'qualification': doc.qualification,
                'specialization': doc.specialization,
                'experience_years': doc.experience_years,
                'hospital_name': doc.hospital_name,
                'address': doc.address,
                'consultation_fee': fee,
                'is_approved': doc.is_approved,
                'availability': slots,
                'next_available': next_slot,
                'why_recommended': (
                    f"Dr. {doc.full_name} specializes in {doc.specialization} "
                    f"with {doc.experience_years} year(s) of clinical experience"
                    + (f" at {doc.hospital_name}" if doc.hospital_name else "") + "."
                ),
            })

        response_data = {
            'is_urgent': False,
            'recommended_specialty': recommended_specialty,
            'reason': reason,
            'source': source,
            'doctors': doctors_list,
            'total_found': len(doctors_list),
            'disclaimer': (
                'These recommendations help you find a suitable specialist. They are not a medical diagnosis. '
                'Seek urgent medical care when needed.'
            ),
        }

        if not doctors_list and recommended_specialty:
            response_data['no_doctors_message'] = (
                f"No approved doctors found for '{recommended_specialty}'. "
                "Please try a different specialty or consult a General Physician."
            )

        return Response(response_data)
