# 🚀 Развертывание Taxi Bot на VPS

## Информация о сервере
- **IP:** 5.42.110.16
- **Провайдер:** Timeweb
- **ОС:** Ubuntu 22.04 LTS
- **Домен:** Будет добавлен позже

---

## 📋 Пошаговая инструкция

### Шаг 1: Подключение к серверу

```bash
ssh root@5.42.110.16
```

При первом подключении подтвердите fingerprint (yes).

---

### Шаг 2: Базовая установка

```bash
# Скачать deploy.sh на сервер
wget https://raw.githubusercontent.com/asqin100/taxi-bot/main/deploy/deploy.sh
# ИЛИ скопировать файл вручную

# Сделать исполняемым
chmod +x deploy.sh

# Запустить установку
sudo bash deploy.sh
```

**Что установится:**
- ✅ Python 3.11
- ✅ PostgreSQL
- ✅ Nginx
- ✅ Redis
- ✅ Пользователь taxibot
- ✅ Firewall (порты 22, 80, 443)

---

### Шаг 3: Загрузка кода бота

**Вариант A: Через Git (рекомендуется)**
```bash
cd /opt/taxibot
sudo -u taxibot git clone https://github.com/asqin100/taxi-bot.git .
```

**Вариант B: Через SCP с локального компьютера**
```bash
# На вашем Windows компьютере:
cd C:\taxi-bot
scp -r bot webapp *.py requirements.txt root@5.42.110.16:/opt/taxibot/
```

**Вариант C: Через FileZilla/WinSCP**
- Подключиться к 5.42.110.16
- Загрузить папки: bot, webapp, deploy
- Загрузить файлы: *.py, requirements.txt

---

### Шаг 4: Настройка приложения

```bash
# Переключиться на пользователя taxibot
sudo su - taxibot
cd /opt/taxibot

# Запустить настройку
bash deploy/setup_bot.sh
```

---

### Шаг 5: Редактирование .env

```bash
nano /opt/taxibot/.env
```

**Обязательно изменить:**
```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_telegram_id
YANDEX_API_KEY=ваш_ключ_яндекс_апи

# Изменить пароль БД
DATABASE_URL=postgresql+asyncpg://taxibot:НОВЫЙ_ПАРОЛЬ@localhost/taxibot_db
```

**Сохранить:** Ctrl+O, Enter, Ctrl+X

**Изменить пароль в PostgreSQL:**
```bash
sudo -u postgres psql
ALTER USER taxibot WITH PASSWORD 'НОВЫЙ_ПАРОЛЬ';
\q
```

---

### Шаг 6: Настройка Nginx

```bash
# Скопировать конфиг
sudo cp /opt/taxibot/deploy/nginx-taxibot.conf /etc/nginx/sites-available/taxibot

# Создать симлинк
sudo ln -s /etc/nginx/sites-available/taxibot /etc/nginx/sites-enabled/

# Удалить дефолтный конфиг
sudo rm /etc/nginx/sites-enabled/default

# Проверить конфигурацию
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx
```

---

### Шаг 7: Запуск бота

```bash
# Запустить сервисы
sudo systemctl start taxibot
sudo systemctl start taxibot-web

# Включить автозапуск
sudo systemctl enable taxibot
sudo systemctl enable taxibot-web

# Проверить статус
sudo systemctl status taxibot
sudo systemctl status taxibot-web
```

---

### Шаг 8: Проверка работы

**Проверить веб-сервер:**
```bash
curl http://localhost:8080
```

**Проверить через браузер:**
```
http://5.42.110.16
```

**Проверить логи:**
```bash
# Логи бота
tail -f /var/log/taxibot/bot.log

# Логи веб-сервера
tail -f /var/log/taxibot/web.log

# Логи Nginx
tail -f /var/log/nginx/taxibot-access.log
```

---

### Шаг 9: Обновление WebApp URL в боте

В Telegram отправьте боту:
```
/setwebapp http://5.42.110.16
```

**Готово!** Бот работает на VPS без ngrok предупреждений! ✅

---

## 🔧 Полезные команды

### Управление сервисами
```bash
# Перезапуск
sudo systemctl restart taxibot
sudo systemctl restart taxibot-web

# Остановка
sudo systemctl stop taxibot
sudo systemctl stop taxibot-web

# Просмотр логов
sudo journalctl -u taxibot -f
sudo journalctl -u taxibot-web -f
```

### Обновление кода
```bash
cd /opt/taxibot
sudo -u taxibot git pull
sudo systemctl restart taxibot
sudo systemctl restart taxibot-web
```

### Бэкап базы данных
```bash
sudo -u postgres pg_dump taxibot_db > backup_$(date +%Y%m%d).sql
```

### Восстановление из бэкапа
```bash
sudo -u postgres psql taxibot_db < backup_20260304.sql
```

---

## 🌐 Настройка домена (когда купите)

### 1. Настроить DNS
В панели регистратора домена добавить A-запись:
```
@ (или your-domain.com)  →  5.42.110.16
```

### 2. Обновить Nginx конфиг
```bash
sudo nano /etc/nginx/sites-available/taxibot
```
Заменить `5.42.110.16` на `your-domain.com`

### 3. Установить SSL сертификат
```bash
sudo certbot --nginx -d your-domain.com
```

### 4. Обновить WebApp URL
```
/setwebapp https://your-domain.com
```

---

## 🔒 Безопасность

### Отключить root SSH (после настройки)
```bash
# Создать нового пользователя с sudo
adduser admin
usermod -aG sudo admin

# Отключить root login
sudo nano /etc/ssh/sshd_config
# Изменить: PermitRootLogin no
sudo systemctl restart sshd
```

### Настроить автообновления
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 📊 Мониторинг

### Проверка ресурсов
```bash
# CPU и память
htop

# Диск
df -h

# Сетевые соединения
netstat -tulpn
```

### Проверка работы PostgreSQL
```bash
sudo -u postgres psql taxibot_db
SELECT COUNT(*) FROM users;
\q
```

---

## ❓ Решение проблем

### Бот не запускается
```bash
# Проверить логи
sudo journalctl -u taxibot -n 50

# Проверить .env
cat /opt/taxibot/.env

# Проверить БД
sudo -u postgres psql -c "\l" | grep taxibot
```

### Веб-сервер не отвечает
```bash
# Проверить порт
netstat -tulpn | grep 8080

# Проверить Nginx
sudo nginx -t
sudo systemctl status nginx
```

### База данных не подключается
```bash
# Проверить PostgreSQL
sudo systemctl status postgresql

# Проверить пароль
sudo -u postgres psql
\du taxibot
```

---

## 📞 Контакты

При возникновении проблем:
1. Проверить логи: `/var/log/taxibot/`
2. Проверить статус сервисов: `systemctl status`
3. Проверить firewall: `sudo ufw status`

**Готово к продакшену! 🚀**
