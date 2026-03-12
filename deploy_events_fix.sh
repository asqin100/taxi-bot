#!/bin/bash
# Полный деплой с проверкой мероприятий

echo "=========================================="
echo "ДЕПЛОЙ ИСПРАВЛЕНИЙ ДЛЯ МЕРОПРИЯТИЙ"
echo "=========================================="

cd /opt/taxibot

echo "1. Обновление кода..."
git pull origin main

echo ""
echo "2. Перезапуск бота (создаст таблицу events)..."
./update_bot.sh

echo ""
echo "Ожидание 15 секунд..."
sleep 15

echo ""
echo "3. Проверка таблицы events в БД..."
sqlite3 data/bot.db "SELECT name FROM sqlite_master WHERE type='table' AND name='events';"

echo ""
echo "4. Проверка структуры таблицы events..."
sqlite3 data/bot.db ".schema events"

echo ""
echo "5. Проверка существующих мероприятий..."
sqlite3 data/bot.db "SELECT id, name, zone_id, event_type, end_time FROM events;"

echo ""
echo "=========================================="
echo "СЛЕДУЮЩИЕ ШАГИ:"
echo "=========================================="
echo "1. Откройте админ-панель: https://kefpulse.ru/admin/dashboard"
echo "2. Откройте консоль браузера (F12)"
echo "3. Перейдите на вкладку 'Мероприятия'"
echo "4. Попробуйте создать мероприятие"
echo "5. Смотрите в консоль - там будут логи:"
echo "   - Creating event: {...}"
echo "   - Response status: 200"
echo "   - Response data: {...}"
echo "   - Loading events after creation..."
echo "   - Events loaded: N [...]"
echo ""
echo "Отправьте мне скриншот консоли или текст логов"
