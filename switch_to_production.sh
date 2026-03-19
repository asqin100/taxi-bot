#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ВОЗВРАТ В БОЕВОЙ РЕЖИМ С БОЕВЫМИ ПАРОЛЯМИ"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Останавливаю бота..."
systemctl stop taxibot

echo ""
echo "[2] Устанавливаю БОЕВЫЕ настройки..."

# Боевой режим
sed -i 's/ROBOKASSA_TEST_MODE=.*/ROBOKASSA_TEST_MODE=False/' /opt/taxibot/.env

# Боевые пароли
sed -i 's/ROBOKASSA_PASSWORD1=.*/ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42/' /opt/taxibot/.env
sed -i 's/ROBOKASSA_PASSWORD2=.*/ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs/' /opt/taxibot/.env

echo ""
echo "[3] Проверяю настройки..."
echo "─────────────────────────────────────────────────────────────"
grep "ROBOKASSA_" /opt/taxibot/.env
echo "─────────────────────────────────────────────────────────────"

echo ""
echo "[4] Запускаю бота..."
systemctl start taxibot

sleep 3

echo ""
echo "[5] Статус бота..."
systemctl status taxibot --no-pager -l | head -15

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✓ Бот в БОЕВОМ режиме с БОЕВЫМИ паролями"
echo ""
echo "СЕЙЧАС:"
echo "1. journalctl -u taxibot -f"
echo "2. Платеж 5₽ в боте"
echo "3. Должно сработать!"
echo "════════════════════════════════════════════════════════════"
