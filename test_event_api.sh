#!/bin/bash
# Тест API создания мероприятий

echo "=== Тест API создания мероприятий ==="
echo ""

# Сначала получаем токен (логинимся)
echo "1. Логин в админ-панель..."
TOKEN_RESPONSE=$(curl -s -X POST https://kefpulse.ru/admin/login \
  -H "Content-Type: application/json" \
  -d '{"password":"admin123!@#"}')

echo "Response: $TOKEN_RESPONSE"

TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Не удалось получить токен"
    exit 1
fi

echo "✅ Токен получен: ${TOKEN:0:20}..."
echo ""

# Создаем тестовое мероприятие
echo "2. Создание тестового мероприятия..."
FUTURE_DATE=$(date -d "+1 day" +"%Y-%m-%dT20:00:00")
echo "Дата окончания: $FUTURE_DATE"

CREATE_RESPONSE=$(curl -s -X POST https://kefpulse.ru/admin/api/events/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"API Test Event\",\"zone_id\":\"luzhniki\",\"event_type\":\"concert\",\"end_time\":\"$FUTURE_DATE\"}")

echo "Response: $CREATE_RESPONSE"
echo ""

# Проверяем список мероприятий
echo "3. Получение списка мероприятий..."
EVENTS_RESPONSE=$(curl -s https://kefpulse.ru/admin/api/events \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $EVENTS_RESPONSE"
echo ""

# Проверяем в БД
echo "4. Проверка в базе данных..."
sqlite3 /opt/taxibot/data/bot.db "SELECT id, name, zone_id, event_type, end_time FROM events ORDER BY id DESC LIMIT 5;"
