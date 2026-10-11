# Healthcare Patient, Treatment, Fund Allocation & Patient Benefit Management System

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.2%2B-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/Django_REST_Framework-3.15%2B-red.svg)](https://www.django-rest-framework.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL_%2F_SQLite-blue.svg)](https://www.postgresql.org/)

A production-grade, centralized healthcare management and transparent fund distribution platform compliant with India's **Ayushman Bharat Digital Mission (ABDM)** and **PM-JAY** healthcare principles.

---

## 1. System Architecture & Complete Flow

```text
PATIENT REGISTRATION
        ↓
OTP & INDIAN PAN VERIFICATION
        ↓
    Existing PAN?
     /        \
   YES        NO
    ↓          ↓
Retrieve Existing ID   Create Unique Patient ID (PAT-2026-XXXXXX)
    ↓          ↓       & Generate HAC Pass (HAC-91-XXXX-XXXX-2026)
    └──────┬───┘
           ↓
      Patient Login
           ↓
   Doctor Consultation (Dr. Notes, Diagnoses, Digital Prescription)
           ↓
   Pathology Diagnostic Investigation (Certified Lab Reports)
           ↓
   Government Healthcare Scheme Eligibility (PM-JAY, PMSBY, ABDM)
           ↓
   Government Fund Allocation (100% Cashless Package)
           ↓
     Government Fund Sufficient?
       /             \
     YES              NO
      ↓                ↓
Treatment Settle   Insurance Secondary Deficit Claim
      ↓                ↓
      └───────┬────────┘
              ↓
  Medical / Pharmacy Dispensation (5% Concessional GST Invoice)
              ↓
  Configurable Fund Distribution Calculation Engine:
    • Doctor Consultation Payout      : 10.00%
    • Pathology Diagnostics Payout    : 10.00%
    • Medical / Pharmacy Payout       :  5.00%
    • Government Administrative Fee   :  5.00%
    • Patient Benefit Wallet Balance  : 70.00%
              ↓
  Smart Payments (Benefit Wallet, UPI, Card, Net Banking)
              ↓
  Final Centralized Healthcare & Fund Distribution Report (Web, Print, PDF, CSV)
```

---

## 2. Technology Stack

* **Frontend**:
  * Semantic HTML5 & Modern CSS3 Design System
  * Bootstrap 5.3 + Bootstrap Icons
  * Vanilla JavaScript (ES6+) with Fetch API
  * Chart.js for live fund distribution visualization
  * Responsive across Mobile, Tablet, Laptop, and Desktop
* **Backend**:
  * Python 3.12+ / 3.14+
  * Django 5.2+ & Django REST Framework (DRF)
  * SimpleJWT (JSON Web Token Authentication)
  * ReportLab 5.0+ (Dynamic PDF report compilation)
  * Gunicorn WSGI Server & Django CORS Headers
* **Database**:
  * PostgreSQL (Production) / SQLite3 (Zero-setup Out-of-the-box local development)
  * Environment-based DB switching via `DB_ENGINE` / `POSTGRES_DB`

---

## 3. Project Directory Structure

```text
PatientCare/
├── backend/
│   ├── manage.py                   # Django management CLI
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment variables template
│   ├── tests_integration.py        # Automated end-to-end integration test suite
│   ├── config/                     # Core settings, master URLs, WSGI/ASGI
│   ├── accounts/                   # User model, roles, JWT, OTP, provider profiles, audit logs
│   ├── patients/                   # Patient model, PAN validation, deduplication, centralized record
│   ├── doctors/                    # Appointments, consultations, diagnoses, prescriptions
│   ├── pathology/                  # Lab profiles, test catalog, certified reports
│   ├── pharmacy/                   # Pharmacy profiles, inventory, dispensations, invoicing
│   ├── government/                 # Government schemes directory, eligibility, dashboard stats
│   ├── insurance/                  # Insurance companies, policies, secondary deficit claims
│   ├── funds/                      # Configurable allocation rules engine & fund calculations
│   ├── payments/                   # Smart payments, transactions, GST computation, digital receipts
│   ├── reports/                    # Centralized report compiler, PDF (ReportLab) & CSV export
│   └── notifications/              # In-app notification engine
│
├── frontend/
│   ├── index.html                  # Professional healthcare landing page & quick record lookup
│   ├── css/
│   │   ├── style.css               # Design tokens, health cards, timeline, responsive components
│   │   └── responsive.css          # Breakpoint rules for mobile & tablet
│   ├── js/
│   │   ├── api.js                  # Centralized Fetch API client & state management
│   │   ├── main.js                 # Global handlers, navbar state, home lookup
│   │   ├── auth.js                 # Authentication & provider registration
│   │   ├── patient.js              # Patient registration, deduplication modal, dashboard
│   │   ├── doctor.js               # Clinical consultations & prescription issuance
│   │   ├── pathology.js            # Lab report uploads & tests catalog
│   │   ├── pharmacy.js             # Prescription verification, dispensation, invoicing
│   │   ├── government.js           # Scheme creation, live allocation preview, approvals
│   │   ├── insurance.js            # Secondary claims filing & review
│   │   ├── payment.js              # Smart checkout & printable digital receipts
│   │   ├── reports.js              # Centralized report view, Chart.js, PDF/CSV triggers
│   │   └── admin.js                # Fund allocation rules engine & audit logs
│   └── pages/
│       ├── register.html           # Patient & provider registration with PAN validation
│       ├── login.html              # Multi-role login with 1-click demo auto-fill
│       ├── patient-dashboard.html  # Patient hub, health pass, timeline & connected records
│       ├── doctor-dashboard.html   # Doctor consultation & prescription issuance
│       ├── pathology-dashboard.html# Diagnostic lab report entry & certification
│       ├── pharmacy-dashboard.html # Pharmacy dispensary & GST invoicing
│       ├── government-dashboard.html# Scheme management & fund allocation directorate
│       ├── admin-dashboard.html    # Policy percentage configuration engine & audit logs
│       └── reports.html            # Final centralized patient report (Web/Print/PDF/CSV)
│
├── deployment/
│   ├── Dockerfile                  # Production container definition
│   ├── docker-compose.yml          # Multi-container stack (PostgreSQL + Django + Gunicorn)
│   ├── gunicorn.conf.py            # High-performance Gunicorn WSGI configuration
│   └── nginx.conf                  # Production reverse-proxy with SSL & caching
│
├── server.js                       # Local static Node.js web server (Port 3000)
├── run_system.py                   # One-command dual-server launcher
└── README.md                       # Complete documentation
```

---

## 4. Key Business Logic & Innovations

### A. Critical PAN → Unique Patient ID Logic
1. When a patient enters their details, the system validates the Indian PAN format (`[A-Z]{5}[0-9]{4}[A-Z]{1}`).
2. **PAN Uniqueness Check**:
   * **If PAN exists**: The system **does not** create a duplicate record. It retrieves the existing `Patient ID` (e.g. `PAT-2026-000001`), displays an informative modal, and directs the patient to access their existing profile.
   * **If PAN does not exist**: A new sequential `PAT-2026-XXXXXX` and Healthcare Assurance Card (`HAC-91-XXXX-XXXX-2026`) are generated and committed to the database.
3. Sensitive Data Protection: The PAN is **masked** across all public APIs and UI views (`XXXXX1234X`).

### B. Configurable Fund Allocation Engine
Percentages are stored in the database model `AllocationConfiguration` and can be adjusted from the Admin/Government Dashboard without changing code:
* **Doctor Consultation Payout**: `10.00%`
* **Pathology Diagnostic Payout**: `10.00%`
* **Medical / Pharmacy Payout**: `5.00%`
* **Government Administration Payout**: `5.00%`
* **Patient Benefit Wallet Balance**: `70.00%`

*Calculations use `Decimal` arithmetic in Python to prevent floating-point inaccuracies.*

### C. Secondary Insurance Deficit Handling
If a patient's treatment cost exceeds the government funding allocation cap, the system triggers a secondary insurance claim workflow, linking approved private insurance funds with the centralized settlement.

### D. GST & Tax Compliance
* Clinical outpatient consultations and accredited pathology diagnostics are **0% GST exempt** per Ministry of Finance healthcare directives.
* Pharmaceutical dispensations compute a concessional **5% GST** on invoices.

---

## 5. System Administration & Provider Credentials

| Role | Username / ID | Password | Profile / Details |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin` | `admin123` | System Administrator & Policy Governor |
| **Government** | `govt_officer` | `govt123` | Ayushman Bharat Directorate Officer |
| **Doctor** | `dr_kadam` | `doc123` | Dr. S. Kadam, MD (ID: `DOC-2026-0001`, Apex Multi-Speciality Hospital) |
| **Pathology** | `city_pathology` | `lab123` | City Care Diagnostics & Imaging (ID: `LAB-2026-0001`, NABL Accredited) |
| **Pharmacy** | `apex_pharmacy` | `med123` | Apex Healthcare Chemists (ID: `PHARM-2026-0001`, FDA Licensed) |

*Note: All demo patient IDs and demo test records have been purged. Patients register securely via the Registration page (`pages/register.html`) using their own Indian PAN card.*

---

## 6. How to Run the System

### Option A: Unified Launcher (Recommended)
From the project root:
```powershell
python run_system.py
```
This automatically boots:
* **Django REST API Backend**: `http://127.0.0.1:8000/api/`
* **Web Frontend Application**: `http://localhost:3000/`

---

### Option B: Manual Startup

#### Step 1: Start Django Backend
```powershell
cd backend
python manage.py migrate
python manage.py seed_data
python manage.py runserver 127.0.0.1:8000
```

#### Step 2: Start Frontend Web Server
In a separate terminal:
```powershell
node server.js
```
Open your browser at `http://localhost:3000/` (or double click `frontend/index.html`).

---

## 7. Running the Automated Test Suite

To verify all core business flows, duplicate PAN prevention, fund distribution math, AI doctor recommendations, and 10% Health Protection Fund ledger consistency:
```powershell
cd backend
python manage.py test tests_integration tests_health_protection
```
Expected output:
```text
Creating test database for alias 'default'...
......................
----------------------------------------------------------------------
Ran 22 tests in 4.602s

OK
Destroying test database for alias 'default'...
Found 22 test(s).
System check identified no issues (0 silenced).
```

---

## 8. REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | Register user or provider account |
| `POST` | `/api/auth/login/` | Authenticate user & issue JWT access + refresh tokens |
| `POST` | `/api/auth/send-otp/` | Request OTP verification code |
| `GET` | `/api/patients/` | Search and list patients |
| `POST` | `/api/patients/` | Enroll patient with PAN check & deduplication |
| `GET` | `/api/patients/lookup/?query=` | Fast lookup by Patient ID, PAN, or Mobile |
| `GET` | `/api/patients/<id>/centralized-record/` | Consolidated longitudinal medical journey with HPF snapshot |
| `GET` | `/api/doctors/stats/` | Doctor consultation statistics |
| `GET` | `/api/doctors/list/` | List empanelled doctors with availability and fees |
| `POST` | `/api/doctors/recommendations/` | AI-assisted specialist recommendation & ranked doctor profiles |
| `POST` | `/api/doctors/ai/recommend/` | AI symptom-to-specialty matching with emergency red-flag triage |
| `POST` | `/api/doctors/appointments/` | Atomic appointment booking & sequential queue token issuance |
| `GET` | `/api/doctors/queue/` | Live doctor token queue |
| `POST` | `/api/doctors/consultations/` | Record diagnosis, treatment, and prescription |
| `POST` | `/api/pathology/reports/` | Upload and certify laboratory investigation |
| `POST` | `/api/pharmacy/transactions/` | Dispense medication, generate GST invoice & auto-credit HPF |
| `GET` | `/api/government/schemes/` | List and create government healthcare schemes |
| `POST` | `/api/funds/allocate/` | Calculate & approve distributed fund settlement |
| `GET` | `/api/funds/protection-account/<id>/` | View patient 10% Health Protection Fund balance & breakdown |
| `GET` | `/api/funds/protection-transactions/<id>/` | Auditable immutable ledger of contributions, withdrawals & reversals |
| `GET` | `/api/funds/protection-rules/` | Configurable service category allocation percentages (default 10%) |
| `GET/POST`| `/api/funds/claims/` | List claims or submit new future healthcare expense claim |
| `POST` | `/api/funds/claims/<ref>/review/` | Administrator review, approval & settlement/payout of healthcare claims |
| `POST` | `/api/insurance/claims/` | Submit secondary deficit insurance claim |
| `POST` | `/api/payments/` | Process smart payment & auto-credit 10% to Health Protection Fund |
| `GET` | `/api/payments/receipt/<txn>/` | Detailed digital receipt with HPF contribution breakdown |
| `GET` | `/api/reports/financial-overview/` | Platform-wide financial overview including HPF aggregate metrics |
| `GET` | `/api/reports/patient/<id>/` | Centralized JSON patient health and fund report |
| `GET` | `/api/reports/pdf/<id>/` | Download official certified ReportLab PDF report |
| `GET` | `/api/reports/csv/<id>/` | Download itemized CSV report with HPF ledger |
>>>>>>> 1db6995 (Configure PatientCare for 24/7 cloud production deployment on Render and Vercel)
