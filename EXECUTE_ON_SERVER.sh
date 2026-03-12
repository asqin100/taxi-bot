#!/bin/bash
# Выполните эти команды на сервере kefpulse.ru

# 1. Деплой
cd /opt/taxibot && git stash && git pull origin main && chmod +x update_bot.sh && ./update_bot.sh

# 2. Подождите 10 секунд
sleep 10

# 3. Проверьте доступность Nominatim API
python3 /opt/taxibot/test_nominatim_server.py

# 4. Протестируйте кнопку "Заехать на обед" в боте

# 5. Проверьте логи
tail -100 /opt/taxibot/bot.log | grep -E "lunch|restaurant|Nominatim|Error"
