#!/bin/bash
# Test payment after saving Robokassa settings

echo "Проверяю настройки после сохранения..."
echo ""

# Check bot status
echo "1. Статус бота:"
systemctl is-active taxibot && echo "✅ Работает" || echo "❌ Не работает"
echo ""

# Check current settings
echo "2. Текущий режим:"
grep ROBOKASSA_TEST_MODE /opt/taxibot/.env
echo ""

# Test Result URL
echo "3. Тест Result URL:"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://5.42.110.16:8080/webhook/robokassa/result?OutSum=299&InvId=123&SignatureValue=test&Shp_user_id=123&Shp_tier=pro&Shp_duration=30")
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "400" ]; then
    echo "✅ Endpoint доступен (код: $RESPONSE)"
else
    echo "❌ Endpoint недоступен (код: $RESPONSE)"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Теперь попробуйте оплату в боте:"
echo "  1. Откройте @KefPulse_bot"
echo "  2. Выберите подписку"
echo "  3. Нажмите 'Оплатить картой'"
echo ""
echo "Если ошибка 29 исчезла - все работает!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
