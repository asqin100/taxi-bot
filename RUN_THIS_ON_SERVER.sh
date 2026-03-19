#!/bin/bash
# Скопируй весь этот файл на сервер и запусти: bash RUN_THIS_ON_SERVER.sh

echo "Исправление дубликатов бота..."
echo ""

# Остановить бота
echo "[1/5] Останавливаю taxibot service..."
sudo systemctl stop taxibot
sleep 2

# Убить все процессы
echo "[2/5] Убиваю зависшие процессы..."
sudo pkill -9 -f "python.*bot/main.py"
sleep 2

# Проверка
echo "[3/5] Проверяю что все убито..."
REMAINING=$(ps aux | grep "python.*bot/main.py" | grep -v grep | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "ОШИБКА: Остались процессы!"
    ps aux | grep "python.*bot/main.py" | grep -v grep
    exit 1
fi
echo "✅ Все процессы убиты"

# Запустить заново
echo "[4/5] Запускаю бота..."
sudo systemctl start taxibot
sleep 3

# Проверка логов
echo "[5/5] Проверяю логи..."
sleep 5
CONFLICTS=$(sudo journalctl -u taxibot -n 50 --no-pager | grep -c "TelegramConflictError")

echo ""
echo "═══════════════════════════════════════════════════════════════"
if [ "$CONFLICTS" -eq 0 ]; then
    echo "✅ УСПЕХ! Бот работает без ошибок"
else
    echo "⚠️ Найдено $CONFLICTS TelegramConflictError"
fi
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Последние 20 строк логов:"
sudo journalctl -u taxibot -n 20 --no-pager
