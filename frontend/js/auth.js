// ============================================================
// APNA BHAGALPUR - Authentication System
// ============================================================

const AuthStore = {
    getCurrentUser() {
        try {
            const user = localStorage.getItem('ab_current_user');
            return user ? JSON.parse(user) : null;
        } catch { return null; }
    },
    setCurrentUser(user) {
        localStorage.setItem('ab_current_user', JSON.stringify(user));
    },
    getToken() {
        return localStorage.getItem('ab_token') || null;
    },
    setToken(token) {
        localStorage.setItem('ab_token', token);
    },
    logout() {
        localStorage.removeItem('ab_current_user');
        localStorage.removeItem('ab_token');
    },
    isLoggedIn() {
        return this.getCurrentUser() !== null;
    }
};

async function loginUser(email, password) {
    try {
        const baseUrl = typeof API_BASE !== 'undefined' ? API_BASE : 'http://localhost:8000/api';
        const res = await fetch(`${baseUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const result = await res.json();
        if (result.access_token) {
            AuthStore.setToken(result.access_token);
            AuthStore.setCurrentUser(result.user);
            return { success: true, message: 'Login successful!', user: result.user };
        }
        return { success: false, message: result.detail || 'Invalid credentials' };
    } catch (error) {
        return { success: false, message: 'Cannot connect to server' };
    }
}

async function registerPatient(name, email, phone, password) {
    try {
        const baseUrl = typeof API_BASE !== 'undefined' ? API_BASE : 'http://localhost:8000/api';
        const res = await fetch(`${baseUrl}/auth/register/patient`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, phone, password })
        });
        const result = await res.json();
        if (result.id) return { success: true, message: 'Registration successful!' };
        return { success: false, message: result.detail || 'Registration failed' };
    } catch (error) {
        return { success: false, message: 'Cannot connect to server' };
    }
}

async function registerClinic(name, email, phone, password, clinicId) {
    try {
        const baseUrl = typeof API_BASE !== 'undefined' ? API_BASE : 'http://localhost:8000/api';
        const res = await fetch(`${baseUrl}/auth/register/clinic`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, phone, password, clinic_id: clinicId })
        });
        const result = await res.json();
        if (result.id) return { success: true, message: 'Clinic registered!' };
        return { success: false, message: result.detail || 'Registration failed' };
    } catch (error) {
        return { success: false, message: 'Cannot connect to server' };
    }
}

function logoutUser() {
    AuthStore.logout();
    window.location.href = 'login.html';
}

function checkAuth() {
    const user = AuthStore.getCurrentUser();
    const page = window.location.pathname.split('/').pop();
    
    const publicPages = ['index.html', 'login.html', 'signup.html', 'clinic-signup.html', 'forgot-password.html', ''];
    if (publicPages.includes(page)) return true;
    
    if (!user) {
        window.location.href = 'login.html';
        return false;
    }
    
    if (page === 'admin.html' && user.user_type !== 'clinic' && user.user_type !== 'admin') {
        alert('Only clinic admins can access this page');
        window.location.href = 'login.html';
        return false;
    }
    
    if (page === 'super-admin.html' && user.user_type !== 'admin') {
        alert('Access denied. Super admin only.');
        window.location.href = 'login.html';
        return false;
    }
    
    return true;
}

function updateAuthUI() {
    const user = AuthStore.getCurrentUser();
    const navLinks = document.querySelector('.nav-links');
    if (!navLinks) return;

    const bookingLink = navLinks.querySelector('a[href="booking.html"]');
    const trackingLink = navLinks.querySelector('a[href="tracking.html"]');
    const myBookingsLink = navLinks.querySelector('a[href="my-bookings.html"]');
    const adminLink = navLinks.querySelector('a[href="admin.html"]');

    if (user && user.user_type === 'admin') {
        if (bookingLink) bookingLink.style.display = 'none';
        if (trackingLink) trackingLink.style.display = 'none';
        if (myBookingsLink) myBookingsLink.style.display = 'none';
        if (adminLink) adminLink.style.display = '';
    } else if (user && user.user_type === 'clinic') {
        if (bookingLink) bookingLink.style.display = '';
        if (trackingLink) trackingLink.style.display = 'none';
        if (myBookingsLink) myBookingsLink.style.display = 'none';
        if (adminLink) adminLink.style.display = '';
    } else if (user && user.user_type === 'patient') {
        if (bookingLink) bookingLink.style.display = '';
        if (trackingLink) trackingLink.style.display = '';
        if (myBookingsLink) myBookingsLink.style.display = '';
        if (adminLink) adminLink.style.display = 'none';
    } else {
        if (bookingLink) bookingLink.style.display = '';
        if (trackingLink) trackingLink.style.display = '';
        if (myBookingsLink) myBookingsLink.style.display = '';
        if (adminLink) adminLink.style.display = '';
    }

    // Remove existing auth area
    const existingAuth = navLinks.querySelector('.auth-area');
    if (existingAuth) existingAuth.remove();

    // Create auth area
    const authArea = document.createElement('div');
    authArea.className = 'auth-area';
    authArea.style.cssText = 'display:flex;align-items:center;gap:8px;margin-left:8px;';

    if (user) {
        const typeLabel = user.user_type === 'admin' ? '👑' : (user.user_type === 'clinic' ? '🏥' : '👤');
        authArea.innerHTML = '<span style="font-size:0.85rem;">' + typeLabel + ' ' + user.name.split(' ')[0] + '</span>' +
            '<a href="profile.html" class="btn btn-sm btn-outline">👤 Profile</a>' +
            '<button onclick="logoutUser()" class="btn btn-sm btn-outline" style="color:var(--danger);">🚪 Logout</button>';
    } else {
        authArea.innerHTML = '<a href="login.html" class="btn btn-sm btn-outline">🔑 Login</a>' +
            '<a href="signup.html" class="btn btn-sm btn-primary">📝 Sign Up</a>';
    }

    navLinks.appendChild(authArea);
}

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    updateAuthUI();
});