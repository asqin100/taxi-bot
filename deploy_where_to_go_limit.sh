#!/bin/bash
# Deployment script for "Where to go" limit check feature

echo "=========================================="
echo "DEPLOYING 'WHERE TO GO' LIMIT CHECK"
echo "=========================================="

# Step 1: Pull latest code
cd /opt/taxibot
git pull origin main

# Step 2: Restart bot (this will create the new table automatically via SQLAlchemy)
./update_bot.sh

echo ""
echo "Waiting 10 seconds for bot to restart..."
sleep 10

# Step 3: Clear usage data for @abubakarone
echo ""
echo "Clearing usage data for @abubakarone..."
python3 clear_user_usage.py @abubakarone

# Step 4: Check bot status
echo ""
echo "Checking bot status..."
systemctl status taxibot --no-pager | head -15

echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Test the feature:"
echo "1. Open bot as @abubakarone"
echo "2. Click 'Куда ехать' button"
echo "3. Should show usage counter: 1/3"
echo "4. Try 3 more times - 4th attempt should show limit error"
echo ""
echo "Check logs:"
echo "tail -50 /opt/taxibot/bot.log | grep -E 'Where to go|where_to_go|limit'"
