from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mhs_thapar_2024_secret'

# ─── DB CONFIG ────────────────────────────────────────────────────────────────
DB = dict(
    host='localhost',
    user='root',
    password='root123',          # <-- set your MySQL root password here
    database='MentalHealthDB',
    cursorclass=pymysql.cursors.DictCursor,
    autocommit=True
)

def get_db():
    return pymysql.connect(**DB)

# ─── AUTH DECORATORS ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*a, **kw)
    return dec

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def dec(*a, **kw):
            if session.get('role') not in roles:
                flash('Access denied.', 'error')
                return redirect(url_for('dashboard'))
            return f(*a, **kw)
        return dec
    return decorator

# ─── HELPERS ──────────────────────────────────────────────────────────────────
SEVERITY_ORDER = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}

def severity_color(s):
    return {'CRITICAL': '#C0392B', 'HIGH': '#E67E22',
            'MEDIUM': '#2980B9', 'LOW': '#27AE60'}.get(s, '#7F8C8D')

app.jinja_env.globals['severity_color'] = severity_color

# ─── ROOT ─────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form['email'].strip()
        password = request.form['password']
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT * FROM Users WHERE Email=%s", (email,))
                user = cur.fetchone()
            if user and check_password_hash(user['PasswordHash'], password):
                session['user_id'] = user['UserID']
                session['name']    = user['Name']
                session['role']    = user['Role']
                session['email']   = user['Email']
                return redirect(url_for('dashboard'))
            flash('Invalid email or password.', 'error')
        finally:
            db.close()
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name     = request.form['name'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']
        age      = request.form.get('age', '')
        gender   = request.form.get('gender', '')
        contact  = request.form.get('contact', '')
        location = request.form.get('location', '')

        hashed = generate_password_hash(password)
        db = get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT UserID FROM Users WHERE Email=%s", (email,))
                if cur.fetchone():
                    flash('Email already registered.', 'error')
                    return render_template('register.html')
                cur.execute(
                    "INSERT INTO Users (Name,Email,PasswordHash,Age,Gender,Contact,Location) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (name, email, hashed, age or None, gender, contact, location)
                )
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
        finally:
            db.close()
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── DASHBOARD ROUTER ─────────────────────────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'admin':      return redirect(url_for('admin_dashboard'))
    if role == 'counselor':  return redirect(url_for('counselor_dashboard'))
    return redirect(url_for('user_dashboard'))

# ══════════════════════════════════════════════════════════════════════════════
# USER SECTION
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/user/dashboard')
@login_required
@role_required('user')
def user_dashboard():
    uid = session['user_id']
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute(
                "SELECT a.*, r.Content AS ReportContent, r.GeneratedAt AS ReportDate "
                "FROM Alerts a LEFT JOIN Reports r ON a.AlertID=r.AlertID "
                "WHERE a.UserID=%s ORDER BY a.AlertDate DESC", (uid,)
            )
            cases = cur.fetchall()
    finally:
        db.close()
    return render_template('user_dashboard.html', cases=cases)


@app.route('/user/submit', methods=['GET', 'POST'])
@login_required
@role_required('user')
def user_submit():
    if request.method == 'POST':
        uid   = session['user_id']
        atype = request.form['alert_type']
        desc  = request.form.get('description', '').strip()
        db = get_db()
        try:
            with db.cursor() as cur:
                # Severity is set automatically by BEFORE INSERT trigger
                cur.execute(
                    "INSERT INTO Alerts (UserID, AlertType, Description) VALUES (%s,%s,%s)",
                    (uid, atype, desc)
                )
            flash('Your case has been submitted. Stay safe.', 'success')
            return redirect(url_for('user_dashboard'))
        except Exception as e:
            flash(f'Error submitting case: {e}', 'error')
        finally:
            db.close()
    return render_template('user_submit.html')

# ══════════════════════════════════════════════════════════════════════════════
# COUNSELOR SECTION
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/counselor/dashboard')
@login_required
@role_required('counselor')
def counselor_dashboard():
    uid = session['user_id']
    db = get_db()
    try:
        with db.cursor() as cur:
            # Get counselor ID for this user
            cur.execute("SELECT CounselorID FROM Counselors WHERE UserID=%s", (uid,))
            c = cur.fetchone()
            if not c:
                flash('Counselor profile not found.', 'error')
                return redirect(url_for('logout'))
            cid = c['CounselorID']
            session['counselor_id'] = cid

            cur.execute(
                "SELECT a.*, u.Name AS PatientName, u.Contact AS PatientContact "
                "FROM Alerts a JOIN Users u ON a.UserID=u.UserID "
                "WHERE a.AssignedCounselorID=%s ORDER BY "
                "FIELD(a.Severity,'CRITICAL','HIGH','MEDIUM','LOW'), a.AlertDate DESC",
                (cid,)
            )
            cases = cur.fetchall()

            cur.execute(
                "SELECT ss.*, a.AlertID, u.Name AS PatientName "
                "FROM SupportSessions ss "
                "JOIN Alerts a ON ss.AlertID=a.AlertID "
                "JOIN Users u ON a.UserID=u.UserID "
                "WHERE ss.CounselorID=%s ORDER BY ss.SessionDate DESC LIMIT 10",
                (cid,)
            )
            sessions = cur.fetchall()
    finally:
        db.close()
    return render_template('counselor_dashboard.html', cases=cases, sessions=sessions)


@app.route('/counselor/update/<int:alert_id>', methods=['POST'])
@login_required
@role_required('counselor')
def counselor_update(alert_id):
    cid   = session.get('counselor_id')
    notes = request.form.get('notes', '').strip()
    action = request.form.get('action')
    db = get_db()
    try:
        with db.cursor() as cur:
            if action == 'resolve':
                # Calls stored procedure resolve_case
                cur.callproc('resolve_case', [alert_id, cid, notes])
                flash('Case marked as resolved.', 'success')
            elif action == 'escalate':
                cur.execute(
                    "UPDATE Alerts SET Severity='CRITICAL' WHERE AlertID=%s", (alert_id,)
                )
                if notes:
                    cur.execute(
                        "INSERT INTO SupportSessions (AlertID,CounselorID,Notes) VALUES (%s,%s,%s)",
                        (alert_id, cid, f'[ESCALATED] {notes}')
                    )
                flash('Case escalated to CRITICAL.', 'warning')
            elif action == 'note':
                cur.execute(
                    "INSERT INTO SupportSessions (AlertID,CounselorID,Notes) VALUES (%s,%s,%s)",
                    (alert_id, cid, notes)
                )
                flash('Session note added.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    finally:
        db.close()
    return redirect(url_for('counselor_dashboard'))

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN SECTION
# ══════════════════════════════════════════════════════════════════════════════
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM v_all_alerts ORDER BY "
                        "FIELD(Severity,'CRITICAL','HIGH','MEDIUM','LOW'), AlertDate DESC")
            all_cases = cur.fetchall()

            cur.execute("SELECT * FROM v_counselor_stats")
            counselors = cur.fetchall()

            cur.execute("SELECT COUNT(*) AS total FROM Alerts")
            total = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) AS cnt FROM Alerts WHERE Status='Pending'")
            pending = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM Alerts WHERE Severity IN ('HIGH','CRITICAL') AND Status!='Approved'")
            critical = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM Alerts WHERE Status='Approved'")
            approved = cur.fetchone()['cnt']

            cur.execute("SELECT * FROM AuditLog ORDER BY ChangedAt DESC LIMIT 20")
            audit = cur.fetchall()

            # Raw counselors list for assign dropdown
            cur.execute("SELECT c.CounselorID, u.Name, c.Specialty, c.Availability "
                        "FROM Counselors c JOIN Users u ON c.UserID=u.UserID")
            counselor_list = cur.fetchall()

    finally:
        db.close()

    stats = dict(total=total, pending=pending, critical=critical, approved=approved)
    return render_template('admin_dashboard.html',
                           all_cases=all_cases,
                           counselors=counselors,
                           counselor_list=counselor_list,
                           stats=stats,
                           audit=audit)


@app.route('/admin/assign/<int:alert_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_assign(alert_id):
    cid = request.form.get('counselor_id', type=int)
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.callproc('assign_counselor', [alert_id, cid])
        flash('Counselor assigned successfully.', 'success')
    except Exception as e:
        flash(f'Assignment failed: {e}', 'error')
    finally:
        db.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/approve/<int:alert_id>', methods=['POST'])
@login_required
@role_required('admin')
def admin_approve(alert_id):
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.callproc('approve_and_generate_report', [alert_id])
        flash('Case approved. Report sent to patient.', 'success')
    except Exception as e:
        flash(f'Approval failed: {e}', 'error')
    finally:
        db.close()
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/batch-severity', methods=['POST'])
@login_required
@role_required('admin')
def admin_batch_severity():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.callproc('batch_update_severities')
        flash('Severity batch update complete (cursor procedure ran).', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    finally:
        db.close()
    return redirect(url_for('admin_dashboard'))


# ─── ADMIN DB VIEWER ──────────────────────────────────────────────────────────
@app.route('/admin/db')
@login_required
@role_required('admin')
def admin_db():
    db = get_db()
    tables = {}
    views  = {}
    procs  = []
    funcs  = []
    triggers = []
    try:
        with db.cursor() as cur:
            # Tables
            for tbl in ['Users','Counselors','Alerts','SupportSessions','Reports','AuditLog']:
                cur.execute(f"SELECT * FROM {tbl} LIMIT 50")
                rows = cur.fetchall()
                tables[tbl] = rows

            # Views
            for v in ['v_pending_alerts','v_critical_cases','v_resolved_cases','v_counselor_stats']:
                cur.execute(f"SELECT * FROM {v} LIMIT 30")
                views[v] = cur.fetchall()

            # Stored Procedures
            cur.execute("SHOW PROCEDURE STATUS WHERE Db='MentalHealthDB'")
            procs = cur.fetchall()

            # Functions
            cur.execute("SHOW FUNCTION STATUS WHERE Db='MentalHealthDB'")
            funcs = cur.fetchall()

            # Triggers
            cur.execute("SHOW TRIGGERS FROM MentalHealthDB")
            triggers = cur.fetchall()

    finally:
        db.close()

    return render_template('admin_db.html',
                           tables=tables, views=views,
                           procs=procs, funcs=funcs, triggers=triggers)


# ─── ADMIN: MANAGE USERS ──────────────────────────────────────────────────────
@app.route('/admin/users')
@login_required
@role_required('admin')
def admin_users():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT UserID,Name,Email,Role,Age,Gender,Contact,Location,CreatedAt FROM Users ORDER BY CreatedAt DESC")
            users = cur.fetchall()
    finally:
        db.close()
    return render_template('admin_users.html', users=users)


@app.route('/admin/promote/<int:uid>', methods=['POST'])
@login_required
@role_required('admin')
def admin_promote(uid):
    role     = request.form.get('role')
    specialty = request.form.get('specialty', 'General')
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("UPDATE Users SET Role=%s WHERE UserID=%s", (role, uid))
            if role == 'counselor':
                cur.execute("SELECT CounselorID FROM Counselors WHERE UserID=%s", (uid,))
                if not cur.fetchone():
                    cur.execute(
                        "INSERT INTO Counselors (UserID, Specialty) VALUES (%s,%s)",
                        (uid, specialty)
                    )
        flash('User role updated.', 'success')
    except Exception as e:
        flash(f'Error: {e}', 'error')
    finally:
        db.close()
    return redirect(url_for('admin_users'))


# ─── API: case data (for dynamic table refresh) ───────────────────────────────
@app.route('/api/cases')
@login_required
@role_required('admin')
def api_cases():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM v_all_alerts ORDER BY AlertDate DESC")
            rows = cur.fetchall()
    finally:
        db.close()
    for r in rows:
        for k, v in r.items():
            if isinstance(v, datetime):
                r[k] = v.strftime('%Y-%m-%d %H:%M')
    return jsonify(rows)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
