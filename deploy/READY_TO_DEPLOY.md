# 🎯 Готово к развертыванию на VPS

## ✅ Что подготовлено

### 📦 Скрипты развертывания (9 файлов)
- ✅ `deploy.sh` - Базовая установка системы
- ✅ `setup_bot.sh` - Настройка приложения
- ✅ `quick_deploy.sh` - Полное автоматическое развертывание
- ✅ `update.sh` - Обновление бота
- ✅ `monitor.sh` - Мониторинг состояния
- ✅ `backup.sh` - Автоматический бэкап
- ✅ `restore.sh` - Восстановление из бэкапа
- ✅ `setup_ssl.sh` - Настройка SSL для домена
- ✅ `migrate_to_postgres.py` - Миграция SQLite → PostgreSQL

### ⚙️ Конфигурационные файлы (3 файла)
- ✅ `taxibot.service` - Systemd сервис бота
- ✅ `taxibot-web.service` - Systemd сервис веб-сервера
- ✅ `nginx-taxibot.conf` - Конфигурация Nginx

### 📚 Документация (3 файла)
- ✅ `VPS_DEPLOYMENT.md` - Полная инструкция по развертыванию
- ✅ `README.md` - Описание скриптов
- ✅ `requirements.txt` - Обновлен с поддержкой PostgreSQL

---

## 🚀 Следующие шаги

### 1. Загрузить код на сервер

**Вариант A: Через Git (рекомендуется)**
```bash
# На сервере
ssh root@5.42.110.16
cd /opt/taxibot
git clone https://github.com/your-repo/taxi-bot.git .
```

**Вариант B: Через WinSCP/FileZilla**
1. Подключиться к `5.42.110.16`
2. Загрузить все файлы в `/opt/taxibot/`

**Вариант C: Через SCP**
```bash
# На вашем компьютере (PowerShell)
cd C:\taxi-bot
scp -r * root@5.42.110.16:/opt/taxibot/
```

### 2. Запустить автоматическое развертывание

```bash
# На сервере
ssh root@5.42.110.16
cd /opt/taxibot/deploy
chmod +x *.sh
sudo bash quick_deploy.sh
```

Скрипт запросит:
- **BOT_TOKEN** - получить у @BotFather
- **ADMIN_ID** - ваш Telegram ID
- **YANDEX_API_KEY** - ключ API Яндекс
- **Пароль PostgreSQL** - придумать надежный пароль

### 3. Проверить работу

```bash
# Статус сервисов
sudo systemctl status taxibot
sudo systemctl status taxibot-web

# Логи
tail -f /var/log/taxibot/bot.log

# Мониторинг
bash /opt/taxibot/deploy/monitor.sh
```

### 4. Обновить WebApp URL в боте

Открыть бота в Telegram и отправить:
```
/setwebapp http://5.42.110.16
```

### 5. Протестировать

1. Открыть карту: `/map`
2. Проверить админ-панель: `http://5.42.110.16/admin/dashboard`
3. Проверить промокоды
4. Проверить подписки

---

## 🌐 Когда купите домен

```bash
# 1. Настроить DNS (A-запись)
your-domain.com → 5.42.110.16

# 2. Установить SSL
ssh root@5.42.110.16
cd /opt/taxibot/deploy
bash setup_ssl.sh your-domain.com

# 3. Обновить URL в боте
/setwebapp https://your-domain.com
```

---

## 📊 Преимущества VPS

✅ **Без предупреждений ngrok** - пользователи сразу видят карту
✅ **Стабильность** - работает 24/7 без перезапусков
✅ **Масштабируемость** - поддержка 500+ пользователей
✅ **PostgreSQL** - надежная БД вместо SQLite
✅ **Профессионализм** - свой домен и SSL
✅ **Автоматизация** - бэкапы, мониторинг, обновления

---

## 🔧 Управление после установки

### Обновление кода
```bash
ssh root@5.42.110.16
cd /opt/taxibot/deploy
bash update.sh
```

### Создание бэкапа
```bash
bash /opt/taxibot/deploy/backup.sh
```

### Мониторинг
```bash
bash /opt/taxibot/deploy/monitor.sh
```

### Просмотр логов
```bash
tail -f /var/log/taxibot/bot.log
journalctl -u taxibot -f
```

---

## 📞 Если что-то пошло не так

1. **Проверить логи:**
   ```bash
   tail -100 /var/log/taxibot/bot.log
   sudo journalctl -u taxibot -n 50
   ```

2. **Проверить статус:**
   ```bash
   bash /opt/taxibot/deploy/monitor.sh
   ```

3. **Перезапустить сервисы:**
   ```bash
   sudo systemctl restart taxibot taxibot-web nginx
   ```

4. **Проверить БД:**
   ```bash
   sudo -u postgres psql taxibot_db -c "SELECT COUNT(*) FROM users;"
   ```

---

## 🎉 Готово!

Все файлы подготовлены и готовы к развертыванию на VPS.

**IP сервера:** 5.42.110.16
**Провайдер:** Timeweb
**ОС:** Ubuntu 22.04 LTS

Следуйте инструкциям выше для развертывания.
