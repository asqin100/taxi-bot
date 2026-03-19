#!/bin/bash
# Switch Robokassa to production mode

echo "Переключаю Robokassa в режим реальных платежей..."
echo ""

cd /opt/taxibot

# Backup .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update ROBOKASSA_TEST_MODE to False
sed -i 's/ROBOKASSA_TEST_MODE=True/ROBOKASSA_TEST_MODE=False/g' .env
sed -i 's/ROBOKASSA_TEST_MODE=true/ROBOKASSA_TEST_MODE=False/g' .env

echo "✅ Настройки обновлены"
echo ""

# Show current setting
echo "Текущие настройки Robokassa:"
grep ROBOKASSA .env | grep -v PASSWORD
echo ""

# Restart bot
echo "Перезапускаю бота..."
systemctl restart taxibot
sleep 3

if systemctl is-active --quiet taxibot; then
    echo "✅ Бот перезапущен в режиме реальных платежей"
else
    echo "❌ Ошибка при перезапуске бота"
    systemctl status taxibot --no-pager -l
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️ ВАЖНО: Теперь используются РЕАЛЬНЫЕ платежи!"
echo ""
echo "URL для Robokassa остаются те же:"
echo "  Result URL:  http://5.42.110.16:8080/webhook/robokassa/result"
echo "  Success URL: http://5.42.110.16:8080/webhook/robokassa/success"
echo "  Fail URL:    http://5.42.110.16:8080/webhook/robokassa/fail"
echo ""
echo "Теперь можно принимать реальные платежи!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
