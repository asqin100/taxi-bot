#!/bin/bash
# Команды для выполнения на сервере

# 1. Исправить права Git
git config --global --add safe.directory /opt/taxibot

# 2. Обновить код
cd /opt/taxibot
git pull origin main

# 3. Перезапустить бота
systemctl restart taxibot
sleep 3

# 4. Запустить диагностику
bash fix_webhook_complete.sh
