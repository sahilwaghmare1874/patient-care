/**
 * PatientCare Healthcare Platform
 * Pharmacy & Chemist Dispensary Controller (pharmacy.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initPharmacyDashboard();
});

let activePharmacyPatient = null;
let activePatientPrescriptions = [];

async function initPharmacyDashboard() {
    loadPharmacyStats();
    loadMedicineInventory();
    loadRecentDispensations();

    // 1. Patient Lookup Handler
    const searchForm = document.getElementById('pharmacyPatientSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = document.getElementById('pharmPatientInput').value.trim();
            if (!query) return;

            const submitBtn = searchForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Verifying...';

            try {
                const patient = await API.patientAPI.lookup(query);
                activePharmacyPatient = patient;

                const cardEl = document.getElementById('pharmPatientCard');
                if (cardEl) cardEl.style.display = 'block';

                const nameEl = document.getElementById('pharmPatientName');
                if (nameEl) nameEl.innerText = patient.full_name || '-';

                const idEl = document.getElementById('pharmPatientId');
                if (idEl) idEl.innerText = patient.patient_id || '-';

                const hacEl = document.getElementById('pharmHacNumber');
                if (hacEl) hacEl.innerText = patient.hac_number || '-';

                const panEl = document.getElementById('pharmMaskedPan');
                if (panEl) panEl.innerText = patient.pan_number || '-';

                const bloodEl = document.getElementById('pharmBlood');
                if (bloodEl) bloodEl.innerText = patient.blood_group || '-';

                loadPatientPrescriptions(patient.patient_id);
                API.UI.showToast(`Patient ${patient.full_name} (${patient.patient_id}) verified.`, 'success');
            } catch (err) {
                API.UI.showToast(err.message || 'Patient not found.', 'danger');
                const cardEl = document.getElementById('pharmPatientCard');
                if (cardEl) cardEl.style.display = 'none';
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-search me-1"></i> Search Patient';
            }
        });
    }

    // 2. Dispensation Form Calculation & Submit Handler
    const subtotalInput = document.getElementById('dispSubtotal');
    const gstInput = document.getElementById('dispGst');
    const totalInput = document.getElementById('dispTotal');

    if (subtotalInput && gstInput && totalInput) {
        subtotalInput.addEventListener('input', () => {
            const sub = parseFloat(subtotalInput.value) || 0;
            const gst = parseFloat((sub * 0.05).toFixed(2));
            const tot = parseFloat((sub + gst).toFixed(2));
            gstInput.value = gst;
            totalInput.value = tot;
        });
    }

    const dispenseForm = document.getElementById('newDispensationForm');
    if (dispenseForm) {
        dispenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!activePharmacyPatient) {
                API.UI.showToast('Please search and verify a patient first.', 'warning');
                return;
            }

            const submitBtn = dispenseForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Dispensing & Billing...';

            const payload = {
                patient_id: activePharmacyPatient.patient_id,
                medicines_dispensed: document.getElementById('dispMedicines').value.trim(),
                subtotal_amount: document.getElementById('dispSubtotal').value || 270,
                gst_amount: document.getElementById('dispGst').value || 13.50,
                total_amount: document.getElementById('dispTotal').value || 283.50,
                payment_status: 'Paid',
                prescription_id: document.getElementById('dispPrescriptionSelect')?.value || null
            };

            try {
                const res = await API.pharmacyAPI.createTransaction(payload);
                API.UI.showToast(res.message || 'Medicines dispensed & tax invoice created!', 'success', 'Invoice Generated');

                // Phase 8: Record 90% Healthcare Reserve credit (Simulation)
                try {
                    const reserveRes = await API.fundsAPI.creditReserve({
                        patient_id: activePharmacyPatient.patient_id,
                        service_type: 'Pharmacy Dispensation',
                        reference_id: res.transaction ? res.transaction.invoice_number : `INV-${Date.now()}`,
                        invoice_amount: parseFloat(payload.total_amount) || 0
                    });
                    if (reserveRes && reserveRes.credit_amount) {
                        API.UI.showToast(`90% Healthcare Reserve credit of ₹${reserveRes.credit_amount} allocated to patient account.`, 'info', 'Reserve Credit');
                    }
                } catch (resErr) {
                    console.warn('Reserve credit notice:', resErr);
                }

                loadPharmacyStats();
                loadRecentDispensations();
                dispenseForm.reset();
            } catch (err) {
                API.UI.showToast(err.message || 'Dispensing failed.', 'danger', 'Dispense Error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-receipt me-1"></i> Dispense Medicines & Generate Invoice';
            }
        });
    }
}

async function loadPharmacyStats() {
    try {
        const stats = await API.pharmacyAPI.getStats();
        if (document.getElementById('pharmTotalTransactions')) document.getElementById('pharmTotalTransactions').innerText = stats.total_transactions;
        if (document.getElementById('pharmTotalMedicines')) document.getElementById('pharmTotalMedicines').innerText = stats.medicines_in_stock;
        if (document.getElementById('pharmTotalRevenue')) document.getElementById('pharmTotalRevenue').innerText = API.UI.formatCurrency(stats.total_dispensed_amount);
    } catch (err) {
        console.error('Error loading pharmacy stats:', err);
    }
}

async function loadMedicineInventory() {
    const listEl = document.getElementById('medicineInventoryList');
    if (!listEl) return;

    try {
        const meds = await API.pharmacyAPI.listMedicines();
        if (!Array.isArray(meds) || meds.length === 0) {
            listEl.innerHTML = '<div class="col-12 text-muted small p-2">No medicines in stock catalog.</div>';
            return;
        }
        listEl.innerHTML = meds.map(m => `
            <div class="col-md-6 mb-2">
                <div class="card p-2 border shadow-sm">
                    <div class="d-flex justify-content-between">
                        <strong class="text-primary">${m.medicine_name}</strong>
                        <span class="badge bg-light text-dark border">₹${m.unit_price} / ${m.dosage_form}</span>
                    </div>
                    <small class="text-muted">${m.category} | Stock: ${m.stock_quantity}</small>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to load medicines:', err);
        listEl.innerHTML = '<div class="col-12 text-danger small p-2">Unable to load medicine catalog.</div>';
    }
}

async function loadRecentDispensations() {
    const tbody = document.getElementById('recentPharmacyTableBody');
    if (!tbody) return;

    try {
        const transactions = await API.pharmacyAPI.listTransactions();
        if (!transactions || transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No transactions found.</td></tr>';
            return;
        }

        tbody.innerHTML = transactions.slice(0, 10).map(t => `
            <tr>
                <td><strong>${t.invoice_number}</strong></td>
                <td>${t.dispensed_at?.split('T')[0] || '-'}</td>
                <td>${t.patient_name} <br><small class="text-muted">${t.patient_id_display}</small></td>
                <td>${t.medicines_dispensed?.substring(0, 35)}...</td>
                <td>${API.UI.formatCurrency(t.total_amount)}</td>
                <td><span class="badge bg-success">${t.payment_status}</span></td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Failed to load recent pharmacy bills:', err);
    }
}

async function loadPatientPrescriptions(patientId) {
    const selectEl = document.getElementById('dispPrescriptionSelect');
    const container = document.getElementById('patientPrescriptionsCard');
    if (!container) return;

    try {
        const rxList = await API.doctorAPI.listPrescriptions(patientId);
        activePatientPrescriptions = rxList;
        container.style.display = 'block';

        const rxListEl = document.getElementById('patientRxList');
        if (!rxList || rxList.length === 0) {
            if (rxListEl) rxListEl.innerHTML = '<p class="text-muted small">No active prescriptions on file from a doctor.</p>';
            if (selectEl) selectEl.innerHTML = '<option value="">No Active Prescription</option>';
            return;
        }

        if (rxListEl) {
            rxListEl.innerHTML = rxList.map(rx => `
                <div class="card mb-2 border-start border-primary border-4 p-3 bg-light">
                    <div class="d-flex justify-content-between">
                        <strong class="text-primary">${rx.prescription_id} - Dr. ${rx.doctor_name}</strong>
                        <span class="badge ${rx.is_dispensed ? 'bg-secondary' : 'bg-success'}">${rx.is_dispensed ? 'Dispensed' : 'Active'}</span>
                    </div>
                    <div class="text-muted small">Date: ${rx.date_prescribed}</div>
                    <pre class="bg-white p-2 border rounded mt-2 mb-0 small">${rx.medicines}</pre>
                </div>
            `).join('');
        }

        if (selectEl) {
            selectEl.innerHTML = rxList.map(rx => `
                <option value="${rx.prescription_id}">${rx.prescription_id} (${rx.date_prescribed}) - ${rx.is_dispensed ? '[Dispensed]' : '[Pending]'}</option>
            `).join('');
        }
    } catch (err) {
        container.style.display = 'none';
    }
}
