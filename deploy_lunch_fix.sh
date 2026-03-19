#!/bin/bash
# Полный скрипт деплоя и диагностики для функции "Заехать на обед"

echo "=============================================="
echo "ДЕПЛОЙ И ДИАГНОСТИКА ФУНКЦИИ ПОИСКА РЕСТОРАНОВ"
echo "=============================================="
echo ""

# Шаг 1: Деплой
echo "ШАГ 1: Деплой изменений..."
cd /opt/taxibot
git stash
git pull origin main
chmod +x update_bot.sh
./update_bot.sh

echo ""
echo "Ожидание перезапуска бота (10 секунд)..."
sleep 10

# Шаг 2: Проверка статуса
echo ""
echo "ШАГ 2: Проверка статуса бота..."
systemctl status taxibot --no-pager | head -10

# Шаг 3: Тест доступности Nominatim API
echo ""
echo "ШАГ 3: Тест доступности Nominatim API с сервера..."
cd /opt/taxibot
python3 test_nominatim_server.py

# Шаг 4: Инструкции для пользователя
echo ""
echo "=============================================="
echo "ШАГ 4: ТЕСТИРОВАНИЕ В TELEGRAM"
echo "=============================================="
echo ""
echo "1. Откройте бота в Telegram"
echo "2. Нажмите кнопку 'Заехать на обед'"
echo "3. Сразу после нажатия выполните команду:"
echo ""
echo "   tail -100 /opt/taxibot/bot.log | grep -E 'lunch|restaurant|Nominatim'"
echo ""
echo "4. Отправьте мне вывод логов для анализа"
echo ""
echo "=============================================="
