// ============================================================
// APNA BHAGALPUR - API Service
// ============================================================

const API_BASE = 'https://apna-bhagalpur.onrender.com/api';

const API = {
    async login(email, password) {
        const res = await fetch(`${API_BASE}/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) });
        return res.json();
    },
    async registerPatient(data) {
        const res = await fetch(`${API_BASE}/auth/register/patient`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        return res.json();
    },
    async registerClinic(data) {
        const res = await fetch(`${API_BASE}/auth/register/clinic`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        return res.json();
    },
    async getClinics() {
        const res = await fetch(`${API_BASE}/clinics/`);
        return res.json();
    },
    async getClinic(id) {
        const res = await fetch(`${API_BASE}/clinics/${id}`);
        return res.json();
    },
    async getDoctors(clinicId) {
        const res = await fetch(`${API_BASE}/clinics/${clinicId}/doctors`);
        return res.json();
    },
    async bookAppointment(data) {
        const res = await fetch(`${API_BASE}/appointments/book`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        return res.json();
    },
    async trackQueue(clinicId, slotNumber, appointmentDate = null) {
        let url = `${API_BASE}/appointments/track/${clinicId}?slot_number=${slotNumber}`;
        if (appointmentDate) url += `&appointment_date=${appointmentDate}`;
        const res = await fetch(url);
        return res.json();
    },
    async getMyBookings(phone) {
        const res = await fetch(`${API_BASE}/appointments/my-bookings?phone=${phone}`);
        return res.json();
    },
    async getDashboard(clinicId, appointmentDate = null) {
        let url = `${API_BASE}/admin/dashboard/${clinicId}`;
        if (appointmentDate) url += `?appointment_date=${appointmentDate}`;
        const res = await fetch(url);
        return res.json();
    },
    async nextSlot(clinicId, appointmentDate = null) {
        let url = `${API_BASE}/admin/next-slot/${clinicId}`;
        if (appointmentDate) url += `?appointment_date=${appointmentDate}`;
        const res = await fetch(url, { method: 'POST' });
        return res.json();
    },
    async markAbsent(clinicId, appointmentDate = null) {
        let url = `${API_BASE}/admin/mark-absent/${clinicId}`;
        if (appointmentDate) url += `?appointment_date=${appointmentDate}`;
        const res = await fetch(url, { method: 'POST' });
        return res.json();
    },
    async addWalkin(clinicId, data, appointmentDate = null) {
        let url = `${API_BASE}/admin/add-walkin/${clinicId}?doctor_id=${data.doctor_id}&patient_name=${encodeURIComponent(data.patient_name)}&patient_phone=${encodeURIComponent(data.patient_phone || '')}`;
        if (appointmentDate) url += `&appointment_date=${appointmentDate}`;
        const res = await fetch(url, { method: 'POST' });
        return res.json();
    },
    async lockQueue(clinicId, appointmentDate = null) {
        let url = `${API_BASE}/admin/lock/${clinicId}`;
        if (appointmentDate) url += `?appointment_date=${appointmentDate}`;
        const res = await fetch(url, { method: 'POST' });
        return res.json();
    },
    async unlockQueue(clinicId, appointmentDate = null) {
        let url = `${API_BASE}/admin/unlock/${clinicId}`;
        if (appointmentDate) url += `?appointment_date=${appointmentDate}`;
        const res = await fetch(url, { method: 'POST' });
        return res.json();
    },
    async isQueueLocked(clinicId, appointmentDate = null) {
        let url = `${API_BASE}/admin/is-locked/${clinicId}`;
        if (appointmentDate) url += `?appointment_date=${appointmentDate}`;
        const res = await fetch(url);
        return res.json();
    },
    async getQueueStatus(clinicId) {
        const res = await fetch(`${API_BASE}/queue/status/${clinicId}`);
        return res.json();
    },
    async togglePause(clinicId) {
        const res = await fetch(`${API_BASE}/queue/pause/${clinicId}`, { method: 'POST' });
        return res.json();
    },
    async getAbsentees(clinicId, appointmentDate = null) {
        let url = `${API_BASE}/admin/absentees/${clinicId}`;
        if (appointmentDate) url += `?appointment_date=${appointmentDate}`;
        const res = await fetch(url);
        return res.json();
    },
    async startTreatment(appointmentId) {
        const res = await fetch(`${API_BASE}/admin/start-treatment/${appointmentId}`, { method: 'POST' });
        return res.json();
    },
    async rescheduleAppointment(appointmentId, newDate) {
        const res = await fetch(`${API_BASE}/admin/reschedule/${appointmentId}?new_date=${newDate}`, { method: 'POST' });
        return res.json();
    }
};