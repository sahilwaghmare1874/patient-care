from rest_framework import views, status, generics, permissions
from rest_framework.response import Response
from django.utils import timezone
from .models import PathologyTest, PathologyReport
from .serializers import PathologyTestSerializer, PathologyReportSerializer
from patients.models import Patient
from accounts.models import PathologyProfile, DoctorProfile
from accounts.views import create_audit_log
from notifications.models import Notification

class PathologyTestListView(generics.ListCreateAPIView):
    queryset = PathologyTest.objects.all()
    serializer_class = PathologyTestSerializer
    permission_classes = [permissions.AllowAny]


class PathologyReportListCreateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        reports = PathologyReport.objects.all()
        if patient_id:
            reports = reports.filter(patient__patient_id__iexact=patient_id)
        serializer = PathologyReportSerializer(reports, many=True)
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
            return Response({"error": "Patient not found. Search patient first."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve Lab profile
        lab = None
        if request.user.is_authenticated and hasattr(request.user, 'pathology_profile'):
            lab = request.user.pathology_profile
        else:
            lab_id_input = data.pop('lab_id', None)
            if lab_id_input:
                lab = PathologyProfile.objects.filter(lab_id__iexact=lab_id_input).first()
            if not lab:
                lab = PathologyProfile.objects.first()

        if not lab:
            return Response({"error": "Pathology lab profile not found."}, status=status.HTTP_400_BAD_REQUEST)

        count = PathologyReport.objects.count() + 1
        report_id = f"LAB-2026-{count:04d}"

        # Referring doctor lookup if provided
        doctor = None
        doc_id = data.pop('referring_doctor_id', None)
        if doc_id:
            doctor = DoctorProfile.objects.filter(doctor_id__iexact=doc_id).first()

        report = PathologyReport.objects.create(
            report_id=report_id,
            patient=patient,
            lab=lab,
            referring_doctor=doctor,
            test_name=data.get('test_name', 'Complete Blood Count (CBC)'),
            test_category=data.get('test_category', 'Clinical Pathology'),
            test_date=data.get('test_date') or timezone.now().date(),
            test_cost=data.get('test_cost', 800.00),
            results_summary=data.get('results_summary', 'Normal findings.'),
            detailed_findings=data.get('detailed_findings', ''),
            status=data.get('status', 'Verified'),
            payment_status=data.get('payment_status', 'Paid')
        )

        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "PATHOLOGY",
            f"Uploaded pathology report: {report.report_id} for {patient.patient_id}",
            patient_id=patient.patient_id,
            request=request
        )

        if patient.user:
            Notification.objects.create(
                recipient=patient.user,
                title="Pathology Report Available",
                message=f"Your diagnostic report for '{report.test_name}' has been uploaded and verified by {lab.lab_name}.",
                notification_type="PATHOLOGY"
            )

        return Response({
            "message": "Pathology report uploaded and verified successfully.",
            "report": PathologyReportSerializer(report).data
        }, status=status.HTTP_201_CREATED)


class PathologyDashboardStatsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_reports = PathologyReport.objects.count()
        verified_reports = PathologyReport.objects.filter(status='Verified').count()
        pending_reports = PathologyReport.objects.filter(status='Pending').count()

        return Response({
            "total_reports": total_reports,
            "verified_reports": verified_reports,
            "pending_reports": pending_reports,
            "available_tests": PathologyTest.objects.count(),
            "recent_reports": PathologyReportSerializer(PathologyReport.objects.all()[:5], many=True).data
        })
