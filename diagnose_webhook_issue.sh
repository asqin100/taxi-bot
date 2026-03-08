#!/bin/bash
# Check if Result URL is accessible and check yesterday's logs

echo "1. Проверяю доступность Result URL извне..."
echo ""

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://5.42.110.16:8080/webhook/robokassa/result?test=1")
echo "HTTP код: $RESPONSE"

if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "400" ]; then
    echo "✅ Result URL доступен извне"
else
    echo "❌ Result URL НЕДОСТУПЕН извне! (код: $RESPONSE)"
    echo ""
    echo "Robokassa не может достучаться до вашего сервера!"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2. Проверяю логи за последние 24 часа (поиск Robokassa):"
echo ""
journalctl -u taxibot --since "24 hours ago" | grep -i "robokassa" | tail -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3. Проверяю все логи за вчерашний вечер (18:00-23:59):"
echo ""
journalctl -u taxibot --since "yesterday 18:00" --until "yesterday 23:59" | tail -50

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "ДИАГНОСТИКА:"
echo ""

if [ "$RESPONSE" != "200" ] && [ "$RESPONSE" != "400" ]; then
    echo "❌ ПРОБЛЕМА: Result URL недоступен из интернета!"
    echo ""
    echo "Robokassa не может вызвать ваш webhook."
    echo ""
    echo "РЕШЕНИЕ:"
    echo "  1. Проверьте файрвол: ufw status"
    echo "  2. Откройте порт 8080: ufw allow 8080/tcp"
    echo "  3. Или настройте nginx для проксирования webhook"
else
    echo "✅ Result URL доступен"
    echo ""
    echo "Если в логах нет запросов от Robokassa, значит:"
    echo "  1. Result URL не сохранен в настройках Robokassa"
    echo "  2. Или Robokassa использует другой URL"
    echo ""
    echo "Проверьте в личном кабинете Robokassa:"
    echo "  Result URL должен быть: http://5.42.110.16:8080/webhook/robokassa/result"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
