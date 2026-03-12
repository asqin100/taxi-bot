#!/bin/bash
# Быстрая проверка - работает ли API создания мероприятий

echo "=== БЫСТРЫЙ ТЕСТ API ==="
echo ""

# Тест 1: Проверка, что эндпоинт существует
echo "1. Проверка доступности API..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://kefpulse.ru/admin/api/events

echo ""
echo "2. Попытка создать мероприятие без токена (должна быть ошибка 401)..."
curl -s -X POST https://kefpulse.ru/admin/api/events/create \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","zone_id":"luzhniki","event_type":"concert","end_time":"2026-03-15T20:00:00"}' \
  -w "\nHTTP Status: %{http_code}\n"

echo ""
echo "3. Проверка логов на ошибки..."
tail -30 /opt/taxibot/bot.log | grep -i "error\|exception\|traceback" | tail -10

echo ""
echo "=== ИНСТРУКЦИЯ ==="
echo "Если видите HTTP Status: 401 - это нормально (нет токена)"
echo "Если видите HTTP Status: 404 - эндпоинт не найден (проблема в роутинге)"
echo "Если видите HTTP Status: 500 - ошибка сервера (смотрите логи выше)"
