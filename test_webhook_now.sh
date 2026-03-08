#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ТЕСТ WEBHOOK (БОТ УЖЕ ЗАПУЩЕН)"
echo "════════════════════════════════════════════════════════════"
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

print(f"Подпись: {signature}")
print(f"URL: http://127.0.0.1:8080/webhook/robokassa/result")
print("")

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
        print("Тариф: ⭐ Pro")
        print("Сумма: 5₽")
    else:
        print("✗ Webhook вернул ошибку")

except Exception as e:
    print(f"✗ Ошибка: {e}")

PYEOF

echo ""
echo "════════════════════════════════════════════════════════════"
