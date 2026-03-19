#!/bin/bash
echo "=== ПРОВЕРКА ПОДПИСКИ В БД ==="
sqlite3 /opt/taxibot/data/bot.db << 'SQL'
.mode column
.headers on
SELECT user_id, subscription_tier, datetime(subscription_expires_at, 'unixepoch', 'localtime') as expires 
FROM users 
WHERE user_id = 244638301;
SQL
