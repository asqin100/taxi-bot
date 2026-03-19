-- Migration: Add coefficient_history table for ML predictions
-- Date: 2026-03-04
-- Description: Creates coefficient_history table to store historical surge data

CREATE TABLE IF NOT EXISTS coefficient_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id TEXT NOT NULL,
    tariff TEXT NOT NULL,
    coefficient REAL NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE INDEX idx_coefficient_history_zone_id ON coefficient_history(zone_id);
CREATE INDEX idx_coefficient_history_timestamp ON coefficient_history(timestamp);
CREATE INDEX idx_zone_tariff_time ON coefficient_history(zone_id, tariff, timestamp);
