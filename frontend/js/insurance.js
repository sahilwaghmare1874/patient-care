/**
 * Health Insurance Assurance Healthcare Platform
 * Insurance Module Controller (insurance.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initInsuranceModule();
});

async function initInsuranceModule() {
    loadInsuranceClaims();

    const claimForm = document.getElementById('newInsuranceClaimForm');
    if (claimForm) {
        claimForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = claimForm.querySelector('button[type="submit"]');

            const payload = {
                patient_id: document.getElementById('clmPatientId').value.trim(),
                treatment_cost: document.getElementById('clmCost').value,
                requested_amount: document.getElementById('clmRequested').value,
                remarks: document.getElementById('clmRemarks').value.trim()
            };

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Submitting Claim...';

            try {
                const res = await API.insuranceAPI.submitClaim(payload);
                API.UI.showToast(`Claim ${res.claim.claim_id} submitted successfully!`, 'success');
                loadInsuranceClaims();
                claimForm.reset();
            } catch (err) {
                API.UI.showToast(err.message || 'Failed to submit insurance claim.', 'danger');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-shield-plus me-1"></i> Submit Insurance Claim';
            }
        });
    }
}

async function loadInsuranceClaims() {
    const tbody = document.getElementById('insuranceClaimsTableBody');
    if (!tbody) return;

    try {
        const claims = await API.insuranceAPI.listClaims();
        if (!claims || claims.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No insurance claims on record.</td></tr>';
            return;
        }

        tbody.innerHTML = claims.map(c => `
            <tr>
                <td><strong>${c.claim_id}</strong></td>
                <td>${c.patient_name} <br><small class="text-muted">${c.patient_id_display}</small></td>
                <td>${c.insurance_company}</td>
                <td>${API.UI.formatCurrency(c.treatment_cost)}</td>
                <td>${API.UI.formatCurrency(c.requested_amount)}</td>
                <td>
                    <span class="badge ${c.status === 'Approved' ? 'bg-success' : c.status === 'Rejected' ? 'bg-danger' : 'bg-warning'}">
                        ${c.status}
                    </span>
                    ${c.approved_amount > 0 ? `<br><small class="text-success fw-bold">₹${c.approved_amount}</small>` : ''}
                </td>
                <td>
                    ${c.status === 'Pending' ? `
                        <button class="btn btn-sm btn-outline-success" onclick="approveClaim('${c.claim_id}', ${c.requested_amount})">
                            <i class="bi bi-check-lg"></i> Approve
                        </button>
                    ` : `<small class="text-muted">${c.approval_date || 'Processed'}</small>`}
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load claims:', err);
    }
}

window.approveClaim = async function(claimId, requestedAmount) {
    try {
        await API.insuranceAPI.updateClaim(claimId, {
            status: 'Approved',
            approved_amount: requestedAmount,
            remarks: 'Claim reviewed and approved for secondary coverage.'
        });
        API.UI.showToast(`Claim ${claimId} approved for ₹${requestedAmount}!`, 'success');
        loadInsuranceClaims();
    } catch (err) {
        API.UI.showToast(err.message || 'Error approving claim.', 'danger');
    }
};
