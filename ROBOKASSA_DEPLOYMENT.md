# Деплой Robokassa на сервер

## Что готово

✅ Интеграция Robokassa полностью реализована
✅ Поддержка тестового и боевого режима
✅ Webhook handlers для Result/Success/Fail URL
✅ Проверка MD5 подписи для безопасности
✅ Автоматическая активация подписки после оплаты
✅ Документация и инструкции по тестированию

## Шаги для деплоя

### 1. Получите данные от Robokassa

Войдите в личный кабинет Robokassa и получите:
- **Идентификатор магазина** (Merchant Login)
- **Пароль #1** (для формирования платежной ссылки)
- **Пароль #2** (для проверки результата оплаты)

### 2. Обновите .env на сервере

Подключитесь к серверу и добавьте в `/opt/taxibot/.env`:

```bash
# Robokassa настройки
ROBOKASSA_MERCHANT_LOGIN=ваш_логин
ROBOKASSA_PASSWORD1=ваш_пароль1
ROBOKASSA_PASSWORD2=ваш_пароль2
ROBOKASSA_TEST_MODE=True
PAYMENT_PROVIDER=robokassa
```

**Важно:** Сначала используйте `ROBOKASSA_TEST_MODE=True` для тестирования!

### 3. Настройте URL в Robokassa

В личном кабинете Robokassa укажите:

**Result URL (обязательно):**
```
https://kefpulse.ru/webhook/robokassa/result
```

**Success URL:**
```
https://kefpulse.ru/webhook/robokassa/success
```

**Fail URL:**
```
https://kefpulse.ru/webhook/robokassa/fail
```

**Метод отправки:** GET

### 4. Деплой на сервер

```bash
# Подключитесь к серверу
ssh root@5.42.110.16

# Перейдите в директорию
cd /opt/taxibot

# Остановите бота
sudo systemctl stop taxibot

# Получите обновления
sudo -u taxibot git pull origin main

# Проверьте .env (добавьте Robokassa настройки)
sudo -u taxibot nano .env

# Запустите бота
sudo systemctl start taxibot

# Проверьте логи
journalctl -u taxibot -n 50 -f
```

### 5. Тестирование

1. Откройте бота в Telegram
2. Нажмите "⭐ Подписка" → "⬆️ Улучшить тариф"
3. Выберите тариф (например, Pro - 299₽)
4. Нажмите "💳 Оплатить картой"

**Тестовая карта:**
- Номер: `5555 5555 5555 5599`
- Срок: любая будущая дата
- CVV: любые 3 цифры

### 6. Проверка в логах

После тестовой оплаты проверьте логи:

```bash
journalctl -u taxibot -n 100 --no-pager | grep -i robokassa
```

Должно быть:
```
INFO: Received Robokassa Result callback: InvId=...
INFO: Successfully processed Robokassa payment ... for user ...
```

### 7. Проверка в БД

```bash
sudo -u postgres psql taxibot_db -c "
SELECT u.telegram_id, u.username, s.tier, s.started_at, s.expires_at, s.is_active
FROM subscriptions s
JOIN users u ON s.user_id = u.id
ORDER BY s.started_at DESC
LIMIT 5;
"
```

### 8. Переход на боевой режим

После успешного тестирования:

1. Обновите `.env`:
```bash
ROBOKASSA_TEST_MODE=False
```

2. В Robokassa:
   - Выключите "Тестовый режим"
   - Убедитесь что Result URL указан правильно
   - Проверьте что используете боевые пароли #1 и #2

3. Перезапустите бота:
```bash
sudo systemctl restart taxibot
```

## Мониторинг

### Проверка платежей

```bash
# Все платежи за сегодня
journalctl -u taxibot --since today | grep "Successfully processed Robokassa"

# Ошибки платежей
journalctl -u taxibot --since today | grep -i "error.*robokassa"
```

### Статистика в БД

```sql
-- Подписки за последние 7 дней
SELECT 
    DATE(started_at) as date,
    tier,
    COUNT(*) as count
FROM subscriptions
WHERE started_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(started_at), tier
ORDER BY date DESC;
```

## Troubleshooting

### Проблема: Result URL не вызывается

**Проверка:**
```bash
# Проверьте что webhook endpoint доступен
curl https://kefpulse.ru/webhook/robokassa/result

# Проверьте nginx логи
tail -f /var/log/nginx/access.log | grep robokassa
```

**Решение:**
- Убедитесь что nginx проксирует запросы на порт 8080
- Проверьте что бот запущен и слушает порт 8080
- Проверьте firewall правила

### Проблема: Invalid signature

**Решение:**
- Проверьте что пароли #1 и #2 скопированы без пробелов
- Убедитесь что используете правильные пароли (тестовые/боевые)
- Проверьте логи для деталей ошибки

### Проблема: Подписка не активируется

**Проверка:**
```bash
# Проверьте логи обработки платежа
journalctl -u taxibot -n 200 | grep -A 10 "Received Robokassa Result"
```

**Решение:**
- Проверьте что user_id передается корректно
- Проверьте что tier и duration_days валидны
- Проверьте что нет ошибок в upgrade_subscription

## Безопасность

⚠️ **Важные моменты:**

1. **Пароли #1 и #2 должны быть разными**
2. **Никогда не коммитьте пароли в git**
3. **Используйте HTTPS для всех webhook URL**
4. **Проверяйте подпись в каждом callback**
5. **Логируйте все платежи для аудита**

## Документация

- Полная настройка: `ROBOKASSA_SETUP.md`
- Тестирование: `TEST_ROBOKASSA.md`
- Пример конфигурации: `.env.example`

## Поддержка

При возникновении проблем:
1. Проверьте логи бота: `journalctl -u taxibot -n 100`
2. Проверьте логи nginx: `tail -f /var/log/nginx/error.log`
3. Проверьте статус бота: `systemctl status taxibot`
4. Проверьте доступность webhook: `curl https://kefpulse.ru/webhook/robokassa/result`
