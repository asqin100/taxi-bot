#!/bin/bash
# Диагностика проблемы с запуском бота

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ДИАГНОСТИКА ПРОБЛЕМЫ ЗАПУСКА БОТА                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /opt/taxibot

echo "[1/5] Проверка .env файла..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if grep -q "ROBOKASSA_MERCHANT_LOGIN" .env; then
    echo "✓ ROBOKASSA_MERCHANT_LOGIN найден"
    grep "ROBOKASSA" .env | head -6
else
    echo "✗ ROBOKASSA_MERCHANT_LOGIN не найден!"
fi
echo ""

echo "[2/5] Проверка синтаксиса Python..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
/opt/taxibot/venv/bin/python -m py_compile bot/services/payment_robokassa.py 2>&1
if [ $? -eq 0 ]; then
    echo "✓ payment_robokassa.py: синтаксис OK"
else
    echo "✗ payment_robokassa.py: ошибка синтаксиса!"
fi

/opt/taxibot/venv/bin/python -m py_compile bot/web/api.py 2>&1
if [ $? -eq 0 ]; then
    echo "✓ api.py: синтаксис OK"
else
    echo "✗ api.py: ошибка синтаксиса!"
fi
echo ""

echo "[3/5] Проверка импортов..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
/opt/taxibot/venv/bin/python -c "from bot.config import settings; print('✓ Config загружен'); print(f'  Payment provider: {settings.payment_provider}'); print(f'  Robokassa merchant: {settings.robokassa_merchant_login}')" 2>&1
echo ""

echo "[4/5] Последние ошибки из bot.log..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f bot.log ]; then
    tail -30 bot.log | grep -A 5 -i "error\|exception\|traceback" || echo "Нет ошибок в последних 30 строках"
else
    echo "⚠️  Файл bot.log не найден"
fi
echo ""

echo "[5/5] Попытка запуска бота (5 секунд)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
timeout 5 /opt/taxibot/venv/bin/python -m bot.main 2>&1 | head -50
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ДИАГНОСТИКА ЗАВЕРШЕНА                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
