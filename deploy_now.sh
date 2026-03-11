#!/bin/bash
# Quick deployment command for Yandex Traffic

echo "🚀 Deploying Yandex Traffic to production..."
echo ""

cd /opt/taxibot

# Make script executable if needed
chmod +x update_bot.sh

# Run update
./update_bot.sh

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check traffic logs:"
echo "tail -f bot.log | grep traffic"
