#!/bin/bash
# Настройка домена для taxi-bot

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "Использование: bash setup_domain.sh your-domain.com"
    exit 1
fi

echo "🌐 Настройка домена: $DOMAIN"

# 1. Обновить .env
echo "📝 Обновление .env..."
sed -i "s|WEBAPP_URL=.*|WEBAPP_URL=http://$DOMAIN|g" /opt/taxibot/.env

# 2. Обновить Nginx конфиг
echo "📝 Обновление Nginx..."
sed -i "s|server_name .*;|server_name $DOMAIN;|g" /etc/nginx/sites-available/taxibot

# 3. Проверить конфиг
nginx -t

# 4. Перезапустить сервисы
echo "🔄 Перезапуск сервисов..."
systemctl reload nginx
systemctl restart taxibot

echo ""
echo "✅ Домен настроен!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Настройте DNS A-запись: $DOMAIN → $(curl -s ifconfig.me)"
echo "2. Подождите 5-10 минут пока DNS обновится"
echo "3. Установите SSL: bash /opt/taxibot/deploy/setup_ssl.sh $DOMAIN"
echo "4. Обновите URL в боте: /setwebapp https://$DOMAIN"
