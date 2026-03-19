# Тестирование Robokassa интеграции

## Шаг 1: Настройка .env

Добавьте в `.env`:

```bash
# Тестовые данные Robokassa
ROBOKASSA_MERCHANT_LOGIN=demo
ROBOKASSA_PASSWORD1=password1
ROBOKASSA_PASSWORD2=password2
ROBOKASSA_TEST_MODE=True
PAYMENT_PROVIDER=robokassa

# URL вашего сервера (для локального тестирования используйте ngrok)
WEBAPP_URL=https://your-ngrok-url.ngrok.io
```

## Шаг 2: Локальное тестирование с ngrok

1. Установите ngrok: https://ngrok.com/download

2. Запустите бота локально:
```bash
python -m bot.main
```

3. В другом терминале запустите ngrok:
```bash
ngrok http 8080
```

4. Скопируйте ngrok URL (например: `https://abc123.ngrok.io`)

5. Обновите `.env`:
```bash
WEBAPP_URL=https://abc123.ngrok.io
```

6. Перезапустите бота

## Шаг 3: Настройка Robokassa

1. Войдите в личный кабинет Robokassa
2. Перейдите в "Технические настройки"
3. Включите "Тестовый режим"
4. Укажите URL:

**Result URL:**
```
https://abc123.ngrok.io/webhook/robokassa/result
```

**Success URL:**
```
https://abc123.ngrok.io/webhook/robokassa/success
```

**Fail URL:**
```
https://abc123.ngrok.io/webhook/robokassa/fail
```

**Метод:** GET

## Шаг 4: Тестовый платеж

1. Откройте бота в Telegram
2. Нажмите "⭐ Подписка"
3. Выберите "⬆️ Улучшить тариф"
4. Выберите тариф (например, Pro - 299₽)
5. Нажмите "💳 Оплатить картой"

Вы будете перенаправлены на страницу Robokassa.

## Шаг 5: Тестовая оплата

Используйте тестовую карту:
- **Номер:** 5555 5555 5555 5599
- **Срок:** любая будущая дата (например, 12/25)
- **CVV:** любые 3 цифры (например, 123)
- **Имя:** любое (например, TEST USER)

Нажмите "Оплатить"

## Шаг 6: Проверка результата

### В логах бота должно появиться:

```
INFO: Received Robokassa Result callback: InvId=1234567890
INFO: Successfully processed Robokassa payment 1234567890 for user 12345
```

### В Telegram:

После оплаты вы будете перенаправлены на Success URL, затем можете вернуться в бот.

Проверьте подписку:
1. Откройте бота
2. Нажмите "⭐ Подписка"
3. Должно показать активную подписку Pro

## Шаг 7: Проверка в базе данных

```bash
# Подключитесь к БД
psql taxibot_db

# Проверьте подписку пользователя
SELECT telegram_id, tier, expires_at, is_active 
FROM subscriptions 
WHERE user_id = (SELECT id FROM users WHERE telegram_id = YOUR_TELEGRAM_ID);
```

## Отладка

### Проблема: Result URL не вызывается

**Решение:**
1. Проверьте что ngrok работает: `curl https://abc123.ngrok.io/api/zones`
2. Проверьте что URL правильно указан в Robokassa
3. Проверьте логи ngrok: в терминале ngrok должны быть запросы

### Проблема: Invalid signature

**Решение:**
1. Убедитесь что пароли #1 и #2 скопированы правильно
2. Проверьте что нет лишних пробелов в .env
3. Проверьте порядок параметров в подписи

### Проблема: Amount mismatch

**Решение:**
1. Проверьте что цена в SUBSCRIPTION_PRICES совпадает с ценой в Robokassa
2. Формат должен быть: 299.00 (с двумя знаками после запятой)

## Переход на боевой режим

После успешного тестирования:

1. Обновите `.env`:
```bash
ROBOKASSA_TEST_MODE=False
WEBAPP_URL=https://kefpulse.ru
```

2. В Robokassa:
   - Выключите "Тестовый режим"
   - Обновите Result URL на боевой домен
   - Проверьте что пароли #1 и #2 для боевого режима

3. Перезапустите бота:
```bash
sudo systemctl restart taxibot
```

4. Проверьте логи:
```bash
journalctl -u taxibot -n 50 -f
```

## Мониторинг платежей

### Проверка логов платежей:

```bash
# Все платежи Robokassa
journalctl -u taxibot --no-pager | grep -i robokassa

# Успешные платежи
journalctl -u taxibot --no-pager | grep "Successfully processed Robokassa"

# Ошибки
journalctl -u taxibot --no-pager | grep -i "error.*robokassa"
```

### Проверка в БД:

```sql
-- Последние 10 подписок
SELECT u.telegram_id, u.username, s.tier, s.started_at, s.expires_at
FROM subscriptions s
JOIN users u ON s.user_id = u.id
ORDER BY s.started_at DESC
LIMIT 10;

-- Статистика по тарифам
SELECT tier, COUNT(*) as count, SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active
FROM subscriptions
GROUP BY tier;
```
