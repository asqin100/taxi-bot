#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ФИНАЛЬНАЯ ПРОВЕРКА ПЕРЕД НАСТРОЙКОЙ ROBOKASSA"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Статус бота..."
systemctl status taxibot --no-pager | head -10
echo ""

echo "[2] Проверка порта 8080..."
if netstat -tuln | grep -q ":8080 "; then
    echo "✓ Порт 8080 слушается"
    netstat -tuln | grep 8080
else
    echo "✗ Порт 8080 НЕ слушается - webhook не будет работать!"
    exit 1
fi
echo ""

echo "[3] Проверка .env настроек Robokassa..."
cd /opt/taxibot
if grep -q "ROBOKASSA_MERCHANT_LOGIN=kefpulse" .env; then
    echo "✓ ROBOKASSA_MERCHANT_LOGIN настроен"
else
    echo "✗ ROBOKASSA_MERCHANT_LOGIN не найден в .env"
fi

if grep -q "ROBOKASSA_PASSWORD1=" .env; then
    echo "✓ ROBOKASSA_PASSWORD1 настроен"
else
    echo "✗ ROBOKASSA_PASSWORD1 не найден в .env"
fi

if grep -q "PAYMENT_PROVIDER=robokassa" .env; then
    echo "✓ PAYMENT_PROVIDER=robokassa"
else
    echo "✗ PAYMENT_PROVIDER не установлен в robokassa"
fi
echo ""

echo "[4] Последние 10 строк логов..."
journalctl -u taxibot -n 10 --no-pager
echo ""

echo "════════════════════════════════════════════════════════════"
echo "  РЕЗУЛЬТАТ"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Если всё ✓ - переходи к настройке Robokassa:"
echo ""
echo "1. Открой: https://auth.robokassa.ru/"
echo "2. Магазин kefpulse → Технические настройки"
echo "3. БОЕВОЙ РЕЖИМ (не тестовый!)"
echo "4. Result URL: http://5.42.110.16:8080/webhook/robokassa/result"
echo "5. Метод: GET"
echo "6. Сохрани"
echo ""
echo "Потом тестовый платеж 5₽ в боте @KefPulse_bot"
echo ""
