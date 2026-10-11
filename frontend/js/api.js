/**
 * PatientCare Healthcare Platform
 * Centralized API & State Management Layer (api.js)
 */

const API_BASE_URL = '/api';

const Storage = {
    TOKEN_KEY: 'healthcare_access_token',
    REFRESH_KEY: 'healthcare_refresh_token',
    USER_KEY: 'healthcare_user',

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },
    setToken(access, refresh) {
        if (access) localStorage.setItem(this.TOKEN_KEY, access);
        if (refresh) localStorage.setItem(this.REFRESH_KEY, refresh);
    },
    clearToken() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_KEY);
        localStorage.removeItem(this.USER_KEY);
    },
    getUser() {
        try {
            return JSON.parse(localStorage.getItem(this.USER_KEY));
        } catch {
            return null;
        }
    },
    setUser(user) {
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    }
};

async function apiFetch(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    const headers = options.headers || {};

    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const token = Storage.getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 401) {
            // Unauthorized - clear token if invalid
            // Storage.clearToken();
        }

        const contentType = response.headers.get('content-type');
        let data = null;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            let errorMsg = 'An error occurred with your request.';
            if (typeof data === 'object' && data !== null) {
                if (data.error) errorMsg = data.error;
                else if (data.message) errorMsg = data.message;
                else if (data.detail) errorMsg = data.detail;
                else if (data.non_field_errors) errorMsg = data.non_field_errors.join(' ');
                else {
                    const firstKey = Object.keys(data)[0];
                    errorMsg = Array.isArray(data[firstKey]) ? `${firstKey}: ${data[firstKey][0]}` : `${firstKey}: ${data[firstKey]}`;
                }
            }
            throw new Error(errorMsg);
        }

        return data;
    } catch (err) {
        console.error(`API Error [${endpoint}]:`, err);
        throw err;
    }
}

/**
 * Normalizes DRF paginated responses ({ count, results: [...] }) or flat arrays
 * into a standard JavaScript array.
 */
function unwrapList(data) {
    if (data && typeof data === 'object' && Array.isArray(data.results)) {
        return data.results;
    }
    return Array.isArray(data) ? data : [];
}

// -------------------------------------------------------------
// Centralized API Service Modules
// -------------------------------------------------------------

const authAPI = {
    async register(data) {
        return apiFetch('/auth/register/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async login(username, password) {
        const res = await apiFetch('/auth/login/', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        if (res.access) {
            Storage.setToken(res.access, res.refresh);
            Storage.setUser(res.user);
        }
        return res;
    },
    async sendOTP(identifier, purpose = 'REGISTRATION') {
        return apiFetch('/auth/send-otp/', {
            method: 'POST',
            body: JSON.stringify({ identifier, purpose })
        });
    },
    async verifyOTP(identifier, otp) {
        return apiFetch('/auth/verify-otp/', {
            method: 'POST',
            body: JSON.stringify({ identifier, otp })
        });
    },
    async getCurrentUser() {
        return apiFetch('/auth/me/');
    },
    logout() {
        Storage.clearToken();
        window.location.href = window.location.pathname.includes('/pages/') ? 'login.html' : 'pages/login.html';
    }
};

const patientAPI = {
    async list(search = '') {
        return apiFetch(`/patients/${search ? `?search=${encodeURIComponent(search)}` : ''}`);
    },
    async create(data) {
        return apiFetch('/patients/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async get(id) {
        return apiFetch(`/patients/${id}/`);
    },
    async lookup(query) {
        return apiFetch(`/patients/lookup/?query=${encodeURIComponent(query)}`);
    },
    async getCentralizedRecord(id) {
        return apiFetch(`/patients/${id}/centralized-record/`);
    }
};

const doctorAPI = {
    async getStats() {
        return apiFetch('/doctors/stats/');
    },
    async listConsultations(patientId = '') {
        return unwrapList(await apiFetch(`/doctors/consultations/${patientId ? `?patient_id=${patientId}` : ''}`));
    },
    async createConsultation(data) {
        return apiFetch('/doctors/consultations/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async listPrescriptions(patientId = '') {
        return unwrapList(await apiFetch(`/doctors/prescriptions/${patientId ? `?patient_id=${patientId}` : ''}`));
    },
    // Phase 3: Doctor listing with availability & fees
    async listDoctors(specialization = '') {
        return unwrapList(await apiFetch(`/doctors/list/${specialization ? `?specialization=${encodeURIComponent(specialization)}` : ''}`));
    },
    // Phase 3: Appointment booking
    async listAppointments(params = {}) {
        const qs = Object.entries(params).map(([k,v]) => `${k}=${encodeURIComponent(v)}`).join('&');
        return unwrapList(await apiFetch(`/doctors/appointments/${qs ? `?${qs}` : ''}`));
    },
    async bookAppointment(data) {
        return apiFetch('/doctors/appointments/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async updateAppointment(appointmentId, data) {
        return apiFetch(`/doctors/appointments/${appointmentId}/`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    // Phase 4: Token queue
    async getTokenQueue(doctorId, date = '') {
        return apiFetch(`/doctors/queue/?doctor_id=${encodeURIComponent(doctorId)}${date ? `&date=${date}` : ''}`);
    },
    async callNextToken(data) {
        return apiFetch('/doctors/queue/call-next/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async getAppointmentToken(appointmentId) {
        return apiFetch(`/doctors/token/${appointmentId}/`);
    },
    // Phase 7: AI symptom recommendation
    async getAIRecommendation(symptoms, language = 'en') {
        return apiFetch('/doctors/ai/recommend/', {
            method: 'POST',
            body: JSON.stringify({ symptoms, language })
        });
    }
};

const pathologyAPI = {
    async getStats() {
        return apiFetch('/pathology/stats/');
    },
    async listTests() {
        return unwrapList(await apiFetch('/pathology/tests/'));
    },
    async listReports(patientId = '') {
        return unwrapList(await apiFetch(`/pathology/reports/${patientId ? `?patient_id=${patientId}` : ''}`));
    },
    async createReport(data) {
        return apiFetch('/pathology/reports/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};

const pharmacyAPI = {
    async getStats() {
        return apiFetch('/pharmacy/stats/');
    },
    async listMedicines() {
        return unwrapList(await apiFetch('/pharmacy/medicines/'));
    },
    async listTransactions(patientId = '') {
        return unwrapList(await apiFetch(`/pharmacy/transactions/${patientId ? `?patient_id=${patientId}` : ''}`));
    },
    async createTransaction(data) {
        return apiFetch('/pharmacy/transactions/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};

const governmentAPI = {
    async getStats() {
        return apiFetch('/government/stats/');
    },
    async listSchemes() {
        return unwrapList(await apiFetch('/government/schemes/'));
    },
    async createScheme(data) {
        return apiFetch('/government/schemes/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async updateScheme(id, data) {
        return apiFetch(`/government/schemes/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
};

const insuranceAPI = {
    async listCompanies() {
        return apiFetch('/insurance/companies/');
    },
    async listClaims(patientId = '') {
        return unwrapList(await apiFetch(`/insurance/claims/${patientId ? `?patient_id=${patientId}` : ''}`));
    },
    async submitClaim(data) {
        return apiFetch('/insurance/claims/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async updateClaim(claimId, data) {
        return apiFetch(`/insurance/claims/${claimId}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
};

const fundsAPI = {
    async getConfiguration() {
        return apiFetch('/funds/config/');
    },
    async updateConfiguration(data) {
        return apiFetch('/funds/config/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async listAllocations(patientId = '') {
        return unwrapList(await apiFetch(`/funds/allocations/${patientId ? `?patient_id=${patientId}` : ''}`));
    },
    async allocateFund(data) {
        return apiFetch('/funds/allocations/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    // Phase 8: Reserve Account
    async getReserveAccount(patientId) {
        return apiFetch(`/funds/reserve/${patientId}/`);
    },
    async getReserveLedger(patientId) {
        return apiFetch(`/funds/reserve/${patientId}/ledger/`);
    },
    async creditReserve(data) {
        return apiFetch('/funds/reserve/credit/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // Phase 9: Health Protection Fund (10% automatic contribution)
    async getProtectionAccount(patientId) {
        return apiFetch(`/funds/protection-account/${patientId}/`);
    },
    async getProtectionTransactions(patientId) {
        return unwrapList(await apiFetch(`/funds/protection-transactions/${patientId}/`));
    },
    async getProtectionRules() {
        return apiFetch('/funds/protection-rules/');
    },
    async listProtectionClaims(patientId) {
        return unwrapList(await apiFetch(`/funds/claims/?patient_id=${encodeURIComponent(patientId)}`));
    },
    async submitProtectionClaim(data) {
        return apiFetch('/funds/claims/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async reviewProtectionClaim(claimReference, data) {
        return apiFetch(`/funds/claims/${claimReference}/review/`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};

// Phase 6: Government scheme applications
const governmentApplicationAPI = {
    async list(patientId = '') {
        return unwrapList(await apiFetch(`/government/applications/${patientId ? `?patient_id=${patientId}` : ''}`));
    },
    async submit(data) {
        return apiFetch('/government/applications/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async update(applicationId, data) {
        return apiFetch(`/government/applications/${applicationId}/`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};


const paymentAPI = {
    async list(patientId = '') {
        return apiFetch(`/payments/${patientId ? `?patient_id=${patientId}` : ''}`);
    },
    async create(data) {
        return apiFetch('/payments/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    async getReceipt(transactionId) {
        return apiFetch(`/payments/receipt/${transactionId}/`);
    }
};

const doctorRecommendationAPI = {
    async getRecommendations(data) {
        return apiFetch('/doctors/recommendations/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};

const reportAPI = {
    async getPatientReport(patientId) {
        return apiFetch(`/reports/patient/${patientId}/`);
    },
    async getFundReport(patientId) {
        return apiFetch(`/reports/fund/${patientId}/`);
    },
    getPDFUrl(patientId) {
        return `${API_BASE_URL}/reports/pdf/${patientId}/`;
    },
    getCSVUrl(patientId) {
        return `${API_BASE_URL}/reports/csv/${patientId}/`;
    },
    // Phase 7: AI Multilingual Assistant & Medical Report Explanation
    async aiChat(message, language = 'en', patientId = '') {
        return apiFetch('/reports/ai/chat/', {
            method: 'POST',
            body: JSON.stringify({ message, language, patient_id: patientId })
        });
    },
    async aiExplain(text, type = 'prescription', language = 'en') {
        return apiFetch('/reports/ai/explain/', {
            method: 'POST',
            body: JSON.stringify({ text, type, language })
        });
    },
    async aiAuditClaims(patientId = '') {
        return apiFetch(`/reports/ai/audit-claims/${patientId ? `?patient_id=${patientId}` : ''}`);
    },
    // Phase 11: Centralized Financial Reporting Overview
    async getFinancialOverview(params = {}) {
        const qs = Object.entries(params).map(([k,v]) => `${k}=${encodeURIComponent(v)}`).join('&');
        return apiFetch(`/reports/financial-overview/${qs ? `?${qs}` : ''}`);
    }
};

const notificationAPI = {
    async list(userId = '') {
        return apiFetch(`/notifications/${userId ? `?user_id=${userId}` : ''}`);
    },
    async markRead(id) {
        return apiFetch(`/notifications/${id}/read/`, { method: 'POST' });
    }
};

// -------------------------------------------------------------
// UI Utilities: Notifications & Alerts
// -------------------------------------------------------------

const UI = {
    showToast(message, type = 'success', title = '') {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const bgClass = type === 'success' ? 'bg-success text-white' :
                        type === 'danger' || type === 'error' ? 'bg-danger text-white' :
                        type === 'warning' ? 'bg-warning text-dark' : 'bg-primary text-white';

        const toastId = 'toast_' + Date.now();
        const toastEl = document.createElement('div');
        toastEl.id = toastId;
        toastEl.className = `toast align-items-center ${bgClass} border-0 shadow-lg`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');

        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${title ? `<strong>${title}</strong><br>` : ''}
                    ${message}
                </div>
                <button type="button" class="btn-close ${type !== 'warning' ? 'btn-close-white' : ''} me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        container.appendChild(toastEl);
        if (window.bootstrap && window.bootstrap.Toast) {
            const toast = new bootstrap.Toast(toastEl, { delay: 4500 });
            toast.show();
            toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
        } else {
            setTimeout(() => toastEl.remove(), 4500);
        }
    },

    formatCurrency(amount) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 2
        }).format(amount || 0);
    },

    maskPan(pan) {
        if (!pan || pan.length !== 10) return pan || 'XXXXXXXXXX';
        return `XXXXX${pan.slice(5, 9)}X`;
    }
};

window.API = {
    API_BASE_URL,
    Storage,
    authAPI,
    patientAPI,
    doctorAPI,
    pathologyAPI,
    pharmacyAPI,
    governmentAPI,
    governmentApplicationAPI,
    insuranceAPI,
    fundsAPI,
    paymentAPI,
    doctorRecommendationAPI,
    reportAPI,
    notificationAPI,
    UI
};
