-- Database Update Script for AI Health Assistant Upgrade

USE health_assistant;

-- 1. Update Doctor Table
ALTER TABLE doctor ADD COLUMN rating DECIMAL(2,1) DEFAULT 4.5;
ALTER TABLE doctor ADD COLUMN availability VARCHAR(100) DEFAULT 'Available Today';
ALTER TABLE doctor ADD COLUMN location VARCHAR(100) DEFAULT 'Main Clinic';

-- 2. Create Appointments Table
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

-- 3. Create Health History Table
CREATE TABLE IF NOT EXISTS history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    symptoms TEXT,
    condition_name VARCHAR(100),
    severity VARCHAR(50),
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_mail) REFERENCES patient(mail)
);

-- 4. Create Medical Reports Table
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    filename VARCHAR(255),
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_mail) REFERENCES patient(mail)
);
