-- Добавление недостающих колонок в таблицу users
ALTER TABLE users ADD COLUMN geo_alerts_sent_today INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN geo_alerts_reset_date TEXT;
