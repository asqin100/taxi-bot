#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  ОБНОВЛЕНИЕ БОТА И ПРОВЕРКА"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Обновление кода..."
git pull origin main
echo ""

echo "[2] Перезапуск бота..."
systemctl restart taxibot
sleep 3
echo ""

echo "[3] Статус бота:"
systemctl is-active taxibot && echo "✅ Работает" || echo "✗ НЕ РАБОТАЕТ"
echo ""

echo "[4] Последние 15 строк логов:"
journalctl -u taxibot -n 15 --no-pager --output=cat
echo ""

echo "[5] Подписка user_id=244638301 в БД:"
sqlite3 /opt/taxibot/data/bot.db "SELECT user_id, subscription_tier, datetime(subscription_expires_at, 'unixepoch', 'localtime') as expires FROM users WHERE user_id = 244638301;" 2>/dev/null || echo "Ошибка БД"
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo "ТЕПЕРЬ ПРОВЕРЬ В @KefPulse_bot:"
echo "Напиши команду: /status"
echo ""
echo "Должно показать активную подписку Pro."
echo "════════════════════════════════════════════════════════════"
