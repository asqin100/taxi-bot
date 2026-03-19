#!/bin/bash
# Восстановление базы данных из бэкапа
# Использование: bash restore.sh backup_file.sql.gz

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}❌ Укажите файл бэкапа${NC}"
    echo "Использование: bash restore.sh backup_file.sql.gz"
    echo ""
    echo "Доступные бэкапы:"
    ls -lh /opt/taxibot/backups/taxibot_backup_*.sql.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ Файл не найден: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}⚠️  ВНИМАНИЕ: Это удалит текущую базу данных!${NC}"
read -p "Продолжить? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Отменено"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/5] Создание бэкапа текущей БД...${NC}"
SAFETY_BACKUP="/tmp/safety_backup_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump taxibot_db > $SAFETY_BACKUP
echo -e "${GREEN}✅ Страховочный бэкап: $SAFETY_BACKUP${NC}"

echo -e "${YELLOW}[2/5] Остановка сервисов...${NC}"
sudo systemctl stop taxibot taxibot-web

echo -e "${YELLOW}[3/5] Распаковка бэкапа...${NC}"
if [[ $BACKUP_FILE == *.gz ]]; then
    UNZIPPED_FILE="${BACKUP_FILE%.gz}"
    gunzip -c $BACKUP_FILE > $UNZIPPED_FILE
else
    UNZIPPED_FILE=$BACKUP_FILE
fi

echo -e "${YELLOW}[4/5] Восстановление базы данных...${NC}"
sudo -u postgres psql -c "DROP DATABASE IF EXISTS taxibot_db;"
sudo -u postgres psql -c "CREATE DATABASE taxibot_db OWNER taxibot;"
sudo -u postgres psql taxibot_db < $UNZIPPED_FILE

# Удаление временного файла
if [[ $BACKUP_FILE == *.gz ]]; then
    rm $UNZIPPED_FILE
fi

echo -e "${YELLOW}[5/5] Запуск сервисов...${NC}"
sudo systemctl start taxibot taxibot-web

echo ""
echo -e "${GREEN}=========================================="
echo -e "  ✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!"
echo -e "==========================================${NC}"
echo ""
echo "Проверьте работу бота:"
echo "  sudo systemctl status taxibot"
echo "  tail -f /var/log/taxibot/bot.log"
echo ""
echo "Страховочный бэкап сохранен:"
echo "  $SAFETY_BACKUP"
echo ""
