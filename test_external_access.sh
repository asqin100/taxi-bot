#!/bin/bash
# Test if Robokassa can reach the webhook

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ПРОВЕРКА ДОСТУПНОСТИ WEBHOOK ДЛЯ ROBOKASSA            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 1. Check firewall
echo "1. Проверка файрвола (ufw):"
if command -v ufw &> /dev/null; then
    ufw status | grep -E "(Status|8080)"
    echo ""
    if ufw status | grep -q "8080.*ALLOW"; then
        echo "   ✅ Порт 8080 открыт в ufw"
    else
        echo "   ❌ Порт 8080 НЕ открыт в ufw!"
        echo ""
        echo "   РЕШЕНИЕ: Откройте порт 8080:"
        echo "   sudo ufw allow 8080/tcp"
        echo "   sudo ufw reload"
    fi
else
    echo "   ufw не установлен"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 2. Check iptables
echo "2. Проверка iptables:"
if iptables -L -n | grep -q "8080"; then
    echo "   Правила для порта 8080:"
    iptables -L -n | grep "8080"
else
    echo "   Нет специальных правил для порта 8080"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 3. Test from external service
echo "3. Тест доступности с внешнего сервиса:"
echo "   Проверяю через curl..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://5.42.110.16:8080/webhook/robokassa/result?test=1" 2>&1)
echo "   HTTP код: $RESPONSE"

if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "400" ]; then
    echo "   ✅ Webhook доступен извне"
elif [ "$RESPONSE" = "000" ]; then
    echo "   ❌ Таймаут - сервер недоступен из интернета!"
    echo ""
    echo "   Возможные причины:"
    echo "   - Порт 8080 закрыт файрволом"
    echo "   - Хостинг-провайдер блокирует входящие соединения"
    echo "   - Сервер за NAT без проброса портов"
else
    echo "   ⚠️  Неожиданный ответ: $RESPONSE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 4. Check if bot is listening
echo "4. Проверка, что бот слушает на 0.0.0.0:8080:"
netstat -tlnp | grep ":8080"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "РЕКОМЕНДАЦИИ:"
echo ""

if [ "$RESPONSE" != "200" ] && [ "$RESPONSE" != "400" ]; then
    echo "❌ Webhook НЕДОСТУПЕН из интернета!"
    echo ""
    echo "Robokassa не может вызвать ваш Result URL."
    echo ""
    echo "РЕШЕНИЕ 1: Откройте порт 8080 в файрволе"
    echo "  sudo ufw allow 8080/tcp"
    echo "  sudo ufw reload"
    echo ""
    echo "РЕШЕНИЕ 2: Используйте nginx как прокси"
    echo "  Настройте nginx для проксирования /webhook/* на localhost:8080"
    echo "  И используйте URL без порта: http://5.42.110.16/webhook/robokassa/result"
else
    echo "✅ Webhook доступен!"
    echo ""
    echo "Если платежи все равно не работают:"
    echo ""
    echo "1. Убедитесь, что нажали 'Сохранить' в Robokassa"
    echo "2. Подождите 1-2 минуты после сохранения"
    echo "3. Сделайте НОВЫЙ тестовый платеж"
    echo "4. Запустите мониторинг: bash monitor_webhook.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
