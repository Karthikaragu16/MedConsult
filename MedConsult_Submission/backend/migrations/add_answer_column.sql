-- ============================================================
-- Migration: Add missing columns to queries table
-- Run this ONCE on your existing database to apply Bug #12 fix
-- ============================================================

USE health_assistant;

-- Add 'answer' column if it doesn't already exist
ALTER TABLE queries
    ADD COLUMN IF NOT EXISTS answer TEXT,
    ADD COLUMN IF NOT EXISTS answered_by INT;

-- Verify
DESCRIBE queries;
