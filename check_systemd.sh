#!/bin/bash
echo "=== SYSTEMD CONFIG ==="
cat /etc/systemd/system/taxibot.service
echo ""
echo "=== ПРОВЕРКА ПОРТА 8080 ==="
sleep 3
if netstat -tuln | grep -q ":8080 "; then
    echo "✓ Порт 8080 работает!"
else
    echo "✗ Порт 8080 не слушается"
fi
