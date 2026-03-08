#!/bin/bash
# Команды для сервера - скопируй и выполни по порядку

echo "=== ШАГ 1: Перейти в директорию проекта ==="
cd /opt/taxibot

echo ""
echo "=== ШАГ 2: Обновить код ==="
git pull origin main

echo ""
echo "=== ШАГ 3: Обновить .env ==="
echo "Добавь эти строки в .env:"
echo ""
echo "ROBOKASSA_MERCHANT_LOGIN=kefpulse"
echo "ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42"
echo "ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs"
echo "ROBOKASSA_TEST_MODE=False"
echo "PAYMENT_PROVIDER=robokassa"
echo ""
echo "Команда для редактирования:"
echo "nano .env"

echo ""
echo "=== ШАГ 4: Перезапустить бота ==="
echo "systemctl restart taxibot"
echo "systemctl status taxibot"

echo ""
echo "=== ШАГ 5: Проверить порт 8080 ==="
echo "sudo ufw allow 8080/tcp"
echo "sudo ufw reload"
echo "netstat -tlnp | grep 8080"

echo ""
echo "=== ШАГ 6: Посмотреть логи ==="
echo "journalctl -u taxibot -f"
