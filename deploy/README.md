# 📁 Deploy Scripts

Набор скриптов для развертывания Taxi Bot на VPS.

## 📋 Список файлов

### Основные скрипты

| Файл | Описание | Использование |
|------|----------|---------------|
| `deploy.sh` | Базовая установка системы | `sudo bash deploy.sh` |
| `setup_bot.sh` | Настройка приложения | `bash setup_bot.sh` |
| `quick_deploy.sh` | Полное развертывание (все в одном) | `sudo bash quick_deploy.sh` |

### Управление

| Файл | Описание | Использование |
|------|----------|---------------|
| `update.sh` | Обновление бота | `bash update.sh` |
| `monitor.sh` | Мониторинг состояния | `bash monitor.sh` |
| `backup.sh` | Создание бэкапа БД | `bash backup.sh` |
| `restore.sh` | Восстановление из бэкапа | `bash restore.sh file.sql.gz` |
| `setup_ssl.sh` | Настройка SSL для домена | `bash setup_ssl.sh domain.com` |

### Конфигурационные файлы

| Файл | Описание | Путь установки |
|------|----------|----------------|
| `taxibot.service` | Systemd сервис бота | `/etc/systemd/system/` |
| `taxibot-web.service` | Systemd сервис веб-сервера | `/etc/systemd/system/` |
| `nginx-taxibot.conf` | Конфигурация Nginx | `/etc/nginx/sites-available/` |

### Утилиты

| Файл | Описание |
|------|----------|
| `migrate_to_postgres.py` | Миграция SQLite → PostgreSQL |
| `VPS_DEPLOYMENT.md` | Полная инструкция по развертыванию |

---

## 🚀 Быстрый старт

### Вариант 1: Полное автоматическое развертывание

```bash
# 1. Подключиться к серверу
ssh root@5.42.110.16

# 2. Загрузить код бота
cd /opt/taxibot
# (загрузить файлы через git/scp/ftp)

# 3. Запустить автоматическое развертывание
cd /opt/taxibot/deploy
chmod +x *.sh
sudo bash quick_deploy.sh
```

Скрипт запросит:
- BOT_TOKEN
- ADMIN_ID
- YANDEX_API_KEY
- Пароль для PostgreSQL

### Вариант 2: Пошаговое развертывание

```bash
# Шаг 1: Базовая установка
sudo bash deploy.sh

# Шаг 2: Загрузка кода
cd /opt/taxibot
# (загрузить файлы)

# Шаг 3: Настройка приложения
sudo su - taxibot
cd /opt/taxibot
bash deploy/setup_bot.sh

# Шаг 4: Редактирование .env
nano .env

# Шаг 5: Настройка Nginx
exit  # выйти из taxibot
sudo cp /opt/taxibot/deploy/nginx-taxibot.conf /etc/nginx/sites-available/taxibot
sudo ln -s /etc/nginx/sites-available/taxibot /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Шаг 6: Запуск
sudo systemctl start taxibot taxibot-web
sudo systemctl enable taxibot taxibot-web
```

---

## 🔧 Управление после установки

### Проверка состояния
```bash
bash deploy/monitor.sh
```

### Просмотр логов
```bash
# Логи бота
tail -f /var/log/taxibot/bot.log

# Логи через journalctl
journalctl -u taxibot -f
```

### Перезапуск сервисов
```bash
sudo systemctl restart taxibot
sudo systemctl restart taxibot-web
```

### Обновление кода
```bash
cd /opt/taxibot/deploy
bash update.sh
```

### Создание бэкапа
```bash
cd /opt/taxibot/deploy
bash backup.sh
```

### Восстановление из бэкапа
```bash
cd /opt/taxibot/deploy
bash restore.sh /opt/taxibot/backups/taxibot_backup_20260304_120000.sql.gz
```

---

## 🌐 Настройка домена и SSL

### 1. Настроить DNS
В панели регистратора домена добавить A-запись:
```
your-domain.com  →  5.42.110.16
```

### 2. Подождать распространения DNS (5-30 минут)
```bash
dig +short your-domain.com
```

### 3. Установить SSL
```bash
cd /opt/taxibot/deploy
bash setup_ssl.sh your-domain.com
```

### 4. Обновить WebApp URL в боте
```
/setwebapp https://your-domain.com
```

---

## 📊 Автоматизация

### Автоматический бэкап (каждый день в 3:00)
```bash
sudo crontab -e
```

Добавить строку:
```
0 3 * * * /opt/taxibot/deploy/backup.sh >> /var/log/taxibot/backup.log 2>&1
```

### Мониторинг (каждый час)
```bash
sudo crontab -e
```

Добавить строку:
```
0 * * * * /opt/taxibot/deploy/monitor.sh >> /var/log/taxibot/monitor.log 2>&1
```

---

## 🔒 Безопасность

### Отключить root SSH
```bash
# Создать нового пользователя
adduser admin
usermod -aG sudo admin

# Отключить root login
sudo nano /etc/ssh/sshd_config
# Изменить: PermitRootLogin no
sudo systemctl restart sshd
```

### Настроить fail2ban
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
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
sudo -u postgres psql taxibot_db -c "SELECT COUNT(*) FROM users;"
```

### Веб-сервер не отвечает
```bash
# Проверить порт
netstat -tuln | grep 8080

# Проверить Nginx
sudo nginx -t
sudo systemctl status nginx
```

### База данных не подключается
```bash
# Проверить PostgreSQL
sudo systemctl status postgresql

# Проверить подключение
sudo -u postgres psql -c "\l" | grep taxibot
```

---

## 📞 Поддержка

Документация:
- `VPS_DEPLOYMENT.md` - Полная инструкция
- `../QUICKSTART.md` - Быстрый старт проекта
- `../TUNNEL_SETUP.md` - Настройка туннелей

Логи:
- `/var/log/taxibot/bot.log` - Логи бота
- `/var/log/taxibot/web.log` - Логи веб-сервера
- `/var/log/nginx/taxibot-access.log` - Nginx access
- `/var/log/nginx/taxibot-error.log` - Nginx errors
