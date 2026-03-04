#!/bin/bash
# Автоматическое развертывание Taxi Bot на Ubuntu 22.04
# Использование: sudo bash deploy.sh

set -e  # Остановка при ошибке

echo "=========================================="
echo "  🚕 TAXI BOT - РАЗВЕРТЫВАНИЕ НА VPS"
echo "=========================================="
echo ""

# Проверка root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Запустите скрипт с sudo"
    exit 1
fi

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[1/10] Обновление системы...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}[2/10] Установка Python 3.11...${NC}"
apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

echo -e "${YELLOW}[3/10] Установка PostgreSQL...${NC}"
apt install -y postgresql postgresql-contrib

echo -e "${YELLOW}[4/10] Установка Nginx...${NC}"
apt install -y nginx

echo -e "${YELLOW}[5/10] Установка Redis...${NC}"
apt install -y redis-server

echo -e "${YELLOW}[6/10] Установка дополнительных пакетов...${NC}"
apt install -y git curl wget htop nano certbot python3-certbot-nginx

echo -e "${YELLOW}[7/10] Создание пользователя taxibot...${NC}"
if ! id -u taxibot > /dev/null 2>&1; then
    useradd -m -s /bin/bash taxibot
    echo -e "${GREEN}✅ Пользователь taxibot создан${NC}"
else
    echo -e "${GREEN}✅ Пользователь taxibot уже существует${NC}"
fi

echo -e "${YELLOW}[8/10] Создание директорий...${NC}"
mkdir -p /opt/taxibot
mkdir -p /var/log/taxibot
chown -R taxibot:taxibot /opt/taxibot
chown -R taxibot:taxibot /var/log/taxibot

echo -e "${YELLOW}[9/10] Настройка PostgreSQL...${NC}"
sudo -u postgres psql -c "CREATE USER taxibot WITH PASSWORD 'change_this_password_123';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "CREATE DATABASE taxibot_db OWNER taxibot;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE taxibot_db TO taxibot;"

echo -e "${YELLOW}[10/10] Настройка firewall...${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo ""
echo -e "${GREEN}=========================================="
echo -e "  ✅ БАЗОВАЯ УСТАНОВКА ЗАВЕРШЕНА!"
echo -e "==========================================${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Загрузите код бота на сервер"
echo "2. Настройте .env файл"
echo "3. Запустите setup_bot.sh"
echo ""
