#!/bin/bash
# Check current Robokassa passwords in bot

echo "Проверяю пароли в .env файле бота..."
echo ""

cd /opt/taxibot

echo "Merchant Login:"
grep ROBOKASSA_MERCHANT_LOGIN .env | cut -d'=' -f2
echo ""

echo "Password #1 (первые 10 символов):"
grep ROBOKASSA_PASSWORD1 .env | cut -d'=' -f2 | cut -c1-10
echo ""

echo "Password #2 (первые 10 символов):"
grep ROBOKASSA_PASSWORD2 .env | cut -d'=' -f2 | cut -c1-10
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Сравните эти пароли с паролями в личном кабинете Robokassa!"
echo ""
echo "Если пароли НЕ совпадают - нужно либо:"
echo "  1. Обновить пароли в .env файле бота"
echo "  2. Или сгенерировать новые в Robokassa и обновить в боте"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
