#!/bin/bash
# Диагностика проблемы с мероприятиями

echo "=== 1. Проверка таблицы events в БД ==="
sqlite3 /opt/taxibot/data/bot.db ".schema events"

echo ""
echo "=== 2. Список всех таблиц в БД ==="
sqlite3 /opt/taxibot/data/bot.db ".tables"

echo ""
echo "=== 3. Проверка логов бота на ошибки Event ==="
tail -100 /opt/taxibot/bot.log | grep -i "event\|error" | tail -30

echo ""
echo "=== 4. Проверка, запущен ли бот ==="
systemctl status taxibot --no-pager | head -10

echo ""
echo "=== 5. Проверка последних логов бота ==="
tail -20 /opt/taxibot/bot.log
