/**
 * Health Insurance Assurance Healthcare Platform
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


// ─────────────────────────────────────────────────────────────────────────────
// Phase 10: YouPI-PG Payment Gateway Orders & Webhook Admin Functions
// ─────────────────────────────────────────────────────────────────────────────

async function loadGatewayOrders() {
    const tbody = document.getElementById('gatewayOrdersTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted"><span class="spinner-border spinner-border-sm me-1"></span> Loading...</td></tr>';

    try {
        const orders = await API.paymentAPI.listOrders();
        if (!orders || orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No payment orders yet.</td></tr>';
            return;
        }

        const statusColor = {
            SUCCESS: 'success', ACTIVE: 'primary', PENDING: 'secondary',
            FAILED: 'danger', EXPIRED: 'warning', CANCELLED: 'secondary', REFUNDED: 'info'
        };

        tbody.innerHTML = orders.map(o => `
            <tr>
                <td><code class="small">${o.order_id}</code></td>
                <td>${o.created_at?.split('T')[0] || '-'}</td>
                <td>${o.patient_name || '-'}<br><small class="text-muted">${o.patient_id_display || ''}</small></td>
                <td><span class="badge bg-secondary-subtle text-secondary">${o.provider_category || '-'}</span></td>
                <td class="fw-bold">₹${parseFloat(o.amount || 0).toFixed(2)}</td>
                <td class="text-success"><small>+₹${parseFloat(o.expected_contribution_amount || 0).toFixed(2)} <span class="text-muted">(${o.contribution_rate}%)</span></small></td>
                <td><small class="text-muted">${o.utr || '—'}</small></td>
                <td><span class="badge bg-${statusColor[o.status] || 'secondary'}">${o.status}</span></td>
            </tr>`).join('');
    } catch (err) {
        if (tbody) tbody.innerHTML = `<tr><td colspan="8" class="text-danger text-center small">${err.message || 'Failed to load orders.'}</td></tr>`;
    }
}

async function loadWebhookDeliveries() {
    const container = document.getElementById('webhookDeliveryContainer') || document.getElementById('webhookDeliveriesContainer');
    if (!container) return;
    container.innerHTML = '<p class="text-muted small text-center"><span class="spinner-border spinner-border-sm me-1"></span> Loading webhook audit log...</p>';

    try {
        const result = await API.apiFetch('/api/payments/webhook-deliveries/?limit=30');
        const deliveries = result.results || [];

        if (!deliveries.length) {
            container.innerHTML = '<p class="text-muted text-center py-3"><i class="bi bi-inbox me-2"></i>No webhook deliveries recorded yet.</p>';
            return;
        }

        const statusBadge = (s) => {
            const map = { PROCESSED: 'success', REJECTED: 'danger', DUPLICATE: 'warning', PENDING: 'secondary' };
            return `<span class="badge bg-${map[s] || 'secondary'}">${s}</span>`;
        };

        const rows = deliveries.map(d => `
            <tr>
                <td><small class="font-monospace text-muted">${d.delivery_id || d.id}</small></td>
                <td><small class="font-monospace">${d.order_id || '—'}</small></td>
                <td><span class="badge bg-light text-dark border">${d.event_type}</span></td>
                <td>${statusBadge(d.status)}</td>
                <td><small class="text-muted">${d.ip_address || '—'}</small></td>
                <td><small class="text-muted">${d.error_message || '—'}</small></td>
                <td><small class="text-muted">${d.received_at ? new Date(d.received_at).toLocaleString('en-IN') : '—'}</small></td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div class="table-responsive">
                <table class="table table-hover table-sm">
                    <thead class="table-dark">
                        <tr>
                            <th>Delivery ID</th>
                            <th>Order</th>
                            <th>Event</th>
                            <th>Status</th>
                            <th>IP</th>
                            <th>Error</th>
                            <th>Received At</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <small class="text-muted">Showing ${deliveries.length} of ${result.total} deliveries.</small>
        `;
    } catch (err) {
        console.error('Failed to load webhook deliveries:', err);
        container.innerHTML = `<div class="alert alert-warning py-2 small"><i class="bi bi-exclamation-triangle me-1"></i>Could not load webhook log: ${err.message}. Admin access required.</div>`;
    }
}

async function adminSandboxSimulate() {
    const orderId = document.getElementById('simOrderIdAdmin')?.value?.trim();
    const event = document.getElementById('simEventAdmin')?.value || 'SUCCESS';
    const resultDiv = document.getElementById('adminSimResult');

    if (!orderId) {
        if (resultDiv) resultDiv.innerHTML = '<small class="text-danger">Please enter an Order ID.</small>';
        return;
    }

    if (resultDiv) resultDiv.innerHTML = `<small class="text-muted"><span class="spinner-border spinner-border-sm me-1"></span> Simulating ${event}…</small>`;

    try {
        const res = await API.paymentAPI.sandboxSimulate(orderId, event);
        const wh = res.webhook_result || {};
        const contrib = wh.health_protection_contribution;

        if (resultDiv) {
            const contribLine = contrib
                ? `<br>💚 HPF Credited: <strong>₹${contrib.amount.toFixed(2)}</strong> (${contrib.rate}%) | Wallet: <strong>₹${contrib.available_balance.toFixed(2)}</strong>`
                : '';
            resultDiv.innerHTML = `<div class="alert alert-${event === 'SUCCESS' ? 'success' : 'secondary'} py-1 mt-1 small">
                <strong>${event}</strong> — Txn: <code>${wh.transaction_id || '—'}</code> | UTR: <code>${wh.utr || '—'}</code>${contribLine}
            </div>`;
        }
        // Refresh orders table after simulate
        loadGatewayOrders();
    } catch (err) {
        if (resultDiv) resultDiv.innerHTML = `<small class="text-danger">${err.message || 'Simulation failed.'}</small>`;
    }
}
