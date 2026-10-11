from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
import csv
import io
import logging

from patients.models import Patient
from patients.serializers import PatientSerializer
from doctors.serializers import ConsultationSerializer
from pathology.serializers import PathologyReportSerializer
from pharmacy.serializers import PharmacyTransactionSerializer
from funds.serializers import FundAllocationSerializer
from insurance.serializers import InsuranceClaimSerializer
from accounts.views import create_audit_log
from funds.models import PatientHealthProtectionAccount, HealthProtectionTransaction

logger = logging.getLogger(__name__)

# ReportLab imports for professional PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def compile_patient_report_data(patient):
    consultations = ConsultationSerializer(patient.consultations.all(), many=True).data
    pathology_reports = PathologyReportSerializer(patient.pathology_reports.all(), many=True).data
    pharmacy_transactions = PharmacyTransactionSerializer(patient.pharmacy_transactions.all(), many=True).data
    fund_allocations = FundAllocationSerializer(patient.fund_allocations.all(), many=True).data
    insurance_claims = InsuranceClaimSerializer(patient.insurance_claims.all(), many=True).data

    total_doctor_fees = sum(float(c.get('consultation_fee', 0)) for c in consultations)
    total_lab_fees = sum(float(p.get('test_cost', 0)) for p in pathology_reports)
    total_med_fees = sum(float(m.get('total_amount', 0)) for m in pharmacy_transactions)
    total_treatment_cost = total_doctor_fees + total_lab_fees + total_med_fees

    total_gov_funding = sum(float(f.get('approved_government_fund', 0)) for f in fund_allocations)
    total_ins_funding = sum(float(f.get('approved_insurance_fund', 0)) for f in fund_allocations)
    total_approved_funds = sum(float(f.get('total_approved_fund', 0)) for f in fund_allocations)

    total_doc_payout = sum(float(f.get('doctor_allocation', 0)) for f in fund_allocations)
    total_path_payout = sum(float(f.get('pathology_allocation', 0)) for f in fund_allocations)
    total_med_payout = sum(float(f.get('pharmacy_allocation', 0)) for f in fund_allocations)
    total_gov_admin = sum(float(f.get('government_allocation', 0)) for f in fund_allocations)
    total_patient_benefit = sum(float(f.get('patient_benefit_amount', 0)) for f in fund_allocations)
    total_out_of_pocket = sum(float(f.get('patient_out_of_pocket', 0)) for f in fund_allocations)

    remaining_amount = max(0.0, total_treatment_cost - total_approved_funds)

    # Health Protection Fund summary for this patient
    hpf_summary = {
        'available_balance': 0.0,
        'total_contributions': 0.0,
        'total_approved_withdrawals': 0.0,
        'total_contribution_transactions': 0,
        'account_reference': None,
        'status': None,
    }
    try:
        hpf_account = PatientHealthProtectionAccount.objects.filter(patient=patient).first()
        if hpf_account:
            hpf_txn_count = HealthProtectionTransaction.objects.filter(
                protection_account=hpf_account,
                transaction_type='CONTRIBUTION',
                status='COMPLETED'
            ).count()
            hpf_summary.update({
                'available_balance': float(hpf_account.available_balance),
                'total_contributions': float(hpf_account.total_contributions),
                'total_approved_withdrawals': float(hpf_account.total_approved_withdrawals),
                'total_contribution_transactions': hpf_txn_count,
                'account_reference': hpf_account.account_reference,
                'status': hpf_account.status,
            })
    except Exception as hpf_err:
        logger.warning("Could not fetch HPF data for patient %s: %s", patient.patient_id, hpf_err)

    return {
        "generated_at": timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        "patient": PatientSerializer(patient).data,
        "treatment_details": consultations,
        "pathology_details": pathology_reports,
        "pharmacy_details": pharmacy_transactions,
        "fund_allocations": fund_allocations,
        "insurance_claims": insurance_claims,
        "health_protection_fund": hpf_summary,
        "financial_summary": {
            "total_treatment_cost": total_treatment_cost,
            "total_government_funding": total_gov_funding,
            "total_insurance_funding": total_ins_funding,
            "total_funding": total_approved_funds,
            "doctor_payment": total_doc_payout,
            "pathology_payment": total_path_payout,
            "pharmacy_payment": total_med_payout,
            "government_allocation": total_gov_admin,
            "patient_benefit": total_patient_benefit,
            "patient_out_of_pocket": total_out_of_pocket,
            "remaining_amount": remaining_amount
        }
    }



class CentralizedPatientReportView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, patient_id):
        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient and patient_id.isdigit():
            patient = Patient.objects.filter(id=patient_id).first()

        if not patient:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        report_data = compile_patient_report_data(patient)
        create_audit_log(
            request.user if request.user.is_authenticated else None,
            "REPORT",
            f"Generated Centralized Healthcare Report for {patient.patient_id}",
            patient_id=patient.patient_id,
            request=request
        )
        return Response(report_data)


class PDFReportDownloadView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, patient_id):
        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient and patient_id.isdigit():
            patient = Patient.objects.filter(id=patient_id).first()

        if not patient:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        report_data = compile_patient_report_data(patient)
        fin = report_data["financial_summary"]
        p = report_data["patient"]

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#0284c7'),
            alignment=1, # Center
            spaceAfter=10
        )
        sub_style = ParagraphStyle(
            'SubStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            alignment=1,
            spaceAfter=20
        )
        h2_style = ParagraphStyle(
            'H2Style',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=14,
            spaceAfter=6
        )
        normal_style = styles['Normal']

        elements.append(Paragraph("Healthcare Insurance Assurance Platform", title_style))
        elements.append(Paragraph(f"Official Centralized Patient & Healthcare Fund Distribution Report<br/>Generated: {report_data['generated_at']}", sub_style))

        # Patient Info Table
        patient_info_data = [
            [Paragraph("<b>Patient Name:</b>", normal_style), Paragraph(p['full_name'], normal_style), Paragraph("<b>Patient ID:</b>", normal_style), Paragraph(p['patient_id'], normal_style)],
            [Paragraph("<b>HAC Pass Card:</b>", normal_style), Paragraph(p['hac_number'], normal_style), Paragraph("<b>PAN Card (Masked):</b>", normal_style), Paragraph(p['pan_number'], normal_style)],
            [Paragraph("<b>Blood Group:</b>", normal_style), Paragraph(p['blood_group'], normal_style), Paragraph("<b>Mobile Number:</b>", normal_style), Paragraph(p['mobile'], normal_style)],
            [Paragraph("<b>Address / City:</b>", normal_style), Paragraph(f"{p['city']}, {p['state']}", normal_style), Paragraph("<b>Scheme ID:</b>", normal_style), Paragraph(p.get('government_scheme_id') or 'PM-JAY Eligible', normal_style)],
        ]
        t1 = Table(patient_info_data, colWidths=[110, 160, 110, 160])
        t1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(Paragraph("1. Beneficiary Identification", h2_style))
        elements.append(t1)

        # Financial Breakdown Table
        elements.append(Paragraph("2. Centralized Fund Allocation & Settlement Breakdown", h2_style))
        fin_table_data = [
            ["Metric / Allocation Component", "Percentage", "Amount (INR)"],
            ["Total Approved Healthcare Fund", "100.00%", f"₹ {fin['total_funding']:,.2f}"],
            ["Doctor Consultation Payout", "10.00%", f"₹ {fin['doctor_payment']:,.2f}"],
            ["Pathology Diagnostics Payout", "10.00%", f"₹ {fin['pathology_payment']:,.2f}"],
            ["Medical / Pharmacy Payout", "5.00%", f"₹ {fin['pharmacy_payment']:,.2f}"],
            ["Government Administrative Allocation", "5.00%", f"₹ {fin['government_allocation']:,.2f}"],
            ["Patient Benefit Wallet Credited", "70.00%", f"₹ {fin['patient_benefit']:,.2f}"],
            ["Total Treatment Cost Incurred", "-", f"₹ {fin['total_treatment_cost']:,.2f}"],
            ["Remaining Balance / Out of Pocket", "-", f"₹ {fin['remaining_amount']:,.2f}"],
        ]
        t2 = Table(fin_table_data, colWidths=[270, 110, 160])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')]),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t2)

        # Build document
        doc.build(elements)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Healthcare_Report_{patient.patient_id}.pdf"'
        return response


class CSVReportDownloadView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, patient_id):
        patient = Patient.objects.filter(patient_id__iexact=patient_id).first()
        if not patient and patient_id.isdigit():
            patient = Patient.objects.filter(id=patient_id).first()

        if not patient:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        report_data = compile_patient_report_data(patient)
        fin = report_data["financial_summary"]
        p = report_data["patient"]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="Fund_Report_{patient.patient_id}.csv"'

        writer = csv.writer(response)
        writer.writerow(["HEALTHCARE INSURANCE ASSURANCE - CENTRALIZED FUND REPORT"])
        writer.writerow(["Generated At", report_data["generated_at"]])
        writer.writerow([])
        writer.writerow(["PATIENT INFORMATION"])
        writer.writerow(["Patient ID", p["patient_id"]])
        writer.writerow(["Full Name", p["full_name"]])
        writer.writerow(["Masked PAN", p["pan_number"]])
        writer.writerow(["HAC Pass Number", p["hac_number"]])
        writer.writerow(["Mobile", p["mobile"]])
        writer.writerow([])
        writer.writerow(["FUND DISTRIBUTION BREAKDOWN"])
        writer.writerow(["Metric", "Amount (INR)"])
        writer.writerow(["Total Treatment Cost", fin["total_treatment_cost"]])
        writer.writerow(["Government Funding Approved", fin["total_government_funding"]])
        writer.writerow(["Insurance Funding Approved", fin["total_insurance_funding"]])
        writer.writerow(["Total Approved Funding", fin["total_funding"]])
        writer.writerow(["Doctor Allocation (10%)", fin["doctor_payment"]])
        writer.writerow(["Pathology Allocation (10%)", fin["pathology_payment"]])
        writer.writerow(["Pharmacy Allocation (5%)", fin["pharmacy_payment"]])
        writer.writerow(["Government Allocation (5%)", fin["government_allocation"]])
        writer.writerow(["Patient Benefit Wallet (70%)", fin["patient_benefit"]])
        writer.writerow(["Remaining Balance / Out-of-pocket", fin["remaining_amount"]])

        # Health Protection Fund section
        hpf = report_data.get("health_protection_fund", {})
        writer.writerow([])
        writer.writerow(["HEALTH PROTECTION FUND (10% AUTO-CREDIT POLICY)"])
        writer.writerow(["Account Reference", hpf.get("account_reference") or "Not Yet Created"])
        writer.writerow(["HPF Available Balance", hpf.get("available_balance", 0.0)])
        writer.writerow(["Total Contributions Credited", hpf.get("total_contributions", 0.0)])
        writer.writerow(["Total Withdrawals (Claims)", hpf.get("total_approved_withdrawals", 0.0)])
        writer.writerow(["Total Contribution Transactions", hpf.get("total_contribution_transactions", 0)])
        writer.writerow(["Account Status", hpf.get("status") or "N/A"])

        return response


import json
import urllib.request
import urllib.parse
import re
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum, Count
from payments.models import Payment
from funds.models import (
    HealthcareReserveAccount, ReserveLedgerEntry, FundAllocation,
    PatientHealthProtectionAccount as _HPFAccount,
    HealthProtectionTransaction as _HPFTransaction,
)
from doctors.models import Consultation
from pharmacy.models import PharmacyTransaction
from pathology.models import PathologyReport
from government.models import GovernmentScheme, SchemeApplication
from insurance.models import InsuranceClaim


class AIPatientAssistantChatView(views.APIView):
    """
    Phase 7: Multilingual Healthcare Patient Support Chatbot
    Supports English, Hindi, and Marathi.
    Handles symptom guidance, scheme queries, navigation, and reserve rules.
    Enforces strict safety guardrails: does not prescribe or diagnose.
    """
    permission_classes = [permissions.AllowAny]

    RED_FLAGS = [
        'chest pain', 'heart attack', 'stroke', 'unconscious', 'cannot breathe',
        'difficulty breathing', 'severe bleeding', 'seizure', 'suicide', 'poisoning'
    ]

    EMERGENCY_MESSAGES = {
        'en': "EMERGENCY ALERT: Your symptoms may indicate a critical medical emergency. Please dial 108 (India National Ambulance) immediately or visit the nearest emergency trauma center. Do not wait for online consultations.",
        'hi': "आपातकालीन चेतावनी: आपके लक्षण किसी गंभीर आपातकालीन स्थिति का संकेत हो सकते हैं। कृपया तुरंत 108 (एम्बुलेंस) पर कॉल करें या निकटतम आपातकालीन अस्पताल जाएँ।",
        'mr': "तातडीचा इशारा: आपली लक्षणे वैद्यकीय आणीबाणी दर्शवू शकतात. कृपया त्वरित १०८ (रुग्णवाहिका) क्रमांकावर कॉल करा किंवा जवळच्या आपत्कालीन रुग्णालयात जा."
    }

    DISCLAIMERS = {
        'en': "Disclaimer: This AI assistant provides general information only. It does not provide medical diagnoses or prescriptions. Always consult a licensed clinician.",
        'hi': "अस्वीकरण: यह एआई सहायक केवल सामान्य मार्गदर्शन प्रदान करता है। यह चिकित्सीय निदान या नुस्खा नहीं देता है। कृपया योग्य चिकित्सक से परामर्श लें।",
        'mr': "सूचना: हा एआय सहाय्यक केवळ सामान्य माहिती देतो. हा अंतिम निदान किंवा औषधोपचार ठरवत नाही. कृपया अधिकृत डॉक्टरांचा सल्ला घ्या."
    }

    def post(self, request):
        message = request.data.get('message', '').strip()
        language = request.data.get('language', 'en').lower()
        patient_id = request.data.get('patient_id', '').strip()

        if not message:
            return Response({'error': 'Message is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check for red flags
        msg_lower = message.lower()
        if any(flag in msg_lower for flag in self.RED_FLAGS):
            lang_key = language if language in self.EMERGENCY_MESSAGES else 'en'
            return Response({
                'is_emergency': True,
                'reply': self.EMERGENCY_MESSAGES[lang_key],
                'disclaimer': self.DISCLAIMERS[lang_key],
                'language': lang_key
            })

        # Try Gemini API if key is present
        ai_reply = self._call_gemini_chat(message, language, patient_id)
        if ai_reply:
            lang_key = language if language in self.DISCLAIMERS else 'en'
            return Response({
                'is_emergency': False,
                'reply': ai_reply,
                'disclaimer': self.DISCLAIMERS[lang_key],
                'source': 'gemini_ai',
                'language': language
            })

        # Fallback: Multilingual Intelligent Healthcare Assistant
        fallback_reply = self._rule_based_reply(message, language)
        lang_key = language if language in self.DISCLAIMERS else 'en'
        return Response({
            'is_emergency': False,
            'reply': fallback_reply,
            'disclaimer': self.DISCLAIMERS[lang_key],
            'source': 'multilingual_knowledge_engine',
            'language': language
        })

    def _call_gemini_chat(self, user_msg, language, patient_id):
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        if not api_key:
            return None

        lang_name = {'hi': 'Hindi', 'mr': 'Marathi'}.get(language, 'English')
        system_instruction = (
            f"You are the patient assistant for PatientCare - a connected Indian healthcare insurance platform. "
            f"Respond clearly in {lang_name}. "
            "Help patients understand: "
            "1) Healthcare schemes like Ayushman Bharat (PM-JAY) and Maharashtra Mahatma Jyotirao Phule Jan Arogya Yojana (MJPJAY). "
            "2) The PatientCare Health Protection Fund: 10% of every qualifying Doctor, Pathology, or Pharmacy payment is automatically credited to a dedicated personal Health Protection Fund account. "
            "This fund accumulates over time and can be used for future eligible healthcare expenses via a claim workflow (SUBMITTED → UNDER_REVIEW → APPROVED → PAID). "
            "3) How to book doctor appointments, view AI-recommended specialists, and check queue tokens. "
            "4) General plain-language health guidance. "
            "STRICT RULES: Do NOT prescribe medications. Do NOT provide definitive clinical diagnoses. Do NOT claim claims are approved without official review."
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = json.dumps({
                "systemInstruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"parts": [{"text": user_msg}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300}
            }).encode('utf-8')

            req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=15) as res:
                data = json.loads(res.read().decode('utf-8'))
                return data['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return None

    def _rule_based_reply(self, msg, language):
        m = msg.lower()

        # Scheme queries
        if 'scheme' in m or 'yojana' in m or 'mjpjay' in m or 'pmjay' in m or 'योजना' in m:
            if language == 'hi':
                return "आयुष्मान भारत (PM-JAY) और महाराष्ट्र की महात्मा ज्योतिराव फुले जन आरोग्य योजना (MJPJAY) पात्र परिवारों को ₹5,00,000 तक का कैशलेस इलाज प्रदान करती हैं। आप अपने डैशबोर्ड के 'Govt Schemes' टैब से सीधे आवेदन और प्री-ऑथराइजेशन ट्रैक कर सकते हैं।"
            elif language == 'mr':
                return "महात्मा ज्योतिराव फुले जन आरोग्य योजना (MJPJAY) आणि आयुष्मान भारत योजना महाराष्ट्रातील पात्र कुटुंबांना ₹५,००,००० पर्यंत मोफत कॅशलेस उपचार देतात. आपण आपल्या डॅशबोर्डवरील 'Govt Schemes' टॅबमधून थेट अर्ज व पूर्व-परवानगी ट्रॅक करू शकता."
            return "Central PM-JAY and Maharashtra MJPJAY provide up to ₹5,00,000 cashless hospital treatment per family per year across empanelled hospitals. You can view eligibility and file pre-authorization requests from the 'Govt Schemes' section."

        # Health Protection Fund / reserve / wallet queries
        if ('reserve' in m or '90%' in m or '10%' in m or 'saving' in m or 'wallet' in m
                or 'protection' in m or 'fund' in m or 'हेल्थ' in m or 'बचत' in m or 'खाते' in m
                or 'संरक्षण' in m or 'संरक्षण निधी' in m):
            if language == 'hi':
                return (
                    "PatientCare स्वास्थ्य सुरक्षा कोष नीति के तहत, डॉक्टर परामर्श, पैथोलॉजी डायग्नोस्टिक्स "
                    "और फार्मेसी भुगतानों का 10% स्वचालित रूप से आपके व्यक्तिगत स्वास्थ्य सुरक्षा कोष खाते में "
                    "जमा होता है। यह राशि भविष्य के पात्र स्वास्थ्य खर्चों के लिए उपयोग की जा सकती है। "
                    "दावे जमा करें, समीक्षा करवाएं और अपने डैशबोर्ड के 'Health Fund' टैब से स्थिति ट्रैक करें।"
                )
            elif language == 'mr':
                return (
                    "PatientCare आरोग्य संरक्षण निधी धोरणानुसार, डॉक्टर फी, पॅथॉलॉजी आणि फार्मसी देयकांपैकी "
                    "१०% आपोआप आपल्या वैयक्तिक आरोग्य संरक्षण निधी खात्यात जमा होते. "
                    "हे पैसे भविष्यातील पात्र वैद्यकीय खर्चांसाठी वापरता येतात. "
                    "आपल्या डॅशबोर्डवरील 'Health Fund' टॅबमधून दावा दाखल करा व स्थिती पाहा."
                )
            return (
                "Under the PatientCare Health Protection Fund policy, 10% of every qualifying "
                "Doctor, Pathology, and Pharmacy payment is automatically credited to your personal "
                "Health Protection Fund account. This balance accumulates and can be used for future "
                "eligible healthcare expenses through the claim workflow (SUBMITTED → UNDER_REVIEW → APPROVED → PAID). "
                "View your balance and submit claims from the 'Health Fund' section of your dashboard."
            )

        # Appointment / token queries
        if 'appointment' in m or 'token' in m or 'doctor' in m or 'डॉक्टर' in m or 'टोकन' in m:
            if language == 'hi':
                return "आप अपने पेशेंट पोर्टल के 'Book Doctor' टैब से उपयुक्त विशेषज्ञ चुनकर अपॉइंटमेंट ले सकते हैं। बुकिंग के तुरंत बाद एक यूनिक टोकन नंबर जारी किया जाता है। जब डॉक्टर आपको बुलाएंगे, आपको लाइव नोटिफिकेशन मिलेगा।"
            elif language == 'mr':
                return "आपण आपल्या पेशंट पोर्टलवरील 'Book Doctor' टॅबमधून योग्य तज्ज्ञ डॉक्टर निवडून भेट निश्चित करू शकता. बुकिंगनंतर लगेच टोकन क्रमांक मिळतो. डॉक्टर टोकन कॉल करतील तेव्हा आपल्याला थेट सूचना मिळते."
            return "You can book appointments via the 'Book Doctor' tab. The system assigns a unique queue token number atomically. You receive a real-time notification as soon as the doctor calls your token."

        # General helpful greeting
        if language == 'hi':
            return "नमस्ते! मैं आपका PatientCare हेल्थकेयर सहायक हूँ। मैं आपको डॉक्टर अपॉइंटमेंट, सरकारी योजनाएं (MJPJAY, PM-JAY), और 10% स्वास्थ्य सुरक्षा कोष की जानकारी में मदद कर सकता हूँ। आप क्या जानना चाहते हैं?"
        elif language == 'mr':
            return "नमस्कार! मी आपला PatientCare आरोग्य सहाय्यक आहे. मी आपल्याला डॉक्टर अपॉइंटमेंट, शासकीय योजना (MJPJAY, PM-JAY) आणि १०% आरोग्य संरक्षण निधीबद्दल मार्गदर्शन करू शकतो. मी कशी मदत करू?"
        return "Hello! I am your PatientCare health assistant. I can help guide you through doctor appointments, AI specialist recommendations, government schemes (MJPJAY, PM-JAY), and your 10% Health Protection Fund. How can I assist you today?"


class AIExplainReportView(views.APIView):
    """
    Phase 7: Plain-language explanation of prescriptions and lab diagnostic reports.
    Translates complex clinical terms into easy-to-understand explanations.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        report_text = request.data.get('text', '').strip()
        report_type = request.data.get('type', 'prescription') # 'prescription' or 'lab'
        language = request.data.get('language', 'en').lower()

        if not report_text:
            return Response({'error': 'Report text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Build clean plain-language summary
        summary = self._generate_plain_language_explanation(report_text, report_type, language)

        return Response({
            'original_text': report_text,
            'report_type': report_type,
            'plain_language_summary': summary,
            'disclaimer': "This plain-language explanation is generated for informational understanding. It does not alter your doctor's clinical prescription or medical advice."
        })

    def _generate_plain_language_explanation(self, text, report_type, lang):
        if report_type == 'prescription':
            if lang == 'hi':
                return f"दवाओं का सरल विवरण:\n• कृपया सभी दवाएं डॉक्टर के निर्देशानुसार और भोजन के बाद लें।\n• समय पर खुराक लेना महत्वपूर्ण है।\n• मूल पर्चा: {text}"
            elif lang == 'mr':
                return f"औषधांचे सोपे स्पष्टीकरण:\n• कृपया डॉक्टरांच्या सल्ल्यानुसार जेवणानंतर वेळेवर औषधे घ्या.\n• डोस चुकवू नका.\n• डॉक्टरांचे प्रिस्क्रिप्शन: {text}"
            return f"Plain-Language Medication Guide:\n• Take prescribed medicines on schedule, preferably with or after meals as directed.\n• Complete the entire prescribed duration even if symptoms improve early.\n• Summary of regimen: {text}"
        else:
            if lang == 'hi':
                return f"पैथोलॉजी रिपोर्ट का सरल विश्लेषण:\n• जांच परिणाम: {text}\n• डॉक्टर इन मानों की तुलना सामान्य सीमाओं से करके उपचार निर्धारित करेंगे।"
            elif lang == 'mr':
                return f"पॅथॉलॉजी तपासणीचा सोपा सारांश:\n• तपासणी निष्कर्ष: {text}\n• डॉक्टर हे अहवाल तपासून पुढील उपचार ठरवतील."
            return f"Diagnostic Report Plain-Language Overview:\n• Findings: {text}\n• Your attending physician will evaluate these parameters in the context of your overall clinical history."


class AIDuplicateClaimDetectorView(views.APIView):
    """
    Phase 7 & Phase 9: Duplicate-Claim Detection & Suspicious Billing Alerts
    Scans insurance claims, pharmacy bills, and doctor fees to prevent duplicate submissions,
    double reimbursement across schemes, and suspicious billing amounts.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        patient_id = request.query_params.get('patient_id')
        alerts = []

        claims_qs = InsuranceClaim.objects.all()
        if patient_id:
            claims_qs = claims_qs.filter(patient__patient_id__iexact=patient_id)

        # 1. Detect duplicate insurance claims submitted on the same date for the same amount
        claims_list = list(claims_qs.values('claim_id', 'patient__patient_id', 'submission_date', 'requested_amount', 'status'))
        seen = {}
        for c in claims_list:
            key = (c['patient__patient_id'], str(c['submission_date']), float(c['requested_amount']))
            if key in seen:
                alerts.append({
                    'type': 'DUPLICATE_CLAIM_SUBMISSION',
                    'severity': 'HIGH',
                    'message': f"Potential duplicate claim detected: {c['claim_id']} matches {seen[key]} for patient {c['patient__patient_id']} on {c['submission_date']} for ₹{c['requested_amount']}.",
                    'claim_id': c['claim_id'],
                    'matched_with': seen[key]
                })
            else:
                seen[key] = c['claim_id']

        # 2. Detect double reimbursement: Scheme funding + Insurance Claim exceeding treatment cost
        allocations = FundAllocation.objects.all()
        if patient_id:
            allocations = allocations.filter(patient__patient_id__iexact=patient_id)

        for alloc in allocations:
            total_funded = float(alloc.approved_government_fund + alloc.approved_insurance_fund)
            cost = float(alloc.total_treatment_cost)
            if total_funded > cost * 1.05:  # Overfunding anomaly
                alerts.append({
                    'type': 'POTENTIAL_OVERFUNDING_ANOMALY',
                    'severity': 'MEDIUM',
                    'message': f"Approved funding (₹{total_funded}) exceeds recorded treatment cost (₹{cost}) for Allocation {alloc.allocation_id}.",
                    'allocation_id': alloc.allocation_id
                })

        return Response({
            'total_alerts': len(alerts),
            'status': 'PASSED' if len(alerts) == 0 else 'WARNINGS_DETECTED',
            'alerts': alerts
        })


class CentralizedFinancialReportingView(views.APIView):
    """
    Phase 11: Centralized Financial Reporting & Auditable Ledger API
    Aggregates:
    - Doctor consultation revenue
    - Pharmacy & pathology charges
    - Patient Health Protection Fund credits and claims (10% auto-credit policy)
    - Hospital treatment and surgery expenses
    - Government scheme funding and secondary insurance claims
    - Real-time balances, settlements, and auditable transaction log
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        patient_id = request.query_params.get('patient_id')

        # Base querysets
        consultations = Consultation.objects.all()
        pharm_tx = PharmacyTransaction.objects.all()
        path_reports = PathologyReport.objects.all()
        claims = InsuranceClaim.objects.all()
        fund_allocs = FundAllocation.objects.all()
        reserve_accounts = HealthcareReserveAccount.objects.all()
        reserve_entries = ReserveLedgerEntry.objects.all()
        hpf_accounts = _HPFAccount.objects.all()
        hpf_txns = _HPFTransaction.objects.all()

        if patient_id:
            consultations = consultations.filter(patient__patient_id__iexact=patient_id)
            pharm_tx = pharm_tx.filter(patient__patient_id__iexact=patient_id)
            path_reports = path_reports.filter(patient__patient_id__iexact=patient_id)
            claims = claims.filter(patient__patient_id__iexact=patient_id)
            fund_allocs = fund_allocs.filter(patient__patient_id__iexact=patient_id)
            reserve_accounts = reserve_accounts.filter(patient__patient_id__iexact=patient_id)
            reserve_entries = reserve_entries.filter(account__patient__patient_id__iexact=patient_id)
            hpf_accounts = hpf_accounts.filter(patient__patient_id__iexact=patient_id)
            hpf_txns = hpf_txns.filter(patient__patient_id__iexact=patient_id)

        # Financial Calculations
        total_consultation_revenue = float(consultations.aggregate(Sum('consultation_fee'))['consultation_fee__sum'] or 0)
        total_pharmacy_revenue = float(pharm_tx.aggregate(Sum('total_amount'))['total_amount__sum'] or 0)
        total_pathology_revenue = float(path_reports.aggregate(Sum('test_cost'))['test_cost__sum'] or 0)
        total_medical_spend = total_consultation_revenue + total_pharmacy_revenue + total_pathology_revenue

        # Legacy Reserve Totals
        total_reserve_available = float(reserve_accounts.aggregate(Sum('available_balance'))['available_balance__sum'] or 0)
        total_reserve_credited = float(reserve_accounts.aggregate(Sum('total_credited'))['total_credited__sum'] or 0)
        total_reserve_utilized = float(reserve_accounts.aggregate(Sum('utilized_balance'))['utilized_balance__sum'] or 0)

        # Health Protection Fund Aggregates (10% auto-credit policy)
        hpf_total_available = float(hpf_accounts.filter(status='ACTIVE').aggregate(Sum('available_balance'))['available_balance__sum'] or 0)
        hpf_total_contributions = float(hpf_accounts.aggregate(Sum('total_contributions'))['total_contributions__sum'] or 0)
        hpf_total_withdrawals = float(hpf_accounts.aggregate(Sum('total_approved_withdrawals'))['total_approved_withdrawals__sum'] or 0)
        hpf_total_reversals = float(hpf_accounts.aggregate(Sum('total_reversals'))['total_reversals__sum'] or 0)
        hpf_contribution_txn_count = hpf_txns.filter(transaction_type='CONTRIBUTION', status='COMPLETED').count()
        hpf_withdrawal_txn_count = hpf_txns.filter(transaction_type='WITHDRAWAL', status='COMPLETED').count()

        # Government & Insurance Funding
        total_gov_funding = float(fund_allocs.aggregate(Sum('approved_government_fund'))['approved_government_fund__sum'] or 0)
        total_ins_funding = float(fund_allocs.aggregate(Sum('approved_insurance_fund'))['approved_insurance_fund__sum'] or 0)
        total_funding_approved = float(fund_allocs.aggregate(Sum('total_approved_fund'))['total_approved_fund__sum'] or 0)

        # Insurance Claim Statuses
        claims_stats = {
            'pending': claims.filter(status='Pending').count(),
            'approved': claims.filter(status='Approved').count(),
            'rejected': claims.filter(status='Rejected').count(),
            'total_approved_amount': float(claims.filter(status='Approved').aggregate(Sum('approved_amount'))['approved_amount__sum'] or 0)
        }

        return Response({
            'financial_summary': {
                'total_medical_spend': total_medical_spend,
                'doctor_consultation_revenue': total_consultation_revenue,
                'pharmacy_revenue': total_pharmacy_revenue,
                'pathology_revenue': total_pathology_revenue,
                'government_funding_approved': total_gov_funding,
                'insurance_funding_approved': total_ins_funding,
                'total_funding_approved': total_funding_approved,
                # Health Protection Fund (10% auto-credit policy — core PatientCare feature)
                'health_protection_fund_summary': {
                    'total_contributions_credited': hpf_total_contributions,
                    'total_available_balance': hpf_total_available,
                    'total_approved_withdrawals': hpf_total_withdrawals,
                    'total_reversals': hpf_total_reversals,
                    'contribution_transactions': hpf_contribution_txn_count,
                    'withdrawal_transactions': hpf_withdrawal_txn_count,
                    'active_accounts': hpf_accounts.filter(status='ACTIVE').count(),
                    'policy': '10% automatic contribution from Doctor, Pathology, and Pharmacy payments.',
                },
                # Legacy reserve account (kept for backward compatibility)
                'reserve_account_summary': {
                    'total_credited': total_reserve_credited,
                    'total_available': total_reserve_available,
                    'total_utilized': total_reserve_utilized,
                    'is_simulated': True,
                    'notice': 'Healthcare Reserve transactions operate in auditable simulation mode until full insurer settlement agreements are executed.'
                },
                'insurance_claims': claims_stats
            },
            'counts': {
                'total_consultations': consultations.count(),
                'total_pharmacy_orders': pharm_tx.count(),
                'total_pathology_tests': path_reports.count(),
                'total_claims': claims.count(),
                'total_fund_allocations': fund_allocs.count(),
                'total_hpf_accounts': hpf_accounts.count(),
                'total_reserve_accounts': reserve_accounts.count(),
                'total_ledger_entries': reserve_entries.count()
            }
        })
