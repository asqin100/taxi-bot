#!/bin/bash
# Deploy test payment feature and update passwords

echo "Разворачиваю тестовый платеж на 5₽..."
echo ""

cd /opt/taxibot

# Pull latest code
echo "1. Обновляю код..."
git pull origin main

# Update passwords to production if not already done
echo ""
echo "2. Обновляю пароли на боевые..."
sed -i 's/ROBOKASSA_PASSWORD1=i9MBFKM8C2j1E4rBZYNU/ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42/g' .env
sed -i 's/ROBOKASSA_PASSWORD2=mrjNy9n8xNuX1BAEq4Q8/ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs/g' .env

# Remove duplicates
echo ""
echo "3. Удаляю дубликаты в .env..."
awk '!seen[$0]++' .env > .env.tmp && mv .env.tmp .env

# Restart bot
echo ""
echo "4. Перезапускаю бота..."
systemctl restart taxibot
sleep 3

if systemctl is-active --quiet taxibot; then
    echo "✅ Бот перезапущен"
else
    echo "❌ Ошибка перезапуска"
    systemctl status taxibot --no-pager -l | head -20
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Готово! Тестовый платеж добавлен."
echo ""
echo "Теперь в боте появилась кнопка:"
echo "  🧪 ТЕСТ — 5₽ (1 день)"
echo ""
echo "Эта кнопка даст Pro подписку на 1 день за 5 рублей."
echo "Используйте её для проверки реальных платежей."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
