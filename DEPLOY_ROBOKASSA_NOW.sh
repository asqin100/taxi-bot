#!/bin/bash

# Robokassa Deployment Script
# Run this on the server: bash DEPLOY_ROBOKASSA_NOW.sh

echo "=== Robokassa Deployment ==="
echo ""

# Stop the bot
echo "1. Stopping bot..."
sudo systemctl stop taxibot

# Backup current .env
echo "2. Backing up .env..."
sudo -u taxibot cp /opt/taxibot/.env /opt/taxibot/.env.backup.$(date +%Y%m%d_%H%M%S)

# Add Robokassa settings to .env
echo "3. Adding Robokassa settings to .env..."
sudo -u taxibot bash -c 'cat >> /opt/taxibot/.env << "ENVEOF"

# Robokassa Payment Settings
ROBOKASSA_MERCHANT_LOGIN=kefpulse
ROBOKASSA_PASSWORD1=i9MBFKM8C2j1E4rBZYNU
ROBOKASSA_PASSWORD2=mrjNy9n8xNuX1BAEq4Q8
ROBOKASSA_TEST_MODE=True
PAYMENT_PROVIDER=robokassa
ENVEOF
'

# Pull latest code
echo "4. Pulling latest code..."
cd /opt/taxibot
sudo -u taxibot git pull origin main

# Start the bot
echo "5. Starting bot..."
sudo systemctl start taxibot

# Wait a bit
sleep 3

# Check status
echo "6. Checking status..."
sudo systemctl status taxibot --no-pager

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Configure Robokassa webhooks:"
echo "   - Result URL: https://kefpulse.ru/webhook/robokassa/result"
echo "   - Success URL: https://kefpulse.ru/webhook/robokassa/success"
echo "   - Fail URL: https://kefpulse.ru/webhook/robokassa/fail"
echo "   - Method: GET"
echo ""
echo "2. Test payment with card: 5555 5555 5555 5599"
echo ""
echo "3. Check logs: journalctl -u taxibot -n 50 -f"
