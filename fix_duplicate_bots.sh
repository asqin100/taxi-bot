#!/bin/bash
# Fix duplicate bot instances on production server
# Run this on the server: bash fix_duplicate_bots.sh

echo "═══════════════════════════════════════════════════════════════"
echo "  Fixing duplicate bot instances"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Step 1: Stop systemd service
echo "[1/6] Stopping taxibot service..."
sudo systemctl stop taxibot
sleep 2

# Step 2: Check for running processes
echo "[2/6] Checking for running bot processes..."
PROCESSES=$(ps aux | grep "python.*bot/main.py" | grep -v grep)
if [ -n "$PROCESSES" ]; then
    echo "Found running processes:"
    echo "$PROCESSES"
    echo ""
    echo "[3/6] Killing hanging processes..."
    sudo pkill -9 -f "python.*bot/main.py"
    sleep 2
else
    echo "No hanging processes found."
fi

# Step 3: Verify all processes are stopped
echo "[4/6] Verifying all processes stopped..."
REMAINING=$(ps aux | grep "python.*bot/main.py" | grep -v grep)
if [ -n "$REMAINING" ]; then
    echo "ERROR: Some processes still running!"
    echo "$REMAINING"
    exit 1
else
    echo "✅ All bot processes stopped."
fi

# Step 4: Start bot cleanly
echo "[5/6] Starting bot..."
sudo systemctl start taxibot
sleep 3

# Step 5: Check status
echo "[6/6] Checking bot status..."
sudo systemctl status taxibot --no-pager -l

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Checking logs for errors..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Show last 20 lines of logs
sudo journalctl -u taxibot -n 20 --no-pager

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Checking for TelegramConflictError..."
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Wait a bit for bot to start polling
sleep 5

# Check for conflict errors in recent logs
CONFLICTS=$(sudo journalctl -u taxibot -n 50 --no-pager | grep -c "TelegramConflictError")

if [ "$CONFLICTS" -gt 0 ]; then
    echo "❌ STILL FOUND $CONFLICTS TelegramConflictError(s)"
    echo "There may be another bot instance running elsewhere."
    echo ""
    echo "Check all Python processes:"
    ps aux | grep python
else
    echo "✅ No TelegramConflictError found!"
    echo "✅ Bot is running cleanly."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Done! Monitor logs with:"
echo "  sudo journalctl -u taxibot -f"
echo "═══════════════════════════════════════════════════════════════"
