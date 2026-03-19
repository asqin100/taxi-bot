#!/bin/bash
# Universal bot update script

set -e  # Exit on error

echo "🔄 Updating taxi-bot..."
echo ""

# 1. Update code
echo "📥 Pulling latest code..."
cd /opt/taxibot
git reset --hard
git pull origin main

# 2. Stop bot
echo "⏹ Stopping bot..."
pkill -9 -f "python.*bot.main" 2>/dev/null || true
sleep 2

# 3. Run migrations if exist
echo "🗄 Running migrations..."
if [ -f "migrate_preferred_tariff.py" ]; then
    venv/bin/python migrate_preferred_tariff.py || true
fi
if [ -f "fix_db.py" ]; then
    venv/bin/python fix_db.py || true
fi

# 4. Start bot
echo "▶️ Starting bot..."
nohup venv/bin/python -m bot.main >> bot.log 2>&1 &
sleep 5

# 5. Check status
echo ""
echo "✅ Bot status:"
if ps aux | grep "python -m bot.main" | grep -v grep > /dev/null; then
    echo "✅ Bot is running"
    ps aux | grep "python -m bot.main" | grep -v grep
else
    echo "❌ Bot is not running!"
    echo "Last 20 lines of log:"
    tail -20 bot.log
    exit 1
fi

echo ""
echo "📋 Recent logs:"
tail -10 bot.log

echo ""
echo "✅ Update complete!"
