#!/bin/bash
# Диагностика ошибки запуска бота

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ДИАГНОСТИКА ОШИБКИ ЗАПУСКА                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /opt/taxibot

echo "[1/4] Попытка запуска бота вручную (10 секунд)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
timeout 10 /opt/taxibot/venv/bin/python -m bot.main 2>&1 | tee /tmp/bot_error.log
echo ""

echo "[2/4] Анализ ошибок..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if grep -q "ERROR\|Exception\|Traceback" /tmp/bot_error.log; then
    echo "✗ Найдены ошибки:"
    grep -A 3 "ERROR\|Exception\|Traceback" /tmp/bot_error.log | head -20
else
    echo "⚠️  Ошибок не найдено в выводе (возможно, бот запустился нормально)"
fi
echo ""

echo "[3/4] Проверка последних логов systemd..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
journalctl -u taxibot --since "5 minutes ago" --no-pager | grep -E "ERROR|Exception|Traceback|Failed" | tail -10
echo ""

echo "[4/4] Проверка зависимостей Python..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
/opt/taxibot/venv/bin/python -c "
try:
    from bot.config import settings
    print('✓ Config загружен')
    print(f'  Payment provider: {settings.payment_provider}')
    print(f'  Robokassa merchant: {settings.robokassa_merchant_login}')
except Exception as e:
    print(f'✗ Ошибка загрузки config: {e}')

try:
    from bot.services.payment_robokassa import create_payment
    print('✓ payment_robokassa импортирован')
except Exception as e:
    print(f'✗ Ошибка импорта payment_robokassa: {e}')

try:
    from bot.web.api import create_app
    print('✓ web.api импортирован')
except Exception as e:
    print(f'✗ Ошибка импорта web.api: {e}')
"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ДИАГНОСТИКА ЗАВЕРШЕНА                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Полный лог ошибок сохранен в: /tmp/bot_error.log"
echo "Для просмотра: cat /tmp/bot_error.log"
