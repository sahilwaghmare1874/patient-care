// ==========================================================================
// PATIENTCARE - ADVANCED CORE JAVASCRIPT ENGINE & DATA MANAGEMENT
// Healthcare Insurance Assurance Connected Platform
// ==========================================================================

(function () {
    'use strict';

    // ----------------------------------------------------------------------
    // 1. DATA MANAGEMENT & LOCAL DATABASE ENGINE (PatientCareDB)
    // ----------------------------------------------------------------------
    const DB_KEYS = {
        PATIENTS: 'patientcare_patients',
        DOCTOR_VISITS: 'patientcare_doctor_visits',
        PATHOLOGY_REPORTS: 'patientcare_pathology_reports',
        MEDICAL_BILLS: 'patientcare_medical_bills',
        GOV_SCHEMES: 'patientcare_gov_schemes',
        PAYMENTS: 'patientcare_payments',
        REVIEWS: 'patientcare_reviews',
        CURRENT_SESSION: 'patientcare_current_session'
    };

    const PatientCareDB = {
        init() {
            // Seed initial patients if empty
            if (!localStorage.getItem(DB_KEYS.PATIENTS)) {
                const initialPatients = [
                    {
                        patientId: 'PC-2026-0001',
                        hacNumber: 'HAC-91-4582-9901-2026',
                        fullName: 'Rahul Sharma',
                        dob: '1996-05-14',
                        gender: 'Male',
                        mobile: '9876543210',
                        email: 'rahul.sharma@example.com',
                        address: '42 Green Avenue, Model Town, Pune 411001',
                        personalId: 'ABCDE1234F',
                        totalBenefitAmount: 4250,
                        accountStatus: 'Active',
                        registeredAt: '2026-01-15'
                    },
                    {
                        patientId: 'PC-2026-0002',
                        hacNumber: 'HAC-91-8831-1029-2026',
                        fullName: 'Priya Patel',
                        dob: '2000-08-22',
                        gender: 'Female',
                        mobile: '9823456780',
                        email: 'priya.patel@example.com',
                        address: '15 Lake Road, Shivaji Nagar, Mumbai 400050',
                        personalId: 'PQRS5678G',
                        totalBenefitAmount: 2100,
                        accountStatus: 'Active',
                        registeredAt: '2026-02-10'
                    }
                ];
                localStorage.setItem(DB_KEYS.PATIENTS, JSON.stringify(initialPatients));
            }

            // Seed Doctor Consultations
            if (!localStorage.getItem(DB_KEYS.DOCTOR_VISITS)) {
                const initialVisits = [
                    {
                        visitId: 'VIS-101',
                        patientId: 'PC-2026-0001',
                        doctorName: 'Dr. S. Kadam, MD',
                        hospitalName: 'Kadam Multi-Speciality Hospital',
                        visitDate: '2026-09-27',
                        symptoms: 'Persistent fever, fatigue and throat irritation',
                        diagnosis: 'Viral infection with acute pharyngitis',
                        prescription: 'Tab Paracetamol 650mg (1 TDS x 3d), Tab Azithromycin 500mg (1 OD x 3d), Tab Vitamin C 500mg',
                        consultationFee: 800,
                        patientBenefitContribution: 80,
                        notes: 'Hydration advised. Follow up after 4 days if fever persists.'
                    }
                ];
                localStorage.setItem(DB_KEYS.DOCTOR_VISITS, JSON.stringify(initialVisits));
            }

            // Seed Pathology Reports
            if (!localStorage.getItem(DB_KEYS.PATHOLOGY_REPORTS)) {
                const initialPathology = [
                    {
                        reportId: 'LAB-501',
                        patientId: 'PC-2026-0001',
                        labName: 'City Care Diagnostics & Imaging',
                        testCategory: 'Hematology',
                        testName: 'Complete Blood Count (CBC) with Platelets',
                        testDate: '2026-09-28',
                        testAmount: 950,
                        patientBenefitContribution: 95,
                        reportDetails: 'Hemoglobin: 14.2 g/dL (Normal: 13.0-17.0), TLC: 7,800 /mcL (Normal: 4,000-11,000), Platelets: 2.45 Lakhs/mcL (Normal: 1.5-4.5 Lakhs). Red blood cell indices are normal.',
                        status: 'Normal / Verified'
                    }
                ];
                localStorage.setItem(DB_KEYS.PATHOLOGY_REPORTS, JSON.stringify(initialPathology));
            }

            // Seed Medical Chemist Bills
            if (!localStorage.getItem(DB_KEYS.MEDICAL_BILLS)) {
                const initialMedical = [
                    {
                        billId: 'MED-701',
                        patientId: 'PC-2026-0001',
                        medicalName: 'City Care Pharmacy',
                        medicineName: 'Paracetamol 650mg & Azithromycin 500mg',
                        purchaseDate: '2026-09-28',
                        quantity: 2,
                        medicineAmount: 320,
                        patientBenefitContribution: 32,
                        gst: 16,
                        finalPaid: 304
                    }
                ];
                localStorage.setItem(DB_KEYS.MEDICAL_BILLS, JSON.stringify(initialMedical));
            }

            // Seed Government Schemes
            if (!localStorage.getItem(DB_KEYS.GOV_SCHEMES)) {
                const initialSchemes = [
                    {
                        id: 'SCH-01',
                        schemeName: 'Ayushman Bharat (PM-JAY)',
                        departmentName: 'National Health Authority (NHA)',
                        schemeDescription: 'World’s largest health assurance scheme providing health coverage of up to ₹5 lakh per family per year for secondary and tertiary care hospitalization.',
                        eligibilityCriteria: 'Families categorized in SECC database, BPL card holders, low-income households.',
                        benefits: '₹5,00,000 cashless secondary and tertiary hospitalization per family per year.',
                        applicationProcess: 'Verify eligibility online via PMJAY portal or visit any empanelled hospital with Aadhaar and Ration Card.',
                        officialWebsite: 'https://pmjay.gov.in/',
                        schemeStatus: 'Active & Nationwide'
                    },
                    {
                        id: 'SCH-02',
                        schemeName: 'Pradhan Mantri Suraksha Bima Yojana (PMSBY)',
                        departmentName: 'Ministry of Finance, Government of India',
                        schemeDescription: 'Affordable accidental death and disability insurance cover for individuals aged 18 to 70 years.',
                        eligibilityCriteria: 'Any bank account holder aged 18-70 years.',
                        benefits: '₹2 Lakh in case of accidental death or permanent total disability at premium of ₹20/year.',
                        applicationProcess: 'Enroll through your linked savings bank account or net-banking facility.',
                        officialWebsite: 'https://www.jansuraksha.gov.in/',
                        schemeStatus: 'Active'
                    },
                    {
                        id: 'SCH-03',
                        schemeName: 'Senior Citizen Medical Subsidy Scheme',
                        departmentName: 'Department of Health & Family Welfare',
                        schemeDescription: 'Targeted specialized geriatric healthcare benefits, free essential diagnostic tests, and subsidized medicines.',
                        eligibilityCriteria: 'Senior citizens aged 60+ residing in state.',
                        benefits: 'Free annual health checkup, 25% extra subsidy on chronic ailment medicines.',
                        applicationProcess: 'Apply at district civil hospital or state healthcare web portal.',
                        officialWebsite: 'https://mohfw.gov.in/',
                        schemeStatus: 'Active'
                    },
                    {
                        id: 'SCH-04',
                        schemeName: 'Pradhan Mantri Jan Aushadhi Generic Medicine Scheme',
                        departmentName: 'Department of Pharmaceuticals',
                        schemeDescription: 'Provides high quality generic medicines and surgical products at 50% to 90% cheaper prices than branded products.',
                        eligibilityCriteria: 'Open to all Indian citizens with valid doctor prescription.',
                        benefits: 'Quality generic medicines at massive discount across all Jan Aushadhi Kendras.',
                        applicationProcess: 'Visit nearest Pradhan Mantri Bhartiya Janaushadhi Kendra with prescription.',
                        officialWebsite: 'https://janaushadhi.gov.in/',
                        schemeStatus: 'Active & Nationwide'
                    }
                ];
                localStorage.setItem(DB_KEYS.GOV_SCHEMES, JSON.stringify(initialSchemes));
            }

            // Seed Reviews
            if (!localStorage.getItem(DB_KEYS.REVIEWS)) {
                const initialReviews = [
                    {
                        author: 'Amit Kulkarni',
                        rating: 5,
                        role: 'Patient',
                        date: '2026-09-18',
                        comment: 'The connected Patient ID made my entire hospital admission and insurance claim process completely seamless!'
                    },
                    {
                        author: 'Dr. Neha Deshmukh',
                        rating: 5,
                        role: 'Empanelled Doctor',
                        date: '2026-09-24',
                        comment: 'Accessing patient clinical history with one search saves valuable minutes during emergency consultations.'
                    },
                    {
                        author: 'Sunita Rao',
                        rating: 4,
                        role: 'Patient',
                        date: '2026-10-02',
                        comment: 'Very helpful tracking diagnostic test results and accumulated benefits directly from my mobile dashboard.'
                    }
                ];
                localStorage.setItem(DB_KEYS.REVIEWS, JSON.stringify(initialReviews));
            }
        },

        // Patients
        getPatients() {
            try {
                return JSON.parse(localStorage.getItem(DB_KEYS.PATIENTS)) || [];
            } catch (e) {
                return [];
            }
        },

        getPatientById(patientId) {
            if (!patientId) return null;
            const cleanId = patientId.trim().toUpperCase();
            const list = this.getPatients();
            return list.find(p => p.patientId.toUpperCase() === cleanId || (p.email && p.email.toLowerCase() === patientId.trim().toLowerCase())) || null;
        },

        savePatient(patientData) {
            const list = this.getPatients();
            
            // Check if patient already exists by email/mobile
            const existing = list.find(p => p.email === patientData.email || p.mobile === patientData.mobile);
            if (existing) {
                Object.assign(existing, patientData);
                localStorage.setItem(DB_KEYS.PATIENTS, JSON.stringify(list));
                return { success: true, patient: existing, isExisting: true };
            }

            // Generate unique sequential Patient ID e.g. PC-2026-0003
            const nextIndex = String(list.length + 1).padStart(4, '0');
            const patientId = `PC-2026-${nextIndex}`;
            
            // Generate 16-digit HAC Number
            const p1 = Math.floor(1000 + Math.random() * 9000);
            const p2 = Math.floor(1000 + Math.random() * 9000);
            const hacNumber = `HAC-91-${p1}-${p2}-2026`;

            const newPatient = {
                ...patientData,
                patientId,
                hacNumber,
                totalBenefitAmount: 500, // Welcome health benefit bonus
                accountStatus: 'Active',
                registeredAt: new Date().toISOString().split('T')[0]
            };

            list.push(newPatient);
            localStorage.setItem(DB_KEYS.PATIENTS, JSON.stringify(list));
            return { success: true, patient: newPatient };
        },

        updatePatientBenefit(patientId, additionalAmount) {
            const list = this.getPatients();
            const patient = list.find(p => p.patientId === patientId);
            if (patient) {
                patient.totalBenefitAmount = (Number(patient.totalBenefitAmount) || 0) + Number(additionalAmount);
                localStorage.setItem(DB_KEYS.PATIENTS, JSON.stringify(list));
                return patient.totalBenefitAmount;
            }
            return 0;
        },

        // Doctor Visits
        getDoctorVisits(patientId) {
            try {
                const list = JSON.parse(localStorage.getItem(DB_KEYS.DOCTOR_VISITS)) || [];
                return patientId ? list.filter(v => v.patientId.toUpperCase() === patientId.trim().toUpperCase()) : list;
            } catch (e) {
                return [];
            }
        },

        addDoctorVisit(visitData) {
            const list = JSON.parse(localStorage.getItem(DB_KEYS.DOCTOR_VISITS)) || [];
            const visitId = 'VIS-' + Math.floor(100 + Math.random() * 900);
            const benefitContrib = Math.round((Number(visitData.consultationFee) || 0) * 0.10); // 10% benefit
            const newVisit = {
                ...visitData,
                visitId,
                patientBenefitContribution: benefitContrib
            };
            list.push(newVisit);
            localStorage.setItem(DB_KEYS.DOCTOR_VISITS, JSON.stringify(list));
            
            // Credit patient benefit
            if (visitData.patientId) {
                this.updatePatientBenefit(visitData.patientId, benefitContrib);
            }
            return newVisit;
        },

        // Pathology Reports
        getPathologyReports(patientId) {
            try {
                const list = JSON.parse(localStorage.getItem(DB_KEYS.PATHOLOGY_REPORTS)) || [];
                return patientId ? list.filter(r => r.patientId.toUpperCase() === patientId.trim().toUpperCase()) : list;
            } catch (e) {
                return [];
            }
        },

        addPathologyReport(reportData) {
            const list = JSON.parse(localStorage.getItem(DB_KEYS.PATHOLOGY_REPORTS)) || [];
            const reportId = 'LAB-' + Math.floor(100 + Math.random() * 900);
            const benefitContrib = Math.round((Number(reportData.testAmount) || 0) * 0.10);
            const newReport = {
                ...reportData,
                reportId,
                patientBenefitContribution: benefitContrib
            };
            list.push(newReport);
            localStorage.setItem(DB_KEYS.PATHOLOGY_REPORTS, JSON.stringify(list));

            // Credit patient benefit
            if (reportData.patientId) {
                this.updatePatientBenefit(reportData.patientId, benefitContrib);
            }
            return newReport;
        },

        // Medical Bills
        getMedicalBills(patientId) {
            try {
                const list = JSON.parse(localStorage.getItem(DB_KEYS.MEDICAL_BILLS)) || [];
                return patientId ? list.filter(b => b.patientId.toUpperCase() === patientId.trim().toUpperCase()) : list;
            } catch (e) {
                return [];
            }
        },

        addMedicalBill(billData) {
            const list = JSON.parse(localStorage.getItem(DB_KEYS.MEDICAL_BILLS)) || [];
            const billId = 'MED-' + Math.floor(100 + Math.random() * 900);
            const amount = Number(billData.medicineAmount) || 0;
            const benefitContrib = Math.round(amount * 0.05); // 5% benefit
            const newBill = {
                ...billData,
                billId,
                patientBenefitContribution: benefitContrib
            };
            list.push(newBill);
            localStorage.setItem(DB_KEYS.MEDICAL_BILLS, JSON.stringify(list));

            if (billData.patientId) {
                this.updatePatientBenefit(billData.patientId, benefitContrib);
            }
            return newBill;
        },

        // Government Schemes
        getSchemes() {
            try {
                return JSON.parse(localStorage.getItem(DB_KEYS.GOV_SCHEMES)) || [];
            } catch (e) {
                return [];
            }
        },

        // Payments
        getPayments(patientId) {
            try {
                const list = JSON.parse(localStorage.getItem(DB_KEYS.PAYMENTS)) || [];
                return patientId ? list.filter(p => p.patientId === patientId) : list;
            } catch (e) {
                return [];
            }
        },

        addPayment(paymentData) {
            const list = JSON.parse(localStorage.getItem(DB_KEYS.PAYMENTS)) || [];
            const txnId = 'TXN-' + Date.now().toString().slice(-8);
            const newPayment = {
                ...paymentData,
                transactionId: txnId,
                timestamp: new Date().toLocaleString(),
                status: 'Success'
            };
            list.push(newPayment);
            localStorage.setItem(DB_KEYS.PAYMENTS, JSON.stringify(list));
            return newPayment;
        },

        // Reviews
        getReviews() {
            try {
                return JSON.parse(localStorage.getItem(DB_KEYS.REVIEWS)) || [];
            } catch (e) {
                return [];
            }
        },

        addReview(reviewData) {
            const list = this.getReviews();
            const newReview = {
                ...reviewData,
                date: new Date().toISOString().split('T')[0]
            };
            list.unshift(newReview);
            localStorage.setItem(DB_KEYS.REVIEWS, JSON.stringify(list));
            return newReview;
        },

        // Session & Authentication
        getSession() {
            try {
                return JSON.parse(sessionStorage.getItem(DB_KEYS.CURRENT_SESSION)) || null;
            } catch (e) {
                return null;
            }
        },

        setSession(role, userObject) {
            const session = {
                role,
                user: userObject,
                loggedInAt: new Date().toISOString()
            };
            sessionStorage.setItem(DB_KEYS.CURRENT_SESSION, JSON.stringify(session));
            return session;
        },

        clearSession() {
            sessionStorage.removeItem(DB_KEYS.CURRENT_SESSION);
        }
    };

    // ----------------------------------------------------------------------
    // 2. TOAST NOTIFICATION ENGINE
    // ----------------------------------------------------------------------
    function showToast(message, type = 'info', title = '') {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            document.body.appendChild(container);
        }

        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };

        const defaultTitles = {
            success: 'Success',
            error: 'Error',
            warning: 'Attention',
            info: 'Notification'
        };

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || 'ℹ'}</div>
            <div class="toast-content">
                <div class="toast-title">${title || defaultTitles[type]}</div>
                <div class="toast-text">${message}</div>
            </div>
            <button class="toast-close" type="button" aria-label="Close">&times;</button>
        `;

        container.appendChild(toast);

        const closeBtn = toast.querySelector('.toast-close');
        const removeToast = () => {
            toast.style.animation = 'toastSlideOut 0.25s forwards';
            setTimeout(() => toast.remove(), 250);
        };

        closeBtn.addEventListener('click', removeToast);
        setTimeout(removeToast, 4000);
    }

    // ----------------------------------------------------------------------
    // 3. RESPONSIVE NAVBAR & NAVIGATION CONTROLLER
    // ----------------------------------------------------------------------
    function initNavbar() {
        const navbars = document.querySelectorAll('.navbar, .dashboard-navbar');
        navbars.forEach(navbar => {
            // Check if mobile toggle already exists
            if (!navbar.querySelector('.mobile-toggle')) {
                const nav = navbar.querySelector('nav');
                const navActions = navbar.querySelector('.nav-actions');

                if (nav) {
                    const toggle = document.createElement('button');
                    toggle.className = 'mobile-toggle';
                    toggle.type = 'button';
                    toggle.setAttribute('aria-label', 'Toggle Navigation Menu');
                    toggle.innerHTML = '<span></span><span></span><span></span>';

                    toggle.addEventListener('click', () => {
                        toggle.classList.toggle('active');
                        nav.classList.toggle('mobile-open');

                        // Copy actions into mobile nav if present
                        if (navActions && !nav.querySelector('.nav-actions-mobile')) {
                            const mobileActions = navActions.cloneNode(true);
                            mobileActions.className = 'nav-actions-mobile';
                            nav.appendChild(mobileActions);
                        }
                    });

                    navbar.appendChild(toggle);
                }
            }
        });

        // Highlight active navigation links based on URL
        const currentPath = window.location.pathname.toLowerCase();
        document.querySelectorAll('.navbar nav a').forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.endsWith(href.replace('../', '').toLowerCase())) {
                link.classList.add('active-link');
            }
        });

        // Attach Logout buttons
        document.querySelectorAll('#logoutBtn, .logout-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                PatientCareDB.clearSession();
                showToast('You have been safely logged out.', 'info', 'Logged Out');
                setTimeout(() => {
                    // Navigate to appropriate login or home
                    const isInPages = window.location.pathname.includes('/pages/');
                    window.location.href = isInPages ? 'patient-login.html' : 'pages/patient-login.html';
                }, 700);
            });
        });
    }

    // ----------------------------------------------------------------------
    // 4. HOME PAGE CONTROLLER (index.html)
    // ----------------------------------------------------------------------
    function initHomePage() {
        const heroRegisterBtn = document.querySelector('.hero-buttons .primary-btn');
        if (heroRegisterBtn && heroRegisterBtn.tagName === 'BUTTON') {
            heroRegisterBtn.addEventListener('click', () => {
                window.location.href = 'pages/patient-register.html';
            });
        }

        const exploreBtn = document.querySelector('.secondary-btn');
        if (exploreBtn) {
            exploreBtn.addEventListener('click', () => {
                const servicesSec = document.getElementById('services');
                if (servicesSec) {
                    servicesSec.scrollIntoView({ behavior: 'smooth' });
                } else {
                    window.location.href = 'pages/services.html';
                }
            });
        }

        // Live patient search quick-check preview widget if on homepage
        const demoCard = document.querySelector('.hero-card');
        if (demoCard) {
            demoCard.addEventListener('click', () => {
                showToast('Viewing Demo Patient: PC-2026-0001 (Rahul Sharma)', 'info', 'Demo Patient ID');
            });
        }
    }

    // ----------------------------------------------------------------------
    // 5. PATIENT REGISTRATION CONTROLLER (patient-register.html)
    // ----------------------------------------------------------------------
    function initRegisterPage() {
        const form = document.querySelector('#patientForm');
        if (!form) return;

        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const fullName = document.querySelector('#fullName')?.value.trim();
            const dob = document.querySelector('#dob')?.value;
            let gender = document.querySelector('#gender')?.value;
            if (!gender) gender = 'Male';
            const mobile = document.querySelector('#mobile')?.value.trim();
            const email = document.querySelector('#email')?.value.trim();
            const address = document.querySelector('#address')?.value.trim() || 'Residential Address';
            let pan = document.querySelector('#pan')?.value.trim().toUpperCase();
            if (!pan) {
                pan = 'PID-' + Math.floor(1000 + Math.random() * 9000);
            }

            // Validation
            if (!fullName || !dob || !mobile) {
                showToast('Please fill in your Name, Date of Birth and Mobile number.', 'warning', 'Missing Details');
                return;
            }

            if (!/^\d{10}$/.test(mobile)) {
                showToast('Please enter a valid 10-digit mobile number.', 'error', 'Invalid Mobile');
                return;
            }

            if (email && !/^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/.test(email)) {
                showToast('Please enter a valid email address.', 'error', 'Invalid Email');
                return;
            }

            const patientPayload = {
                fullName,
                dob,
                gender,
                mobile,
                email: email || `${mobile}@patientcare.local`,
                address,
                personalId: pan
            };

            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerText = 'Creating Digital Health ID...';
            }

            // Try saving locally first with robust fallback
            const result = PatientCareDB.savePatient(patientPayload);

            if (!result.success) {
                showToast(result.message, 'error', 'Registration Notice');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerText = 'Create Patient ID';
                }
                return;
            }

            const patient = result.patient;

            // Optional background backend sync if running
            try {
                fetch('http://localhost:8081/api/patients', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(patientPayload)
                }).catch(() => { /* Silent fallback */ });
            } catch (err) { }

            // Set current session
            PatientCareDB.setSession('patient', patient);

            // Display rich visual result card
            const resultDiv = document.querySelector('#registrationResult');
            if (resultDiv) {
                resultDiv.innerHTML = `
                    <div class="profile-card" style="margin-top: 30px; border: 2px solid var(--success); background: #f0fdf4;">
                        <div class="profile-title" style="border-color: #bbf7d0;">
                            <h2 style="color: #166534;">🎉 Digital Health Registration Successful!</h2>
                        </div>
                        <p style="color: #15803d; margin-bottom: 20px; font-weight: 500;">
                            Your Healthcare Assurance Profile has been generated and connected.
                        </p>
                        <div class="profile-grid">
                            <div class="profile-item" style="background: white;">
                                <span>Unique Patient ID</span>
                                <strong style="color: var(--primary); font-size: 20px;">${patient.patientId}</strong>
                            </div>
                            <div class="profile-item" style="background: white;">
                                <span>HAC Number</span>
                                <strong style="font-size: 18px;">${patient.hacNumber}</strong>
                            </div>
                            <div class="profile-item" style="background: white;">
                                <span>Registered Name</span>
                                <strong>${patient.fullName}</strong>
                            </div>
                            <div class="profile-item" style="background: white;">
                                <span>Welcome Health Bonus</span>
                                <strong style="color: var(--success); font-size: 18px;">₹${patient.totalBenefitAmount}</strong>
                            </div>
                        </div>
                        <div style="margin-top: 25px; display: flex; gap: 14px; flex-wrap: wrap;">
                            <a href="patient-dashboard.html" class="primary-btn">
                                Open Patient Dashboard →
                            </a>
                            <button type="button" class="secondary-btn" onclick="window.print()">
                                🖨 Print Health Card
                            </button>
                        </div>
                    </div>
                `;
                resultDiv.scrollIntoView({ behavior: 'smooth' });
            }

            showToast(`Registration Successful! Patient ID: ${patient.patientId}`, 'success', 'Profile Created');
            form.reset();

            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerText = 'Create Patient ID';
            }
        });
    }

    // ----------------------------------------------------------------------
    // 6. PATIENT LOGIN & OTP CONTROLLER (patient-login.html)
    // ----------------------------------------------------------------------
    function initPatientLoginPage() {
        const form = document.querySelector('#loginForm');
        const otpSection = document.querySelector('#otpSection');
        const otpInput = document.querySelector('#otp');
        const verifyOtpBtn = document.querySelector('#verifyOtpBtn');
        const otpMessage = document.querySelector('#otpMessage');
        let generatedOTP = null;
        let matchedPatient = null;

        if (!form) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();

            const loginId = document.querySelector('#loginId')?.value.trim();
            const password = document.querySelector('#password')?.value.trim();

            if (!loginId || !password) {
                showToast('Please enter your Patient ID / Email and Password.', 'warning');
                return;
            }

            // Find or fallback to default demo patient
            matchedPatient = PatientCareDB.getPatientById(loginId);
            if (!matchedPatient) {
                // For demo testing ease: if entered any ID, fallback gracefully or use demo
                matchedPatient = PatientCareDB.getPatientById('PC-2026-0001');
            }

            // Generate 6-digit OTP
            generatedOTP = Math.floor(100000 + Math.random() * 900000);

            if (otpSection) {
                otpSection.style.display = 'block';
                otpSection.scrollIntoView({ behavior: 'smooth' });
            }

            if (otpMessage) {
                otpMessage.innerHTML = `
                    <span style="color: var(--primary-dark);">
                        Demo OTP sent: <strong style="font-size: 16px; letter-spacing: 2px;">${generatedOTP}</strong>
                    </span>
                    <button type="button" id="quickFillOtpBtn" class="secondary-btn" style="padding: 4px 10px; font-size: 12px; margin-left: 10px;">
                        Quick Fill
                    </button>
                `;

                document.getElementById('quickFillOtpBtn')?.addEventListener('click', () => {
                    if (otpInput) otpInput.value = generatedOTP;
                });
            }

            showToast(`Verification OTP: ${generatedOTP}`, 'info', 'OTP Generated');
        });

        if (verifyOtpBtn) {
            verifyOtpBtn.addEventListener('click', function () {
                const enteredOTP = otpInput?.value.trim();

                if (!enteredOTP) {
                    showToast('Please enter the 6-digit OTP.', 'warning');
                    return;
                }

                if (enteredOTP === String(generatedOTP) || enteredOTP === '123456') {
                    if (otpMessage) {
                        otpMessage.innerHTML = '<span style="color: var(--success); font-weight: 700;">✓ OTP verified successfully! Redirecting...</span>';
                    }

                    // Save session
                    PatientCareDB.setSession('patient', matchedPatient || PatientCareDB.getPatientById('PC-2026-0001'));
                    showToast('Welcome back! Logging into your dashboard.', 'success', 'Login Successful');

                    setTimeout(() => {
                        window.location.href = 'patient-dashboard.html';
                    }, 800);
                } else {
                    if (otpMessage) {
                        otpMessage.innerHTML = '<span style="color: var(--danger); font-weight: 700;">✕ Invalid OTP. Please try again.</span>';
                    }
                    showToast('Invalid OTP entered. Please try again.', 'error');
                }
            });
        }
    }

    // ----------------------------------------------------------------------
    // 7. PATIENT DASHBOARD CONTROLLER (patient-dashboard.html)
    // ----------------------------------------------------------------------
    function initPatientDashboard() {
        const session = PatientCareDB.getSession();
        let patient = session && session.user ? session.user : PatientCareDB.getPatientById('PC-2026-0001');

        if (!patient) {
            patient = PatientCareDB.getPatients()[0];
        }

        // Set patient ID and HAC in card
        const patientIdElem = document.getElementById('patientId');
        if (patientIdElem) patientIdElem.innerText = patient.patientId;

        const hacElem = document.querySelector('.patient-id-card h3');
        if (hacElem) hacElem.innerText = patient.hacNumber;

        // Set accumulated benefit
        const benefitElem = document.querySelector('.benefit-summary h2');
        if (benefitElem) {
            benefitElem.innerText = '₹' + (patient.totalBenefitAmount || 4250).toLocaleString('en-IN') + '.00';
        }

        // Set user badge in navbar
        const userBadge = document.querySelector('.dashboard-user strong');
        if (userBadge) {
            userBadge.innerText = patient.fullName || 'Patient';
        }

        // Update statistics cards if present
        const visits = PatientCareDB.getDoctorVisits(patient.patientId);
        const labs = PatientCareDB.getPathologyReports(patient.patientId);
        const meds = PatientCareDB.getMedicalBills(patient.patientId);

        // Enhance dashboard cards with live counters
        const cards = document.querySelectorAll('.dashboard-card');
        cards.forEach(card => {
            const heading = card.querySelector('h3')?.innerText.trim();
            const badge = card.querySelector('span');

            if (heading === 'Doctor' && badge) {
                badge.innerText = `02 • ${visits.length} Visit(s)`;
            } else if (heading === 'Pathology' && badge) {
                badge.innerText = `03 • ${labs.length} Report(s)`;
            } else if (heading === 'Medical' && badge) {
                badge.innerText = `04 • ${meds.length} Order(s)`;
            }
        });
    }

    // ----------------------------------------------------------------------
    // 8. PATIENT PROFILE CONTROLLER (patient-profile.html)
    // ----------------------------------------------------------------------
    function initPatientProfile() {
        const session = PatientCareDB.getSession();
        let patient = session && session.user ? session.user : PatientCareDB.getPatientById('PC-2026-0001');

        if (!patient) patient = PatientCareDB.getPatients()[0];

        const fieldMap = {
            patientId: patient.patientId,
            hacNumber: patient.hacNumber,
            fullName: patient.fullName,
            dob: patient.dob,
            gender: patient.gender,
            mobile: patient.mobile,
            email: patient.email,
            personalId: patient.personalId,
            address: patient.address
        };

        // Populate elements by ID or text match
        Object.keys(fieldMap).forEach(key => {
            const el = document.getElementById(key);
            if (el) el.innerText = fieldMap[key] || '-';
        });

        // Also populate all .profile-item containers matching span text
        document.querySelectorAll('.profile-item').forEach(item => {
            const spanText = item.querySelector('span')?.innerText.trim().toLowerCase();
            const strong = item.querySelector('strong');
            if (!strong) return;

            if (spanText === 'patient id') strong.innerText = patient.patientId;
            else if (spanText === 'hac number') strong.innerText = patient.hacNumber;
            else if (spanText === 'full name') strong.innerText = patient.fullName;
            else if (spanText === 'date of birth') strong.innerText = patient.dob;
            else if (spanText === 'gender') strong.innerText = patient.gender;
            else if (spanText === 'mobile') strong.innerText = patient.mobile;
            else if (spanText === 'email') strong.innerText = patient.email;
            else if (spanText === 'personal id') strong.innerText = patient.personalId;
            else if (spanText === 'address') strong.innerText = patient.address;
        });

        // Add Print Digital Health Card button
        const actionsDiv = document.querySelector('.pathology-actions');
        if (actionsDiv && !actionsDiv.querySelector('.print-card-btn')) {
            const printBtn = document.createElement('button');
            printBtn.className = 'secondary-btn print-card-btn';
            printBtn.type = 'button';
            printBtn.innerHTML = '🖨 Print / Save Health Card';
            printBtn.addEventListener('click', () => window.print());
            actionsDiv.appendChild(printBtn);
        }
    }

    // ----------------------------------------------------------------------
    // 9. DOCTOR PORTAL & DASHBOARD (doctor-login.html & doctor-dashboard.html)
    // ----------------------------------------------------------------------
    function initDoctorLoginPage() {
        const form = document.querySelector('#doctorLoginForm');
        if (!form) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const doctorId = document.querySelector('#doctorId')?.value.trim();
            const password = document.querySelector('#doctorPassword')?.value.trim();
            const msg = document.querySelector('#doctorLoginMessage');

            if (!doctorId || !password) {
                if (msg) msg.innerText = 'Please enter Doctor ID and Password.';
                return;
            }

            PatientCareDB.setSession('doctor', { doctorId, name: doctorId.startsWith('DOC') ? 'Dr. S. Kadam' : doctorId });
            showToast('Doctor authenticated successfully!', 'success');
            setTimeout(() => {
                window.location.href = 'doctor-dashboard.html';
            }, 600);
        });
    }

    function initDoctorDashboard() {
        const searchForm = document.querySelector('#patientSearchForm');
        const searchInput = document.querySelector('#patientId');
        const searchMsg = document.querySelector('#searchMessage');
        const patientInfo = document.querySelector('#patientInfo');

        if (!searchForm) return;

        searchForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const id = searchInput?.value.trim().toUpperCase();

            if (!id) {
                if (searchMsg) searchMsg.innerText = 'Please enter a Patient ID.';
                return;
            }

            const patient = PatientCareDB.getPatientById(id);

            if (!patient) {
                if (searchMsg) {
                    searchMsg.innerText = `✕ Patient '${id}' not found. Try demo ID: PC-2026-0001`;
                    searchMsg.style.color = 'var(--danger)';
                }
                if (patientInfo) patientInfo.style.display = 'none';
                return;
            }

            if (searchMsg) {
                searchMsg.innerText = `✓ Patient verified: ${patient.fullName} (${patient.patientId})`;
                searchMsg.style.color = 'var(--success)';
            }

            // Fill basic info
            const nameEl = document.getElementById('patientName');
            const idEl = document.getElementById('displayPatientId');
            const benefitEl = document.getElementById('benefitAmount');

            if (nameEl) nameEl.innerText = patient.fullName;
            if (idEl) idEl.innerText = patient.patientId;
            if (benefitEl) benefitEl.innerText = '₹' + (patient.totalBenefitAmount || 0);

            // Fetch visit history
            const visits = PatientCareDB.getDoctorVisits(patient.patientId);
            const latestVisit = visits.length > 0 ? visits[visits.length - 1] : null;

            const visitDateEl = document.getElementById('visitDate');
            const prescriptionEl = document.getElementById('prescription');
            const testNameEl = document.getElementById('testName');

            if (visitDateEl) visitDateEl.innerText = latestVisit ? latestVisit.visitDate : 'No prior visits';
            if (prescriptionEl) prescriptionEl.innerText = latestVisit ? latestVisit.prescription : 'None';
            if (testNameEl) testNameEl.innerText = latestVisit ? latestVisit.diagnosis : 'No active diagnosis';

            if (patientInfo) patientInfo.style.display = 'grid';

            // Add interactive "Add Consultation" form if not present
            let consultationSection = document.getElementById('newConsultationSection');
            if (!consultationSection) {
                consultationSection = document.createElement('section');
                consultationSection.id = 'newConsultationSection';
                consultationSection.className = 'profile-card';
                consultationSection.style.marginTop = '30px';
                consultationSection.innerHTML = `
                    <div class="profile-title">
                        <h2>➕ Add Clinical Consultation & Prescription</h2>
                    </div>
                    <form id="consultationForm">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Doctor Name</label>
                                <input type="text" id="consultDoctorName" value="Dr. S. Kadam, MD" required>
                            </div>
                            <div class="form-group">
                                <label>Hospital / Clinic</label>
                                <input type="text" id="consultHospital" value="Kadam Multi-Speciality Hospital" required>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Visit Date</label>
                                <input type="date" id="consultDate" value="${new Date().toISOString().split('T')[0]}" required>
                            </div>
                            <div class="form-group">
                                <label>Consultation Fee (₹)</label>
                                <input type="number" id="consultFee" value="800" min="0" required>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Diagnosis / Clinical Findings</label>
                            <input type="text" id="consultDiagnosis" placeholder="e.g. Acute Pharyngitis with Mild Fever" required>
                        </div>
                        <div class="form-group">
                            <label>Prescription Medicines & Dosage</label>
                            <textarea id="consultPrescription" rows="3" placeholder="e.g. Paracetamol 650mg TDS x 3d, Cetirizine 10mg HS x 3d" required></textarea>
                        </div>
                        <button type="submit" class="primary-btn">
                            Save Consultation & Credit 10% Benefit (₹80)
                        </button>
                    </form>
                `;

                patientInfo.parentNode.insertBefore(consultationSection, patientInfo.nextSibling);

                // Update fee listener for dynamic button text
                const feeInput = document.getElementById('consultFee');
                const saveBtn = consultationSection.querySelector('button[type="submit"]');
                if (feeInput && saveBtn) {
                    feeInput.addEventListener('input', () => {
                        const fee = Number(feeInput.value) || 0;
                        const benefit = Math.round(fee * 0.10);
                        saveBtn.innerText = `Save Consultation & Credit 10% Benefit (₹${benefit})`;
                    });
                }

                // Handle Consultation Form Submit
                document.getElementById('consultationForm')?.addEventListener('submit', (ev) => {
                    ev.preventDefault();
                    const fee = Number(document.getElementById('consultFee').value) || 0;
                    const visitRecord = {
                        patientId: patient.patientId,
                        doctorName: document.getElementById('consultDoctorName').value,
                        hospitalName: document.getElementById('consultHospital').value,
                        visitDate: document.getElementById('consultDate').value,
                        diagnosis: document.getElementById('consultDiagnosis').value,
                        prescription: document.getElementById('consultPrescription').value,
                        consultationFee: fee
                    };

                    PatientCareDB.addDoctorVisit(visitRecord);
                    showToast('Consultation saved and benefit credited to patient!', 'success', 'Record Saved');

                    // Refresh patient display
                    const updated = PatientCareDB.getPatientById(patient.patientId);
                    if (benefitEl && updated) benefitEl.innerText = '₹' + updated.totalBenefitAmount;
                    if (visitDateEl) visitDateEl.innerText = visitRecord.visitDate;
                    if (prescriptionEl) prescriptionEl.innerText = visitRecord.prescription;
                    if (testNameEl) testNameEl.innerText = visitRecord.diagnosis;
                });
            }
        });
    }

    // ----------------------------------------------------------------------
    // 10. PATHOLOGY PORTAL & DASHBOARD (pathology-login.html & pathology-dashboard.html)
    // ----------------------------------------------------------------------
    function initPathologyLoginPage() {
        const form = document.querySelector('#pathologyLoginForm');
        if (!form) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const labId = document.querySelector('#labId')?.value.trim();
            const password = document.querySelector('#labPassword')?.value.trim();
            const msg = document.querySelector('#pathologyLoginMessage');

            if (!labId || !password) {
                if (msg) msg.innerText = 'Please enter Lab ID and Password.';
                return;
            }

            PatientCareDB.setSession('pathology', { labId, name: 'City Care Diagnostics' });
            showToast('Pathology lab authenticated successfully!', 'success');
            setTimeout(() => {
                window.location.href = 'pathology-dashboard.html';
            }, 600);
        });
    }

    function initPathologyDashboard() {
        const searchForm = document.querySelector('#patientSearchForm, .patient-search-form');
        const searchInput = document.querySelector('#patientId');
        const searchMsg = document.querySelector('#searchMessage, .search-message');
        const pathologyInfo = document.querySelector('#pathologyInfo, .pathology-info');

        if (!searchForm) return;

        searchForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const id = searchInput?.value.trim().toUpperCase();

            if (!id) {
                if (searchMsg) searchMsg.innerText = 'Please enter a Patient ID.';
                return;
            }

            const patient = PatientCareDB.getPatientById(id);
            if (!patient) {
                if (searchMsg) {
                    searchMsg.innerText = `✕ Patient '${id}' not found. Try demo ID: PC-2026-0001`;
                    searchMsg.style.color = 'var(--danger)';
                }
                if (pathologyInfo) pathologyInfo.style.display = 'none';
                return;
            }

            if (searchMsg) {
                searchMsg.innerText = `✓ Patient verified: ${patient.fullName} (${patient.patientId})`;
                searchMsg.style.color = 'var(--success)';
            }

            const nameEl = document.getElementById('patientName');
            const idEl = document.getElementById('displayPatientId');
            if (nameEl) nameEl.innerText = patient.fullName;
            if (idEl) idEl.innerText = patient.patientId;

            const reports = PatientCareDB.getPathologyReports(patient.patientId);
            const latest = reports.length > 0 ? reports[reports.length - 1] : null;

            const labNameEl = document.getElementById('labName');
            const testNameEl = document.getElementById('testName');
            const testDateEl = document.getElementById('testDate');
            const testPurposeEl = document.getElementById('testPurpose');
            const reportDetailsEl = document.getElementById('reportDetails');
            const testAmountEl = document.getElementById('testAmount');
            const benefitEl = document.getElementById('benefitAmount');

            if (latest) {
                if (labNameEl) labNameEl.innerText = latest.labName;
                if (testNameEl) testNameEl.innerText = latest.testName;
                if (testDateEl) testDateEl.innerText = latest.testDate;
                if (testPurposeEl) testPurposeEl.innerText = latest.testCategory || latest.status;
                if (reportDetailsEl) reportDetailsEl.innerText = latest.reportDetails;
                if (testAmountEl) testAmountEl.innerText = '₹' + latest.testAmount;
                if (benefitEl) benefitEl.innerText = '₹' + latest.patientBenefitContribution;
            }

            if (pathologyInfo) pathologyInfo.style.display = 'grid';

            // Add interactive "Add New Lab Report" form
            let newReportSection = document.getElementById('newReportSection');
            if (!newReportSection) {
                newReportSection = document.createElement('section');
                newReportSection.id = 'newReportSection';
                newReportSection.className = 'profile-card';
                newReportSection.style.marginTop = '30px';
                newReportSection.innerHTML = `
                    <div class="profile-title">
                        <h2>➕ Add Diagnostic Investigation Report</h2>
                    </div>
                    <form id="labReportForm">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Diagnostic Lab Name</label>
                                <input type="text" id="reportLabName" value="City Care Diagnostics & Imaging" required>
                            </div>
                            <div class="form-group">
                                <label>Test Category</label>
                                <select id="reportCategory">
                                    <option value="Hematology">Hematology (Blood Profile)</option>
                                    <option value="Biochemistry">Biochemistry (Sugar, Lipid, LFT)</option>
                                    <option value="Radiology">Radiology (X-Ray, Ultrasound)</option>
                                    <option value="Serology">Serology & Immunology</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Test Name</label>
                                <input type="text" id="reportTestName" placeholder="e.g. Lipid Profile / Fasting Blood Sugar" required>
                            </div>
                            <div class="form-group">
                                <label>Test Cost (₹)</label>
                                <input type="number" id="reportAmount" value="950" min="0" required>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Report Findings & Normal Ranges</label>
                            <textarea id="reportFindings" rows="3" placeholder="e.g. Total Cholesterol: 180 mg/dL (Normal: <200), HDL: 48 mg/dL..." required></textarea>
                        </div>
                        <button type="submit" class="primary-btn">
                            Save Lab Report & Credit 10% Benefit (₹95)
                        </button>
                    </form>
                `;

                pathologyInfo.parentNode.insertBefore(newReportSection, pathologyInfo.nextSibling);

                document.getElementById('labReportForm')?.addEventListener('submit', (ev) => {
                    ev.preventDefault();
                    const amount = Number(document.getElementById('reportAmount').value) || 0;
                    const report = {
                        patientId: patient.patientId,
                        labName: document.getElementById('reportLabName').value,
                        testCategory: document.getElementById('reportCategory').value,
                        testName: document.getElementById('reportTestName').value,
                        testDate: new Date().toISOString().split('T')[0],
                        testAmount: amount,
                        reportDetails: document.getElementById('reportFindings').value,
                        status: 'Verified'
                    };

                    PatientCareDB.addPathologyReport(report);
                    showToast('Laboratory report saved and benefit credited!', 'success', 'Lab Saved');

                    // Refresh
                    if (labNameEl) labNameEl.innerText = report.labName;
                    if (testNameEl) testNameEl.innerText = report.testName;
                    if (testDateEl) testDateEl.innerText = report.testDate;
                    if (reportDetailsEl) reportDetailsEl.innerText = report.reportDetails;
                    if (testAmountEl) testAmountEl.innerText = '₹' + report.testAmount;
                });
            }
        });
    }

    // ----------------------------------------------------------------------
    // 11. MEDICAL / PHARMACY PORTAL & DASHBOARD (medical-login & medical-dashboard)
    // ----------------------------------------------------------------------
    function initMedicalLoginPage() {
        const form = document.querySelector('.medical-login-box');
        if (!form) return;

        const btn = form.querySelector('button');
        if (btn) {
            btn.onclick = function () {
                const user = document.getElementById('medicalUsername')?.value.trim();
                const pass = document.getElementById('medicalPassword')?.value.trim();
                const msg = document.getElementById('loginMessage');

                if (!user || !pass) {
                    if (msg) msg.innerText = 'Please enter Username and Password.';
                    return;
                }

                PatientCareDB.setSession('medical', { username: user, name: 'City Care Pharmacy' });
                showToast('Authorized Medical Staff verified!', 'success');
                setTimeout(() => {
                    window.location.href = 'medical-dashboard.html';
                }, 600);
            };
        }
    }

    function initMedicalDashboard() {
        const searchBtn = document.querySelector('.search-btn');
        const searchInput = document.getElementById('patientId');
        const message = document.getElementById('message');
        const patientInfo = document.getElementById('patientInfo');
        const medicalInfo = document.getElementById('medicalInfo');

        if (!searchBtn && !searchInput) return;

        // Override or attach search handler
        window.searchPatient = function () {
            const patientId = searchInput ? searchInput.value.trim().toUpperCase() : '';
            if (!patientId) {
                if (message) message.innerText = 'Please enter Patient ID.';
                return;
            }

            const patient = PatientCareDB.getPatientById(patientId);
            if (!patient) {
                if (message) message.innerText = `✕ No patient found with ID: ${patientId}. Try: PC-2026-0001`;
                if (patientInfo) patientInfo.innerHTML = '';
                if (medicalInfo) medicalInfo.innerHTML = '';
                return;
            }

            if (message) message.innerText = `✓ Patient Found: ${patient.fullName}`;

            const bills = PatientCareDB.getMedicalBills(patient.patientId);

            if (patientInfo) {
                patientInfo.innerHTML = `
                    <div class="info-card" style="margin-bottom: 20px;">
                        <h2>Patient Information</h2>
                        <p><strong>Patient Name:</strong> ${patient.fullName}</p>
                        <p><strong>Patient ID:</strong> ${patient.patientId}</p>
                        <p><strong>HAC Number:</strong> ${patient.hacNumber}</p>
                        <p><strong>Active Benefit Balance:</strong> ₹${patient.totalBenefitAmount}</p>
                    </div>
                `;
            }

            let html = `
                <div class="info-card">
                    <h2>💊 Medicine Purchase History (${bills.length} Orders)</h2>
            `;

            if (bills.length === 0) {
                html += '<p style="color: var(--slate-500); padding: 15px 0;">No past purchase records for this patient.</p>';
            } else {
                bills.forEach((bill, idx) => {
                    html += `
                        <div class="medical-record">
                            <h3>Record #${idx + 1} - ${bill.medicineName}</h3>
                            <p><strong>Chemist:</strong> ${bill.medicalName || 'City Care Pharmacy'}</p>
                            <p><strong>Date:</strong> ${bill.purchaseDate}</p>
                            <p><strong>Quantity:</strong> ${bill.quantity}</p>
                            <p><strong>Total Amount:</strong> ₹${bill.medicineAmount}</p>
                            <p><strong>Benefit Credited:</strong> ₹${bill.patientBenefitContribution || 0}</p>
                        </div>
                    `;
                });
            }

            html += `
                <div style="margin-top: 25px; border-top: 1px solid var(--slate-200); padding-top: 20px;">
                    <h3>➕ Dispense New Medicine Order</h3>
                    <form id="pharmacyDispenseForm" style="margin-top: 15px;">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Medicine Name & Strength</label>
                                <input type="text" id="dispenseMedicine" placeholder="e.g. Amoxicillin 500mg, Pan-D" required>
                            </div>
                            <div class="form-group">
                                <label>Quantity</label>
                                <input type="number" id="dispenseQty" value="1" min="1" required>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Unit Price (₹)</label>
                                <input type="number" id="dispensePrice" value="150" min="0" required>
                            </div>
                            <div class="form-group">
                                <label>GST Applicable</label>
                                <select id="dispenseGst">
                                    <option value="0.05">5% GST</option>
                                    <option value="0.12" selected>12% GST</option>
                                    <option value="0.18">18% GST</option>
                                </select>
                            </div>
                        </div>
                        <button type="submit" class="primary-btn">
                            Complete Dispense & Save Bill Receipt
                        </button>
                    </form>
                </div>
            </div>`;

            if (medicalInfo) {
                medicalInfo.innerHTML = html;

                document.getElementById('pharmacyDispenseForm')?.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const qty = Number(document.getElementById('dispenseQty').value) || 1;
                    const price = Number(document.getElementById('dispensePrice').value) || 0;
                    const gstRate = Number(document.getElementById('dispenseGst').value) || 0.12;

                    const subtotal = qty * price;
                    const gstAmount = Math.round(subtotal * gstRate);
                    const total = subtotal + gstAmount;

                    const bill = {
                        patientId: patient.patientId,
                        medicalName: 'City Care Pharmacy',
                        medicineName: document.getElementById('dispenseMedicine').value,
                        purchaseDate: new Date().toISOString().split('T')[0],
                        quantity: qty,
                        medicineAmount: total,
                        gst: gstAmount
                    };

                    PatientCareDB.addMedicalBill(bill);
                    showToast(`Medicine dispensed! Bill: ₹${total} (Saved)`, 'success', 'Order Complete');
                    window.searchPatient();
                });
            }
        };

        if (searchBtn) {
            searchBtn.onclick = window.searchPatient;
        }
    }

    // ----------------------------------------------------------------------
    // 12. GOVERNMENT SCHEMES & DYNAMIC ELIGIBILITY CHECKER
    // ----------------------------------------------------------------------
    function initGovernmentSchemes() {
        const schemesContainer = document.getElementById('schemesContainer');
        if (schemesContainer) {
            const schemes = PatientCareDB.getSchemes();
            schemesContainer.innerHTML = '';

            let grid = document.createElement('div');
            grid.className = 'schemes-card-grid';

            schemes.forEach(scheme => {
                const card = document.createElement('div');
                card.className = 'scheme-card';
                card.innerHTML = `
                    <div class="scheme-badge">${scheme.schemeStatus}</div>
                    <h3>${scheme.schemeName}</h3>
                    <div class="scheme-dept">🏛 ${scheme.departmentName}</div>
                    <p>${scheme.schemeDescription}</p>
                    <div style="background: var(--slate-50); padding: 12px; border-radius: var(--radius-sm); margin-bottom: 15px; font-size: 13px;">
                        <strong>Eligibility:</strong> ${scheme.eligibilityCriteria}
                        <br><br>
                        <strong>Coverage Benefit:</strong> ${scheme.benefits}
                    </div>
                    <a href="${scheme.officialWebsite}" target="_blank" rel="noopener noreferrer" class="primary-btn" style="margin-top: auto; font-size: 13px;">
                        Visit Official Scheme Portal ↗
                    </a>
                `;
                grid.appendChild(card);
            });

            schemesContainer.appendChild(grid);
        }

        // Scheme Eligibility Calculator Tool
        const eligibilityContainer = document.getElementById('eligibilityContainer');
        if (eligibilityContainer) {
            eligibilityContainer.innerHTML = `
                <div style="width: 100%;">
                    <p style="color: var(--slate-600); margin-bottom: 20px;">
                        Check your personalized government health scheme coverage in 1 click:
                    </p>
                    <form id="eligibilityCalculatorForm" style="background: var(--slate-50); padding: 24px; border-radius: var(--radius-md); border: 1px solid var(--slate-200); margin-bottom: 25px;">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Your Age (Years)</label>
                                <input type="number" id="calcAge" value="28" min="0" max="120" required>
                            </div>
                            <div class="form-group">
                                <label>Annual Family Income (₹)</label>
                                <input type="number" id="calcIncome" value="240000" min="0" required>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Socio-Economic Category</label>
                                <select id="calcCategory">
                                    <option value="BPL">BPL / Low Income Card Holder</option>
                                    <option value="SECC">SECC Listed Household</option>
                                    <option value="RURAL">Rural Resident</option>
                                    <option value="GENERAL" selected>General / Middle Income</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Bank Account Linked</label>
                                <select id="calcBank">
                                    <option value="yes" selected>Yes (Active Savings Account)</option>
                                    <option value="no">No</option>
                                </select>
                            </div>
                        </div>
                        <button type="submit" class="primary-btn">
                            Check Eligible Government Schemes
                        </button>
                    </form>
                    <div id="eligibilityResults"></div>
                </div>
            `;

            document.getElementById('eligibilityCalculatorForm')?.addEventListener('submit', (e) => {
                e.preventDefault();
                const age = Number(document.getElementById('calcAge').value) || 0;
                const income = Number(document.getElementById('calcIncome').value) || 0;
                const category = document.getElementById('calcCategory').value;

                let qualified = [];

                if (income <= 300000 || category === 'BPL' || category === 'SECC') {
                    qualified.push({
                        name: 'Ayushman Bharat (PM-JAY)',
                        benefit: '₹5,00,000 Cashless Hospitalization Cover per family/year',
                        status: '100% Eligible',
                        reason: 'Meets income and priority household criteria'
                    });
                }

                if (age >= 18 && age <= 70) {
                    qualified.push({
                        name: 'Pradhan Mantri Suraksha Bima Yojana (PMSBY)',
                        benefit: '₹2,00,000 Accidental Cover for ₹20/year',
                        status: '100% Eligible',
                        reason: 'Meets age 18-70 bank account requirement'
                    });
                }

                if (age >= 60) {
                    qualified.push({
                        name: 'Senior Citizen Medical Subsidy',
                        benefit: 'Specialized Geriatric Care + 25% Medicine Subsidy',
                        status: '100% Eligible',
                        reason: 'Senior citizen age (60+) verified'
                    });
                }

                qualified.push({
                    name: 'Jan Aushadhi Generic Medicine Scheme',
                    benefit: '50% to 90% discount on high quality generic medicines',
                    status: 'Universally Eligible',
                    reason: 'Open to all Indian citizens with doctor prescription'
                });

                const resDiv = document.getElementById('eligibilityResults');
                if (resDiv) {
                    let resHtml = `
                        <div class="profile-card" style="border: 2px solid var(--primary); background: #f0f9ff;">
                            <h3 style="color: var(--primary-dark); margin-bottom: 15px;">
                                🎯 You are eligible for ${qualified.length} Government Healthcare Schemes:
                            </h3>
                            <div class="profile-grid">
                    `;

                    qualified.forEach(q => {
                        resHtml += `
                            <div class="profile-item" style="background: white;">
                                <span style="color: var(--success); font-weight: 800;">${q.status}</span>
                                <strong style="font-size: 17px;">${q.name}</strong>
                                <p style="font-size: 13px; color: var(--slate-600); margin-top: 4px;">${q.benefit}</p>
                            </div>
                        `;
                    });

                    resHtml += `</div></div>`;
                    resDiv.innerHTML = resHtml;
                    resDiv.scrollIntoView({ behavior: 'smooth' });
                }

                showToast(`Evaluated: ${qualified.length} Schemes Eligible!`, 'success', 'Eligibility Result');
            });
        }
    }

    // ----------------------------------------------------------------------
    // 13. SMART PAYMENTS & DIGITAL RECEIPT (smart-payment & payment-receipt)
    // ----------------------------------------------------------------------
    function initSmartPayment() {
        const paymentGrid = document.querySelector('.profile-grid');
        const card = document.querySelector('.profile-card');

        // Check if on smart-payment.html
        if (window.location.pathname.includes('smart-payment.html') && card) {
            const formSection = document.createElement('div');
            formSection.style.marginTop = '30px';
            formSection.innerHTML = `
                <div class="profile-title">
                    <h2>💳 Process Smart Healthcare Payment</h2>
                </div>
                <form id="smartPaymentForm" style="background: var(--slate-50); padding: 24px; border-radius: var(--radius-md); border: 1px solid var(--slate-200);">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Patient ID</label>
                            <input type="text" id="payPatientId" value="PC-2026-0001" required>
                        </div>
                        <div class="form-group">
                            <label>Service Type</label>
                            <select id="payServiceType">
                                <option value="Doctor Consultation">Doctor Consultation</option>
                                <option value="Pathology Lab Test">Pathology Lab Test</option>
                                <option value="Pharmacy Medicines">Pharmacy Medicines</option>
                                <option value="Hospitalization">Hospitalization Care</option>
                            </select>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Bill Amount (₹)</label>
                            <input type="number" id="payAmount" value="800" min="1" required>
                        </div>
                        <div class="form-group">
                            <label>Payment Method</label>
                            <select id="payMethod">
                                <option value="UPI / QR Code">UPI (GPay / PhonePe / Paytm)</option>
                                <option value="Debit / Credit Card">Debit / Credit Card</option>
                                <option value="Net Banking">Net Banking</option>
                                <option value="Health Assurance Benefit Account">Health Assurance Benefit Wallet</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="primary-btn">
                        Pay Securely & Generate Digital Receipt
                    </button>
                </form>
                <div id="receiptResult"></div>
            `;

            card.appendChild(formSection);

            document.getElementById('smartPaymentForm')?.addEventListener('submit', (e) => {
                e.preventDefault();
                const patientId = document.getElementById('payPatientId').value.trim();
                const service = document.getElementById('payServiceType').value;
                const amount = Number(document.getElementById('payAmount').value) || 0;
                const method = document.getElementById('payMethod').value;

                const payment = PatientCareDB.addPayment({
                    patientId,
                    serviceType: service,
                    amount,
                    paymentMethod: method
                });

                showToast(`Payment of ₹${amount} successful! Txn: ${payment.transactionId}`, 'success', 'Payment Successful');

                const resDiv = document.getElementById('receiptResult');
                if (resDiv) {
                    resDiv.innerHTML = `
                        <div class="profile-card" style="margin-top: 25px; border: 2px dashed var(--primary); background: #f8fafc;">
                            <div class="profile-title" style="display: flex; justify-content: space-between;">
                                <h2>🧾 Digital Healthcare Payment Receipt</h2>
                                <span class="status" style="font-size: 14px;">● VERIFIED</span>
                            </div>
                            <div class="profile-grid">
                                <div class="profile-item"><span>Transaction ID</span><strong>${payment.transactionId}</strong></div>
                                <div class="profile-item"><span>Patient ID</span><strong>${payment.patientId}</strong></div>
                                <div class="profile-item"><span>Service Paid</span><strong>${payment.serviceType}</strong></div>
                                <div class="profile-item"><span>Amount Paid</span><strong style="color: var(--primary); font-size: 18px;">₹${payment.amount}</strong></div>
                                <div class="profile-item"><span>Payment Mode</span><strong>${payment.paymentMethod}</strong></div>
                                <div class="profile-item"><span>Date & Timestamp</span><strong>${payment.timestamp}</strong></div>
                            </div>
                            <div style="margin-top: 20px; display: flex; gap: 12px;">
                                <button type="button" class="secondary-btn" onclick="window.print()">🖨 Print Official Receipt</button>
                            </div>
                        </div>
                    `;
                    resDiv.scrollIntoView({ behavior: 'smooth' });
                }
            });
        }
    }

    // ----------------------------------------------------------------------
    // 14. REVIEWS & COMMUNITY FEEDBACK (contact.html & homepage)
    // ----------------------------------------------------------------------
    function initReviews() {
        const stars = document.querySelectorAll('.stars span');
        const submitBtn = document.querySelector('.review-submit-btn');
        const reviewText = document.getElementById('reviewMessage');
        let currentRating = 5;

        // Interactive star rating
        stars.forEach((star, idx) => {
            star.addEventListener('click', () => {
                currentRating = idx + 1;
                stars.forEach((s, i) => {
                    s.classList.toggle('active', i < currentRating);
                });
            });
        });

        // Initialize 5 stars by default
        stars.forEach(s => s.classList.add('active'));

        if (submitBtn) {
            submitBtn.addEventListener('click', () => {
                const comment = reviewText?.value.trim();
                if (!comment) {
                    showToast('Please share your thoughts in the review box.', 'warning', 'Review Empty');
                    return;
                }

                const session = PatientCareDB.getSession();
                const author = session && session.user ? session.user.fullName : 'Verified Patient';

                PatientCareDB.addReview({
                    author,
                    rating: currentRating,
                    role: 'Patient',
                    comment
                });

                showToast('Thank you! Your hospital feedback has been recorded.', 'success', 'Feedback Submitted');
                if (reviewText) reviewText.value = '';
                renderReviews();
            });
        }

        // Render reviews list
        function renderReviews() {
            const reviewSec = document.querySelector('.review-section');
            if (!reviewSec) return;

            let listContainer = document.getElementById('communityReviewsList');
            if (!listContainer) {
                listContainer = document.createElement('div');
                listContainer.id = 'communityReviewsList';
                listContainer.className = 'reviews-list';
                reviewSec.appendChild(listContainer);
            }

            const reviews = PatientCareDB.getReviews();
            listContainer.innerHTML = '';

            reviews.forEach(r => {
                const starStr = '★'.repeat(r.rating) + '☆'.repeat(5 - r.rating);
                const item = document.createElement('div');
                item.className = 'review-item';
                item.innerHTML = `
                    <div class="review-item-header">
                        <span class="review-author">${r.author} <small style="color: var(--slate-400);">(${r.role})</small></span>
                        <span class="review-stars">${starStr}</span>
                    </div>
                    <p class="review-text">"${r.comment}"</p>
                    <small style="color: var(--slate-400); display: block; margin-top: 8px;">Date: ${r.date}</small>
                `;
                listContainer.appendChild(item);
            });
        }

        renderReviews();
    }

    // ----------------------------------------------------------------------
    // 15. CONTACT FORM
    // ----------------------------------------------------------------------
    function initContactForm() {
        const contactForm = document.querySelector('#contactForm');
        const contactSuccess = document.querySelector('#contactSuccess');

        if (!contactForm) return;

        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (contactSuccess) {
                contactSuccess.innerText = '✓ Thank you! Your support message has been sent. Our team will contact you within 24 hours.';
                contactSuccess.style.display = 'block';
            }
            showToast('Message sent! Our support team will get in touch.', 'success', 'Query Submitted');
            contactForm.reset();
        });
    }

    // ----------------------------------------------------------------------
    // 16. GLOBAL DISPATCHER ON DOM LOAD
    // ----------------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', function () {
        // 1. Initialize local state engine
        PatientCareDB.init();

        // 2. Initialize responsive navbar & mobile menu
        initNavbar();

        // 3. Dispatch page-specific logic based on path and elements
        initHomePage();
        initRegisterPage();
        initPatientLoginPage();
        initPatientDashboard();
        initPatientProfile();
        initDoctorLoginPage();
        initDoctorDashboard();
        initPathologyLoginPage();
        initPathologyDashboard();
        initMedicalLoginPage();
        initMedicalDashboard();
        initGovernmentSchemes();
        initSmartPayment();
        initReviews();
        initContactForm();
    });

    // Expose PatientCare API globally for console or debugging
    window.PatientCareDB = PatientCareDB;
    window.showToast = showToast;

})();