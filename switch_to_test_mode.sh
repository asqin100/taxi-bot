#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ПЕРЕКЛЮЧЕНИЕ В ТЕСТОВЫЙ РЕЖИМ ROBOKASSA"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Останавливаю бота..."
systemctl stop taxibot

echo ""
echo "[2] Изменяю ROBOKASSA_TEST_MODE на True..."
sed -i 's/ROBOKASSA_TEST_MODE=False/ROBOKASSA_TEST_MODE=True/' /opt/taxibot/.env

echo ""
echo "[3] Проверяю изменение..."
grep "ROBOKASSA_TEST_MODE" /opt/taxibot/.env

echo ""
echo "[4] Запускаю бота..."
systemctl start taxibot

sleep 3

echo ""
echo "[5] Проверка статуса..."
systemctl status taxibot --no-pager -l

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✓ Бот переключён в тестовый режим Robokassa"
echo ""
echo "Теперь сделай тестовый платеж 5₽ в боте и смотри логи:"
echo "journalctl -u taxibot -f"
echo "════════════════════════════════════════════════════════════"
