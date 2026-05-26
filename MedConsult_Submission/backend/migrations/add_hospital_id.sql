-- Migration: add_hospital_id to doctor table
USE health_assistant;
ALTER TABLE doctor ADD COLUMN hospital_id INT NOT NULL AFTER dept;
ALTER TABLE doctor ADD CONSTRAINT fk_doctor_hospital FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON UPDATE CASCADE ON DELETE RESTRICT;

-- OPTIONAL: If you have an old column 'hospital_name', you may drop it after migrating data:
-- ALTER TABLE doctor DROP COLUMN hospital_name;
