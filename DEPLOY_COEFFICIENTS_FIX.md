# Обновление: Исправление коэффициентов на карте

## Что исправлено

Восстановлена функциональность получения коэффициентов от Яндекс API.
Проблема была в том, что `fetch_all_coefficients()` был заглушкой и не делал реальных запросов к API.

Восстановлено:
- YandexGoPassengerProvider - для пассажирского API Яндекс.Go
- YandexGoProvider - для Pro API
- MockProvider - для разработки
- Реальные HTTP запросы к https://tc.mobile.yandex.net/3.0/routestats
- Парсинг коэффициентов из JSON ответов
- Защита от rate limiting с retry логикой

## Обновление на сервере

### Быстрая команда (всё в одной строке):

```bash
cd /opt/taxibot && git pull origin main && systemctl restart taxibot
```

### Пошагово:

1. Обнови код:
```bash
cd /opt/taxibot
git pull origin main
```

2. Перезапусти бота:
```bash
systemctl restart taxibot
```

## Проверка

После обновления:

1. Проверь что бот запустился:
```bash
systemctl status taxibot
```

2. Проверь логи (должны появиться запросы к Yandex API):
```bash
journalctl -u taxibot -n 100 --no-pager | grep -i "surge\|yandex\|coefficient"
```

3. Открой карту в браузере:
```
https://kefpulse.ru
```

4. Через 1-2 минуты на карте должны появиться гексагоны с коэффициентами

5. В боте нажми "🗺 Открыть карту" - должна открыться карта с коэффициентами

## Важно

- Коэффициенты обновляются каждые 2 минуты (настройка `parse_interval_seconds`)
- Между запросами к API задержка 8 секунд (защита от rate limiting)
- Если нет `yandex_bearer_token` в .env, будут использоваться mock данные

## Troubleshooting

### Коэффициенты всё равно не показываются

Проверь API ключи в .env:
```bash
cd /opt/taxibot
grep -E "yandex_bearer_token|yandex_device_id|yandex_mob_id" .env
```

Должны быть заполнены:
- YANDEX_BEARER_TOKEN
- YANDEX_DEVICE_ID
- YANDEX_MOB_ID

### Ошибки в логах

Если видишь ошибки 401/403:
- Проверь что токены актуальны
- Возможно нужно обновить bearer token

Если видишь ошибки 429:
- Это rate limiting, бот автоматически повторит запрос через 10 секунд
- Нормальная ситуация при большом количестве зон
