/**
 * PatientCare Healthcare Platform
 * Main Script (main.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    // Check user authentication and update navbar
    const user = API.Storage.getUser();
    const token = API.Storage.getToken();

    const authLinksContainer = document.getElementById('navAuthLinks');
    if (authLinksContainer) {
        if (token && user) {
            let dashboardUrl = 'pages/patient-dashboard.html';
            if (user.role === 'DOCTOR') dashboardUrl = 'pages/doctor-dashboard.html';
            else if (user.role === 'PATHOLOGY') dashboardUrl = 'pages/pathology-dashboard.html';
            else if (user.role === 'PHARMACY') dashboardUrl = 'pages/pharmacy-dashboard.html';
            else if (user.role === 'GOVERNMENT') dashboardUrl = 'pages/government-dashboard.html';
            else if (user.role === 'ADMIN') dashboardUrl = 'pages/admin-dashboard.html';

            const prefix = window.location.pathname.includes('/pages/') ? '' : 'pages/';
            authLinksContainer.innerHTML = `
                <div class="d-flex align-items-center gap-2">
                    <a href="${prefix}${dashboardUrl.replace('pages/', '')}" class="btn btn-outline-primary btn-sm">
                        <i class="bi bi-speedometer2 me-1"></i> Dashboard (${user.role})
                    </a>
                    <button id="globalLogoutBtn" class="btn btn-outline-secondary btn-sm">
                        <i class="bi bi-box-arrow-right"></i> Logout
                    </button>
                </div>
            `;

            document.getElementById('globalLogoutBtn')?.addEventListener('click', () => {
                API.authAPI.logout();
            });
        }
    }

    // Quick Home Page Patient ID Lookup Handler
    const homeSearchBtn = document.getElementById('homePatientSearchBtn');
    const homeSearchInput = document.getElementById('homePatientSearchInput');
    const homeSearchResult = document.getElementById('homeLookupResult');

    if (homeSearchBtn && homeSearchInput && homeSearchResult) {
        homeSearchBtn.addEventListener('click', async () => {
            const query = homeSearchInput.value.trim();
            if (!query) {
                API.UI.showToast('Please enter a Patient ID, PAN, or Mobile.', 'warning');
                return;
            }

            homeSearchBtn.disabled = true;
            homeSearchBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Searching...';

            try {
                const patient = await API.patientAPI.lookup(query);
                homeSearchResult.innerHTML = `
                    <div class="card border-primary p-3 mt-3 text-start bg-light">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h5 class="mb-0 text-primary"><i class="bi bi-person-check-fill me-1"></i> ${patient.full_name}</h5>
                            <span class="badge bg-success"><i class="bi bi-check-circle me-1"></i> Active Beneficiary</span>
                        </div>
                        <p class="mb-1 text-muted small"><strong>Patient ID:</strong> <span class="badge bg-dark">${patient.patient_id}</span> | <strong>HAC:</strong> ${patient.hac_number}</p>
                        <p class="mb-1 text-muted small"><strong>Masked PAN:</strong> <code>${patient.masked_pan}</code> | <strong>Blood Group:</strong> ${patient.blood_group}</p>
                        <div class="mt-3">
                            <a href="pages/reports.html?id=${patient.patient_id}" class="btn btn-sm btn-primary">
                                <i class="bi bi-file-earmark-medical me-1"></i> View Full Centralized Health & Fund Report →
                            </a>
                        </div>
                    </div>
                `;
            } catch (err) {
                homeSearchResult.innerHTML = `
                    <div class="alert alert-danger mt-3 text-start">
                        <i class="bi bi-exclamation-triangle-fill me-1"></i> ${err.message || 'No patient record found matching the entered ID or PAN.'}
                    </div>
                `;
            } finally {
                homeSearchBtn.disabled = false;
                homeSearchBtn.innerHTML = '<i class="bi bi-search me-1"></i> Search Records';
            }
        });
    }

    // ---------------------------------------------------------
    // 3D Card Interactive Tilt & Parallax Physics
    // ---------------------------------------------------------
    const viewport = document.getElementById('hero3dViewport');
    const card = document.getElementById('heroCard3d');

    if (viewport && card) {
        let bounds = viewport.getBoundingClientRect();

        const updateBounds = () => {
            bounds = viewport.getBoundingClientRect();
        };
        window.addEventListener('resize', updateBounds);
        window.addEventListener('scroll', updateBounds, { passive: true });

        viewport.addEventListener('mousemove', (e) => {
            const mouseX = e.clientX - bounds.left;
            const mouseY = e.clientY - bounds.top;

            const xPct = (mouseX / bounds.width) - 0.5;
            const yPct = (mouseY / bounds.height) - 0.5;

            const rotateY = xPct * 24;  // -12deg to +12deg
            const rotateX = -yPct * 20; // -10deg to +10deg

            card.style.transform = `rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.03, 1.03, 1.03)`;
        });

        viewport.addEventListener('mouseleave', () => {
            card.style.transform = 'rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        });
    }
});

