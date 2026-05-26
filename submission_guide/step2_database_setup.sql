-- STEP 2: DATABASE SETUP
-- This script initializes the MySQL database for the project.

CREATE DATABASE IF NOT EXISTS health_assistant;
USE health_assistant;

-- Hospitals Table – list of partner hospitals / clinics
CREATE TABLE IF NOT EXISTS hospitals (
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);
-- Seed data for hospitals table
INSERT INTO hospitals (name) VALUES
('City General Hospital'),
('Sunrise Medical Center'),
('Northern Clinic'),
('Green Valley Hospital'),
('Eastside Health Institute');

-- Patients Table
CREATE TABLE IF NOT EXISTS patient (
    name VARCHAR(100),
    mail VARCHAR(100) PRIMARY KEY,
    pwd VARCHAR(255),
    age INT,
    gender VARCHAR(20),
    location VARCHAR(100),
    BMI DECIMAL(4,2)
);

-- Doctors Table
CREATE TABLE IF NOT EXISTS doctor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    dept VARCHAR(100),
    hospital_id INT NOT NULL,
    mail VARCHAR(100),
    pwd VARCHAR(255),
    rating DECIMAL(2,1) DEFAULT 4.5,
    availability VARCHAR(100) DEFAULT 'Available Today',
    location VARCHAR(100) DEFAULT 'Main Clinic',
    CONSTRAINT fk_doctor_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Appointments Table
CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    doctor_id INT,
    appointment_date DATE,
    appointment_time VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Pending',
    FOREIGN KEY (patient_mail) REFERENCES patient(mail),
    FOREIGN KEY (doctor_id) REFERENCES doctor(id)
);

-- Health Analysis History
CREATE TABLE IF NOT EXISTS history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    symptoms TEXT,
    condition_name VARCHAR(100),
    severity VARCHAR(50),
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_mail) REFERENCES patient(mail)
);

-- Queries Table
CREATE TABLE IF NOT EXISTS queries (
    sno INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT,
    answer TEXT,
    status VARCHAR(20) DEFAULT 'pending'
);
