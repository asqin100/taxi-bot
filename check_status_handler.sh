#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  ПРОВЕРКА ОБРАБОТЧИКА /status"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Логи при отправке /status (последние 30 строк):"
journalctl -u taxibot -n 30 --no-pager --output=cat | tail -20
echo ""

echo "[2] Есть ли ошибки в логах:"
journalctl -u taxibot -n 50 --no-pager | grep -i "error\|exception\|traceback" | tail -10 || echo "Нет ошибок"
echo ""

echo "[3] Подписка в БД:"
sqlite3 /opt/taxibot/data/bot.db "SELECT * FROM users WHERE user_id = 244638301;" 2>/dev/null || echo "Ошибка БД"
echo ""

echo "════════════════════════════════════════════════════════════"
