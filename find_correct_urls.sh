#!/bin/bash
# Quick diagnostic - run this on server to get correct Robokassa URLs

echo "Проверяю конфигурацию..."
echo ""

# Test without port (nginx)
echo "Тест 1: http://5.42.110.16/webhook/robokassa/success"
RESPONSE1=$(curl -s -o /dev/null -w "%{http_code}" http://5.42.110.16/webhook/robokassa/success 2>/dev/null)
echo "Код ответа: $RESPONSE1"
echo ""

# Test with port (direct)
echo "Тест 2: http://5.42.110.16:8080/webhook/robokassa/success"
RESPONSE2=$(curl -s -o /dev/null -w "%{http_code}" http://5.42.110.16:8080/webhook/robokassa/success 2>/dev/null)
echo "Код ответа: $RESPONSE2"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$RESPONSE1" = "200" ]; then
    echo "✅ ИСПОЛЬЗУЙТЕ URL БЕЗ ПОРТА:"
    echo ""
    echo "Result URL:  http://5.42.110.16/webhook/robokassa/result"
    echo "Success URL: http://5.42.110.16/webhook/robokassa/success"
    echo "Fail URL:    http://5.42.110.16/webhook/robokassa/fail"
elif [ "$RESPONSE2" = "200" ]; then
    echo "✅ ИСПОЛЬЗУЙТЕ URL С ПОРТОМ :8080:"
    echo ""
    echo "Result URL:  http://5.42.110.16:8080/webhook/robokassa/result"
    echo "Success URL: http://5.42.110.16:8080/webhook/robokassa/success"
    echo "Fail URL:    http://5.42.110.16:8080/webhook/robokassa/fail"
else
    echo "❌ ОШИБКА: Webhook недоступен!"
    echo ""
    echo "Проверьте:"
    echo "  sudo systemctl status taxibot"
    echo "  netstat -tlnp | grep 8080"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
