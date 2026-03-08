#!/bin/bash
# Автоматическая настройка Robokassa на сервере

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     АВТОМАТИЧЕСКАЯ НАСТРОЙКА ROBOKASSA НА СЕРВЕРЕ         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Шаг 1: Перейти в директорию проекта
echo "[1/7] Переход в директорию проекта..."
cd /opt/taxibot || { echo "❌ Ошибка: директория /opt/taxibot не найдена"; exit 1; }

# Шаг 2: Обновить код
echo "[2/7] Обновление кода из GitHub..."
git pull origin main || { echo "❌ Ошибка при git pull"; exit 1; }

# Шаг 3: Проверить, есть ли уже настройки Robokassa
echo "[3/7] Проверка настроек в .env..."
if grep -q "ROBOKASSA_MERCHANT_LOGIN" .env; then
    echo "⚠️  Настройки Robokassa уже есть в .env"
    echo "Хочешь перезаписать? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo "Пропускаем обновление .env"
    else
        # Удалить старые настройки
        sed -i '/ROBOKASSA_/d' .env
        sed -i '/PAYMENT_PROVIDER/d' .env
        # Добавить новые
        cat >> .env << 'EOF'

# Robokassa Payment Settings
ROBOKASSA_MERCHANT_LOGIN=kefpulse
ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42
ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs
ROBOKASSA_TEST_MODE=False
PAYMENT_PROVIDER=robokassa
EOF
        echo "✓ Настройки Robokassa обновлены"
    fi
else
    # Добавить настройки
    cat >> .env << 'EOF'

# Robokassa Payment Settings
ROBOKASSA_MERCHANT_LOGIN=kefpulse
ROBOKASSA_PASSWORD1=Er1jVuWGOj0I9weDrs42
ROBOKASSA_PASSWORD2=ED44A3KMHu6r7eGWhcGs
ROBOKASSA_TEST_MODE=False
PAYMENT_PROVIDER=robokassa
EOF
    echo "✓ Настройки Robokassa добавлены в .env"
fi

# Шаг 4: Открыть порт 8080
echo "[4/7] Открытие порта 8080..."
sudo ufw allow 8080/tcp 2>/dev/null || echo "⚠️  Не удалось открыть порт (возможно, уже открыт)"
sudo ufw reload 2>/dev/null || echo "⚠️  Не удалось перезагрузить firewall"

# Шаг 5: Перезапустить бота
echo "[5/7] Перезапуск бота..."
systemctl restart taxibot || { echo "❌ Ошибка при перезапуске бота"; exit 1; }

# Подождать 3 секунды
sleep 3

# Шаг 6: Проверить статус
echo "[6/7] Проверка статуса бота..."
if systemctl is-active --quiet taxibot; then
    echo "✓ Бот запущен"
else
    echo "❌ Бот не запущен! Проверь логи: journalctl -u taxibot -n 50"
    exit 1
fi

# Шаг 7: Проверить порт
echo "[7/7] Проверка порта 8080..."
if netstat -tlnp | grep -q ":8080"; then
    echo "✓ Порт 8080 слушается"
else
    echo "⚠️  Порт 8080 не слушается. Проверь логи бота."
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    ✅ ГОТОВО!                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Следующие шаги:"
echo ""
echo "1. Настрой Result URL в Robokassa:"
echo "   https://auth.robokassa.ru/"
echo "   → Магазин kefpulse → Технические настройки"
echo "   → БОЕВОЙ РЕЖИМ"
echo "   → Result URL: http://5.42.110.16:8080/webhook/robokassa/result"
echo "   → Метод: GET"
echo "   → Сохранить"
echo ""
echo "2. Сделай тестовый платеж:"
echo "   @KefPulse_bot → /menu → 💎 Подписка → ⬆️ Улучшить тариф"
echo "   → 🧪 ТЕСТ — 5₽ (1 день) → Оплатить"
echo ""
echo "3. Смотри логи в реальном времени:"
echo "   journalctl -u taxibot -f"
echo ""
echo "Должно появиться:"
echo "   'Received Robokassa Result callback'"
echo "   'Successfully processed Robokassa payment'"
echo "   'Sent payment confirmation to user'"
echo ""
