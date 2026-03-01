# 🚀 Быстрый старт - KefPulse Bot

## Шаг 1: Установка зависимостей

### Вариант А: Без виртуального окружения
```bash
cd C:\Users\Пользо\taxi-bot
pip install -r requirements.txt
```

### Вариант Б: С виртуальным окружением (рекомендуется)
```bash
cd C:\Users\Пользо\taxi-bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Шаг 2: Миграции базы данных

Запустите все миграции по порядку:

```bash
python migrate_event_filters.py
python migrate_quiet_hours.py
python migrate_financial.py
```

Каждая должна вывести: `✅ Migration complete!`

---

## Шаг 3: Проверка .env файла

Убедитесь, что файл `.env` содержит:

```env
# Обязательно
BOT_TOKEN=7845157915:AAEhfIe-ch9iruOrXQ4mXgN0TF0ye6hPmzQ
YANDEX_BEARER_TOKEN=your_bearer_token

# Опционально (для поиска по адресу)
YANDEX_GEOCODER_KEY=your_geocoder_key

# Опционально (для пробок)
YANDEX_API_KEY=your_traffic_key

# Остальные настройки
PARSE_INTERVAL_SECONDS=480
WEBAPP_URL=https://turgently-renunciatory-kellye.ngrok-free.dev
WEB_PORT=8080
```

---

## Шаг 4: Запуск бота

```bash
python bot/main.py
```

**Ожидаемый вывод:**
```
2026-03-01 09:00:00 [INFO] __main__: Database initialized
2026-03-01 09:00:00 [INFO] __main__: Skipping initial coefficient fetch for faster startup
2026-03-01 09:00:00 [INFO] __main__: Skipping initial event parsing for faster startup
2026-03-01 09:00:00 [INFO] __main__: Scheduler started (interval=480s)
2026-03-01 09:00:00 [INFO] __main__: Web server started on port 8080
2026-03-01 09:00:00 [INFO] __main__: Bot starting polling...
```

---

## Шаг 5: Быстрый тест в Telegram

Откройте бота: [@KefPulse_bot](https://t.me/KefPulse_bot)

### Тест 1: Базовые команды (2 минуты)
```
/start
/coefficients
/notify
/stats
```

### Тест 2: Финансовый трекер (5 минут)
```
/shift_start
(подождать 1 минуту)
/shift_end
Заработок: 1000
Пробег: 50
Поездок: 5
Заметки: -
/stats
```

### Тест 3: Настройки (3 минуты)
```
/notify
(включить тихие часы)
(настроить время: 22:00 - 07:00)
/expenses
/set_fuel 56
/goal
/set_daily_goal 5000
```

### Тест 4: Пробки (1 минута)
```
/traffic
/traffic_mkad
```

---

## Шаг 6: Проверка логов

Откройте второй терминал:
```bash
cd C:\Users\Пользо\taxi-bot
tail -f bot.log
```

Или просто откройте файл `bot.log` в редакторе.

---

## Возможные проблемы и решения

### Проблема 1: ModuleNotFoundError
**Решение:**
```bash
pip install -r requirements.txt
```

### Проблема 2: Database is locked
**Решение:**
```bash
# Остановить бота (Ctrl+C)
# Подождать 5 секунд
# Запустить снова
```

### Проблема 3: Бот не отвечает в Telegram
**Проверьте:**
1. Бот запущен и работает (нет ошибок в консоли)
2. BOT_TOKEN правильный в .env
3. Интернет соединение работает

### Проблема 4: Поиск не работает (/search)
**Причина:** Нет YANDEX_GEOCODER_KEY

**Решение:**
1. Получить ключ на https://developer.tech.yandex.ru/
2. Добавить в .env: `YANDEX_GEOCODER_KEY=your_key`
3. Перезапустить бота

### Проблема 5: Пробки показывают заглушки
**Это нормально!** Текущая версия использует упрощенную реализацию.

Для реальных данных нужен API ключ Яндекс.Пробок.

---

## Что тестировать в первую очередь

### Критичные функции (обязательно)
- [x] Запуск бота
- [x] /start работает
- [x] /coefficients показывает данные
- [x] /shift_start и /shift_end работают
- [x] /stats показывает статистику

### Важные функции (желательно)
- [x] /notify настройки работают
- [x] Тихие часы настраиваются
- [x] /expenses и настройки расходов
- [x] /goal и цели работают
- [x] /traffic показывает данные

### Дополнительные функции (опционально)
- [ ] /search (требует API ключ)
- [ ] /events и автопарсинг
- [ ] Уведомления о событиях
- [ ] Веб-карта работает

---

## Полезные команды

### Остановить бота
```
Ctrl + C
```

### Очистить базу данных (начать с нуля)
```bash
rm data/bot.db
python migrate_event_filters.py
python migrate_quiet_hours.py
python migrate_financial.py
```

### Проверить таблицы БД
```bash
sqlite3 data/bot.db ".tables"
```

### Посмотреть свои данные
```bash
sqlite3 data/bot.db "SELECT * FROM users WHERE telegram_id = YOUR_ID;"
```

### Посмотреть смены
```bash
sqlite3 data/bot.db "SELECT * FROM shifts ORDER BY start_time DESC LIMIT 5;"
```

---

## Следующие шаги после тестирования

### Если все работает ✅
1. Протестировать все команды из `TESTING_PLAN.md`
2. Проверить уведомления (добавить тестовое событие)
3. Использовать бот несколько дней для реальной работы
4. Собрать обратную связь

### Если есть проблемы ❌
1. Проверить логи в `bot.log`
2. Проверить консоль на ошибки
3. Проверить `.env` файл
4. Попробовать перезапустить бота

### Что улучшить дальше 🚀
1. Получить API ключи (геокодер, пробки)
2. Добавить больше площадок в `data/venues.json`
3. Настроить автозапуск бота (systemd, supervisor)
4. Добавить AI-советника
5. Реализовать монетизацию

---

## Контакты и поддержка

**Документация:**
- `PROJECT_STATUS.md` - общий статус проекта
- `VARIANT_A_COMPLETE.md` - поиск + тихие часы
- `VARIANT_B_COMPLETE.md` - финансовый трекер
- `VARIANT_C_COMPLETE.md` - дорожная обстановка
- `TESTING_PLAN.md` - детальный план тестирования
- `SUMMARY_ALL_VARIANTS.md` - общая сводка

**Бот:** @KefPulse_bot

---

## Чек-лист готовности

- [ ] Зависимости установлены
- [ ] Миграции выполнены
- [ ] .env настроен
- [ ] Бот запускается
- [ ] /start работает
- [ ] Базовые команды работают
- [ ] Финансовый трекер работает
- [ ] Настройки сохраняются
- [ ] Логи чистые (нет ERROR)

**Готов к использованию!** 🎉
