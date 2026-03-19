#!/bin/bash
# Check current Robokassa settings

echo "Проверяю текущие настройки..."
echo ""

cd /opt/taxibot

echo "Настройки в .env:"
grep ROBOKASSA .env | grep -v PASSWORD | grep -v "^#"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "ОШИБКА 29 - Магазин не активирован или URL не сохранены"
echo ""
echo "Возможные причины:"
echo ""
echo "1. URL не сохранены в личном кабинете Robokassa"
echo "   Решение: Зайдите в Robokassa и СОХРАНИТЕ URL:"
echo "   - Result URL:  http://5.42.110.16:8080/webhook/robokassa/result"
echo "   - Success URL: http://5.42.110.16:8080/webhook/robokassa/success"
echo "   - Fail URL:    http://5.42.110.16:8080/webhook/robokassa/fail"
echo ""
echo "2. Магазин еще в тестовом режиме на стороне Robokassa"
echo "   Решение: Переключите магазин в боевой режим в личном кабинете"
echo ""
echo "3. Магазин не активирован"
echo "   Решение: Завершите активацию магазина в Robokassa"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Хотите вернуться в тестовый режим? (y/n)"
