#!/bin/bash
# Check logs for Robokassa webhook calls

echo "Проверяю логи за последние 10 минут..."
echo ""

echo "1. Поиск запросов от Robokassa:"
journalctl -u taxibot --since "10 minutes ago" | grep -i "robokassa" | tail -20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2. Поиск ошибок:"
journalctl -u taxibot --since "10 minutes ago" | grep -i "error" | tail -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3. Все логи за последние 5 минут:"
journalctl -u taxibot --since "5 minutes ago" | tail -50

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
