-- Migration 002: Add export tracking
-- Created: 2026-03-04

-- Add last_export_at column to users table for rate limiting
ALTER TABLE users ADD COLUMN last_export_at DATETIME;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_last_export ON users(last_export_at);
