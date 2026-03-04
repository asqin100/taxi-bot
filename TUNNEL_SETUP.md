# Настройка туннеля без предупреждений

## Проблема
Ngrok бесплатный показывает предупреждение "Visit Site" перед каждым новым посещением.

## Решение: Cloudflare Tunnel (РЕКОМЕНДУЕТСЯ)

### Шаг 1: Установка

1. Скачать cloudflared:
   - Windows: https://github.com/cloudflare/cloudflared/releases/latest
   - Скачать `cloudflared-windows-amd64.exe`
   - Переименовать в `cloudflared.exe`
   - Положить в папку `C:\taxi-bot\`

### Шаг 2: Запуск

```bash
# Вариант 1: Через батник
start_cloudflare_tunnel.bat

# Вариант 2: Вручную
cloudflared tunnel --url http://localhost:8080
```

### Шаг 3: Получить URL

После запуска увидите:
```
Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):
https://random-name.trycloudflare.com
```

### Шаг 4: Обновить URL в боте

Скопировать URL и вставить в команду бота:
```bash
/setwebapp https://random-name.trycloudflare.com
```

## Альтернативы

### 1. Ngrok Paid ($8/мес)
- Убирает предупреждение
- Фиксированный домен
- Команда: `ngrok http 8080 --domain=your-domain.ngrok-free.app`

### 2. Localtunnel (Бесплатно)
```bash
npm install -g localtunnel
lt --port 8080
```
⚠️ Может быть нестабильным

### 3. VPS (200-500₽/мес)
- Timeweb, Beget, DigitalOcean
- Свой домен без ограничений
- Для 100+ юзеров - лучший вариант

## Сравнение

| Решение | Цена | Предупреждение | Стабильность | Для 100 юзеров |
|---------|------|----------------|--------------|-----------------|
| Cloudflare Tunnel | 0₽ | ❌ Нет | ⭐⭐⭐⭐⭐ | ✅ Да |
| Ngrok Free | 0₽ | ✅ Есть | ⭐⭐⭐⭐ | ✅ Да |
| Ngrok Paid | $8/мес | ❌ Нет | ⭐⭐⭐⭐⭐ | ✅ Да |
| VPS | 200₽/мес | ❌ Нет | ⭐⭐⭐⭐⭐ | ✅ Да |

## Рекомендация

**Для текущего этапа:** Cloudflare Tunnel (бесплатно, без предупреждений)
**Для продакшена (100+ юзеров):** VPS с доменом
