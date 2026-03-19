#!/bin/bash
# Настройка приложения Taxi Bot
# Запускать от пользователя taxibot: bash setup_bot.sh

set -e

echo "=========================================="
echo "  🚕 НАСТРОЙКА ПРИЛОЖЕНИЯ"
echo "=========================================="
echo ""

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

BOT_DIR="/opt/taxibot"
cd $BOT_DIR

echo -e "${YELLOW}[1/8] Создание виртуального окружения...${NC}"
python3.11 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[2/8] Обновление pip...${NC}"
pip install --upgrade pip

echo -e "${YELLOW}[3/8] Установка зависимостей...${NC}"
pip install aiogram==3.4.1
pip install sqlalchemy==2.0.25
pip install asyncpg  # PostgreSQL драйвер
pip install aiohttp
pip install python-dotenv
pip install apscheduler
pip install matplotlib seaborn pandas numpy scikit-learn
pip install redis
pip install psycopg2-binary

echo -e "${YELLOW}[4/8] Создание .env файла...${NC}"
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Telegram Bot
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=KefPulse_bot
ADMIN_IDS=your_telegram_id

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://taxibot:change_this_password_123@localhost/taxibot_db

# Yandex API
YANDEX_API_KEY=your_yandex_api_key

# Web Server
WEB_HOST=0.0.0.0
WEB_PORT=8080

# Redis
REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=production
EOF
    echo -e "${GREEN}✅ Создан .env файл. ВАЖНО: Отредактируйте его!${NC}"
else
    echo -e "${GREEN}✅ .env уже существует${NC}"
fi

echo -e "${YELLOW}[5/8] Создание директорий...${NC}"
mkdir -p data
mkdir -p logs
mkdir -p webapp

echo -e "${YELLOW}[6/8] Применение миграций БД...${NC}"
if [ -f "migrate_to_postgres.py" ]; then
    python migrate_to_postgres.py
    echo -e "${GREEN}✅ Миграция выполнена${NC}"
else
    echo -e "${YELLOW}⚠️  Файл миграции не найден, пропускаем${NC}"
fi

echo -e "${YELLOW}[7/8] Проверка конфигурации...${NC}"
python -c "from bot.config import settings; print('✅ Конфигурация загружена')" || echo "❌ Ошибка конфигурации"

echo -e "${YELLOW}[8/8] Установка systemd сервисов...${NC}"
sudo cp /opt/taxibot/deploy/taxibot.service /etc/systemd/system/
sudo cp /opt/taxibot/deploy/taxibot-web.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo -e "${GREEN}=========================================="
echo -e "  ✅ НАСТРОЙКА ЗАВЕРШЕНА!"
echo -e "==========================================${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Отредактируйте /opt/taxibot/.env"
echo "2. Запустите сервисы:"
echo "   sudo systemctl start taxibot"
echo "   sudo systemctl start taxibot-web"
echo "3. Включите автозапуск:"
echo "   sudo systemctl enable taxibot"
echo "   sudo systemctl enable taxibot-web"
echo ""
