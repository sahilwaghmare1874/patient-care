/**
 * PatientCare Healthcare Platform
 * Admin Dashboard & System Rule Configuration (admin.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initAdminDashboard();
});

async function initAdminDashboard() {
    loadAdminStats();
    loadAdminConfig();
    loadAuditLogs();
    loadFinancialOverview();
    loadDuplicateClaimAlerts();

    // 1. Percentage Configuration Form Handler (Requirement 14 & 28)
    const configForm = document.getElementById('allocationConfigForm');
    const docInput = document.getElementById('cfgDoctor');
    const pathInput = document.getElementById('cfgPathology');
    const medInput = document.getElementById('cfgPharmacy');
    const govInput = document.getElementById('cfgGovernment');
    const benefitInput = document.getElementById('cfgBenefit');
    const sumDisplay = document.getElementById('cfgTotalSum');

    function calculateSum() {
        const d = parseFloat(docInput?.value) || 0;
        const p = parseFloat(pathInput?.value) || 0;
        const m = parseFloat(medInput?.value) || 0;
        const g = parseFloat(govInput?.value) || 0;
        const b = parseFloat(benefitInput?.value) || 0;
        const total = (d + p + m + g + b).toFixed(2);

        if (sumDisplay) {
            sumDisplay.innerText = `${total}%`;
            if (parseFloat(total) === 100.00) {
                sumDisplay.className = 'badge bg-success fs-6';
            } else {
                sumDisplay.className = 'badge bg-danger fs-6';
            }
        }
        return parseFloat(total);
    }

    [docInput, pathInput, medInput, govInput, benefitInput].forEach(el => {
        el?.addEventListener('input', calculateSum);
    });

    if (configForm) {
        configForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const sum = calculateSum();
            if (sum !== 100.00) {
                API.UI.showToast(`Total allocation percentage must equal exactly 100.00%. Current sum is ${sum}%.`, 'danger', 'Invalid Rule');
                return;
            }

            const submitBtn = configForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Updating Policy...';

            const payload = {
                doctor_percentage: docInput.value,
                pathology_percentage: pathInput.value,
                pharmacy_percentage: medInput.value,
                government_percentage: govInput.value,
                patient_benefit_percentage: benefitInput.value
            };

            try {
                const res = await API.fundsAPI.updateConfiguration(payload);
                API.UI.showToast(res.message || 'Fund distribution policy updated successfully!', 'success', 'Policy Activated');
                loadAdminConfig();
                loadAuditLogs();
            } catch (err) {
                API.UI.showToast(err.message || 'Failed to update policy.', 'danger');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-check2-circle me-1"></i> Save & Activate Allocation Rules';
            }
        });
    }
}

async function loadAdminStats() {
    try {
        const stats = await API.governmentAPI.getStats();
        if (document.getElementById('admTotalPatients')) document.getElementById('admTotalPatients').innerText = stats.total_patients;
        if (document.getElementById('admTotalDoctors')) document.getElementById('admTotalDoctors').innerText = stats.total_doctors;
        if (document.getElementById('admTotalLabs')) document.getElementById('admTotalLabs').innerText = stats.total_pathology_labs;
        if (document.getElementById('admTotalPharmacies')) document.getElementById('admTotalPharmacies').innerText = stats.total_pharmacies;
        if (document.getElementById('admTotalFunds')) document.getElementById('admTotalFunds').innerText = API.UI.formatCurrency(stats.total_approved_funds);
        if (document.getElementById('admTotalBenefits')) document.getElementById('admTotalBenefits').innerText = API.UI.formatCurrency(stats.total_patient_benefits);
        if (document.getElementById('admPendingClaims')) document.getElementById('admPendingClaims').innerText = stats.pending_claims;
    } catch (err) {
        console.error('Error loading admin stats:', err);
    }
}

async function loadAdminConfig() {
    try {
        const cfg = await API.fundsAPI.getConfiguration();
        if (document.getElementById('cfgDoctor')) document.getElementById('cfgDoctor').value = cfg.doctor_percentage;
        if (document.getElementById('cfgPathology')) document.getElementById('cfgPathology').value = cfg.pathology_percentage;
        if (document.getElementById('cfgPharmacy')) document.getElementById('cfgPharmacy').value = cfg.pharmacy_percentage;
        if (document.getElementById('cfgGovernment')) document.getElementById('cfgGovernment').value = cfg.government_percentage;
        if (document.getElementById('cfgBenefit')) document.getElementById('cfgBenefit').value = cfg.patient_benefit_percentage;

        const sumDisplay = document.getElementById('cfgTotalSum');
        if (sumDisplay) {
            sumDisplay.innerText = '100.00%';
            sumDisplay.className = 'badge bg-success fs-6';
        }
    } catch (err) {
        console.error('Error loading admin config:', err);
    }
}

async function loadAuditLogs() {
    const tbody = document.getElementById('auditLogsTableBody');
    if (!tbody) return;

    try {
        const logs = await API.apiFetch('/auth/audit-logs/');
        if (!logs || logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No audit logs recorded.</td></tr>';
            return;
        }

        tbody.innerHTML = logs.slice(0, 15).map(l => `
            <tr>
                <td><small class="text-muted">${l.created_at?.replace('T', ' ').substring(0, 19)}</small></td>
                <td><span class="badge bg-secondary">${l.role}</span></td>
                <td><strong>${l.action}</strong></td>
                <td><code>${l.patient_id || '-'}</code></td>
                <td><small class="text-muted">${l.ip_address || '127.0.0.1'}</small></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error loading audit logs:', err);
    }
}

window.verifyProvider = async function(type, id) {
    try {
        await API.apiFetch(`/auth/verify-provider/${type}/${id}/`, { method: 'POST' });
        API.UI.showToast(`Provider ${id} verified successfully!`, 'success');
        loadAdminStats();
    } catch (err) {
        API.UI.showToast(err.message || 'Verification failed.', 'danger');
    }
};


// ============================================================
// PHASE 11 & PHASE 8: Centralized Financial Overview
// ============================================================

async function loadFinancialOverview() {
    try {
        const data = await API.reportAPI.getFinancialOverview();
        const fin = data.financial_summary;

        if (document.getElementById('finTotalSpend')) {
            document.getElementById('finTotalSpend').innerText = API.UI.formatCurrency(fin.total_medical_spend);
        }
        if (document.getElementById('finReserveCredited')) {
            document.getElementById('finReserveCredited').innerText = API.UI.formatCurrency(fin.reserve_account_summary.total_credited);
        }
        if (document.getElementById('finGovDisbursed')) {
            document.getElementById('finGovDisbursed').innerText = API.UI.formatCurrency(fin.government_funding_approved);
        }
        if (document.getElementById('finInsSettled')) {
            document.getElementById('finInsSettled').innerText = API.UI.formatCurrency(fin.insurance_funding_approved);
        }
    } catch (err) {
        console.error('Error loading financial overview:', err);
    }
}

// ============================================================
// PHASE 7 & PHASE 9: AI Duplicate Claim & Anomaly Detection
// ============================================================

async function loadDuplicateClaimAlerts() {
    const container = document.getElementById('aiClaimAlertsContainer');
    if (!container) return;

    try {
        const res = await API.reportAPI.aiAuditClaims();
        if (!res.alerts || res.alerts.length === 0) {
            container.innerHTML = `
                <div class="alert alert-success py-2 small mb-0">
                    <i class="bi bi-check-circle-fill me-1"></i> AI Scan Status: <strong>0 Anomaly Detected</strong>. All claims, government fund disbursements, and payments are consistent.
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="alert alert-danger py-2 small mb-2">
                <i class="bi bi-exclamation-triangle-fill me-1"></i>
                <strong>AI Alert: ${res.total_alerts} Suspicious Billing / Duplicate submission anomalies found!</strong>
            </div>
            <div class="list-group list-group-flush small">
                ${res.alerts.map(a => `
                    <div class="list-group-item d-flex justify-content-between align-items-center py-2 px-0 bg-transparent">
                        <div>
                            <span class="badge ${a.severity === 'HIGH' ? 'bg-danger' : 'bg-warning text-dark'} me-1">${a.type}</span>
                            <span>${a.message}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `<div class="text-danger small">Scan unavailable: ${err.message}</div>`;
    }
}
