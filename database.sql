-- ============================================================
--  HOSTEL MANAGEMENT SYSTEM - MySQL Database
--  File: database.sql
--  Run this ONCE in MySQL Workbench
-- ============================================================

-- Drop and recreate database cleanly
DROP DATABASE IF EXISTS hostel_db;
CREATE DATABASE hostel_db;
USE hostel_db;

-- ─────────────────────────────────────────────
-- TABLE 1: WARDENS
-- Stores warden details for each block
-- Must be created before students (FK reference)
-- ─────────────────────────────────────────────
CREATE TABLE wardens (
    warden_id  INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) UNIQUE NOT NULL,
    phone      VARCHAR(15),
    block      ENUM('D','L') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default wardens for D and L block
INSERT INTO wardens (name, email, phone, block) VALUES
    ('Mr. Rajesh Kumar', 'rajesh@hostel.edu', '9876543210', 'D'),
    ('Mrs. Priya Devi',  'priya@hostel.edu',  '9876543211', 'L');


-- ─────────────────────────────────────────────
-- TABLE 2: PARENTS
-- parent_id is VARCHAR so it can accept values
-- like "PAR001" entered from the form
-- Must be created before students (FK reference)
-- ─────────────────────────────────────────────
CREATE TABLE parents (
    parent_id  VARCHAR(20) PRIMARY KEY,       -- e.g. PAR001
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(15)  NOT NULL,
    email      VARCHAR(100),
    relation   VARCHAR(50) DEFAULT 'Parent',  -- Father / Mother / Guardian
    address    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────
-- TABLE 3: STUDENTS
-- Links to wardens (warden_id FK)
-- Links to parents  (parent_id FK)
-- ─────────────────────────────────────────────
CREATE TABLE students (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  VARCHAR(20)  UNIQUE NOT NULL,   -- e.g. STU001
    name        VARCHAR(100) NOT NULL,
    roll_number VARCHAR(20)  UNIQUE NOT NULL,   -- e.g. 22CS001
    dept        VARCHAR(100) NOT NULL,
    year        VARCHAR(20)  NOT NULL,
    phone       VARCHAR(15),
    block       ENUM('D','L') NOT NULL,
    floor       TINYINT NOT NULL,               -- 0=Ground 1=First 2=Second
    room_number TINYINT NOT NULL,               -- 1 to 29
    warden_id   INT          DEFAULT NULL,
    parent_id   VARCHAR(20)  DEFAULT NULL,      -- matches parents.parent_id type
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- FK: student → warden
    CONSTRAINT fk_warden
        FOREIGN KEY (warden_id) REFERENCES wardens(warden_id)
        ON DELETE SET NULL,

    -- FK: student → parent
    CONSTRAINT fk_parent
        FOREIGN KEY (parent_id) REFERENCES parents(parent_id)
        ON DELETE SET NULL,

    -- Index for fast room queries
    INDEX idx_room (block, floor, room_number)
);


-- ─────────────────────────────────────────────
-- TABLE 4: COMPLAINTS
-- Linked to students via student_id FK
-- ─────────────────────────────────────────────
CREATE TABLE complaints (
    complaint_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id   VARCHAR(20) NOT NULL,
    subject      VARCHAR(200) NOT NULL,
    description  TEXT,
    status       ENUM('Pending','In Progress','Resolved') DEFAULT 'Pending',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_complaint_student
        FOREIGN KEY (student_id) REFERENCES students(student_id)
        ON DELETE CASCADE
);


-- ─────────────────────────────────────────────
-- VERIFY  (uncomment and run to check)
-- ─────────────────────────────────────────────
-- SHOW TABLES;
-- SELECT * FROM wardens;
-- DESCRIBE students;
-- DESCRIBE parents;
