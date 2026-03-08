#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ПРОВЕРКА ДОСТУПНОСТИ RESULT URL ИЗ ИНТЕРНЕТА"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "Проверяю, доступен ли Result URL извне..."
echo ""

# Test from localhost
echo "[1] Тест с localhost (внутри сервера):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "http://localhost:8080/webhook/robokassa/result?test=1"
echo ""

# Test from external IP
echo "[2] Тест с внешнего IP (как видит Robokassa):"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "http://5.42.110.16:8080/webhook/robokassa/result?test=1"
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo "Если оба теста показывают HTTP Status: 400 - это нормально!"
echo "Endpoint работает, но отклоняет запросы без правильной подписи."
echo ""
echo "Если HTTP Status: 000 или timeout - порт недоступен извне."
echo ""
