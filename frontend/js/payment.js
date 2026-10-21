/**
 * PatientCare Healthcare Platform
 * Payment & Digital Receipt Controller (payment.js)
 * Phase 10: YouPI-PG Payment Gateway Integration
 * 
 * Payment workflow:
 *  1. Provider creates a bill → POST /api/payments/orders/create/ (server generates order + checkout URL)
 *  2. Patient is redirected / shown checkout modal (YouPI-PG hosted OR sandbox)
 *  3. Gateway sends HMAC-verified webhook → /api/payments/webhook/
 *  4. Backend atomically credits Health Protection Fund
 *  5. Patient polls GET /api/payments/orders/<id>/status/ to confirm
 * 
 * Contribution rates (server-authoritative, never client-computed):
 *   Doctor:    10% of bill
 *   Pathology: 10% of bill
 *   Pharmacy:   5% of bill
 */

document.addEventListener('DOMContentLoaded', () => {
    initPaymentModule();
});

// ─────────────────────────────────────────────────────────────────────────────
// Module initialisation
// ─────────────────────────────────────────────────────────────────────────────
async function initPaymentModule() {
    loadRecentPayments();
    loadRecentOrders();

    // ── New Gateway Payment form (orders/create)
    const gatewayForm = document.getElementById('gatewayPaymentForm');
    if (gatewayForm) {
        gatewayForm.addEventListener('submit', handleGatewayPaymentSubmit);
    }

    // ── Legacy direct payment form (backward compat for internal admin use)
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
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Processing...';

            try {
                const res = await API.paymentAPI.create(payload);
                API.UI.showToast(
                    `Payment of ₹${payload.amount} recorded! Txn: ${res.payment.transaction_id}`,
                    'success', 'Payment Recorded'
                );
                displayReceipt(res.payment, res.health_protection_contribution);
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

    // ── Sandbox simulate button
    const simBtn = document.getElementById('sandboxSimulateBtn');
    if (simBtn) {
        simBtn.addEventListener('click', handleSandboxSimulate);
    }

    // ── Check if arriving from a checkout redirect with order_id query param
    const urlParams = new URLSearchParams(window.location.search);
    const orderIdFromUrl = urlParams.get('pay_order') || urlParams.get('order_id');
    if (orderIdFromUrl) {
        pollOrderStatus(orderIdFromUrl);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// GATEWAY PAYMENT: Create order → checkout
// ─────────────────────────────────────────────────────────────────────────────
async function handleGatewayPaymentSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');

    const patientId = (document.getElementById('gwPatientId') || document.getElementById('payPatientId'))?.value?.trim();
    const paymentType = document.getElementById('gwPayType')?.value || document.getElementById('payType')?.value;
    const amount = document.getElementById('gwAmount')?.value || document.getElementById('payAmount')?.value;
    const serviceDescription = document.getElementById('gwDescription')?.value?.trim()
        || document.getElementById('payDescription')?.value?.trim()
        || `Healthcare service: ${paymentType}`;
    const providerId = document.getElementById('gwProviderId')?.value?.trim() || '';
    const providerName = document.getElementById('gwProviderName')?.value?.trim() || '';

    if (!patientId || !amount || parseFloat(amount) <= 0) {
        API.UI.showToast('Please fill in patient ID and a valid amount.', 'warning');
        return;
    }

    // Show estimated contribution to provider/admin (informational only - server is authoritative)
    const rate = CONTRIBUTION_RATE_MAP[paymentType] || 10;
    const estimated = (parseFloat(amount) * rate / 100).toFixed(2);

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Initiating Checkout...';

    try {
        const orderRes = await API.paymentAPI.createOrder({
            patient_id: patientId,
            payment_type: paymentType,
            amount: amount,
            service_description: serviceDescription,
            provider_id: providerId,
            provider_name: providerName,
        });

        displayOrderInitiated(orderRes);

        // If sandbox mode, show inline simulator; if live, redirect to checkout URL
        if (orderRes.sandbox_mode) {
            showSandboxCheckout(orderRes);
        } else if (orderRes.checkout_url) {
            window.location.href = orderRes.checkout_url;
        }

    } catch (err) {
        API.UI.showToast(err.message || 'Failed to initiate payment order.', 'danger', 'Gateway Error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-qr-code me-1"></i> Generate UPI Payment Order';
    }
}

// Contribution rate hint map (display only — server is always authoritative)
const CONTRIBUTION_RATE_MAP = {
    'Doctor Payment':    10,
    'Pathology Payment': 10,
    'Pharmacy Payment':   5,
};

// ─────────────────────────────────────────────────────────────────────────────
// ORDER INITIATED DISPLAY
// ─────────────────────────────────────────────────────────────────────────────
function displayOrderInitiated(order) {
    const container = document.getElementById('orderInitiatedContainer') || document.getElementById('digitalReceiptDisplay');
    if (!container) return;

    const sandboxBadge = order.sandbox_mode
        ? `<span class="badge bg-warning text-dark ms-2"><i class="bi bi-beaker me-1"></i>SANDBOX MODE</span>`
        : `<span class="badge bg-success ms-2"><i class="bi bi-shield-check me-1"></i>LIVE</span>`;

    container.style.display = 'block';
    container.innerHTML = `
        <div class="card border-primary p-4 bg-light shadow-sm mb-3">
            <div class="d-flex justify-content-between align-items-center border-bottom pb-3 mb-3">
                <div>
                    <h5 class="text-primary mb-0">
                        <i class="bi bi-qr-code me-2"></i>Payment Order Created ${sandboxBadge}
                    </h5>
                    <small class="text-muted">Order ID: <strong>${order.order_id}</strong></small>
                </div>
                <span class="badge bg-primary fs-6">${order.status}</span>
            </div>
            <div class="row g-3">
                <div class="col-md-4">
                    <small class="text-muted d-block">BILL AMOUNT</small>
                    <strong class="text-dark fs-5">₹${parseFloat(order.amount).toFixed(2)}</strong>
                </div>
                <div class="col-md-4">
                    <small class="text-muted d-block">HEALTH PROTECTION CONTRIBUTION</small>
                    <strong class="text-success fs-5">
                        ₹${parseFloat(order.expected_contribution).toFixed(2)}
                        <small class="text-muted">(${order.contribution_rate}%)</small>
                    </strong>
                </div>
                <div class="col-md-4">
                    <small class="text-muted d-block">GATEWAY</small>
                    <strong>${order.gateway}</strong>
                </div>
            </div>
            <div class="mt-3 p-3 bg-info-subtle border border-info rounded">
                <i class="bi bi-info-circle me-1 text-info"></i>
                <strong>Health Protection Fund:</strong> After successful payment, 
                <strong>₹${parseFloat(order.expected_contribution).toFixed(2)} (${order.contribution_rate}%)</strong>
                will be automatically credited to the patient's PatientCare Wallet.
                <br><small class="text-muted">This is not yet transferable to external insurance. It remains in the PatientCare Insurance Support Ledger until an authorized insurer is integrated.</small>
            </div>
            <div id="orderStatusPoll_${order.order_id}" class="mt-3"></div>
        </div>`;
    container.scrollIntoView({ behavior: 'smooth' });
}

// ─────────────────────────────────────────────────────────────────────────────
// SANDBOX CHECKOUT (Simulation Modal)
// ─────────────────────────────────────────────────────────────────────────────
function showSandboxCheckout(order) {
    const pollContainer = document.getElementById(`orderStatusPoll_${order.order_id}`);
    if (!pollContainer) return;

    pollContainer.innerHTML = `
        <div class="alert alert-warning border">
            <h6><i class="bi bi-beaker me-1"></i>Sandbox Checkout Simulator</h6>
            <p class="mb-2 small">In <strong>Sandbox Mode</strong>, no real UPI payment is required. 
            Use the buttons below to simulate gateway outcomes for Order <code>${order.order_id}</code>.</p>
            <div class="d-flex gap-2 flex-wrap">
                <button class="btn btn-success btn-sm" onclick="simulatePaymentOutcome('${order.order_id}', 'SUCCESS')">
                    <i class="bi bi-check-circle me-1"></i>Simulate Payment SUCCESS
                </button>
                <button class="btn btn-danger btn-sm" onclick="simulatePaymentOutcome('${order.order_id}', 'FAILED')">
                    <i class="bi bi-x-circle me-1"></i>Simulate FAILED
                </button>
                <button class="btn btn-secondary btn-sm" onclick="simulatePaymentOutcome('${order.order_id}', 'EXPIRED')">
                    <i class="bi bi-clock me-1"></i>Simulate EXPIRED
                </button>
                <button class="btn btn-warning btn-sm" onclick="simulatePaymentOutcome('${order.order_id}', 'CANCELLED')">
                    <i class="bi bi-slash-circle me-1"></i>Simulate CANCELLED
                </button>
            </div>
            <div id="sim_result_${order.order_id}" class="mt-2"></div>
        </div>`;
}

window.simulatePaymentOutcome = async function(orderId, event) {
    const resultDiv = document.getElementById(`sim_result_${orderId}`);
    if (resultDiv) resultDiv.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Simulating ${event}...`;

    try {
        const res = await API.paymentAPI.sandboxSimulate(orderId, event);
        const whResult = res.webhook_result || {};

        if (resultDiv) {
            const contributed = whResult.health_protection_contribution;
            const contributionBadge = contributed
                ? `<br>💚 Health Protection Fund: <strong>₹${contributed.amount.toFixed(2)}</strong> credited. Wallet Balance: <strong>₹${contributed.available_balance.toFixed(2)}</strong>`
                : '';
            resultDiv.innerHTML = `<div class="alert alert-${event === 'SUCCESS' ? 'success' : 'secondary'} py-2 mt-2">
                <strong>${event}</strong> simulated. Order: <code>${orderId}</code>${contributionBadge}
            </div>`;
        }

        if (event === 'SUCCESS') {
            API.UI.showToast(`✅ Payment verified! Health protection fund credited.`, 'success', 'Payment Confirmed');
            pollOrderStatus(orderId, true);
        }

        loadRecentPayments();
        loadRecentOrders();
    } catch (err) {
        if (resultDiv) resultDiv.innerHTML = `<div class="alert alert-danger py-2">${err.message}</div>`;
        API.UI.showToast(err.message || 'Simulation failed.', 'danger');
    }
};

// ─────────────────────────────────────────────────────────────────────────────
// POLL ORDER STATUS
// ─────────────────────────────────────────────────────────────────────────────
async function pollOrderStatus(orderId, immediate = false) {
    const checkStatus = async () => {
        try {
            const data = await API.paymentAPI.getOrderStatus(orderId);
            if (data.status === 'SUCCESS') {
                displayOrderSuccess(data);
                return true;
            }
            if (['FAILED', 'EXPIRED', 'CANCELLED'].includes(data.status)) {
                displayOrderTerminated(data);
                return true;
            }
            return false;
        } catch (err) {
            console.warn('Order status poll error:', err);
            return false;
        }
    };

    if (immediate) {
        await checkStatus();
        return;
    }

    // Poll every 3 seconds up to 60 seconds
    let attempts = 0;
    const maxAttempts = 20;
    const intervalId = setInterval(async () => {
        attempts++;
        const done = await checkStatus();
        if (done || attempts >= maxAttempts) clearInterval(intervalId);
    }, 3000);
}

function displayOrderSuccess(data) {
    const container = document.getElementById('digitalReceiptDisplay') || document.getElementById('orderInitiatedContainer');
    if (!container) return;

    const walletInfo = data.wallet_balance !== undefined
        ? `<div class="col-md-6">
            <small class="text-muted d-block">WALLET BALANCE (Health Protection)</small>
            <strong class="text-success fs-5">₹${parseFloat(data.wallet_balance).toFixed(2)}</strong>
           </div>`
        : '';

    container.innerHTML = `
        <div class="card border-success p-4 shadow-sm">
            <div class="d-flex justify-content-between align-items-center border-bottom pb-3 mb-3">
                <h5 class="text-success mb-0"><i class="bi bi-check-circle-fill me-2"></i>Payment Verified & Confirmed</h5>
                <span class="badge bg-success fs-6">PAYMENT SUCCESS</span>
            </div>
            <div class="row g-3">
                <div class="col-md-6">
                    <small class="text-muted d-block">ORDER ID</small>
                    <strong>${data.order_id}</strong>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">TRANSACTION ID</small>
                    <strong>${data.transaction_id || '-'}</strong>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">AMOUNT PAID</small>
                    <strong>₹${parseFloat(data.amount).toFixed(2)}</strong>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">UPI REFERENCE (UTR)</small>
                    <strong>${data.utr || 'N/A'}</strong>
                </div>
                <div class="col-md-6">
                    <small class="text-muted d-block">HEALTH PROTECTION CREDITED</small>
                    <strong class="text-success">₹${parseFloat(data.contribution_amount || data.expected_contribution || 0).toFixed(2)} (${data.contribution_rate}%)</strong>
                </div>
                ${walletInfo}
            </div>
            <div class="alert alert-success mt-3 py-2">
                <i class="bi bi-shield-check me-1"></i>
                <strong>Insurance-Support Balance Updated.</strong> Contributions accumulate in your PatientCare Health Protection Wallet. 
                Future integration with an authorized insurer will allow conversion to insurance premiums.
            </div>
            <div class="mt-2 text-end">
                <button class="btn btn-outline-secondary btn-sm" onclick="window.print()">
                    <i class="bi bi-printer me-1"></i>Print Receipt
                </button>
            </div>
        </div>`;
    container.scrollIntoView({ behavior: 'smooth' });
}

function displayOrderTerminated(data) {
    const container = document.getElementById('digitalReceiptDisplay') || document.getElementById('orderInitiatedContainer');
    if (!container) return;
    container.innerHTML = `
        <div class="alert alert-warning">
            <i class="bi bi-exclamation-triangle me-1"></i>
            <strong>Payment ${data.status}</strong> — Order <code>${data.order_id}</code>
            was <strong>${data.status.toLowerCase()}</strong>. No money has been deducted.
            You can retry by creating a new payment order.
        </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// LEGACY PAYMENTS LIST
// ─────────────────────────────────────────────────────────────────────────────
async function loadRecentPayments() {
    const tbody = document.getElementById('recentPaymentsTableBody');
    if (!tbody) return;

    try {
        const payments = await API.paymentAPI.list();
        if (!payments || payments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">No payment transactions recorded.</td></tr>';
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
                <td class="text-success"><small>${parseFloat(p.contribution_rate || 0) > 0 ? `+₹${parseFloat(p.contribution_amount || 0).toFixed(2)} (${p.contribution_rate}%)` : '—'}</small></td>
                <td><span class="badge bg-success">${p.status}</span></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load payments:', err);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// GATEWAY ORDERS LIST
// ─────────────────────────────────────────────────────────────────────────────
async function loadRecentOrders() {
    const tbody = document.getElementById('recentOrdersTableBody');
    if (!tbody) return;

    try {
        const orders = await API.paymentAPI.listOrders();
        if (!orders || orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No payment orders yet.</td></tr>';
            return;
        }

        const statusColor = { SUCCESS: 'success', ACTIVE: 'primary', PENDING: 'secondary', FAILED: 'danger', EXPIRED: 'warning', CANCELLED: 'secondary', REFUNDED: 'info' };
        tbody.innerHTML = orders.slice(0, 10).map(o => `
            <tr>
                <td><strong class="small">${o.order_id}</strong></td>
                <td>${o.created_at?.split('T')[0] || '-'}</td>
                <td>${o.patient_name}<br><small class="text-muted">${o.patient_id_display}</small></td>
                <td>${o.provider_category}</td>
                <td>${API.UI.formatCurrency(o.amount)}</td>
                <td class="text-success"><small>₹${parseFloat(o.expected_contribution_amount || 0).toFixed(2)} (${o.contribution_rate}%)</small></td>
                <td><span class="badge bg-${statusColor[o.status] || 'secondary'}">${o.status}</span></td>
            </tr>
        `).join('');
    } catch (err) {
        console.warn('Could not load orders table:', err);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// LEGACY RECEIPT DISPLAY
// ─────────────────────────────────────────────────────────────────────────────
function displayReceipt(p, hpfContribution) {
    const receiptContainer = document.getElementById('digitalReceiptDisplay');
    if (!receiptContainer) return;

    const hpfInfo = hpfContribution
        ? `<div class="col-12 border-top pt-3">
            <small class="text-muted d-block">HEALTH PROTECTION FUND CONTRIBUTION</small>
            <strong class="text-success">
                ₹${parseFloat(hpfContribution.credit_amount || 0).toFixed(2)} (${parseFloat(hpfContribution.rate || 0)}%)
                credited ${hpfContribution.is_duplicate ? '<span class="badge bg-warning">Duplicate Skipped</span>' : ''}
            </strong>
            <br><small class="text-muted">Wallet Balance: ₹${parseFloat(hpfContribution.available_balance || 0).toFixed(2)}</small>
           </div>`
        : '';

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
                ${hpfInfo}
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
        </div>`;
    receiptContainer.scrollIntoView({ behavior: 'smooth' });
}

// ─────────────────────────────────────────────────────────────────────────────
// SANDBOX SIMULATE BUTTON (standalone)
// ─────────────────────────────────────────────────────────────────────────────
async function handleSandboxSimulate() {
    const orderId = document.getElementById('simOrderId')?.value?.trim();
    const event = document.getElementById('simEvent')?.value || 'SUCCESS';
    if (!orderId) {
        API.UI.showToast('Enter an Order ID to simulate.', 'warning');
        return;
    }
    await simulatePaymentOutcome(orderId, event);
}
