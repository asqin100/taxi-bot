#!/bin/bash
echo "=== СТАТУС БОТА ==="
systemctl status taxibot --no-pager | head -15
echo ""
echo "=== СВЕЖИЕ ЛОГИ (последние 40 строк) ==="
tail -40 bot.log
echo ""
echo "=== ПРОВЕРКА ОШИБОК В СВЕЖИХ ЛОГАХ ==="
tail -100 bot.log | grep -i "error" | tail -10
