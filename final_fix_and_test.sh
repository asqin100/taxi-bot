#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ПРОВЕРКА И ИСПРАВЛЕНИЕ НАСТРОЕК"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Текущие настройки .env:"
echo "────────────────────────────────────────────────────────────"
grep "ROBOKASSA" /opt/taxibot/.env
echo ""

echo "[2] Переключаю в БОЕВОЙ режим с БОЕВЫМИ паролями..."
systemctl stop taxibot

sed -i 's/ROBOKASSA_TEST_MODE=.*/ROBOKASSA_TEST_MODE=False/' /opt/taxibot/.env
sed -i 's/ROBOKASSA_PASSWORD1=.*/ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42/' /opt/taxibot/.env
sed -i 's/ROBOKASSA_PASSWORD2=.*/ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs/' /opt/taxibot/.env

echo ""
echo "[3] Новые настройки:"
echo "────────────────────────────────────────────────────────────"
grep "ROBOKASSA" /opt/taxibot/.env
echo ""

echo "[4] Запускаю бота..."
systemctl start taxibot
sleep 3

echo ""
echo "[5] Тестирую webhook с БОЕВЫМИ паролями..."
echo ""

python3 << 'PYEOF'
import hashlib
import requests
from urllib.parse import urlencode
import time

PASSWORD2 = "ED44A3KMHu6r7eGWhcGs"  # БОЕВОЙ пароль 2
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

print(f"Подпись: {signature}")
print("")

# Даём боту время запуститься
time.sleep(2)

try:
    response = requests.get(f"http://127.0.0.1:8080/webhook/robokassa/result?{urlencode(params)}", timeout=10)

    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.text}")
    print("")

    if response.status_code == 200 and response.text.startswith("OK"):
        print("✅ WEBHOOK РАБОТАЕТ!")
        print("")
        print("Проверь @KefPulse_bot - должно прийти уведомление:")
        print("✅ Подписка активирована!")
    else:
        print("✗ Webhook вернул ошибку")
        print("Смотри логи: journalctl -u taxibot -n 20")

except Exception as e:
    print(f"✗ Ошибка: {e}")

PYEOF

echo ""
echo "════════════════════════════════════════════════════════════"
