#!/bin/bash
# Настройка SSL сертификата для домена
# Использование: bash setup_ssl.sh your-domain.com

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}❌ Укажите домен${NC}"
    echo "Использование: bash setup_ssl.sh your-domain.com"
    exit 1
fi

DOMAIN=$1

echo "=========================================="
echo "  🔒 НАСТРОЙКА SSL ДЛЯ $DOMAIN"
echo "=========================================="
echo ""

# Проверка DNS
echo -e "${YELLOW}[1/5] Проверка DNS записи...${NC}"
DOMAIN_IP=$(dig +short $DOMAIN | tail -1)
SERVER_IP=$(curl -s ifconfig.me)

if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo -e "${RED}❌ DNS не настроен правильно!${NC}"
    echo "  Домен указывает на: $DOMAIN_IP"
    echo "  IP сервера:         $SERVER_IP"
    echo ""
    echo "Настройте A-запись в DNS:"
    echo "  $DOMAIN → $SERVER_IP"
    exit 1
fi

echo -e "${GREEN}✅ DNS настроен правильно${NC}"

# Обновление Nginx конфига
echo -e "${YELLOW}[2/5] Обновление Nginx конфигурации...${NC}"
sed -i "s/server_name .*/server_name $DOMAIN;/" /etc/nginx/sites-available/taxibot
nginx -t && systemctl reload nginx

# Установка Certbot (если не установлен)
echo -e "${YELLOW}[3/5] Проверка Certbot...${NC}"
if ! command -v certbot &> /dev/null; then
    apt install -y certbot python3-certbot-nginx
fi

# Получение SSL сертификата
echo -e "${YELLOW}[4/5] Получение SSL сертификата...${NC}"
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --register-unsafely-without-email

# Настройка автообновления
echo -e "${YELLOW}[5/5] Настройка автообновления сертификата...${NC}"
systemctl enable certbot.timer
systemctl start certbot.timer

echo ""
echo -e "${GREEN}=========================================="
echo -e "  ✅ SSL НАСТРОЕН!"
echo -e "==========================================${NC}"
echo ""
echo "Ваш сайт доступен по адресу:"
echo "  https://$DOMAIN"
echo ""
echo "Обновите WebApp URL в боте:"
echo "  /setwebapp https://$DOMAIN"
echo ""
echo "Сертификат будет автоматически обновляться."
echo "Проверка обновления: sudo certbot renew --dry-run"
echo ""
