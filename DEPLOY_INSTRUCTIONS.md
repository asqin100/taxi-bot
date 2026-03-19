# Инструкция по деплою обновления (Спортивные события)

## Подготовка

1. **Сделайте репозиторий приватным обратно** (если делали публичным)
   - GitHub → Settings → Danger Zone → Change visibility → Make private

2. **Проверьте изменения локально:**
   ```bash
   cd ~/storage/downloads/taxi-bot-main/taxi-bot-main
   git status
   git diff bot/services/event_parser.py
   ```

## Коммит изменений

```bash
cd ~/storage/downloads/taxi-bot-main/taxi-bot-main

# Добавить измененные файлы
git add bot/services/event_parser.py
git add SPORT_EVENTS_UPDATE.md
git add DEPLOY_INSTRUCTIONS.md

# Создать коммит
git commit -m "feat: добавлен парсинг спортивных мероприятий

- Добавлена категория 'sport' в KudaGo API парсер
- Расширен список ключевых слов для спортивных событий
- Обновлена длительность спортивных событий до 2.5 часов
- Добавлены названия команд и турниров для лучшего определения

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# Отправить на GitHub
git push origin main
```

## Деплой на Timeweb

### Вариант 1: Через SSH

```bash
# Подключиться к серверу
ssh user@your-server.timeweb.ru

# Перейти в директорию проекта
cd /path/to/taxi-bot

# Получить изменения
git pull origin main

# Перезапустить бота
sudo systemctl restart taxi-bot

# Проверить статус
sudo systemctl status taxi-bot

# Проверить логи
tail -f bot.log | grep -i "sport\|event"
```

### Вариант 2: Через панель Timeweb

1. Зайти в панель управления Timeweb
2. Найти ваш проект taxi-bot
3. Нажать "Обновить из Git"
4. Перезапустить приложение

## Проверка работы

### 1. Проверить парсинг событий

```bash
# На сервере
tail -f bot.log | grep "KudaGo"
```

Должны появиться строки:
```
Fetching concert events from KudaGo API
Fetched X concert events from KudaGo API
Fetching sport events from KudaGo API
Fetched X sport events from KudaGo API
Parsed X total events from KudaGo (concerts + sports)
```

### 2. Проверить в боте

Отправьте команду `/events` в бот - должны появиться спортивные мероприятия с эмодзи ⚽

### 3. Проверить уведомления

- Зайдите в настройки уведомлений
- Убедитесь, что "⚽ Спорт" доступен для выбора
- Включите уведомления о спортивных событиях

## Откат изменений (если что-то пошло не так)

```bash
# На сервере
cd /path/to/taxi-bot
git log --oneline -5  # Найти предыдущий коммит
git revert HEAD  # Откатить последний коммит
sudo systemctl restart taxi-bot
```

## Мониторинг

После деплоя следите за:
- Логами бота: `tail -f bot.log`
- Количеством спортивных событий в БД
- Отправкой уведомлений пользователям

## Контакты для поддержки

- Telegram: @your_support_bot
- Email: support@example.com

---
Дата: 19.03.2026
