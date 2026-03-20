# 🚀 ДЕПЛОЙ ОБНОВЛЕНИЯ: События и Ночные Клубы

## Дата: 20 марта 2026
## Коммит: 1ca3666

---

## ✅ ЧТО ДОБАВЛЕНО

1. **Расширен парсинг событий** - теперь загружаются концерты, спорт, театр, выставки, фестивали
2. **Алерты по ночным клубам** - уведомления в 05:00 по пятницам/субботам
3. **12 топовых ночных клубов Москвы** - с координатами и кнопкой "Поехать"
4. **Документация** - идеи дополнительных мероприятий

---

## 📋 КОМАНДЫ ДЛЯ ОБНОВЛЕНИЯ НА СЕРВЕРЕ

### Вариант 1: Быстрое обновление (рекомендуется)

```bash
# Подключись к серверу по SSH
ssh root@your-server-ip

# Перейди в директорию бота
cd /opt/taxibot

# Сохрани изменения (если есть)
git stash

# Получи последние изменения
git pull origin main

# Перезапусти бота
systemctl restart taxibot

# Проверь статус
systemctl status taxibot

# Проверь логи
tail -f bot.log
```

### Вариант 2: С проверкой изменений

```bash
# Подключись к серверу
ssh root@your-server-ip

# Перейди в директорию
cd /opt/taxibot

# Посмотри текущую версию
git log --oneline -1

# Получи изменения
git fetch origin main

# Посмотри что изменилось
git log HEAD..origin/main --oneline

# Примени изменения
git pull origin main

# Проверь новые файлы
ls -la bot/services/nightclub_alerts.py
ls -la data/nightclubs.json

# Перезапусти бота
systemctl restart taxibot

# Проверь что бот запустился
systemctl status taxibot

# Смотри логи в реальном времени
tail -f bot.log
```

### Вариант 3: Полная перезагрузка (если что-то пошло не так)

```bash
cd /opt/taxibot

# Останови бота
systemctl stop taxibot

# Сохрани базу данных
cp data/bot.db data/bot.db.backup_$(date +%Y%m%d_%H%M%S)

# Получи изменения
git pull origin main

# Проверь виртуальное окружение (если нужно)
source venv/bin/activate
pip install -r requirements.txt

# Запусти бота
systemctl start taxibot

# Проверь статус
systemctl status taxibot

# Проверь логи
tail -f bot.log
```

---

## 🔍 ПРОВЕРКА РАБОТЫ

### 1. Проверь что бот запущен

```bash
systemctl status taxibot
```

Должно быть: `Active: active (running)`

### 2. Проверь логи на ошибки

```bash
tail -100 bot.log | grep -i error
```

Не должно быть критических ошибок.

### 3. Проверь что новые файлы на месте

```bash
ls -la bot/services/nightclub_alerts.py
ls -la data/nightclubs.json
```

### 4. Проверь парсинг событий в логах

```bash
grep "Fetching.*events from KudaGo" bot.log | tail -5
```

Должны быть записи о загрузке событий разных категорий.

### 5. Проверь scheduler ночных клубов

```bash
grep "nightclub" bot.log | tail -10
```

Должны быть записи: "Checking for nightclub alerts..."

---

## 📊 НОВЫЕ ФАЙЛЫ В ПРОЕКТЕ

```
bot/services/nightclub_alerts.py    - Сервис алертов по клубам
data/nightclubs.json                - База данных клубов
ADDITIONAL_EVENTS_IDEAS.md          - Идеи дополнительных мероприятий
TASKS_777_COMPLETED.md              - Отчет о выполненных задачах
```

---

## ⚙️ ИЗМЕНЁННЫЕ ФАЙЛЫ

```
bot/services/event_parser.py        - Расширен парсинг (5 категорий)
bot/main.py                         - Добавлен scheduler для клубов
```

---

## 🕐 КОГДА СРАБОТАЮТ НОВЫЕ ФУНКЦИИ

### Парсинг событий
- **Частота:** Каждые 6 часов
- **Категории:** concert, theater, exhibition, festival, recreation
- **Проверка:** Смотри логи "Fetching events from KudaGo API"

### Алерты по ночным клубам
- **Когда:** Пятница и суббота в 05:00 утра (04:50-05:10)
- **Частота проверки:** Каждые 10 минут
- **Кому:** Всем пользователям с включенными уведомлениями
- **Проверка:** Смотри логи "Checking for nightclub alerts"

---

## ❗ ВОЗМОЖНЫЕ ПРОБЛЕМЫ

### Проблема 1: Бот не запускается после git pull

**Решение:**
```bash
cd /opt/taxibot
git status
# Если есть конфликты:
git stash
git pull origin main
systemctl restart taxibot
```

### Проблема 2: Ошибка импорта nightclub_alerts

**Решение:**
```bash
# Проверь что файл существует
ls -la bot/services/nightclub_alerts.py

# Проверь права доступа
chmod 644 bot/services/nightclub_alerts.py

# Перезапусти
systemctl restart taxibot
```

### Проблема 3: Файл nightclubs.json не найден

**Решение:**
```bash
# Проверь что файл существует
ls -la data/nightclubs.json

# Проверь права доступа
chmod 644 data/nightclubs.json

# Перезапусти
systemctl restart taxibot
```

### Проблема 4: События не парсятся

**Решение:**
```bash
# Проверь логи
grep "KudaGo" bot.log | tail -20

# Проверь интернет соединение
curl -I https://kudago.com/public-api/v1.4/events/

# Если API недоступен - подожди и попробуй позже
```

---

## 📝 ПОСЛЕ ДЕПЛОЯ

### Тестирование в боте:

1. **Проверь события:**
   - Отправь боту команду (если есть команда для просмотра событий)
   - Или дождись следующего парсинга (каждые 6 часов)

2. **Проверь алерты по клубам:**
   - Дождись пятницы/субботы 05:00
   - Или проверь логи: `grep "nightclub" bot.log`

3. **Проверь кнопку "Поехать" в алертах:**
   - Дождись алерта о мероприятии
   - Нажми кнопку "🚕 Поехать"
   - Должен открыться выбор: Навигатор или Карты

---

## 🎯 ИТОГО

- **Новых зависимостей:** НЕТ (все библиотеки уже установлены)
- **Миграций базы данных:** НЕТ (структура не изменилась)
- **Время деплоя:** ~2 минуты
- **Downtime:** ~10 секунд (перезапуск бота)

---

## 🚀 БЫСТРАЯ КОМАНДА (КОПИРУЙ И ВСТАВЛЯЙ)

```bash
cd /opt/taxibot && git stash && git pull origin main && systemctl restart taxibot && systemctl status taxibot && tail -50 bot.log
```

Эта команда:
1. Переходит в директорию бота
2. Сохраняет локальные изменения
3. Получает обновления с GitHub
4. Перезапускает бота
5. Показывает статус
6. Показывает последние 50 строк логов

---

✅ **ГОТОВО К ДЕПЛОЮ!**
