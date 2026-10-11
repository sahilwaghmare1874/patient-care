/**
 * PatientCare Healthcare Platform
 * Government & Scheme Administration Controller (government.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initGovernmentDashboard();
});

let currentConfig = {
    doctor_percentage: 10.0,
    pathology_percentage: 10.0,
    pharmacy_percentage: 5.0,
    government_percentage: 5.0,
    patient_benefit_percentage: 70.0
};

async function initGovernmentDashboard() {
    loadGovernmentStats();
    loadGovernmentSchemes();
    loadAllocationConfig();
    loadSchemeApplications();

    // 1. Live Fund Calculation Preview
    const treatCostInput = document.getElementById('allocTreatmentCost');
    const govFundInput = document.getElementById('allocGovFund');
    const insFundInput = document.getElementById('allocInsFund');

    function updatePreview() {
        const cost = parseFloat(treatCostInput?.value) || 0;
        const gov = parseFloat(govFundInput?.value) || 0;
        const ins = parseFloat(insFundInput?.value) || 0;

        let approved = gov + ins;
        if (approved > cost) approved = cost;

        const doc = (approved * (currentConfig.doctor_percentage / 100)).toFixed(2);
        const path = (approved * (currentConfig.pathology_percentage / 100)).toFixed(2);
        const med = (approved * (currentConfig.pharmacy_percentage / 100)).toFixed(2);
        const adminGov = (approved * (currentConfig.government_percentage / 100)).toFixed(2);
        const benefit = (approved * (currentConfig.patient_benefit_percentage / 100)).toFixed(2);
        const outOfPocket = Math.max(0, cost - approved).toFixed(2);

        if (document.getElementById('prevTotalApproved')) document.getElementById('prevTotalApproved').innerText = API.UI.formatCurrency(approved);
        if (document.getElementById('prevDocAlloc')) document.getElementById('prevDocAlloc').innerText = API.UI.formatCurrency(doc);
        if (document.getElementById('prevPathAlloc')) document.getElementById('prevPathAlloc').innerText = API.UI.formatCurrency(path);
        if (document.getElementById('prevMedAlloc')) document.getElementById('prevMedAlloc').innerText = API.UI.formatCurrency(med);
        if (document.getElementById('prevGovAlloc')) document.getElementById('prevGovAlloc').innerText = API.UI.formatCurrency(adminGov);
        if (document.getElementById('prevBenefitAlloc')) document.getElementById('prevBenefitAlloc').innerText = API.UI.formatCurrency(benefit);
        if (document.getElementById('prevOutOfPocket')) document.getElementById('prevOutOfPocket').innerText = API.UI.formatCurrency(outOfPocket);

        // Insurance deficit warning
        const deficitAlert = document.getElementById('insDeficitAlert');
        if (deficitAlert) {
            if (cost > gov) {
                deficitAlert.style.display = 'block';
                deficitAlert.innerHTML = `
                    <i class="bi bi-info-circle-fill me-1"></i> Government funding (₹${gov}) is less than total treatment cost (₹${cost}).
                    <strong>Deficit of ₹${(cost - gov).toFixed(2)}</strong> can be covered via Insurance Claim below.
                `;
            } else {
                deficitAlert.style.display = 'none';
            }
        }
    }

    treatCostInput?.addEventListener('input', updatePreview);
    govFundInput?.addEventListener('input', updatePreview);
    insFundInput?.addEventListener('input', updatePreview);

    // 2. Fund Allocation Submit Handler
    const allocForm = document.getElementById('fundAllocationForm');
    if (allocForm) {
        allocForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = allocForm.querySelector('button[type="submit"]');

            const payload = {
                patient_id: document.getElementById('allocPatientId').value.trim(),
                total_treatment_cost: document.getElementById('allocTreatmentCost').value,
                approved_government_fund: document.getElementById('allocGovFund').value,
                approved_insurance_fund: document.getElementById('allocInsFund').value || 0,
                scheme_id: document.getElementById('allocSchemeSelect')?.value || null
            };

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Approving & Allocating...';

            try {
                const res = await API.fundsAPI.allocateFund(payload);
                API.UI.showToast(res.message || 'Healthcare fund approved and settled!', 'success', 'Fund Settled');
                loadGovernmentStats();
                allocForm.reset();
                updatePreview();
            } catch (err) {
                API.UI.showToast(err.message || 'Failed to allocate fund.', 'danger', 'Allocation Error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-shield-check me-1"></i> Approve & Distribute Healthcare Fund';
            }
        });
    }

    // 3. Create Scheme Form Handler
    const schemeForm = document.getElementById('newSchemeForm');
    if (schemeForm) {
        schemeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = schemeForm.querySelector('button[type="submit"]');

            const payload = {
                scheme_code: document.getElementById('scCode').value.trim(),
                scheme_name: document.getElementById('scName').value.trim(),
                description: document.getElementById('scDescription').value.trim(),
                eligibility: document.getElementById('scEligibility').value.trim(),
                maximum_fund: document.getElementById('scMaxFund').value,
                coverage_percentage: document.getElementById('scCoverage').value || 100,
                start_date: document.getElementById('scStartDate').value,
                end_date: document.getElementById('scEndDate').value,
                status: 'Active'
            };

            submitBtn.disabled = true;
            try {
                await API.governmentAPI.createScheme(payload);
                API.UI.showToast(`Scheme ${payload.scheme_name} created successfully!`, 'success');
                loadGovernmentSchemes();
                schemeForm.reset();
                const modal = bootstrap.Modal.getInstance(document.getElementById('newSchemeModal'));
                if (modal) modal.hide();
            } catch (err) {
                API.UI.showToast(err.message || 'Failed to create scheme.', 'danger');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }
}

async function loadGovernmentStats() {
    try {
        const stats = await API.governmentAPI.getStats();
        if (document.getElementById('govTotalPatients')) document.getElementById('govTotalPatients').innerText = stats.total_patients;
        if (document.getElementById('govTotalFunds')) document.getElementById('govTotalFunds').innerText = API.UI.formatCurrency(stats.total_approved_funds);
        if (document.getElementById('govTotalDistributed')) document.getElementById('govTotalDistributed').innerText = API.UI.formatCurrency(stats.total_distributed_funds);
        if (document.getElementById('govPatientBenefits')) document.getElementById('govPatientBenefits').innerText = API.UI.formatCurrency(stats.total_patient_benefits);

        if (document.getElementById('govDocPayouts')) document.getElementById('govDocPayouts').innerText = API.UI.formatCurrency(stats.total_doctor_payouts);
        if (document.getElementById('govPathPayouts')) document.getElementById('govPathPayouts').innerText = API.UI.formatCurrency(stats.total_pathology_payouts);
        if (document.getElementById('govMedPayouts')) document.getElementById('govMedPayouts').innerText = API.UI.formatCurrency(stats.total_pharmacy_payouts);
    } catch (err) {
        console.error('Error loading government stats:', err);
    }
}

async function loadAllocationConfig() {
    try {
        const cfg = await API.fundsAPI.getConfiguration();
        currentConfig = {
            doctor_percentage: parseFloat(cfg.doctor_percentage),
            pathology_percentage: parseFloat(cfg.pathology_percentage),
            pharmacy_percentage: parseFloat(cfg.pharmacy_percentage),
            government_percentage: parseFloat(cfg.government_percentage),
            patient_benefit_percentage: parseFloat(cfg.patient_benefit_percentage)
        };

        if (document.getElementById('ruleDocPct')) document.getElementById('ruleDocPct').innerText = `${currentConfig.doctor_percentage}%`;
        if (document.getElementById('rulePathPct')) document.getElementById('rulePathPct').innerText = `${currentConfig.pathology_percentage}%`;
        if (document.getElementById('ruleMedPct')) document.getElementById('ruleMedPct').innerText = `${currentConfig.pharmacy_percentage}%`;
        if (document.getElementById('ruleGovPct')) document.getElementById('ruleGovPct').innerText = `${currentConfig.government_percentage}%`;
        if (document.getElementById('ruleBenefitPct')) document.getElementById('ruleBenefitPct').innerText = `${currentConfig.patient_benefit_percentage}%`;
    } catch (err) {
        console.error('Error loading allocation config:', err);
    }
}

async function loadGovernmentSchemes() {
    const listEl = document.getElementById('governmentSchemesList');
    const selectEl = document.getElementById('allocSchemeSelect');
    if (!listEl) return;

    try {
        const schemes = await API.governmentAPI.listSchemes();
        if (!schemes || schemes.length === 0) {
            listEl.innerHTML = '<p class="text-muted">No government schemes registered.</p>';
            return;
        }

        listEl.innerHTML = schemes.map(s => `
            <div class="card mb-3 p-3 border shadow-sm">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0 text-primary fw-bold">${s.scheme_name}</h5>
                    <span class="badge ${s.status === 'Active' ? 'bg-success' : 'bg-secondary'}">${s.status}</span>
                </div>
                <div class="text-muted small mt-1">Code: <strong>${s.scheme_code}</strong> | Max Fund: <strong>${API.UI.formatCurrency(s.maximum_fund)}</strong> | Coverage: <strong>${s.coverage_percentage}%</strong></div>
                <p class="mb-1 mt-2 text-dark small">${s.description}</p>
                <div class="bg-light p-2 rounded small text-muted"><strong>Eligibility:</strong> ${s.eligibility}</div>
            </div>
        `).join('');

        if (selectEl) {
            selectEl.innerHTML = schemes.map(s => `
                <option value="${s.id}">${s.scheme_name} (${s.scheme_code}) - Max: ₹${s.maximum_fund}</option>
            `).join('');
        }
    } catch (err) {
        console.error('Failed to load schemes:', err);
    }
}


// ============================================================
// PHASE 6: Scheme Applications & Pre-Authorization Review
// ============================================================

async function loadSchemeApplications() {
    const tbody = document.getElementById('schemeApplicationsTableBody');
    if (!tbody) return;

    try {
        const apps = await API.governmentApplicationAPI.list();
        if (!apps || apps.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No scheme applications submitted yet.</td></tr>';
            return;
        }

        tbody.innerHTML = apps.map(a => {
            const statusClass =
                a.status === 'Approved' ? 'bg-success' :
                a.status === 'Pre-Authorized' ? 'bg-info text-dark' :
                a.status === 'Under Review' ? 'bg-warning text-dark' :
                a.status === 'Rejected' ? 'bg-danger' : 'bg-secondary';

            return `
                <tr>
                    <td><strong>${a.application_id}</strong></td>
                    <td>
                        <div class="fw-bold">${a.patient_name}</div>
                        <code class="small">${a.patient_id}</code>
                    </td>
                    <td><span class="badge bg-light text-dark border">${a.scheme_code}</span></td>
                    <td>
                        <div class="small fw-semibold">${a.hospital_name || 'Network Hospital'}</div>
                        <div class="small text-muted text-truncate" style="max-width: 180px;">${a.treatment_description}</div>
                    </td>
                    <td>${API.UI.formatCurrency(a.estimated_cost)}</td>
                    <td>${API.UI.formatCurrency(a.requested_amount)}</td>
                    <td class="fw-bold text-success">${API.UI.formatCurrency(a.approved_amount)}</td>
                    <td><span class="badge ${statusClass}">${a.status}</span></td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            ${a.status !== 'Approved' && a.status !== 'Rejected' ? `
                                <button type="button" class="btn btn-outline-info btn-sm" onclick="handleUpdateAppStatus('${a.application_id}', 'Pre-Authorized')">
                                    Pre-Auth
                                </button>
                                <button type="button" class="btn btn-outline-success btn-sm" onclick="handleUpdateAppStatus('${a.application_id}', 'Approved')">
                                    Approve
                                </button>
                                <button type="button" class="btn btn-outline-danger btn-sm" onclick="handleUpdateAppStatus('${a.application_id}', 'Rejected')">
                                    Reject
                                </button>
                            ` : `<span class="small text-muted">Settled</span>`}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-danger text-center py-3">Error loading applications: ${err.message}</td></tr>`;
    }
}

async function handleUpdateAppStatus(appId, newStatus) {
    let approvedAmount = null;
    let remarks = '';

    if (newStatus === 'Approved' || newStatus === 'Pre-Authorized') {
        const amtStr = prompt(`Enter Approved/Pre-Authorized Amount for ${appId} (₹):`, '50000');
        if (amtStr === null) return;
        approvedAmount = parseFloat(amtStr) || 0;
    }
    remarks = prompt(`Enter Officer Remarks for ${newStatus} status:`, `${newStatus} verified against scheme criteria`);
    if (remarks === null) return;

    try {
        const payload = {
            status: newStatus,
            officer_remarks: remarks,
            approved_amount: approvedAmount
        };
        const res = await API.governmentApplicationAPI.update(appId, payload);
        API.UI.showToast(res.message || `Application updated to ${newStatus}.`, 'success');
        loadSchemeApplications();
        loadGovernmentStats();
    } catch (err) {
        API.UI.showToast(err.message || 'Failed to update application.', 'danger');
    }
}
