# 🌐 Настройка домена kefpulse.ru

## Шаг 1: Настройка DNS (в панели регистратора)

Зайдите в панель управления доменом и добавьте A-запись:

```
Тип: A
Имя: @ (или kefpulse.ru)
Значение: 5.42.110.16
TTL: 3600 (или Auto)
```

**Важно:** DNS обновляется 5-30 минут. Подождите перед следующим шагом.

## Шаг 2: Проверка DNS

Выполните на сервере:

```bash
# Проверить что домен указывает на правильный IP
dig +short kefpulse.ru

# Должно вывести: 5.42.110.16
```

Если выводит другой IP или пусто - подождите еще.

## Шаг 3: Автоматическая настройка

```bash
cd /opt/taxibot
sudo -u taxibot git pull
cd deploy
bash setup_domain.sh kefpulse.ru
```

Скрипт автоматически:
- Обновит WEBAPP_URL в .env
- Обновит server_name в Nginx
- Перезапустит сервисы

## Шаг 4: Установка SSL сертификата

```bash
bash setup_ssl.sh kefpulse.ru
```

Скрипт автоматически:
- Проверит DNS
- Получит бесплатный SSL от Let's Encrypt
- Настроит HTTPS
- Настроит автообновление сертификата

## Шаг 5: Обновить URL в боте

Откройте бота в Telegram и отправьте:

```
/setwebapp https://kefpulse.ru
```

## ✅ Готово!

Теперь бот доступен по адресу:
- **Карта**: https://kefpulse.ru
- **Админ-панель**: https://kefpulse.ru/admin/login

## 🔧 Проверка

```bash
# Проверить что сайт работает
curl https://kefpulse.ru

# Проверить SSL
curl -I https://kefpulse.ru

# Проверить статус бота
systemctl status taxibot
```

## ❓ Решение проблем

### DNS не обновился
```bash
# Проверить текущий IP домена
dig +short kefpulse.ru

# Если не 5.42.110.16 - подождите еще 10-15 минут
```

### SSL не устанавливается
```bash
# Убедитесь что DNS настроен правильно
dig +short kefpulse.ru

# Проверьте что порт 80 открыт
curl http://kefpulse.ru

# Попробуйте еще раз
bash /opt/taxibot/deploy/setup_ssl.sh kefpulse.ru
```

### Бот не видит новый URL
```bash
# Проверьте .env
cat /opt/taxibot/.env | grep WEBAPP_URL

# Должно быть: WEBAPP_URL=https://kefpulse.ru

# Перезапустите бота
systemctl restart taxibot
```
