/**
 * Health Insurance Assurance Healthcare Platform
 * Patient Registration & Dashboard Controller (patient.js)
 */

// ---------------------------------------------------------
// Helper: Show Inline Form Alert
// ---------------------------------------------------------
function showPatientRegAlert(message, type = 'danger') {
    const alertBox = document.getElementById('patientRegAlert');
    if (alertBox) {
        alertBox.className = `alert alert-${type} d-block my-3 shadow-sm`;
        const icon = type === 'success' ? 'bi-check-circle-fill' : type === 'warning' ? 'bi-exclamation-triangle-fill' : 'bi-x-circle-fill';
        alertBox.innerHTML = `<i class="bi ${icon} me-2"></i> ${message}`;
        alertBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function clearPatientRegAlert() {
    const alertBox = document.getElementById('patientRegAlert');
    if (alertBox) {
        alertBox.className = 'alert d-none my-3';
        alertBox.innerHTML = '';
    }
}

// ---------------------------------------------------------
// Helper: Generate Valid Test PAN
// ---------------------------------------------------------
window.generateDemoPan = function() {
    const letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    let pan = '';
    for (let i = 0; i < 5; i++) pan += letters.charAt(Math.floor(Math.random() * letters.length));
    for (let i = 0; i < 4; i++) pan += Math.floor(Math.random() * 10);
    pan += letters.charAt(Math.floor(Math.random() * letters.length));

    const panInput = document.getElementById('pPan');
    if (panInput) {
        panInput.value = pan;
        panInput.dispatchEvent(new Event('input'));
    }
    const helper = document.getElementById('panHelperText');
    if (helper) {
        helper.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill"></i> Generated valid test PAN: <strong>${pan}</strong></span>`;
    }
    return pan;
};

// ---------------------------------------------------------
// Helper: Quick-Fill Demo Patient
// ---------------------------------------------------------
window.quickFillDemoPatient = function() {
    clearPatientRegAlert();
    const demoPan = window.generateDemoPan();
    const randNum = Math.floor(Math.random() * 900) + 100;

    const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.value = val;
    };

    setVal('pFullName', 'Siddharth R. Deshmukh');
    setVal('pDob', '1990-08-20');
    setVal('pGender', 'Male');
    setVal('pMobile', '9822114455');
    setVal('pEmail', `siddharth.${randNum}@example.com`);
    setVal('pAddress', 'Flat 502, Orchid Towers, FC Road, Shivaji Nagar');
    setVal('pCity', 'Pune');
    setVal('pDistrict', 'Pune');
    setVal('pState', 'Maharashtra');
    setVal('pPincode', '411005');
    setVal('pPan', demoPan);
    setVal('pAadhaar', '987654321098');
    setVal('pBlood', 'B+');
    setVal('pConditions', 'None');
    setVal('pAllergies', 'None');
    setVal('pEmergName', 'Sunita Deshmukh');
    setVal('pEmergPhone', '9822114456');

    // Clinical Phase 2 fields
    setVal('pIllness', 'Persistent migraine headache with mild dizziness');
    setVal('pSymptoms', 'Throbbing frontal headache, light sensitivity for 3 days');
    setVal('pSymptomDuration', '3 days');
    setVal('pSeverity', 'Moderate');
    setVal('pCurrentMedicines', 'Paracetamol 650mg SOS');

    const consent = document.getElementById('pConsent');
    if (consent) consent.checked = true;

    setVal('pUsername', `siddharth_${randNum}`);
    setVal('pPassword', 'Password@123');
    setVal('pConfirmPassword', 'Password@123');

    showPatientRegAlert('Demo patient data loaded successfully! Review the information and click "Complete Patient Registration" below.', 'info');
    if (window.API && window.API.UI) {
        window.API.UI.showToast('Demo data auto-filled.', 'info', 'Quick Fill');
    }
};

// ---------------------------------------------------------
// Helper: Show Result Modal (with Bootstrap & DOM fallback)
// ---------------------------------------------------------
function showRegistrationResultModal(modalEl) {
    if (!modalEl) return;
    if (window.bootstrap && window.bootstrap.Modal) {
        try {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
            return;
        } catch (e) {
            console.warn('Bootstrap modal constructor failed, falling back to DOM display:', e);
        }
    }
    // Fallback: Pure DOM modal display
    modalEl.classList.add('show');
    modalEl.style.display = 'block';
    modalEl.removeAttribute('aria-hidden');
    modalEl.setAttribute('aria-modal', 'true');
    document.body.classList.add('modal-open');
    let backdrop = document.getElementById('modalBackdropFallback');
    if (!backdrop) {
        backdrop = document.createElement('div');
        backdrop.id = 'modalBackdropFallback';
        backdrop.className = 'modal-backdrop fade show';
        document.body.appendChild(backdrop);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // ---------------------------------------------------------
    // 1. PATIENT REGISTRATION FORM & PAN LOGIC
    // ---------------------------------------------------------
    const panInput = document.getElementById('pPan');
    const panHelper = document.getElementById('panHelperText');

    if (panInput && panHelper) {
        panInput.addEventListener('input', () => {
            panInput.value = panInput.value.toUpperCase();
            const val = panInput.value.trim();
            const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
            if (val.length === 10) {
                if (panRegex.test(val)) {
                    panHelper.innerHTML = '<span class="text-success fw-bold"><i class="bi bi-check-circle-fill"></i> Valid PAN Card format</span>';
                } else {
                    panHelper.innerHTML = '<span class="text-danger fw-bold"><i class="bi bi-x-circle-fill"></i> Invalid format. Must be 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)</span>';
                }
            } else {
                panHelper.innerHTML = `<span>${val.length}/10 chars — Must be 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F).</span>`;
            }
        });
    }

    const patientRegForm = document.getElementById('patientRegistrationForm');
    if (patientRegForm) {
        patientRegForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearPatientRegAlert();
            const submitBtn = patientRegForm.querySelector('button[type="submit"]') || document.getElementById('submitPatientBtn');

            // Pre-flight check: API object availability
            if (typeof API === 'undefined' || !API.patientAPI) {
                showPatientRegAlert('System API layer is still initializing. Please refresh the page and try again.', 'danger');
                return;
            }

            const pan = document.getElementById('pPan').value.trim().toUpperCase();
            const panRegex = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
            if (!panRegex.test(pan)) {
                const msg = 'Invalid PAN Card format. Must be exactly 5 uppercase letters, 4 digits, and 1 uppercase letter (e.g. ABCDE1234F). Click "Generate Test PAN" above if you need a valid test PAN.';
                showPatientRegAlert(msg, 'danger');
                API.UI.showToast(msg, 'danger', 'Validation Error');
                document.getElementById('pPan').focus();
                return;
            }

            let mobile = document.getElementById('pMobile').value.trim().replace(/\D/g, '');
            if (mobile.length > 10) mobile = mobile.slice(-10);
            if (mobile.length !== 10) {
                const msg = 'Mobile number must contain 10 numeric digits.';
                showPatientRegAlert(msg, 'danger');
                API.UI.showToast(msg, 'danger', 'Validation Error');
                document.getElementById('pMobile').focus();
                return;
            }

            const password = document.getElementById('pPassword').value;
            const confirmPassword = document.getElementById('pConfirmPassword').value;
            if (password !== confirmPassword) {
                const msg = 'Password and Confirm Password do not match. Please verify both fields.';
                showPatientRegAlert(msg, 'danger');
                API.UI.showToast(msg, 'danger', 'Validation Error');
                document.getElementById('pConfirmPassword').focus();
                return;
            }

            // Phase 2: Consent validation
            const consent = document.getElementById('pConsent');
            if (consent && !consent.checked) {
                const msg = 'You must check the consent box for medical data processing to complete registration.';
                showPatientRegAlert(msg, 'danger');
                API.UI.showToast(msg, 'danger', 'Consent Required');
                consent.focus();
                return;
            }

            let emergPhone = document.getElementById('pEmergPhone')?.value?.trim()?.replace(/\D/g, '') || '';
            if (emergPhone.length > 10) emergPhone = emergPhone.slice(-10);

            const payload = {
                full_name: document.getElementById('pFullName').value.trim(),
                dob: document.getElementById('pDob').value,
                gender: document.getElementById('pGender').value,
                mobile: mobile,
                email: document.getElementById('pEmail').value.trim(),
                address: document.getElementById('pAddress').value.trim(),
                city: document.getElementById('pCity').value.trim(),
                district: document.getElementById('pDistrict').value.trim(),
                state: document.getElementById('pState').value.trim(),
                pincode: document.getElementById('pPincode').value.trim(),
                pan_number: pan,
                aadhaar_number: document.getElementById('pAadhaar')?.value?.trim() || '',
                blood_group: document.getElementById('pBlood').value,
                existing_conditions: document.getElementById('pConditions')?.value || '',
                allergies: document.getElementById('pAllergies')?.value || '',
                emergency_contact_name: document.getElementById('pEmergName').value.trim(),
                emergency_contact_phone: emergPhone || mobile,
                // Phase 2: Medical history fields
                illness_description: document.getElementById('pIllness')?.value?.trim() || '',
                presenting_symptoms: document.getElementById('pSymptoms')?.value?.trim() || '',
                symptom_duration: document.getElementById('pSymptomDuration')?.value?.trim() || '',
                symptom_severity: document.getElementById('pSeverity')?.value || '',
                current_medicines: document.getElementById('pCurrentMedicines')?.value?.trim() || '',
                consent_data_processing: consent ? consent.checked : false,
                username: document.getElementById('pUsername').value.trim() || `user_${pan}`,
                password: password
            };

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Verifying PAN & Enrolling...';
            }

            try {
                const res = await API.patientAPI.create(payload);

                if (res.is_existing) {
                    // Existing Patient Record Found (Requirement 5)
                    showPatientRegAlert(res.message, 'warning');
                    API.UI.showToast(res.message, 'warning', 'Existing Record Found');
                    const modalEl = document.getElementById('patientResultModal');
                    if (modalEl) {
                        document.getElementById('modalTitle').innerHTML = '<i class="bi bi-info-circle-fill text-warning me-2"></i> Existing Record Retrieved';
                        document.getElementById('modalBody').innerHTML = `
                            <div class="alert alert-warning">
                                <strong>${res.message}</strong>
                            </div>
                            <div class="card p-3 bg-light">
                                <p class="mb-1"><strong>Patient ID:</strong> <span class="badge bg-primary fs-6">${res.patient.patient_id}</span></p>
                                <p class="mb-1"><strong>Patient Name:</strong> ${res.patient.full_name}</p>
                                <p class="mb-1"><strong>HAC Pass Number:</strong> ${res.patient.hac_number}</p>
                                <p class="mb-1"><strong>Masked PAN:</strong> <code>${res.patient.masked_pan || res.patient.pan_number}</code></p>
                            </div>
                        `;
                        document.getElementById('modalActionBtn').href = 'login.html';
                        document.getElementById('modalActionBtn').innerText = 'Proceed to Login →';
                        showRegistrationResultModal(modalEl);
                    }
                } else {
                    // Store active session for immediate dashboard access
                    API.Storage.setUser({
                        username: payload.username,
                        role: 'PATIENT',
                        profile: {
                            patient_id: res.patient.patient_id,
                            full_name: res.patient.full_name
                        }
                    });

                    // New Patient Successfully Created (Requirement 5)
                    showPatientRegAlert('Enrollment complete! Your Permanent Health ID has been created.', 'success');
                    API.UI.showToast(res.message, 'success', 'Enrollment Complete');
                    const modalEl = document.getElementById('patientResultModal');
                    if (modalEl) {
                        document.getElementById('modalTitle').innerHTML = '<i class="bi bi-check-circle-fill text-success me-2"></i> Permanent Health ID Created!';
                        let recDoctorsHtml = '';
                        if (window.lastRecommendedDoctors && window.lastRecommendedDoctors.length > 0) {
                            recDoctorsHtml = `
                                <div class="mt-3 p-3 bg-light rounded-3 text-start">
                                    <h6 class="fw-bold text-dark mb-2"><i class="bi bi-star-fill text-warning me-1"></i> Recommended Verified Doctors for You</h6>
                                    <div class="list-group list-group-flush">
                                        ${window.lastRecommendedDoctors.slice(0, 3).map(doc => `
                                            <div class="list-group-item bg-transparent px-0 py-2 d-flex justify-content-between align-items-center">
                                                <div>
                                                    <div class="fw-bold text-primary">${doc.full_name} <span class="badge bg-success-subtle text-success ms-1 small">Verified</span></div>
                                                    <small class="text-muted">${doc.specialization} &bull; ${doc.hospital_name || 'Clinic'}</small>
                                                    <div class="text-success small fw-semibold">Consultation Fee: ${API.UI.formatCurrency(doc.consultation_fee)}</div>
                                                </div>
                                                <a href="patient-dashboard.html?id=${res.patient.patient_id}&bookDoctorId=${doc.doctor_id}" class="btn btn-sm btn-primary rounded-pill">Book Appointment</a>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            `;
                        }

                        document.getElementById('modalBody').innerHTML = `
                            <div class="alert alert-success">
                                <strong>${res.message}</strong>
                            </div>
                            <div class="health-pass-card mb-3">
                                <div class="pass-chip"></div>
                                <div class="pass-id">${res.patient.patient_id}</div>
                                <div class="pass-hac">${res.patient.hac_number}</div>
                                <div class="pass-footer">
                                    <div>
                                        <small class="text-white-50">PATIENT NAME</small>
                                        <div class="fw-bold">${res.patient.full_name}</div>
                                    </div>
                                    <div class="text-end">
                                        <span class="pass-status-dot"></span> Active Beneficiary
                                    </div>
                                </div>
                            </div>
                            <p class="text-muted small">Your permanent Health ID is connected across all empanelled Doctors, Pathology Labs, Pharmacies, and Government healthcare schemes.</p>
                            ${recDoctorsHtml}
                        `;
                        document.getElementById('modalActionBtn').href = `patient-dashboard.html?id=${res.patient.patient_id}`;
                        document.getElementById('modalActionBtn').innerText = 'Go to Patient Dashboard →';
                        showRegistrationResultModal(modalEl);
                    }
                }
            } catch (err) {
                console.error('Registration failed:', err);
                const errMsg = err.message || 'Enrollment failed. Please check your network and inputs.';
                showPatientRegAlert(errMsg, 'danger');
                API.UI.showToast(errMsg, 'danger', 'Enrollment Error');
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="bi bi-shield-check me-1"></i> Complete Patient Registration';
                }
            }
        });
    }

    // ---------------------------------------------------------
    // 2. PATIENT DASHBOARD DATA LOADER
    // ---------------------------------------------------------
    const patientDashboardEl = document.getElementById('patientDashboardView');
    if (patientDashboardEl) {
        loadPatientDashboard();
    }
});

window.activeDashboardPatientId = null;

function getActivePatientId() {
    if (window.activeDashboardPatientId) return window.activeDashboardPatientId;
    const urlParams = new URLSearchParams(window.location.search);
    const idFromUrl = urlParams.get('id');
    if (idFromUrl) return idFromUrl;
    const currentUser = API.Storage.getUser();
    return currentUser?.profile?.patient_id || currentUser?.patient_profile?.patient_id || currentUser?.patient_id || localStorage.getItem('LAST_REGISTERED_PATIENT_ID') || null;
}

async function loadPatientDashboard() {
    let patientId = getActivePatientId();

    if (!patientId) {
        document.getElementById('patientDashboardView').innerHTML = `
            <div class="card p-5 text-center bg-white border shadow-sm my-4">
                <div class="display-6 text-primary mb-3"><i class="bi bi-person-bounding-box"></i></div>
                <h4 class="fw-bold">No Patient Selected</h4>
                <p class="text-muted">Please sign in to your patient account or enter a valid Patient ID to view dashboard.</p>
                <div class="d-flex justify-content-center gap-2 mt-3">
                    <a href="login.html" class="btn btn-primary"><i class="bi bi-box-arrow-in-right me-1"></i> Patient Sign In</a>
                    <a href="register.html" class="btn btn-outline-primary"><i class="bi bi-person-plus me-1"></i> Register New Patient</a>
                </div>
            </div>
        `;
        return;
    }

    try {
        const data = await API.patientAPI.getCentralizedRecord(patientId);
        window.activeDashboardPatientId = data.patient.patient_id;
        renderPatientDashboard(data);
    } catch (err) {
        console.error('Error loading patient dashboard:', err);
        document.getElementById('patientDashboardView').innerHTML = `
            <div class="alert alert-danger p-4 text-center my-4">
                <h4><i class="bi bi-exclamation-triangle-fill me-2"></i> Patient Record Not Found</h4>
                <p>${err.message || 'The specified Patient ID does not exist in the system.'}</p>
                <div class="d-flex justify-content-center gap-2 mt-3">
                    <a href="register.html" class="btn btn-primary">Register New Patient</a>
                    <a href="login.html" class="btn btn-outline-secondary">Back to Login</a>
                </div>
            </div>
        `;
    }
}

function renderPatientDashboard(data) {
    const p = data.patient;
    const s = data.summary;
    window.activeDashboardPatientId = p.patient_id;

    // Header & Pass
    document.getElementById('dashPatientName').innerText = p.full_name;
    document.getElementById('dashPatientId').innerText = p.patient_id;
    document.getElementById('dashHacNumber').innerText = p.hac_number;
    document.getElementById('dashMaskedPan').innerText = p.pan_number;
    document.getElementById('dashBloodGroup').innerText = p.blood_group;
    document.getElementById('dashEmergency').innerText = `${p.emergency_contact_name} (${p.emergency_contact_phone})`;

    // Stat Cards
    document.getElementById('statTotalCost').innerText = API.UI.formatCurrency(s.total_treatment_cost);
    document.getElementById('statApprovedFund').innerText = API.UI.formatCurrency(s.total_funds_approved);
    document.getElementById('statBenefitWallet').innerText = API.UI.formatCurrency(s.total_patient_benefits);
    document.getElementById('statVisitsCount').innerText = s.total_consultations;

    // Report Links
    const pdfBtn = document.getElementById('dashPdfReportBtn');
    const csvBtn = document.getElementById('dashCsvReportBtn');
    const webBtn = document.getElementById('dashWebReportBtn');
    if (pdfBtn) pdfBtn.href = API.reportAPI.getPDFUrl(p.patient_id);
    if (csvBtn) csvBtn.href = API.reportAPI.getCSVUrl(p.patient_id);
    if (webBtn) webBtn.href = `reports.html?id=${p.patient_id}`;

    // Timeline Rendering (Requirement 7 & 29)
    renderTimeline(data);

    // Connected Records Tables
    renderConsultationsTable(data.consultations);
    renderPathologyTable(data.pathology_reports);
    renderPharmacyTable(data.pharmacy_transactions);
    renderFundAllocationsTable(data.fund_allocations);
    renderInsuranceClaimsTable(data.insurance_claims);
    renderPaymentsTable(data.payments);

    // Load Appointments, Reserve Account, Health Protection Fund, and Scheme Applications
    loadPatientAppointments();
    loadReserveAccount();
    loadHealthProtectionAccount();
    loadPatientSchemeApplications();

    // Check if bookDoctorId was passed in URL (e.g. from registration recommendation)
    const urlParams = new URLSearchParams(window.location.search);
    const bookDoctorId = urlParams.get('bookDoctorId');
    if (bookDoctorId) {
        const bookTabBtn = document.querySelector('[data-bs-target="#tabBooking"]');
        if (bookTabBtn) {
            const tab = new bootstrap.Tab(bookTabBtn);
            tab.show();
            loadDoctorListForBooking();
        }
    }
}

function renderTimeline(data) {
    const timelineEl = document.getElementById('dashTimelineContainer');
    if (!timelineEl) return;

    const hasConsultation = data.consultations && data.consultations.length > 0;
    const hasPathology = data.pathology_reports && data.pathology_reports.length > 0;
    const hasPharmacy = data.pharmacy_transactions && data.pharmacy_transactions.length > 0;
    const hasFund = data.fund_allocations && data.fund_allocations.length > 0;
    const hasPayment = data.payments && data.payments.length > 0;

    timelineEl.innerHTML = `
        <div class="healthcare-timeline">
            <!-- 1. Registration -->
            <div class="timeline-step completed">
                <div class="timeline-icon-box"><i class="bi bi-person-check-fill"></i></div>
                <div class="timeline-content">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 text-primary fw-bold">1. Patient Registration & Permanent ID Generated</h6>
                        <span class="badge bg-success">Completed</span>
                    </div>
                    <p class="text-muted small mb-0 mt-1">Patient ID <strong>${data.patient.patient_id}</strong> linked with verified PAN.</p>
                </div>
            </div>

            <!-- 2. Doctor Consultation -->
            <div class="timeline-step ${hasConsultation ? 'completed' : ''}">
                <div class="timeline-icon-box"><i class="bi bi-stethoscope"></i></div>
                <div class="timeline-content">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 fw-bold">2. Clinical Consultation & Diagnosis</h6>
                        <span class="badge ${hasConsultation ? 'bg-success' : 'bg-secondary'}">${hasConsultation ? 'Recorded' : 'Pending'}</span>
                    </div>
                    <p class="text-muted small mb-0 mt-1">${hasConsultation ? `Dr. ${data.consultations[0].doctor_name}: ${data.consultations[0].diagnosis}` : 'Consultation awaiting completion.'}</p>
                </div>
            </div>

            <!-- 3. Pathology Diagnostics -->
            <div class="timeline-step ${hasPathology ? 'completed' : ''}">
                <div class="timeline-icon-box"><i class="bi bi-clipboard2-pulse"></i></div>
                <div class="timeline-content">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 fw-bold">3. Pathology & Investigation Reports</h6>
                        <span class="badge ${hasPathology ? 'bg-success' : 'bg-secondary'}">${hasPathology ? 'Verified' : 'Pending'}</span>
                    </div>
                    <p class="text-muted small mb-0 mt-1">${hasPathology ? `${data.pathology_reports[0].test_name} - ${data.pathology_reports[0].status}` : 'Diagnostic tests ordered or pending.'}</p>
                </div>
            </div>

            <!-- 4. Government Funding Approval -->
            <div class="timeline-step ${hasFund ? 'completed' : ''}">
                <div class="timeline-icon-box"><i class="bi bi-bank2"></i></div>
                <div class="timeline-content">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 fw-bold">4. Government Healthcare Fund Allocation</h6>
                        <span class="badge ${hasFund ? 'bg-success' : 'bg-secondary'}">${hasFund ? 'Approved' : 'Under Review'}</span>
                    </div>
                    <p class="text-muted small mb-0 mt-1">${hasFund ? `Total Approved: ${API.UI.formatCurrency(data.fund_allocations[0].total_approved_fund)} under ${data.fund_allocations[0].scheme_name}` : 'Scheme eligibility evaluation pending.'}</p>
                </div>
            </div>

            <!-- 5. Pharmacy Dispensary -->
            <div class="timeline-step ${hasPharmacy ? 'completed' : ''}">
                <div class="timeline-icon-box"><i class="bi bi-capsule"></i></div>
                <div class="timeline-content">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 fw-bold">5. Medical & Pharmacy Dispensation</h6>
                        <span class="badge ${hasPharmacy ? 'bg-success' : 'bg-secondary'}">${hasPharmacy ? 'Dispensed' : 'Pending'}</span>
                    </div>
                    <p class="text-muted small mb-0 mt-1">${hasPharmacy ? `Invoice: ${data.pharmacy_transactions[0].invoice_number} (${API.UI.formatCurrency(data.pharmacy_transactions[0].total_amount)})` : 'Medications pending dispensation.'}</p>
                </div>
            </div>

            <!-- 6. Fund Settlement & Patient Benefit -->
            <div class="timeline-step ${hasFund ? 'completed' : ''}">
                <div class="timeline-icon-box"><i class="bi bi-cash-coin"></i></div>
                <div class="timeline-content">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0 fw-bold">6. Fund Distribution Settlement & Patient Benefit</h6>
                        <span class="badge ${hasFund ? 'bg-success' : 'bg-secondary'}">${hasFund ? 'Settled' : 'Pending'}</span>
                    </div>
                    <p class="text-muted small mb-0 mt-1">${hasFund ? `Patient Benefit Savings: ${API.UI.formatCurrency(data.fund_allocations[0].patient_benefit_amount)} (70%)` : 'Benefit wallet distribution pending.'}</p>
                </div>
            </div>
        </div>
    `;
}

function renderConsultationsTable(consultations) {
    const tableBody = document.getElementById('consultationsTableBody');
    if (!tableBody) return;
    if (!consultations || consultations.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No consultations recorded yet.</td></tr>';
        return;
    }
    tableBody.innerHTML = consultations.map(c => `
        <tr>
            <td><strong>${c.consultation_id}</strong></td>
            <td>${c.visit_date}</td>
            <td>${c.doctor_name} <br><small class="text-muted">${c.hospital_name || ''}</small></td>
            <td><span class="badge bg-info text-dark">${c.diagnosis}</span></td>
            <td>${API.UI.formatCurrency(c.consultation_fee)}</td>
            <td><span class="badge bg-success">${c.status}</span></td>
        </tr>
    `).join('');
}

function renderPathologyTable(reports) {
    const tableBody = document.getElementById('pathologyTableBody');
    if (!tableBody) return;
    if (!reports || reports.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No lab reports found.</td></tr>';
        return;
    }
    tableBody.innerHTML = reports.map(r => `
        <tr>
            <td><strong>${r.report_id}</strong></td>
            <td>${r.test_date}</td>
            <td>${r.test_name}</td>
            <td>${r.lab_name}</td>
            <td>${API.UI.formatCurrency(r.test_cost)}</td>
            <td><span class="badge bg-success">${r.status}</span></td>
        </tr>
    `).join('');
}

function renderPharmacyTable(transactions) {
    const tableBody = document.getElementById('pharmacyTableBody');
    if (!tableBody) return;
    if (!transactions || transactions.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No pharmacy bills found.</td></tr>';
        return;
    }
    tableBody.innerHTML = transactions.map(t => `
        <tr>
            <td><strong>${t.invoice_number}</strong></td>
            <td>${t.dispensed_at?.split('T')[0] || '-'}</td>
            <td>${t.pharmacy_name}</td>
            <td>${t.medicines_dispensed?.substring(0, 45)}...</td>
            <td>${API.UI.formatCurrency(t.total_amount)}</td>
            <td><span class="badge bg-success">${t.payment_status}</span></td>
        </tr>
    `).join('');
}

function renderFundAllocationsTable(allocations) {
    const tableBody = document.getElementById('fundsTableBody');
    if (!tableBody) return;
    if (!allocations || allocations.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-3">No government fund allocations recorded.</td></tr>';
        return;
    }
    tableBody.innerHTML = allocations.map(a => `
        <tr>
            <td><strong>${a.allocation_id}</strong></td>
            <td>${a.scheme_name}</td>
            <td>${API.UI.formatCurrency(a.total_approved_fund)}</td>
            <td>${API.UI.formatCurrency(a.doctor_allocation)} (${a.applied_doctor_pct}%)</td>
            <td>${API.UI.formatCurrency(a.pathology_allocation)} (${a.applied_pathology_pct}%)</td>
            <td>${API.UI.formatCurrency(a.pharmacy_allocation)} (${a.applied_pharmacy_pct}%)</td>
            <td class="text-success fw-bold">${API.UI.formatCurrency(a.patient_benefit_amount)} (${a.applied_benefit_pct}%)</td>
            <td><span class="badge bg-success">${a.status}</span></td>
        </tr>
    `).join('');
}

function renderInsuranceClaimsTable(claims) {
    const tableBody = document.getElementById('insuranceTableBody');
    if (!tableBody) return;
    if (!claims || claims.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No insurance claims filed.</td></tr>';
        return;
    }
    tableBody.innerHTML = claims.map(c => `
        <tr>
            <td><strong>${c.claim_id}</strong></td>
            <td>${c.policy_number}</td>
            <td>${c.insurance_company}</td>
            <td>${API.UI.formatCurrency(c.requested_amount)}</td>
            <td>${API.UI.formatCurrency(c.approved_amount)}</td>
            <td><span class="badge ${c.status === 'Approved' ? 'bg-success' : 'bg-warning'}">${c.status}</span></td>
        </tr>
    `).join('');
}

function renderPaymentsTable(payments) {
    const tableBody = document.getElementById('paymentsTableBody');
    if (!tableBody) return;
    if (!payments || payments.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">No payments recorded.</td></tr>';
        return;
    }
    tableBody.innerHTML = payments.map(p => `
        <tr>
            <td><strong>${p.transaction_id}</strong></td>
            <td>${p.created_at?.split('T')[0] || '-'}</td>
            <td>${p.payment_type}</td>
            <td>${p.payment_method}</td>
            <td>${API.UI.formatCurrency(p.amount)}</td>
            <td><span class="badge bg-success">${p.status}</span></td>
        </tr>
    `).join('');
}

// ============================================================
// PHASE 3: AI Symptom Recommendation (register.html)
// ============================================================
// ============================================================
// PHASE 3 & FEATURE 1: AI Specialist & Doctor Recommendation (register.html)
// ============================================================
window.lastRecommendedDoctors = [];

async function requestAIRecommendation() {
    const healthConcern = document.getElementById('pIllness')?.value?.trim() || '';
    const symptoms = document.getElementById('pSymptoms')?.value?.trim() || '';
    const preferredSpecialty = document.getElementById('pPreferredSpecialty')?.value?.trim() || '';
    const consultationType = document.getElementById('pConsultationType')?.value?.trim() || 'In-person';
    const language = document.getElementById('pPreferredLanguage')?.value?.trim() || 'en';
    const location = document.getElementById('pPreferredLocation')?.value?.trim() || '';

    if (!healthConcern && !symptoms && !preferredSpecialty) {
        API.UI.showToast('Please enter your main health concern, symptoms, or select a preferred specialty.', 'warning');
        return;
    }

    const resultDiv = document.getElementById('aiRecommendResult');
    const btn = document.getElementById('aiRecommendBtn');
    if (!resultDiv) return;

    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Matching Verified Doctors...'; }
    resultDiv.innerHTML = '<div class="p-3 bg-light rounded text-center"><span class="spinner-border spinner-border-sm text-primary me-2"></span> Analyzing health concern and querying verified doctors...</div>';

    try {
        const res = await API.doctorRecommendationAPI.getRecommendations({
            health_concern: healthConcern,
            symptoms: symptoms,
            specialty: preferredSpecialty,
            consultation_type: consultationType,
            language: language,
            preferred_location: location
        });

        if (res.is_urgent) {
            resultDiv.innerHTML = `
                <div class="alert alert-danger shadow-sm border-0 rounded-3 p-3">
                    <div class="d-flex align-items-center gap-2 mb-2">
                        <i class="bi bi-exclamation-triangle-fill fs-4 text-danger"></i>
                        <h6 class="fw-bold mb-0 text-danger">URGENT MEDICAL ATTENTION RECOMMENDED</h6>
                    </div>
                    <p class="mb-2 fw-medium">${res.urgent_message}</p>
                    <div class="p-2 bg-white rounded text-danger small mb-2">
                        <strong>Emergency Helpline:</strong> Dial <strong>108 / 112</strong> or proceed to the nearest hospital emergency room.
                    </div>
                    <small class="text-muted fst-italic d-block">${res.disclaimer}</small>
                </div>
            `;
            return;
        }

        window.lastRecommendedDoctors = res.doctors || [];

        // Sync preferred specialty dropdown if empty
        const specSelect = document.getElementById('pPreferredSpecialty');
        if (specSelect && !specSelect.value && res.recommended_specialty) {
            for (let opt of specSelect.options) {
                if (opt.value.toLowerCase().includes(res.recommended_specialty.toLowerCase())) {
                    specSelect.value = opt.value;
                    break;
                }
            }
        }

        let doctorsHtml = '';
        if (res.doctors && res.doctors.length > 0) {
            doctorsHtml = `
                <div class="mt-3">
                    <h6 class="fw-bold text-dark mb-2"><i class="bi bi-person-check-fill text-success me-1"></i> Recommended Verified Doctors (${res.doctors.length} available)</h6>
                    <div class="row g-2">
                        ${res.doctors.map(doc => `
                        <div class="col-md-6">
                            <div class="card h-100 border shadow-sm p-3 doctor-rec-card bg-white rounded-3">
                                <div class="d-flex justify-content-between align-items-start mb-2">
                                    <div>
                                        <h6 class="fw-bold text-primary mb-0">${doc.full_name}</h6>
                                        <small class="text-muted">${doc.qualification} &bull; ${doc.experience_years} yrs exp</small>
                                    </div>
                                    <span class="badge bg-success-subtle text-success"><i class="bi bi-patch-check-fill me-1"></i>Verified</span>
                                </div>
                                <div class="badge bg-primary-subtle text-primary mb-2 align-self-start">${doc.specialization}</div>
                                <div class="small text-muted mb-2">
                                    <i class="bi bi-hospital me-1"></i>${doc.hospital_name || 'Empanelled Clinic'}
                                    ${doc.address ? `<br><i class="bi bi-geo-alt me-1"></i>${doc.address}` : ''}
                                </div>
                                <div class="p-2 bg-light rounded small mb-2">
                                    <i class="bi bi-info-circle text-primary me-1"></i>${doc.why_recommended}
                                </div>
                                <div class="d-flex justify-content-between align-items-center mt-auto pt-2 border-top">
                                    <div>
                                        <span class="fw-bold text-success">${API.UI.formatCurrency(doc.consultation_fee)}</span>
                                        <small class="text-muted d-block">Fee &bull; Next: ${doc.next_available || 'Available'}</small>
                                    </div>
                                    <span class="badge bg-primary rounded-pill px-2 py-1 small">Available upon registration</span>
                                </div>
                            </div>
                        </div>`).join('')}
                    </div>
                </div>
            `;
        } else {
            doctorsHtml = `
                <div class="alert alert-light border mt-2 small text-muted">
                    <i class="bi bi-info-circle me-1"></i> ${res.no_doctors_message || 'No direct specialist found with the exact filter. A General Physician will evaluate and refer you upon registration.'}
                </div>
            `;
        }

        resultDiv.innerHTML = `
            <div class="alert alert-success shadow-sm border-0 rounded-3 p-3 mb-2">
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <strong class="text-success"><i class="bi bi-robot me-1"></i> Recommended Specialty: ${res.recommended_specialty}</strong>
                    <span class="badge bg-success">${res.source === 'gemini_ai' ? 'AI Matched' : 'Clinical Rule Match'}</span>
                </div>
                <p class="small mb-1 text-dark">${res.reason}</p>
                <small class="text-muted fst-italic d-block mb-1">${res.disclaimer}</small>
            </div>
            ${doctorsHtml}
        `;
    } catch (err) {
        resultDiv.innerHTML = `
            <div class="alert alert-warning small p-2">
                <i class="bi bi-exclamation-circle me-1"></i> AI Doctor recommendation is currently in offline mode. You can proceed with registration and choose a specialist anytime in your dashboard.
            </div>
        `;
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-robot me-1"></i> Find Recommended Doctors Now';
        }
    }
}

// ============================================================
// PHASE 3 & 4: Appointment Booking (Patient Dashboard)
// ============================================================

async function loadDoctorListForBooking() {
    const container = document.getElementById('doctorListContainer');
    if (!container) return;

    container.innerHTML = '<div class="text-center py-3"><span class="spinner-border spinner-border-sm"></span> Loading doctors...</div>';

    const specialization = document.getElementById('specialtyFilter')?.value || '';
    try {
        const doctors = await API.doctorAPI.listDoctors(specialization);
        if (!doctors || doctors.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">No doctors found. Try a different specialty.</p>';
            return;
        }
        container.innerHTML = doctors.map(doc => `
            <div class="card mb-3 shadow-sm border-0">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
                        <div>
                            <h6 class="fw-bold mb-1"><i class="bi bi-person-badge me-1 text-primary"></i>${doc.full_name}</h6>
                            <span class="badge bg-primary-subtle text-primary">${doc.specialization}</span>
                            <span class="badge bg-light text-dark ms-1">${doc.qualification}</span>
                        </div>
                        <div class="text-end">
                            <div class="fw-bold text-success">${API.UI.formatCurrency(doc.default_fee)}</div>
                            <small class="text-muted">Consultation Fee</small>
                        </div>
                    </div>
                    <div class="mt-2 small text-muted">
                        <i class="bi bi-hospital me-1"></i>${doc.hospital_name} &nbsp;|&nbsp;
                        <i class="bi bi-award me-1"></i>${doc.experience_years} yrs experience
                    </div>
                    ${doc.availability.length > 0 ? `
                    <div class="mt-2">
                        <small class="text-muted fw-bold">Available:</small>
                        ${doc.availability.slice(0,3).map(a => `
                            <span class="badge bg-success-subtle text-success ms-1">${a.day_of_week} ${a.start_time}</span>
                        `).join('')}
                    </div>` : '<small class="text-warning mt-1 d-block"><i class="bi bi-clock me-1"></i>Schedule pending</small>'}
                    <div class="mt-3">
                        <button class="btn btn-primary btn-sm" onclick="showBookingForm('${doc.doctor_id}', '${doc.full_name}', '${doc.specialization}', ${doc.default_fee})">
                            <i class="bi bi-calendar-check me-1"></i> Book Appointment
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (err) {
        container.innerHTML = `<p class="text-danger small">Could not load doctors: ${err.message}</p>`;
    }
}

function showBookingForm(doctorId, doctorName, specialization, fee) {
    const modalEl = document.getElementById('bookingModal');
    if (!modalEl) {
        alert(`Booking for Dr. ${doctorName} (${specialization}). Fee: ₹${fee}`);
        return;
    }
    document.getElementById('bookDoctorId').value = doctorId;
    document.getElementById('bookDoctorName').textContent = doctorName;
    document.getElementById('bookSpecialization').textContent = specialization;
    document.getElementById('bookFee').textContent = API.UI.formatCurrency(fee);

    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('bookDate');
    if (dateInput) {
        dateInput.min = today;
        if (!dateInput.value) dateInput.value = today;
    }

    const symptomInput = document.getElementById('bookingSymptomInput');
    const bookSymptoms = document.getElementById('bookSymptoms');
    if (symptomInput && bookSymptoms && symptomInput.value.trim() && !bookSymptoms.value.trim()) {
        bookSymptoms.value = symptomInput.value.trim();
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

async function submitAppointmentBooking() {
    const patientId = getActivePatientId();
    if (!patientId) {
        API.UI.showToast('Please log in as a patient or select a patient to book appointments.', 'warning');
        return;
    }

    const doctorId = document.getElementById('bookDoctorId').value;
    const date = document.getElementById('bookDate').value;
    const symptoms = document.getElementById('bookSymptoms')?.value || '';
    const timeSlot = document.getElementById('bookTimeSlot')?.value || '10:00 AM';

    if (!date) {
        API.UI.showToast('Please select an appointment date.', 'warning');
        return;
    }

    const btn = document.getElementById('confirmBookingBtn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Booking...'; }

    try {
        const idempotencyKey = `appt-${patientId}-${doctorId}-${date}-${Date.now()}`;
        const res = await API.doctorAPI.bookAppointment({
            patient_id: patientId,
            doctor_id: doctorId,
            appointment_date: date,
            time_slot: timeSlot,
            symptoms: symptoms,
            idempotency_key: idempotencyKey
        });

        API.UI.showToast(res.message, 'success', 'Appointment Confirmed!');

        // Show token info
        const token = res.appointment?.token;
        if (token) {
            API.UI.showToast(`Your queue token is <strong>#${token.token_number}</strong>. Please wait for your turn.`, 'info', 'Token Assigned');
        }

        // Close modal & refresh appointments list
        const modalEl = document.getElementById('bookingModal');
        if (modalEl) bootstrap.Modal.getInstance(modalEl)?.hide();

        if (typeof loadPatientAppointments === 'function') {
            setTimeout(loadPatientAppointments, 500);
        }
    } catch (err) {
        API.UI.showToast(err.message || 'Booking failed. Please try again.', 'danger', 'Booking Error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-calendar-check me-1"></i> Confirm Booking'; }
    }
}

async function loadPatientAppointments(patientIdOverride) {
    const patientId = patientIdOverride || getActivePatientId();
    const container = document.getElementById('appointmentsContainer');
    if (!container) return;

    if (!patientId) {
        container.innerHTML = '<p class="text-muted text-center py-3">Please sign in or select a patient to view appointments.</p>';
        return;
    }

    try {
        const appointments = await API.doctorAPI.listAppointments({ patient_id: patientId });
        if (!appointments || appointments.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-3">No appointments yet. Book one below.</p>';
            return;
        }
        container.innerHTML = appointments.map(appt => {
            const token = appt.token;
            const statusClass = appt.status === 'Scheduled' ? 'success' :
                               appt.status === 'Completed' ? 'secondary' : 'danger';
            const tokenBadge = token ? `
                <span class="badge bg-primary ms-2">Token #${token.token_number}</span>
                <span class="badge bg-${token.status === 'Called' || token.status === 'In Consultation' ? 'warning' : 'light'} text-dark ms-1">
                    ${token.status === 'In Consultation' ? '🔔 Your Turn!' : token.status}
                </span>` : '';
            return `
                <div class="card mb-2 border-0 shadow-sm">
                    <div class="card-body py-2 px-3">
                        <div class="d-flex justify-content-between align-items-center flex-wrap gap-1">
                            <div>
                                <strong>${appt.doctor_name}</strong>
                                <span class="text-muted small ms-1">${appt.doctor_specialization}</span>
                                ${tokenBadge}
                            </div>
                            <div class="text-end">
                                <span class="badge bg-${statusClass}">${appt.status}</span>
                                <div class="small text-muted">${appt.appointment_date}</div>
                            </div>
                        </div>
                        ${appt.symptoms ? `<div class="small text-muted mt-1"><i class="bi bi-chat-text me-1"></i>${appt.symptoms}</div>` : ''}
                        <div class="mt-2 d-flex gap-2">
                            ${appt.status === 'Scheduled' ? `
                            <button class="btn btn-outline-danger btn-sm" onclick="cancelAppointment('${appt.appointment_id}')">
                                <i class="bi bi-x-circle me-1"></i> Cancel
                            </button>` : ''}
                        </div>
                    </div>
                </div>`;
        }).join('');
    } catch (err) {
        if (container) container.innerHTML = '<p class="text-danger small">Could not load appointments.</p>';
    }
}

async function cancelAppointment(appointmentId) {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    try {
        await API.doctorAPI.updateAppointment(appointmentId, { status: 'Cancelled' });
        API.UI.showToast('Appointment cancelled successfully.', 'success');
        loadPatientAppointments();
    } catch (err) {
        API.UI.showToast(err.message || 'Could not cancel appointment.', 'danger');
    }
}

// ============================================================
// PHASE 8: Healthcare Reserve Account Display
// ============================================================

async function loadReserveAccount(patientIdOverride) {
    const patientId = patientIdOverride || getActivePatientId();
    const container = document.getElementById('reserveAccountContainer');
    if (!container) return;

    if (!patientId) {
        container.innerHTML = '<p class="text-muted small">Reserve account not yet loaded. Please sign in or select a patient.</p>';
        return;
    }

    try {
        const account = await API.fundsAPI.getReserveAccount(patientId);
        container.innerHTML = `
            <div class="row g-3">
                <div class="col-12">
                    <div class="alert alert-warning py-2 small mb-2">
                        <i class="bi bi-info-circle me-1"></i>
                        <strong>Simulation Mode:</strong> ${account.simulation_notice}
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 bg-success-subtle">
                        <div class="card-body py-2">
                            <div class="fw-bold text-success fs-5">${API.UI.formatCurrency(account.available_balance)}</div>
                            <small class="text-muted">Available Balance</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 bg-primary-subtle">
                        <div class="card-body py-2">
                            <div class="fw-bold text-primary fs-5">${API.UI.formatCurrency(account.total_credited)}</div>
                            <small class="text-muted">Total Credited</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 bg-warning-subtle">
                        <div class="card-body py-2">
                            <div class="fw-bold text-warning fs-5">${account.reserve_percentage}%</div>
                            <small class="text-muted">Reserve Rate</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 bg-secondary-subtle">
                        <div class="card-body py-2">
                            <div class="fw-bold text-secondary fs-5">${API.UI.formatCurrency(account.utilized_balance)}</div>
                            <small class="text-muted">Utilized</small>
                        </div>
                    </div>
                </div>
                <div class="col-12">
                    <small class="text-muted">Account: <code>${account.account_number}</code></small>
                    <button class="btn btn-outline-secondary btn-sm ms-2" onclick="loadReserveLedger()">
                        <i class="bi bi-list-ul me-1"></i> View Transaction History
                    </button>
                </div>
            </div>`;
    } catch (err) {
        if (container) container.innerHTML = '<p class="text-muted small">Reserve account not yet activated. Make an eligible transaction to get started.</p>';
    }
}

async function loadReserveLedger(patientIdOverride) {
    const patientId = patientIdOverride || getActivePatientId();
    const container = document.getElementById('reserveLedgerContainer');
    if (!container) return;

    if (!patientId) {
        container.innerHTML = '<p class="text-muted text-center small py-2">Please select a patient to view transaction history.</p>';
        return;
    }

    try {
        const data = await API.fundsAPI.getReserveLedger(patientId);
        if (!data.entries || data.entries.length === 0) {
            container.innerHTML = '<p class="text-muted text-center small py-2">No transactions yet.</p>';
            return;
        }
        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-sm table-hover small">
                    <thead><tr>
                        <th>Date</th><th>Type</th><th>Service</th><th>Invoice</th><th>Rate</th><th>Credit</th><th>Balance After</th><th>Status</th>
                    </tr></thead>
                    <tbody>
                        ${data.entries.map(e => `
                            <tr>
                                <td>${e.created_at?.split('T')[0] || '-'}</td>
                                <td><span class="badge bg-${e.entry_type === 'CREDIT' ? 'success' : 'danger'}">${e.entry_type}</span></td>
                                <td>${e.service_type}</td>
                                <td>${API.UI.formatCurrency(e.original_invoice_amount)}</td>
                                <td>${e.reserve_percentage}%</td>
                                <td class="fw-bold text-success">${API.UI.formatCurrency(e.credit_amount)}</td>
                                <td>${API.UI.formatCurrency(e.balance_after)}</td>
                                <td><span class="badge bg-${e.status === 'COMPLETED' ? 'success' : 'warning'}">${e.status}</span>
                                    ${e.is_simulated ? '<i class="bi bi-info-circle text-muted ms-1" title="Simulation"></i>' : ''}</td>
                            </tr>`).join('')}
                    </tbody>
                </table>
            </div>`;
    } catch (err) {
        if (container) container.innerHTML = '<p class="text-danger small">Could not load ledger.</p>';
    }
}

// ============================================================
// PHASE 9: Health Protection Fund (10% Auto-Contribution)
// ============================================================

async function loadHealthProtectionAccount(patientIdOverride) {
    const patientId = patientIdOverride || getActivePatientId();
    const container = document.getElementById('hpfAccountContainer');
    if (!container) return;

    if (!patientId) {
        container.innerHTML = '<p class="text-muted small">Please sign in to view your Health Protection Fund.</p>';
        return;
    }

    container.innerHTML = '<p class="text-muted text-center py-3"><span class="spinner-border spinner-border-sm me-1"></span> Loading fund account...</p>';

    try {
        const account = await API.fundsAPI.getProtectionAccount(patientId);
        const byCategory = account.breakdown_by_category || {};

        container.innerHTML = `
            <div class="row g-3 mb-3">
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 bg-danger-subtle h-100">
                        <div class="card-body py-3">
                            <div class="fw-bold text-danger fs-4">${API.UI.formatCurrency(account.available_balance)}</div>
                            <small class="text-muted">Available Balance</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 bg-success-subtle h-100">
                        <div class="card-body py-3">
                            <div class="fw-bold text-success fs-4">${API.UI.formatCurrency(account.total_contributions)}</div>
                            <small class="text-muted">Total Contributed</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 bg-primary-subtle h-100">
                        <div class="card-body py-3">
                            <div class="fw-bold text-primary fs-4">${API.UI.formatCurrency(account.total_approved_withdrawals)}</div>
                            <small class="text-muted">Total Disbursed</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 col-6">
                    <div class="card text-center border-0 bg-warning-subtle h-100">
                        <div class="card-body py-3">
                            <div class="fw-bold text-warning fs-4">${(account.claims_summary?.pending_claims || 0)}</div>
                            <small class="text-muted">Pending Claims</small>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row g-3 mb-3">
                <div class="col-12">
                    <h6 class="fw-bold small text-uppercase text-muted mb-2"><i class="bi bi-bar-chart-fill me-1"></i> Contributions by Category</h6>
                    <div class="d-flex gap-3 flex-wrap">
                        ${Object.entries(byCategory).map(([cat, data]) => `
                        <div class="card border-0 bg-light px-3 py-2 text-center">
                            <div class="fw-bold text-success">${API.UI.formatCurrency(data.total_amount || 0)}</div>
                            <small class="text-muted">${cat}</small>
                            <small class="badge bg-secondary-subtle text-secondary">${data.count || 0} transactions</small>
                        </div>`).join('') || '<span class="text-muted small">No contributions yet. Eligible payments auto-credit 10%.</span>'}
                    </div>
                </div>
            </div>
            <div class="d-flex gap-2 mb-2">
                <button class="btn btn-outline-secondary btn-sm" onclick="loadHPFTransactions()">
                    <i class="bi bi-list-ul me-1"></i> View Transaction Ledger
                </button>
                <button class="btn btn-outline-primary btn-sm" onclick="loadHPFClaims()">
                    <i class="bi bi-file-earmark-medical me-1"></i> View My Claims
                </button>
            </div>`;
    } catch (err) {
        container.innerHTML = '<p class="text-muted small text-center py-3">Health Protection Fund account not yet activated. Make a doctor, pathology, or pharmacy payment to get started. (10% is automatically credited.)</p>';
    }
}

async function loadHPFTransactions(patientIdOverride) {
    const patientId = patientIdOverride || getActivePatientId();
    const container = document.getElementById('hpfTransactionsContainer');
    if (!container || !patientId) return;

    container.innerHTML = '<p class="text-muted small text-center"><span class="spinner-border spinner-border-sm me-1"></span> Loading transactions...</p>';

    try {
        const transactions = await API.fundsAPI.getProtectionTransactions(patientId);
        if (!transactions || transactions.length === 0) {
            container.innerHTML = '<p class="text-muted small text-center py-2">No fund transactions yet.</p>';
            return;
        }
        container.innerHTML = `
            <h6 class="fw-bold small text-uppercase text-muted mb-2"><i class="bi bi-clock-history me-1"></i> Fund Transaction Ledger</h6>
            <div class="table-responsive">
                <table class="table table-sm table-hover small">
                    <thead><tr>
                        <th>Date</th><th>Type</th><th>Category</th><th>Payment Amount</th><th>Rate</th><th>Fund Amount</th><th>Balance After</th><th>Status</th>
                    </tr></thead>
                    <tbody>
                        ${transactions.map(t => `
                        <tr>
                            <td>${t.created_at?.split('T')[0] || '-'}</td>
                            <td><span class="badge bg-${t.transaction_type === 'CONTRIBUTION' ? 'success' : t.transaction_type === 'WITHDRAWAL' ? 'primary' : 'danger'}-subtle text-${t.transaction_type === 'CONTRIBUTION' ? 'success' : t.transaction_type === 'WITHDRAWAL' ? 'primary' : 'danger'}">${t.transaction_type}</span></td>
                            <td>${t.service_category || '-'}</td>
                            <td>${API.UI.formatCurrency(t.eligible_payment_amount)}</td>
                            <td>${t.contribution_percentage}%</td>
                            <td class="fw-bold ${t.transaction_type === 'CONTRIBUTION' ? 'text-success' : 'text-danger'}">${t.transaction_type === 'CONTRIBUTION' ? '+' : '-'}${API.UI.formatCurrency(t.amount)}</td>
                            <td>${API.UI.formatCurrency(t.balance_after)}</td>
                            <td><span class="badge bg-${t.status === 'COMPLETED' ? 'success' : t.status === 'REVERSED' ? 'danger' : 'warning'}">${t.status}</span></td>
                        </tr>`).join('')}
                    </tbody>
                </table>
            </div>`;
    } catch (err) {
        container.innerHTML = '<p class="text-danger small">Could not load transactions.</p>';
    }
}

async function loadHPFClaims(patientIdOverride) {
    const patientId = patientIdOverride || getActivePatientId();
    const container = document.getElementById('hpfClaimsContainer');
    if (!container || !patientId) return;

    container.innerHTML = '<p class="text-muted small text-center"><span class="spinner-border spinner-border-sm me-1"></span> Loading claims...</p>';

    try {
        const claims = await API.fundsAPI.listProtectionClaims(patientId);
        if (!claims || claims.length === 0) {
            container.innerHTML = '<p class="text-muted small text-center py-2">No claims submitted yet. Use the "Submit Healthcare Claim" button above to apply.</p>';
            return;
        }
        const statusColors = { SUBMITTED: 'warning', UNDER_REVIEW: 'info', APPROVED: 'primary', PAID: 'success', REJECTED: 'danger', CANCELLED: 'secondary' };
        container.innerHTML = `
            <h6 class="fw-bold small text-uppercase text-muted mb-2"><i class="bi bi-file-earmark-medical me-1"></i> My Healthcare Claims</h6>
            <div class="table-responsive">
                <table class="table table-sm table-hover small">
                    <thead><tr>
                        <th>Claim Ref</th><th>Date</th><th>Category</th><th>Amount</th><th>Description</th><th>Status</th>
                    </tr></thead>
                    <tbody>
                        ${claims.map(c => `
                        <tr>
                            <td><code>${c.claim_reference}</code></td>
                            <td>${c.created_at?.split('T')[0] || '-'}</td>
                            <td>${c.expense_category}</td>
                            <td>${API.UI.formatCurrency(c.claimed_amount)}</td>
                            <td>${(c.description || '').substring(0, 50)}${c.description?.length > 50 ? '...' : ''}</td>
                            <td><span class="badge bg-${statusColors[c.status] || 'secondary'}">${c.status}</span>
                                ${c.status === 'PAID' ? `<div class="text-success small">${API.UI.formatCurrency(c.approved_amount)} paid</div>` : ''}
                            </td>
                        </tr>`).join('')}
                    </tbody>
                </table>
            </div>`;
    } catch (err) {
        container.innerHTML = '<p class="text-danger small">Could not load claims.</p>';
    }
}

async function submitHealthProtectionClaim() {
    const patientId = getActivePatientId();
    if (!patientId) {
        API.UI.showToast('Please sign in to submit a claim.', 'warning');
        return;
    }

    const category = document.getElementById('hpfClaimCategory')?.value;
    const amount = document.getElementById('hpfClaimAmount')?.value;
    const description = document.getElementById('hpfClaimDescription')?.value?.trim();
    const provider = document.getElementById('hpfClaimProvider')?.value?.trim();
    const serviceDate = document.getElementById('hpfClaimDate')?.value;

    if (!category || !amount || !description) {
        API.UI.showToast('Please fill in all required fields (category, amount, description).', 'warning');
        return;
    }
    if (parseFloat(amount) <= 0) {
        API.UI.showToast('Claim amount must be greater than 0.', 'warning');
        return;
    }

    const btn = document.getElementById('submitHpfClaimBtn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Submitting...'; }

    try {
        const res = await API.fundsAPI.submitProtectionClaim({
            patient_id: patientId,
            expense_category: category,
            claimed_amount: parseFloat(amount),
            description: description,
            provider_name: provider || '',
            service_date: serviceDate || new Date().toISOString().split('T')[0]
        });
        API.UI.showToast(`Claim submitted successfully! Reference: ${res.claim?.claim_reference || '—'}`, 'success', 'Claim Submitted');

        // Close modal and refresh claims
        const modal = bootstrap.Modal.getInstance(document.getElementById('hpfClaimModal'));
        if (modal) modal.hide();
        // Reset form
        ['hpfClaimAmount', 'hpfClaimDescription', 'hpfClaimProvider', 'hpfClaimDate'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = '';
        });
        loadHPFClaims();
        loadHealthProtectionAccount();
    } catch (err) {
        API.UI.showToast(err.message || 'Failed to submit claim. Please try again.', 'danger', 'Claim Error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-send me-1"></i> Submit Claim'; }
    }
}

async function getAIAndLoadDoctors() {
    const input = document.getElementById('bookingSymptomInput');
    const symptoms = input ? input.value.trim() : '';
    const resDiv = document.getElementById('aiSuggestionResult');
    if (!symptoms) {
        API.UI.showToast('Please describe your symptoms first.', 'warning');
        return;
    }
    if (resDiv) {
        resDiv.innerHTML = '<div class="alert alert-info py-2 small"><span class="spinner-border spinner-border-sm me-1"></span> AI evaluating symptoms and matching medical specialty...</div>';
    }

    try {
        const rec = await API.doctorAPI.getAIRecommendation(symptoms, 'en');
        if (rec.is_urgent) {
            resDiv.innerHTML = `
                <div class="alert alert-danger py-2">
                    <h6 class="fw-bold mb-1"><i class="bi bi-exclamation-octagon-fill me-1"></i> EMERGENCY ALERT</h6>
                    <p class="small mb-1">${rec.urgent_message}</p>
                    <small class="fst-italic text-white-50">${rec.disclaimer}</small>
                </div>
            `;
            return;
        }

        const specialty = rec.recommended_specialty || 'General Medicine';
        const filterInput = document.getElementById('specialtyFilter');
        if (filterInput) filterInput.value = specialty;

        resDiv.innerHTML = `
            <div class="alert alert-success py-3">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                    <div>
                        <h6 class="fw-bold mb-1 text-success">
                            <i class="bi bi-robot me-1"></i> AI Recommendation: <strong>${specialty}</strong>
                        </h6>
                        <p class="small text-muted mb-1">${rec.reason}</p>
                        <small class="text-muted fst-italic d-block mb-2">${rec.disclaimer}</small>
                    </div>
                    <div>
                        <div class="alert alert-primary mb-0 py-2 px-3 fw-bold">
                            Would you like to book an appointment with this doctor?
                        </div>
                    </div>
                </div>
            </div>
        `;

        loadDoctorListForBooking();
    } catch (err) {
        if (resDiv) {
            resDiv.innerHTML = `<div class="alert alert-warning py-2 small">AI suggestion currently unavailable. Showing available doctors directly.</div>`;
        }
        loadDoctorListForBooking();
    }
}

// ---------------------------------------------------------
// Phase 6: Government Scheme Pre-Authorization Handlers
// ---------------------------------------------------------
async function loadPatientSchemeApplications(patientIdOverride) {
    const patientId = patientIdOverride || getActivePatientId();
    const tableBody = document.getElementById('patientSchemeApplicationsTableBody');
    if (!tableBody) return;

    if (!patientId) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted small py-2">Select a patient to view scheme applications.</td></tr>';
        return;
    }

    try {
        const apps = await API.governmentApplicationAPI.list(patientId);
        if (!apps || apps.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted small py-2">No government scheme pre-auth applications filed yet. Click "Apply for Scheme Pre-Auth" above.</td></tr>';
            return;
        }

        const getStatusBadge = (status) => {
            switch ((status || '').toLowerCase()) {
                case 'approved': return '<span class="badge bg-success">Approved</span>';
                case 'pre-authorized': return '<span class="badge bg-info text-dark">Pre-Authorized</span>';
                case 'submitted': return '<span class="badge bg-warning text-dark">Submitted</span>';
                case 'under review': return '<span class="badge bg-primary">Under Review</span>';
                case 'rejected': return '<span class="badge bg-danger">Rejected</span>';
                default: return `<span class="badge bg-secondary">${status || 'Draft'}</span>`;
            }
        };

        tableBody.innerHTML = apps.map(app => `
            <tr>
                <td><strong>${app.application_id}</strong></td>
                <td><span class="badge bg-light text-dark border">${app.scheme_code}</span><br><small class="text-muted">${app.scheme_name}</small></td>
                <td><small>${app.hospital_name || '-'}</small></td>
                <td><small>${app.treatment_description ? app.treatment_description.substring(0, 35) + '...' : '-'}</small></td>
                <td>${API.UI.formatCurrency(app.estimated_cost)}</td>
                <td class="fw-bold text-success">${API.UI.formatCurrency(app.approved_amount)}</td>
                <td>${getStatusBadge(app.status)}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.warn('Error loading patient scheme applications:', err);
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted small py-2">Unable to load scheme applications.</td></tr>';
    }
}

async function loadSchemesForModal() {
    const select = document.getElementById('schemeModalSelect');
    if (!select) return;

    try {
        select.innerHTML = '<option value="">Loading schemes...</option>';
        const schemes = await API.governmentAPI.listSchemes();
        const activeSchemes = (schemes || []).filter(s => s.status === 'Active');
        if (activeSchemes.length === 0) {
            select.innerHTML = '<option value="">No active government schemes available</option>';
            return;
        }

        select.innerHTML = '<option value="">-- Choose Healthcare Scheme --</option>' +
            activeSchemes.map(s => `
                <option value="${s.scheme_code}">
                    ${s.scheme_code} — ${s.scheme_name} (${API.UI.formatCurrency(s.coverage_amount)})
                </option>
            `).join('');
    } catch (err) {
        console.error('Error fetching schemes for modal:', err);
        select.innerHTML = '<option value="">Failed to load schemes</option>';
    }
}

async function submitSchemeApplication() {
    const patientId = getActivePatientId();
    if (!patientId) {
        API.UI.showToast('No active patient selected.', 'warning');
        return;
    }

    const schemeCode = document.getElementById('schemeModalSelect')?.value;
    const hospitalName = document.getElementById('schemeHospitalName')?.value.trim();
    const treatmentDesc = document.getElementById('schemeTreatmentDesc')?.value.trim();
    const estimatedCost = parseFloat(document.getElementById('schemeEstimatedCost')?.value || '0');
    const requestedAmount = parseFloat(document.getElementById('schemeRequestedAmount')?.value || '0');

    if (!schemeCode) {
        API.UI.showToast('Please select a healthcare scheme.', 'warning');
        return;
    }
    if (!treatmentDesc) {
        API.UI.showToast('Please describe the clinical procedure or treatment.', 'warning');
        return;
    }
    if (!estimatedCost || estimatedCost <= 0) {
        API.UI.showToast('Please enter a valid estimated cost.', 'warning');
        return;
    }

    const submitBtn = document.getElementById('submitSchemeBtn');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Submitting...';
    }

    try {
        const payload = {
            patient_id: patientId,
            scheme_code: schemeCode,
            hospital_name: hospitalName,
            treatment_description: treatmentDesc,
            estimated_cost: estimatedCost,
            requested_amount: requestedAmount || estimatedCost
        };

        const res = await API.governmentApplicationAPI.submit(payload);
        API.UI.showToast(`Pre-authorization application ${res.application?.application_id || ''} submitted successfully!`, 'success');

        // Close modal
        const modalEl = document.getElementById('schemeApplyModal');
        if (modalEl && window.bootstrap && window.bootstrap.Modal) {
            const modalInstance = bootstrap.Modal.getInstance(modalEl) || new bootstrap.Modal(modalEl);
            modalInstance.hide();
        } else if (modalEl) {
            modalEl.classList.remove('show');
            modalEl.style.display = 'none';
            document.body.classList.remove('modal-open');
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        }

        // Reset inputs
        const descEl = document.getElementById('schemeTreatmentDesc');
        if (descEl) descEl.value = '';

        // Reload table
        await loadPatientSchemeApplications();
    } catch (err) {
        console.error('Failed to submit scheme application:', err);
        API.UI.showToast(err.message || 'Failed to submit scheme application.', 'danger');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-send-fill me-1"></i> Submit Pre-Authorization';
        }
    }
}

// Window attachments for inline event handlers & global accessibility
window.loadPatientSchemeApplications = loadPatientSchemeApplications;
window.loadSchemesForModal = loadSchemesForModal;
window.submitSchemeApplication = submitSchemeApplication;
window.loadReserveAccount = loadReserveAccount;
window.loadReserveLedger = loadReserveLedger;
window.getAIAndLoadDoctors = getAIAndLoadDoctors;
window.loadDoctorListForBooking = loadDoctorListForBooking;
window.loadPatientAppointments = loadPatientAppointments;
window.submitAppointmentBooking = submitAppointmentBooking;
window.showBookingForm = showBookingForm;



// ─── Gateway Payment Orders (Phase 10) ───────────────────────────────────────
async function loadMyPaymentOrders() {
    const container = document.getElementById('myOrdersContainer');
    if (!container) return;

    container.innerHTML = '<p class="text-muted text-center py-3"><span class="spinner-border spinner-border-sm me-1"></span> Loading orders...</p>';

    try {
        const patientIdEl = document.getElementById('dashPatientId') || document.getElementById('profilePatientId') || document.getElementById('patientId');
        const patientId = patientIdEl ? patientIdEl.innerText.trim() : (window.activeDashboardPatientId || '');

        const orders = await API.paymentAPI.listOrders(patientId);

        if (!orders || orders.length === 0) {
            container.innerHTML = '<p class="text-muted text-center py-4"><i class="bi bi-receipt me-2"></i>No payment orders found. Orders appear here after you initiate a gateway payment.</p>';
            return;
        }

        const statusBadge = (s) => {
            const map = { SUCCESS: 'success', ACTIVE: 'primary', PENDING: 'warning', FAILED: 'danger', EXPIRED: 'secondary', CANCELLED: 'secondary' };
            return `<span class="badge bg-${map[s] || 'secondary'}">${s}</span>`;
        };

        const rows = orders.map(o => `
            <tr>
                <td><small class="font-monospace text-muted">${o.order_id}</small></td>
                <td><span class="badge bg-light text-dark border">${o.provider_category || o.payment_type || '—'}</span></td>
                <td>₹${parseFloat(o.amount || 0).toFixed(2)}</td>
                <td>${statusBadge(o.status)}</td>
                <td>${o.contribution_amount ? `<span class="text-success fw-bold">₹${parseFloat(o.contribution_amount).toFixed(2)}</span>` : '<span class="text-muted">—</span>'}</td>
                <td><small class="text-muted">${o.utr || '—'}</small></td>
                <td><small class="text-muted">${o.created_at ? new Date(o.created_at).toLocaleDateString('en-IN', {day:'2-digit',month:'short',year:'numeric'}) : '—'}</small></td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover table-sm table-custom">
                    <thead>
                        <tr>
                            <th>Order Ref</th>
                            <th>Category</th>
                            <th>Amount</th>
                            <th>Status</th>
                            <th>HPF Contribution</th>
                            <th>UTR</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    } catch (err) {
        console.error('Failed to load payment orders:', err);
        container.innerHTML = `<div class="alert alert-warning py-2 small"><i class="bi bi-exclamation-triangle me-1"></i> Could not load orders: ${err.message || 'Unknown error'}. Please try again.</div>`;
    }
}

window.loadMyPaymentOrders = loadMyPaymentOrders;
