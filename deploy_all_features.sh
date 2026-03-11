#!/bin/bash
# Complete deployment script for all new features

echo "🚀 Deploying 11 new features to production..."
echo ""

cd /opt/taxibot

# 1. Update code
echo "📥 Updating code from GitHub..."
chmod +x update_bot.sh
./update_bot.sh

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 New features deployed:"
echo "  1. ✅ Filters in coefficient notifications"
echo "  2. ✅ Lunch feature (find restaurants)"
echo "  3. ✅ Usage limits for 'Where to go'"
echo "  4. ✅ Fixed geocoder (metro from zone center)"
echo "  5. ✅ VPN referral button"
echo "  6. ✅ Ban system in admin panel"
echo "  7. ✅ Events without coefficient threshold"
echo "  8. ✅ Geo alerts usage counter"
echo "  9. ✅ Minimum price display"
echo " 10. ✅ Business tariff MKAD restriction"
echo ""
echo "⚠️  Required: Set YANDEX_GEOCODER_API_KEY in .env for lunch feature"
echo ""
echo "📊 Check logs:"
echo "tail -f bot.log"
