#!/bin/bash
# Автоматический бэкап базы данных
# Использование: bash backup.sh
# Для автоматизации добавьте в crontab: 0 3 * * * /opt/taxibot/deploy/backup.sh

set -e

BACKUP_DIR="/opt/taxibot/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="taxibot_backup_$TIMESTAMP.sql"
KEEP_DAYS=7  # Хранить бэкапы за последние 7 дней

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔄 Создание бэкапа базы данных...${NC}"

# Создание директории для бэкапов
mkdir -p $BACKUP_DIR

# Создание бэкапа
sudo -u postgres pg_dump taxibot_db > $BACKUP_DIR/$BACKUP_FILE

# Сжатие бэкапа
gzip $BACKUP_DIR/$BACKUP_FILE

echo -e "${GREEN}✅ Бэкап создан: $BACKUP_DIR/$BACKUP_FILE.gz${NC}"

# Размер бэкапа
SIZE=$(du -h $BACKUP_DIR/$BACKUP_FILE.gz | cut -f1)
echo -e "${GREEN}📦 Размер: $SIZE${NC}"

# Удаление старых бэкапов
echo -e "${YELLOW}🗑️  Удаление бэкапов старше $KEEP_DAYS дней...${NC}"
find $BACKUP_DIR -name "taxibot_backup_*.sql.gz" -mtime +$KEEP_DAYS -delete

# Список текущих бэкапов
echo ""
echo "📋 Доступные бэкапы:"
ls -lh $BACKUP_DIR/taxibot_backup_*.sql.gz 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo -e "${GREEN}✅ Бэкап завершен!${NC}"
echo ""
echo "Для восстановления:"
echo "  gunzip $BACKUP_DIR/$BACKUP_FILE.gz"
echo "  sudo -u postgres psql taxibot_db < $BACKUP_DIR/$BACKUP_FILE"
