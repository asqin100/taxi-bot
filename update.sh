#!/bin/bash
# Скрипт обновления бота

echo "🔄 Обновление бота..."

# Получить изменения
git pull origin main

# Создать виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активировать виртуальное окружение и установить зависимости
echo "📦 Установка зависимостей..."
source venv/bin/activate
pip install -r requirements.txt --quiet

# Применить миграции базы данных
echo "🗄️ Обновление базы данных..."
venv/bin/alembic upgrade head

# Остановить старый процесс
echo "⏹ Остановка бота..."
pkill -9 -f "python.*bot.main"
sleep 2

# Запустить новый процесс с виртуальным окружением
echo "▶️ Запуск бота..."
nohup venv/bin/python -m bot.main > bot.log 2>&1 &

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
