# Mental Health Support System

Web-based mental health platform built with Flask and MySQL. Users submit alerts, counselors manage and resolve cases, admins oversee everything.

---

## Tech Stack

- **Backend:** Python (Flask)
- **Database:** MySQL 8.4
- **Driver:** PyMySQL
- **Auth:** Werkzeug password hashing
- **Frontend:** HTML/CSS (Jinja2)

---

## Project Structure
mental_health_system/

├── app.py            # Routes and logic

├── schema.sql        # Tables, triggers, procedures, views

├── seed.py           # Initial data

├── requirements.txt

└── templates/        # Jinja2 HTML templates
---

## Prerequisites

- Python 3.10+
- MySQL Server 8.4 (service name: `MySQL84`)
- pip

---

## Setup

```bash
# 1. Enter project directory
cd D:\mental_health_system

# 2. Create and activate venv
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start MySQL (run PowerShell as Administrator)
net start MySQL84

# 5. Load schema
Get-Content D:\mental_health_system\schema.sql | & "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" -u root -p"root123"

# 6. Seed initial data
python seed.py

# 7. Run
python app.py
```

Visit `http://127.0.0.1:5000`

---

## Login Credentials

| Role      | Email               | Password   |
|-----------|---------------------|------------|
| Admin     | admin@mhs.com       | admin123   |
| Counselor | priya@mhs.com       | counsel123 |
| Counselor | arjun@mhs.com       | counsel456 |
| User      | raj@student.com     | user123    |
| User      | varish@student.com  | user456    |
| User      | isha@student.com    | user789    |

---

## Database

**Tables:** Users, Counselors, Alerts, SupportSessions, Reports, AuditLog

**Views:** v_all_alerts, v_pending_alerts, v_critical_cases, v_resolved_cases, v_counselor_stats

**Triggers:** Auto-set severity on insert, audit log on status/counselor change

**Stored Procedures:** assign_counselor, resolve_case, approve_and_generate_report, batch_update_severities

**Functions:** get_severity_level, get_counselor_active_cases

---

## Roles

**User** — submit alerts, view own cases and reports

**Counselor** — view assigned cases by severity, resolve/escalate, add session notes

**Admin** — view all cases, assign counselors, approve resolutions, generate reports, manage users, run batch severity recalculation, inspect DB objects

---

## Restarting

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1
python app.py
```

---

## Useful MySQL Commands

```bash
mysql -u root -p"root123"
```

```sql
USE MentalHealthDB;
SHOW TABLES;
SELECT UserID, Email, Role FROM Users;

-- Delete a user (clear alerts first due to FK constraint)
DELETE FROM Alerts WHERE UserID = (SELECT UserID FROM Users WHERE Email='user@example.com');
DELETE FROM Users WHERE Email='user@example.com';
```

---

## Troubleshooting

**MySQL Access Denied** — make sure the service is running:
```bash
net start MySQL84
```

**PowerShell `<` redirection error** — use `Get-Content` instead of `<` for piping to mysql.exe.

**venv not activating:**
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```
