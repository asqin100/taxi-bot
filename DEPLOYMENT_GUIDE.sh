#!/bin/bash
# Complete deployment and testing guide for lunch feature

echo "=========================================="
echo "DEPLOYMENT GUIDE FOR LUNCH FEATURE FIX"
echo "=========================================="
echo ""
echo "Run these commands on your production server (kefpulse.ru):"
echo ""
echo "-----------------------------------------------------------"
echo "STEP 1: Deploy the changes"
echo "-----------------------------------------------------------"
cat << 'DEPLOY'
cd /opt/taxibot
git stash
git pull origin main
chmod +x update_bot.sh
./update_bot.sh
DEPLOY

echo ""
echo "-----------------------------------------------------------"
echo "STEP 2: Wait 10 seconds for bot to restart"
echo "-----------------------------------------------------------"
echo "sleep 10"
echo ""

echo "-----------------------------------------------------------"
echo "STEP 3: Test if Nominatim API is accessible from server"
echo "-----------------------------------------------------------"
cat << 'TEST'
cd /opt/taxibot
python3 test_nominatim_server.py
TEST

echo ""
echo "-----------------------------------------------------------"
echo "STEP 4: Test the button in Telegram"
echo "-----------------------------------------------------------"
echo "1. Open your bot in Telegram"
echo "2. Click 'Заехать на обед'"
echo "3. Immediately run the next command to check logs"
echo ""

echo "-----------------------------------------------------------"
echo "STEP 5: Check the logs"
echo "-----------------------------------------------------------"
cat << 'LOGS'
tail -100 /opt/taxibot/bot.log | grep -E "lunch|restaurant|Nominatim|_search_restaurants"
LOGS

echo ""
echo "-----------------------------------------------------------"
echo "STEP 6: If you see errors, send me the log output"
echo "-----------------------------------------------------------"
echo ""
echo "=========================================="
