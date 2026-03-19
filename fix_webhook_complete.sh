#!/bin/bash
# ПОЛНАЯ ИНСТРУКЦИЯ: Исправление Robokassa webhook

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ИСПРАВЛЕНИЕ ROBOKASSA WEBHOOK - ПОШАГОВАЯ ИНСТРУКЦИЯ      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Шаг 1
echo "📋 ШАГ 1: Обновление кода"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /opt/taxibot
git pull origin main
echo "✅ Код обновлен"
echo ""

# Шаг 2
echo "📋 ШАГ 2: Перезапуск бота"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo systemctl restart taxibot
sleep 3
echo "✅ Бот перезапущен"
echo ""

# Шаг 3
echo "📋 ШАГ 3: Проверка статуса"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if systemctl is-active --quiet taxibot; then
    echo "✅ Бот работает"
else
    echo "❌ ОШИБКА: Бот не запущен!"
    echo "Проверьте логи: journalctl -u taxibot -n 50"
    exit 1
fi
echo ""

# Шаг 4
echo "📋 ШАГ 4: Определение правильных URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Тестирую доступность webhook..."
echo ""

# Test without port
RESPONSE1=$(curl -s -o /dev/null -w "%{http_code}" http://5.42.110.16/webhook/robokassa/success 2>/dev/null)
echo "Без порта (nginx): код $RESPONSE1"

# Test with port
RESPONSE2=$(curl -s -o /dev/null -w "%{http_code}" http://5.42.110.16:8080/webhook/robokassa/success 2>/dev/null)
echo "С портом :8080: код $RESPONSE2"
echo ""

# Determine correct URLs
if [ "$RESPONSE1" = "200" ]; then
    USE_PORT=""
    URL_BASE="http://5.42.110.16"
    echo "✅ Используйте URL БЕЗ порта (через nginx)"
elif [ "$RESPONSE2" = "200" ]; then
    USE_PORT=":8080"
    URL_BASE="http://5.42.110.16:8080"
    echo "✅ Используйте URL С портом :8080"
else
    echo "❌ ОШИБКА: Webhook недоступен!"
    echo ""
    echo "Проверьте:"
    echo "  netstat -tlnp | grep 8080"
    echo "  journalctl -u taxibot -n 20"
    exit 1
fi
echo ""

# Шаг 5
echo "📋 ШАГ 5: СКОПИРУЙТЕ ЭТИ URL В ROBOKASSA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Result URL (обязательно!):"
echo "  ${URL_BASE}/webhook/robokassa/result"
echo ""
echo "Success URL:"
echo "  ${URL_BASE}/webhook/robokassa/success"
echo ""
echo "Fail URL:"
echo "  ${URL_BASE}/webhook/robokassa/fail"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Шаг 6
echo "📋 ШАГ 6: Что делать дальше"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Зайдите в личный кабинет Robokassa"
echo "2. Откройте настройки магазина 'kefpulse'"
echo "3. Вставьте URL выше в соответствующие поля"
echo "4. ОБЯЗАТЕЛЬНО нажмите 'Сохранить'!"
echo "5. Протестируйте оплату тестовой картой: 5555 5555 5555 5599"
echo ""
echo "После оплаты должно произойти:"
echo "  ✅ Откроется страница 'Оплата успешна'"
echo "  ✅ Бот пришлет сообщение 'Подписка активирована!'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Готово! Теперь обновите URL в Robokassa и протестируйте."
echo ""
