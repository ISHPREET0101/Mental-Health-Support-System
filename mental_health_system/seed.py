"""
seed.py — Run once to populate MentalHealthDB with initial data.
Usage:  python seed.py
Ensure schema.sql has already been run: mysql -u root -p < schema.sql
"""
import pymysql
from werkzeug.security import generate_password_hash

DB = dict(host='localhost', user='root', password='root123',   # set your password
          database='MentalHealthDB', cursorclass=pymysql.cursors.DictCursor, autocommit=True)

def seed():
    db = pymysql.connect(**DB)
    cur = db.cursor()

    users = [
        ('Admin User',   'admin@mhs.com',    generate_password_hash('patient@'),    'admin',     28, 'M', '9000000001', 'Patiala'),
        ('Dr. Priya',    'priya@mhs.com',    generate_password_hash('counsel123'),  'counselor', 35, 'F', '9000000002', 'Patiala'),
        ('Dr. Arjun',    'arjun@mhs.com',    generate_password_hash('counsel456'),  'counselor', 40, 'M', '9000000003', 'Chandigarh'),
        ('Raj Shekhar',  'raj@student.com',  generate_password_hash('user123'),     'user',      20, 'M', '9111000001', 'Patiala'),
        ('Varish Kapur', 'varish@student.com',generate_password_hash('user456'),    'user',      20, 'M', '9111000002', 'Delhi'),
        ('Isha Singh',   'isha@student.com', generate_password_hash('user789'),     'user',      21, 'F', '9111000003', 'Amritsar'),
    ]

    for u in users:
        cur.execute(
            "INSERT IGNORE INTO Users (Name,Email,PasswordHash,Role,Age,Gender,Contact,Location) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", u
        )

    cur.execute("SELECT UserID FROM Users WHERE Email='priya@mhs.com'")
    priya_id = cur.fetchone()['UserID']
    cur.execute("SELECT UserID FROM Users WHERE Email='arjun@mhs.com'")
    arjun_id = cur.fetchone()['UserID']

    cur.execute("INSERT IGNORE INTO Counselors (UserID,Specialty,Availability) VALUES (%s,%s,%s)",
                (priya_id, 'Anxiety & Depression', 'Available'))
    cur.execute("INSERT IGNORE INTO Counselors (UserID,Specialty,Availability) VALUES (%s,%s,%s)",
                (arjun_id, 'Trauma & Crisis Intervention', 'Available'))

    cur.execute("SELECT UserID FROM Users WHERE Email='raj@student.com'")
    raj_id = cur.fetchone()['UserID']
    cur.execute("SELECT UserID FROM Users WHERE Email='varish@student.com'")
    varish_id = cur.fetchone()['UserID']
    cur.execute("SELECT UserID FROM Users WHERE Email='isha@student.com'")
    isha_id = cur.fetchone()['UserID']

    alerts = [
        (raj_id,    'Anxiety',            'Feeling overwhelmed before exams. Constant worry.'),
        (varish_id, 'Severe Depression',  'Not able to get out of bed. Lost interest in everything.'),
        (isha_id,   'Suicidal',           'Having thoughts of self-harm. Need immediate help.'),
        (raj_id,    'Stress',             'Academic pressure and sleep issues.'),
        (varish_id, 'Depression',         'Feeling hopeless and disconnected from friends.'),
    ]
    for a in alerts:
        cur.execute(
            "INSERT INTO Alerts (UserID,AlertType,Description) VALUES (%s,%s,%s)", a
        )

    print("Seed complete.")
    print("\nLogin credentials:")
    print("  Admin:     admin@mhs.com     / admin123")
    print("  Counselor: priya@mhs.com     / counsel123")
    print("  Counselor: arjun@mhs.com     / counsel456")
    print("  User:      raj@student.com   / user123")
    print("  User:      varish@student.com/ user456")
    print("  User:      isha@student.com  / user789")
    cur.close()
    db.close()

if __name__ == '__main__':
    seed()
