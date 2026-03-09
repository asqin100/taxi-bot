#!/bin/bash
# Fix ngrok expiration - switch to server IP

echo "Обновляем WEBAPP_URL на IP сервера..."

cd /opt/taxibot || exit 1

# Update WEBAPP_URL in .env
sed -i 's|WEBAPP_URL=.*|WEBAPP_URL=http://5.42.110.16:8080|g' .env

echo "Проверяем изменения:"
grep WEBAPP_URL .env

echo ""
echo "Перезапускаем бота..."
systemctl restart taxibot

echo ""
echo "Готово! Карта теперь работает на http://5.42.110.16:8080"
echo "Ngrok больше не нужен - используем прямой IP сервера"
