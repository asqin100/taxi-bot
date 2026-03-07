#!/bin/bash
# Простое решение - запустить с текущим кодом

echo "Перезапускаю бота..."
systemctl restart taxibot
sleep 3

echo ""
echo "Проверяю статус бота..."
if systemctl is-active --quiet taxibot; then
    echo "✅ Бот работает"
else
    echo "❌ Бот не запущен"
    systemctl status taxibot --no-pager -l
    exit 1
fi

echo ""
echo "Определяю правильные URL для Robokassa..."
echo ""

# Test without port
RESPONSE1=$(curl -s -o /dev/null -w "%{http_code}" http://5.42.110.16/webhook/robokassa/success 2>/dev/null)
echo "Тест без порта: код $RESPONSE1"

# Test with port
RESPONSE2=$(curl -s -o /dev/null -w "%{http_code}" http://5.42.110.16:8080/webhook/robokassa/success 2>/dev/null)
echo "Тест с портом :8080: код $RESPONSE2"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$RESPONSE1" = "200" ]; then
    echo "✅ ИСПОЛЬЗУЙТЕ ЭТИ URL В ROBOKASSA:"
    echo ""
    echo "Result URL:"
    echo "  http://5.42.110.16/webhook/robokassa/result"
    echo ""
    echo "Success URL:"
    echo "  http://5.42.110.16/webhook/robokassa/success"
    echo ""
    echo "Fail URL:"
    echo "  http://5.42.110.16/webhook/robokassa/fail"
elif [ "$RESPONSE2" = "200" ]; then
    echo "✅ ИСПОЛЬЗУЙТЕ ЭТИ URL В ROBOKASSA:"
    echo ""
    echo "Result URL:"
    echo "  http://5.42.110.16:8080/webhook/robokassa/result"
    echo ""
    echo "Success URL:"
    echo "  http://5.42.110.16:8080/webhook/robokassa/success"
    echo ""
    echo "Fail URL:"
    echo "  http://5.42.110.16:8080/webhook/robokassa/fail"
else
    echo "❌ ОШИБКА: Webhook недоступен!"
    echo ""
    echo "Проверьте:"
    echo "  netstat -tlnp | grep 8080"
    echo "  journalctl -u taxibot -n 20"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
