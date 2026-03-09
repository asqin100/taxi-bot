# Обновление бота - Последние исправления

## Что исправлено (3 коммита)

### 1. Восстановлена функциональность коэффициентов (commit 97d344b)
- Исправлена проблема: коэффициенты не показывались на карте
- Восстановлен полный функционал Yandex API
- Добавлены провайдеры: YandexGoPassengerProvider, YandexGoProvider, MockProvider
- Реальные HTTP запросы к Yandex routestats API
- Защита от rate limiting с retry логикой

### 2. Исправлен layout кнопок в главном меню (commit baeb6be)
- Все кнопки теперь одинаковой ширины (по одной в ряд)
- Исправлена проблема: кнопки меняли размер после навигации в "Мой кабинет"

### 3. Добавлена кнопка "Куда ехать?" (commit ad3e4aa)
- Новая кнопка в главном меню: "🗺 Куда ехать?"
- Функция находит ближайшую зону с коэффициентом ≥1.3 в радиусе 5км
- Запрашивает геолокацию пользователя
- Показывает маршрут с выбором Яндекс.Навигатор или Яндекс.Карты

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

## Проверка после обновления

1. Проверь что бот запустился:
```bash
systemctl status taxibot
```

2. Проверь логи:
```bash
journalctl -u taxibot -n 50 --no-pager
```

3. Протестируй в боте:
   - `/start` - главное меню должно показать все кнопки одинаковой ширины
   - Кнопка "🗺 Куда ехать?" должна быть первой в меню
   - Зайди в "Мой кабинет" и вернись - кнопки должны остаться широкими
   - Открой карту https://kefpulse.ru - через 1-2 минуты появятся коэффициенты

4. Проверь функцию "Куда ехать?":
   - Нажми "🗺 Куда ехать?"
   - Поделись геолокацией
   - Должен найти ближайшую зону с коэффициентом ≥1.3
   - Показать кнопки для навигации

## Логи коэффициентов

Чтобы увидеть как работает получение коэффициентов:

```bash
journalctl -u taxibot -f | grep -i "surge\|yandex\|coefficient"
```

Должны появиться записи типа:
- "Found surge 1.5 for tariff econom"
- "Fetched X surge data points"

## Важные настройки

Убедись что в .env есть:

```bash
cd /opt/taxibot
grep -E "WEBAPP_URL|YANDEX_BEARER_TOKEN" .env
```

Должно быть:
- `WEBAPP_URL=https://kefpulse.ru`
- `YANDEX_BEARER_TOKEN=<твой токен>`

## Troubleshooting

### Коэффициенты не показываются

1. Проверь API ключи:
```bash
grep -E "yandex" .env
```

2. Проверь логи на ошибки API:
```bash
journalctl -u taxibot -n 200 | grep -i "error\|warning"
```

### Кнопка "Куда ехать?" не работает

1. Проверь что handler зарегистрирован:
```bash
grep -r "where_to_go" /opt/taxibot/bot/handlers/
```

2. Проверь логи при нажатии кнопки:
```bash
journalctl -u taxibot -f
```

### Карта не открывается

1. Проверь WEBAPP_URL:
```bash
grep WEBAPP_URL /opt/taxibot/.env
```

2. Проверь что nginx работает:
```bash
systemctl status nginx
curl -I https://kefpulse.ru
```

## Коммиты

- `97d344b` - Restore Yandex API coefficient fetching functionality
- `675bc58` - Add deployment instructions for coefficient fix
- `baeb6be` - Fix main menu button layout - make all buttons full width
- `ad3e4aa` - Add 'Where to go' button to main menu
