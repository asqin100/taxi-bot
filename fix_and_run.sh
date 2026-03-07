#!/bin/bash
# Fix Git ownership and run webhook fix

echo "Исправляю права на репозиторий..."
git config --global --add safe.directory /opt/taxibot

echo "Обновляю код..."
cd /opt/taxibot
git pull origin main

echo ""
echo "Запускаю диагностику..."
bash fix_webhook_complete.sh
