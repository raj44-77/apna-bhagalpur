// ============================================================
// APNA BHAGALPUR - Shared Data & Utilities
// ============================================================

// ===== DEMO DATA =====
const CLINICS = [
  {
    id: 1,
    name: "City General Hospital",
    address: "Adampur, Bhagalpur, Bihar 812001",
    phone: "0641-2400100",
    timing: "8:00 AM – 8:00 PM",
    type: "Government Hospital",
    emoji: "🏥",
    doctors: [
      { id: 101, name: "Dr. Rajeev Kumar", specialty: "General Physician", slots: 30, fee: 200 },
      { id: 102, name: "Dr. Sunita Devi", specialty: "Gynaecologist", slots: 20, fee: 300 },
      { id: 103, name: "Dr. Amit Singh", specialty: "Paediatrician", slots: 25, fee: 200 },
    ]
  },
  {
    id: 2,
    name: "Sunshine Medical Clinic",
    address: "Maidan Ghat, Bhagalpur, Bihar 812002",
    phone: "0641-2200456",
    timing: "9:00 AM – 7:00 PM",
    type: "Private Clinic",
    emoji: "☀️",
    doctors: [
      { id: 201, name: "Dr. Priya Sharma", specialty: "Dermatologist", slots: 15, fee: 400 },
      { id: 202, name: "Dr. Vivek Gupta", specialty: "ENT Specialist", slots: 20, fee: 350 },
    ]
  },
  {
    id: 3,
    name: "Metro Specialty Hospital",
    address: "Khalifabagh, Bhagalpur, Bihar 812001",
    phone: "0641-2500300",
    timing: "24 Hours",
    type: "Specialty Hospital",
    emoji: "🏨",
    doctors: [
      { id: 301, name: "Dr. Anil Prasad", specialty: "Cardiologist", slots: 20, fee: 600 },
      { id: 302, name: "Dr. Meena Kumari", specialty: "Neurologist", slots: 15, fee: 700 },
      { id: 303, name: "Dr. Ravi Shankar", specialty: "Orthopaedic", slots: 25, fee: 500 },
    ]
  },
  {
    id: 4,
    name: "Family Care Clinic",
    address: "Barari, Bhagalpur, Bihar 812003",
    phone: "0641-2300789",
    timing: "9:00 AM – 6:00 PM",
    type: "Family Clinic",
    emoji: "❤️",
    doctors: [
      { id: 401, name: "Dr. Seema Pandey", specialty: "General Physician", slots: 25, fee: 150 },
      { id: 402, name: "Dr. Mukesh Yadav", specialty: "Diabetologist", slots: 15, fee: 300 },
    ]
  },
  {
    id: 5,
    name: "Bhagalpur Health Centre",
    address: "Tilkamanjhi, Bhagalpur, Bihar 812002",
    phone: "0641-2100567",
    timing: "8:00 AM – 5:00 PM",
    type: "Health Centre",
    emoji: "💊",
    doctors: [
      { id: 501, name: "Dr. Kavita Singh", specialty: "General Physician", slots: 30, fee: 100 },
      { id: 502, name: "Dr. Deepak Kumar", specialty: "Paediatrician", slots: 20, fee: 150 },
    ]
  }
];

const TIME_SLOTS = [
  "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
  "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM",
  "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM",
  "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM"
];

// ===== LOCAL STORAGE HELPERS =====
const Storage = {
  get(key, def = null) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : def; } catch { return def; }
  },
  set(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch {} },
  getAppointments() { return this.get('ab_appointments', []); },
  saveAppointments(data) { this.set('ab_appointments', data); },
  getQueues() { return this.get('ab_queues', {}); },
  saveQueues(data) { this.set('ab_queues', data); },
  getQueue(clinicId) { const q = this.getQueues(); return q[clinicId] || { current: 1, list: [] }; },
  saveQueue(clinicId, queue) { const q = this.getQueues(); q[clinicId] = queue; this.saveQueues(q); },
};

// Seed demo data if empty
function seedDemoData() {
  if (Storage.get('ab_seeded')) return;
  const now = new Date();
  const today = now.toISOString().split('T')[0];

  const appointments = [
    { id: 'BKG001', clinicId: 1, clinicName: 'City General Hospital', doctorId: 101, doctorName: 'Dr. Rajeev Kumar', patientName: 'Ramesh Paswan', phone: '9876543210', date: today, slot: '09:00 AM', slotNum: 1, status: 'completed', type: 'online', bookedAt: new Date(now - 3600000*3).toISOString() },
    { id: 'BKG002', clinicId: 1, clinicName: 'City General Hospital', doctorId: 101, doctorName: 'Dr. Rajeev Kumar', patientName: 'Sita Devi', phone: '9876543211', date: today, slot: '09:30 AM', slotNum: 2, status: 'completed', type: 'online', bookedAt: new Date(now - 3600000*3).toISOString() },
    { id: 'BKG003', clinicId: 1, clinicName: 'City General Hospital', doctorId: 101, doctorName: 'Dr. Rajeev Kumar', patientName: 'Mohan Kumar', phone: '9876543212', date: today, slot: '10:00 AM', slotNum: 3, status: 'absent', type: 'online', bookedAt: new Date(now - 3600000*2).toISOString() },
    { id: 'BKG004', clinicId: 1, clinicName: 'City General Hospital', doctorId: 101, doctorName: 'Dr. Rajeev Kumar', patientName: 'Priya Rani', phone: '9876543213', date: today, slot: '10:30 AM', slotNum: 4, status: 'current', type: 'online', bookedAt: new Date(now - 3600000*2).toISOString() },
    { id: 'BKG005', clinicId: 1, clinicName: 'City General Hospital', doctorId: 101, doctorName: 'Dr. Rajeev Kumar', patientName: 'Ajay Sharma', phone: '9876543214', date: today, slot: '11:00 AM', slotNum: 5, status: 'waiting', type: 'online', bookedAt: new Date(now - 3600000*1).toISOString() },
    { id: 'BKG006', clinicId: 1, clinicName: 'City General Hospital', doctorId: 101, doctorName: 'Dr. Rajeev Kumar', patientName: 'Geeta Kumari', phone: '9876543215', date: today, slot: '11:30 AM', slotNum: 6, status: 'waiting', type: 'online', bookedAt: new Date(now - 3600000*1).toISOString() },
    { id: 'BKG007', clinicId: 1, clinicName: 'City General Hospital', doctorId: 101, doctorName: 'Dr. Rajeev Kumar', patientName: 'Walk-in Patient', phone: '', date: today, slot: '11:30 AM', slotNum: 7, status: 'waiting', type: 'walkin', bookedAt: new Date().toISOString() },
    { id: 'BKG008', clinicId: 2, clinicName: 'Sunshine Medical Clinic', doctorId: 201, doctorName: 'Dr. Priya Sharma', patientName: 'Neha Singh', phone: '9876543216', date: today, slot: '10:00 AM', slotNum: 1, status: 'completed', type: 'online', bookedAt: new Date(now - 3600000*2).toISOString() },
    { id: 'BKG009', clinicId: 2, clinicName: 'Sunshine Medical Clinic', doctorId: 201, doctorName: 'Dr. Priya Sharma', patientName: 'Ritu Devi', phone: '9876543217', date: today, slot: '10:30 AM', slotNum: 2, status: 'current', type: 'online', bookedAt: new Date(now - 3600000*1).toISOString() },
    { id: 'BKG010', clinicId: 2, clinicName: 'Sunshine Medical Clinic', doctorId: 201, doctorName: 'Dr. Priya Sharma', patientName: 'Kavita Pandey', phone: '9876543218', date: today, slot: '11:00 AM', slotNum: 3, status: 'waiting', type: 'online', bookedAt: new Date().toISOString() },
  ];

  const queues = {
    1: { current: 4, list: appointments.filter(a => a.clinicId === 1) },
    2: { current: 2, list: appointments.filter(a => a.clinicId === 2) },
    3: { current: 1, list: [] },
    4: { current: 1, list: [] },
    5: { current: 1, list: [] },
  };

  Storage.saveAppointments(appointments);
  Storage.saveQueues(queues);
  Storage.set('ab_seeded', true);
}

// ===== TOAST SYSTEM =====
function showToast(title, message = '', type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${message ? `<div class="toast-message">${message}</div>` : ''}
    </div>
    <button class="toast-close" onclick="this.closest('.toast').remove()">×</button>
  `;
  container.appendChild(toast);
  setTimeout(() => { toast.style.animation = 'fadeOut 0.3s ease forwards'; setTimeout(() => toast.remove(), 300); }, duration);
}

// ===== MODAL =====
function showModal(id) { document.getElementById(id)?.classList.remove('hidden'); }
function hideModal(id) { document.getElementById(id)?.classList.add('hidden'); }

// ===== NAVBAR =====
function initNavbar() {
  const hamburger = document.querySelector('.hamburger');
  const navLinks = document.querySelector('.nav-links');
  hamburger?.addEventListener('click', () => navLinks?.classList.toggle('open'));
  // Set active link
  const current = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.nav-links a').forEach(a => {
    if (a.getAttribute('href') === current) a.classList.add('active');
  });
}

// ===== HELPERS =====
function generateId(prefix = 'BKG') {
  const apps = Storage.getAppointments();
  return prefix + String(apps.length + Date.now()).slice(-6);
}

function formatDate(d) {
  const date = new Date(d);
  return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function getClinicById(id) { return CLINICS.find(c => c.id === parseInt(id)); }
function getDoctorById(clinicId, docId) {
  const clinic = getClinicById(clinicId);
  return clinic?.doctors.find(d => d.id === parseInt(docId));
}

function getStatusBadge(status) {
  const map = {
    waiting: `<span class="badge badge-primary">⏳ Waiting</span>`,
    current: `<span class="badge badge-warning">🔔 Current</span>`,
    completed: `<span class="badge badge-success">✅ Done</span>`,
    absent: `<span class="badge badge-danger">❌ Absent</span>`,
  };
  return map[status] || `<span class="badge badge-gray">${status}</span>`;
}

function getTypeBadge(type) {
  return type === 'walkin'
    ? `<span class="badge badge-warning">🚶 Walk-in</span>`
    : `<span class="badge badge-primary">💻 Online</span>`;
}

// Init on load
document.addEventListener('DOMContentLoaded', () => {
  seedDemoData();
  initNavbar();
});

// ============================================================
// DARK MODE FUNCTIONALITY
// ============================================================

// Check for saved theme preference
function getThemePreference() {
  const savedTheme = localStorage.getItem('ab_theme');
  if (savedTheme) return savedTheme;
  
  // Check system preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  
  return 'light';
}

// Apply theme
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('ab_theme', theme);
  
  // Update toggle button icons
  updateToggleIcons(theme);
}

// Update toggle button icons
function updateToggleIcons(theme) {
  const floatingBtn = document.getElementById('themeToggleFloating');
  if (floatingBtn) {
    floatingBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
  }
  
  const navBtns = document.querySelectorAll('.nav-theme-toggle');
  navBtns.forEach(btn => {
    btn.innerHTML = theme === 'dark' ? '☀️ Light' : '🌙 Dark';
  });
}

// Toggle theme
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(newTheme);
}

// Create floating toggle button
function createFloatingToggle() {
  // Check if already exists
  if (document.getElementById('themeToggleFloating')) return;
  
  const btn = document.createElement('button');
  btn.id = 'themeToggleFloating';
  btn.className = 'theme-toggle';
  btn.setAttribute('aria-label', 'Toggle theme');
  btn.onclick = toggleTheme;
  document.body.appendChild(btn);
}

// Add toggle to navbar
function addNavToggle() {
  const navLinks = document.querySelector('.nav-links');
  if (!navLinks) return;
  
  // Check if already exists
  if (navLinks.querySelector('.nav-theme-toggle')) return;
  
  const li = document.createElement('li');
  const btn = document.createElement('button');
  btn.className = 'nav-theme-toggle';
  btn.onclick = toggleTheme;
  li.appendChild(btn);
  navLinks.appendChild(li);
}

// Listen for system theme changes
function listenForSystemChanges() {
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      // Only change if user hasn't manually set a preference
      if (!localStorage.getItem('ab_theme')) {
        applyTheme(e.matches ? 'dark' : 'light');
      }
    });
  }
}

// Initialize dark mode
function initDarkMode() {
  const theme = getThemePreference();
  applyTheme(theme);
  createFloatingToggle();
  addNavToggle();
  listenForSystemChanges();
}

// Add to existing DOMContentLoaded or call separately
document.addEventListener('DOMContentLoaded', () => {
  initDarkMode();
});

// If DOM is already loaded, init immediately
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  setTimeout(initDarkMode, 1);
}

function getTypeBadge(type) {
    if (type === 'revisit') return '<span class="badge badge-warning">🔄 Revisit</span>';
    if (type === 'walkin') return '<span class="badge badge-warning">🚶 Walk-in</span>';
    return '<span class="badge badge-primary">💻 Online</span>';
}

// ===== GLOBAL BUTTON LOADING =====
document.addEventListener('click', function(e) {
    const btn = e.target.closest('button, .btn');
    if (!btn || btn.disabled || btn.classList.contains('no-loader')) return;
    
    // Skip if it's a logout button, modal close, hamburger, or theme toggle
    if (btn.closest('.hamburger') || btn.closest('.modal-close') || 
        btn.closest('.toast-close') || btn.classList.contains('theme-toggle') ||
        btn.getAttribute('type') === 'submit') return;  // ← Don't block form submit buttons
    
    // Skip if it's inside a form (let the form handle it)
    if (btn.closest('form') && btn.tagName === 'BUTTON') return;
    
    const originalText = btn.textContent;
    btn.classList.add('btn-loading');
    btn.disabled = true;
    btn.textContent = 'Loading...';
    
    // Remove after 5 seconds max (safety)
    setTimeout(() => {
        btn.classList.remove('btn-loading');
        btn.disabled = false;
        btn.textContent = originalText;
    }, 5000);
});