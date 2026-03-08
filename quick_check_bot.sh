#!/bin/bash
# Быстрая проверка статуса бота

echo "╔════════════════════════════════════════════════════════════╗" > /tmp/bot_check.txt
echo "║         ПРОВЕРКА СТАТУСА БОТА                              ║" >> /tmp/bot_check.txt
echo "╚════════════════════════════════════════════════════════════╝" >> /tmp/bot_check.txt
echo "" >> /tmp/bot_check.txt

echo "[1] СТАТУС БОТА:" >> /tmp/bot_check.txt
if systemctl is-active --quiet taxibot; then
    echo "✓ Бот запущен (active)" >> /tmp/bot_check.txt
else
    echo "✗ Бот не запущен" >> /tmp/bot_check.txt
fi
echo "" >> /tmp/bot_check.txt

echo "[2] ПОРТ 8080:" >> /tmp/bot_check.txt
if netstat -tlnp 2>/dev/null | grep -q ":8080"; then
    echo "✓ Порт 8080 слушается - БОТ РАБОТАЕТ!" >> /tmp/bot_check.txt
    netstat -tlnp 2>/dev/null | grep ":8080" >> /tmp/bot_check.txt
else
    echo "✗ Порт 8080 НЕ слушается - бот падает" >> /tmp/bot_check.txt
fi
echo "" >> /tmp/bot_check.txt

echo "[3] ОШИБКИ ПАРСИНГА .env:" >> /tmp/bot_check.txt
if journalctl -u taxibot --since "2 minutes ago" --no-pager 2>/dev/null | grep -q "could not parse"; then
    echo "✗ Есть ошибки парсинга:" >> /tmp/bot_check.txt
    journalctl -u taxibot --since "2 minutes ago" --no-pager 2>/dev/null | grep "could not parse" >> /tmp/bot_check.txt
else
    echo "✓ Ошибок парсинга нет" >> /tmp/bot_check.txt
fi
echo "" >> /tmp/bot_check.txt

echo "[4] НАСТРОЙКИ ROBOKASSA:" >> /tmp/bot_check.txt
cd /opt/taxibot
if grep -q "ROBOKASSA_MERCHANT_LOGIN" .env 2>/dev/null; then
    echo "✓ Настройки найдены:" >> /tmp/bot_check.txt
    grep "ROBOKASSA\|PAYMENT_PROVIDER" .env >> /tmp/bot_check.txt
else
    echo "✗ Настройки не найдены" >> /tmp/bot_check.txt
fi
echo "" >> /tmp/bot_check.txt

echo "════════════════════════════════════════════════════════════" >> /tmp/bot_check.txt
echo "ВЫВОД СОХРАНЕН В: /tmp/bot_check.txt" >> /tmp/bot_check.txt
echo "════════════════════════════════════════════════════════════" >> /tmp/bot_check.txt

cat /tmp/bot_check.txt
