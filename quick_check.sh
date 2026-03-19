#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  БЫСТРАЯ ПРОВЕРКА БОТА"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Статус бота:"
systemctl is-active taxibot && echo "✅ Работает" || echo "✗ НЕ РАБОТАЕТ"
echo ""

echo "[2] Последние 20 строк логов:"
journalctl -u taxibot -n 20 --no-pager --output=cat
echo ""

echo "[3] Подписка user_id=244638301:"
sqlite3 /opt/taxibot/data/bot.db "SELECT user_id, subscription_tier, datetime(subscription_expires_at, 'unixepoch') FROM users WHERE user_id = 244638301;" 2>/dev/null || echo "Ошибка чтения БД"
echo ""

echo "════════════════════════════════════════════════════════════"
