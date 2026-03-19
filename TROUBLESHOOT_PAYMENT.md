# Диагностика проблемы с платежами Robokassa

## Быстрая проверка (выполните на сервере)

```bash
# 1. Проверьте что бот запущен
systemctl status taxibot

# 2. Проверьте логи за последние 10 минут
journalctl -u taxibot --since "10 minutes ago" --no-pager

# 3. Проверьте что endpoint доступен локально
curl http://localhost:8080/webhook/robokassa/result?test=1

# 4. Проверьте настройки Robokassa в .env
cat /opt/taxibot/.env | grep ROBOKASSA

# 5. Проверьте nginx логи
tail -50 /var/log/nginx/access.log | grep robokassa
```

## Чек-лист настройки

### ✓ В Robokassa (https://auth.robokassa.ru/)

- [ ] Тестовый режим ВКЛЮЧЕН
- [ ] Result URL: `https://kefpulse.ru/webhook/robokassa/result`
- [ ] Success URL: `https://kefpulse.ru/webhook/robokassa/success`
- [ ] Fail URL: `https://kefpulse.ru/webhook/robokassa/fail`
- [ ] Метод: GET
- [ ] Настройки СОХРАНЕНЫ (кнопка "Сохранить")

### ✓ На сервере

- [ ] Бот запущен: `systemctl status taxibot`
- [ ] Порт 8080 слушается: `netstat -tlnp | grep 8080`
- [ ] .env содержит настройки Robokassa
- [ ] PAYMENT_PROVIDER=robokassa
- [ ] Nginx проксирует на порт 8080

### ✓ Тест доступности

```bash
# На сервере
curl http://localhost:8080/webhook/robokassa/result?test=1

# На вашем компьютере
curl https://kefpulse.ru/webhook/robokassa/result?test=1
```

Оба должны вернуть ответ (не Connection refused, не 404)

## Частые проблемы

### Проблема: "Connection refused" при curl localhost:8080

**Причина:** Бот не запущен или упал

**Решение:**
```bash
systemctl restart taxibot
journalctl -u taxibot -n 50 -f
```

### Проблема: curl localhost работает, но curl https://kefpulse.ru не работает

**Причина:** Nginx не настроен или не проксирует

**Решение:**
```bash
# Проверьте nginx конфиг
cat /etc/nginx/sites-enabled/default

# Должно быть:
# location / {
#     proxy_pass http://localhost:8080;
# }

# Перезапустите nginx
systemctl restart nginx
```

### Проблема: Webhook приходит, но "Invalid signature"

**Причина:** Неправильные пароли или порядок параметров

**Решение:**
1. Убедитесь что пароли в .env совпадают с Robokassa
2. Для тестового режима используйте тестовые пароли
3. Проверьте логи: `journalctl -u taxibot -n 100 | grep signature`

### Проблема: Robokassa вообще не вызывает Result URL

**Причина:** URL не сохранен в настройках

**Решение:**
1. Зайдите в Robokassa → Технические настройки
2. Проверьте что Result URL указан правильно
3. **ОБЯЗАТЕЛЬНО нажмите "Сохранить"**
4. Попробуйте новый платеж

## Ручной тест webhook

Выполните на сервере (замените YOUR_TELEGRAM_ID на ваш ID):

```bash
curl "http://localhost:8080/webhook/robokassa/result?OutSum=299.00&InvId=99999&Shp_user_id=YOUR_TELEGRAM_ID&Shp_tier=pro&Shp_duration=30&SignatureValue=test123"
```

Проверьте логи:
```bash
journalctl -u taxibot -n 20
```

Должно быть:
- `INFO: Received Robokassa Result callback: InvId=99999`
- `ERROR: Invalid signature` (это нормально для теста)

Если этого нет - бот не получает запросы.

## Проверка подписи

Если webhook приходит, но подпись неверная, проверьте:

```bash
# На сервере выполните Python скрипт
python3 << 'PYEOF'
import hashlib

# Ваши данные
merchant_login = "kefpulse"
password2 = "mrjNy9n8xNuX1BAEq4Q8"
out_sum = "299.00"
inv_id = "12345"
user_id = "123456"
tier = "pro"
duration = "30"

# Формируем строку для подписи (Result URL)
sig_string = f"{out_sum}:{inv_id}:{password2}:Shp_duration={duration}:Shp_tier={tier}:Shp_user_id={user_id}"
signature = hashlib.md5(sig_string.encode()).hexdigest().upper()

print(f"Signature string: {sig_string}")
print(f"Signature: {signature}")
PYEOF
```

## Следующие шаги

1. **Выполните быструю проверку** (команды в начале документа)
2. **Пришлите вывод команд** для диагностики
3. **Проверьте чек-лист** - все ли пункты выполнены
4. **Попробуйте ручной тест** webhook

## Если ничего не помогает

Временное решение - оплата балансом:
1. Начислите себе баланс через админ панель
2. Оплатите подписку балансом
3. Продолжите отладку Robokassa параллельно
