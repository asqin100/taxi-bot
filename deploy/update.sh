#!/bin/bash
# Скрипт обновления бота на VPS
# Использование: bash update.sh

set -e

echo "=========================================="
echo "  🔄 ОБНОВЛЕНИЕ TAXI BOT"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd /opt/taxibot

echo -e "${YELLOW}[1/5] Создание бэкапа БД...${NC}"
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump taxibot_db > /tmp/$BACKUP_FILE
echo -e "${GREEN}✅ Бэкап сохранен: /tmp/$BACKUP_FILE${NC}"

echo -e "${YELLOW}[2/5] Остановка сервисов...${NC}"
sudo systemctl stop taxibot taxibot-web

echo -e "${YELLOW}[3/5] Обновление кода...${NC}"
sudo -u taxibot git pull

echo -e "${YELLOW}[4/5] Обновление зависимостей...${NC}"
sudo -u taxibot /opt/taxibot/venv/bin/pip install -r requirements.txt --upgrade

echo -e "${YELLOW}[5/5] Запуск сервисов...${NC}"
sudo systemctl start taxibot taxibot-web

echo ""
echo -e "${GREEN}=========================================="
echo -e "  ✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo -e "==========================================${NC}"
echo ""
echo "Проверьте статус:"
echo "  sudo systemctl status taxibot"
echo "  sudo systemctl status taxibot-web"
echo ""
echo "Логи:"
echo "  tail -f /var/log/taxibot/bot.log"
echo ""
