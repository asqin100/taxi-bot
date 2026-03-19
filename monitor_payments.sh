#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "  МОНИТОРИНГ ПЛАТЕЖЕЙ ROBOKASSA"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Ожидаю вызовы от Robokassa..."
echo "Нажми Ctrl+C для выхода"
echo ""
echo "────────────────────────────────────────────────────────────"

journalctl -u taxibot -f | grep --line-buffered -E "(Robokassa|payment|subscription)"
