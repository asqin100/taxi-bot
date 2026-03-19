#!/bin/bash
# Автоматическое исправление .env и перезапуск бота

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ИСПРАВЛЕНИЕ .env И ПЕРЕЗАПУСК БОТА                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /opt/taxibot

echo "[1/6] Удаление проблемных строк..."
sed -i '/^# Robokassa/d' .env
sed -i '/^$/d' .env
echo "✓ Пустые строки и комментарии удалены"

echo ""
echo "[2/6] Удаление старых настроек Robokassa..."
sed -i '/ROBOKASSA_/d' .env
sed -i '/PAYMENT_PROVIDER/d' .env
echo "✓ Старые настройки удалены"

echo ""
echo "[3/6] Добавление новых настроек Robokassa..."
echo "ROBOKASSA_MERCHANT_LOGIN=kefpulse" >> .env
echo "ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42" >> .env
echo "ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs" >> .env
echo "ROBOKASSA_TEST_MODE=False" >> .env
echo "PAYMENT_PROVIDER=robokassa" >> .env
echo "✓ Настройки добавлены"

echo ""
echo "[4/6] Проверка .env..."
echo "Последние 10 строк .env:"
tail -10 .env

echo ""
echo "[5/6] Перезапуск бота..."
systemctl restart taxibot
sleep 3

echo ""
echo "[6/6] Проверка статуса..."
if systemctl is-active --quiet taxibot; then
    echo "✓ Бот запущен успешно!"

    # Проверка порта
    if netstat -tlnp | grep -q ":8080"; then
        echo "✓ Порт 8080 слушается"
    else
        echo "⚠️  Порт 8080 не слушается"
    fi

    # Проверка ошибок парсинга
    sleep 2
    if journalctl -u taxibot -n 20 --no-pager | grep -q "could not parse"; then
        echo "⚠️  Всё ещё есть ошибки парсинга .env"
        echo "Последние ошибки:"
        journalctl -u taxibot -n 20 --no-pager | grep "could not parse"
    else
        echo "✓ Ошибок парсинга нет!"
    fi
else
    echo "✗ Бот не запустился!"
    echo "Последние 20 строк логов:"
    journalctl -u taxibot -n 20 --no-pager
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
