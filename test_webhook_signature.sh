#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ТЕСТ RESULT URL С ПРАВИЛЬНОЙ ПОДПИСЬЮ"
echo "════════════════════════════════════════════════════════════"
echo ""

cd /opt/taxibot

# Создаём временный Python скрипт
cat > /tmp/test_robokassa.py << 'PYEOF'
import hashlib
import requests
from urllib.parse import urlencode

# Боевые настройки
MERCHANT_LOGIN = "kefpulse"
PASSWORD2 = "ED44A3KMHu6r7eGWhcGs"

# Данные последнего платежа
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

# Вычисляем подпись
sig_parts = [
    f"{OUT_SUM:.2f}",
    str(INV_ID),
    PASSWORD2
]

for key in sorted(custom_params.keys()):
    sig_parts.append(f"{key}={custom_params[key]}")

sig_string = ":".join(sig_parts)
print(f"Строка подписи: {sig_string}")

signature = hashlib.md5(sig_string.encode('utf-8')).hexdigest().upper()
print(f"Подпись: {signature}\n")

params = {
    "OutSum": f"{OUT_SUM:.2f}",
    "InvId": INV_ID,
    "SignatureValue": signature,
    **custom_params
}

result_url = f"http://127.0.0.1:8080/webhook/robokassa/result?{urlencode(params)}"

print("="*60)
print("ТЕСТИРОВАНИЕ RESULT URL")
print("="*60)
print(f"\nURL: {result_url}\n")

try:
    response = requests.get(result_url, timeout=10)
    print(f"Статус: {response.status_code}")
    print(f"Ответ: {response.text}\n")

    if response.status_code == 200 and response.text.startswith("OK"):
        print("✅ SUCCESS! Webhook работает!")
        print("Проверь бота - должно прийти уведомление.")
    else:
        print("❌ FAILED! Webhook вернул ошибку.")
        print("Смотри логи: journalctl -u taxibot -f")

except Exception as e:
    print(f"❌ ERROR: {e}")
    print("Проверь что бот запущен: systemctl status taxibot")

print("="*60)
PYEOF

echo "Запускаю тест..."
echo ""

python3 /tmp/test_robokassa.py

echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Если увидел ✅ SUCCESS - проверь бота, должно прийти уведомление!"
echo "Если ❌ FAILED - запусти: journalctl -u taxibot -f"
echo ""
