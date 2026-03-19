#!/bin/bash
# Deployment and Testing Script for Taxi Bot
# Run this script on your server to update and test the bot

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           TAXI BOT - DEPLOYMENT & TESTING                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Update code
echo "📦 Step 1: Updating code from GitHub..."
cd /opt/taxibot
git fetch origin
BEFORE_COMMIT=$(git rev-parse HEAD)
git pull origin main
AFTER_COMMIT=$(git rev-parse HEAD)

if [ "$BEFORE_COMMIT" = "$AFTER_COMMIT" ]; then
    echo -e "${YELLOW}⚠ No new commits. Already up to date.${NC}"
else
    echo -e "${GREEN}✓ Updated from $BEFORE_COMMIT to $AFTER_COMMIT${NC}"
    git log --oneline $BEFORE_COMMIT..$AFTER_COMMIT
fi
echo ""

# Step 2: Restart bot
echo "🔄 Step 2: Restarting bot service..."
systemctl restart taxibot
sleep 3
echo -e "${GREEN}✓ Bot restarted${NC}"
echo ""

# Step 3: Check status
echo "🔍 Step 3: Checking bot status..."
if systemctl is-active --quiet taxibot; then
    echo -e "${GREEN}✓ Bot is running${NC}"
else
    echo -e "${RED}✗ Bot is NOT running!${NC}"
    systemctl status taxibot
    exit 1
fi
echo ""

# Step 4: Check logs for errors
echo "📋 Step 4: Checking recent logs for errors..."
ERROR_COUNT=$(journalctl -u taxibot -n 100 --no-pager | grep -i "error\|exception\|traceback" | wc -l)
if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ No errors in recent logs${NC}"
else
    echo -e "${YELLOW}⚠ Found $ERROR_COUNT error lines in logs:${NC}"
    journalctl -u taxibot -n 100 --no-pager | grep -i "error\|exception" | tail -5
fi
echo ""

# Step 5: Check coefficients
echo "📊 Step 5: Checking coefficient fetching..."
COEFF_COUNT=$(journalctl -u taxibot -n 50 --no-pager | grep -i "surge\|coefficient" | wc -l)
if [ $COEFF_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Coefficients are being fetched${NC}"
    journalctl -u taxibot -n 50 --no-pager | grep -i "surge\|coefficient" | tail -3
else
    echo -e "${YELLOW}⚠ No coefficient activity in recent logs${NC}"
fi
echo ""

# Step 6: Check domain
echo "🌐 Step 6: Checking domain (kefpulse.ru)..."
if curl -s -o /dev/null -w "%{http_code}" https://kefpulse.ru | grep -q "200"; then
    echo -e "${GREEN}✓ Domain is accessible (HTTP 200)${NC}"
else
    echo -e "${RED}✗ Domain is not accessible${NC}"
fi
echo ""

# Step 7: Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           DEPLOYMENT COMPLETE                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Next steps:"
echo "1. Open Telegram and test the bot with /start"
echo "2. Test 'Куда ехать?' button"
echo "3. Test 'Мой кабинет' → 'Финансы' → 'Карта заработка' (Elite)"
echo "4. Check that 'Главное меню' button works from heatmap"
echo "5. Open https://kefpulse.ru and check coefficients on map"
echo ""
echo "📋 Full testing checklist: /opt/taxibot/FINAL_TESTING_CHECKLIST.md"
echo ""
