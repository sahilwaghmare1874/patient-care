/**
 * PatientCare Healthcare Platform
 * Centralized Patient & Fund Distribution Report Controller (reports.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    initReportsPage();
});

let reportChartInstance = null;

async function initReportsPage() {
    const urlParams = new URLSearchParams(window.location.search);
    let patientId = urlParams.get('id');

    if (!patientId) {
        const currentUser = API.Storage.getUser();
        if (currentUser && currentUser.profile && currentUser.profile.patient_id) {
            patientId = currentUser.profile.patient_id;
        }
    }

    const searchInput = document.getElementById('reportPatientSearchInput');
    const searchBtn = document.getElementById('reportSearchBtn');

    if (searchInput && patientId) searchInput.value = patientId;

    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', () => {
            const id = searchInput.value.trim();
            if (id) loadReport(id);
        });
    }

    if (patientId) {
        loadReport(patientId);
    } else {
        const container = document.getElementById('reportContentContainer');
        if (container) {
            container.innerHTML = `
                <div class="card p-5 text-center bg-white border shadow-sm">
                    <div class="display-6 text-primary mb-3"><i class="bi bi-file-earmark-medical"></i></div>
                    <h4 class="fw-bold">Search Patient to Generate Report</h4>
                    <p class="text-muted">Enter a valid Patient ID in the search box above to view their complete centralized clinical records, test investigations, pharmacy invoices, and fund distribution breakdown.</p>
                </div>
            `;
        }
    }
}

async function loadReport(patientId) {
    const container = document.getElementById('reportContentContainer');
    if (!container) return;

    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="mt-2 text-muted">Compiling centralized healthcare & fund distribution report...</p>
        </div>
    `;

    try {
        const data = await API.reportAPI.getPatientReport(patientId);
        renderFullReport(data);
    } catch (err) {
        container.innerHTML = `
            <div class="alert alert-danger p-4 text-center">
                <h5><i class="bi bi-exclamation-triangle-fill me-2"></i> Report Not Found</h5>
                <p>${err.message || 'Could not find records for Patient ID: ' + patientId}</p>
            </div>
        `;
    }
}

function renderFullReport(data) {
    const container = document.getElementById('reportContentContainer');
    if (!container) return;

    const p = data.patient;
    const fin = data.financial_summary;

    // Action button URLs
    const pdfUrl = API.reportAPI.getPDFUrl(p.patient_id);
    const csvUrl = API.reportAPI.getCSVUrl(p.patient_id);

    container.innerHTML = `
        <!-- Report Header Bar -->
        <div class="card p-4 border shadow-sm mb-4 bg-white">
            <div class="d-flex flex-wrap justify-content-between align-items-center border-bottom pb-3 mb-3 gap-2">
                <div>
                    <h3 class="text-primary fw-bold mb-0">PatientCare</h3>
                    <p class="text-muted small mb-0">Official Centralized Patient & Healthcare Fund Distribution Report</p>
                    <small class="text-muted">Generated: <strong>${data.generated_at}</strong></small>
                </div>
                <div class="d-flex gap-2 no-print">
                    <button class="btn btn-outline-secondary" onclick="window.print()">
                        <i class="bi bi-printer me-1"></i> Print
                    </button>
                    <a href="${csvUrl}" class="btn btn-outline-success" download>
                        <i class="bi bi-file-earmark-spreadsheet me-1"></i> CSV Export
                    </a>
                    <a href="${pdfUrl}" class="btn btn-primary" download>
                        <i class="bi bi-file-earmark-pdf me-1"></i> Download PDF Report
                    </a>
                </div>
            </div>

            <!-- Patient Information Grid -->
            <h5 class="text-dark fw-bold mb-3"><i class="bi bi-person-vcard text-primary me-2"></i> 1. Beneficiary Demographics</h5>
            <div class="row g-3 bg-light p-3 rounded border mb-4">
                <div class="col-md-3">
                    <small class="text-muted d-block">PATIENT FULL NAME</small>
                    <strong class="fs-6">${p.full_name}</strong>
                </div>
                <div class="col-md-3">
                    <small class="text-muted d-block">PERMANENT PATIENT ID</small>
                    <span class="badge bg-primary fs-6">${p.patient_id}</span>
                </div>
                <div class="col-md-3">
                    <small class="text-muted d-block">HEALTHCARE ASSURANCE (HAC)</small>
                    <strong class="text-dark font-monospace">${p.hac_number}</strong>
                </div>
                <div class="col-md-3">
                    <small class="text-muted d-block">PAN NUMBER (MASKED)</small>
                    <code>${p.pan_number}</code>
                </div>
                <div class="col-md-3">
                    <small class="text-muted d-block">DATE OF BIRTH / GENDER</small>
                    <span>${p.dob} (${p.gender})</span>
                </div>
                <div class="col-md-3">
                    <small class="text-muted d-block">MOBILE NUMBER</small>
                    <span>${p.mobile}</span>
                </div>
                <div class="col-md-3">
                    <small class="text-muted d-block">BLOOD GROUP</small>
                    <span class="badge bg-danger">${p.blood_group}</span>
                </div>
                <div class="col-md-3">
                    <small class="text-muted d-block">GOVERNMENT SCHEME</small>
                    <span class="badge bg-success">${p.government_scheme_id || 'PM-JAY Eligible'}</span>
                </div>
            </div>

            <!-- Financial Distribution Summary -->
            <h5 class="text-dark fw-bold mb-3"><i class="bi bi-cash-stack text-success me-2"></i> 2. Centralized Fund Distribution Breakdown</h5>
            <div class="row g-4 mb-4">
                <div class="col-lg-7">
                    <div class="table-responsive">
                        <table class="table table-bordered table-custom">
                            <thead>
                                <tr>
                                    <th>Fund Distribution Component</th>
                                    <th>Rule %</th>
                                    <th>Settled Amount (INR)</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr class="table-light fw-bold">
                                    <td>Total Approved Healthcare Fund</td>
                                    <td>100.00%</td>
                                    <td class="text-primary">${API.UI.formatCurrency(fin.total_funding)}</td>
                                </tr>
                                <tr>
                                    <td>Doctor Consultation Payout</td>
                                    <td>10.00%</td>
                                    <td>${API.UI.formatCurrency(fin.doctor_payment)}</td>
                                </tr>
                                <tr>
                                    <td>Pathology Diagnostics Payout</td>
                                    <td>10.00%</td>
                                    <td>${API.UI.formatCurrency(fin.pathology_payment)}</td>
                                </tr>
                                <tr>
                                    <td>Medical & Pharmacy Payout</td>
                                    <td>5.00%</td>
                                    <td>${API.UI.formatCurrency(fin.pharmacy_payment)}</td>
                                </tr>
                                <tr>
                                    <td>Government Administrative Allocation</td>
                                    <td>5.00%</td>
                                    <td>${API.UI.formatCurrency(fin.government_allocation)}</td>
                                </tr>
                                <tr class="table-success fw-bold">
                                    <td>Patient Benefit Wallet Credited</td>
                                    <td>70.00%</td>
                                    <td class="text-success">${API.UI.formatCurrency(fin.patient_benefit)}</td>
                                </tr>
                                <tr>
                                    <td>Total Incurred Treatment Cost</td>
                                    <td>-</td>
                                    <td>${API.UI.formatCurrency(fin.total_treatment_cost)}</td>
                                </tr>
                                <tr>
                                    <td>Patient Out-of-pocket / Deficit</td>
                                    <td>-</td>
                                    <td>${API.UI.formatCurrency(fin.remaining_amount)}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <div class="col-lg-5">
                    <div class="card p-3 border text-center h-100 d-flex flex-column justify-content-center bg-light">
                        <h6 class="fw-bold mb-3 text-muted">Fund Distribution Ratio</h6>
                        <div style="height: 220px; position: relative;">
                            <canvas id="fundDistributionCanvas"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Clinical Consultations Section -->
            <h5 class="text-dark fw-bold mb-3"><i class="bi bi-hospital text-info me-2"></i> 3. Clinical Consultations & Prescriptions</h5>
            <div class="table-responsive mb-4">
                <table class="table table-sm table-bordered">
                    <thead class="table-light">
                        <tr>
                            <th>Consultation ID</th>
                            <th>Visit Date</th>
                            <th>Consulting Doctor</th>
                            <th>Diagnosis & Symptoms</th>
                            <th>Prescribed Medication</th>
                            <th>Fee</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.treatment_details && data.treatment_details.length > 0 ? data.treatment_details.map(c => `
                            <tr>
                                <td><strong>${c.consultation_id}</strong></td>
                                <td>${c.visit_date}</td>
                                <td>${c.doctor_name}</td>
                                <td><strong>${c.diagnosis}</strong><br><small class="text-muted">${c.symptoms}</small></td>
                                <td><small>${c.prescriptions && c.prescriptions.length > 0 ? c.prescriptions[0].medicines.replace(/\n/g, '<br>') : 'Clinical observation'}</small></td>
                                <td>${API.UI.formatCurrency(c.consultation_fee)}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="6" class="text-center text-muted">No consultations on file.</td></tr>'}
                    </tbody>
                </table>
            </div>

            <!-- Diagnostic Pathology Section -->
            <h5 class="text-dark fw-bold mb-3"><i class="bi bi-droplet-half text-danger me-2"></i> 4. Diagnostic Pathology Investigations</h5>
            <div class="table-responsive mb-4">
                <table class="table table-sm table-bordered">
                    <thead class="table-light">
                        <tr>
                            <th>Report ID</th>
                            <th>Date</th>
                            <th>Diagnostic Test</th>
                            <th>Accredited Lab</th>
                            <th>Clinical Findings Summary</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.pathology_details && data.pathology_details.length > 0 ? data.pathology_details.map(r => `
                            <tr>
                                <td><strong>${r.report_id}</strong></td>
                                <td>${r.test_date}</td>
                                <td>${r.test_name}</td>
                                <td>${r.lab_name}</td>
                                <td><small>${r.results_summary}</small></td>
                                <td><span class="badge bg-success">${r.status}</span></td>
                            </tr>
                        `).join('') : '<tr><td colspan="6" class="text-center text-muted">No pathology reports on file.</td></tr>'}
                    </tbody>
                </table>
            </div>

            <!-- Pharmacy Dispensations Section -->
            <h5 class="text-dark fw-bold mb-3"><i class="bi bi-capsule-pill text-warning me-2"></i> 5. Pharmacy Dispensations & Invoicing</h5>
            <div class="table-responsive">
                <table class="table table-sm table-bordered">
                    <thead class="table-light">
                        <tr>
                            <th>Invoice Number</th>
                            <th>Dispensed Date</th>
                            <th>Pharmacy</th>
                            <th>Medications Dispensed</th>
                            <th>GST Amount</th>
                            <th>Total Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.pharmacy_details && data.pharmacy_details.length > 0 ? data.pharmacy_details.map(t => `
                            <tr>
                                <td><strong>${t.invoice_number}</strong></td>
                                <td>${t.dispensed_at?.split('T')[0] || '-'}</td>
                                <td>${t.pharmacy_name}</td>
                                <td><small>${t.medicines_dispensed}</small></td>
                                <td>${API.UI.formatCurrency(t.gst_amount)}</td>
                                <td class="fw-bold">${API.UI.formatCurrency(t.total_amount)}</td>
                            </tr>
                        `).join('') : '<tr><td colspan="6" class="text-center text-muted">No pharmacy orders on file.</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // Render Chart.js Pie Chart
    renderChart(fin);
}

function renderChart(fin) {
    const canvas = document.getElementById('fundDistributionCanvas');
    if (!canvas || !window.Chart) return;

    if (reportChartInstance) {
        reportChartInstance.destroy();
    }

    reportChartInstance = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['Doctor (10%)', 'Pathology (10%)', 'Pharmacy (5%)', 'Government (5%)', 'Patient Benefit (70%)'],
            datasets: [{
                data: [
                    fin.doctor_payment || 10,
                    fin.pathology_payment || 10,
                    fin.pharmacy_payment || 5,
                    fin.government_allocation || 5,
                    fin.patient_benefit || 70
                ],
                backgroundColor: [
                    '#0284c7', // Primary Blue
                    '#0d9488', // Accent Teal
                    '#6366f1', // Secondary Indigo
                    '#f59e0b', // Warning Amber
                    '#10b981'  // Success Green
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 12, font: { size: 10 } }
                }
            }
        }
    });
}
