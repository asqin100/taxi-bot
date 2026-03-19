#!/bin/bash
# Quick verification and restart

cd /opt/taxibot

echo "1. Обновляю код..."
git pull origin main

echo ""
echo "2. Перезапускаю бота..."
systemctl restart taxibot
sleep 3

echo ""
echo "3. Проверяю статус..."
if systemctl is-active --quiet taxibot; then
    echo "✅ Бот работает"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "✅ Кнопка добавлена! Откройте бота:"
    echo ""
    echo "   /menu → 💎 Подписка → ⬆️ Улучшить тариф"
    echo ""
    echo "   Там будет кнопка: 🧪 ТЕСТ — 5₽ (1 день)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo "❌ Бот не запустился!"
    journalctl -u taxibot -n 20
fi
