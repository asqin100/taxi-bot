#!/bin/bash
# Switch back to test mode

echo "Возвращаю в тестовый режим..."
echo ""

cd /opt/taxibot

# Switch back to test mode
sed -i 's/ROBOKASSA_TEST_MODE=False/ROBOKASSA_TEST_MODE=True/g' .env
sed -i 's/ROBOKASSA_TEST_MODE=false/ROBOKASSA_TEST_MODE=True/g' .env

echo "✅ Переключено на тестовый режим"
echo ""

# Restart bot
systemctl restart taxibot
sleep 3

if systemctl is-active --quiet taxibot; then
    echo "✅ Бот перезапущен"
else
    echo "❌ Ошибка перезапуска"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Бот снова в тестовом режиме"
echo ""
echo "Теперь можно тестировать картой: 5555 5555 5555 5599"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
