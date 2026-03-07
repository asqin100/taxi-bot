#!/bin/bash
# Determine correct Robokassa URLs based on server configuration

echo "=== Определение правильных URL для Robokassa ==="
echo ""

SERVER_IP="5.42.110.16"

echo "Проверяем конфигурацию сервера..."
echo ""

# Test port 80
echo "1. Проверка порта 80 (nginx):"
if curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP/ | grep -q "200\|301\|302"; then
    echo "   ✅ Порт 80 доступен (nginx работает)"
    NGINX_WORKS=true
else
    echo "   ❌ Порт 80 недоступен"
    NGINX_WORKS=false
fi
echo ""

# Test port 8080
echo "2. Проверка порта 8080 (прямой доступ к боту):"
if curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP:8080/ | grep -q "200\|301\|302"; then
    echo "   ✅ Порт 8080 доступен"
    PORT_8080_WORKS=true
else
    echo "   ❌ Порт 8080 недоступен"
    PORT_8080_WORKS=false
fi
echo ""

# Test webhook through nginx
echo "3. Проверка webhook через nginx:"
NGINX_WEBHOOK=$(curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP/webhook/robokassa/success)
if [ "$NGINX_WEBHOOK" = "200" ]; then
    echo "   ✅ Webhook доступен через nginx (без порта)"
    NGINX_WEBHOOK_WORKS=true
else
    echo "   ❌ Webhook НЕ доступен через nginx (код: $NGINX_WEBHOOK)"
    NGINX_WEBHOOK_WORKS=false
fi
echo ""

# Test webhook direct
echo "4. Проверка webhook напрямую:"
DIRECT_WEBHOOK=$(curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP:8080/webhook/robokassa/success)
if [ "$DIRECT_WEBHOOK" = "200" ]; then
    echo "   ✅ Webhook доступен напрямую (с портом :8080)"
    DIRECT_WEBHOOK_WORKS=true
else
    echo "   ❌ Webhook НЕ доступен напрямую (код: $DIRECT_WEBHOOK)"
    DIRECT_WEBHOOK_WORKS=false
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 РЕКОМЕНДУЕМЫЕ URL ДЛЯ ROBOKASSA:"
echo ""

if [ "$NGINX_WEBHOOK_WORKS" = true ]; then
    echo "✅ Используйте URL БЕЗ порта (через nginx):"
    echo ""
    echo "Result URL:"
    echo "  http://$SERVER_IP/webhook/robokassa/result"
    echo ""
    echo "Success URL:"
    echo "  http://$SERVER_IP/webhook/robokassa/success"
    echo ""
    echo "Fail URL:"
    echo "  http://$SERVER_IP/webhook/robokassa/fail"
    echo ""
elif [ "$DIRECT_WEBHOOK_WORKS" = true ]; then
    echo "✅ Используйте URL С портом :8080 (прямой доступ):"
    echo ""
    echo "Result URL:"
    echo "  http://$SERVER_IP:8080/webhook/robokassa/result"
    echo ""
    echo "Success URL:"
    echo "  http://$SERVER_IP:8080/webhook/robokassa/success"
    echo ""
    echo "Fail URL:"
    echo "  http://$SERVER_IP:8080/webhook/robokassa/fail"
    echo ""
else
    echo "❌ ПРОБЛЕМА: Webhook недоступен ни через nginx, ни напрямую!"
    echo ""
    echo "Возможные причины:"
    echo "  1. Бот не запущен: sudo systemctl start taxibot"
    echo "  2. Порт 8080 закрыт файрволом"
    echo "  3. Nginx не настроен для проксирования webhook"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
