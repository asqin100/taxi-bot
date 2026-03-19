#!/bin/bash
# Быстрый деплой - все в одном скрипте
# Использование: bash quick_deploy.sh

set -e

echo "=========================================="
echo "  🚀 БЫСТРОЕ РАЗВЕРТЫВАНИЕ TAXI BOT"
echo "=========================================="
echo ""

# Проверка root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите с sudo: sudo bash quick_deploy.sh"
    exit 1
fi

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Запрос данных
echo -e "${YELLOW}Введите данные для настройки:${NC}"
read -p "BOT_TOKEN (от @BotFather): " BOT_TOKEN
read -p "ADMIN_ID (ваш Telegram ID): " ADMIN_ID
read -p "YANDEX_API_KEY: " YANDEX_KEY
read -sp "Пароль для PostgreSQL: " DB_PASSWORD
echo ""

# Шаг 1: Базовая установка
echo -e "${YELLOW}[1/5] Установка системных пакетов...${NC}"
apt update && apt upgrade -y
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip \
    postgresql postgresql-contrib nginx redis-server \
    git curl wget htop nano certbot python3-certbot-nginx

# Шаг 2: Создание пользователя
echo -e "${YELLOW}[2/5] Создание пользователя taxibot...${NC}"
if ! id -u taxibot > /dev/null 2>&1; then
    useradd -m -s /bin/bash taxibot
fi
mkdir -p /opt/taxibot /var/log/taxibot
chown -R taxibot:taxibot /opt/taxibot /var/log/taxibot

# Шаг 3: Настройка PostgreSQL
echo -e "${YELLOW}[3/5] Настройка PostgreSQL...${NC}"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS taxibot_db;" 2>/dev/null || true
sudo -u postgres psql -c "DROP USER IF EXISTS taxibot;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER taxibot WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE taxibot_db OWNER taxibot;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE taxibot_db TO taxibot;"

# Шаг 4: Копирование файлов (предполагается, что код уже загружен)
echo -e "${YELLOW}[4/5] Настройка приложения...${NC}"
cd /opt/taxibot

# Создание venv
sudo -u taxibot python3.11 -m venv venv
sudo -u taxibot /opt/taxibot/venv/bin/pip install --upgrade pip
sudo -u taxibot /opt/taxibot/venv/bin/pip install -r requirements.txt

# Создание .env
cat > /opt/taxibot/.env << EOF
BOT_TOKEN=$BOT_TOKEN
BOT_USERNAME=KefPulse_bot
ADMIN_IDS=$ADMIN_ID

DATABASE_URL=postgresql+asyncpg://taxibot:$DB_PASSWORD@localhost/taxibot_db

YANDEX_API_KEY=$YANDEX_KEY

WEB_HOST=0.0.0.0
WEB_PORT=8080

REDIS_URL=redis://localhost:6379/0

ENVIRONMENT=production
EOF

chown taxibot:taxibot /opt/taxibot/.env
chmod 600 /opt/taxibot/.env

# Миграция БД
if [ -f "deploy/migrate_to_postgres.py" ]; then
    sudo -u taxibot /opt/taxibot/venv/bin/python deploy/migrate_to_postgres.py
fi

# Шаг 5: Настройка сервисов
echo -e "${YELLOW}[5/5] Настройка systemd и Nginx...${NC}"

# Systemd сервисы
cp deploy/taxibot.service /etc/systemd/system/
cp deploy/taxibot-web.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable taxibot taxibot-web
systemctl start taxibot taxibot-web

# Nginx
cp deploy/nginx-taxibot.conf /etc/nginx/sites-available/taxibot
ln -sf /etc/nginx/sites-available/taxibot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo ""
echo -e "${GREEN}=========================================="
echo -e "  ✅ РАЗВЕРТЫВАНИЕ ЗАВЕРШЕНО!"
echo -e "==========================================${NC}"
echo ""
echo "Проверьте статус:"
echo "  sudo systemctl status taxibot"
echo "  sudo systemctl status taxibot-web"
echo ""
echo "Логи:"
echo "  tail -f /var/log/taxibot/bot.log"
echo ""
echo "Обновите WebApp URL в боте:"
echo "  /setwebapp http://$(curl -s ifconfig.me)"
echo ""
