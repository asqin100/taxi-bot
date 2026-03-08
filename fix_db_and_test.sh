#!/bin/bash
# Исправление базы данных и проверка

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ИСПРАВЛЕНИЕ БАЗЫ ДАННЫХ                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /opt/taxibot

echo "[1/4] Добавление недостающих колонок в базу данных..."
sqlite3 data/bot.db << 'EOF'
ALTER TABLE users ADD COLUMN geo_alerts_sent_today INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN geo_alerts_reset_date TEXT;
EOF

if [ $? -eq 0 ]; then
    echo "✓ Колонки добавлены успешно"
else
    echo "⚠️  Колонки уже существуют или ошибка (это нормально, если они уже есть)"
fi

echo ""
echo "[2/4] Перезапуск бота..."
systemctl restart taxibot
sleep 3

echo ""
echo "[3/4] Проверка статуса..."
if systemctl is-active --quiet taxibot; then
    echo "✓ Бот запущен"
else
    echo "✗ Бот не запущен"
fi

echo ""
echo "[4/4] Проверка порта 8080..."
if netstat -tlnp | grep -q ":8080"; then
    echo "✓ Порт 8080 слушается - БОТ РАБОТАЕТ!"
    netstat -tlnp | grep ":8080"
else
    echo "✗ Порт 8080 не слушается"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ГОТОВО!                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Если всё ОК, переходи к настройке Robokassa:"
echo "1. https://auth.robokassa.ru/"
echo "2. Result URL: http://5.42.110.16:8080/webhook/robokassa/result"
echo "3. Тестовый платеж 5₽ в боте"
