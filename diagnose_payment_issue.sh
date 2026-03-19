#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  ДИАГНОСТИКА ПРОБЛЕМЫ С ПЛАТЕЖОМ"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Проверка логов за последние 10 минут (поиск Robokassa)..."
echo "────────────────────────────────────────────────────────────"
journalctl -u taxibot --since "10 minutes ago" --no-pager | grep -i robokassa
if [ $? -ne 0 ]; then
    echo "⚠️  НЕТ записей о Robokassa в логах!"
    echo "Это значит Result URL не был вызван Robokassa."
fi
echo ""

echo "[2] Все логи за последние 10 минут..."
echo "────────────────────────────────────────────────────────────"
journalctl -u taxibot --since "10 minutes ago" --no-pager | tail -50
echo ""

echo "[3] Проверка доступности webhook endpoints..."
echo "────────────────────────────────────────────────────────────"
echo "Тестирую Result URL:"
curl -s "http://localhost:8080/webhook/robokassa/result?test=1" || echo "✗ Result endpoint не отвечает"
echo ""
echo "Тестирую Success URL:"
curl -s "http://localhost:8080/webhook/robokassa/success?test=1" | head -5 || echo "✗ Success endpoint не отвечает"
echo ""

echo "[4] Проверка статуса бота..."
systemctl status taxibot --no-pager -l | head -15
echo ""

echo "════════════════════════════════════════════════════════════"
echo "  ВЫВОД"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Если в логах НЕТ записей о Robokassa - проблема в настройке"
echo "Result URL в личном кабинете Robokassa."
echo ""
echo "Result URL должен быть:"
echo "http://5.42.110.16:8080/webhook/robokassa/result"
echo ""
echo "Метод: GET"
echo "Раздел: БОЕВОЙ РЕЖИМ (не тестовый!)"
echo ""
