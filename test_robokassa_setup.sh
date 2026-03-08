#!/bin/bash

echo "========================================"
echo "  ТЕСТ ROBOKASSA ИНТЕГРАЦИИ"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Проверка 1: Настройки в .env"
if grep -q "ROBOKASSA_MERCHANT_LOGIN" .env; then
    echo -e "${GREEN}✓${NC} ROBOKASSA_MERCHANT_LOGIN найден"
else
    echo -e "${RED}✗${NC} ROBOKASSA_MERCHANT_LOGIN не найден"
    exit 1
fi

if grep -q "ROBOKASSA_PASSWORD1" .env; then
    echo -e "${GREEN}✓${NC} ROBOKASSA_PASSWORD1 найден"
else
    echo -e "${RED}✗${NC} ROBOKASSA_PASSWORD1 не найден"
    exit 1
fi

if grep -q "ROBOKASSA_PASSWORD2" .env; then
    echo -e "${GREEN}✓${NC} ROBOKASSA_PASSWORD2 найден"
else
    echo -e "${RED}✗${NC} ROBOKASSA_PASSWORD2 не найден"
    exit 1
fi

if grep -q "PAYMENT_PROVIDER=robokassa" .env; then
    echo -e "${GREEN}✓${NC} PAYMENT_PROVIDER установлен на robokassa"
else
    echo -e "${YELLOW}⚠${NC} PAYMENT_PROVIDER не установлен на robokassa"
fi

echo ""
echo "Проверка 2: Файлы интеграции"
if [ -f "bot/services/payment_robokassa.py" ]; then
    echo -e "${GREEN}✓${NC} payment_robokassa.py существует"
else
    echo -e "${RED}✗${NC} payment_robokassa.py не найден"
    exit 1
fi

echo ""
echo "Проверка 3: Синтаксис Python"
python -m py_compile bot/services/payment_robokassa.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} payment_robokassa.py: синтаксис OK"
else
    echo -e "${RED}✗${NC} payment_robokassa.py: ошибка синтаксиса"
    exit 1
fi

python -m py_compile bot/web/api.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} api.py: синтаксис OK"
else
    echo -e "${RED}✗${NC} api.py: ошибка синтаксиса"
    exit 1
fi

echo ""
echo "Проверка 4: Webhook endpoints"
if grep -q "webhook_robokassa_result" bot/web/api.py; then
    echo -e "${GREEN}✓${NC} webhook_robokassa_result найден"
else
    echo -e "${RED}✗${NC} webhook_robokassa_result не найден"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Запустить бота: python start_bot.py"
echo "2. Настроить Result URL в Robokassa"
echo "3. Сделать тестовый платеж 5₽"
echo ""
