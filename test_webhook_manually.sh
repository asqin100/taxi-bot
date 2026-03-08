#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  РУЧНОЙ ТЕСТ WEBHOOK (для проверки что бот работает)"
echo "════════════════════════════════════════════════════════════"
echo ""

# Test parameters
OUT_SUM="5.00"
INV_ID=$(date +%s)
PASSWORD2="ED44A3KMHu6r7eGWhcGs"
USER_ID="244638301"
TIER="pro"
DURATION="1"

# Calculate signature: MD5(OutSum:InvId:Password2:Shp_duration=1:Shp_tier=pro:Shp_user_id=244638301)
SIG_STRING="${OUT_SUM}:${INV_ID}:${PASSWORD2}:Shp_duration=${DURATION}:Shp_tier=${TIER}:Shp_user_id=${USER_ID}"
SIGNATURE=$(echo -n "$SIG_STRING" | md5sum | awk '{print toupper($1)}')

echo "Тестовые параметры:"
echo "  OutSum: $OUT_SUM"
echo "  InvId: $INV_ID"
echo "  Signature: $SIGNATURE"
echo ""

# Make request
URL="http://127.0.0.1:8080/webhook/robokassa/result?OutSum=${OUT_SUM}&InvId=${INV_ID}&SignatureValue=${SIGNATURE}&Shp_user_id=${USER_ID}&Shp_tier=${TIER}&Shp_duration=${DURATION}"

echo "Отправка запроса к боту..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$URL")
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE:")

echo ""
echo "Ответ бота:"
echo "  HTTP код: $HTTP_CODE"
echo "  Тело: $BODY"
echo ""

if [ "$HTTP_CODE" = "200" ] && [[ "$BODY" == OK* ]]; then
    echo "✅ WEBHOOK РАБОТАЕТ!"
    echo ""
    echo "Проверь логи:"
    echo "journalctl -u taxibot -n 30 --no-pager | grep -A 5 'Processing payment result'"
else
    echo "❌ ОШИБКА!"
    echo ""
    echo "Проверь логи для деталей:"
    echo "journalctl -u taxibot -n 50 --no-pager | tail -30"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
