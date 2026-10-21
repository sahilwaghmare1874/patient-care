/**
 * PatientCare Healthcare Platform
 * Pathology & Diagnostic Lab Controller (pathology.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initPathologyDashboard();
});

let activePathologyPatient = null;

async function initPathologyDashboard() {
    loadPathologyStats();
    loadTestsCatalog();
    loadRecentReports();

    // 1. Patient Lookup Handler
    const searchForm = document.getElementById('pathologyPatientSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = document.getElementById('pathPatientInput').value.trim();
            if (!query) return;

            const submitBtn = searchForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Searching...';

            try {
                const patient = await API.patientAPI.lookup(query);
                activePathologyPatient = patient;

                const cardEl = document.getElementById('pathPatientCard');
                if (cardEl) cardEl.style.display = 'block';

                const nameEl = document.getElementById('ppFullName');
                if (nameEl) nameEl.innerText = patient.full_name || '-';

                const idEl = document.getElementById('ppPatientId');
                if (idEl) idEl.innerText = patient.patient_id || '-';

                const hacEl = document.getElementById('ppHacNumber');
                if (hacEl) hacEl.innerText = patient.hac_number || '-';

                const panEl = document.getElementById('ppMaskedPan');
                if (panEl) panEl.innerText = patient.pan_number || '-';

                const bloodEl = document.getElementById('ppBlood');
                if (bloodEl) bloodEl.innerText = patient.blood_group || '-';

                loadPatientPathologyHistory(patient.patient_id);
                API.UI.showToast(`Patient ${patient.full_name} (${patient.patient_id}) verified.`, 'success');
            } catch (err) {
                API.UI.showToast(err.message || 'Patient not found.', 'danger');
                const cardEl = document.getElementById('pathPatientCard');
                if (cardEl) cardEl.style.display = 'none';
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-search me-1"></i> Search Patient';
            }
        });
    }

    // 2. Add Pathology Report Handler
    const reportForm = document.getElementById('newPathologyReportForm');
    if (reportForm) {
        reportForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!activePathologyPatient) {
                API.UI.showToast('Please search and verify a patient first.', 'warning');
                return;
            }

            const submitBtn = reportForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Uploading Report...';

            const payload = {
                patient_id: activePathologyPatient.patient_id,
                test_name: document.getElementById('labTestName').value.trim(),
                test_category: document.getElementById('labCategory').value,
                test_date: document.getElementById('labTestDate').value,
                test_cost: document.getElementById('labTestCost').value || 800,
                results_summary: document.getElementById('labResultsSummary').value.trim(),
                detailed_findings: document.getElementById('labDetailedFindings').value.trim(),
                status: document.getElementById('labStatus').value
            };

            try {
                const res = await API.pathologyAPI.createReport(payload);
                API.UI.showToast(res.message || 'Diagnostic report verified and uploaded!', 'success', 'Report Verified');

                // Phase 8: Record 90% Healthcare Reserve credit (Simulation)
                try {
                    const reserveRes = await API.fundsAPI.creditReserve({
                        patient_id: activePathologyPatient.patient_id,
                        service_type: 'Pathology Diagnostics',
                        reference_id: res.report ? res.report.report_id : `REP-${Date.now()}`,
                        invoice_amount: parseFloat(payload.test_cost) || 0
                    });
                    if (reserveRes && reserveRes.credit_amount) {
                        API.UI.showToast(`90% Healthcare Reserve credit of ₹${reserveRes.credit_amount} allocated to patient account.`, 'info', 'Reserve Credit');
                    }
                } catch (resErr) {
                    console.warn('Reserve credit notice:', resErr);
                }

                // Phase 9: Auto-credit 10% HPF contribution for Pathology Diagnostic
                try {
                    const hpfRes = await API.paymentAPI.create({
                        patient_id: activePathologyPatient.patient_id,
                        payment_type: 'Pathology Payment',
                        service_description: `Pathology Diagnostic - ${res.report ? res.report.report_id : 'REP'}`,
                        amount: parseFloat(payload.test_cost) || 0,
                        payment_method: 'Assurance Benefit Wallet'
                    });
                    if (hpfRes && hpfRes.health_protection_contribution) {
                        const contrib = hpfRes.health_protection_contribution;
                        API.UI.showToast(`✅ 10% Health Protection contribution of ₹${contrib.amount} credited to patient fund.`, 'success', 'Health Protection Fund');
                    }
                } catch (hpfErr) {
                    console.warn('HPF contribution notice (pathology):', hpfErr);
                }

                loadPathologyStats();
                loadRecentReports();
                loadPatientPathologyHistory(activePathologyPatient.patient_id);
                reportForm.reset();
            } catch (err) {
                API.UI.showToast(err.message || 'Failed to upload report.', 'danger', 'Upload Error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-file-earmark-check me-1"></i> Upload & Certify Digital Report';
            }
        });
    }
}

async function loadPathologyStats() {
    try {
        const stats = await API.pathologyAPI.getStats();
        if (document.getElementById('pathTotalReports')) document.getElementById('pathTotalReports').innerText = stats.total_reports;
        if (document.getElementById('pathVerifiedReports')) document.getElementById('pathVerifiedReports').innerText = stats.verified_reports;
        if (document.getElementById('pathPendingReports')) document.getElementById('pathPendingReports').innerText = stats.pending_reports;
        if (document.getElementById('pathAvailableTests')) document.getElementById('pathAvailableTests').innerText = stats.available_tests;
    } catch (err) {
        console.error('Error loading pathology stats:', err);
    }
}

async function loadTestsCatalog() {
    const listEl = document.getElementById('pathologyTestsCatalogList');
    if (!listEl) return;

    try {
        const tests = await API.pathologyAPI.listTests();
        if (!Array.isArray(tests) || tests.length === 0) {
            listEl.innerHTML = '<div class="col-12 text-muted small p-2">No tests in diagnostic catalog.</div>';
            return;
        }
        listEl.innerHTML = tests.map(t => `
            <div class="col-md-6 mb-2">
                <div class="card p-2 border shadow-sm">
                    <div class="d-flex justify-content-between">
                        <strong class="text-primary">${t.test_name}</strong>
                        <span class="badge bg-light text-dark border">₹${t.standard_price}</span>
                    </div>
                    <small class="text-muted">${t.category} | Code: ${t.test_code}</small>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to load test catalog:', err);
        listEl.innerHTML = '<div class="col-12 text-danger small p-2">Unable to load diagnostic catalog.</div>';
    }
}

async function loadRecentReports() {
    const tbody = document.getElementById('recentPathologyReportsTableBody');
    if (!tbody) return;

    try {
        const reports = await API.pathologyAPI.listReports();
        if (!reports || reports.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No reports found.</td></tr>';
            return;
        }

        tbody.innerHTML = reports.slice(0, 10).map(r => `
            <tr>
                <td><strong>${r.report_id}</strong></td>
                <td>${r.test_date}</td>
                <td>${r.patient_name} <br><small class="text-muted">${r.patient_id_display}</small></td>
                <td>${r.test_name}</td>
                <td>${API.UI.formatCurrency(r.test_cost)}</td>
                <td><span class="badge bg-success">${r.status}</span></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load recent reports:', err);
    }
}

async function loadPatientPathologyHistory(patientId) {
    const historyEl = document.getElementById('patientLabHistory');
    if (!historyEl) return;

    try {
        const reports = await API.pathologyAPI.listReports(patientId);
        if (!reports || reports.length === 0) {
            historyEl.innerHTML = '<p class="text-muted small">No prior lab tests on file for this patient.</p>';
            return;
        }

        historyEl.innerHTML = reports.map(r => `
            <div class="card mb-2 border-start border-success border-4 p-3 bg-light">
                <div class="d-flex justify-content-between">
                    <strong class="text-success">${r.test_name} (${r.report_id})</strong>
                    <span class="badge bg-success">${r.status}</span>
                </div>
                <div class="text-muted small">Date: ${r.test_date} | Lab: ${r.lab_name}</div>
                <div class="mt-2 p-2 bg-white rounded border small">
                    <strong>Findings:</strong> ${r.results_summary}
                </div>
            </div>
        `).join('');
    } catch (err) {
        historyEl.innerHTML = '<p class="text-danger small">Error loading patient lab history.</p>';
    }
}
