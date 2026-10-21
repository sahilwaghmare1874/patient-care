/**
 * PatientCare Healthcare Platform
 * Payment & Digital Receipt Controller (payment.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initPaymentModule();
});

async function initPaymentModule() {
    loadRecentPayments();

    const paymentForm = document.getElementById('smartPaymentForm');
    if (paymentForm) {
        paymentForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = paymentForm.querySelector('button[type="submit"]');

            const payload = {
                patient_id: document.getElementById('payPatientId').value.trim(),
                payment_type: document.getElementById('payType').value,
                amount: document.getElementById('payAmount').value,
                payment_method: document.getElementById('payMethod').value,
                service_description: document.getElementById('payDescription').value.trim() || 'Healthcare service bill'
            };

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Processing 256-bit Payment...';

            try {
                const res = await API.paymentAPI.create(payload);
                API.UI.showToast(`Payment of ₹${payload.amount} successful! Txn: ${res.payment.transaction_id}`, 'success', 'Payment Complete');
                displayReceipt(res.payment);
                loadRecentPayments();
                paymentForm.reset();
            } catch (err) {
                API.UI.showToast(err.message || 'Payment processing failed.', 'danger');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-credit-card me-1"></i> Pay Securely & Generate Digital Receipt';
            }
        });
    }
}

async function loadRecentPayments() {
    const tbody = document.getElementById('recentPaymentsTableBody');
    if (!tbody) return;

    try {
        const payments = await API.paymentAPI.list();
        if (!payments || payments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No payment transactions recorded.</td></tr>';
            return;
        }

        tbody.innerHTML = payments.slice(0, 10).map(p => `
            <tr>
                <td><strong>${p.transaction_id}</strong></td>
                <td>${p.created_at?.split('T')[0] || '-'}</td>
                <td>${p.patient_name} <br><small class="text-muted">${p.patient_id_display}</small></td>
                <td>${p.payment_type}</td>
                <td>${p.payment_method}</td>
                <td class="fw-bold">${API.UI.formatCurrency(p.amount)}</td>
                <td><span class="badge bg-success">${p.status}</span></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load payments:', err);
    }
}

function displayReceipt(p) {
    const receiptContainer = document.getElementById('digitalReceiptDisplay');
    if (!receiptContainer) return;

    receiptContainer.style.display = 'block';
    receiptContainer.innerHTML = `
        <div class="card border-primary p-4 bg-light shadow-sm">
            <div class="d-flex justify-content-between align-items-center border-bottom pb-3 mb-3">
                <div>
                    <h5 class="text-primary mb-0"><i class="bi bi-receipt me-1"></i> Official Digital Healthcare Receipt</h5>
                    <small class="text-muted">Transaction ID: <strong>${p.transaction_id}</strong></small>
                </div>
                <div class="text-end">
                    <span class="badge bg-success fs-6"><i class="bi bi-check-circle me-1"></i> VERIFIED PAYMENT</span>
                </div>
            </div>

            <div class="row g-3">
                <div class="col-md-6">
                    <small class="text-muted d-block">PATIENT ID</small>
                    <strong>${p.patient_id_display || p.patient}</strong>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">PAYMENT TYPE</small>
                    <strong>${p.payment_type}</strong>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">SERVICE DESCRIPTION</small>
                    <span>${p.service_description}</span>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">PAYMENT METHOD</small>
                    <span class="badge bg-primary">${p.payment_method}</span>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">BASE AMOUNT</small>
                    <span>${API.UI.formatCurrency(p.amount)}</span>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">GST COMPLIANCE</small>
                    <span>${parseFloat(p.gst_amount) > 0 ? API.UI.formatCurrency(p.gst_amount) + ' (5% Concessional)' : '0% (Exempt Healthcare Service)'}</span>
                </div>
                <div class="col-12 border-top pt-3 text-end">
                    <span class="fs-5 me-2 text-muted">Total Paid:</span>
                    <strong class="fs-4 text-success">${API.UI.formatCurrency(parseFloat(p.amount) + parseFloat(p.gst_amount))}</strong>
                </div>
            </div>

            <div class="mt-4 text-end">
                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="window.print()">
                    <i class="bi bi-printer me-1"></i> Print Digital Receipt
                </button>
            </div>
        </div>
    `;
    receiptContainer.scrollIntoView({ behavior: 'smooth' });
}
