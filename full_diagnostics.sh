#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ПОЛНАЯ ДИАГНОСТИКА ROBOKASSA"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Текущие настройки .env:"
echo "────────────────────────────────────────────────────────────"
grep "ROBOKASSA" /opt/taxibot/.env
echo ""

echo "[2] Проверка доступности Result URL ИЗВНЕ (через интернет):"
echo "────────────────────────────────────────────────────────────"
curl -v http://5.42.110.16:8080/webhook/robokassa/result 2>&1 | head -20
echo ""

echo "[3] Проверка nginx (может перехватывать запросы):"
echo "────────────────────────────────────────────────────────────"
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "Nginx установлен, проверяю конфигурацию..."
    grep -A 10 "location.*webhook" /etc/nginx/sites-enabled/* 2>/dev/null || echo "Webhook routes не найдены в nginx"
else
    echo "Nginx не установлен или не активен"
fi
echo ""

echo "[4] Проверка firewall:"
echo "────────────────────────────────────────────────────────────"
if command -v ufw &> /dev/null; then
    ufw status | grep 8080 || echo "Порт 8080 не открыт в UFW"
else
    echo "UFW не установлен"
fi
echo ""

echo "[5] Проверка, слушается ли порт 8080:"
echo "────────────────────────────────────────────────────────────"
netstat -tuln | grep 8080 || ss -tuln | grep 8080
echo ""

echo "[6] Последние 5 платежей из базы данных:"
echo "────────────────────────────────────────────────────────────"
python3 << 'PYEOF'
import sqlite3
import os
os.chdir('/opt/taxibot')
conn = sqlite3.connect('data/bot.db')
cursor = conn.cursor()
cursor.execute("SELECT id, user_id, amount, status, created_at FROM payments ORDER BY created_at DESC LIMIT 5")
for row in cursor.fetchall():
    print(f"Payment ID: {row[0]}, User: {row[1]}, Amount: {row[2]}, Status: {row[3]}, Date: {row[4]}")
conn.close()
PYEOF
echo ""

echo "[7] Симуляция вызова Result URL от Robokassa:"
echo "────────────────────────────────────────────────────────────"
echo "Тестирую с фейковыми данными..."
curl -v "http://127.0.0.1:8080/webhook/robokassa/result?OutSum=5.00&InvId=999999&SignatureValue=test" 2>&1 | grep -E "(HTTP|ERROR|OK)"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "  РЕЗУЛЬТАТЫ ДИАГНОСТИКИ"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Скопируй весь вывод и пришли мне."
echo ""
