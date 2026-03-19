#!/bin/bash
# Fix ngrok expiration - switch to domain

echo "Обновляем WEBAPP_URL на домен kefpulse.ru..."

cd /opt/taxibot || exit 1

# Update WEBAPP_URL in .env
sed -i 's|WEBAPP_URL=.*|WEBAPP_URL=https://kefpulse.ru|g' .env

echo "Проверяем изменения:"
grep WEBAPP_URL .env

echo ""
echo "Перезапускаем бота..."
systemctl restart taxibot

echo ""
echo "Готово! Карта теперь работает на https://kefpulse.ru"
