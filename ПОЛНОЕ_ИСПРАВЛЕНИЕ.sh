#!/bin/bash
# Полное исправление бота - выполни этот скрипт на сервере

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           ПОЛНОЕ ИСПРАВЛЕНИЕ БОТА                            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Шаг 1: Перейти в папку бота
echo "[1/7] Переход в папку бота..."
cd /opt/taxibot || exit 1

# Шаг 2: Проверить текущую версию
echo "[2/7] Текущая версия кода:"
git log --oneline -3

# Шаг 3: Обновить код с GitHub
echo ""
echo "[3/7] Обновление кода с GitHub..."
git pull origin main

# Шаг 4: Остановить systemd service
echo ""
echo "[4/7] Остановка taxibot service..."
sudo systemctl stop taxibot
sleep 2

# Шаг 5: Убить ВСЕ процессы бота
echo "[5/7] Убийство всех процессов бота..."
sudo pkill -9 -f "python.*bot/main.py"
sudo pkill -9 -f "python.*taxibot"
sleep 2

# Проверка что все убиты
REMAINING=$(ps aux | grep -E "python.*(bot/main|taxibot)" | grep -v grep | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  Остались процессы:"
    ps aux | grep -E "python.*(bot/main|taxibot)" | grep -v grep
    echo "Убиваю принудительно..."
    ps aux | grep -E "python.*(bot/main|taxibot)" | grep -v grep | awk '{print $2}' | xargs -r sudo kill -9
    sleep 2
fi

echo "✅ Все процессы убиты"

# Шаг 6: Запустить бота заново
echo ""
echo "[6/7] Запуск бота..."
sudo systemctl start taxibot
sleep 5

# Шаг 7: Проверить логи
echo ""
echo "[7/7] Проверка логов..."
echo ""
sudo journalctl -u taxibot -n 30 --no-pager

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    ПРОВЕРКА РЕЗУЛЬТАТА                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Проверка на ошибки
ERRORS=$(sudo journalctl -u taxibot -n 50 --no-pager | grep -c "ERROR\|NameError\|TelegramConflictError")

if [ "$ERRORS" -eq 0 ]; then
    echo "✅ БОТ РАБОТАЕТ! Ошибок не найдено."
else
    echo "⚠️  Найдено $ERRORS ошибок в логах"
    echo "Проверь логи выше"
fi

echo ""
echo "Проверь бота в Telegram: @KefPulse_bot → /start"
echo ""
