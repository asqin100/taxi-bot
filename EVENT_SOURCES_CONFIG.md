# Конфигурация источников событий

## Активные источники

### KudaGo API
```python
KUDAGO_CONFIG = {
    "enabled": True,
    "url": "https://kudago.com/public-api/v1.4/events/",
    "categories": ["concert", "sport", "exhibition", "festival"],
    "location": "msk",
    "page_size": 100,
    "days_ahead": 30,
    "priority": 1,  # Highest priority
}
```

### Sports.ru
```python
SPORTS_RU_CONFIG = {
    "enabled": True,  # Базовая реализация добавлена
    "urls": {
        "football": "https://www.sports.ru/football/calendar/",
        "hockey": "https://www.sports.ru/hockey/calendar/",
    },
    "moscow_teams": ["спартак", "цска", "динамо", "локомотив"],
    "priority": 2,
}
```

### Ticket Platforms (планируется)
```python
TICKET_PLATFORMS_CONFIG = {
    "enabled": False,  # Пока не реализовано
    "platforms": {
        "kassir": "https://www.kassir.ru/",
        "ticketland": "https://ticketland.ru/",
    },
    "priority": 3,
}
```

## Настройки парсинга

### Частота обновления
```python
PARSING_SCHEDULE = {
    "kudago": "6 hours",      # Каждые 6 часов
    "sports_ru": "12 hours",  # Каждые 12 часов
    "tickets": "12 hours",    # Каждые 12 часов (когда реализуем)
}
```

### Лимиты запросов
```python
RATE_LIMITS = {
    "kudago": {
        "requests_per_minute": 60,
        "timeout": 30,
    },
    "sports_ru": {
        "requests_per_minute": 10,  # Консервативно для парсинга
        "timeout": 30,
        "delay_between_requests": 2,  # секунды
    },
}
```

### User-Agent для парсинга
```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
```

## Приоритеты источников

При дублировании событий используется источник с более высоким приоритетом:
1. **KudaGo** - официальный API, наиболее надежный
2. **Sports.ru** - специализированный спортивный источник
3. **Ticket platforms** - дополнительный источник

## Дедупликация

### Критерии совпадения событий
```python
DEDUPLICATION_CONFIG = {
    "name_similarity_threshold": 0.85,  # Схожесть названий (Levenshtein)
    "time_window_minutes": 60,          # Окно времени ±60 минут
    "venue_match_required": False,      # Не обязательно совпадение места
}
```

### Стратегия объединения
При обнаружении дубликата:
1. Берем событие из источника с более высоким приоритетом
2. Дополняем недостающие поля из других источников
3. Логируем факт дедупликации для мониторинга

## Мониторинг качества

### Метрики для отслеживания
```python
MONITORING_METRICS = {
    "events_fetched_per_source": {},    # Количество событий по источникам
    "events_stored": 0,                  # Сохранено в БД
    "duplicates_found": 0,               # Найдено дубликатов
    "parsing_errors": {},                # Ошибки по источникам
    "events_without_venue": 0,           # События без определенного места
    "parsing_duration_seconds": {},      # Время парсинга по источникам
}
```

### Алерты
Отправлять уведомление админу если:
- Парсинг источника падает 3 раза подряд
- Количество событий упало на 50%+ по сравнению с предыдущим парсингом
- Более 30% событий не имеют определенной зоны

## Расширение источников

### Как добавить новый источник

1. Создать функцию парсера:
```python
async def parse_new_source() -> list[dict]:
    events = []
    # Парсинг логика
    return events
```

2. Добавить в `fetch_and_store_events()`:
```python
try:
    new_events = await parse_new_source()
    all_events.extend(new_events)
    logger.info("Fetched %d events from NewSource", len(new_events))
except Exception as e:
    logger.error("NewSource parsing failed: %s", e)
```

3. Добавить конфигурацию в этот файл

4. Обновить документацию

---
Дата: 19.03.2026
