# Исправление кнопки "Главное меню" для медиа-сообщений

## Проблема

Кнопка "Главное меню" не работала при нажатии на сообщениях с медиа (фото, документы):
- Тепловая карта (heatmap) - отправляет фото
- Экспорт CSV - отправляет документ

## Причина

Обработчик `cmd:menu` в `bot/handlers/start.py` пытался вызвать `edit_text()` на медиа-сообщении, что невозможно в Telegram API.

## Решение

Обновлен обработчик `cmd:menu` для определения типа сообщения:

```python
# Проверка на наличие медиа
has_media = any([
    callback.message.photo,
    callback.message.document,
    callback.message.video,
    callback.message.audio,
    callback.message.animation,
    callback.message.voice,
    callback.message.video_note,
    callback.message.sticker
])

if has_media:
    # Удаляем медиа-сообщение и отправляем новое текстовое
    await callback.message.delete()
    await callback.message.answer(...)
else:
    # Обычное текстовое сообщение - редактируем
    await callback.message.edit_text(...)
```

## Поддерживаемые типы медиа

- ✅ Фото (photo) - тепловая карта
- ✅ Документы (document) - CSV экспорт
- ✅ Видео (video)
- ✅ Аудио (audio)
- ✅ Анимации (animation)
- ✅ Голосовые (voice)
- ✅ Видео-заметки (video_note)
- ✅ Стикеры (sticker)

## Коммиты

- `afa3279` - Fix main menu button for media messages (photos/documents)
- `6133c0c` - Improve main menu handler to support all media types

## Проверка

После обновления на сервере проверить:

1. Тепловая карта:
   - Открыть "Мой кабинет" → "Финансы" → "📊 Карта заработка" (для Elite)
   - Нажать "🔙 Главное меню" на фото
   - Должно открыться главное меню

2. CSV экспорт:
   - Открыть "Мой кабинет" → "Финансы" → "📥 Экспорт в CSV" (для Elite)
   - Нажать "🏠 Главное меню" на документе
   - Должно открыться главное меню

3. Все остальные кнопки "Главное меню":
   - Проверить что работают из текстовых сообщений
   - Проверить что не сломались после изменений

## Статус

✅ Исправлено и протестировано в коде
⏳ Требуется тестирование на сервере после деплоя
