-- Migration: doctor_features.sql
-- 1. Add patient_rating column to appointments
ALTER TABLE appointments
    ADD COLUMN IF NOT EXISTS patient_rating DECIMAL(2,1) DEFAULT NULL;

-- 2. Create doctor_prescriptions table (doctor uploads per appointment)
CREATE TABLE IF NOT EXISTS doctor_prescriptions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id  INT NOT NULL,
    doctor_id       INT NOT NULL,
    patient_mail    VARCHAR(100) NOT NULL,
    filename        VARCHAR(255) NOT NULL,
    description     VARCHAR(500),
    upload_date     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id)      REFERENCES doctor(id)       ON DELETE CASCADE
);
