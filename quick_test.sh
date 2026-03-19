#!/bin/bash

# Quick test script for Robokassa integration
# Run this on the server to verify everything is ready

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         ROBOKASSA INTEGRATION - QUICK TEST                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Bot service status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Checking bot service status..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if systemctl is-active --quiet taxibot; then
    echo -e "${GREEN}✅ Bot service is running${NC}"
else
    echo -e "${RED}❌ Bot service is NOT running${NC}"
    echo "   Run: systemctl start taxibot"
fi
echo ""

# Check 2: Port 8080 listening
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Checking if port 8080 is listening..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if netstat -tlnp | grep -q ":8080"; then
    echo -e "${GREEN}✅ Port 8080 is listening${NC}"
    netstat -tlnp | grep ":8080"
else
    echo -e "${RED}❌ Port 8080 is NOT listening${NC}"
    echo "   Bot may not be running or not configured correctly"
fi
echo ""

# Check 3: Firewall status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Checking firewall rules..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "8080.*ALLOW"; then
        echo -e "${GREEN}✅ Port 8080 is allowed in firewall${NC}"
    else
        echo -e "${RED}❌ Port 8080 is NOT allowed in firewall${NC}"
        echo "   Run: sudo ufw allow 8080/tcp"
    fi
else
    echo -e "${YELLOW}⚠️  UFW not found, skipping firewall check${NC}"
fi
echo ""

# Check 4: Webhook accessibility from localhost
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Testing webhook from localhost..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/webhook/robokassa/result 2>/dev/null)
if [ "$response" = "400" ]; then
    echo -e "${GREEN}✅ Webhook responds (HTTP 400 expected)${NC}"
else
    echo -e "${RED}❌ Webhook not responding (got HTTP $response)${NC}"
fi
echo ""

# Check 5: Environment variables
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Checking Robokassa configuration..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f .env ]; then
    if grep -q "ROBOKASSA_MERCHANT_LOGIN=kefpulse" .env; then
        echo -e "${GREEN}✅ Merchant login configured${NC}"
    else
        echo -e "${RED}❌ Merchant login not found in .env${NC}"
    fi

    if grep -q "ROBOKASSA_PASSWORD1=" .env && ! grep -q "ROBOKASSA_PASSWORD1=$" .env; then
        echo -e "${GREEN}✅ Password #1 configured${NC}"
    else
        echo -e "${RED}❌ Password #1 not configured${NC}"
    fi

    if grep -q "ROBOKASSA_PASSWORD2=" .env && ! grep -q "ROBOKASSA_PASSWORD2=$" .env; then
        echo -e "${GREEN}✅ Password #2 configured${NC}"
    else
        echo -e "${RED}❌ Password #2 not configured${NC}"
    fi

    if grep -q "ROBOKASSA_TEST_MODE=False" .env; then
        echo -e "${GREEN}✅ Production mode enabled${NC}"
    else
        echo -e "${YELLOW}⚠️  Test mode or not configured${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
fi
echo ""

# Check 6: Recent logs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Recent bot logs (last 5 lines)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
journalctl -u taxibot -n 5 --no-pager
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                      SUMMARY                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. If all checks passed, verify Result URL in Robokassa:"
echo "   https://auth.robokassa.ru/"
echo ""
echo "2. Result URL should be:"
echo "   http://5.42.110.16:8080/webhook/robokassa/result"
echo ""
echo "3. Start monitoring and do a test payment:"
echo "   bash monitor_webhook.sh"
echo ""
echo "4. In bot: /menu → 💎 Подписка → 🧪 ТЕСТ — 5₽"
echo ""
