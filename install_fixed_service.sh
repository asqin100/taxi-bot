#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  УСТАНОВКА ИСПРАВЛЕННОГО SYSTEMD СЕРВИСА"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Останавливаю бота..."
systemctl stop taxibot
echo ""

echo "[2] Копирую новый конфиг..."
cp taxibot.service /etc/systemd/system/taxibot.service
echo ""

echo "[3] Перезагружаю systemd..."
systemctl daemon-reload
echo ""

echo "[4] Запускаю бота..."
systemctl start taxibot
sleep 5
echo ""

echo "[5] Проверка статуса..."
systemctl status taxibot --no-pager -l | head -15
echo ""

echo "[6] Проверка порта 8080..."
if netstat -tuln | grep -q ":8080 "; then
    echo "✓ Порт 8080 работает - webhook готов!"
else
    echo "✗ Порт 8080 не слушается"
    echo ""
    echo "Последние 20 строк логов:"
    journalctl -u taxibot -n 20 --no-pager
fi
echo ""

echo "════════════════════════════════════════════════════════════"
