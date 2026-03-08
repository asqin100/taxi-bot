#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  ПРОВЕРКА ЛОГОВ ПЛАТЕЖА 299₽"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Последние 50 строк логов (ищем платеж 299):"
journalctl -u taxibot -n 50 --no-pager --output=cat | grep -E "(299|Robokassa|payment|webhook)" || echo "Нет записей о платеже"
echo ""

echo "[2] Все логи за последние 5 минут:"
journalctl -u taxibot --since "5 minutes ago" --no-pager --output=cat | tail -30
echo ""

echo "════════════════════════════════════════════════════════════"
