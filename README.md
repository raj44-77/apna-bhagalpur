text
# 🏥 Apna Bhagalpur

**Bhagalpur ka apna doctor appointment system**

A healthcare SaaS platform for clinics in Bhagalpur, Bihar. Patients book appointments online, track queues in real-time, and clinics manage their patient flow digitally.

---

## 🚀 Features

### 👤 For Patients
- 📅 **Online Booking** — Choose clinic, doctor, date & time in 30 seconds
- 📍 **Live Queue Tracking** — Real-time position updates via WebSocket
- 📋 **My Bookings** — View all appointments by phone number
- 🔄 **Free Revisit** — One follow-up visit within 15 days of consultation
- 📥 **Booking Receipt** — Download printable PDF receipt

### 👨‍⚕️ For Clinics
- ⏭️ **Queue Management** — Next slot, mark absent, add walk-in
- ⏪ **Undo Last Action** — Mistake-proof with one-click undo
- 🔍 **Patient Search** — Find patients by name instantly
- ⏱️ **Consultation Timer** — Track time per patient
- 📊 **Analytics** — Daily, hourly & doctor performance reports
- 📢 **WhatsApp Notifications** — Bulk message all waiting patients
- 📥 **PDF Downloads** — Queue list & analytics export

### 👑 For Super Admin
- 📈 **Platform Overview** — All clinics at a glance
- 🏆 **Clinic Rankings** — Performance-based with medals
- 📝 **Audit Logs** — Every action tracked & filterable

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript (Vanilla) |
| Backend | FastAPI (Python 3.9+) |
| Database | MySQL on Railway |
| Hosting | Render |
| Real-time | WebSocket |
| Authentication | JWT + bcrypt + Google OAuth |
| Rate Limiting | slowapi |
| Backups | GitHub Actions (daily at 2 AM) |
| Monitoring | UptimeRobot (every 5 minutes) |

---

## 📁 Project Structure
apna-bhagalpur/
├── backend/
│ ├── app/
│ │ ├── main.py
│ │ ├── config.py
│ │ ├── database.py
│ │ ├── models/
│ │ └── routes/
│ ├── requirements.txt
│ └── backup.py
├── frontend/
│ ├── index.html
│ ├── booking.html
│ ├── tracking.html
│ ├── admin.html
│ ├── admin-analytics.html
│ ├── super-admin.html
│ ├── audit-logs.html
│ ├── my-bookings.html
│ ├── login.html
│ ├── signup.html
│ ├── profile.html
│ ├── about.html
│ ├── privacy.html
│ ├── terms.html
│ ├── top-clinics.html
│ ├── clinic-signup.html
│ ├── forgot-password.html
│ ├── css/style.css
│ ├── js/
│ │ ├── app.js
│ │ ├── api.js
│ │ └── auth.js
│ └── images/
│ └── main-logo.png
├── .github/workflows/backup.yml
├── render.yaml
├── robots.txt
├── sitemap.xml
├── INCIDENT_RESPONSE.md
├── .gitignore
└── README.md

text

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MySQL
- Git

### Backend Setup
```bash
git clone https://github.com/raj44-77/apna-bhagalpur.git
cd apna-bhagalpur/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
Frontend Setup
bash
cd frontend
python -m http.server 5500
Environment Variables
Create backend/.env:

env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=apna_bhagalpur
JWT_SECRET=your_jwt_secret
SWAGGER_KEY=your_swagger_key
SUPER_ADMIN_KEY=your_super_admin_key
🔒 Security
Feature	Implementation
Authentication	JWT (24hr expiry) + bcrypt + Google OAuth
Authorization	3 roles: patient, clinic, super admin
Rate Limiting	All 20+ endpoints protected
IDOR Prevention	Ownership verification on all admin endpoints
Security Headers	HSTS, X-Frame-Options, X-XSS-Protection
Database User	Dedicated with least privilege
Data Privacy	Phone numbers masked as 9876****01
Audit Logging	All admin actions & logins tracked
Backups	Daily automated + manual
HTTPS	Enforced via Render
📊 Performance
3 database indexes

N+1 queries eliminated (172 to 3 queries)

Connection pooling

Load tested: 50 concurrent bookings, 100% success

Average response: under 500ms

🌙 Dark Mode
Auto-detects system preference

Manual toggle via floating button

Persists across sessions

Full coverage across all pages

🚨 Incident Response
See INCIDENT_RESPONSE.md for emergency contacts, recovery commands, and communication templates.

👨‍💻 Developer
Kumar Raj

rajkr2240@gmail.com

Bhagalpur, Bihar, India

Built with ❤️ for Bhagalpur.

text
### 🏥 Apna Bhagalpur

Doctor appointment platform connecting patients, doctors and clinics.

**Tech:** Python · FastAPI · MySQL · SQLAlchemy · WebSockets

🔗 [Live Demo](https://YOUR-LIVE-WEBSITE.com) · [Source Code](https://github.com/raj44-77/apna-bhagalpur)

---

### Then push:
```bash
git add README.md
git commit -m "Final README with proper formatting"
git push
