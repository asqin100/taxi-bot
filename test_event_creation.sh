#!/bin/bash
# Test event creation on production server

echo "Testing event creation..."
echo ""
echo "1. Check if bot is running:"
systemctl status taxibot --no-pager | head -5

echo ""
echo "2. Check recent logs for event-related errors:"
tail -100 /opt/taxibot/bot.log | grep -i "event\|error" | tail -20

echo ""
echo "3. Try to create a test event via curl:"
echo "   (You need to get admin token first from browser console: localStorage.getItem('admin_token'))"
echo ""
echo "   curl -X POST https://kefpulse.ru/admin/api/events/create \\"
echo "     -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"name\":\"Test Event\",\"zone_id\":\"luzhniki\",\"event_type\":\"concert\",\"end_time\":\"2026-03-15T20:00:00\"}'"
