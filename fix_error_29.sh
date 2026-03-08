#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ИСПРАВЛЕНИЕ ОШИБКИ 29 - ОБНОВЛЕНИЕ ПАРОЛЕЙ"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Останавливаю бота..."
systemctl stop taxibot

echo ""
echo "[2] Обновляю пароли на ТЕСТОВЫЕ..."

# Заменяем боевые пароли на тестовые
sed -i 's/ROBOKASSA_PASSWORD1=.*/ROBOKASSA_PASSWORD1=i9MBFKM8C2j1E4rBZYNU/' /opt/taxibot/.env
sed -i 's/ROBOKASSA_PASSWORD2=.*/ROBOKASSA_PASSWORD2=mrjNy9n8xNuX1BAEq4Q8/' /opt/taxibot/.env

echo ""
echo "[3] Проверяю изменения..."
echo "─────────────────────────────────────────────────────────────"
grep "ROBOKASSA_" /opt/taxibot/.env
echo "─────────────────────────────────────────────────────────────"

echo ""
echo "[4] Запускаю бота..."
systemctl start taxibot

sleep 3

echo ""
echo "[5] Проверка статуса..."
systemctl status taxibot --no-pager -l | head -20

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✓ Пароли обновлены на ТЕСТОВЫЕ"
echo "✓ Бот перезапущен"
echo ""
echo "СЕЙЧАС:"
echo "1. journalctl -u taxibot -f"
echo "2. Тестовый платеж 5₽ в боте"
echo "3. Ошибка 29 должна исчезнуть!"
echo "════════════════════════════════════════════════════════════"
