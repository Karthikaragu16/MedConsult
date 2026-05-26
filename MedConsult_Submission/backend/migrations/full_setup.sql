-- ============================================================
-- Virtual Health Assistant - COMPLETE DATABASE SETUP
-- Run this entire file in MySQL to set up your database
-- ============================================================

CREATE DATABASE IF NOT EXISTS health_assistant;
USE health_assistant;

-- Disable FK checks so we can drop/recreate cleanly
SET FOREIGN_KEY_CHECKS = 0;

-- Drop all tables to ensure clean rebuild
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS doctor_availability;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS queries;
DROP TABLE IF EXISTS history;
DROP TABLE IF EXISTS consult;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS remedies;
DROP TABLE IF EXISTS doctor;
DROP TABLE IF EXISTS patient;
DROP TABLE IF EXISTS hospitals;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. Hospitals Table (must be created BEFORE doctor table)
CREATE TABLE IF NOT EXISTS hospitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    location VARCHAR(100),
    contact VARCHAR(15),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Patients Table
CREATE TABLE IF NOT EXISTS patient (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    mail VARCHAR(100) UNIQUE NOT NULL,
    pwd VARCHAR(255) NOT NULL,
    phone_number VARCHAR(15),
    age INT,
    gender VARCHAR(10),
    location VARCHAR(100),
    BMI DECIMAL(5,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Doctors Table (references hospitals)
CREATE TABLE IF NOT EXISTS doctor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    mail VARCHAR(100) UNIQUE NOT NULL,
    pwd VARCHAR(255) NOT NULL,
    dept VARCHAR(100) NOT NULL,
    hospital_id INT,
    hospital_name VARCHAR(150),
    experience INT,
    contact VARCHAR(15),
    rating DECIMAL(2,1) DEFAULT 4.5,
    availability VARCHAR(100) DEFAULT 'Available Today',
    location VARCHAR(100),
    link VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- 4. Symptoms History Table
CREATE TABLE IF NOT EXISTS history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    symptoms TEXT,
    condition_name VARCHAR(100),
    severity VARCHAR(50),
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_mail) REFERENCES patient(mail) ON DELETE CASCADE
);

-- 5. Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    doctor_id INT,
    appointment_date DATE,
    appointment_time VARCHAR(50),
    consultation_mode VARCHAR(50) DEFAULT 'Physical',
    status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (patient_mail) REFERENCES patient(mail) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE CASCADE
);

-- 6. Consult Table
CREATE TABLE IF NOT EXISTS consult (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    doctor_id INT,
    status VARCHAR(50),
    timing VARCHAR(100),
    FOREIGN KEY (patient_mail) REFERENCES patient(mail) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE CASCADE
);

-- 7. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    amount DECIMAL(10,2),
    payment_status VARCHAR(50) DEFAULT 'Completed',
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

-- 8. Remedies Table
CREATE TABLE IF NOT EXISTS remedies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    condition_name VARCHAR(100),
    remedy_text TEXT,
    dos TEXT,
    donts TEXT
);

-- 9. Doctor Availability Table
CREATE TABLE IF NOT EXISTS doctor_availability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT,
    available_date DATE,
    available_time VARCHAR(100),
    is_booked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE CASCADE
);

-- 10. Medical Reports Table
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    filename VARCHAR(255),
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_mail) REFERENCES patient(mail) ON DELETE CASCADE
);

-- 11. Queries Table (Chatbot / Support)
CREATE TABLE IF NOT EXISTS queries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT,
    answer TEXT,
    answered_by INT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- SAMPLE DATA: Add some hospitals so doctor registration works
-- ============================================================
INSERT IGNORE INTO hospitals (name, location, contact) VALUES
('City General Hospital', 'Chennai', '044-12345678'),
('Apollo Hospital', 'Chennai', '044-98765432'),
('MIOT International', 'Chennai', '044-22222222'),
('Fortis Malar Hospital', 'Chennai', '044-33333333'),
('Sri Ramachandra Hospital', 'Porur', '044-44444444'),
('Kauvery Hospital', 'Trichy', '0431-1111111'),
('PSG Hospitals', 'Coimbatore', '0422-9999999'),
('Government General Hospital', 'Chennai', '044-55555555');

-- ============================================================
-- VERIFY: Show all tables created
-- ============================================================
SHOW TABLES;
