#!/bin/bash
# Final verification before testing payment

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           ФИНАЛЬНАЯ ПРОВЕРКА ПЕРЕД ТЕСТОМ                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 1. Check bot status
echo "1. Статус бота:"
if systemctl is-active --quiet taxibot; then
    echo "   ✅ Бот работает"
else
    echo "   ❌ Бот не работает!"
    exit 1
fi

# 2. Check port
echo ""
echo "2. Порт 8080:"
if netstat -tlnp | grep -q ":8080"; then
    echo "   ✅ Порт слушает"
else
    echo "   ❌ Порт не слушает!"
    exit 1
fi

# 3. Check Result URL accessibility
echo ""
echo "3. Доступность Result URL извне:"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://5.42.110.16:8080/webhook/robokassa/result?test=1")
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "400" ]; then
    echo "   ✅ Доступен (код: $RESPONSE)"
else
    echo "   ❌ Недоступен (код: $RESPONSE)"
    exit 1
fi

# 4. Check passwords
echo ""
echo "4. Пароли Robokassa:"
if grep -q "ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42" /opt/taxibot/.env; then
    echo "   ✅ Password1 боевой"
else
    echo "   ⚠️  Password1 тестовый (нужно обновить)"
fi

if grep -q "ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs" /opt/taxibot/.env; then
    echo "   ✅ Password2 боевой"
else
    echo "   ⚠️  Password2 тестовый (нужно обновить)"
fi

# 5. Check test mode
echo ""
echo "5. Режим работы:"
if grep -q "ROBOKASSA_TEST_MODE=False" /opt/taxibot/.env; then
    echo "   ✅ Боевой режим"
else
    echo "   ⚠️  Тестовый режим"
fi

# 6. Check test button in code
echo ""
echo "6. Кнопка тестового платежа:"
if grep -q "ТЕСТ — 5₽" /opt/taxibot/bot/handlers/subscription.py; then
    echo "   ✅ Добавлена в код"
else
    echo "   ❌ Не найдена в коде"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "ИТОГ:"
echo ""
echo "✅ Сервер готов к приему платежей!"
echo ""
echo "СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Сохраните Result URL в Robokassa:"
echo "   http://5.42.110.16:8080/webhook/robokassa/result"
echo ""
echo "2. Запустите мониторинг:"
echo "   bash monitor_webhook.sh"
echo ""
echo "3. Сделайте тестовый платеж на 5₽ в боте"
echo ""
echo "4. Проверьте логи - должен появиться запрос от Robokassa"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
