#!/bin/bash
cd /opt/taxibot && \
git pull origin main && \
echo "=== ТЕСТ АДМИН ФУНКЦИЙ ===" && \
source venv/bin/activate && \
python test_admin.py && \
echo "" && \
echo "=== ПРОВЕРКА ЛОГОВ ВЕБА ===" && \
tail -100 bot.log | grep -E "(admin|recent-users|Error|error)" | tail -20
