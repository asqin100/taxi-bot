#!/bin/bash
# Detailed check after payment

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        ДЕТАЛЬНАЯ ПРОВЕРКА ПОСЛЕ ПЛАТЕЖА                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# 1. Check all logs for last 15 minutes
echo "1. Все логи бота за последние 15 минут:"
journalctl -u taxibot --since "15 minutes ago" | tail -30

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 2. Check nginx logs if exists
echo "2. Проверка nginx логов (если есть):"
if [ -f /var/log/nginx/access.log ]; then
    echo "   Последние запросы к nginx:"
    tail -20 /var/log/nginx/access.log | grep "webhook"
else
    echo "   Nginx логи не найдены"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 3. Check if port 8080 received any connections
echo "3. Проверка соединений на порт 8080:"
netstat -tn | grep ":8080" | head -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 4. Test Result URL manually
echo "4. Ручной тест Result URL:"
curl -v "http://5.42.110.16:8080/webhook/robokassa/result?OutSum=5&InvId=123&SignatureValue=test&Shp_user_id=123&Shp_tier=pro&Shp_duration=1" 2>&1 | head -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "ДИАГНОСТИКА:"
echo ""
echo "Если в логах НЕТ запросов от Robokassa, значит:"
echo ""
echo "❌ Result URL НЕ СОХРАНЕН в настройках Robokassa!"
echo ""
echo "Проверьте в личном кабинете Robokassa:"
echo ""
echo "1. Зайдите: https://auth.robokassa.ru/"
echo "2. Магазин: kefpulse → Технические настройки"
echo "3. Убедитесь, что вы в разделе БОЕВОГО режима"
echo "4. Проверьте поле Result URL:"
echo "   http://5.42.110.16:8080/webhook/robokassa/result"
echo "5. Метод должен быть: GET"
echo "6. Нажмите 'Сохранить' и дождитесь подтверждения"
echo ""
echo "После сохранения сделайте НОВЫЙ платеж на 5₽"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
