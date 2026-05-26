-- Migration: add missing columns to doctor table
USE health_assistant;
ALTER TABLE doctor
    ADD COLUMN experience VARCHAR(255) NULL AFTER hospital_id,
    ADD COLUMN contact VARCHAR(50) NULL AFTER experience;
-- Optional: you can also add a location column if needed, but the existing schema already has a default.
