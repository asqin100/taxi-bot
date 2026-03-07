#!/bin/bash
# Comprehensive test of Result URL accessibility

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     ПРОВЕРКА ДОСТУПНОСТИ RESULT URL ДЛЯ ROBOKASSA         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Check if bot is running
echo "1. Проверка статуса бота:"
if systemctl is-active --quiet taxibot; then
    echo "   ✅ Бот работает"
else
    echo "   ❌ Бот не работает!"
    exit 1
fi
echo ""

# Test 2: Check if port 8080 is listening
echo "2. Проверка порта 8080:"
if netstat -tlnp | grep -q ":8080"; then
    echo "   ✅ Порт 8080 слушает"
else
    echo "   ❌ Порт 8080 не слушает!"
    exit 1
fi
echo ""

# Test 3: Test from localhost
echo "3. Тест с localhost:"
RESPONSE=$(curl -s "http://localhost:8080/webhook/robokassa/result?OutSum=299&InvId=12345&SignatureValue=test&Shp_user_id=123&Shp_tier=pro&Shp_duration=30")
echo "   Ответ: $RESPONSE"
if [ -n "$RESPONSE" ]; then
    echo "   ✅ Endpoint отвечает"
else
    echo "   ❌ Endpoint не отвечает"
fi
echo ""

# Test 4: Test from external IP
echo "4. Тест с внешнего IP (5.42.110.16):"
RESPONSE=$(curl -s "http://5.42.110.16:8080/webhook/robokassa/result?OutSum=299&InvId=12345&SignatureValue=test&Shp_user_id=123&Shp_tier=pro&Shp_duration=30")
echo "   Ответ: $RESPONSE"
if [ -n "$RESPONSE" ]; then
    echo "   ✅ Доступен извне"
else
    echo "   ❌ Недоступен извне!"
fi
echo ""

# Test 5: Check firewall
echo "5. Проверка файрвола:"
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(ufw status | grep "8080")
    if [ -n "$UFW_STATUS" ]; then
        echo "   Правила UFW для порта 8080:"
        echo "   $UFW_STATUS"
    else
        echo "   ⚠️  Порт 8080 не открыт в UFW"
    fi
else
    echo "   UFW не установлен"
fi
echo ""

# Test 6: Test Success URL
echo "6. Тест Success URL:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://5.42.110.16:8080/webhook/robokassa/success")
echo "   HTTP код: $HTTP_CODE"
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Success URL работает"
else
    echo "   ❌ Success URL не работает"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "РЕЗУЛЬТАТ:"
echo ""

if [ "$RESPONSE" = "ERROR" ]; then
    echo "✅ Result URL доступен и отвечает правильно!"
    echo ""
    echo "Ошибка 29 может быть из-за:"
    echo "  1. Robokassa не может достучаться до вашего сервера"
    echo "  2. Нужно добавить IP Robokassa в whitelist"
    echo "  3. Robokassa делает проверочный запрос с другими параметрами"
    echo ""
    echo "РЕШЕНИЕ: Попробуйте сделать тестовый платеж и проверьте логи:"
    echo "  journalctl -u taxibot -f"
elif [ -z "$RESPONSE" ]; then
    echo "❌ Result URL недоступен извне!"
    echo ""
    echo "Возможные причины:"
    echo "  1. Порт 8080 закрыт файрволом"
    echo "  2. Nginx не проксирует запросы"
    echo "  3. Сервер недоступен из интернета"
    echo ""
    echo "РЕШЕНИЕ: Откройте порт 8080:"
    echo "  ufw allow 8080/tcp"
    echo "  ufw reload"
else
    echo "⚠️  Неожиданный ответ: $RESPONSE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
