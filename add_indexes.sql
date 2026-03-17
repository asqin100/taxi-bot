-- Database Performance Indexes
-- Run with: sqlite3 data/bot.db < add_indexes.sql

-- User table indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);

-- Shifts table indexes
CREATE INDEX IF NOT EXISTS idx_shifts_user_id ON shifts(user_id);
CREATE INDEX IF NOT EXISTS idx_shifts_start_time ON shifts(start_time);
CREATE INDEX IF NOT EXISTS idx_shifts_user_start ON shifts(user_id, start_time);

-- AI Usage indexes
CREATE INDEX IF NOT EXISTS idx_ai_usage_user_date ON ai_usage(user_id, date);

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_end_time ON events(end_time);
CREATE INDEX IF NOT EXISTS idx_events_zone_type ON events(zone_id, event_type);

-- Coefficient history indexes
CREATE INDEX IF NOT EXISTS idx_coeff_timestamp ON coefficient_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_coeff_zone_timestamp ON coefficient_history(zone_id, timestamp);

-- Subscription indexes
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_expires ON subscriptions(expires_at);

-- Achievements indexes
CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id);

-- Referral earnings indexes
CREATE INDEX IF NOT EXISTS idx_referral_earnings_user ON referral_earnings(user_id);

-- Show created indexes
SELECT 'Created indexes:' as status;
SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name;
