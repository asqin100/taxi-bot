#!/bin/bash
# Update Robokassa passwords to production

echo "Обновляю пароли на боевые..."
echo ""

cd /opt/taxibot

# Backup
cp .env .env.backup.before_prod_passwords

# Update passwords
sed -i 's/ROBOKASSA_PASSWORD1=.*/ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42/g' .env
sed -i 's/ROBOKASSA_PASSWORD2=.*/ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs/g' .env

echo "✅ Пароли обновлены"
echo ""

echo "Новые настройки:"
grep "ROBOKASSA_MERCHANT_LOGIN\|ROBOKASSA_PASSWORD1\|ROBOKASSA_PASSWORD2\|ROBOKASSA_TEST_MODE" .env | head -4
echo ""

# Restart bot
echo "Перезапускаю бота..."
systemctl restart taxibot
sleep 3

if systemctl is-active --quiet taxibot; then
    echo "✅ Бот перезапущен с боевыми паролями"
else
    echo "❌ Ошибка перезапуска"
    systemctl status taxibot --no-pager -l | head -20
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Готово! Теперь попробуйте оплату в боте."
echo ""
echo "Бот теперь использует:"
echo "  - Боевые пароли Robokassa"
echo "  - Боевой режим (IsTest=0)"
echo ""
echo "Ошибка 29 должна исчезнуть!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
