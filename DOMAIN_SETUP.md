# Настройка домена kefpulse.ru для бота

## Проблема

Ngrok туннель истекает и показывает ошибку `ERR_NGROK_3200`. Нужно использовать постоянный домен.

## Решение

Использовать домен **kefpulse.ru** вместо ngrok.

---

## Быстрое исправление (только обновить URL)

Если домен уже настроен и работает, просто обнови WEBAPP_URL:

```bash
cd /opt/taxibot && sed -i '/^WEBAPP_URL=/d' .env && echo "WEBAPP_URL=https://kefpulse.ru" >> .env && systemctl restart taxibot
```

---

## Полная настройка с нуля

### Шаг 1: Проверь DNS

Убедись что A запись домена указывает на IP сервера:

```bash
dig kefpulse.ru +short
```

Должен показать IP твоего сервера.

### Шаг 2: Установи nginx

```bash
apt update
apt install -y nginx
```

### Шаг 3: Создай конфигурацию nginx

```bash
cat > /etc/nginx/sites-available/kefpulse.ru << 'NGINX'
server {
    listen 80;
    server_name kefpulse.ru www.kefpulse.ru;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/kefpulse.ru /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Шаг 4: Установи SSL сертификат

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d kefpulse.ru -d www.kefpulse.ru
```

Certbot автоматически:
- Получит SSL сертификат от Let's Encrypt
- Обновит конфигурацию nginx для HTTPS
- Настроит автоматическое продление сертификата

### Шаг 5: Обнови WEBAPP_URL в .env

```bash
cd /opt/taxibot
sed -i '/^WEBAPP_URL=/d' .env
echo "WEBAPP_URL=https://kefpulse.ru" >> .env
systemctl restart taxibot
```

---

## Проверка

После настройки:

1. Открой в браузере: https://kefpulse.ru
2. Должна открыться карта бота
3. В боте нажми "🗺 Открыть карту" - должно работать

---

## Автоматический скрипт

Создан скрипт `/tmp/setup_domain.sh` который делает всё автоматически (кроме SSL).

Запусти:
```bash
bash /tmp/setup_domain.sh
```

Затем установи SSL:
```bash
certbot --nginx -d kefpulse.ru -d www.kefpulse.ru
```

---

## Troubleshooting

### Ошибка "Connection refused"

Проверь что бот запущен и слушает порт 8080:
```bash
systemctl status taxibot
netstat -tlnp | grep 8080
```

### Ошибка "502 Bad Gateway"

Проверь логи nginx:
```bash
tail -f /var/log/nginx/error.log
```

### SSL не работает

Проверь статус certbot:
```bash
certbot certificates
```

Обнови сертификат вручную:
```bash
certbot renew
```
