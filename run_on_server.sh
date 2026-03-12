#!/bin/bash
# Команды для выполнения на сервере (копируйте по одной)

# 1. Дать права на выполнение скрипта
chmod +x /opt/taxibot/update_bot.sh

# 2. Принудительно обновить до последней версии
cd /opt/taxibot && git fetch origin && git reset --hard origin/main

# 3. Запустить обновление бота
cd /opt/taxibot && ./update_bot.sh

# 4. Подождать 5 секунд
sleep 5

# 5. Проверить статус бота
systemctl status taxibot --no-pager | head -15

echo ""
echo "=========================================="
echo "Теперь протестируйте кнопку 'Заехать на обед' в боте"
echo "=========================================="
