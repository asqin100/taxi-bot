#!/bin/bash
# Мониторинг состояния Taxi Bot
# Использование: bash monitor.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "  📊 МОНИТОРИНГ TAXI BOT"
echo "=========================================="
echo ""

# Проверка сервисов
echo "🔧 Статус сервисов:"
if systemctl is-active --quiet taxibot; then
    echo -e "  Bot:        ${GREEN}✅ Работает${NC}"
else
    echo -e "  Bot:        ${RED}❌ Остановлен${NC}"
fi

if systemctl is-active --quiet taxibot-web; then
    echo -e "  Web Server: ${GREEN}✅ Работает${NC}"
else
    echo -e "  Web Server: ${RED}❌ Остановлен${NC}"
fi

if systemctl is-active --quiet nginx; then
    echo -e "  Nginx:      ${GREEN}✅ Работает${NC}"
else
    echo -e "  Nginx:      ${RED}❌ Остановлен${NC}"
fi

if systemctl is-active --quiet postgresql; then
    echo -e "  PostgreSQL: ${GREEN}✅ Работает${NC}"
else
    echo -e "  PostgreSQL: ${RED}❌ Остановлен${NC}"
fi

if systemctl is-active --quiet redis; then
    echo -e "  Redis:      ${GREEN}✅ Работает${NC}"
else
    echo -e "  Redis:      ${RED}❌ Остановлен${NC}"
fi

echo ""

# Использование ресурсов
echo "💻 Использование ресурсов:"
echo "  CPU:    $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "  RAM:    $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "  Диск:   $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " использовано)"}')"

echo ""

# Проверка портов
echo "🌐 Сетевые порты:"
if netstat -tuln | grep -q ":8080"; then
    echo -e "  8080:       ${GREEN}✅ Открыт${NC}"
else
    echo -e "  8080:       ${RED}❌ Закрыт${NC}"
fi

if netstat -tuln | grep -q ":80"; then
    echo -e "  80:         ${GREEN}✅ Открыт${NC}"
else
    echo -e "  80:         ${RED}❌ Закрыт${NC}"
fi

echo ""

# База данных
echo "🗄️  База данных:"
DB_SIZE=$(sudo -u postgres psql -t -c "SELECT pg_size_pretty(pg_database_size('taxibot_db'));" 2>/dev/null | xargs)
USER_COUNT=$(sudo -u postgres psql -t taxibot_db -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)
SHIFT_COUNT=$(sudo -u postgres psql -t taxibot_db -c "SELECT COUNT(*) FROM shifts;" 2>/dev/null | xargs)

if [ ! -z "$DB_SIZE" ]; then
    echo "  Размер БД:     $DB_SIZE"
    echo "  Пользователей: $USER_COUNT"
    echo "  Смен:          $SHIFT_COUNT"
else
    echo -e "  ${RED}❌ Не удалось подключиться к БД${NC}"
fi

echo ""

# Последние ошибки
echo "⚠️  Последние ошибки (за 1 час):"
ERROR_COUNT=$(journalctl -u taxibot --since "1 hour ago" | grep -i error | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}✅ Ошибок не обнаружено${NC}"
else
    echo -e "  ${YELLOW}⚠️  Найдено ошибок: $ERROR_COUNT${NC}"
    echo "  Последние 3 ошибки:"
    journalctl -u taxibot --since "1 hour ago" | grep -i error | tail -3 | sed 's/^/    /'
fi

echo ""

# Uptime
echo "⏱️  Uptime:"
UPTIME=$(uptime -p)
echo "  Система: $UPTIME"

BOT_UPTIME=$(systemctl show taxibot --property=ActiveEnterTimestamp --value)
if [ ! -z "$BOT_UPTIME" ]; then
    echo "  Bot:     Запущен $(date -d "$BOT_UPTIME" '+%Y-%m-%d %H:%M:%S')"
fi

echo ""
echo "=========================================="
echo "Для просмотра логов:"
echo "  tail -f /var/log/taxibot/bot.log"
echo "  journalctl -u taxibot -f"
echo "=========================================="
