-- ============================================================
--  HOSTEL MANAGEMENT SYSTEM - MySQL Database
--  File: database.sql
--  Run this ONCE in MySQL Workbench
-- ============================================================

-- Create and select the database
CREATE DATABASE IF NOT EXISTS hostel_db;
USE hostel_db;

-- ─────────────────────────────────────────────
-- TABLE 1: WARDENS
-- Created first because students references it
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wardens (
    warden_id  INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(100) UNIQUE NOT NULL,
    phone      VARCHAR(15),
    block      ENUM('D','L') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO wardens (name, email, phone, block) VALUES
    ('Mr. Rajesh Kumar', 'rajesh@hostel.edu', '9876543210', 'D'),
    ('Mrs. Priya Devi',  'priya@hostel.edu',  '9876543211', 'L');


-- ─────────────────────────────────────────────
-- TABLE 2: PARENTS
-- Created before students because students references it
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parents (
    parent_id  INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(15)  NOT NULL,
    email      VARCHAR(100),
    relation   VARCHAR(50) DEFAULT 'Parent',
    address    TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ─────────────────────────────────────────────
-- TABLE 3: STUDENTS
-- Main table. Connected to wardens + parents
-- via FOREIGN KEY. This is the table app.py
-- reads and writes to for room allocation.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    student_id  VARCHAR(20)  UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    roll_number VARCHAR(20)  UNIQUE NOT NULL,
    dept        VARCHAR(100) NOT NULL,
    year        VARCHAR(20)  NOT NULL,
    phone       VARCHAR(15),
    block       ENUM('D','L') NOT NULL,
    floor       TINYINT NOT NULL,       -- 0=Ground, 1=First, 2=Second
    room_number TINYINT NOT NULL,       -- 1 to 29
    warden_id   INT DEFAULT NULL,
    parent_id   INT DEFAULT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- FK: every student linked to a warden
    CONSTRAINT fk_warden
        FOREIGN KEY (warden_id) REFERENCES wardens(warden_id)
        ON DELETE SET NULL,

    -- FK: every student linked to a parent
    CONSTRAINT fk_parent
        FOREIGN KEY (parent_id) REFERENCES parents(parent_id)
        ON DELETE SET NULL,

    -- Index speeds up room lookup queries
    INDEX idx_room (block, floor, room_number)
);


-- ─────────────────────────────────────────────
-- TABLE 4: COMPLAINTS
-- Students file complaints linked to their ID
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS complaints (
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
-- VERIFY: Run these to check tables were created
-- ─────────────────────────────────────────────
-- SHOW TABLES;
-- SELECT * FROM wardens;
-- SELECT * FROM students;