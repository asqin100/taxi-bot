#!/bin/bash
# Deploy webhook fix to server

echo "=== Deploying Robokassa webhook fix ==="
echo ""

# Stop bot
echo "1. Stopping bot..."
sudo systemctl stop taxibot

# Pull latest code
echo "2. Pulling latest code..."
cd /opt/taxibot
git pull origin main

# Restart bot
echo "3. Starting bot..."
sudo systemctl start taxibot

# Wait for bot to start
sleep 3

# Check status
echo "4. Checking bot status..."
sudo systemctl status taxibot --no-pager -l

echo ""
echo "=== Deployment complete ==="
echo ""
echo "Now test the webhook:"
echo "  cd /opt/taxibot"
echo "  source venv/bin/activate"
echo "  python test_webhook.py YOUR_TELEGRAM_ID"
echo ""
