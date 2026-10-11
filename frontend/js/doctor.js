/**
 * PatientCare Healthcare Platform
 * Doctor Consultation Portal (doctor.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initDoctorDashboard();
});

let activeDoctorPatient = null;

async function initDoctorDashboard() {
    loadDoctorStats();

    // Initialize Queue Date
    const queueDateEl = document.getElementById('queueDateFilter');
    if (queueDateEl && !queueDateEl.value) {
        queueDateEl.value = new Date().toISOString().split('T')[0];
    }
    loadDoctorTokenQueue();

    // 1. Patient Lookup Handler
    const searchForm = document.getElementById('doctorPatientSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = document.getElementById('searchPatientInput').value.trim();
            if (!query) return;

            const submitBtn = searchForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Searching...';

            try {
                const patient = await API.patientAPI.lookup(query);
                activeDoctorPatient = patient;
                displayDoctorPatientProfile(patient);
                loadPatientMedicalHistory(patient.patient_id);
                API.UI.showToast(`Patient ${patient.full_name} (${patient.patient_id}) verified.`, 'success');
            } catch (err) {
                API.UI.showToast(err.message || 'Patient record not found in system.', 'danger');
                document.getElementById('doctorPatientDetailsCard').style.display = 'none';
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-search me-1"></i> Search Patient';
            }
        });
    }

    // 2. Add Consultation Form Handler
    const consultForm = document.getElementById('newConsultationForm');
    if (consultForm) {
        consultForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!activeDoctorPatient) {
                API.UI.showToast('Please search and select a verified patient first.', 'warning');
                return;
            }

            const submitBtn = consultForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving Consultation...';

            const fee = parseFloat(document.getElementById('cFee').value) || 500.00;
            const payload = {
                patient_id: activeDoctorPatient.patient_id,
                visit_date: document.getElementById('cVisitDate').value,
                symptoms: document.getElementById('cSymptoms').value.trim(),
                diagnosis: document.getElementById('cDiagnosis').value.trim(),
                doctor_notes: document.getElementById('cNotes').value.trim(),
                treatment_plan: document.getElementById('cTreatment').value.trim(),
                operation_recommended: document.getElementById('cOperationRecommended').checked,
                operation_details: document.getElementById('cOperationDetails')?.value || '',
                pathology_referral: document.getElementById('cPathologyReferral').checked,
                pathology_tests_recommended: document.getElementById('cPathologyTests')?.value || '',
                pharmacy_referral: document.getElementById('cPharmacyReferral').checked,
                prescribed_medicines: document.getElementById('cMedicines').value.trim(),
                consultation_fee: fee
            };

            try {
                const res = await API.doctorAPI.createConsultation(payload);
                API.UI.showToast(res.message || 'Consultation successfully recorded!', 'success', 'Consultation Saved');

                // Phase 8: Record 90% Healthcare Reserve credit (Simulation - legacy)
                try {
                    const reserveRes = await API.fundsAPI.creditReserve({
                        patient_id: activeDoctorPatient.patient_id,
                        service_type: 'Doctor Consultation',
                        reference_id: res.consultation ? res.consultation.consultation_id : `CON-${Date.now()}`,
                        invoice_amount: fee
                    });
                    if (reserveRes && reserveRes.credit_amount) {
                        API.UI.showToast(`90% Healthcare Reserve credit of ₹${reserveRes.credit_amount} allocated to patient account.`, 'info', 'Reserve Credit');
                    }
                } catch (resErr) {
                    console.warn('Reserve credit notice:', resErr);
                }

                // Phase 9: Create payment to auto-trigger 10% Health Protection Fund contribution
                try {
                    const paymentRes = await API.paymentAPI.create({
                        patient_id: activeDoctorPatient.patient_id,
                        payment_type: 'Doctor Payment',
                        service_description: `Doctor Consultation - ${res.consultation ? res.consultation.consultation_id : 'CON'}`,
                        amount: fee,
                        payment_method: 'Assurance Benefit Wallet',
                        provider_id: document.getElementById('doctorId') ? document.getElementById('doctorId').value : ''
                    });
                    if (paymentRes && paymentRes.health_protection_contribution) {
                        const contrib = paymentRes.health_protection_contribution;
                        API.UI.showToast(`✅ 10% Health Protection Fund contribution of ₹${contrib.amount} credited automatically.`, 'success', 'Health Protection Fund');
                    }
                } catch (payErr) {
                    console.warn('Health protection fund notice:', payErr);
                }

                // If currently calling a token, mark it completed
                handleCallNextToken('complete');

                loadDoctorStats();
                loadDoctorTokenQueue();
                loadPatientMedicalHistory(activeDoctorPatient.patient_id);
                consultForm.reset();
            } catch (err) {
                API.UI.showToast(err.message || 'Failed to save consultation.', 'danger', 'Error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Save Consultation & Issue Prescription';
            }
        });
    }
}

async function loadDoctorStats() {
    try {
        const stats = await API.doctorAPI.getStats();
        if (document.getElementById('docTotalPatients')) document.getElementById('docTotalPatients').innerText = stats.total_patients;
        if (document.getElementById('docTotalConsultations')) document.getElementById('docTotalConsultations').innerText = stats.total_consultations;
        if (document.getElementById('docTodayAppointments')) document.getElementById('docTodayAppointments').innerText = stats.today_consultations;
        if (document.getElementById('docTotalPrescriptions')) document.getElementById('docTotalPrescriptions').innerText = stats.total_prescriptions;
    } catch (err) {
        console.error('Error loading doctor stats:', err);
    }
}

function displayDoctorPatientProfile(p) {
    const card = document.getElementById('doctorPatientDetailsCard');
    if (!card) return;
    card.style.display = 'block';

    const setIfExists = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val || '-';
    };

    setIfExists('dpFullName', p.full_name);
    setIfExists('dpPatientId', p.patient_id);
    setIfExists('dpHacNumber', p.hac_number);
    setIfExists('dpMaskedPan', p.pan_number);
    setIfExists('dpAgeGender', `${p.dob || ''} (${p.gender || ''})`);
    setIfExists('dpBlood', p.blood_group);
    setIfExists('dpConditions', p.existing_conditions || 'None reported');
    setIfExists('dpAllergies', p.allergies || 'None reported');
}

async function loadPatientMedicalHistory(patientId) {
    const listEl = document.getElementById('patientHistoryTimeline');
    if (!listEl) return;

    try {
        const data = await API.patientAPI.getCentralizedRecord(patientId);
        if (!data.consultations || data.consultations.length === 0) {
            listEl.innerHTML = '<p class="text-muted small">No prior consultations recorded for this patient.</p>';
            return;
        }

        listEl.innerHTML = data.consultations.map(c => `
            <div class="card mb-2 border-start border-primary border-4 p-3 bg-light">
                <div class="d-flex justify-content-between">
                    <strong class="text-primary">${c.visit_date} - ${c.doctor_name}</strong>
                    <span class="badge bg-secondary">${c.consultation_id}</span>
                </div>
                <div class="fw-bold mt-1 text-dark">Diagnosis: ${c.diagnosis}</div>
                <p class="text-muted small mb-1">Symptoms: ${c.symptoms}</p>
                <p class="text-muted small mb-1">Treatment: ${c.treatment_plan || 'Symptomatic'}</p>
                <div class="small"><strong>Prescription:</strong> <pre class="bg-white p-2 border rounded mt-1 mb-0">${c.prescriptions && c.prescriptions.length > 0 ? c.prescriptions[0].medicines : 'Direct clinical advice'}</pre></div>
            </div>
        `).join('');
    } catch (err) {
        listEl.innerHTML = '<p class="text-danger small">Failed to load prior clinical history.</p>';
    }
}


// ============================================================
// PHASE 4: Doctor Token Queue & Real-time Calling Controls
// ============================================================

function getActiveDoctorId() {
    const user = API.Storage.getUser();
    return user?.profile?.doctor_id || 'DOC-2026-0001';
}

async function loadDoctorTokenQueue() {
    const doctorId = getActiveDoctorId();
    const dateInput = document.getElementById('queueDateFilter');
    const date = dateInput ? dateInput.value : '';

    const tbody = document.getElementById('doctorQueueTableBody');
    if (!tbody) return;

    try {
        const queueData = await API.doctorAPI.getTokenQueue(doctorId, date);

        // Update Live Cards
        const curToken = queueData.current_token;
        const nextToken = queueData.next_token;

        if (document.getElementById('curTokenNumber')) {
            document.getElementById('curTokenNumber').innerText = curToken ? `#${curToken.token_number}` : '--';
        }
        if (document.getElementById('curTokenPatient')) {
            document.getElementById('curTokenPatient').innerText = curToken ? curToken.patient_name : 'No active consultation';
        }
        if (document.getElementById('curTokenDetails')) {
            document.getElementById('curTokenDetails').innerText = curToken ? `${curToken.patient_id} • Called: ${curToken.called_at ? new Date(curToken.called_at).toLocaleTimeString() : 'Just now'}` : 'Waiting to call next patient';
        }

        if (document.getElementById('nextTokenNumber')) {
            document.getElementById('nextTokenNumber').innerText = nextToken ? `#${nextToken.token_number}` : '--';
        }
        if (document.getElementById('nextTokenPatient')) {
            document.getElementById('nextTokenPatient').innerText = nextToken ? nextToken.patient_name : 'No patients waiting';
        }
        if (document.getElementById('nextTokenDetails')) {
            document.getElementById('nextTokenDetails').innerHTML = `Total waiting: <strong>${queueData.waiting_count || 0}</strong> of ${queueData.total_tokens || 0}`;
        }
        if (document.getElementById('waitingCount')) {
            document.getElementById('waitingCount').innerText = queueData.waiting_count || 0;
        }

        // Render Table
        if (!queueData.queue || queueData.queue.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No appointments scheduled for this session date.</td></tr>';
            return;
        }

        tbody.innerHTML = queueData.queue.map(q => {
            const statusBadgeClass =
                q.status === 'In Consultation' ? 'bg-primary' :
                q.status === 'Waiting' ? 'bg-warning text-dark' :
                q.status === 'Completed' ? 'bg-success' :
                q.status === 'No Show' ? 'bg-danger' : 'bg-secondary';

            const isCurrent = q.status === 'In Consultation';

            return `
                <tr class="${isCurrent ? 'table-primary fw-semibold' : ''}">
                    <td>
                        <span class="badge ${isCurrent ? 'bg-primary' : 'bg-dark'} fs-6">#${q.token_number}</span>
                    </td>
                    <td>
                        <div class="fw-bold">${q.patient_name}</div>
                        <code class="small">${q.patient_id}</code>
                    </td>
                    <td><small class="text-muted">${q.time_slot || '-'}</small></td>
                    <td><small class="text-truncate d-inline-block" style="max-width: 220px;">${q.symptoms || 'General Consultation'}</small></td>
                    <td><span class="badge ${statusBadgeClass}">${q.status}</span></td>
                    <td class="text-end">
                        <div class="btn-group btn-group-sm">
                            ${q.status === 'Waiting' ? `
                                <button type="button" class="btn btn-outline-primary btn-sm" onclick="handleCallNextToken('call', ${q.token_number})">
                                    <i class="bi bi-megaphone me-1"></i> Call
                                </button>
                            ` : ''}
                            <button type="button" class="btn btn-sm btn-outline-success" onclick="selectPatientFromQueue('${q.patient_id}')">
                                <i class="bi bi-person-check me-1"></i> Examine
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-danger text-center py-3">Failed to load queue: ${err.message}</td></tr>`;
    }
}

async function handleCallNextToken(action = 'call', tokenNumber = null) {
    const doctorId = getActiveDoctorId();
    const dateInput = document.getElementById('queueDateFilter');
    const date = dateInput ? dateInput.value : '';

    try {
        const payload = {
            doctor_id: doctorId,
            action: action,
            date: date
        };
        if (tokenNumber) payload.token_number = tokenNumber;

        const res = await API.doctorAPI.callNextToken(payload);
        API.UI.showToast(res.message, 'success', action === 'call' ? 'Patient Called' : 'Queue Updated');

        // Automatically populate consultation form with called patient
        if (action === 'call' && res.token_number) {
            // Find patient from queue and load
            loadDoctorTokenQueue();
            const searchInput = document.getElementById('searchPatientInput');
            if (searchInput && res.patient_name) {
                // If patient_id available
            }
        } else {
            loadDoctorTokenQueue();
        }
    } catch (err) {
        API.UI.showToast(err.message || 'Action failed on queue.', 'warning');
    }
}

function selectPatientFromQueue(patientId) {
    const input = document.getElementById('searchPatientInput');
    const form = document.getElementById('doctorPatientSearchForm');
    if (input && form) {
        input.value = patientId;
        form.dispatchEvent(new Event('submit', { cancelable: true }));
        // Scroll to examination card
        const card = document.getElementById('doctorPatientDetailsCard');
        if (card) {
            card.scrollIntoView({ behavior: 'smooth' });
        }
    }
}
