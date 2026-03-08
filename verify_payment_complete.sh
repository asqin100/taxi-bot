#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  ПОЛНАЯ ПРОВЕРКА ПЛАТЕЖА 5₽"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Логи обработки платежа InvId=1773005523:"
echo "────────────────────────────────────────────────────────────"
journalctl -u taxibot -n 100 --no-pager --output=cat | grep -A 3 -B 1 "1773005523" || echo "Нет логов"
echo ""

echo "[2] Проверка подписки в базе данных (user_id=244638301):"
echo "────────────────────────────────────────────────────────────"
sqlite3 /opt/taxibot/data/bot.db << 'SQL'
.mode column
.headers on
SELECT 
    user_id,
    subscription_tier,
    subscription_expires_at,
    datetime(subscription_expires_at, 'unixepoch', 'localtime') as expires_readable
FROM users 
WHERE user_id = 244638301;
SQL
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo "Если подписка активирована, должно быть:"
echo "✓ subscription_tier: pro"
echo "✓ expires_at: дата через 1 день от сейчас"
echo ""
echo "════════════════════════════════════════════════════════════"
