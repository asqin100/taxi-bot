#!/bin/bash
# Полная диагностика проблемы с созданием мероприятий

echo "=========================================="
echo "ДИАГНОСТИКА СОЗДАНИЯ МЕРОПРИЯТИЙ"
echo "=========================================="
echo ""

echo "1. Проверка таблицы events..."
sqlite3 /opt/taxibot/data/bot.db "SELECT COUNT(*) as total FROM events;" 2>/dev/null || echo "Ошибка доступа к БД"

echo ""
echo "2. Проверка API эндпоинта (без токена - ожидается 401)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://kefpulse.ru/admin/api/events/create \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","zone_id":"luzhniki","event_type":"concert","end_time":"2026-03-15T20:00:00"}')
echo "HTTP Status: $HTTP_CODE"
if [ "$HTTP_CODE" = "401" ]; then
    echo "✅ API эндпоинт работает (401 = нужна авторизация)"
elif [ "$HTTP_CODE" = "404" ]; then
    echo "❌ API эндпоинт не найден (проблема в роутинге)"
else
    echo "⚠️ Неожиданный статус: $HTTP_CODE"
fi

echo ""
echo "3. Проверка последних ошибок в логах..."
tail -50 /opt/taxibot/bot.log | grep -i "error\|exception" | tail -5

echo ""
echo "4. Проверка, запущен ли бот..."
systemctl is-active taxibot && echo "✅ Бот запущен" || echo "❌ Бот не запущен"

echo ""
echo "=========================================="
echo "СЛЕДУЮЩИЙ ШАГ:"
echo "=========================================="
echo ""
echo "Откройте браузер и проверьте консоль:"
echo "1. https://kefpulse.ru/admin/dashboard"
echo "2. F12 → Console"
echo "3. Вкладка 'Мероприятия' → 'Добавить мероприятие'"
echo "4. Заполните форму (время ЗАВТРА!)"
echo "5. Нажмите 'Создать'"
echo "6. Отправьте мне логи из консоли"
echo ""
