#!/bin/bash
# Test if Result URL is accessible from internet and returns correct format

echo "Проверяю доступность Result URL из интернета..."
echo ""

# Test from external service
echo "1. Тест доступности с внешнего сервера:"
curl -s "https://ifconfig.me/forwarded" 2>/dev/null || echo "Внешний IP недоступен"
echo ""

# Test local webhook
echo "2. Тест локального webhook:"
RESPONSE=$(curl -s "http://localhost:8080/webhook/robokassa/result?OutSum=299&InvId=12345&SignatureValue=test&Shp_user_id=123&Shp_tier=pro&Shp_duration=30")
echo "Ответ: $RESPONSE"
echo ""

# Test external webhook
echo "3. Тест внешнего webhook:"
RESPONSE=$(curl -s "http://5.42.110.16:8080/webhook/robokassa/result?OutSum=299&InvId=12345&SignatureValue=test&Shp_user_id=123&Shp_tier=pro&Shp_duration=30")
echo "Ответ: $RESPONSE"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Ожидаемый ответ: ERROR (т.к. подпись неверная)"
echo "Если получен ERROR - endpoint работает правильно!"
echo ""
echo "Для реального платежа Robokassa должен получить: OK{InvId}"
echo "где {InvId} - номер счета"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
