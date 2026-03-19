#!/bin/bash
# Check if bot is running and test button is deployed

echo "Проверяю статус бота..."
echo ""

# Check bot status
if systemctl is-active --quiet taxibot; then
    echo "✅ Бот работает"
else
    echo "❌ Бот не работает!"
    systemctl status taxibot --no-pager -l | head -20
    exit 1
fi

echo ""
echo "Проверяю код..."
if grep -q "ТЕСТ — 5₽" /opt/taxibot/bot/handlers/subscription.py; then
    echo "✅ Кнопка тестового платежа найдена в коде"
else
    echo "❌ Кнопка не найдена в коде!"
fi

echo ""
echo "Проверяю логи на ошибки..."
journalctl -u taxibot --since "2 minutes ago" | grep -i error | tail -5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "КАК НАЙТИ КНОПКУ В БОТЕ:"
echo ""
echo "1. Откройте бота @KefPulse_bot"
echo "2. Нажмите /menu"
echo "3. Выберите '💎 Подписка'"
echo "4. Нажмите '⬆️ Улучшить тариф'"
echo "5. Кнопка '🧪 ТЕСТ — 5₽ (1 день)' должна быть ПЕРВОЙ"
echo "   (после документов, перед Pro/Premium/Elite)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
