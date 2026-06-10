# Mental-Health-Support-System
# 🧠 Community Mental Health Alert & Support System

**Course:** UCS310 — Database Management Systems
**Institute:** Thapar Institute of Engineering & Technology

A web-based mental health support platform built with Flask and MySQL. It allows users to submit mental health alerts, counselors to manage and resolve cases, and admins to oversee the entire system.

---

## 📋 Tech Stack

- **Backend:** Python (Flask)
- **Database:** MySQL 8.4
- **ORM/Driver:** PyMySQL
- **Auth:** Werkzeug password hashing
- **Frontend:** HTML/CSS (Jinja2 templates)

---

## 🗂️ Project Structure

```
mental_health_system/
├── app.py            # Flask application (routes, logic)
├── schema.sql        # Database schema (tables, triggers, procedures, views)
├── seed.py           # Seed script to populate initial data
├── requirements.txt  # Python dependencies
└── templates/        # HTML templates
```

---

## ⚙️ Prerequisites

- Python 3.10+
- MySQL Server 8.4 (service name: `MySQL84`)
- pip

---

## 🚀 Setup & Installation

### Step 1 — Clone / Open the project in VS Code

```bash
cd D:\mental_health_system
```

### Step 2 — Create and activate virtual environment

```bash
python -m venv .venv
```

Activate in PowerShell:
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Start MySQL service (run PowerShell as Administrator)

```bash
net start MySQL84
```

### Step 5 — Load the database schema

```bash
Get-Content D:\mental_health_system\schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p"root123"
```

### Step 6 — Seed the database with initial data

```bash
python seed.py
```

### Step 7 — Run the Flask app

```bash
python app.py
```

### Step 8 — Open in browser

```
http://127.0.0.1:5000
```

---

## 🔑 Login Credentials

| Role      | Email                  | Password    |
|-----------|------------------------|-------------|
| Admin     | admin@mhs.com          | admin123    |
| Counselor | priya@mhs.com          | counsel123  |
| Counselor | arjun@mhs.com          | counsel456  |
| User      | raj@student.com        | user123     |
| User      | varish@student.com     | user456     |
| User      | isha@student.com       | user789     |

---

## 🛠️ MySQL — Useful Commands

Open MySQL in terminal:
```bash
mysql -u root -p"root123"
```

Inside MySQL:
```sql
USE MentalHealthDB;
SHOW TABLES;
SELECT UserID, Email, Role FROM Users;
```

Delete a user (deletes their alerts first due to foreign key):
```sql
USE MentalHealthDB;
DELETE FROM Alerts WHERE UserID = (SELECT UserID FROM Users WHERE Email='user@example.com');
DELETE FROM Users WHERE Email='user@example.com';
```

---

## 🗃️ Database Features

| Feature | Details |
|---|---|
| Tables | Users, Counselors, Alerts, SupportSessions, Reports, AuditLog |
| Views | v_all_alerts, v_pending_alerts, v_critical_cases, v_resolved_cases, v_counselor_stats |
| Triggers | Auto-set severity on insert, audit log on status/counselor change |
| Stored Procedures | assign_counselor, resolve_case, approve_and_generate_report, batch_update_severities |
| Functions | get_severity_level, get_counselor_active_cases |

---

## 👥 Roles & Permissions

**User**
- Register and log in
- Submit a mental health alert (Anxiety, Depression, Stress, etc.)
- View their own cases and reports

**Counselor**
- View assigned cases sorted by severity
- Resolve cases, add session notes, escalate to CRITICAL
- View session history

**Admin**
- View all cases across the system
- Assign counselors to cases
- Approve resolved cases and auto-generate patient reports
- Manage users (promote roles)
- View database tables, views, procedures, triggers
- Run batch severity recalculation (cursor procedure)

---

## 🔄 Restarting the App

Every time you reopen VS Code:

```bash
# 1. Activate virtual environment
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1

# 2. Run the app
python app.py
```

Then visit `http://127.0.0.1:5000`

---

## ⚠️ Troubleshooting

**MySQL Access Denied:**
Make sure MySQL service is running:
```bash
# In Admin PowerShell
net start MySQL84
```

**PowerShell `<` redirection error:**
Use this instead of `mysql ... < schema.sql`:
```bash
Get-Content schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p"root123"
```

**Virtual environment not activating:**
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```
