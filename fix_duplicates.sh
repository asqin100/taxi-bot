#!/bin/bash
# Fix duplicate entries in .env

cd /opt/taxibot

# Backup
cp .env .env.backup.duplicates

# Remove duplicate ROBOKASSA lines
grep -v "^ROBOKASSA_" .env > .env.tmp

# Add ROBOKASSA settings once
cat >> .env.tmp << 'EOF'
ROBOKASSA_MERCHANT_LOGIN=kefpulse
ROBOKASSA_PASSWORD1=i9MBFKM8C2j1E4rBZYNU
ROBOKASSA_PASSWORD2=mrjNy9n8xNuX1BAEq4Q8
ROBOKASSA_TEST_MODE=False
EOF

# Replace .env
mv .env.tmp .env

echo "✅ Дубликаты удалены"
echo ""
echo "Новый .env:"
grep ROBOKASSA .env
echo ""

# Restart bot
systemctl restart taxibot
sleep 3

if systemctl is-active --quiet taxibot; then
    echo "✅ Бот перезапущен"
else
    echo "❌ Ошибка перезапуска"
fi
