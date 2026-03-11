-- ============================================================
--  HOSTEL MANAGEMENT SYSTEM — Full Schema v3
--  New: Workers table + full Complaint lifecycle
--  Run this ONCE to set up the complete database
-- ============================================================

DROP DATABASE IF EXISTS hostel_db;
CREATE DATABASE hostel_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hostel_db;

-- ─────────────────────────────────────────────
-- TABLE 1: WATCHMEN
-- ─────────────────────────────────────────────
CREATE TABLE watchmen (
    watchman_id  INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(100) UNIQUE,
    phone        VARCHAR(15)  UNIQUE NOT NULL,
    shift        ENUM('Morning','Evening','Night') DEFAULT 'Morning',
    active       TINYINT(1) DEFAULT 1,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- TABLE 2: WARDENS
-- ─────────────────────────────────────────────
CREATE TABLE wardens (
    warden_id  INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) UNIQUE NOT NULL,
    phone      VARCHAR(15),
    year       ENUM('1','2','3','4') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO wardens (name, email, phone, year) VALUES
    ('Mr. Rajesh Kumar', 'rajesh@hostel.edu', '9876543210', '1'),
    ('Mrs. Priya Devi',  'priya@hostel.edu',  '9876543211', '2');

-- ─────────────────────────────────────────────
-- TABLE 3: PARENTS
-- ─────────────────────────────────────────────
CREATE TABLE parents (
    parent_id  INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(15)  UNIQUE NOT NULL,
    email      VARCHAR(100),
    relation   VARCHAR(50) DEFAULT 'Parent',
    address    TEXT,
    otp        VARCHAR(10)  DEFAULT NULL,
    otp_expiry DATETIME     DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- TABLE 4: STUDENTS
-- ─────────────────────────────────────────────
CREATE TABLE students (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  VARCHAR(20)  UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    roll_number VARCHAR(20)  UNIQUE NOT NULL,
    dept        VARCHAR(100) NOT NULL,
    year        VARCHAR(20)  NOT NULL,
    phone       VARCHAR(15),
    block       ENUM('D','L') NOT NULL,
    floor       TINYINT NOT NULL,
    room_number TINYINT NOT NULL,
    warden_id   INT          DEFAULT NULL,
    parent_id   INT          DEFAULT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_warden FOREIGN KEY (warden_id) REFERENCES wardens(warden_id) ON DELETE SET NULL,
    CONSTRAINT fk_parent FOREIGN KEY (parent_id) REFERENCES parents(parent_id)  ON DELETE SET NULL,
    INDEX idx_room (block, floor, room_number)
);

-- ─────────────────────────────────────────────
-- TABLE 5: WORKERS  (maintenance staff)
-- ─────────────────────────────────────────────
CREATE TABLE workers (
    worker_id   INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    phone       VARCHAR(15)  UNIQUE NOT NULL,
    email       VARCHAR(100),
    category    ENUM('Plumbing','Electrical','Carpentry','Cleaning','Other') DEFAULT 'Other',
    active      TINYINT(1) DEFAULT 1,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO workers (name, phone, category) VALUES
    ('Ramu (Plumber)',  '9000000001', 'Plumbing'),
    ('Selvam (Elect.)', '9000000002', 'Electrical'),
    ('Murugan (Carp.)', '9000000003', 'Carpentry');

-- ─────────────────────────────────────────────
-- TABLE 6: COMPLAINTS  (full lifecycle)
--   OPEN → ASSIGNED → IN_PROGRESS → COMPLETED
-- ─────────────────────────────────────────────
CREATE TABLE complaints (
    complaint_id         INT AUTO_INCREMENT PRIMARY KEY,
    student_id           VARCHAR(20)  NOT NULL,
    student_name         VARCHAR(100) NOT NULL,
    roll_number          VARCHAR(20)  NOT NULL,
    block                ENUM('D','L') NOT NULL,
    room_number          TINYINT      NOT NULL,
    category             ENUM('Plumbing','Electrical','Carpentry','Cleaning','Other') DEFAULT 'Other',
    subject              VARCHAR(200) NOT NULL,
    description          TEXT,
    status               ENUM('OPEN','ASSIGNED','IN_PROGRESS','COMPLETED') DEFAULT 'OPEN',
    assigned_worker_id   INT          DEFAULT NULL,
    assigned_worker_name VARCHAR(100) DEFAULT NULL,
    warden_note          TEXT         DEFAULT NULL,
    assigned_at          DATETIME     DEFAULT NULL,
    worker_started_at    DATETIME     DEFAULT NULL,
    worker_note          TEXT         DEFAULT NULL,
    completed_at         DATETIME     DEFAULT NULL,
    student_feedback     TEXT         DEFAULT NULL,
    rating               TINYINT      DEFAULT NULL,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_complaint_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_complaint_worker  FOREIGN KEY (assigned_worker_id) REFERENCES workers(worker_id) ON DELETE SET NULL,
    INDEX idx_c_student (student_id),
    INDEX idx_c_status  (status)
);

-- ─────────────────────────────────────────────
-- TABLE 7: OUTPASSES
-- ─────────────────────────────────────────────
CREATE TABLE outpasses (
    outpass_id       INT AUTO_INCREMENT PRIMARY KEY,
    student_id       VARCHAR(20)  NOT NULL,
    student_name     VARCHAR(100) NOT NULL,
    roll_number      VARCHAR(20)  NOT NULL,
    dept             VARCHAR(100) NOT NULL,
    year             VARCHAR(20)  NOT NULL,
    phone            VARCHAR(15),
    block            ENUM('D','L') NOT NULL,
    destination      VARCHAR(255) NOT NULL,
    reason           TEXT         NOT NULL,
    leave_datetime   DATETIME     NOT NULL,
    return_datetime  DATETIME     NOT NULL,
    status           ENUM('PENDING','PARENT_APPROVED','PARENT_REJECTED','WARDEN_APPROVED','WARDEN_REJECTED') DEFAULT 'PENDING',
    parent_id        INT          DEFAULT NULL,
    parent_remarks   TEXT         DEFAULT NULL,
    parent_action_at DATETIME     DEFAULT NULL,
    warden_id        INT          DEFAULT NULL,
    warden_remarks   TEXT         DEFAULT NULL,
    warden_action_at DATETIME     DEFAULT NULL,
    exit_time        DATETIME     DEFAULT NULL,
    entry_time       DATETIME     DEFAULT NULL,
    watchman_note    TEXT         DEFAULT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_op_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_op_parent  FOREIGN KEY (parent_id)  REFERENCES parents(parent_id)   ON DELETE SET NULL,
    CONSTRAINT fk_op_warden  FOREIGN KEY (warden_id)  REFERENCES wardens(warden_id)   ON DELETE SET NULL,
    INDEX idx_op_student (student_id),
    INDEX idx_op_status  (status),
    INDEX idx_op_parent  (parent_id),
    INDEX idx_op_warden  (warden_id)
);
