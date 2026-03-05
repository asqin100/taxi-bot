#!/bin/bash
# Продолжение установки после ошибки миграции

echo "🔧 Продолжаем установку сервисов..."

# Копируем systemd сервисы
cp /opt/taxibot/deploy/taxibot.service /etc/systemd/system/
cp /opt/taxibot/deploy/taxibot-web.service /etc/systemd/system/

# Перезагружаем systemd
systemctl daemon-reload

# Включаем автозапуск
systemctl enable taxibot taxibot-web

# Запускаем сервисы
systemctl start taxibot taxibot-web

# Настраиваем Nginx
cp /opt/taxibot/deploy/nginx-taxibot.conf /etc/nginx/sites-available/taxibot
ln -sf /etc/nginx/sites-available/taxibot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверяем конфиг Nginx
nginx -t && systemctl restart nginx

# Настраиваем firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo ""
echo "✅ Установка завершена!"
echo ""
echo "Проверьте статус:"
echo "  systemctl status taxibot"
echo "  systemctl status taxibot-web"
