#!/bin/bash
# Check current bot settings

echo "Текущие настройки бота:"
grep ROBOKASSA_TEST_MODE /opt/taxibot/.env
echo ""
echo "Merchant login:"
grep ROBOKASSA_MERCHANT_LOGIN /opt/taxibot/.env
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Магазин АКТИВЕН, но ошибка 29 означает, что Result URL"
echo "не сохранен для БОЕВОГО режима в личном кабинете Robokassa."
echo ""
echo "В Robokassa есть ДВА набора настроек:"
echo "  1. Для тестового режима (IsTest=1)"
echo "  2. Для боевого режима (IsTest=0)"
echo ""
echo "Вам нужно сохранить Result URL для БОЕВОГО режима!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
