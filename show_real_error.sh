#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ПОКАЗАТЬ РЕАЛЬНУЮ ОШИБКУ БОТА"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "Останавливаю бот..."
systemctl stop taxibot
sleep 2
echo ""

echo "Запускаю бот вручную, чтобы увидеть ошибку:"
echo "────────────────────────────────────────────────────────────"
cd /opt/taxibot
source venv/bin/activate
timeout 10 python -m bot.main 2>&1 || true
echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

echo "Перезапускаю через systemd..."
systemctl start taxibot
sleep 2
systemctl status taxibot --no-pager -l | head -15
echo ""

echo "════════════════════════════════════════════════════════════"
