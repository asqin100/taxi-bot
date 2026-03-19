#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ ВСЕХ ПРОБЛЕМ"
echo "════════════════════════════════════════════════════════════"
echo ""

# 1. Проверка и открытие порта 8080 в firewall
echo "[1] Проверка firewall..."
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | grep -i "Status: active")
    if [ -n "$UFW_STATUS" ]; then
        echo "UFW активен, проверяю порт 8080..."
        if ! ufw status | grep -q "8080"; then
            echo "Открываю порт 8080..."
            ufw allow 8080/tcp
            echo "✓ Порт 8080 открыт"
        else
            echo "✓ Порт 8080 уже открыт"
        fi
    else
        echo "✓ UFW не активен"
    fi
else
    echo "✓ UFW не установлен"
fi

echo ""

# 2. Переключение в боевой режим
echo "[2] Переключение в боевой режим..."
systemctl stop taxibot

sed -i 's/ROBOKASSA_TEST_MODE=.*/ROBOKASSA_TEST_MODE=False/' /opt/taxibot/.env
sed -i 's/ROBOKASSA_PASSWORD1=.*/ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42/' /opt/taxibot/.env
sed -i 's/ROBOKASSA_PASSWORD2=.*/ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs/' /opt/taxibot/.env

echo "✓ Настройки обновлены"
echo ""

# 3. Запуск бота
echo "[3] Запуск бота..."
systemctl start taxibot
sleep 3

if systemctl is-active --quiet taxibot; then
    echo "✓ Бот запущен"
else
    echo "✗ Ошибка запуска бота"
    systemctl status taxibot --no-pager -l | tail -20
    exit 1
fi

echo ""

# 4. Тест webhook с правильной подписью
echo "[4] Тестирование webhook..."
echo ""

python3 << 'PYEOF'
import hashlib
import requests
from urllib.parse import urlencode

PASSWORD2 = "ED44A3KMHu6r7eGWhcGs"
OUT_SUM = 5.00
INV_ID = 1773005523
USER_ID = 244638301
TIER = "pro"
DURATION = 1

custom_params = {
    "Shp_duration": str(DURATION),
    "Shp_tier": TIER,
    "Shp_user_id": str(USER_ID)
}

sig_parts = [f"{OUT_SUM:.2f}", str(INV_ID), PASSWORD2]
for key in sorted(custom_params.keys()):
    sig_parts.append(f"{key}={custom_params[key]}")

signature = hashlib.md5(":".join(sig_parts).encode('utf-8')).hexdigest().upper()

params = {
    "OutSum": f"{OUT_SUM:.2f}",
    "InvId": INV_ID,
    "SignatureValue": signature,
    **custom_params
}

try:
    response = requests.get(f"http://127.0.0.1:8080/webhook/robokassa/result?{urlencode(params)}", timeout=10)

    if response.status_code == 200 and response.text.startswith("OK"):
        print("✅ WEBHOOK РАБОТАЕТ!")
        print(f"Ответ: {response.text}")
        print("\nПроверь бота @KefPulse_bot - должно прийти уведомление о подписке!")
    else:
        print(f"✗ Webhook вернул ошибку: {response.status_code} {response.text}")

except Exception as e:
    print(f"✗ Ошибка: {e}")

PYEOF

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  РЕЗУЛЬТАТ"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Если увидел ✅ WEBHOOK РАБОТАЕТ:"
echo "  → Проверь бота - должно прийти уведомление"
echo "  → Webhook работает локально"
echo "  → Проблема: Robokassa не вызывает Result URL"
echo "  → Решение: Проверь настройки Result URL в личном кабинете"
echo ""
echo "Если увидел ✗ ошибку:"
echo "  → Запусти: journalctl -u taxibot -f"
echo "  → Пришли логи"
echo ""
