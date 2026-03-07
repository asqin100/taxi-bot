#!/bin/bash
# Check nginx configuration for webhook proxying

echo "=== Checking nginx configuration ==="
echo ""

echo "1. Nginx config files:"
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo "No sites-enabled directory"
echo ""

echo "2. Looking for taxibot/webhook configuration:"
grep -r "webhook" /etc/nginx/sites-enabled/ 2>/dev/null || echo "No webhook config found"
grep -r "8080" /etc/nginx/sites-enabled/ 2>/dev/null || echo "No 8080 proxy found"
echo ""

echo "3. Checking if nginx is running:"
systemctl status nginx --no-pager -l | head -20
echo ""

echo "4. Checking ports:"
netstat -tlnp | grep -E "(80|443|8080)"
echo ""

echo "5. Testing webhook endpoint locally:"
curl -s http://localhost:8080/webhook/robokassa/success | head -20
echo ""

echo "6. Testing via nginx (if configured):"
curl -s http://localhost/webhook/robokassa/success | head -20
echo ""
