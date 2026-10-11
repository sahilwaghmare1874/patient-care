/**
 * PatientCare Healthcare Platform
 * Authentication Script (auth.js)
 */

document.addEventListener('DOMContentLoaded', () => {
    // ---------------------------------------------------------
    // 1. LOGIN FORM HANDLER
    // ---------------------------------------------------------
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const username = document.getElementById('loginUsername').value.trim();
            const password = document.getElementById('loginPassword').value;

            if (!username || !password) {
                API.UI.showToast('Please enter your credentials.', 'warning');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Authenticating...';

            try {
                const res = await API.authAPI.login(username, password);
                API.UI.showToast('Authentication successful! Redirecting...', 'success', 'Login Successful');

                setTimeout(() => {
                    const role = res.user.role;
                    if (role === 'PATIENT') window.location.href = 'patient-dashboard.html';
                    else if (role === 'DOCTOR') window.location.href = 'doctor-dashboard.html';
                    else if (role === 'PATHOLOGY') window.location.href = 'pathology-dashboard.html';
                    else if (role === 'PHARMACY') window.location.href = 'pharmacy-dashboard.html';
                    else if (role === 'GOVERNMENT' || role === 'GOVERNMENT_OFFICER') window.location.href = 'government-dashboard.html';
                    else if (role === 'ADMIN' || role === 'FINANCE' || role === 'HOSPITAL_ADMIN' || role === 'INSURANCE_OFFICER') window.location.href = 'admin-dashboard.html';
                    else window.location.href = 'patient-dashboard.html';
                }, 800);
            } catch (err) {
                API.UI.showToast(err.message || 'Login failed. Please check credentials.', 'danger', 'Login Failed');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="bi bi-box-arrow-in-right me-1"></i> Login to Portal';
            }
        });
    }

    // ---------------------------------------------------------
    // 2. PROVIDER REGISTRATION HANDLER
    // ---------------------------------------------------------
    const providerForm = document.getElementById('providerRegisterForm');
    
    function showProviderAlert(message, type = 'danger') {
        const box = document.getElementById('providerRegAlert');
        if (box) {
            box.className = `alert alert-${type} d-block my-3 shadow-sm`;
            const icon = type === 'success' ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
            box.innerHTML = `<i class="bi ${icon} me-2"></i> ${message}`;
            box.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    function clearProviderAlert() {
        const box = document.getElementById('providerRegAlert');
        if (box) {
            box.className = 'alert d-none my-3';
            box.innerHTML = '';
        }
    }

    window.quickFillDemoDoctor = function() {
        clearProviderAlert();
        const randNum = Math.floor(Math.random() * 900) + 100;
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.value = val;
        };

        const roleSelect = document.getElementById('regRole');
        if (roleSelect) {
            roleSelect.value = 'DOCTOR';
            roleSelect.dispatchEvent(new Event('change'));
        }

        setVal('regUsername', `dr_wagh_${randNum}`);
        setVal('regEmail', `dr.wagh.${randNum}@hospital.org`);
        setVal('regMobile', '7894525846');
        setVal('regFullName', 'Dr. Sahil Santosh Wagh');
        setVal('regRegNo', `MCI-${randNum}-MH`);
        setVal('regQualification', 'MBBS, MD (Internal Medicine)');
        setVal('regSpecialization', 'Internal Medicine');
        setVal('regHospital', 'Sahil Healthcare Clinic');
        setVal('regAddress', 'Plot 12, Shivaji Nagar, Pune');
        setVal('regPassword', 'Password@123');
        setVal('regConfirmPassword', 'Password@123');

        showProviderAlert('Demo Doctor credentials loaded! Click "Register Provider Account" below.', 'info');
        if (window.API && window.API.UI) {
            window.API.UI.showToast('Doctor credentials auto-filled.', 'info', 'Quick Fill');
        }
    };

    if (providerForm) {
        // Toggle role fields
        const roleSelect = document.getElementById('regRole');
        const doctorFields = document.getElementById('doctorFields');
        const pathologyFields = document.getElementById('pathologyFields');
        const pharmacyFields = document.getElementById('pharmacyFields');

        function updateRoleFields() {
            const role = roleSelect ? roleSelect.value : 'DOCTOR';
            if (doctorFields) doctorFields.style.display = role === 'DOCTOR' ? 'block' : 'none';
            if (pathologyFields) pathologyFields.style.display = role === 'PATHOLOGY' ? 'block' : 'none';
            if (pharmacyFields) pharmacyFields.style.display = role === 'PHARMACY' ? 'block' : 'none';
        }

        if (roleSelect) {
            roleSelect.addEventListener('change', updateRoleFields);
            updateRoleFields();
        }

        providerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            clearProviderAlert();
            const submitBtn = providerForm.querySelector('button[type="submit"]') || document.getElementById('submitProviderBtn');

            const payload = {
                username: document.getElementById('regUsername').value.trim(),
                email: document.getElementById('regEmail').value.trim(),
                mobile: document.getElementById('regMobile').value.trim(),
                role: document.getElementById('regRole').value,
                password: document.getElementById('regPassword').value,
                confirm_password: document.getElementById('regConfirmPassword').value,
                full_name: document.getElementById('regFullName')?.value || '',
                hospital_name: document.getElementById('regHospital')?.value || '',
                specialization: document.getElementById('regSpecialization')?.value || '',
                registration_number: document.getElementById('regRegNo')?.value || '',
                qualification: document.getElementById('regQualification')?.value || 'MBBS, MD',
                lab_name: document.getElementById('regLabName')?.value || '',
                license_number: document.getElementById('regLicenseNo')?.value || '',
                pharmacy_name: document.getElementById('regPharmacyName')?.value || '',
                pharmacist_name: document.getElementById('regPharmacistName')?.value || '',
                address: document.getElementById('regAddress')?.value || ''
            };

            if (payload.password !== payload.confirm_password) {
                const msg = 'Passwords do not match. Please verify Password and Confirm Password.';
                showProviderAlert(msg, 'danger');
                if (window.API && window.API.UI) API.UI.showToast(msg, 'danger');
                return;
            }

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Registering...';
            }

            try {
                await API.authAPI.register(payload);
                showProviderAlert('Provider registration successful! Redirecting to login...', 'success');
                if (window.API && window.API.UI) {
                    API.UI.showToast('Provider registration successful! You can now login.', 'success', 'Account Registered');
                }
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 1200);
            } catch (err) {
                const errMsg = err.message || 'Registration failed. Please check inputs.';
                showProviderAlert(errMsg, 'danger');
                if (window.API && window.API.UI) {
                    API.UI.showToast(errMsg, 'danger', 'Registration Error');
                }
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="bi bi-person-plus-fill me-1"></i> Register Provider Account';
                }
            }
        });
    }
});
