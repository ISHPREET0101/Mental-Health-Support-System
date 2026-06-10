-- ============================================================
-- Community Mental Health Alert & Support System
-- Database: MentalHealthDB  |  Course: UCS310 (DBMS)
-- Thapar Institute of Engineering & Technology
-- ============================================================

DROP DATABASE IF EXISTS MentalHealthDB;
CREATE DATABASE MentalHealthDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE MentalHealthDB;

-- ============================================================
-- TABLE DEFINITIONS
-- ============================================================

CREATE TABLE Users (
    UserID      INT PRIMARY KEY AUTO_INCREMENT,
    Name        VARCHAR(100) NOT NULL,
    Email       VARCHAR(100) UNIQUE NOT NULL,
    PasswordHash VARCHAR(256) NOT NULL,
    Role        ENUM('user', 'counselor', 'admin') DEFAULT 'user',
    Age         INT CHECK (Age > 0 AND Age < 100),
    Gender      VARCHAR(10),
    Contact     VARCHAR(15),
    Location    VARCHAR(100),
    CreatedAt   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Counselors (
    CounselorID  INT PRIMARY KEY AUTO_INCREMENT,
    UserID       INT NOT NULL,
    Specialty    VARCHAR(100) NOT NULL,
    Availability ENUM('Available', 'Busy', 'Offline') DEFAULT 'Available',
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

CREATE TABLE Alerts (
    AlertID             INT PRIMARY KEY AUTO_INCREMENT,
    UserID              INT NOT NULL,
    AlertType           ENUM('Anxiety','Depression','Severe Depression','Suicidal','Self-harm','Stress','Others') NOT NULL,
    Description         TEXT,
    Severity            ENUM('LOW','MEDIUM','HIGH','CRITICAL') DEFAULT 'LOW',
    Status              ENUM('Pending','In Progress','Resolved','Approved') DEFAULT 'Pending',
    AssignedCounselorID INT DEFAULT NULL,
    AlertDate           DATETIME DEFAULT CURRENT_TIMESTAMP,
    ResolvedAt          DATETIME DEFAULT NULL,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (AssignedCounselorID) REFERENCES Counselors(CounselorID) ON DELETE SET NULL
);

CREATE TABLE SupportSessions (
    SessionID   INT PRIMARY KEY AUTO_INCREMENT,
    AlertID     INT NOT NULL,
    CounselorID INT NOT NULL,
    SessionDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    Notes       TEXT,
    FOREIGN KEY (AlertID) REFERENCES Alerts(AlertID) ON DELETE CASCADE,
    FOREIGN KEY (CounselorID) REFERENCES Counselors(CounselorID)
);

CREATE TABLE Reports (
    ReportID      INT PRIMARY KEY AUTO_INCREMENT,
    AlertID       INT NOT NULL UNIQUE,
    Content       TEXT NOT NULL,
    GeneratedAt   DATETIME DEFAULT CURRENT_TIMESTAMP,
    SentToPatient BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (AlertID) REFERENCES Alerts(AlertID)
);

CREATE TABLE AuditLog (
    LogID      INT PRIMARY KEY AUTO_INCREMENT,
    AlertID    INT,
    Action     VARCHAR(100),
    OldValue   VARCHAR(200),
    NewValue   VARCHAR(200),
    ChangedAt  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AlertID) REFERENCES Alerts(AlertID) ON DELETE SET NULL
);

-- ============================================================
-- FUNCTIONS
-- ============================================================

DELIMITER //

-- Function 1: Map AlertType → Severity string
CREATE FUNCTION get_severity_level(alert_type VARCHAR(50))
RETURNS VARCHAR(10)
DETERMINISTIC
BEGIN
    DECLARE sev VARCHAR(10);
    CASE alert_type
        WHEN 'Suicidal'          THEN SET sev = 'CRITICAL';
        WHEN 'Self-harm'         THEN SET sev = 'HIGH';
        WHEN 'Severe Depression' THEN SET sev = 'HIGH';
        WHEN 'Depression'        THEN SET sev = 'MEDIUM';
        WHEN 'Anxiety'           THEN SET sev = 'MEDIUM';
        WHEN 'Stress'            THEN SET sev = 'LOW';
        ELSE                          SET sev = 'LOW';
    END CASE;
    RETURN sev;
END //

-- Function 2: Count active (non-resolved) cases for a counselor
CREATE FUNCTION get_counselor_active_cases(c_id INT)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt
    FROM Alerts
    WHERE AssignedCounselorID = c_id
      AND Status IN ('Pending', 'In Progress');
    RETURN cnt;
END //

DELIMITER ;

-- ============================================================
-- TRIGGERS
-- ============================================================

DELIMITER //

-- Trigger 1: Auto-set Severity BEFORE a new alert is inserted
CREATE TRIGGER trg_set_severity
BEFORE INSERT ON Alerts
FOR EACH ROW
BEGIN
    SET NEW.Severity = get_severity_level(NEW.AlertType);
END //

-- Trigger 2: Audit log on Status or Counselor change (AFTER UPDATE)
CREATE TRIGGER trg_audit_status_change
AFTER UPDATE ON Alerts
FOR EACH ROW
BEGIN
    IF OLD.Status != NEW.Status THEN
        INSERT INTO AuditLog (AlertID, Action, OldValue, NewValue)
        VALUES (NEW.AlertID, 'STATUS_CHANGE', OLD.Status, NEW.Status);
    END IF;

    IF (OLD.AssignedCounselorID IS NULL AND NEW.AssignedCounselorID IS NOT NULL)
       OR (OLD.AssignedCounselorID != NEW.AssignedCounselorID) THEN
        INSERT INTO AuditLog (AlertID, Action, OldValue, NewValue)
        VALUES (
            NEW.AlertID,
            'COUNSELOR_ASSIGNED',
            COALESCE(CAST(OLD.AssignedCounselorID AS CHAR), 'None'),
            CAST(NEW.AssignedCounselorID AS CHAR)
        );
    END IF;
END //

DELIMITER ;

-- ============================================================
-- STORED PROCEDURES
-- ============================================================

DELIMITER //

-- Procedure 1: Assign a counselor to an alert
CREATE PROCEDURE assign_counselor(IN p_alert_id INT, IN p_counselor_id INT)
BEGIN
    DECLARE v_alert_count  INT DEFAULT 0;
    DECLARE v_cnslr_count  INT DEFAULT 0;

    SELECT COUNT(*) INTO v_alert_count  FROM Alerts     WHERE AlertID     = p_alert_id;
    SELECT COUNT(*) INTO v_cnslr_count  FROM Counselors WHERE CounselorID = p_counselor_id;

    IF v_alert_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Alert not found';
    ELSEIF v_cnslr_count = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Counselor not found';
    ELSE
        UPDATE Alerts
        SET AssignedCounselorID = p_counselor_id,
            Status = 'In Progress'
        WHERE AlertID = p_alert_id;
        SELECT 'Counselor assigned successfully' AS message;
    END IF;
END //

-- Procedure 2: Resolve a case (counselor logs session + marks resolved)
CREATE PROCEDURE resolve_case(
    IN p_alert_id    INT,
    IN p_counselor_id INT,
    IN p_notes       TEXT
)
BEGIN
    INSERT INTO SupportSessions (AlertID, CounselorID, Notes)
    VALUES (p_alert_id, p_counselor_id, p_notes);

    UPDATE Alerts
    SET Status = 'Resolved', ResolvedAt = NOW()
    WHERE AlertID = p_alert_id;

    SELECT 'Case resolved successfully' AS message;
END //

-- Procedure 3: Admin approves case + auto-generates patient report
CREATE PROCEDURE approve_and_generate_report(IN p_alert_id INT)
BEGIN
    DECLARE v_patient_name   VARCHAR(100);
    DECLARE v_alert_type     VARCHAR(50);
    DECLARE v_severity       VARCHAR(10);
    DECLARE v_counselor_name VARCHAR(100);
    DECLARE v_alert_date     DATETIME;
    DECLARE v_resolved_at    DATETIME;
    DECLARE v_report         TEXT;

    SELECT
        u.Name, a.AlertType, a.Severity,
        IFNULL(u2.Name, 'Not Assigned'),
        a.AlertDate, a.ResolvedAt
    INTO
        v_patient_name, v_alert_type, v_severity,
        v_counselor_name, v_alert_date, v_resolved_at
    FROM Alerts a
    JOIN Users u ON a.UserID = u.UserID
    LEFT JOIN Counselors c ON a.AssignedCounselorID = c.CounselorID
    LEFT JOIN Users u2 ON c.UserID = u2.UserID
    WHERE a.AlertID = p_alert_id;

    SET v_report = CONCAT(
        'MENTAL HEALTH SUPPORT — CASE REPORT\n',
        '=====================================\n',
        'Patient      : ', v_patient_name, '\n',
        'Alert Type   : ', v_alert_type, '\n',
        'Severity     : ', v_severity, '\n',
        'Counselor    : ', v_counselor_name, '\n',
        'Reported On  : ', v_alert_date, '\n',
        'Resolved On  : ', IFNULL(v_resolved_at, 'Pending'), '\n',
        '-------------------------------------\n',
        'Your case has been reviewed and approved by the administration.\n',
        'Thank you for reaching out. Your wellbeing matters.\n',
        'If you need further support, please submit a new case.'
    );

    INSERT INTO Reports (AlertID, Content, SentToPatient)
    VALUES (p_alert_id, v_report, TRUE)
    ON DUPLICATE KEY UPDATE Content = v_report, GeneratedAt = NOW();

    UPDATE Alerts SET Status = 'Approved' WHERE AlertID = p_alert_id;

    SELECT v_report AS report;
END //

-- Procedure 4: CURSOR — batch-recalculate severity for all Pending alerts
CREATE PROCEDURE batch_update_severities()
BEGIN
    DECLARE v_done     INT DEFAULT FALSE;
    DECLARE v_alert_id INT;
    DECLARE v_type     VARCHAR(50);
    DECLARE v_sev      VARCHAR(10);

    DECLARE sev_cursor CURSOR FOR
        SELECT AlertID, AlertType
        FROM Alerts
        WHERE Status = 'Pending';

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;

    OPEN sev_cursor;

    batch_loop: LOOP
        FETCH sev_cursor INTO v_alert_id, v_type;
        IF v_done THEN
            LEAVE batch_loop;
        END IF;
        SET v_sev = get_severity_level(v_type);
        UPDATE Alerts SET Severity = v_sev WHERE AlertID = v_alert_id;
    END LOOP;

    CLOSE sev_cursor;

    SELECT 'Batch severity recalculation complete' AS message;
END //

DELIMITER ;

-- ============================================================
-- VIEWS
-- ============================================================

CREATE VIEW v_all_alerts AS
SELECT
    a.AlertID,
    u.Name        AS PatientName,
    u.Email       AS PatientEmail,
    u.Contact     AS PatientContact,
    a.AlertType,
    a.Severity,
    a.Status,
    a.Description,
    a.AlertDate,
    a.ResolvedAt,
    IFNULL(u2.Name, 'Unassigned') AS CounselorName,
    c.Specialty                   AS CounselorSpecialty
FROM Alerts a
JOIN  Users u   ON a.UserID             = u.UserID
LEFT JOIN Counselors c ON a.AssignedCounselorID = c.CounselorID
LEFT JOIN Users u2  ON c.UserID             = u2.UserID;

CREATE VIEW v_pending_alerts AS
SELECT * FROM v_all_alerts WHERE Status IN ('Pending', 'In Progress');

CREATE VIEW v_critical_cases AS
SELECT * FROM v_pending_alerts WHERE Severity IN ('HIGH', 'CRITICAL');

CREATE VIEW v_resolved_cases AS
SELECT * FROM v_all_alerts WHERE Status IN ('Resolved', 'Approved');

CREATE VIEW v_counselor_stats AS
SELECT
    u.Name          AS CounselorName,
    c.CounselorID,
    c.Specialty,
    c.Availability,
    get_counselor_active_cases(c.CounselorID) AS ActiveCases
FROM Counselors c
JOIN Users u ON c.UserID = u.UserID;
