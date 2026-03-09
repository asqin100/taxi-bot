#!/bin/bash
# Скрипт обновления бота

echo "🔄 Обновление бота..."

# Получить изменения
git pull origin main

# Установить/обновить зависимости
echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt --quiet

# Остановить старый процесс
echo "⏹ Остановка бота..."
pkill -9 -f "python.*bot.main"
sleep 2

# Запустить новый процесс
echo "▶️ Запуск бота..."
nohup python3 -m bot.main > bot.log 2>&1 &

sleep 3

# Проверить что запустился
if ps aux | grep -v grep | grep "bot.main" > /dev/null; then
    echo "✅ Бот успешно обновлен и запущен!"
    echo ""
    echo "📋 Последние строки лога:"
    tail -10 bot.log
else
    echo "❌ Ошибка запуска! Проверьте логи:"
    tail -20 bot.log
fi
