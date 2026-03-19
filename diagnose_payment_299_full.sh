#!/bin/bash
echo "════════════════════════════════════════════════════════════"
echo "  ОБНОВЛЕНИЕ БОТА И ДИАГНОСТИКА ПЛАТЕЖА 299₽"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "[1] Обновление кода..."
git pull origin main
echo ""

echo "[2] Перезапуск бота..."
systemctl restart taxibot
sleep 3
echo ""

echo "[3] Статус бота:"
systemctl is-active taxibot && echo "✅ Работает" || echo "❌ НЕ РАБОТАЕТ"
echo ""

echo "[4] ДЕТАЛЬНЫЕ ЛОГИ ОБРАБОТКИ ПЛАТЕЖА 299₽:"
echo "────────────────────────────────────────────────────────────"
journalctl -u taxibot --since "30 minutes ago" --no-pager | grep -B 2 -A 10 "Processing payment result" | head -80
echo ""

echo "════════════════════════════════════════════════════════════"
