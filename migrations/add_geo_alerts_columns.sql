-- Migration: Add geo alerts tracking columns
-- Date: 2026-03-09
-- Description: Add columns for tracking daily geo alert limits

-- Add geo_alerts_sent_today column
ALTER TABLE users ADD COLUMN geo_alerts_sent_today INTEGER DEFAULT 0;

-- Add geo_alerts_reset_date column
ALTER TABLE users ADD COLUMN geo_alerts_reset_date DATETIME;
