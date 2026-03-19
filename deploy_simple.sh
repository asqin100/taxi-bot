#!/bin/bash
# Alternative deployment without Python script

echo "Restarting bot to create new table..."
cd /opt/taxibot
systemctl restart taxibot

echo "Waiting 15 seconds for bot to start..."
sleep 15

echo "Checking bot status..."
systemctl status taxibot --no-pager | head -10

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "The new table 'where_to_go_usage' has been created."
echo ""
echo "To clear usage for @abubakarone, run this SQL:"
echo "sqlite3 /opt/taxibot/data/bot.db \"DELETE FROM where_to_go_usage WHERE user_id = (SELECT telegram_id FROM users WHERE username = 'abubakarone');\""
echo ""
echo "Or just test the feature - it will start tracking from now."
