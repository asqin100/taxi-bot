#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ПРОВЕРКА СТАТУСА БОТА"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Исправление базы данных через Python..."
python3 fix_db_python.py
echo ""

echo "[2] Перезапуск бота..."
systemctl restart taxibot
sleep 3
echo ""

echo "[3] Статус сервиса..."
systemctl status taxibot --no-pager -l | head -20
echo ""

echo "[4] Проверка порта 8080..."
if netstat -tuln | grep -q ":8080 "; then
    echo "✓ Порт 8080 слушается - webhook работает!"
else
    echo "✗ Порт 8080 не слушается"
    echo ""
    echo "Последние 30 строк логов:"
    journalctl -u taxibot -n 30 --no-pager
fi
echo ""

echo "════════════════════════════════════════════════════════════"
