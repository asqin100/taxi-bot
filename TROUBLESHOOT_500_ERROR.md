# 🔍 ДИАГНОСТИКА ОШИБКИ HTTP 500 В МЕРОПРИЯТИЯХ

## Проблема
После деплоя в разделе "Мероприятия" админ панели появляется ошибка: **HTTP 500**

## ✅ ШАГ 1: Запусти диагностический скрипт

На сервере выполни:

```bash
cd /opt/taxibot
source venv/bin/activate
python test_bot.py
```

Этот скрипт проверит:
- ✅ Импорты модулей
- ✅ Подключение к базе данных
- ✅ Парсер событий
- ✅ Алерты по ночным клубам
- ✅ Запрос событий из БД

## ✅ ШАГ 2: Проверь свежие логи

```bash
cd /opt/taxibot
# Покажи последние 100 строк логов
tail -100 bot.log

# Или смотри логи в реальном времени
tail -f bot.log
```

Ищи строки с:
- `ERROR` - ошибки
- `nightclub` - работа алертов по клубам
- `KudaGo` - парсинг событий
- `event` - работа с мероприятиями

## ✅ ШАГ 3: Проверь что бот запущен

```bash
systemctl status taxibot
```

Должно быть: `Active: active (running)`

## ✅ ШАГ 4: Проверь веб-сервер

```bash
# Проверь что веб-сервер работает
curl -I http://localhost:8080/

# Проверь API мероприятий (нужен токен админа)
# Сначала получи токен через админ панель, затем:
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/admin/api/events
```

## 🔧 ВОЗМОЖНЫЕ ПРИЧИНЫ ОШИБКИ 500

### Причина 1: Проблема с timezone
**Симптом:** Ошибка при вызове `get_moscow_now()`

**Решение:**
```bash
cd /opt/taxibot
python -c "from bot.utils.timezone import now; print(now())"
```

Если ошибка - проверь что установлен `tzdata`:
```bash
apt install tzdata
```

### Причина 2: Проблема с базой данных
**Симптом:** Ошибка при запросе событий

**Решение:**
```bash
cd /opt/taxibot
sqlite3 data/bot.db "SELECT COUNT(*) FROM events;"
```

Если ошибка - база повреждена, восстанови из бэкапа.

### Причина 3: Отсутствуют новые поля в таблице events
**Симптом:** Ошибка "no such column: venue_name"

**Решение:**
```bash
cd /opt/taxibot
sqlite3 data/bot.db "PRAGMA table_info(events);"
```

Должны быть поля: venue_name, venue_lat, venue_lon

Если их нет, примени миграцию:
```bash
cd /opt/taxibot
python -c "
from alembic.versions.add_venue_info import upgrade
import asyncio
asyncio.run(upgrade())
"
```

### Причина 4: Старая версия кода
**Симптом:** Импорты не работают

**Решение:**
```bash
cd /opt/taxibot
git log --oneline -1
```

Должен быть коммит: `0d69fe6 Add deployment documentation and fix script`

Если нет:
```bash
git fetch origin main
git reset --hard origin/main
systemctl restart taxibot
```

## 📋 ПОСЛЕ ДИАГНОСТИКИ

Скопируй вывод команд и отправь мне:

1. Вывод `python test_bot.py`
2. Последние 50 строк логов: `tail -50 bot.log`
3. Статус бота: `systemctl status taxibot`
4. Версию кода: `git log --oneline -1`

Это поможет точно определить проблему!

## 🚀 БЫСТРАЯ КОМАНДА (всё в одном)

```bash
cd /opt/taxibot && \
echo "=== GIT VERSION ===" && \
git log --oneline -1 && \
echo "" && \
echo "=== BOT STATUS ===" && \
systemctl status taxibot --no-pager | head -20 && \
echo "" && \
echo "=== DIAGNOSTIC TEST ===" && \
source venv/bin/activate && \
python test_bot.py && \
echo "" && \
echo "=== RECENT LOGS ===" && \
tail -50 bot.log
```

Скопируй весь вывод этой команды!
