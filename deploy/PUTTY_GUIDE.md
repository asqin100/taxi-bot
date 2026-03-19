# 🔌 Подключение к серверу через PuTTY

## Шаг 1: Запуск PuTTY

1. Откройте **PuTTY** (найдите в меню Пуск)
2. В поле **Host Name (or IP address)** введите: `5.42.110.16`
3. **Port**: `22`
4. **Connection type**: `SSH`
5. Нажмите **Open**

## Шаг 2: Первое подключение

При первом подключении появится предупреждение о ключе сервера:
```
The server's host key is not cached in the registry...
```

Нажмите **Yes** (это нормально для первого подключения)

## Шаг 3: Вход

```
login as: root
password: [введите пароль от timeweb.cloud]
```

**Важно:** При вводе пароля символы не отображаются - это нормально!

---

## 🚀 Команды для развертывания

После успешного входа выполните команды по порядку:

### 1. Обновление системы
```bash
apt update && apt upgrade -y
```

### 2. Установка Git
```bash
apt install -y git
```

### 3. Создание директории и клонирование репозитория
```bash
mkdir -p /opt/taxibot
cd /opt/taxibot
git clone https://github.com/asqin100/taxi-bot.git .
```

### 4. Запуск автоматического развертывания
```bash
cd /opt/taxibot/deploy
chmod +x *.sh
bash quick_deploy.sh
```

Скрипт запросит:
- **BOT_TOKEN** - получите у @BotFather в Telegram
- **ADMIN_ID** - ваш Telegram ID (можно узнать у @userinfobot)
- **YANDEX_API_KEY** - ключ API Яндекс (если есть, иначе оставьте пустым)
- **Пароль PostgreSQL** - придумайте надежный пароль (запомните его!)

### 5. Проверка статуса
```bash
systemctl status taxibot
systemctl status taxibot-web
```

Должно быть: **active (running)** зеленым цветом

### 6. Просмотр логов
```bash
tail -f /var/log/taxibot/bot.log
```

Нажмите `Ctrl+C` чтобы выйти из просмотра логов

---

## 📱 Финальный шаг: Обновить URL в боте

Откройте вашего бота в Telegram и отправьте команду:
```
/setwebapp http://5.42.110.16
```

---

## ✅ Готово!

Бот работает на VPS 24/7 без ngrok предупреждений!

Проверьте:
- Откройте карту: `/map`
- Проверьте админ-панель: `http://5.42.110.16/admin/dashboard`

---

## 🔧 Полезные команды

### Перезапуск бота
```bash
systemctl restart taxibot
```

### Просмотр логов в реальном времени
```bash
journalctl -u taxibot -f
```

### Обновление кода с GitHub
```bash
cd /opt/taxibot
git pull
systemctl restart taxibot taxibot-web
```

### Создание бэкапа БД
```bash
bash /opt/taxibot/deploy/backup.sh
```

### Мониторинг системы
```bash
bash /opt/taxibot/deploy/monitor.sh
```

---

## ❓ Если что-то пошло не так

### Бот не запускается
```bash
journalctl -u taxibot -n 50
```

### Проверить конфигурацию
```bash
cat /opt/taxibot/.env
```

### Проверить БД
```bash
sudo -u postgres psql taxibot_db -c "SELECT COUNT(*) FROM users;"
```

### Перезапустить всё
```bash
systemctl restart taxibot taxibot-web nginx postgresql
```

---

## 📞 Нужна помощь?

Если возникли проблемы:
1. Скопируйте вывод команды с ошибкой
2. Покажите логи: `tail -100 /var/log/taxibot/bot.log`
3. Проверьте статус: `bash /opt/taxibot/deploy/monitor.sh`
