# Настройка Robokassa

## 1. Тестовый режим

### Конфигурация в .env

```bash
# Robokassa настройки
ROBOKASSA_MERCHANT_LOGIN=your_test_login
ROBOKASSA_PASSWORD1=your_password1
ROBOKASSA_PASSWORD2=your_password2
ROBOKASSA_TEST_MODE=True
PAYMENT_PROVIDER=robokassa
```

### Получение тестовых данных

1. Зарегистрируйтесь на https://auth.robokassa.ru/
2. Перейдите в "Технические настройки"
3. Включите "Тестовый режим"
4. Скопируйте:
   - Идентификатор магазина (Merchant Login)
   - Пароль #1 (для формирования ссылки)
   - Пароль #2 (для проверки результата)

### Настройка URL в личном кабинете Robokassa

В разделе "Технические настройки" укажите:

**Result URL (обязательно):**
```
https://your-domain.com/webhook/robokassa/result
```

**Success URL (опционально):**
```
https://your-domain.com/webhook/robokassa/success
```

**Fail URL (опционально):**
```
https://your-domain.com/webhook/robokassa/fail
```

**Метод отправки данных:** GET

### Тестовые карты

В тестовом режиме используйте:
- Карта: `5555 5555 5555 5599`
- Срок: любая будущая дата
- CVV: любые 3 цифры
- Имя: любое

## 2. Боевой режим

### Переключение на production

В .env измените:
```bash
ROBOKASSA_TEST_MODE=False
```

### Проверка перед запуском

✅ Result URL настроен и доступен
✅ Пароли #1 и #2 скопированы правильно
✅ Тестовые платежи проходят успешно
✅ Webhook обрабатывается корректно

## 3. Проверка интеграции

### Локальное тестирование

1. Запустите бота локально
2. Используйте ngrok для публичного URL:
   ```bash
   ngrok http 8080
   ```
3. Укажите ngrok URL в Robokassa Result URL
4. Попробуйте тестовый платеж

### Проверка webhook

Логи должны показать:
```
INFO: Received Robokassa Result callback: InvId=123456
INFO: Successfully processed Robokassa payment 123456 for user 12345
```

## 4. Структура платежа

### Параметры платежной ссылки

```
https://auth.robokassa.ru/Merchant/Index.aspx?
  MerchantLogin=your_login
  &OutSum=299.00
  &InvId=1234567890
  &Description=Подписка PRO на 30 дней
  &SignatureValue=abc123...
  &IsTest=1
  &Shp_user_id=12345
  &Shp_tier=pro
  &Shp_duration=30
```

### Callback от Robokassa (Result URL)

```
GET /webhook/robokassa/result?
  OutSum=299.00
  &InvId=1234567890
  &SignatureValue=xyz789...
  &Shp_user_id=12345
  &Shp_tier=pro
  &Shp_duration=30
```

## 5. Безопасность

⚠️ **Важно:**
- Пароли #1 и #2 должны быть разными
- Никогда не коммитьте пароли в git
- Используйте HTTPS для Result URL
- Проверяйте подпись в каждом callback

## 6. Отладка

### Проверка подписи вручную

```python
import hashlib

# Для платежной ссылки (Password #1)
sig_string = f"{login}:{amount}:{inv_id}:{password1}:Shp_user_id={user_id}:Shp_tier={tier}"
signature = hashlib.md5(sig_string.encode()).hexdigest()

# Для Result URL (Password #2)
sig_string = f"{amount}:{inv_id}:{password2}:Shp_user_id={user_id}:Shp_tier={tier}"
signature = hashlib.md5(sig_string.encode()).hexdigest()
```

### Логи для отладки

```bash
# Проверить логи webhook
journalctl -u taxibot -n 100 --no-pager | grep -i robokassa

# Проверить логи бота
tail -f /var/log/taxibot/bot.log | grep -i payment
```

## 7. Частые ошибки

❌ **Invalid signature** - проверьте пароли и порядок параметров
❌ **Amount mismatch** - проверьте формат суммы (299.00)
❌ **Result URL not called** - проверьте доступность URL
❌ **Test mode not working** - убедитесь что IsTest=1

## 8. Документация Robokassa

- Тестовый режим: https://docs.robokassa.ru/testing-mode/
- Параметры скриптов: https://docs.robokassa.ru/script-parameters/
- Скрипт оплаты: https://docs.robokassa.ru/script-pay/
