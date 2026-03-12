#!/bin/bash
# Проверка после деплоя - все ли работает

echo "╔════════════════════════════════════════════════════════╗"
echo "║     ПРОВЕРКА ПОСЛЕ ДЕПЛОЯ - ВСЕ ЛИ РАБОТАЕТ?          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 1. Проверка, что бот запущен
echo "1. Статус бота..."
if systemctl is-active --quiet taxibot; then
    echo "   ✅ Бот запущен"
else
    echo "   ❌ Бот НЕ запущен!"
    exit 1
fi

# 2. Проверка таблицы events
echo ""
echo "2. Таблица events в БД..."
EVENT_COUNT=$(sqlite3 /opt/taxibot/data/bot.db "SELECT COUNT(*) FROM events;" 2>/dev/null)
echo "   Всего мероприятий: $EVENT_COUNT"

# 3. Показать последние мероприятия
echo ""
echo "3. Последние 3 мероприятия:"
sqlite3 /opt/taxibot/data/bot.db "SELECT id, name, zone_id, datetime(end_time) as end_time FROM events ORDER BY id DESC LIMIT 3;" 2>/dev/null | while read line; do
    echo "   $line"
done

# 4. Проверка API эндпоинта
echo ""
echo "4. Проверка API эндпоинта..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://kefpulse.ru/admin/api/events)
if [ "$HTTP_CODE" = "401" ]; then
    echo "   ✅ API работает (401 = требуется авторизация)"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ API работает (200 = OK)"
else
    echo "   ⚠️  HTTP Status: $HTTP_CODE"
fi

# 5. Проверка последних ошибок
echo ""
echo "5. Последние ошибки в логах (если есть):"
ERRORS=$(tail -100 /opt/taxibot/bot.log | grep -i "error\|exception" | tail -3)
if [ -z "$ERRORS" ]; then
    echo "   ✅ Ошибок не найдено"
else
    echo "$ERRORS"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                  СЛЕДУЮЩИЙ ШАГ                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Теперь откройте браузер и попробуйте создать мероприятие:"
echo "  https://kefpulse.ru/admin/dashboard"
echo ""
echo "Если мероприятие НЕ создается:"
echo "  1. Откройте консоль (F12 → Console)"
echo "  2. Попробуйте создать мероприятие"
echo "  3. Отправьте мне логи из консоли"
echo ""
