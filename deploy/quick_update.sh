#!/bin/bash
# Quick update script for taxi-bot
# Run this on the server to deploy latest changes

set -e

echo "=== Updating taxi-bot ==="

cd /opt/taxibot

echo "1. Pulling latest changes from GitHub..."
sudo -u taxibot git pull

echo "2. Restarting bot service..."
systemctl restart taxibot

echo "3. Waiting for service to start..."
sleep 3

echo "4. Checking service status..."
systemctl status taxibot --no-pager

echo ""
echo "=== Update complete! ==="
echo ""
echo "To view logs:"
echo "  journalctl -u taxibot -f"
echo ""
