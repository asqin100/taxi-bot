#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  ДИАГНОСТИКА ПЛАТЕЖА 299₽"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Ищем упоминания 299 в логах за последние 10 минут:"
journalctl -u taxibot --since "10 minutes ago" --no-pager | grep -i "299" || echo "❌ Нет упоминаний 299₽"
echo ""

echo "[2] Ищем любые Robokassa webhook вызовы за последние 10 минут:"
journalctl -u taxibot --since "10 minutes ago" --no-pager | grep -i "robokassa" || echo "❌ Нет вызовов Robokassa webhook"
echo ""

echo "[3] Ищем ошибки за последние 10 минут:"
journalctl -u taxibot --since "10 minutes ago" --no-pager | grep -i "error\|exception" | tail -10 || echo "✅ Нет ошибок"
echo ""

echo "[4] Последние 30 строк логов:"
journalctl -u taxibot -n 30 --no-pager --output=cat
echo ""

echo "[5] Проверка порта 8080:"
netstat -tuln | grep 8080 || echo "❌ Порт 8080 не слушается"
echo ""

echo "════════════════════════════════════════════════════════════"
echo ""
echo "ЕСЛИ НЕТ ВЫЗОВОВ ROBOKASSA WEBHOOK:"
echo "  → Result URL не настроен в Robokassa"
echo "  → Или настроен неправильный URL"
echo ""
echo "ЕСЛИ ЕСТЬ ВЫЗОВЫ, НО ЕСТЬ ОШИБКИ:"
echo "  → Проблема с обработкой платежа (подпись, сумма, и т.д.)"
echo ""
echo "════════════════════════════════════════════════════════════"
