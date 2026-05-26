-- --------------------------------------------------------
-- Virtual Health Assistant - Full Database Schema
-- --------------------------------------------------------

CREATE DATABASE IF NOT EXISTS health_assistant;
USE health_assistant;

-- 1. Patients Table
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

-- 2. Doctors Table
CREATE TABLE IF NOT EXISTS doctor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    mail VARCHAR(100) UNIQUE NOT NULL,
    pwd VARCHAR(255) NOT NULL,
    dept VARCHAR(100) NOT NULL, -- Specialization
    hospital_name VARCHAR(150),
    experience INT,
    contact VARCHAR(15),
    rating DECIMAL(2,1) DEFAULT 4.5,
    availability VARCHAR(100) DEFAULT 'Available Today',
    location VARCHAR(100),
    link VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 3. Symptoms History Table
CREATE TABLE IF NOT EXISTS history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    symptoms TEXT,
    condition_name VARCHAR(100),
    severity VARCHAR(50),
    analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_mail) REFERENCES patient(mail) ON DELETE CASCADE
);

-- 4. Appointments Table
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

-- 5. Consult Table (Legacy Support)
CREATE TABLE IF NOT EXISTS consult (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    doctor_id INT,
    status VARCHAR(50),
    timing VARCHAR(100),
    FOREIGN KEY (patient_mail) REFERENCES patient(mail) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE CASCADE
);

-- 6. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    amount DECIMAL(10,2),
    payment_status VARCHAR(50) DEFAULT 'Completed',
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

-- 7. Remedies Table
CREATE TABLE IF NOT EXISTS remedies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    condition_name VARCHAR(100),
    remedy_text TEXT,
    dos TEXT,
    donts TEXT
);

-- 8. Doctor Availability Table
CREATE TABLE IF NOT EXISTS doctor_availability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id INT,
    available_date DATE,
    available_time VARCHAR(100),
    is_booked BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE CASCADE
);

-- 9. Medical Reports Table
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    patient_mail VARCHAR(100),
    filename VARCHAR(255),
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_mail) REFERENCES patient(mail) ON DELETE CASCADE
);

-- 10. Queries Table (Chatbot / Support)
CREATE TABLE IF NOT EXISTS queries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT,
    answer TEXT,
    answered_by INT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
